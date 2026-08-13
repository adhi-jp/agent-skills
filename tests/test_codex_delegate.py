"""Hermetic regression and extension tests for the Codex delegate."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "vibe-orchestrate" / "scripts"
if not SCRIPT_DIR.is_dir():
    SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import codex_delegate as M  # noqa: E402
import delegate_common as C  # noqa: E402


def args(**overrides):
    base = dict(
        codex_binary="codex",
        model="gpt-5.6-sol",
        reasoning_effort="low",
        sandbox="read-only",
        timeout=30.0,
        artifact_dir="/tmp/x",
        result_schema="worker-report-v1",
        print_full_receipt=False,
        manifest_max_files=20000,
        manifest_max_total_bytes=536870912,
        preflight_receipt=None,
        preflight_max_age=1800,
        task_profile="inspect",
        target=["input.txt"],
        mission_file=None,
        mission_stdin=False,
        allowed_write=[],
        env_passthrough=[],
        expected_exact=None,
        cwd="/tmp/work",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


FAKE_PASSTHROUGH = [
    "--env-passthrough", "FAKE_CODEX_PROMPT_CAPTURE",
    "--env-passthrough", "FAKE_CODEX_EXTRA",
    "--env-passthrough", "FAKE_CODEX_REPORTED_FILE",
    "--env-passthrough", "FAKE_CODEX_GIT_MUTATION",
    "--env-passthrough", "FAKE_CODEX_FAIL",
    "--env-passthrough", "FAKE_CODEX_BUILD_BLOAT",
]


def write_fake_tools(bin_dir: Path) -> None:
    git = bin_dir / "git"
    git.write_text(
        """#!/usr/bin/env python3
import os, pathlib, sys
a=sys.argv[1:]
cwd=pathlib.Path.cwd()
if a[:1] == ['init']:
    raise SystemExit(0)
if a == ['rev-parse','--verify','HEAD']:
    if (cwd/'.fake-no-head').exists(): raise SystemExit(1)
    print('a'*40); raise SystemExit(0)
if a == ['symbolic-ref','--quiet','HEAD']:
    print('refs/heads/main'); raise SystemExit(0)
if a and a[0] == 'for-each-ref':
    value='refs/heads/main\\0' + 'a'*40
    if (cwd/'.git/fake-ref-mutated').exists(): value += '\\nrefs/heads/worker\\0' + 'a'*40
    print(value); raise SystemExit(0)
if a == ['ls-files','--stage','-z']:
    value='100644 ' + 'b'*40 + ' 0\\tinput.txt\\0'
    if (cwd/'.git/fake-index-mutated').exists(): value += '100644 ' + 'c'*40 + ' 0\\tstaged.txt\\0'
    sys.stdout.write(value); raise SystemExit(0)
if a == ['ls-files','-v','-z']:
    sys.stdout.write('H input.txt\\0'); raise SystemExit(0)
if a == ['diff','--name-only','-z','HEAD']:
    if (cwd/'.fake-dirty').exists(): sys.stdout.write('input.txt\\0')
    if (cwd/'result.txt').exists() and os.environ.get('FAKE_CODEX_BUILD_BLOAT') == '1':
        sys.stdout.write('result.txt\\0')
    raise SystemExit(0)
if a == ['ls-files','--others','--exclude-standard','-z']:
    raise SystemExit(0)
if a[:3] == ['ls-files','-z','--']:
    raise SystemExit(0)
