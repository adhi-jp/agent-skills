import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "eval_runner.py"


class EvalRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "AGENTS.md").write_text("# test policy\n", encoding="utf-8")
        (self.root / "evals" / "demo" / "fixtures").mkdir(parents=True)
        (self.root / "evals" / "demo" / "fixtures" / "input.txt").write_text("fixture\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, check=True):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f"command failed: {result.args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def write_json(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def write_suite(self, data=None):
        suite = data or {
            "schema_version": "1.0.0",
            "skill_name": "demo",
            "purpose": "test suite",
            "common_assertions": ["common assertion"],
            "evals": [
                {
                    "id": "E01",
                    "name": "First eval",
                    "prompt": "Do the thing.",
                    "expected_output": "A useful result.",
                    "files": ["evals/demo/fixtures/input.txt"],
                    "expectations": ["per-eval assertion"],
                }
            ],
            "scoring": {
                "common_assertion_weight": 0.5,
                "per_eval_expectation_weight": 0.5,
                "pass_threshold": 0.8,
            },
        }
        path = self.root / "evals" / "demo" / "evals.json"
        self.write_json(path, suite)
        return path

    def agent_iteration(self, agent="codex", number=1, workspace_root=None):
        root = Path(workspace_root) if workspace_root else self.root / "evals" / "demo" / "workspace"
        return root / agent / f"iteration-{number}"

    def write_run(
        self,
        iteration,
        config,
        *,
        eval_id="E01",
        eval_name="First eval",
        eval_dir_name="eval-first",
        run_number=1,
        passed=True,
        seconds=12.5,
        tokens=1000,
        output_chars=None,
        legacy=False,
    ):
        eval_dir = iteration / eval_dir_name
        if not (eval_dir / "eval_metadata.json").exists():
            self.write_json(
                eval_dir / "eval_metadata.json",
                {
                    "eval_id": eval_id,
                    "eval_name": eval_name,
                    "prompt": "Prompt text for report.",
                    "assertions": ["Expectation text"],
                },
            )
        run_dir = eval_dir / config / f"run-{run_number}"
        run_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir = (eval_dir / config / "outputs") if legacy else (run_dir / "outputs")
        outputs_dir.mkdir(parents=True, exist_ok=True)
        (outputs_dir / "output.md").write_text(f"output from {config}\n", encoding="utf-8")
        if output_chars is None:
            output_chars = tokens
        expectation = {"text": "Expectation text", "passed": passed, "evidence": "Evidence text"}
        self.write_json(
            run_dir / "grading.json",
            {
                "expectations": [expectation],
                "summary": {
                    "passed": 1 if passed else 0,
                    "failed": 0 if passed else 1,
                    "total": 1,
                    "pass_rate": 1.0 if passed else 0.0,
                },
                "execution_metrics": {
                    "total_tool_calls": 2,
                    "errors_encountered": 0,
                    "output_chars": output_chars,
                },
            },
        )
        timing = {"total_duration_seconds": seconds}
        if tokens is not None:
            timing["total_tokens"] = tokens
        self.write_json(run_dir / "timing.json", timing)
        return run_dir

    def first_eval_dir(self, iteration):
        return next(iteration.glob("eval-*"))

    def prepared_run_dir(self, iteration, config, run_number=1):
        return self.first_eval_dir(iteration) / config / f"run-{run_number}"

    def receipt_payload(self, run_dir):
        manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
        return {
            "schema_version": "eval-runner-receipt-v1",
            "run_dir": str(run_dir),
            "prompt_sha256": manifest["prompt_sha256"],
            "run_fingerprint": manifest["run_fingerprint"],
        }

    def write_receipt(self, run_dir, destination=None, **overrides):
        payload = self.receipt_payload(run_dir)
        payload.update(overrides)
        target = destination or (run_dir / "outputs" / "run_receipt.json")
        self.write_json(target, payload)
        return target

    def record_prepared_run(
        self,
        run_dir,
        *,
        passed=True,
        seconds=12.5,
        tokens=1000,
        output_chars=1000,
        output_text="answer\n",
    ):
        suffix = "_".join(run_dir.parts[-4:])
        external = self.root / "external" / suffix
        external.mkdir(parents=True, exist_ok=True)
        (external / "response.md").write_text(output_text, encoding="utf-8")
        self.write_receipt(run_dir, external / "run_receipt.json")
        timing = self.root / "external" / f"{suffix}-timing.json"
        grading = self.root / "external" / f"{suffix}-grading.json"
        timing_data = {"total_duration_seconds": seconds}
        if tokens is not None:
            timing_data["total_tokens"] = tokens
        timing_data["output_chars"] = output_chars
        self.write_json(timing, timing_data)
        self.run_cli("record", run_dir, "--outputs", external, "--timing", timing)
        self.run_cli("prepare-grading", run_dir)
        metadata = json.loads((run_dir.parents[1] / "eval_metadata.json").read_text(encoding="utf-8"))
        assertions = metadata.get("assertions") or ["Expectation text"]
        passed_count = len(assertions) if passed else 0
        failed_count = 0 if passed else len(assertions)
        self.write_json(
            grading,
            {
                "expectations": [
                    {"text": assertion, "passed": passed, "evidence": "Evidence text"}
                    for assertion in assertions
                ],
                "summary": {
                    "passed": passed_count,
                    "failed": failed_count,
                    "total": len(assertions),
                    "pass_rate": 1.0 if passed else 0.0,
                },
                "execution_metrics": {
                    "total_tool_calls": 2,
                    "errors_encountered": 0,
                    "output_chars": output_chars,
                },
            },
        )
        self.run_cli("record", run_dir, "--outputs", external, "--timing", timing, "--grading", grading)

    def write_boundary_suite(self, prompt, assertions):
        return self.write_suite(
            {
                "schema_version": "1.0.0",
                "skill_name": "demo",
                "purpose": "boundary audit suite",
                "common_assertions": [],
                "evals": [
                    {
                        "id": "E01",
                        "name": "Boundary eval",
                        "prompt": prompt,
                        "expected_output": "Boundary-sensitive output.",
                        "files": [],
                        "expectations": assertions,
                    }
                ],
                "scoring": {
                    "common_assertion_weight": 0,
                    "per_eval_expectation_weight": 1,
                    "pass_threshold": 1,
                },
            }
        )

    def write_record_inputs(self, run_dir, *, output_text, evidence="ok", passed=True):
        suffix = "_".join(run_dir.parts[-4:])
        external = self.root / "external" / f"audit-{suffix}"
        external.mkdir(parents=True, exist_ok=True)
        (external / "response.md").write_text(output_text, encoding="utf-8")
        self.write_receipt(run_dir, external / "run_receipt.json")
        timing = self.root / "external" / f"audit-{suffix}-timing.json"
        self.write_json(timing, {"duration_ms": 10, "total_tokens": 11, "output_chars": len(output_text)})
        self.run_cli("record", run_dir, "--outputs", external, "--timing", timing)
        self.run_cli("prepare-grading", run_dir)
        grading = self.root / "external" / f"audit-{suffix}-grading.json"
        metadata = json.loads((run_dir.parents[1] / "eval_metadata.json").read_text(encoding="utf-8"))
        self.write_json(
            grading,
            {
                "expectations": [
                    {"text": assertion, "passed": passed, "evidence": evidence}
                    for assertion in metadata["assertions"]
                ]
            },
        )
        return external, timing, grading

    def test_validate_success_reports_counts(self):
        suite = self.write_suite()
        result = self.run_cli("validate", suite)
        self.assertIn("skill_name: demo", result.stdout)
        self.assertIn("evals: 1", result.stdout)
        self.assertIn("common_assertions: 1", result.stdout)
        self.assertIn("fixtures: 1 checked", result.stdout)

    def test_validate_rejects_ignored_or_invalid_fields(self):
        suite = self.write_suite(
            {
                "schema_version": "1.0.0",
                "skill_name": "demo",
                "unknown_top": True,
                "common_assertions": [],
                "evals": [
                    {
                        "id": "E01",
                        "name": "First",
                        "prompt": "Prompt.",
                        "files": ["evals/demo/fixtures/missing.txt"],
                        "expectations": "not a list",
                        "ignored": "field",
                    },
                    {"id": "E01", "name": "Duplicate", "files": [], "expectations": []},
                ],
            }
        )
        result = self.run_cli("validate", suite, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("unsupported top-level field", result.stderr)
        self.assertIn("unsupported eval field", result.stderr)
        self.assertIn("missing fixture file", result.stderr)
        self.assertIn("expected list", result.stderr)
        self.assertIn("duplicate eval id", result.stderr)
        self.assertIn(".prompt: missing required", result.stderr)

    def test_prepare_requires_agent(self):
        suite = self.write_suite()
        result = self.run_cli("prepare", suite, "--eval", "E01", "--config", "with_skill", check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("--agent", result.stderr)

    def test_grading_template_help_mentions_prepare_grading(self):
        result = self.run_cli("grading-template", "--help")

        self.assertIn("after prepare-grading", result.stdout)

    def test_prepare_rejects_invalid_agent_labels(self):
        suite = self.write_suite()
        for agent in ("", ".", "..", "/", "codex/child", "../codex", r"codex\child", "codex child"):
            result = self.run_cli(
                "prepare",
                suite,
                "--agent",
                agent,
                "--eval",
                "E01",
                "--config",
                "with_skill",
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("--agent", result.stderr)
        self.assertFalse((self.root / "evals" / "demo" / "workspace").exists())

    def test_prepare_creates_canonical_layout_and_refuses_overwrite(self):
        suite = self.write_suite()
        result = self.run_cli(
            "prepare",
            suite,
            "--agent",
            "codex",
            "--eval",
            "E01",
            "--config",
            "with_skill,without_skill",
            "--runs",
            "2",
            "--skill-path",
            "skills/demo/SKILL.md",
            "--model",
            "test-model",
            "--grader-model",
            "test-grader",
        )
        self.assertIn("prepared:", result.stdout)
        self.assertIn("evals:", result.stdout)
        iteration = self.agent_iteration("codex", 1)
        self.assertFalse((self.root / "evals" / "demo" / "workspace" / "iteration-1").exists())
        self.assertTrue((iteration / "run_index.json").is_file())
        self.assertTrue((iteration / "next_steps.md").is_file())
        eval_dirs = list(iteration.glob("eval-*"))
        self.assertEqual(1, len(eval_dirs))
        for config in ("with_skill", "without_skill"):
            for run_number in (1, 2):
                run_dir = eval_dirs[0] / config / f"run-{run_number}"
                self.assertTrue((run_dir / "outputs").is_dir())
                self.assertTrue((run_dir / "prompt.md").is_file())
                self.assertFalse((run_dir / "grader_prompt.md").exists())
                self.assertTrue((run_dir / "run_manifest.json").is_file())
                prompt = (run_dir / "prompt.md").read_text(encoding="utf-8")
                manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
                executor_metadata = json.loads((eval_dirs[0] / "executor_metadata.json").read_text(encoding="utf-8"))
                self.assertIn("Agent: `codex`", prompt)
                self.assertIn(f"Configuration: `{config}`", prompt)
                if config == "with_skill":
                    self.assertIn("Skill: `demo`", prompt)
                    self.assertIn("skills/demo/SKILL.md", prompt)
                    self.assertEqual("skills/demo/SKILL.md", manifest["skill_path"])
                else:
                    self.assertNotIn("Skill: `demo`", prompt)
                    self.assertNotIn("Skill path:", prompt)
                    self.assertNotIn("skills/demo/SKILL.md", prompt)
                    self.assertIsNone(manifest["skill_path"])
                    self.assertIn("Do not use any skill package or local skill file", prompt)
                self.assertNotIn("## Expected Output Summary", prompt)
                self.assertNotIn("A useful result.", prompt)
                self.assertNotIn("grader_prompt.md", prompt)
                self.assertNotIn("## Assertions For Grading", prompt)
                self.assertIn("separate grader pass", prompt)
                self.assertIn("duration_seconds", prompt)
                self.assertIn("--output-chars <N>", prompt)
                self.assertIn("--total-duration-seconds", prompt)
                self.assertIn(f"python3 scripts/eval_runner.py record {run_dir} --outputs <path> --timing <timing.json>", prompt)
                self.assertIn("run_receipt.json", prompt)
                self.assertIn("response.md", prompt)
                self.assertNotIn("common assertion", json.dumps(manifest))
                self.assertNotIn("per-eval assertion", json.dumps(manifest))
                self.assertNotIn("A useful result.", json.dumps(manifest))
                self.assertNotIn("common assertion", json.dumps(executor_metadata))
                self.assertNotIn("per-eval assertion", json.dumps(executor_metadata))
                self.assertNotIn("A useful result.", json.dumps(executor_metadata))
                self.assertIsNone(manifest["grader_prompt"])
                self.assertEqual("pending", manifest["grader_material_status"])
                self.assertEqual("eval-runner-v6", manifest["run_contract_version"])
                self.assertEqual("eval-runner-v6", manifest["run_fingerprint_inputs"]["run_contract_version"])
                self.assertEqual(64, len(manifest["prompt_sha256"]))
                self.assertEqual(64, len(manifest["executor_metadata_sha256"]))
                self.assertNotIn("grader_prompt_sha256", manifest)
                self.assertNotIn("eval_metadata_sha256", manifest)
                self.write_receipt(run_dir)
        metadata = json.loads((eval_dirs[0] / "executor_metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["eval_fingerprint"])
        self.assertNotIn("expected_output", metadata)
        self.assertFalse((eval_dirs[0] / "eval_metadata.json").exists())
        run_index = json.loads((iteration / "run_index.json").read_text(encoding="utf-8"))
        self.assertEqual(4, run_index["run_count"])
        self.assertEqual("eval-runner-v6", run_index["run_contract_version"])
        next_steps = (iteration / "next_steps.md").read_text(encoding="utf-8")
        self.assertIn("Do not reuse prompt text", next_steps)
        self.assertIn("eval-runner-receipt-v1", next_steps)
        self.assertIn("prepare-grading", next_steps)
        self.assertNotIn("grader_prompt.md", next_steps)

        iteration_manifest_text = (iteration / "iteration_manifest.json").read_text(encoding="utf-8")
        self.assertNotIn("source_evals_json", iteration_manifest_text)
        self.assertNotIn(str(suite), iteration_manifest_text)
        self.run_cli("prepare-grading", iteration)
        for config in ("with_skill", "without_skill"):
            for run_number in (1, 2):
                run_dir = eval_dirs[0] / config / f"run-{run_number}"
                self.assertTrue((run_dir / "grader_prompt.md").is_file())
                grader_prompt = (run_dir / "grader_prompt.md").read_text(encoding="utf-8")
                manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
                self.assertIn("common assertion", grader_prompt)
                self.assertIn("per-eval assertion", grader_prompt)
                self.assertIn("## Grading Boundary Rules", grader_prompt)
                self.assertIn("Grade the whole primary response", grader_prompt)
                self.assertIn("Markdown fences", grader_prompt)
                self.assertIn("show, inspect", grader_prompt)
                self.assertIn(str(run_dir / "outputs"), grader_prompt)
                self.assertIn(str(run_dir / "grading.json"), grader_prompt)
                self.assertEqual(str(run_dir / "grader_prompt.md"), manifest["grader_prompt"])
                self.assertEqual("ready", manifest["grader_material_status"])
                self.assertEqual(64, len(manifest["grader_prompt_sha256"]))
                self.assertEqual(64, len(manifest["eval_metadata_sha256"]))
        grader_metadata = json.loads((eval_dirs[0] / "eval_metadata.json").read_text(encoding="utf-8"))
        self.assertEqual("A useful result.", grader_metadata["expected_output"])
        self.assertIn("fingerprint_inputs", grader_metadata)

        iteration_manifest = json.loads((iteration / "iteration_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("codex", iteration_manifest["agent"])

        collision = self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", check=False)
        self.assertNotEqual(0, collision.returncode)
        self.assertIn("iteration already exists", collision.stderr)

    def test_prepare_uses_agent_scoped_iteration_numbers(self):
        suite = self.write_suite()
        for agent in ("codex", "claude"):
            self.run_cli("prepare", suite, "--agent", agent, "--eval", "E01", "--config", "with_skill")

        self.assertTrue(self.agent_iteration("codex", 1).is_dir())
        self.assertTrue(self.agent_iteration("claude", 1).is_dir())
        self.assertFalse(self.agent_iteration("claude", 2).exists())

    def test_prepare_workspace_root_is_parent_of_agent_roots(self):
        suite = self.write_suite()
        workspace_root = self.root / "custom-workspace"
        self.run_cli(
            "prepare",
            suite,
            "--workspace-root",
            workspace_root,
            "--agent",
            "gemini",
            "--eval",
            "E01",
            "--config",
            "with_skill",
        )

        self.assertTrue((workspace_root / "gemini" / "iteration-1").is_dir())
        self.assertFalse((workspace_root / "iteration-1").exists())

    def test_prepare_grading_custom_workspace_requires_evals_json(self):
        suite = self.write_suite()
        workspace_root = self.root / "custom-workspace"
        self.run_cli(
            "prepare",
            suite,
            "--workspace-root",
            workspace_root,
            "--agent",
            "gemini",
            "--eval",
            "E01",
            "--config",
            "with_skill",
        )
        run_dir = self.prepared_run_dir(self.agent_iteration("gemini", 1, workspace_root), "with_skill")
        self.write_receipt(run_dir)

        failed = self.run_cli("prepare-grading", run_dir, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("pass --evals-json", failed.stderr)
        next_steps = (self.agent_iteration("gemini", 1, workspace_root) / "next_steps.md").read_text(encoding="utf-8")
        self.assertIn("prepare-grading", next_steps)
        self.assertIn("--evals-json <evals.json>", next_steps)
        prompt = (run_dir / "prompt.md").read_text(encoding="utf-8")
        self.assertIn("--evals-json <evals.json>", prompt)
        self.run_cli("prepare-grading", run_dir, "--evals-json", suite)
        self.assertTrue((run_dir / "grader_prompt.md").is_file())

    def test_prepare_writes_stable_fingerprints_and_fixture_changes_affect_them(self):
        suite = self.write_suite()
        for iteration in ("1", "2"):
            self.run_cli(
                "prepare",
                suite,
                "--agent",
                "codex",
                "--iteration",
                iteration,
                "--eval",
                "E01",
                "--config",
                "with_skill",
                "--runs",
                "1",
                "--model",
                "exec-model",
                "--grader-model",
                "grader-model",
            )

        self.run_cli(
            "prepare",
            suite,
            "--agent",
            "claude",
            "--iteration",
            "1",
            "--eval",
            "E01",
            "--config",
            "with_skill",
            "--runs",
            "1",
            "--model",
            "exec-model",
            "--grader-model",
            "grader-model",
        )

        first = self.agent_iteration("codex", 1)
        second = self.agent_iteration("codex", 2)
        claude = self.agent_iteration("claude", 1)
        first_metadata = json.loads((self.first_eval_dir(first) / "executor_metadata.json").read_text(encoding="utf-8"))
        second_metadata = json.loads((self.first_eval_dir(second) / "executor_metadata.json").read_text(encoding="utf-8"))
        first_manifest = json.loads((self.prepared_run_dir(first, "with_skill") / "run_manifest.json").read_text(encoding="utf-8"))
        second_manifest = json.loads((self.prepared_run_dir(second, "with_skill") / "run_manifest.json").read_text(encoding="utf-8"))
        claude_manifest = json.loads((self.prepared_run_dir(claude, "with_skill") / "run_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(first_metadata["eval_fingerprint"], second_metadata["eval_fingerprint"])
        self.assertEqual(first_manifest["run_fingerprint"], second_manifest["run_fingerprint"])
        self.assertNotEqual(first_manifest["run_fingerprint"], claude_manifest["run_fingerprint"])
        self.assertEqual("eval-runner-v6", first_manifest["run_contract_version"])
        self.assertEqual("eval-runner-v6", first_manifest["run_fingerprint_inputs"]["run_contract_version"])
        self.assertEqual("codex", first_manifest["agent"])
        self.assertEqual("codex", first_manifest["run_fingerprint_inputs"]["agent"])
        self.assertEqual("claude", claude_manifest["agent"])
        self.assertEqual("grader-model", first_manifest["grader_model"])
        fixture_entry = first_metadata["fixtures"][0]
        self.assertEqual("evals/demo/fixtures/input.txt", fixture_entry["path"])
        self.assertEqual(64, len(fixture_entry["sha256"]))

        (self.root / "evals" / "demo" / "fixtures" / "input.txt").write_text("changed fixture\n", encoding="utf-8")
        self.run_cli(
            "prepare",
            suite,
            "--agent",
            "codex",
            "--iteration",
            "3",
            "--eval",
            "E01",
            "--config",
            "with_skill",
            "--runs",
            "1",
            "--model",
            "exec-model",
            "--grader-model",
            "grader-model",
        )
        third = self.agent_iteration("codex", 3)
        third_metadata = json.loads((self.first_eval_dir(third) / "executor_metadata.json").read_text(encoding="utf-8"))
        third_manifest = json.loads((self.prepared_run_dir(third, "with_skill") / "run_manifest.json").read_text(encoding="utf-8"))
        self.assertNotEqual(first_metadata["eval_fingerprint"], third_metadata["eval_fingerprint"])
        self.assertNotEqual(first_manifest["run_fingerprint"], third_manifest["run_fingerprint"])

    def test_prepare_rerun_of_compares_inputs_before_writing(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        first = self.agent_iteration("codex", 1)

        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--rerun-of", first)
        self.assertTrue(self.agent_iteration("codex", 2).is_dir())

        (self.root / "evals" / "demo" / "fixtures" / "input.txt").write_text("changed fixture\n", encoding="utf-8")
        failed = self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "3", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--rerun-of", first, check=False)
        self.assertNotEqual(0, failed.returncode)
        self.assertIn("input changes detected", failed.stderr)
        self.assertIn("eval fingerprint changed", failed.stderr)
        self.assertFalse(self.agent_iteration("codex", 3).exists())

        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "3", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--rerun-of", first, "--accept-input-changes")
        manifest = json.loads((self.agent_iteration("codex", 3) / "iteration_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["accepted_input_changes"])

        force = self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "4", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--rerun-of", first, "--force", check=False)
        self.assertNotEqual(0, force.returncode)
        self.assertIn("cannot be combined with --force", force.stderr)

    def test_prepare_rerun_of_rejects_legacy_current_contract_mismatch(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        first = self.agent_iteration("codex", 1)
        manifest_path = first / "iteration_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["run_contract_version"] = "eval-runner-v4"
        self.write_json(manifest_path, manifest)

        failed = self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--rerun-of", first, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("run contract", failed.stderr)
        self.assertIn("eval-runner-v4", failed.stderr)
        self.assertIn("eval-runner-v6", failed.stderr)

    def test_record_copies_outputs_and_validates_grading_schema(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = next(self.agent_iteration("codex", 1).glob("eval-*")) / "with_skill" / "run-1"
        external = self.root / "external"
        external.mkdir()
        (external / "answer.md").write_text("answer\n", encoding="utf-8")
        (external / "response.md").write_text("answer\n", encoding="utf-8")
        self.write_receipt(run_dir, external / "run_receipt.json")
        timing = self.root / "timing.json"
        grading = self.root / "grading.json"
        invalid_grading = self.root / "invalid-grading.json"
        self.write_json(timing, {"total_duration_seconds": 3, "total_tokens": 42, "output_chars": 7})
        self.write_json(
            grading,
            {
                "expectations": [
                    {"text": "common assertion", "passed": True, "evidence": "y"},
                    {"text": "per-eval assertion", "passed": True, "evidence": "y"},
                ]
            },
        )
        self.write_json(invalid_grading, {"expectations": [{"text": "common assertion", "passed": True}]})

        self.run_cli("record", run_dir, "--outputs", external, "--timing", timing)
        self.run_cli("prepare-grading", run_dir)
        self.run_cli("record", run_dir, "--outputs", external, "--timing", timing, "--grading", grading)
        self.assertEqual("answer\n", (run_dir / "outputs" / "answer.md").read_text(encoding="utf-8"))
        self.assertTrue((run_dir / "timing.json").is_file())
        self.assertTrue((run_dir / "grading.json").is_file())

        result = self.run_cli("record", run_dir, "--grading", invalid_grading, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn(".evidence: missing required field", result.stderr)

    def test_record_rejects_grading_with_missing_or_changed_expectation_text(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)
        self.run_cli("prepare-grading", run_dir)
        grading = self.root / "changed-grading.json"
        self.write_json(
            grading,
            {
                "expectations": [
                    {"text": "common assertion", "passed": True, "evidence": "ok"},
                    {"text": "changed assertion", "passed": True, "evidence": "ok"},
                ]
            },
        )

        result = self.run_cli("record", run_dir, "--grading", grading, check=False)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("expectation text mismatch", result.stderr)
        self.assertIn("per-eval assertion", result.stderr)

    def test_record_metric_flags_write_timing_json(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")

        self.run_cli("record", run_dir, "--total-tokens", "123", "--duration-ms", "4567", "--output-chars", "89")

        timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
        self.assertEqual(123, timing["total_tokens"])
        self.assertEqual(4567, timing["duration_ms"])
        self.assertEqual(89, timing["output_chars"])

    def test_record_metric_flags_merge_with_timing_file(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        timing = self.root / "timing.json"
        self.write_json(timing, {"duration_ms": 1, "total_duration_seconds": 9, "note": "keep"})

        self.run_cli("record", run_dir, "--timing", timing, "--duration-ms", "22", "--total-tokens", "33")

        merged = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
        self.assertEqual("keep", merged["note"])
        self.assertEqual(22, merged["duration_ms"])
        self.assertEqual(33, merged["total_tokens"])
        self.assertEqual(9, merged["total_duration_seconds"])

    def test_record_finalize_requires_receipt_and_metrics_for_current_contract_runs(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")

        failed = self.run_cli("record", run_dir, "--finalize", check=False)
        self.assertNotEqual(0, failed.returncode)
        self.assertIn("missing prompt receipt", failed.stderr)

        self.write_receipt(run_dir)
        failed_metrics = self.run_cli("record", run_dir, "--finalize", check=False)
        self.assertNotEqual(0, failed_metrics.returncode)
        self.assertIn("missing total_tokens", failed_metrics.stderr)

        self.run_cli("record", run_dir, "--total-tokens", "11", "--duration-ms", "22", "--output-chars", "33", "--finalize")
        metadata = json.loads((run_dir / "record_metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["finalized"])
        self.assertFalse(metadata["noncanonical"])

    def test_record_finalize_rejects_non_positive_metrics_without_writing_timing(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)

        failed = self.run_cli("record", run_dir, "--total-tokens", "0", "--duration-ms", "0", "--output-chars", "0", "--finalize", check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("non-positive-duration", failed.stderr)
        self.assertIn("non-positive-total-tokens", failed.stderr)
        self.assertFalse((run_dir / "timing.json").exists())

    def test_record_finalize_preserves_existing_timing_when_metric_audit_fails(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)
        self.write_json(run_dir / "timing.json", {"duration_ms": 10, "total_tokens": 11, "output_chars": 12})

        failed = self.run_cli("record", run_dir, "--total-tokens", "0", "--duration-ms", "0", "--output-chars", "0", "--finalize", check=False)

        self.assertNotEqual(0, failed.returncode)
        timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
        self.assertEqual({"duration_ms": 10, "total_tokens": 11, "output_chars": 12}, timing)

    def test_record_finalize_allows_suspicious_metric_opt_out_as_noncanonical(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)

        self.run_cli("record", run_dir, "--total-tokens", "0", "--duration-ms", "0", "--output-chars", "0", "--finalize", "--allow-suspicious-metrics")

        metadata = json.loads((run_dir / "record_metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["allow_suspicious_metrics"])
        self.assertTrue(metadata["noncanonical"])
        self.assertEqual("opted-out", metadata["metrics_audit"]["status"])

    def test_record_finalize_warns_on_single_known_placeholder_metric_pair(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)

        self.run_cli("record", run_dir, "--total-tokens", "5000", "--duration-ms", "30000", "--output-chars", "0", "--finalize")

        metadata = json.loads((run_dir / "record_metadata.json").read_text(encoding="utf-8"))
        self.assertFalse(metadata["noncanonical"])
        self.assertEqual("warning", metadata["metrics_audit"]["status"])
        self.assertEqual("known-placeholder-metrics", metadata["metrics_audit"]["findings"][0]["rule_id"])

    def test_record_finalize_allows_zero_output_chars_with_real_metrics(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)

        self.run_cli("record", run_dir, "--total-tokens", "1", "--duration-ms", "1", "--output-chars", "0", "--finalize")

        metadata = json.loads((run_dir / "record_metadata.json").read_text(encoding="utf-8"))
        self.assertFalse(metadata["noncanonical"])
        timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
        self.assertEqual(0, timing["output_chars"])

    def test_record_allows_missing_receipt_and_marks_aggregate_incomplete(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        for config in ("with_skill", "without_skill"):
            run_dir = self.prepared_run_dir(iteration, config)
            self.run_cli("prepare-grading", run_dir, "--allow-missing-receipt")
            metadata = json.loads((run_dir.parents[1] / "eval_metadata.json").read_text(encoding="utf-8"))
            self.write_json(
                run_dir / "grading.json",
                {"expectations": [{"text": assertion, "passed": True, "evidence": "ok"} for assertion in metadata["assertions"]]},
            )
            self.run_cli("record", run_dir, "--total-tokens", "1", "--duration-ms", "2", "--output-chars", "3", "--finalize", "--allow-missing-prompt-receipt")

        failed = self.run_cli("aggregate", iteration, check=False)
        self.assertNotEqual(0, failed.returncode)
        self.assertIn("prompt receipt opt-out", failed.stderr)
        self.run_cli("aggregate", iteration, "--allow-incomplete")

    def test_record_grading_rejects_passed_raw_commit_message_with_fence(self):
        suite = self.write_boundary_suite(
            "Show the raw commit message as plain text. Do not wrap it in Markdown.",
            ["Output is a raw commit message and does not wrap it in a Markdown code fence."],
        )
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        external, timing, grading = self.write_record_inputs(
            run_dir,
            output_text="```text\nfix(demo): correct behavior\n```\n",
            evidence="The commit message is raw inside the fence.",
        )

        failed = self.run_cli("record", run_dir, "--outputs", external, "--timing", timing, "--grading", grading, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("suspicious grading", failed.stderr)
        self.assertIn("raw-commit-message-fence", failed.stderr)
        self.assertFalse((run_dir / "grading.json").exists())

    def test_record_finalize_audits_existing_grading_json(self):
        suite = self.write_boundary_suite(
            "Return a standalone answer without prompt-local references.",
            ["Output stands alone without prompt context."],
        )
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)
        (run_dir / "outputs" / "response.md").write_text("Use the fenced block above.\n", encoding="utf-8")
        self.write_json(run_dir / "timing.json", {"duration_ms": 10, "total_tokens": 11, "output_chars": 28})
        self.run_cli("prepare-grading", run_dir)
        self.write_json(
            run_dir / "grading.json",
            {"expectations": [{"text": "Output stands alone without prompt context.", "passed": True, "evidence": "ok"}]},
        )

        failed = self.run_cli("record", run_dir, "--finalize", check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("standalone-prompt-local-reference", failed.stderr)

    def test_record_grading_allows_suspicious_opt_out_and_surfaces_in_outputs(self):
        suite = self.write_boundary_suite(
            "Show the raw commit message as plain text. Do not wrap it in Markdown.",
            ["Output is a raw commit message and does not wrap it in a Markdown code fence."],
        )
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        run_dir = self.prepared_run_dir(iteration, "with_skill")
        external, timing, grading = self.write_record_inputs(
            run_dir,
            output_text="```text\nfix(demo): correct behavior\n```\n",
            evidence="The real command would receive raw text inside the fence.",
        )

        self.run_cli(
            "record",
            run_dir,
            "--outputs",
            external,
            "--timing",
            timing,
            "--grading",
            grading,
            "--allow-suspicious-grading",
        )

        metadata = json.loads((run_dir / "record_metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["allow_suspicious_grading"])
        self.assertTrue(metadata["noncanonical"])
        doctor = self.run_cli("doctor", iteration, "--require-complete", check=False)
        self.assertNotEqual(0, doctor.returncode)
        self.assertIn("grading_audit_opted-out: 1", doctor.stdout)
        self.assertIn("grading audit opted-out", doctor.stdout)
        aggregate_failed = self.run_cli("aggregate", iteration, check=False)
        self.assertNotEqual(0, aggregate_failed.returncode)
        self.assertIn("suspicious-grading opt-out", aggregate_failed.stderr)
        self.run_cli("aggregate", iteration, "--allow-incomplete")
        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertEqual("opted-out", benchmark["runs"][0]["grading_audit"]["status"])
        review = self.root / "review-audit.html"
        self.run_cli("report", iteration, "--output", review)
        html_text = review.read_text(encoding="utf-8")
        self.assertIn("raw-commit-message-fence", html_text)
        self.assertIn("Grading Audit", html_text)

    def test_record_grading_rejects_json_only_response_with_prose(self):
        suite = self.write_boundary_suite(
            "Return valid JSON only.",
            ["Output is valid JSON only with no surrounding prose."],
        )
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        external, timing, grading = self.write_record_inputs(
            run_dir,
            output_text="Here is the JSON:\n{\"ok\": true}\n",
            evidence="It is JSON.",
        )

        failed = self.run_cli("record", run_dir, "--outputs", external, "--timing", timing, "--grading", grading, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("json-only-contract", failed.stderr)

    def test_record_batch_prevalidates_grading_audit_without_partial_writes(self):
        suite = self.write_boundary_suite(
            "Show the raw commit message as plain text. Do not wrap it in Markdown.",
            ["Output is a raw commit message and does not wrap it in a Markdown code fence."],
        )
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        (run_dir / "outputs" / "response.md").write_text("```text\nfix(demo): correct behavior\n```\n", encoding="utf-8")
        self.write_receipt(run_dir)
        self.run_cli("prepare-grading", run_dir)
        grading = self.root / "batch-grading.json"
        self.write_json(
            grading,
            {"expectations": [{"text": "Output is a raw commit message and does not wrap it in a Markdown code fence.", "passed": True, "evidence": "inside the fence"}]},
        )
        records = self.root / "records-audit.json"
        self.write_json(
            records,
            {"records": [{"run_dir": str(run_dir), "grading": str(grading), "total_tokens": 1, "duration_ms": 2, "output_chars": 3}]},
        )

        failed = self.run_cli("record-batch", records, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("raw-commit-message-fence", failed.stderr)
        self.assertFalse((run_dir / "timing.json").exists())
        self.assertFalse((run_dir / "grading.json").exists())

    def test_record_auto_fills_output_chars_and_parses_usage(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)
        (run_dir / "outputs" / "response.md").write_text("abcdef\n", encoding="utf-8")
        usage = self.root / "usage.txt"
        usage.write_text("<usage>total_tokens: 77, tool_uses: 5, total_duration_seconds: 1.5</usage>\n", encoding="utf-8")

        self.run_cli("record", run_dir, "--usage-file", usage, "--duration-ms", "2500", "--finalize")

        timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
        self.assertEqual(77, timing["total_tokens"])
        self.assertEqual(5, timing["total_tool_calls"])
        self.assertEqual(2500, timing["duration_ms"])
        self.assertEqual(7, timing["output_chars"])

    def test_grading_template_writes_assertions_and_unfilled_template_fails(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        template = self.root / "template.json"

        missing = self.run_cli("grading-template", run_dir, "--output", template, check=False)
        self.assertNotEqual(0, missing.returncode)
        self.assertIn("grading materials are not prepared", missing.stderr)
        self.write_receipt(run_dir)
        self.run_cli("prepare-grading", run_dir)
        self.run_cli("grading-template", run_dir, "--output", template)

        data = json.loads(template.read_text(encoding="utf-8"))
        self.assertEqual(["common assertion", "per-eval assertion"], [item["text"] for item in data["expectations"]])
        self.assertIsNone(data["expectations"][0]["passed"])
        failed = self.run_cli("record", run_dir, "--grading", template, check=False)
        self.assertNotEqual(0, failed.returncode)
        self.assertIn(".passed: expected boolean", failed.stderr)

    def test_extract_timing_accepts_duration_seconds(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", seconds=10, tokens=100)
        self.write_run(iteration, "without_skill", seconds=20, tokens=200)
        for path, seconds in (
            (iteration / "eval-first" / "with_skill" / "run-1" / "timing.json", 3.5),
            (iteration / "eval-first" / "without_skill" / "run-1" / "timing.json", 4.5),
        ):
            self.write_json(path, {"duration_seconds": seconds, "total_tokens": 10})

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertEqual(3.5, benchmark["runs"][0]["result"]["time_seconds"])
        self.assertEqual(8.0, benchmark["configs"]["with_skill"]["time_seconds"]["total"] + benchmark["configs"]["without_skill"]["time_seconds"]["total"])

    def test_extract_timing_prefers_duration_ms_when_aliases_conflict(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", seconds=10, tokens=100)
        self.write_run(iteration, "without_skill", seconds=20, tokens=200)
        self.write_json(iteration / "eval-first" / "with_skill" / "run-1" / "timing.json", {"duration_ms": 22, "total_duration_seconds": 9, "total_tokens": 10})

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertEqual(0.022, benchmark["configs"]["with_skill"]["time_seconds"]["total"])

    def test_aggregate_rejects_grading_with_expectation_text_mismatch(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.run_cli("prepare-grading", run_dir, "--allow-missing-receipt")
        self.write_json(run_dir / "timing.json", {"duration_ms": 1, "total_tokens": 1})
        self.write_json(
            run_dir / "grading.json",
            {
                "expectations": [
                    {"text": "common assertion", "passed": True, "evidence": "ok"},
                    {"text": "paraphrased assertion", "passed": True, "evidence": "ok"},
                ]
            },
        )

        result = self.run_cli("aggregate", self.agent_iteration("codex", 1), "--allow-incomplete", check=False)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("expectation text mismatch", result.stderr)

    def test_record_idempotent_when_outputs_are_already_in_run_dir(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        (run_dir / "outputs" / "answer.md").write_text("answer\n", encoding="utf-8")

        self.run_cli("record", run_dir, "--outputs", run_dir / "outputs")

        self.assertEqual("answer\n", (run_dir / "outputs" / "answer.md").read_text(encoding="utf-8"))

    def test_record_rejects_outputs_source_that_contains_destination(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        (run_dir / "answer.md").write_text("answer\n", encoding="utf-8")

        result = self.run_cli("record", run_dir, "--outputs", run_dir, check=False)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("outputs source contains destination", result.stderr)

    def test_record_idempotent_when_timing_or_grading_is_same_file(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)
        self.write_json(run_dir / "timing.json", {"duration_ms": 100, "total_tokens": 2, "output_chars": 3})
        self.run_cli("prepare-grading", run_dir)
        self.write_json(
            run_dir / "grading.json",
            {
                "expectations": [
                    {"text": "common assertion", "passed": True, "evidence": "ok"},
                    {"text": "per-eval assertion", "passed": True, "evidence": "ok"},
                ]
            },
        )

        self.run_cli("record", run_dir, "--timing", run_dir / "timing.json", "--grading", run_dir / "grading.json")

        timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
        self.assertEqual(100, timing["duration_ms"])

    def test_aggregate_canonical_uses_real_counts_and_labels(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", passed=True, seconds=10, tokens=100)
        self.write_run(iteration, "without_skill", passed=False, seconds=20, tokens=200)
        result = self.run_cli("aggregate", iteration, "--model", "test-model")
        self.assertIn("benchmark_json", result.stdout)
        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertEqual("codex", benchmark["metadata"]["agent"])
        self.assertEqual("codex", benchmark["runs"][0]["agent"])
        self.assertEqual({"with_skill": 1, "without_skill": 1}, benchmark["metadata"]["runs_per_configuration"])
        self.assertEqual(["with_skill", "without_skill"], benchmark["metadata"]["configs"])
        self.assertEqual("test-model", benchmark["metadata"]["executor_model"])
        self.assertFalse(benchmark["metadata"]["incomplete"])
        self.assertEqual(1, len(benchmark["comparisons"]))
        self.assertEqual(100, benchmark["configs"]["with_skill"]["tokens"]["total"])
        self.assertEqual(10, benchmark["configs"]["with_skill"]["time_seconds"]["total"])
        self.assertEqual(100, benchmark["configs"]["with_skill"]["output_chars"]["total"])
        self.assertEqual(1, benchmark["configs"]["without_skill"]["failed_expectations_total"])
        markdown = (iteration / "benchmark.md").read_text(encoding="utf-8")
        self.assertIn("with_skill", markdown)
        self.assertIn("without_skill", markdown)
        self.assertIn("Total tokens", markdown)
        self.assertIn("Output chars", markdown)
        self.assertIn("Tool calls", markdown)
        self.assertIn("Failed expectations", markdown)
        self.assertNotIn("Config B", markdown)

    def test_aggregate_uses_tool_trace_when_tool_call_metrics_missing(self):
        iteration = self.agent_iteration("codex", 1)
        with_run = self.write_run(iteration, "with_skill", passed=True, seconds=10, tokens=100)
        without_run = self.write_run(iteration, "without_skill", passed=True, seconds=20, tokens=200)
        for run_dir in (with_run, without_run):
            grading_path = run_dir / "grading.json"
            grading = json.loads(grading_path.read_text(encoding="utf-8"))
            grading["execution_metrics"].pop("total_tool_calls")
            self.write_json(grading_path, grading)
        self.write_json(
            with_run / "outputs" / "tool_trace.json",
            {
                "source": "parent-captured host trace",
                "delegated_invocation_count": 7,
                "delegated_invocations": [{"id": "ignored"}],
            },
        )
        self.write_json(
            without_run / "outputs" / "tool_trace.json",
            {
                "source": "parent-captured host trace",
                "tool_invocations": [{"id": "one"}, {"id": "two"}],
            },
        )

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        by_config = {run["configuration"]: run for run in benchmark["runs"]}
        self.assertEqual(7, by_config["with_skill"]["result"]["tool_calls"])
        self.assertEqual(2, by_config["without_skill"]["result"]["tool_calls"])
        self.assertEqual(7, benchmark["configs"]["with_skill"]["tool_calls"]["total"])
        self.assertEqual(2, benchmark["configs"]["without_skill"]["tool_calls"]["total"])

    def test_aggregate_rejects_invalid_tool_call_counts(self):
        iteration = self.agent_iteration("codex", 1)
        with_run = self.write_run(iteration, "with_skill", passed=True)
        self.write_run(iteration, "without_skill", passed=True)
        grading_path = with_run / "grading.json"
        grading = json.loads(grading_path.read_text(encoding="utf-8"))
        grading["execution_metrics"].pop("total_tool_calls")
        grading["execution_metrics"]["tool_calls"] = {"Agent": True}
        self.write_json(grading_path, grading)

        failed = self.run_cli("aggregate", iteration, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("tool_calls.Agent must be a non-negative integer", failed.stderr)

    def test_aggregate_rejects_invalid_tool_trace_count(self):
        iteration = self.agent_iteration("codex", 1)
        with_run = self.write_run(iteration, "with_skill", passed=True)
        self.write_run(iteration, "without_skill", passed=True)
        grading_path = with_run / "grading.json"
        grading = json.loads(grading_path.read_text(encoding="utf-8"))
        grading["execution_metrics"].pop("total_tool_calls")
        self.write_json(grading_path, grading)
        self.write_json(
            with_run / "outputs" / "tool_trace.json",
            {
                "source": "parent-captured host trace",
                "delegated_invocation_count": 1.5,
            },
        )

        failed = self.run_cli("aggregate", iteration, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("delegated_invocation_count must be a non-negative integer", failed.stderr)

    def test_aggregate_computes_summary_from_expectations_not_grader_summary(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", passed=True, seconds=10, tokens=100)
        self.write_run(iteration, "without_skill", passed=False, seconds=20, tokens=200)
        grading_path = iteration / "eval-first" / "without_skill" / "run-1" / "grading.json"
        grading = json.loads(grading_path.read_text(encoding="utf-8"))
        grading["summary"] = {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0}
        self.write_json(grading_path, grading)

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        baseline = next(run for run in benchmark["runs"] if run["configuration"] == "without_skill")
        self.assertEqual(0, baseline["result"]["passed"])
        self.assertEqual(1, baseline["result"]["failed"])
        self.assertEqual(0.0, baseline["result"]["pass_rate"])

    def test_aggregate_reuses_compatible_baseline_from_explicit_source(self):
        suite = self.write_suite()
        self.run_cli(
            "prepare",
            suite,
            "--agent",
            "codex",
            "--iteration",
            "1",
            "--eval",
            "E01",
            "--config",
            "without_skill",
            "--runs",
            "1",
            "--model",
            "exec-model",
            "--grader-model",
            "grader-model",
        )
        source = self.agent_iteration("codex", 1)
        self.record_prepared_run(
            self.prepared_run_dir(source, "without_skill"),
            passed=False,
            seconds=20,
            tokens=50,
            output_chars=500,
            output_text="baseline\n",
        )
        self.run_cli(
            "prepare",
            suite,
            "--agent",
            "codex",
            "--iteration",
            "2",
            "--eval",
            "E01",
            "--config",
            "with_skill",
            "--runs",
            "1",
            "--model",
            "exec-model",
            "--grader-model",
            "grader-model",
        )
        current = self.agent_iteration("codex", 2)
        self.record_prepared_run(
            self.prepared_run_dir(current, "with_skill"),
            passed=True,
            seconds=10,
            tokens=100,
            output_chars=1000,
            output_text="candidate\n",
        )

        self.run_cli("aggregate", current, "--baseline-from", source)
        benchmark = json.loads((current / "benchmark.json").read_text(encoding="utf-8"))
        reused = [run for run in benchmark["runs"] if run["configuration"] == "without_skill"]
        self.assertEqual(1, len(reused))
        self.assertTrue(reused[0]["reused"])
        self.assertTrue(reused[0]["fingerprint_match"])
        self.assertEqual(str(source), reused[0]["source_iteration"])
        self.assertEqual("codex", reused[0]["agent"])
        self.assertIn("source_run_dir", reused[0])
        self.assertEqual(1, benchmark["metadata"]["baseline_reused_runs"])
        self.assertEqual({"with_skill": 1, "without_skill": 1}, benchmark["metadata"]["runs_per_configuration"])
        self.assertEqual(50, benchmark["configs"]["without_skill"]["tokens"]["total"])
        self.assertEqual(500, benchmark["configs"]["without_skill"]["output_chars"]["total"])
        self.assertEqual(2, benchmark["configs"]["without_skill"]["failed_expectations_total"])
        markdown = (current / "benchmark.md").read_text(encoding="utf-8")
        self.assertIn("| E01 | without_skill | 1 | yes |", markdown)

    def test_aggregate_does_not_replace_current_baseline_with_source_baseline(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "without_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        source = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(source, "without_skill"), tokens=50, output_chars=500)
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 2)
        self.record_prepared_run(self.prepared_run_dir(current, "with_skill"), tokens=100, output_chars=1000)
        self.record_prepared_run(self.prepared_run_dir(current, "without_skill"), tokens=999, output_chars=9999)

        self.run_cli("aggregate", current, "--baseline-from", source)
        benchmark = json.loads((current / "benchmark.json").read_text(encoding="utf-8"))
        self.assertEqual(0, benchmark["metadata"]["baseline_reused_runs"])
        self.assertFalse(any(run.get("reused") for run in benchmark["runs"]))
        self.assertEqual(999, benchmark["configs"]["without_skill"]["tokens"]["total"])
        self.assertEqual(9999, benchmark["configs"]["without_skill"]["output_chars"]["total"])

    def test_aggregate_baseline_reuse_reports_missing_source_run(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(current, "with_skill"))
        source = self.agent_iteration("codex", 99)
        source.mkdir(parents=True)

        result = self.run_cli("aggregate", current, "--baseline-from", source, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("missing source run for E01 without_skill run-1", result.stderr)

    def test_aggregate_baseline_reuse_rejects_missing_fingerprint_metadata(self):
        suite = self.write_suite()
        source = self.agent_iteration("codex", 1)
        self.write_run(source, "without_skill")
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 2)
        self.record_prepared_run(self.prepared_run_dir(current, "with_skill"))

        result = self.run_cli("aggregate", current, "--baseline-from", source, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("missing fingerprint metadata", result.stderr)

    def test_aggregate_baseline_reuse_rejects_eval_fingerprint_mismatch(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "without_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        source = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(source, "without_skill"))
        (self.root / "evals" / "demo" / "fixtures" / "input.txt").write_text("changed fixture\n", encoding="utf-8")
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 2)
        self.record_prepared_run(self.prepared_run_dir(current, "with_skill"))

        result = self.run_cli("aggregate", current, "--baseline-from", source, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("eval fingerprint mismatch", result.stderr)

    def test_aggregate_baseline_reuse_rejects_run_fingerprint_mismatch(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "without_skill", "--runs", "1", "--model", "old-model", "--grader-model", "grader-model")
        source = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(source, "without_skill"))
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--model", "new-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 2)
        self.record_prepared_run(self.prepared_run_dir(current, "with_skill"))

        result = self.run_cli("aggregate", current, "--baseline-from", source, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("model mismatch", result.stderr)
        self.assertIn("run fingerprint mismatch", result.stderr)

    def test_aggregate_baseline_from_rejects_legacy_current_contract_mismatch(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "without_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        source = self.agent_iteration("codex", 1)
        source_run = self.prepared_run_dir(source, "without_skill")
        self.record_prepared_run(source_run)
        manifest_path = source_run / "run_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["run_contract_version"] = "eval-runner-v4"
        self.write_json(manifest_path, manifest)
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 2)
        self.record_prepared_run(self.prepared_run_dir(current, "with_skill"))

        result = self.run_cli("aggregate", current, "--baseline-from", source, check=False)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("run contract mismatch", result.stderr)
        self.assertIn("eval-runner-v4", result.stderr)
        self.assertIn("eval-runner-v6", result.stderr)

    def test_aggregate_baseline_from_rejects_same_legacy_contract_without_current_recompute(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "without_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        source = self.agent_iteration("codex", 1)
        source_run = self.prepared_run_dir(source, "without_skill")
        self.record_prepared_run(source_run)
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "2", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 2)
        current_run = self.prepared_run_dir(current, "with_skill")
        self.record_prepared_run(current_run)
        for run_dir in (source_run, current_run):
            manifest_path = run_dir / "run_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["run_contract_version"] = "eval-runner-v4"
            self.write_json(manifest_path, manifest)

        result = self.run_cli("aggregate", current, "--baseline-from", source, check=False)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("baseline reuse for run contract 'eval-runner-v4' is unsupported", result.stderr)
        self.assertNotIn("run fingerprint mismatch", result.stderr)

    def test_aggregate_baseline_reuse_rejects_agent_mismatch(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "claude", "--iteration", "1", "--eval", "E01", "--config", "without_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        source = self.agent_iteration("claude", 1)
        self.record_prepared_run(self.prepared_run_dir(source, "without_skill"))
        self.run_cli("prepare", suite, "--agent", "codex", "--iteration", "1", "--eval", "E01", "--config", "with_skill", "--runs", "1", "--model", "exec-model", "--grader-model", "grader-model")
        current = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(current, "with_skill"))

        result = self.run_cli("aggregate", current, "--baseline-from", source, check=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("agent mismatch", result.stderr)

    def test_aggregate_separates_tokens_from_output_chars(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", tokens=None, output_chars=321)
        self.write_run(iteration, "without_skill", tokens=None, output_chars=654)

        self.run_cli("aggregate", iteration, "--allow-incomplete")
        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertIsNone(benchmark["runs"][0]["result"]["tokens"])
        self.assertEqual(321, benchmark["configs"]["with_skill"]["output_chars"]["total"])
        self.assertIsNone(benchmark["configs"]["with_skill"]["tokens"]["mean"])
        self.assertIn("missing tokens", "; ".join(benchmark["metadata"]["incomplete_reasons"]))
        markdown = (iteration / "benchmark.md").read_text(encoding="utf-8")
        self.assertIn("321", markdown)
        self.assertIn("n/a", markdown)

    def test_aggregate_blocks_repeated_known_placeholder_metrics(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(iteration, "with_skill"), seconds=30, tokens=5000, output_chars=123)
        self.record_prepared_run(self.prepared_run_dir(iteration, "without_skill"), seconds=30, tokens=5000, output_chars=456)

        failed = self.run_cli("aggregate", iteration, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("repeated known placeholder metrics 30000ms/5000 tokens", failed.stderr)
        self.run_cli("aggregate", iteration, "--allow-incomplete")
        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertTrue(benchmark["metadata"]["incomplete"])
        self.assertEqual("warning", benchmark["runs"][0]["metrics_audit"]["status"])
        markdown = (iteration / "benchmark.md").read_text(encoding="utf-8")
        self.assertIn("Metric Integrity", markdown)
        self.assertIn("known-placeholder-metrics", markdown)
        review = self.root / "placeholder-review.html"
        self.run_cli("report", iteration, "--output", review)
        html_text = review.read_text(encoding="utf-8")
        self.assertIn("Metric Integrity", html_text)
        self.assertIn("repeated known placeholder metrics", html_text)

    def test_aggregate_blocks_alternate_repeated_known_placeholder_metrics(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(iteration, "with_skill"), seconds=60, tokens=15000)
        self.record_prepared_run(self.prepared_run_dir(iteration, "without_skill"), seconds=60, tokens=15000)

        failed = self.run_cli("aggregate", iteration, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("repeated known placeholder metrics 60000ms/15000 tokens", failed.stderr)

    def test_aggregate_notes_generic_repeated_metrics_without_blocking(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(iteration, "with_skill"), seconds=12, tokens=345)
        self.record_prepared_run(self.prepared_run_dir(iteration, "without_skill"), seconds=12, tokens=345)

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertFalse(benchmark["metadata"]["incomplete"])
        kinds = {note["kind"] for note in benchmark["analysis"]["notes"]}
        self.assertIn("repeated_metric_tuple", kinds)

    def test_aggregate_writes_analyzer_notes_for_equal_always_passing_and_failing_expectations(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", eval_id="E01", eval_dir_name="eval-one", passed=True)
        self.write_run(iteration, "without_skill", eval_id="E01", eval_dir_name="eval-one", passed=True)
        self.write_run(iteration, "with_skill", eval_id="E02", eval_dir_name="eval-two", passed=False)
        self.write_run(iteration, "without_skill", eval_id="E02", eval_dir_name="eval-two", passed=False)

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        kinds = {note["kind"] for note in benchmark["analysis"]["notes"]}
        self.assertIn("always_passing_expectation", kinds)
        self.assertIn("always_failing_expectation", kinds)
        self.assertIn("equal_expectation_pass_rate", kinds)
        markdown = (iteration / "benchmark.md").read_text(encoding="utf-8")
        self.assertIn("## Analysis", markdown)
        self.assertIn("Always-passing expectation", markdown)
        self.assertIn("Always-failing expectation", markdown)

    def test_aggregate_writes_equal_note_for_candidate_baseline_with_third_config(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", passed=True)
        self.write_run(iteration, "without_skill", passed=True)
        self.write_run(iteration, "variant", passed=False)

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        equal_notes = [note for note in benchmark["analysis"]["notes"] if note["kind"] == "equal_expectation_pass_rate"]
        self.assertTrue(equal_notes)
        self.assertEqual({"with_skill", "without_skill"}, set(equal_notes[0]["pass_rates"]))

    def test_aggregate_writes_analyzer_notes_for_repeated_run_variance(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", run_number=1, passed=True, seconds=10, tokens=100)
        self.write_run(iteration, "with_skill", run_number=2, passed=False, seconds=11, tokens=150)
        self.write_run(iteration, "without_skill", run_number=1, passed=False, seconds=20, tokens=200)
        self.write_run(iteration, "without_skill", run_number=2, passed=True, seconds=20, tokens=200)

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        messages = "\n".join(note["message"] for note in benchmark["analysis"]["notes"])
        self.assertIn("Repeated-run expectation variance", messages)
        self.assertIn("Repeated-run pass-rate variance", messages)
        self.assertIn("Repeated-run metric variance", messages)
        self.assertIn("Time/token tradeoff", messages)

    def test_aggregate_surfaces_file_artifact_boundary_warning_without_changing_pass_rate(self):
        suite = self.write_boundary_suite(
            "Produce plan.md as an artifact.",
            ["Output records that file `plan.md` exists as a produced artifact."],
        )
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        run_dir = self.prepared_run_dir(iteration, "with_skill")
        external, timing, grading = self.write_record_inputs(
            run_dir,
            output_text="Created plan.md.\n",
            evidence="The file exists.",
        )
        self.run_cli("record", run_dir, "--outputs", external, "--timing", timing, "--grading", grading)

        self.run_cli("aggregate", iteration, "--allow-incomplete")

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        run = benchmark["runs"][0]
        self.assertEqual(1.0, run["result"]["pass_rate"])
        self.assertEqual("warning", run["grading_audit"]["status"])
        self.assertEqual(1, benchmark["metadata"]["grading_audit"]["warning"])
        markdown = (iteration / "benchmark.md").read_text(encoding="utf-8")
        self.assertIn("file-artifact-boundary", markdown)

    def test_aggregate_single_config_requires_allow_incomplete(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", passed=True)
        failed = self.run_cli("aggregate", iteration, check=False)
        self.assertNotEqual(0, failed.returncode)
        self.assertIn("single configuration smoke run", failed.stderr)

        self.run_cli("aggregate", iteration, "--allow-incomplete")
        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertTrue(benchmark["metadata"]["incomplete"])
        self.assertTrue(benchmark["metadata"]["smoke"])
        self.assertEqual([], benchmark["comparisons"])
        markdown = (iteration / "benchmark.md").read_text(encoding="utf-8")
        self.assertIn("No comparative delta", markdown)
        self.assertNotIn("Config B", markdown)

    def test_aggregate_detects_missing_config_per_eval(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", eval_id="E01", eval_dir_name="eval-one", passed=True)
        self.write_run(iteration, "without_skill", eval_id="E02", eval_dir_name="eval-two", passed=True)
        failed = self.run_cli("aggregate", iteration, check=False)
        self.assertNotEqual(0, failed.returncode)
        self.assertIn("E01 missing config(s): without_skill", failed.stderr)
        self.assertIn("E02 missing config(s): with_skill", failed.stderr)

    def test_aggregate_rejects_old_workspace_layout(self):
        iteration = self.root / "evals" / "demo" / "workspace" / "iteration-1"
        self.write_run(iteration, "with_skill", passed=True)

        failed = self.run_cli("aggregate", iteration, "--allow-incomplete", check=False)
        self.assertNotEqual(0, failed.returncode)
        self.assertIn("old canonical workspace layout", failed.stderr)
        failed_report = self.run_cli("report", iteration, check=False)
        self.assertNotEqual(0, failed_report.returncode)
        self.assertIn("old canonical workspace layout", failed_report.stderr)

    def test_aggregate_reads_legacy_split_layout_with_flag(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", passed=True, legacy=True)
        self.write_run(iteration, "without_skill", passed=True, legacy=True)
        out = self.root / "out" / "benchmark.json"
        self.run_cli("aggregate", iteration, "--allow-legacy", "--output", out)
        benchmark = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual({"legacy-split"}, {run["layout"] for run in benchmark["runs"]})
        self.assertEqual({"with_skill": 1, "without_skill": 1}, benchmark["metadata"]["runs_per_configuration"])

    def test_report_writes_static_html_without_pid_file(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", passed=True)
        self.run_cli("aggregate", iteration, "--allow-incomplete")
        previous = self.root / "previous"
        previous.mkdir()
        (previous / "feedback.json").write_text('{"note":"prior feedback"}\n', encoding="utf-8")
        review = self.root / "review.html"

        result = self.run_cli("report", iteration, "--previous-workspace", previous, "--output", review)
        self.assertIn("server: not started", result.stdout)
        html_text = review.read_text(encoding="utf-8")
        self.assertIn("Prompt text for report.", html_text)
        self.assertIn("output from with_skill", html_text)
        self.assertIn("Expectation text", html_text)
        self.assertIn("Benchmark Summary", html_text)
        self.assertIn("Benchmark Analysis", html_text)
        self.assertIn("Tool calls", html_text)
        self.assertIn("Download feedback.json", html_text)
        self.assertIn("textarea data-feedback-run", html_text)
        self.assertIn("feedback.json", html_text)
        self.assertIn("prior feedback", html_text)
        self.assertEqual([], list(self.root.rglob("*.pid")))

    def test_report_previous_iteration_renders_pass_rate_delta_and_previous_outputs(self):
        previous = self.agent_iteration("codex", 1)
        current = self.agent_iteration("codex", 2)
        previous_run = self.write_run(previous, "with_skill", passed=False)
        current_run = self.write_run(current, "with_skill", passed=True)
        (previous_run / "outputs" / "output.md").write_text("previous output\n", encoding="utf-8")
        (current_run / "outputs" / "output.md").write_text("current output\n", encoding="utf-8")
        self.run_cli("aggregate", previous, "--allow-incomplete")
        self.run_cli("aggregate", current, "--allow-incomplete")
        review = self.root / "review-previous.html"

        self.run_cli("report", current, "--previous-iteration", previous, "--output", review)

        html_text = review.read_text(encoding="utf-8")
        self.assertIn("Previous Iteration Comparison", html_text)
        self.assertIn("100.0%", html_text)
        self.assertIn("0.0%", html_text)
        self.assertIn("Previous outputs", html_text)
        self.assertIn("previous output", html_text)
        self.assertIn("current output", html_text)

    def test_report_previous_iteration_auto_and_expectation_deltas(self):
        previous = self.agent_iteration("codex", 1)
        current = self.agent_iteration("codex", 2)
        self.write_run(previous, "with_skill", passed=False)
        self.write_run(current, "with_skill", passed=True)
        self.run_cli("aggregate", previous, "--allow-incomplete")
        self.run_cli("aggregate", current, "--allow-incomplete")
        review = self.root / "review-auto.html"

        self.run_cli("report", current, "--previous-iteration", "auto", "--output", review)

        html_text = review.read_text(encoding="utf-8")
        self.assertIn("Previous Iteration Comparison", html_text)
        self.assertIn("Previous</th>", html_text)
        self.assertIn("fail: Evidence text", html_text)

    def test_aggregate_writes_systematic_failure_diagnostic(self):
        iteration = self.agent_iteration("codex", 1)
        self.write_run(iteration, "with_skill", passed=False)
        self.write_run(iteration, "without_skill", passed=False)

        self.run_cli("aggregate", iteration)

        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        messages = "\n".join(note["message"] for note in benchmark["analysis"]["notes"])
        self.assertIn("Repeated identical failed evidence", messages)
        self.assertIn("prompt/config/input mismatch", messages)

    def test_doctor_reports_pending_and_require_complete_blockers(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)

        info = self.run_cli("doctor", iteration)
        self.assertIn("prepared_runs: 1", info.stdout)
        self.assertIn("grading_material_pending: 1", info.stdout)
        self.assertIn("grading_missing: 1", info.stdout)
        self.assertIn("phase_executor-prepared: 1", info.stdout)

        strict = self.run_cli("doctor", iteration, "--require-complete", check=False)
        self.assertNotEqual(0, strict.returncode)
        self.assertIn("completion_blockers", strict.stdout)
        self.assertIn("grading materials pending", strict.stdout)

    def test_doctor_require_complete_blocks_repeated_known_placeholder_metrics(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        self.record_prepared_run(self.prepared_run_dir(iteration, "with_skill"), seconds=30, tokens=5000)
        self.record_prepared_run(self.prepared_run_dir(iteration, "without_skill"), seconds=30, tokens=5000)

        strict = self.run_cli("doctor", iteration, "--require-complete", check=False)

        self.assertNotEqual(0, strict.returncode)
        self.assertIn("metrics_audit_warning: 2", strict.stdout)
        self.assertIn("repeated known placeholder metrics 30000ms/5000 tokens", strict.stdout)

    def test_prepare_grading_requires_completed_executor_receipt(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")

        failed = self.run_cli("prepare-grading", run_dir, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("executor receipt is required", failed.stderr)
        self.assertFalse((run_dir / "grader_prompt.md").exists())
        self.write_receipt(run_dir)
        self.run_cli("prepare-grading", run_dir)
        self.assertTrue((run_dir / "grader_prompt.md").is_file())

    def test_prepare_grading_one_run_does_not_enable_pending_sibling_grading(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        with_run = self.prepared_run_dir(iteration, "with_skill")
        without_run = self.prepared_run_dir(iteration, "without_skill")
        self.write_receipt(with_run)
        self.run_cli("prepare-grading", with_run)
        self.assertTrue((with_run / "grader_prompt.md").is_file())
        self.assertFalse((without_run / "grader_prompt.md").exists())
        without_manifest = json.loads((without_run / "run_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("pending", without_manifest["grader_material_status"])

        template_failed = self.run_cli("grading-template", without_run, check=False)

        self.assertNotEqual(0, template_failed.returncode)
        self.assertIn("grading materials are not prepared", template_failed.stderr)
        grading = self.root / "pending-sibling-grading.json"
        self.write_json(
            grading,
            {
                "expectations": [
                    {"text": "common assertion", "passed": True, "evidence": "ok"},
                    {"text": "per-eval assertion", "passed": True, "evidence": "ok"},
                ]
            },
        )
        record_failed = self.run_cli("record", without_run, "--grading", grading, check=False)
        self.assertNotEqual(0, record_failed.returncode)
        self.assertIn("grading materials are not prepared", record_failed.stderr)

    def test_aggregate_blocks_current_contract_missing_grading_materials_without_allow_incomplete(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)

        failed = self.run_cli("aggregate", iteration, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("missing grading materials", failed.stderr)
        self.run_cli("aggregate", iteration, "--allow-incomplete")
        benchmark = json.loads((iteration / "benchmark.json").read_text(encoding="utf-8"))
        self.assertTrue(benchmark["metadata"]["incomplete"])

    def test_record_batch_prevalidates_before_writing(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        records = self.root / "records.json"
        self.write_json(
            records,
            {
                "records": [
                    {"run_dir": str(run_dir), "total_tokens": 1, "duration_ms": 2, "output_chars": 3, "finalize": True, "allow_missing_prompt_receipt": True},
                    {"run_dir": str(run_dir), "total_tokens": 4, "duration_ms": 5, "output_chars": 6},
                ]
            },
        )

        failed = self.run_cli("record-batch", records, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("duplicate run_dir", failed.stderr)
        self.assertFalse((run_dir / "timing.json").exists())

    def test_record_batch_rejects_non_positive_metrics_before_writing(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)
        records = self.root / "records-invalid-metrics.json"
        self.write_json(records, {"records": [{"run_dir": str(run_dir), "total_tokens": 0, "duration_ms": 0, "output_chars": 3, "finalize": True}]})

        failed = self.run_cli("record-batch", records, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("non-positive-duration", failed.stderr)
        self.assertIn("non-positive-total-tokens", failed.stderr)
        self.assertFalse((run_dir / "timing.json").exists())

    def test_record_batch_rejects_repeated_known_placeholder_metrics_before_writing(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill,without_skill", "--runs", "1")
        iteration = self.agent_iteration("codex", 1)
        with_run = self.prepared_run_dir(iteration, "with_skill")
        without_run = self.prepared_run_dir(iteration, "without_skill")
        self.write_receipt(with_run)
        self.write_receipt(without_run)
        records = self.root / "records-placeholder-metrics.json"
        self.write_json(
            records,
            {
                "records": [
                    {"run_dir": str(with_run), "total_tokens": 5000, "duration_ms": 30000, "output_chars": 3, "finalize": True},
                    {"run_dir": str(without_run), "total_tokens": 5000, "duration_ms": 30000, "output_chars": 4, "finalize": True},
                ]
            },
        )

        failed = self.run_cli("record-batch", records, check=False)

        self.assertNotEqual(0, failed.returncode)
        self.assertIn("record-batch metric integrity", failed.stderr)
        self.assertIn("30000ms/5000 tokens", failed.stderr)
        self.assertFalse((with_run / "timing.json").exists())
        self.assertFalse((without_run / "timing.json").exists())

    def test_record_batch_records_valid_entries(self):
        suite = self.write_suite()
        self.run_cli("prepare", suite, "--agent", "codex", "--eval", "E01", "--config", "with_skill", "--runs", "1")
        run_dir = self.prepared_run_dir(self.agent_iteration("codex", 1), "with_skill")
        self.write_receipt(run_dir)
        records = self.root / "records-valid.json"
        self.write_json(records, {"records": [{"run_dir": str(run_dir), "total_tokens": 1, "duration_ms": 2, "output_chars": 3, "finalize": True}]})

        self.run_cli("record-batch", records)

        timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
        self.assertEqual(1, timing["total_tokens"])
        self.assertTrue((run_dir / "record_metadata.json").is_file())

    def test_cli_does_not_import_ignored_agents_skill(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(".agents", source)


if __name__ == "__main__":
    unittest.main()
