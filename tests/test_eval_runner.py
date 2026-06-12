"""Tests for the slim, runner-driven eval CLI.

The runner drives execution itself: a fresh executor subprocess (prompt only)
then a fresh grader subprocess (clean env, output plus assertions). These tests
exercise the real orchestration through a hermetic ``stub`` provider that is
dispatched by the same matrix the ``claude``/``codex`` adapters use, plus direct
unit checks of the provider parsers and the grading/aggregation helpers.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "eval_runner.py"
sys.path.insert(0, str(SCRIPT.parent))

import eval_runner  # noqa: E402


class BaseRunnerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "AGENTS.md").write_text("# test policy\n", encoding="utf-8")
        (self.root / "evals" / "demo" / "fixtures").mkdir(parents=True)
        (self.root / "evals" / "demo" / "fixtures" / "input.txt").write_text("fixture\n", encoding="utf-8")
        (self.root / "skills" / "demo").mkdir(parents=True)
        (self.root / "skills" / "demo" / "SKILL.md").write_text("# Demo Skill\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def write_suite(self, data=None):
        suite = data if data is not None else {
            "schema_version": "1.0.0",
            "skill_name": "demo",
            "common_assertions": ["common assertion"],
            "evals": [
                {
                    "id": "E01",
                    "name": "First eval",
                    "prompt": "Do the thing.",
                    "files": ["evals/demo/fixtures/input.txt"],
                    "expectations": ["per-eval assertion"],
                },
                {
                    "id": "E02",
                    "name": "Second eval",
                    "prompt": "Do another thing.",
                    "expectations": ["second assertion"],
                },
            ],
        }
        path = self.root / "evals" / "demo" / "evals.json"
        path.write_text(json.dumps(suite, indent=2) + "\n", encoding="utf-8")
        return path

    def write_stub_spec(self, spec=None):
        spec = spec if spec is not None else {
            "executor_output": "answer",
            "grading": {"with_skill": {"pass": True}, "without_skill": {"pass": False}},
        }
        path = self.root / "stub_spec.json"
        path.write_text(json.dumps(spec), encoding="utf-8")
        return path

    def stub_env(self, spec_path, *, log=None, sleep=None, timeout=None):
        env = dict(os.environ)
        env["EVAL_RUNNER_STUB_FILE"] = str(spec_path)
        if log is not None:
            env["EVAL_RUNNER_STUB_LOG"] = str(log)
        if sleep is not None:
            env["EVAL_RUNNER_STUB_SLEEP"] = str(sleep)
        if timeout is not None:
            env["EVAL_RUNNER_STUB_TIMEOUT"] = str(timeout)
        return env

    def run_cli(self, *args, env=None, check=False):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            cwd=self.root,
            text=True,
            capture_output=True,
            env=env or dict(os.environ),
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f"command failed: {result.args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def iteration_dir(self, agent="stub", number=1):
        return self.root / "evals" / "demo" / "workspace" / agent / f"iteration-{number}"


# --------------------------------------------------------------------------- #
# Validation (retained behavior)
# --------------------------------------------------------------------------- #
class ValidateTests(BaseRunnerTest):
    def test_validate_accepts_well_formed_suite(self):
        path = self.write_suite()
        result = self.run_cli("validate", path, check=True)
        self.assertIn("OK:", result.stdout)
        self.assertIn("evals: 2", result.stdout)

    def test_validate_rejects_missing_skill_name(self):
        path = self.write_suite({"evals": [{"id": "E01", "prompt": "x"}]})
        result = self.run_cli("validate", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("skill_name", result.stderr)

    def test_validate_rejects_unsupported_field_and_duplicate_id(self):
        path = self.write_suite(
            {
                "skill_name": "demo",
                "surprise": 1,
                "evals": [
                    {"id": "E01", "prompt": "a"},
                    {"id": "E01", "prompt": "b"},
                ],
            }
        )
        result = self.run_cli("validate", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unsupported top-level field", result.stderr)
        self.assertIn("duplicate eval id", result.stderr)

    def test_validate_rejects_missing_fixture(self):
        path = self.write_suite(
            {
                "skill_name": "demo",
                "evals": [{"id": "E01", "prompt": "a", "files": ["evals/demo/fixtures/nope.txt"]}],
            }
        )
        result = self.run_cli("validate", path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing fixture file", result.stderr)


# --------------------------------------------------------------------------- #
# Fail-fast: invalid input exits non-zero with zero subprocess launches.
# --------------------------------------------------------------------------- #
class FailFastTests(BaseRunnerTest):
    def assert_no_subprocess(self, log_path):
        # The stub appends to the log on every launch; absence proves zero launches.
        self.assertFalse(log_path.exists(), "a provider subprocess was launched before pre-flight passed")

    def test_invalid_suite_exits_without_launch(self):
        path = self.write_suite({"evals": [{"id": "E01", "prompt": "x"}]})
        spec = self.write_stub_spec()
        log = self.root / "launch.log"
        result = self.run_cli("run", path, "--agent", "stub", env=self.stub_env(spec, log=log))
        self.assertEqual(result.returncode, 2)
        self.assert_no_subprocess(log)
        self.assertFalse(self.iteration_dir().exists())

    def test_runs_out_of_range_exits_without_launch(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        log = self.root / "launch.log"
        result = self.run_cli("run", path, "--agent", "stub", "--runs", "99", env=self.stub_env(spec, log=log))
        self.assertEqual(result.returncode, 2)
        self.assertIn("between 1 and 5", result.stderr)
        self.assert_no_subprocess(log)

    def test_concurrency_out_of_range_exits_without_launch(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        log = self.root / "launch.log"
        result = self.run_cli(
            "run", path, "--agent", "stub", "--concurrency", "999", env=self.stub_env(spec, log=log)
        )
        self.assertEqual(result.returncode, 2)
        self.assert_no_subprocess(log)

    def test_unavailable_provider_exits_without_launch(self):
        path = self.write_suite()
        log = self.root / "launch.log"
        # No EVAL_RUNNER_STUB_FILE -> stub reports unavailable.
        env = dict(os.environ)
        env.pop("EVAL_RUNNER_STUB_FILE", None)
        env["EVAL_RUNNER_STUB_LOG"] = str(log)
        result = self.run_cli("run", path, "--agent", "stub", env=env)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not available", result.stderr)
        self.assert_no_subprocess(log)

    def test_unknown_provider_exits_non_zero(self):
        path = self.write_suite()
        result = self.run_cli("run", path, "--agent", "imaginary")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown provider", result.stderr)

    def test_empty_suite_exits_zero_without_launch(self):
        path = self.write_suite({"skill_name": "demo", "evals": []})
        spec = self.write_stub_spec()
        log = self.root / "launch.log"
        result = self.run_cli("run", path, "--agent", "stub", env=self.stub_env(spec, log=log))
        self.assertEqual(result.returncode, 0)
        self.assert_no_subprocess(log)
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        self.assertEqual(benchmark["run_count"], 0)
        self.assertEqual(benchmark["evals"], [])


# --------------------------------------------------------------------------- #
# No-fabrication surface: no flag/field injects a token/duration value.
# --------------------------------------------------------------------------- #
class NoFabricationTests(BaseRunnerTest):
    def test_no_hand_typed_metric_flags(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        for flag in ("--total-tokens", "--duration-ms", "--output-chars", "--usage-text", "--allow-suspicious-metrics"):
            result = self.run_cli("run", path, "--agent", "stub", flag, "5", env=self.stub_env(spec))
            self.assertEqual(result.returncode, 2, f"{flag} should be rejected by argparse")
            self.assertIn("unrecognized arguments", result.stderr)

    def test_absent_metrics_recorded_as_absence(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        metrics = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "metrics.json").read_text()
        )
        self.assertIs(metrics["captured"], False)
        self.assertIsNone(metrics["source"])
        # No numeric token/duration value is fabricated when absent.
        self.assertNotIn("total_tokens", metrics)
        self.assertNotIn("duration_ms", metrics)


# --------------------------------------------------------------------------- #
# Separation of executor and grader (argv/env/prompt inspection).
# --------------------------------------------------------------------------- #
class SeparationTests(BaseRunnerTest):
    def test_executor_has_no_assertions_grader_has_them(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        run_dir = self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1"
        executor_prompt = (run_dir / "prompt.md").read_text()
        grader_prompt = (run_dir / "grader_prompt.md").read_text()
        self.assertNotIn("per-eval assertion", executor_prompt)
        self.assertNotIn("common assertion", executor_prompt)
        self.assertIn("per-eval assertion", grader_prompt)
        self.assertIn("common assertion", grader_prompt)

    def test_executor_and_grader_are_distinct_clean_invocations(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        record = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "run.json").read_text()
        )
        executor = record["executor_invocation"]
        grader = record["grader_invocation"]
        self.assertIsNotNone(grader)
        self.assertNotEqual(executor["argv"], grader["argv"])
        # Clean environment: neither pass carries the parent CLAUDECODE session.
        self.assertNotIn("CLAUDECODE", executor["env_keys"])
        self.assertNotIn("CLAUDECODE", grader["env_keys"])

    def test_delivered_content_keeps_assertions_out_of_executor(self):
        # Inspect the actual delivered invocation content (argv + stdin recorded
        # in run.json), not just the on-disk prompt.md, so a regression that
        # delivered assertions to the executor process would be caught.
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        record = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "run.json").read_text()
        )

        def delivered(inv):
            return " ".join(inv["argv"]) + "\n" + (inv.get("stdin") or "")

        exec_delivered = delivered(record["executor_invocation"])
        grader_delivered = delivered(record["grader_invocation"])
        # Assertions must not reach the executor process via argv or stdin...
        self.assertNotIn("per-eval assertion", exec_delivered)
        self.assertNotIn("common assertion", exec_delivered)
        self.assertIn("Do the thing.", exec_delivered)
        # ...but must reach the grader process.
        self.assertIn("per-eval assertion", grader_delivered)
        self.assertIn("common assertion", grader_delivered)

    def test_claude_strips_claudecode_for_nesting(self):
        os.environ["CLAUDECODE"] = "1"
        try:
            invocation = eval_runner.ClaudeProvider().build_invocation(
                "prompt", run_dir=self.root, role="executor"
            )
        finally:
            del os.environ["CLAUDECODE"]
        self.assertNotIn("CLAUDECODE", invocation.env)
        self.assertEqual(invocation.argv[:2], ["claude", "-p"])
        self.assertIn("--output-format", invocation.argv)


# --------------------------------------------------------------------------- #
# Model selection: --model is passed through to the provider CLI verbatim and
# recorded in the manifest/benchmark; an absent model uses the provider default.
# --------------------------------------------------------------------------- #
class ModelSelectionTests(BaseRunnerTest):
    def test_validate_model_label_accepts_vendor_ids(self):
        for value in (
            "sonnet",
            "claude-sonnet-4-6",
            "gpt-5.3-codex-spark",
            "us.anthropic.claude-opus-4-1-20250805-v1:0",
            "anthropic/claude-3",
        ):
            self.assertEqual(eval_runner.validate_model_label(value), value)

    def test_validate_model_label_none_and_blank_pass_through(self):
        self.assertIsNone(eval_runner.validate_model_label(None))
        self.assertIsNone(eval_runner.validate_model_label("   "))

    def test_validate_model_label_rejects_flag_like_and_spaced(self):
        for bad in ("-bad", "--model", "has space", "weird$char"):
            with self.assertRaises(eval_runner.CommandError):
                eval_runner.validate_model_label(bad)

    def test_claude_build_invocation_passes_model(self):
        provider = eval_runner.ClaudeProvider()
        without = provider.build_invocation("prompt", run_dir=self.root, role="executor")
        self.assertNotIn("--model", without.argv)
        with_model = provider.build_invocation(
            "prompt", run_dir=self.root, role="executor", model="claude-sonnet-4-6"
        )
        self.assertEqual(with_model.argv[-2:], ["--model", "claude-sonnet-4-6"])

    def test_codex_build_invocation_passes_model_before_prompt(self):
        provider = eval_runner.CodexProvider()
        without = provider.build_invocation("the prompt", run_dir=self.root, role="executor")
        self.assertNotIn("--model", without.argv)
        self.assertEqual(without.argv[-1], "the prompt")
        with_model = provider.build_invocation(
            "the prompt", run_dir=self.root, role="executor", model="gpt-5.3-codex-spark"
        )
        # The prompt stays positional/last; the model is an option before it.
        self.assertEqual(with_model.argv[-1], "the prompt")
        self.assertEqual(with_model.argv[-3:-1], ["--model", "gpt-5.3-codex-spark"])

    def test_codex_grader_invocation_writes_schema_file(self):
        provider = eval_runner.CodexProvider()
        run_dir = self.root / "rd"
        run_dir.mkdir()
        inv = provider.build_invocation(
            "the prompt", run_dir=run_dir, role="grader", schema=eval_runner.grader_schema()
        )
        self.assertIn("--output-schema", inv.argv)
        schema_path = run_dir / "grader_schema.json"
        self.assertTrue(schema_path.is_file())
        self.assertEqual(json.loads(schema_path.read_text())["required"], ["verdicts"])
        # The executor invocation carries no schema.
        ex = provider.build_invocation("p", run_dir=run_dir, role="executor")
        self.assertNotIn("--output-schema", ex.argv)

    def test_claude_grader_invocation_passes_json_schema(self):
        provider = eval_runner.ClaudeProvider()
        inv = provider.build_invocation(
            "prompt", run_dir=self.root, role="grader", schema=eval_runner.grader_schema()
        )
        self.assertIn("--json-schema", inv.argv)
        payload = inv.argv[inv.argv.index("--json-schema") + 1]
        self.assertEqual(json.loads(payload)["required"], ["verdicts"])
        ex = provider.build_invocation("prompt", run_dir=self.root, role="executor")
        self.assertNotIn("--json-schema", ex.argv)

    def test_model_recorded_in_manifest_and_benchmark(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli(
            "run", path, "--agent", "stub", "--model", "test-model-1", "--runs", "1",
            env=self.stub_env(spec), check=True,
        )
        manifest = json.loads((self.iteration_dir() / "iteration_manifest.json").read_text())
        self.assertEqual(manifest["model"], "test-model-1")
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        self.assertEqual(benchmark["model"], "test-model-1")
        self.assertIn("Model: `test-model-1`", (self.iteration_dir() / "benchmark.md").read_text())

    def test_absent_model_recorded_as_provider_default(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        self.assertIsNone(benchmark["model"])
        self.assertIn("Model: provider default", (self.iteration_dir() / "benchmark.md").read_text())

    def test_invalid_model_exits_without_launch(self):
        # A value that clears argparse (not flag-like) but fails the model regex
        # must be rejected by command_run's pre-flight with zero launches.
        path = self.write_suite()
        spec = self.write_stub_spec()
        log = self.root / "launch.log"
        result = self.run_cli(
            "run", path, "--agent", "stub", "--model", "bad model", env=self.stub_env(spec, log=log)
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("model must match", result.stderr)
        self.assertFalse(log.exists(), "a provider subprocess launched before model validation")

    def test_flag_like_model_rejected_by_argparse_without_launch(self):
        # argparse itself rejects a flag-like value (defense in depth before the
        # regex even runs); still zero launches.
        path = self.write_suite()
        spec = self.write_stub_spec()
        log = self.root / "launch.log"
        result = self.run_cli(
            "run", path, "--agent", "stub", "--model", "-bad", env=self.stub_env(spec, log=log)
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(log.exists(), "a provider subprocess launched before model validation")


# --------------------------------------------------------------------------- #
# Core pipeline + grading round-trip through the real dispatch path.
# --------------------------------------------------------------------------- #
class CorePipelineTests(BaseRunnerTest):
    def test_full_matrix_grades_and_compares(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        result = self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        self.assertIn("with_skill=100.0%", result.stdout)
        self.assertIn("without_skill=0.0%", result.stdout)
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        self.assertEqual(benchmark["overall_pass_rate"]["with_skill"], 1.0)
        self.assertEqual(benchmark["overall_pass_rate"]["without_skill"], 0.0)
        self.assertEqual(benchmark["comparison"]["candidate"], "with_skill")
        self.assertEqual(benchmark["comparison"]["delta"], 1.0)
        self.assertTrue((self.iteration_dir() / "benchmark.md").is_file())
        # Stub provider exposes no metrics, so the aggregate flag rolls up False.
        self.assertIs(benchmark["metrics_captured"], False)
        self.assertEqual(benchmark["error_run_count"], 0)

    def test_grader_verdict_round_trip_sets_pass_fail(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        grading = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "grading.json").read_text()
        )
        self.assertEqual(grading["passed"], grading["total"])
        self.assertEqual(grading["pass_rate"], 1.0)
        self.assertEqual([e["text"] for e in grading["expectations"]], ["common assertion", "per-eval assertion"])
        baseline = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "without_skill" / "run-1" / "grading.json").read_text()
        )
        self.assertEqual(baseline["passed"], 0)

    def test_clean_run_reports_sanity_ok(self):
        path = self.write_suite()
        spec = self.write_stub_spec(
            {"executor_output": "answer", "grading": {"with_skill": {"pass": True}, "without_skill": {"pass": True}}}
        )
        result = self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        self.assertTrue(benchmark["sanity_checks"]["ok"])
        self.assertIn("Sanity checks: OK", result.stdout)
        self.assertIn("## Sanity checks", (self.iteration_dir() / "benchmark.md").read_text())

    def test_report_re_renders_from_benchmark_json(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        out = self.root / "out.md"
        result = self.run_cli("report", self.iteration_dir(), "--output", out, check=True)
        self.assertIn("Eval Benchmark", result.stdout)
        self.assertTrue(out.is_file())


# --------------------------------------------------------------------------- #
# Bounded cost: exact launch count and concurrency cap.
# --------------------------------------------------------------------------- #
def parse_launch_log(log_path):
    events = []
    for line in log_path.read_text().splitlines():
        parts = line.split()
        if len(parts) != 4:
            continue
        event, role, _pid, ts = parts
        events.append((float(ts), event, role))
    return events


def max_concurrency(events):
    # Sweep line: exit before enter at equal timestamps to avoid overcount.
    ordered = sorted(events, key=lambda item: (item[0], 0 if item[1] == "exit" else 1))
    current = 0
    peak = 0
    for _ts, event, _role in ordered:
        if event == "enter":
            current += 1
            peak = max(peak, current)
        else:
            current -= 1
    return peak


class BoundedCostTests(BaseRunnerTest):
    def test_exact_launch_count_and_concurrency_cap(self):
        path = self.write_suite()  # 2 evals x 2 configs
        spec = self.write_stub_spec(
            {"executor_output": "answer", "grading": {"with_skill": {"pass": True}, "without_skill": {"pass": True}}}
        )
        log = self.root / "launch.log"
        runs = 2
        self.run_cli(
            "run", path, "--agent", "stub", "--runs", str(runs), "--concurrency", "2",
            env=self.stub_env(spec, log=log, sleep=0.1), check=True,
        )
        events = parse_launch_log(log)
        enters = [e for e in events if e[1] == "enter"]
        expected_tasks = 2 * 2 * runs  # evals x configs x runs
        executor_enters = [e for e in enters if e[2] == "executor"]
        grader_enters = [e for e in enters if e[2] == "grader"]
        # Each task launches exactly one executor and one matching grader: no more.
        self.assertEqual(len(executor_enters), expected_tasks)
        self.assertEqual(len(grader_enters), expected_tasks)
        self.assertLessEqual(max_concurrency(events), 2)


# --------------------------------------------------------------------------- #
# Negative and edge cases.
# --------------------------------------------------------------------------- #
class NegativeTests(BaseRunnerTest):
    def test_executor_timeout_records_failure_without_retry_or_grader(self):
        path = self.write_suite(
            {"skill_name": "demo", "evals": [{"id": "E01", "name": "First eval", "prompt": "x", "expectations": ["a"]}]}
        )
        spec = self.write_stub_spec()
        log = self.root / "launch.log"
        # with_skill executor sleeps 1.0s; --timeout 0.3 kills it. without_skill is fast.
        self.run_cli(
            "run", path, "--agent", "stub", "--runs", "1", "--timeout", "0.3", "--concurrency", "1",
            env=self.stub_env(spec, log=log, timeout=1.0),
        )
        record = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "run.json").read_text()
        )
        self.assertEqual(record["status"], "executor_timeout")
        self.assertEqual(record["passed"], 0)
        self.assertIsNone(record["pass_rate"])  # not scored, not folded into the mean
        self.assertFalse(record["scored"])
        self.assertIsNone(record["grader_invocation"])  # grader skipped, not run on empty output
        events = parse_launch_log(log)
        executor_enters = [e for e in events if e[1] == "enter" and e[2] == "executor"]
        grader_enters = [e for e in events if e[1] == "enter" and e[2] == "grader"]
        # One executor per config (with_skill timed out, without_skill ran): no retry storm.
        self.assertEqual(len(executor_enters), 2)
        # Grader-skip proven from the launch log, not only the run.json field:
        # only without_skill reached the grader.
        self.assertEqual(len(grader_enters), 1)

    def test_executor_failure_excluded_from_overall_pass_rate(self):
        # An executor that exits non-zero is recorded as a failure and must NOT
        # be folded into the comparison mean as a genuine 0%.
        path = self.write_suite()
        spec = self.write_stub_spec(
            {"executor_output": "answer", "executor_exit": 2, "grading": {"without_skill": {"pass": True}}}
        )
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        record = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "run.json").read_text()
        )
        self.assertEqual(record["status"], "executor_failed")
        self.assertIsNone(record["pass_rate"])
        self.assertFalse(record["scored"])
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        # with_skill had no scored run -> None, NOT 0.0; without_skill scored 100%.
        self.assertIsNone(benchmark["overall_pass_rate"]["with_skill"])
        self.assertEqual(benchmark["overall_pass_rate"]["without_skill"], 1.0)
        self.assertGreaterEqual(benchmark["error_run_count"], 1)
        self.assertIn("executor_failed", benchmark["status_counts"])
        self.assertIsNone(benchmark["comparison"]["candidate_pass_rate"])
        self.assertIsNone(benchmark["comparison"]["delta"])

    def test_grader_unparseable_excluded_and_not_a_pass(self):
        path = self.write_suite()
        spec = self.write_stub_spec(
            {
                "executor_output": "answer",
                "grading": {"with_skill": {"unparseable": True}, "without_skill": {"pass": True}},
            }
        )
        log = self.root / "launch.log"
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec, log=log), check=True)
        record = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "run.json").read_text()
        )
        self.assertEqual(record["status"], "grader_unparseable")
        self.assertEqual(record["passed"], 0)
        self.assertIsNone(record["pass_rate"])
        # The grader WAS launched (this is not a grader-skip).
        events = parse_launch_log(log)
        self.assertTrue(any(e[1] == "enter" and e[2] == "grader" for e in events))
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        self.assertIsNone(benchmark["overall_pass_rate"]["with_skill"])

    def test_sanity_checks_flag_infrastructure_failure(self):
        path = self.write_suite()
        spec = self.write_stub_spec(
            {"executor_output": "answer", "grading": {"with_skill": {"unparseable": True}, "without_skill": {"pass": True}}}
        )
        result = self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        sc = benchmark["sanity_checks"]
        self.assertFalse(sc["ok"])
        self.assertTrue(any(f["status"] == "grader_unparseable" for f in sc["infrastructure_failures"]))
        self.assertIn("REVIEW REQUIRED", result.stdout)
        self.assertIn("REVIEW REQUIRED", (self.iteration_dir() / "benchmark.md").read_text())

    def test_default_grading_failure_records_zero_pass(self):
        path = self.write_suite()
        spec = self.write_stub_spec({"executor_output": "answer", "grading": {}})
        self.run_cli("run", path, "--agent", "stub", "--runs", "1", env=self.stub_env(spec), check=True)
        grading = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "grading.json").read_text()
        )
        # A grader that ran and returned an all-false verdict IS a genuine 0%.
        self.assertEqual(grading["passed"], 0)
        record = json.loads(
            (self.iteration_dir() / "eval-first-eval" / "with_skill" / "run-1" / "run.json").read_text()
        )
        self.assertEqual(record["status"], "ok")
        self.assertEqual(record["pass_rate"], 0.0)


# --------------------------------------------------------------------------- #
# Provider parsers and helpers (hermetic unit tests).
# --------------------------------------------------------------------------- #
class ProviderParserTests(unittest.TestCase):
    def test_claude_parse_captures_metrics(self):
        sample = json.dumps(
            {
                "result": "the answer",
                "usage": {"input_tokens": 10, "output_tokens": 5},
                "duration_ms": 2250,
                "total_cost_usd": 0.01,
            }
        )
        output, metrics = eval_runner.ClaudeProvider().parse(
            run_dir=Path("."), stdout=sample, stderr="", exit_code=0, role="executor"
        )
        self.assertEqual(output, "the answer")
        self.assertTrue(metrics["captured"])
        self.assertEqual(metrics["total_tokens"], 15)
        self.assertEqual(metrics["duration_ms"], 2250)
        self.assertEqual(metrics["source"], "claude -p --output-format json")

    def test_claude_parse_absent_metrics_when_not_json(self):
        output, metrics = eval_runner.ClaudeProvider().parse(
            run_dir=Path("."), stdout="not json", stderr="", exit_code=0, role="executor"
        )
        self.assertEqual(output, "not json")
        self.assertIs(metrics["captured"], False)

    def test_claude_parse_flags_is_error_envelope(self):
        # claude reports an errored turn via is_error while still exiting 0; the
        # parser must flag it so the run is recorded as a provider failure, not
        # graded as a real answer.
        sample = json.dumps(
            {
                "is_error": True,
                "subtype": "error_max_turns",
                "result": "ran out of turns",
                "usage": {"input_tokens": 3, "output_tokens": 1},
            }
        )
        _output, metrics = eval_runner.ClaudeProvider().parse(
            run_dir=Path("."), stdout=sample, stderr="", exit_code=0, role="executor"
        )
        self.assertEqual(metrics.get("error"), "error_max_turns")

    def test_codex_metrics_absent_in_slim_core(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            (run_dir / "executor_codex_last.txt").write_text("codex answer", encoding="utf-8")
            output, metrics = eval_runner.CodexProvider().parse(
                run_dir=run_dir, stdout="{}", stderr="", exit_code=0, role="executor"
            )
        self.assertEqual(output, "codex answer")
        self.assertIs(metrics["captured"], False)

    def test_parse_grader_output_handles_wrapped_and_garbage(self):
        valid = '{"expectations": [{"text": "a", "passed": true, "evidence": "x"}]}'
        data, err = eval_runner.parse_grader_output(valid)
        self.assertIsNone(err)
        self.assertEqual(data["expectations"][0]["passed"], True)

        wrapped = "Sure!\n" + valid + "\nDone."
        data, err = eval_runner.parse_grader_output(wrapped)
        self.assertIsNone(err)
        self.assertEqual(len(data["expectations"]), 1)

        data, err = eval_runner.parse_grader_output("no json here")
        self.assertIsNone(data)
        self.assertIsNotNone(err)

    def test_parse_grader_output_survives_prose_with_braces(self):
        # Prose around the JSON that itself contains braces must not defeat
        # extraction (greedy first-{/last-} would fail here).
        verdict = '{"expectations": [{"text": "a", "passed": true, "evidence": "x"}]}'
        text = "Here is my analysis {note: see below}.\n" + verdict + "\nThanks {end}"
        data, err = eval_runner.parse_grader_output(text)
        self.assertIsNone(err)
        self.assertEqual(len(data["expectations"]), 1)
        self.assertEqual(data["expectations"][0]["text"], "a")

    def test_parse_grader_output_rejects_non_contract_fragment(self):
        # An unterminated evidence string (here ended by backticks instead of a
        # closing quote) merges array entries, so json.loads fails on the whole
        # object and only per-entry ``{"text","passed","evidence"}`` fragments
        # are brace-balanced. None of those fragments carries an ``expectations``
        # list, so the verdict is unparseable and must be reported as None --
        # returning a fragment would slip past the caller's ``grading is None``
        # guard and be scored as a false 0%.
        malformed = (
            '{"expectations": [{"text": "a", "passed": true, "evidence": "ok"},'
            '{"text": "b", "passed": true, "evidence": "broke `gate`.},'
            '{"text": "c", "passed": true, "evidence": "ok2"}]}'
        )
        data, err = eval_runner.parse_grader_output(malformed)
        self.assertIsNone(data)
        self.assertIsNotNone(err)

    def test_summarize_grading_recovers_enumerated_assertion_texts(self):
        # A grader that echoes the numbered "Assertions For Grading" list
        # (``1. ``, ``2) ``) prepends list markers to each text. Matching must
        # strip that leading marker so real verdicts are not lost to an exact
        # text mismatch and recorded as a false 0%; the assertion body still
        # has to match exactly.
        grading = {
            "expectations": [
                {"text": "1. Uses conventions mode.", "passed": True, "evidence": "e1"},
                {"text": "2) Stops before implementation.", "passed": False, "evidence": "e2"},
            ]
        }
        summary = eval_runner.summarize_grading(
            grading, ["Uses conventions mode.", "Stops before implementation."]
        )
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["expectations"][0]["evidence"], "e1")
        self.assertFalse(summary["expectations"][1]["passed"])

    def test_summarize_grading_marks_missing_assertions_failed(self):
        grading = {"expectations": [{"text": "a", "passed": True}]}
        summary = eval_runner.summarize_grading(grading, ["a", "b"])
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["total"], 2)
        self.assertFalse(summary["expectations"][1]["passed"])

    def test_summarize_grading_dedups_first_wins_and_drops_ghost(self):
        grading = {
            "expectations": [
                {"text": "a", "passed": True},
                {"text": "a", "passed": False},  # duplicate text -> first wins
                {"text": "ghost", "passed": True},  # not requested -> dropped
            ]
        }
        summary = eval_runner.summarize_grading(grading, ["a"])
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual([e["text"] for e in summary["expectations"]], ["a"])

    def test_grader_schema_is_index_keyed_verdict_contract(self):
        schema = eval_runner.grader_schema()
        self.assertEqual(schema["required"], ["verdicts"])
        item = schema["properties"]["verdicts"]["items"]
        self.assertEqual(sorted(item["required"]), ["evidence", "id", "passed"])
        self.assertEqual(item["properties"]["id"]["type"], "integer")
        self.assertEqual(item["properties"]["passed"]["type"], "boolean")
        self.assertIs(item["additionalProperties"], False)

    def test_parse_grader_output_accepts_structured_verdicts(self):
        verdict = '{"verdicts": [{"id": 1, "passed": true, "evidence": "x"}]}'
        data, err = eval_runner.parse_grader_output(verdict)
        self.assertIsNone(err)
        self.assertEqual(eval_runner.grader_verdict_list(data)[0]["id"], 1)

    def test_summarize_grading_maps_structured_verdicts_by_id(self):
        # Verdicts carry no assertion text at all; matching is by 1-based id, and
        # out-of-order verdicts still land on the right assertion.
        grading = {
            "verdicts": [
                {"id": 2, "passed": True, "evidence": "e2"},
                {"id": 1, "passed": False, "evidence": "e1"},
            ]
        }
        summary = eval_runner.summarize_grading(grading, ["first", "second"])
        self.assertEqual(summary["total"], 2)
        self.assertFalse(summary["expectations"][0]["passed"])
        self.assertEqual(summary["expectations"][0]["evidence"], "e1")
        self.assertTrue(summary["expectations"][1]["passed"])
        self.assertEqual(summary["expectations"][1]["text"], "second")

    def test_claude_parse_serializes_structured_result_object(self):
        # With --json-schema the result can come back as a nested object; the
        # parser must re-serialize it so the grader parser sees JSON text.
        sample = json.dumps(
            {"result": {"verdicts": [{"id": 1, "passed": True, "evidence": "x"}]},
             "usage": {"input_tokens": 1, "output_tokens": 1}}
        )
        output, _metrics = eval_runner.ClaudeProvider().parse(
            run_dir=Path("."), stdout=sample, stderr="", exit_code=0, role="grader"
        )
        data, err = eval_runner.parse_grader_output(output)
        self.assertIsNone(err)
        self.assertEqual(eval_runner.grader_verdict_list(data)[0]["passed"], True)

    def test_compute_sanity_checks_flags_anomalies(self):
        configs = ["with_skill", "without_skill"]
        runs = [
            {"eval_id": "E1", "configuration": "with_skill", "scored": False, "status": "grader_unparseable"},
            {"eval_id": "E1", "configuration": "without_skill", "scored": True, "status": "ok"},
        ]
        per_eval = [
            {"eval_id": "E1", "eval_name": "n", "configs": {
                "with_skill": {"pass_rate": None, "scored_runs": 0},
                "without_skill": {"pass_rate": 0.0, "scored_runs": 1},
            }},
            {"eval_id": "E2", "eval_name": "n", "configs": {
                "with_skill": {"pass_rate": 0.2, "scored_runs": 1},
                "without_skill": {"pass_rate": 0.6, "scored_runs": 1},
            }},
        ]
        s = eval_runner.compute_sanity_checks(configs, runs, per_eval)
        self.assertFalse(s["ok"])
        self.assertEqual(s["infrastructure_failures"][0]["eval_id"], "E1")
        self.assertEqual(s["zero_scored_cells"][0], {"eval_id": "E1", "configuration": "without_skill"})
        self.assertEqual(s["candidate_below_baseline"][0]["eval_id"], "E2")

    def test_compute_sanity_checks_ok_when_clean(self):
        s = eval_runner.compute_sanity_checks(
            ["with_skill", "without_skill"],
            [{"eval_id": "E1", "configuration": "with_skill", "scored": True, "status": "ok"}],
            [{"eval_id": "E1", "eval_name": "n", "configs": {
                "with_skill": {"pass_rate": 1.0, "scored_runs": 1},
                "without_skill": {"pass_rate": 0.5, "scored_runs": 1},
            }}],
        )
        self.assertTrue(s["ok"])
        self.assertEqual(s["infrastructure_failures"], [])

    def test_assertions_for_case_dedups_preserving_order(self):
        suite = eval_runner.EvalSuite(
            path=Path("e.json"), skill_name="demo", common_assertions=["x", "y"], evals=[], scoring={}, raw={}
        )
        case = eval_runner.EvalCase("E01", "n", "p", "", None, None, [], ["y", "z"], {})
        self.assertEqual(eval_runner.assertions_for_case(suite, case), ["x", "y", "z"])

    def test_aggregate_raw_pass_rate_numbers(self):
        suite = eval_runner.EvalSuite(
            path=Path("evals.json"),
            skill_name="demo",
            common_assertions=[],
            evals=[eval_runner.EvalCase("E01", "First", "p", "", None, None, [], ["a"], {})],
            scoring={},
            raw={},
        )
        runs = [
            {"eval_id": "E01", "configuration": "with_skill", "pass_rate": 1.0, "metrics": {"captured": False}},
            {"eval_id": "E01", "configuration": "without_skill", "pass_rate": 0.0, "metrics": {"captured": False}},
        ]
        benchmark = eval_runner.aggregate_runs(
            suite, ["with_skill", "without_skill"], runs, agent="stub", skill_path=None
        )
        self.assertEqual(benchmark["overall_pass_rate"]["with_skill"], 1.0)
        self.assertEqual(benchmark["comparison"]["delta"], 1.0)


# --------------------------------------------------------------------------- #
# Skill source resolution (folded snapshot guard).
# --------------------------------------------------------------------------- #
class SkillSourceTests(BaseRunnerTest):
    def test_with_skill_rejects_snapshot_path(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        (self.root / ".claude" / "skills" / "demo").mkdir(parents=True)
        (self.root / ".claude" / "skills" / "demo" / "SKILL.md").write_text("# snap\n", encoding="utf-8")
        result = self.run_cli(
            "run", path, "--agent", "stub", "--skill-path", ".claude/skills/demo/SKILL.md",
            env=self.stub_env(spec),
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("authoritative", result.stderr)

    def test_with_skill_defaults_to_authoritative_source(self):
        path = self.write_suite()
        spec = self.write_stub_spec()
        self.run_cli("run", path, "--agent", "stub", "--config", "with_skill", env=self.stub_env(spec), check=True)
        benchmark = json.loads((self.iteration_dir() / "benchmark.json").read_text())
        self.assertTrue(benchmark["skill_path"].endswith("skills/demo/SKILL.md"))


if __name__ == "__main__":
    unittest.main()