if a[:2] == ['check-ignore','-q']:
    raise SystemExit(0 if a[-1] == 'build' else 1)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    git.chmod(0o755)
    codex = bin_dir / "codex"
    codex.write_text(
        """#!/usr/bin/env python3
import json, os, pathlib, sys
a=sys.argv[1:]
if a == ['--version']:
    print('codex-cli fake-1.0'); raise SystemExit(0)
if a == ['login','status']:
    print('Logged in using fake auth'); raise SystemExit(0)
def value(flag): return a[a.index(flag)+1]
out=pathlib.Path(value('-o'))
prompt=sys.stdin.read()
capture=os.environ.get('FAKE_CODEX_PROMPT_CAPTURE')
if capture: pathlib.Path(capture).write_text(prompt)
cwd=pathlib.Path.cwd()
read_only=value('-s') == 'read-only'
if (cwd/'probe-marker.txt').exists():
    files=[]
    if 'create probe-output.txt' in prompt and not read_only:
        (cwd/'probe-output.txt').write_text('CODEX_CANARY_WRITE\\n')
        files=['probe-output.txt']
else:
    files=[]
    if not read_only:
        (cwd/'result.txt').write_text('fake-result\\n')
        files=['result.txt']
        if os.environ.get('FAKE_CODEX_BUILD_BLOAT') == '1':
            build=cwd/'build'; build.mkdir(exist_ok=True)
            for i in range(32): (build/f'generated-{i}.txt').write_text('generated\\n')
    if os.environ.get('FAKE_CODEX_EXTRA') == '1':
        (cwd/'extra.log').write_text('scope violation\\n')
        files.append('extra.log')
    if os.environ.get('FAKE_CODEX_REPORTED_FILE') == '1':
        files.append('claimed.txt')
    mutation=os.environ.get('FAKE_CODEX_GIT_MUTATION')
    if mutation:
        (cwd/'.git').mkdir(exist_ok=True)
        (cwd/'.git'/('fake-'+mutation+'-mutated')).write_text('mutated\\n')
    if os.environ.get('FAKE_CODEX_FAIL') == '1':
        print('fake provider failure', file=sys.stderr)
        raise SystemExit(1)
report={'files':files,'compile':{'status':'SKIPPED','detail':'fake'},'decisions':[],'blockers':[]}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report))
print(json.dumps({'type':'thread.started','thread_id':'fake-thread'}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}))
""",
        encoding="utf-8",
    )
    codex.chmod(0o755)


def fake_env(root: Path) -> tuple[dict[str, str], Path]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    write_fake_tools(bin_dir)
    state = root / "codex-home"
    state.mkdir()
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["CODEX_HOME"] = str(state)
    return env, bin_dir


class CodexDelegateTests(unittest.TestCase):
    def test_run_parser_exposes_closed_and_mission_task_inputs(self):
        actions = M.build_parser()._subparsers._group_actions[0].choices["run"]._actions
        destinations = {action.dest for action in actions}
        self.assertIn("task_profile", destinations)
        self.assertIn("target", destinations)
        self.assertIn("mission_file", destinations)
        self.assertIn("mission_stdin", destinations)
        self.assertIn("allowed_write", destinations)
        self.assertIn("manifest_exclude", destinations)
        self.assertNotIn("prompt_file", destinations)
        self.assertFalse(hasattr(M, "read_prompt"))
        self.assertFalse(hasattr(M, "invoke"))
        self.assertNotIn("inherit_user_config", destinations)
        self.assertNotIn("allow_web", destinations)
        self.assertNotIn("full_runtime", destinations)
        sandbox = next(action for action in actions if action.dest == "sandbox")
        self.assertEqual(sandbox.choices, ("read-only", "workspace-write"))

    def test_global_approval_precedes_exec_and_prompt_is_stdin_marker(self):
        argv = M.build_argv(args(), output_last=Path("/tmp/last"), output_schema=Path("/tmp/schema"), ephemeral=True)
        self.assertEqual(argv[:4], ["codex", "-a", "never", "--disable"])
        self.assertLess(argv.index("-a"), argv.index("exec"))
        self.assertEqual(argv[-1], "-")
        self.assertIn("--json", argv)
        self.assertIn("--ignore-rules", argv)
        self.assertIn("--ignore-user-config", argv)
        overrides = [argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "-c"]
        self.assertIn("project_doc_max_bytes=0", overrides)
        self.assertIn("project_doc_fallback_filenames=[]", overrides)
        self.assertIn('web_search="disabled"', overrides)

    def test_private_runner_sink_rejects_raw_prompt_text(self):
        with self.assertRaises(TypeError):
            M._invoke_adapter_prompt(
                args(),
                prompt="OUTSIDER-CONTENT",  # type: ignore[arg-type]
                cwd=Path("/unused"),
                artifact_dir=Path("/unused"),
                expected_exact=None,
                ephemeral=True,
            )

    def test_removed_prompt_file_option_fails_during_argument_parsing(self):
        with self.assertRaises(SystemExit):
            M.build_parser().parse_args(
                [
                    "run",
                    "--model", "fake-model",
                    "--artifact-dir", "/tmp/artifacts",
                    "--cwd", "/tmp/work",
                    "--task-profile", "inspect",
                    "--target", "input.txt",
                    "--prompt-file", "issue.md",
                ]
            )

    def test_minimal_profile_disables_optional_features(self):
        argv = M.build_argv(args(), output_last=Path("/tmp/last"), output_schema=None, ephemeral=True)
        disabled = [argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "--disable"]
        self.assertEqual(disabled, list(M.MINIMAL_FEATURES))

    def test_failure_classification(self):
        cases = [
            ("Error: failed to initialize in-process app-server client: Read-only file system", False, 1, "codex_state_not_writable"),
            ("Could not resolve host chatgpt.com", False, 1, "network_unavailable"),
            ("error: unexpected argument -a", False, 2, "cli_contract_mismatch"),
            ("", True, None, "timeout"),
            ("", False, 0, "receipt_mismatch"),
        ]
        for stderr, timed, exit_code, expected in cases:
            self.assertEqual(M.classify_failure(stderr, timed_out=timed, exit_code=exit_code, receipt_ok=False), expected)

    def test_fingerprint_covers_transport_contract_and_both_adapter_files(self):
        fp = M.fingerprint(args(), "codex-cli 0.146.0")
        self.assertEqual(fp["adapter_schema"], 12)
        self.assertEqual(set(fp["adapter_files"]), {"codex_delegate.py", "delegate_common.py"})
        self.assertEqual(fp["adapter_files"]["codex_delegate.py"], M.sha256_file(Path(M.__file__)))
        for key in ("model", "reasoning_effort", "sandbox", "runtime_profile", "result_schema", "rules_profile", "project_instructions", "web_search", "workspace_write_network", "write_allowlist_required", "env_passthrough", "codex_home", "manifest_max_total_bytes", "manifest_exclusions", "external_task_contract", "mission_contract"):
            self.assertIn(key, fp)
        self.assertEqual(fp["runtime_profile"], "minimal")
        self.assertEqual(fp["rules_profile"], "disabled")
        self.assertEqual(fp["project_instructions"], "disabled")
        self.assertEqual(fp["web_search"], "disabled")
        self.assertEqual(fp["workspace_write_network"], "disabled")
        self.assertFalse(fp["write_allowlist_required"])
        self.assertTrue(
            M.fingerprint(args(sandbox="workspace-write"), "codex-cli 0.146.0")[
                "write_allowlist_required"
            ]
        )
        changed = M.fingerprint(args(model="different-model"), "codex-cli 0.146.0")
        self.assertNotEqual(M.fingerprint_digest(fp), M.fingerprint_digest(changed))
        passthrough_changed = M.fingerprint(
            args(env_passthrough=["FAKE_CODEX_EXTRA"]), "codex-cli 0.146.0"
        )
        self.assertNotEqual(M.fingerprint_digest(fp), M.fingerprint_digest(passthrough_changed))

    def test_git_metadata_snapshot_detects_index_and_ref_mutation(self):
        state = {"index": b"base", "refs": b"main"}

        def run(_cwd, *a):
            outputs = {
                ("rev-parse", "--verify", "HEAD"): b"head\n",
                ("symbolic-ref", "--quiet", "HEAD"): b"refs/heads/main\n",
                ("ls-files", "--stage", "-z"): state["index"],
                ("ls-files", "-v", "-z"): b"H x\0",
            }
            if a and a[0] == "for-each-ref":
                return subprocess.CompletedProcess(["git"], 0, state["refs"], b"")
            return subprocess.CompletedProcess(["git"], 0, outputs[a], b"")

        with mock.patch.object(C, "run_git", side_effect=run):
            baseline = M.git_metadata_snapshot(Path("/unused"))
            state["index"] = b"staged"
            self.assertNotEqual(M.git_metadata_snapshot(Path("/unused")), baseline)
            state.update(index=b"base", refs=b"mainworker")
            self.assertNotEqual(M.git_metadata_snapshot(Path("/unused")), baseline)

    def test_filesystem_manifest_detects_mode_and_empty_directory(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            tracked = work / "tracked.txt"
            tracked.write_text("same bytes\n", encoding="utf-8")
            baseline, error = M.filesystem_manifest(work, 20, 1000)
            self.assertIsNone(error)
            tracked.chmod(0o755)
            changed, _ = M.filesystem_manifest(work, 20, 1000)
            self.assertEqual(M.manifest_changed_paths(baseline, changed), ["tracked.txt"])
            tracked.chmod(0o644)
            restored, _ = M.filesystem_manifest(work, 20, 1000)
            (work / "empty").mkdir()
            directory_changed, _ = M.filesystem_manifest(work, 20, 1000)
            self.assertEqual(M.manifest_changed_paths(restored, directory_changed), ["empty"])

    def test_artifact_dir_inside_cwd_is_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            artifact = work / "artifacts"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(M.command_run(args(cwd=str(work), artifact_dir=str(artifact))), 2)
            self.assertFalse(artifact.exists())

    def test_worker_report_validation(self):
        good = json.dumps({"files": ["x"], "compile": {"status": "SKIPPED", "detail": "n/a"}, "decisions": [], "blockers": []})
        self.assertTrue(M.validate_structured_last(args(), good)[0])
        bad = json.dumps({"files": ["x"], "compile": {"status": "SKIPPED", "detail": "n/a"}, "decisions": []})
        self.assertFalse(M.validate_structured_last(args(), bad)[0])

    def test_jsonl_parse_requires_terminal_event(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            path.write_text(json.dumps({"type": "thread.started", "thread_id": "t-1"}) + "\n" + json.dumps({"type": "turn.completed", "usage": {"input_tokens": 3}}) + "\n", encoding="utf-8")
            parsed = M.parse_jsonl(path)
            self.assertEqual(parsed["thread_id"], "t-1")
            self.assertTrue(parsed["turn_completed"])
            self.assertFalse(parsed["turn_failed"])

    def test_preflight_receipt_negatives(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(M, "utc_epoch", return_value=1000):
            path = Path(td) / "receipt.json"
            a = args(preflight_receipt=str(path), preflight_max_age=100)
            fp = M.fingerprint(a, "fake-version")
            cases = [
                ({"ok": True, "created_at_epoch": 899, "fingerprint_sha256": M.fingerprint_digest(fp)}, "age"),
                ({"ok": True, "created_at_epoch": 1006, "fingerprint_sha256": M.fingerprint_digest(fp)}, "future"),
                ({"ok": False, "created_at_epoch": 1000}, "not successful"),
                ({"ok": True, "created_at_epoch": 1000, "fingerprint_sha256": "bad"}, "fingerprint"),
            ]
            for receipt, expected in cases:
                path.write_text(json.dumps(receipt), encoding="utf-8")
                ok, _, reason = M.validate_preflight(a, "fake-version")
                self.assertFalse(ok)
                self.assertIn(expected, reason)
            path.write_text("{bad", encoding="utf-8")
            self.assertFalse(M.validate_preflight(a, "fake-version")[0])

    def test_preflight_receipt_accepts_bounded_clock_rollback(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(M, "utc_epoch", return_value=1000):
            path = Path(td) / "receipt.json"
            a = args(preflight_receipt=str(path), preflight_max_age=100)
            base = {
                "ok": True,
                "kind": "codex_delegate_preflight",
                "fingerprint_sha256": M.fingerprint_digest(
                    M.fingerprint(a, "fake-version")
                ),
                "file_probe_ok": True,
            }
            for created_at in (1000, 1001, 1005):
                path.write_text(
                    json.dumps({**base, "created_at_epoch": created_at}),
                    encoding="utf-8",
                )
                ok, _, reason = M.validate_preflight(a, "fake-version")
                self.assertTrue(ok, reason)

    def test_preflight_rejects_run_kind_and_missing_successful_file_probe(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "receipt.json"
            a = args(preflight_receipt=str(path))
            digest = M.fingerprint_digest(M.fingerprint(a, "fake-version"))
            base = {
                "ok": True,
                "created_at_epoch": M.utc_epoch(),
                "fingerprint_sha256": digest,
                "file_probe_ok": True,
            }
            path.write_text(json.dumps({**base, "kind": "codex_delegate_run"}), encoding="utf-8")
            ok, _, reason = M.validate_preflight(a, "fake-version")
            self.assertFalse(ok)
            self.assertEqual(reason, "preflight receipt kind is not a preflight receipt")
            path.write_text(
                json.dumps({**base, "kind": "codex_delegate_preflight", "file_probe_ok": False}),
                encoding="utf-8",
            )
            ok, _, reason = M.validate_preflight(a, "fake-version")
            self.assertFalse(ok)
            self.assertEqual(reason, "preflight receipt lacks a successful canary file probe")

    def test_command_level_setup_rejections(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env, _ = fake_env(root)
            script = str(Path(M.__file__).resolve())
            common = [
                sys.executable, "-B", script, "--model", "fake-model", "--sandbox",
                "read-only", "--result-schema", "worker-report-v1",
            ]
            preflight = root / "preflight"
            pre = subprocess.run(
                common[:3] + ["preflight"] + common[3:] + ["--artifact-dir", str(preflight)],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            receipt = preflight / "receipt.json"

            def run_case(name: str, cwd: Path, extra: list[str] | None = None):
                artifact = root / f"run-{name}"
                argv = common[:3] + ["run"] + common[3:] + [
                    "--artifact-dir", str(artifact), "--cwd", str(cwd),
                    "--preflight-receipt", str(receipt), "--task-profile", "inspect",
                    "--target", "input.txt",
                ] + (extra or [])
                completed = subprocess.run(argv, env=env, capture_output=True, text=True)
                return completed, json.loads((artifact / "receipt.json").read_text())

            dirty = root / "dirty"
            dirty.mkdir()
            (dirty / "input.txt").write_text("input\n", encoding="utf-8")
            (dirty / ".fake-dirty").write_text("marker\n", encoding="utf-8")
            completed, report = run_case("dirty", dirty)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(report["failure_kind"], "worktree_not_clean")

            no_head = root / "no-head"
            no_head.mkdir()
            (no_head / ".fake-no-head").write_text("marker\n", encoding="utf-8")
            completed, report = run_case("no-head", no_head)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(report["failure_kind"], "git_baseline_unavailable")

            completed, report = run_case("invalid-cwd", root / "missing")
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(report["failure_kind"], "cwd_invalid")

            invalid_task = root / "invalid-task"
            invalid_task.mkdir()
            (invalid_task / "input.txt").write_text("input\n", encoding="utf-8")
            completed, report = run_case(
                "invalid-task", invalid_task, extra=["--task-profile", "repair"]
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(report["failure_kind"], "task_contract_invalid")

            limited = common + ["--manifest-max-files", "1"]
            limited_preflight = root / "limited-preflight"
            pre = subprocess.run(
                limited[:3] + ["preflight"] + limited[3:] + ["--artifact-dir", str(limited_preflight)],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            over = root / "over-ceiling"
            over.mkdir()
            (over / "input.txt").write_text("input\n", encoding="utf-8")
            over_artifact = root / "run-over-ceiling"
            completed = subprocess.run(
                limited[:3] + ["run"] + limited[3:] + [
                    "--artifact-dir", str(over_artifact), "--cwd", str(over),
                    "--preflight-receipt", str(limited_preflight / "receipt.json"),
                    "--task-profile", "inspect", "--target", "input.txt",
                ],
                env=env, input="task\n", capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 2)
            report = json.loads((over_artifact / "receipt.json").read_text())
            self.assertEqual(report["failure_kind"], "manifest_unavailable")
            self.assertIn("file count exceeds 1", report["reason"])

    def test_read_only_git_metadata_mutation_and_dual_failure_are_visible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env, _ = fake_env(root)
            script = str(Path(M.__file__).resolve())
            common = [
                sys.executable, "-B", script, "--model", "fake-model", "--sandbox",
                "read-only", "--result-schema", "worker-report-v1",
            ] + FAKE_PASSTHROUGH
            preflight = root / "preflight"
            pre = subprocess.run(
                common[:3] + ["preflight"] + common[3:] + ["--artifact-dir", str(preflight)],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)

            def invoke(name: str, mutation: str, fail: bool = False):
                work = root / f"work-{name}"
                work.mkdir()
                (work / ".git").mkdir()
                (work / "input.txt").write_text("input\n", encoding="utf-8")
                run_env = env.copy()
                run_env["FAKE_CODEX_GIT_MUTATION"] = mutation
                if fail:
                    run_env["FAKE_CODEX_FAIL"] = "1"
                artifact = root / f"run-{name}"
                completed = subprocess.run(
                    common[:3] + ["run"] + common[3:] + [
                        "--artifact-dir", str(artifact), "--cwd", str(work),
                        "--preflight-receipt", str(preflight / "receipt.json"),
                        "--task-profile", "inspect", "--target", "input.txt",
                    ],
                    env=run_env, input="inspect\n", capture_output=True, text=True,
                )
                return completed, json.loads((artifact / "receipt.json").read_text())

            completed, report = invoke("index", "index")
            self.assertEqual(completed.returncode, 5)
            self.assertEqual(report["failure_kind"], "scope_violation")
            self.assertFalse(report["change_manifest"]["git_metadata_unchanged"])
            self.assertEqual(json.loads(completed.stdout)["scope_ok"], False)

            completed, report = invoke("ref-failure", "ref", fail=True)
            self.assertEqual(completed.returncode, 5)
            self.assertEqual(report["failure_kind"], "provider_failed")
            self.assertFalse(report["change_manifest"]["scope_ok"])
            self.assertEqual(json.loads(completed.stdout)["scope_ok"], False)

    def test_shared_module_byte_change_invalidates_preflight_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env, _ = fake_env(root)
            copied = root / "scripts"
            copied.mkdir()
            shutil.copyfile(Path(M.__file__), copied / "codex_delegate.py")
            shutil.copyfile(Path(C.__file__), copied / "delegate_common.py")
            preflight = root / "preflight"
            common = [sys.executable, "-B", str(copied / "codex_delegate.py"), "--model", "fake", "--sandbox", "read-only", "--result-schema", "worker-report-v1"]
            pre = subprocess.run(common[:3] + ["preflight"] + common[3:] + ["--artifact-dir", str(preflight)], env=env, capture_output=True, text=True)
            self.assertEqual(pre.returncode, 0, pre.stderr)
            with (copied / "delegate_common.py").open("a", encoding="utf-8") as handle:
                handle.write("\n# byte change\n")
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            run = subprocess.run(common[:3] + ["run"] + common[3:] + ["--artifact-dir", str(root / "run"), "--cwd", str(work), "--preflight-receipt", str(preflight / "receipt.json"), "--task-profile", "inspect", "--target", "input.txt"], env=env, input="OUTSIDER-CONTENT\n", capture_output=True, text=True)
            self.assertEqual(run.returncode, 4, run.stderr)
            self.assertEqual(json.loads((root / "run" / "receipt.json").read_text())["failure_kind"], "preflight_required")

    def test_fake_codex_integration_uses_closed_prompt_and_rejects_scope_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env, _ = fake_env(root)
            preflight = root / "preflight"
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            common = [sys.executable, "-B", str(Path(M.__file__).resolve()), "--model", "fake-model", "--sandbox", "read-only", "--result-schema", "worker-report-v1"] + FAKE_PASSTHROUGH
            pre = subprocess.run(common[:3] + ["preflight"] + common[3:] + ["--artifact-dir", str(preflight)], env=env, capture_output=True, text=True)
            self.assertEqual(pre.returncode, 0, pre.stderr)
            capture = root / "received-prompt.txt"
            env["FAKE_CODEX_PROMPT_CAPTURE"] = str(capture)
            accepted = root / "accepted"
            run_args = common[:3] + ["run"] + common[3:] + ["--artifact-dir", str(accepted), "--cwd", str(work), "--task-profile", "review", "--target", "input.txt", "--preflight-receipt", str(preflight / "receipt.json")]
            ok = subprocess.run(
                run_args, env=env, input="OUTSIDER-CONTENT\n", capture_output=True, text=True
            )
            receipt = json.loads((accepted / "receipt.json").read_text())
            self.assertEqual(ok.returncode, 0, f"{ok.stderr}\n{receipt}")
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["fingerprint_sha256"], receipt["preflight_fingerprint_sha256"])
            self.assertEqual(receipt["preflight_receipt_sha256"], M.sha256_file(preflight / "receipt.json"))
            self.assertEqual(set(receipt["fingerprint"]["adapter_files"]), {"codex_delegate.py", "delegate_common.py"})
            invocation = receipt["invocation"]
            self.assertIn("argv", invocation)
            received = capture.read_text(encoding="utf-8")
            self.assertEqual(received, C.render_external_task_prompt("review", ["input.txt"]).text)
            self.assertNotIn("OUTSIDER-CONTENT", received)
            self.assertEqual(invocation["prompt"]["origin"], "adapter-generated")
            self.assertEqual(invocation["prompt"]["contract"], C.EXTERNAL_TASK_CONTRACT)
            self.assertEqual(receipt["task_contract"]["targets"], ["input.txt"])
            self.assertEqual(invocation["event_types"], ["thread.started", "turn.completed"])
            self.assertFalse(invocation["stderr"]["truncated"])
            self.assertIn("baseline_git_metadata", receipt["change_manifest"])
            self.assertIn("final_git_metadata", receipt["change_manifest"])
            bad_env = env.copy()
            bad_env["FAKE_CODEX_EXTRA"] = "1"
            rejected = root / "rejected"
            bad_args = [str(rejected) if value == str(accepted) else value for value in run_args]
            bad = subprocess.run(bad_args, env=bad_env, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 5)
            self.assertEqual(json.loads(bad.stdout)["scope_ok"], False)
            rejected_receipt = json.loads((rejected / "receipt.json").read_text())
            self.assertEqual(rejected_receipt["failure_kind"], "scope_violation")
            self.assertEqual(rejected_receipt["change_manifest"]["actual_changed_paths"], ["extra.log"])

            report_env = env.copy()
            report_env["FAKE_CODEX_REPORTED_FILE"] = "1"
            report_rejected = root / "report-rejected"
            report_args = [
                str(report_rejected) if value == str(accepted) else value for value in run_args
            ]
            bad_report = subprocess.run(
                report_args, env=report_env, capture_output=True, text=True
            )
            self.assertEqual(bad_report.returncode, 5)
            report_receipt = json.loads((report_rejected / "receipt.json").read_text())
            self.assertFalse(report_receipt["change_manifest"]["reported_files_match"])
            self.assertEqual(report_receipt["change_manifest"]["actual_changed_paths"], [])

    def test_workspace_write_mission_run_enforces_allowlist_and_envelope(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env, _ = fake_env(root)
            script = str(Path(M.__file__).resolve())
            common = [
                sys.executable, "-B", script, "--model", "fake-model", "--sandbox",
                "workspace-write", "--result-schema", "worker-report-v1",
            ] + FAKE_PASSTHROUGH
            preflight = root / "preflight"
            pre = subprocess.run(
                common[:3] + ["preflight"] + common[3:] + ["--artifact-dir", str(preflight)],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            self.assertTrue(json.loads((preflight / "receipt.json").read_text())["file_probe_ok"])

            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            mission = root / "mission.md"
            mission.write_text("Edit result.txt to record the fake result.\n", encoding="utf-8")
            capture = root / "received-prompt.txt"
            env["FAKE_CODEX_PROMPT_CAPTURE"] = str(capture)
            accepted = root / "accepted"
            run_args = common[:3] + ["run"] + common[3:] + [
                "--artifact-dir", str(accepted), "--cwd", str(work),
                "--mission-file", str(mission), "--allowed-write", "result.txt",
                "--preflight-receipt", str(preflight / "receipt.json"),
            ]
            ok = subprocess.run(run_args, env=env, capture_output=True, text=True)
            receipt = json.loads((accepted / "receipt.json").read_text())
            self.assertEqual(ok.returncode, 0, f"{ok.stderr}\n{receipt}")
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["task_contract"]["contract"], C.MISSION_CONTRACT)
            self.assertEqual(receipt["task_contract"]["allowed_write_paths"], ["result.txt"])
            invocation = receipt["invocation"]
            self.assertEqual(invocation["prompt"]["origin"], "coordinator-mission")
            self.assertIn("sandbox_workspace_write.network_access=false", invocation["argv"])
            received = capture.read_text(encoding="utf-8")
            self.assertIn("Edit result.txt to record the fake result.", received)
            self.assertIn("<<<mission ", received)
            self.assertIn('["result.txt"]', received)
            self.assertIn("untrusted data", received)
            self.assertEqual(
                (accepted / "mission.txt").read_text(encoding="utf-8"),
                mission.read_text(encoding="utf-8"),
            )
            manifest = receipt["change_manifest"]
            self.assertEqual(manifest["actual_changed_paths"], ["result.txt"])
            self.assertEqual(manifest["out_of_scope_paths"], [])
            self.assertTrue(manifest["scope_ok"])

            bad_env = env.copy()
            bad_env["FAKE_CODEX_EXTRA"] = "1"
            rejected = root / "rejected"
            bad_args = [str(rejected) if value == str(accepted) else value for value in run_args]
            bad = subprocess.run(bad_args, env=bad_env, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 5)
            bad_receipt = json.loads((rejected / "receipt.json").read_text())
            self.assertEqual(bad_receipt["failure_kind"], "scope_violation")
            self.assertEqual(bad_receipt["change_manifest"]["out_of_scope_paths"], ["extra.log"])

            both = root / "both"
            both_args = [str(both) if value == str(accepted) else value for value in run_args]
            both_args += ["--task-profile", "inspect", "--target", "input.txt"]
            mixed = subprocess.run(both_args, env=env, capture_output=True, text=True)
            self.assertEqual(mixed.returncode, 2)
            both_receipt = json.loads((both / "receipt.json").read_text())
            self.assertEqual(both_receipt["failure_kind"], "task_contract_invalid")
            self.assertIn("exactly one task input", both_receipt["reason"])

            missing = root / "missing-allowlist"
            missing_args = [
                value
                for value in [str(missing) if value == str(accepted) else value for value in run_args]
                if value not in ("--allowed-write", "result.txt")
            ]
            no_allow = subprocess.run(missing_args, env=env, capture_output=True, text=True)
            self.assertEqual(no_allow.returncode, 2)
            missing_receipt = json.loads((missing / "receipt.json").read_text())
            self.assertEqual(missing_receipt["failure_kind"], "write_allowlist_required")

    def test_workspace_write_manifest_exclusion_and_degraded_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env, _ = fake_env(root)
            script = str(Path(M.__file__).resolve())
            common = [
                sys.executable, "-B", script, "--model", "fake-model", "--sandbox",
                "workspace-write", "--result-schema", "worker-report-v1",
            ] + FAKE_PASSTHROUGH
            preflight = root / "preflight"
            pre = subprocess.run(
                common[:3] + ["preflight"] + common[3:] + ["--artifact-dir", str(preflight)],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            mission = root / "mission.md"
            mission.write_text("Edit result.txt and generate disposable build output.\n")

            def run_case(name: str, extra: list[str]):
                work = root / f"work-{name}"
                work.mkdir()
                (work / "input.txt").write_text("input\n")
                artifact = root / f"run-{name}"
                case_preflight = root / f"preflight-{name}"
                case_pre = subprocess.run(
                    common[:3] + ["preflight"] + common[3:] + [
                        "--artifact-dir", str(case_preflight)
                    ] + extra,
                    env=env, capture_output=True, text=True,
                )
                self.assertEqual(case_pre.returncode, 0, case_pre.stderr)
                run_env = env.copy()
                run_env["FAKE_CODEX_BUILD_BLOAT"] = "1"
                completed = subprocess.run(
                    common[:3] + ["run"] + common[3:] + [
                        "--artifact-dir", str(artifact), "--cwd", str(work),
                        "--mission-file", str(mission), "--allowed-write", "result.txt",
                        "--preflight-receipt", str(case_preflight / "receipt.json"),
                    ] + extra,
                    env=run_env, capture_output=True, text=True,
                )
                return completed, json.loads((artifact / "receipt.json").read_text())

            excluded, receipt = run_case("excluded", ["--manifest-exclude", "build"])
            self.assertEqual(excluded.returncode, 0, receipt)
            self.assertEqual(receipt["change_manifest"]["manifest_exclusions"], ["build"])
            self.assertEqual(receipt["change_manifest"]["reconciliation_mode"], "filesystem_manifest")

            degraded, receipt = run_case("degraded", ["--manifest-max-files", "10"])
            self.assertEqual(degraded.returncode, 0, receipt)
            self.assertFalse(receipt["change_manifest"]["manifest_ok"])
            self.assertTrue(receipt["change_manifest"]["degraded_reconciliation"])
            self.assertEqual(receipt["change_manifest"]["reconciliation_mode"], "vcs_degraded")

            read_preflight = root / "read-preflight"
            read_common = [
                sys.executable, "-B", script, "--model", "fake-model", "--sandbox",
                "read-only", "--result-schema", "worker-report-v1",
            ] + FAKE_PASSTHROUGH
            pre = subprocess.run(
                read_common[:3] + ["preflight"] + read_common[3:] + [
                    "--artifact-dir", str(read_preflight), "--manifest-exclude", "build"
                ], env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            work = root / "read-work"; work.mkdir()
            (work / "input.txt").write_text("input\n")
            artifact = root / "read-run"
            denied = subprocess.run(
                read_common[:3] + ["run"] + read_common[3:] + [
                    "--artifact-dir", str(artifact), "--cwd", str(work),
                    "--task-profile", "inspect", "--target", "input.txt",
                    "--manifest-exclude", "build",
                    "--preflight-receipt", str(read_preflight / "receipt.json"),
                ], env=env, capture_output=True, text=True,
            )
            self.assertEqual(denied.returncode, 2)
            self.assertIn(
                "workspace-write",
                json.loads((artifact / "receipt.json").read_text())["reason"],
            )

    def test_env_minimization_blocks_unlisted_variables(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env, _ = fake_env(root)
            script = str(Path(M.__file__).resolve())
            common = [
                sys.executable, "-B", script, "--model", "fake-model", "--sandbox",
                "workspace-write", "--result-schema", "worker-report-v1",
            ]
            preflight = root / "preflight"
            pre = subprocess.run(
                common[:3] + ["preflight"] + common[3:] + ["--artifact-dir", str(preflight)],
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            mission = root / "mission.md"
            mission.write_text("Edit result.txt only.\n", encoding="utf-8")
            env["FAKE_CODEX_EXTRA"] = "1"
            artifact = root / "run"
            run = subprocess.run(
                common[:3] + ["run"] + common[3:] + [
                    "--artifact-dir", str(artifact), "--cwd", str(work),
                    "--mission-file", str(mission), "--allowed-write", "result.txt",
                    "--preflight-receipt", str(preflight / "receipt.json"),
                ],
                env=env, capture_output=True, text=True,
            )
            receipt = json.loads((artifact / "receipt.json").read_text())
            self.assertEqual(run.returncode, 0, f"{run.stderr}\n{receipt}")
            self.assertEqual(receipt["change_manifest"]["actual_changed_paths"], ["result.txt"])

    def test_workspace_write_requires_worker_report_schema(self):
        completed = subprocess.run(
            [
                sys.executable, "-B", str(Path(M.__file__).resolve()), "run",
                "--model", "fake-model", "--sandbox", "workspace-write",
                "--artifact-dir", "/tmp/unused-artifacts", "--cwd", "/tmp/unused-work",
            ],
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("worker-report-v1", completed.stderr)


if __name__ == "__main__":
    unittest.main()
