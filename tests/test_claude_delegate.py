"""Hermetic contract and integration tests for the Claude delegate."""
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

import claude_delegate as M  # noqa: E402
import delegate_common as C  # noqa: E402


def args(**overrides):
    base = dict(
        claude_binary="claude",
        model="fake-claude",
        effort="low",
        profile="read-only",
        timeout=30.0,
        artifact_dir="/tmp/x",
        result_schema="none",
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
    "--env-passthrough", "FAKE_CLAUDE_PROMPT_CAPTURE",
    "--env-passthrough", "FAKE_CLAUDE_WRITE",
    "--env-passthrough", "FAKE_CLAUDE_EXTRA",
    "--env-passthrough", "FAKE_CLAUDE_REPORTED_FILE",
    "--env-passthrough", "FAKE_CLAUDE_FAIL",
    "--env-passthrough", "FAKE_CLAUDE_BUILD_BLOAT",
]


def result_object(**overrides):
    value = {
        "is_error": False,
        "subtype": "success",
        "terminal_reason": "completed",
        "result": "done",
        "permission_denials": [],
        "usage": {"input_tokens": 4, "output_tokens": 2},
        "session_id": "fake-session",
    }
    value.update(overrides)
    return value


def write_fake_tools(bin_dir: Path) -> None:
    git = bin_dir / "git"
    git.write_text(
        """#!/usr/bin/env python3
import os, pathlib, sys
a=sys.argv[1:]
if a[:1] == ['init']: raise SystemExit(0)
if a == ['rev-parse','--verify','HEAD']: print('a'*40); raise SystemExit(0)
if a == ['symbolic-ref','--quiet','HEAD']: print('refs/heads/main'); raise SystemExit(0)
if a and a[0] == 'for-each-ref': print('refs/heads/main\\0'+'a'*40); raise SystemExit(0)
if a == ['ls-files','--stage','-z']: sys.stdout.write('100644 '+'b'*40+' 0\\tinput.txt\\0'); raise SystemExit(0)
if a == ['ls-files','-v','-z']: sys.stdout.write('H input.txt\\0'); raise SystemExit(0)
if a == ['diff','--name-only','-z','HEAD']:
    if (pathlib.Path.cwd()/'result.txt').exists() and os.environ.get('FAKE_CLAUDE_BUILD_BLOAT') == '1':
        sys.stdout.write('result.txt\\0')
    raise SystemExit(0)
if a == ['ls-files','--others','--exclude-standard','-z']: raise SystemExit(0)
if a[:3] == ['ls-files','-z','--']: raise SystemExit(0)
if a[:2] == ['check-ignore','-q']: raise SystemExit(0 if a[-1] == 'build' else 1)
raise SystemExit(2)
""",
        encoding="utf-8",
    )
    git.chmod(0o755)
    claude = bin_dir / "claude"
    claude.write_text(
        """#!/usr/bin/env python3
import json, os, pathlib, sys
a=sys.argv[1:]
if a == ['--version']:
    print('2.1.223 (Claude Code fake)'); raise SystemExit(0)
if a == ['auth','status']:
    print(json.dumps({'loggedIn':True,'authMethod':'fake'})); raise SystemExit(0)
prompt=sys.stdin.read()
capture=os.environ.get('FAKE_CLAUDE_PROMPT_CAPTURE')
if capture: pathlib.Path(capture).write_text(prompt)
cwd=pathlib.Path.cwd()
schema='--json-schema' in a
write_profile='--permission-mode' in a
if (cwd/'probe-marker.txt').exists():
    files=[]
    if write_profile:
        (cwd/'probe-output.txt').write_bytes(b'CLAUDE_CANARY_WRITE')
        files=['probe-output.txt']
    plain='CLAUDE_DELEGATE_READY'
else:
    files=[]
    if write_profile:
        (cwd/'result.txt').write_text('fake-result\\n')
        files=['result.txt']
        if os.environ.get('FAKE_CLAUDE_BUILD_BLOAT') == '1':
            build=cwd/'build'; build.mkdir(exist_ok=True)
            for i in range(32): (build/f'generated-{i}.txt').write_text('generated\\n')
        if os.environ.get('FAKE_CLAUDE_EXTRA') == '1':
            (cwd/'extra.log').write_text('scope violation\\n')
    elif os.environ.get('FAKE_CLAUDE_WRITE') == '1':
        (cwd/'forbidden.txt').write_text('write attempt\\n')
    if os.environ.get('FAKE_CLAUDE_REPORTED_FILE') == '1':
        files.append('claimed.txt')
    plain='done'
if os.environ.get('FAKE_CLAUDE_FAIL') == '1' and not (cwd/'probe-marker.txt').exists():
    print('fake provider failure', file=sys.stderr)
    raise SystemExit(1)
report={'files':files,'compile':{'status':'SKIPPED','detail':'fake'},'decisions':[],'blockers':[]}
value={'is_error':False,'subtype':'success','terminal_reason':'completed','result':json.dumps(report) if schema else plain,'permission_denials':[],'usage':{'input_tokens':9,'output_tokens':3},'session_id':'fake-session'}
if schema: value['structured_output']=report
print(json.dumps(value))
""",
        encoding="utf-8",
    )
    claude.chmod(0o755)


def fake_env(root: Path) -> dict[str, str]:
    bin_dir = root / "bin"
    bin_dir.mkdir()
    write_fake_tools(bin_dir)
    config = root / "claude-config"
    config.mkdir()
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["CLAUDE_CONFIG_DIR"] = str(config)
    return env


def command(
    script: Path,
    subcommand: str,
    artifact: Path,
    profile: str,
    schema: str,
    passthrough: bool = True,
) -> list[str]:
    return [
        sys.executable,
        "-B",
        str(script),
        subcommand,
        "--model",
        "fake-model",
        "--profile",
        profile,
        "--result-schema",
        schema,
        "--artifact-dir",
        str(artifact),
    ] + (FAKE_PASSTHROUGH if passthrough else [])


class ClaudeDelegateTests(unittest.TestCase):
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
        profile = next(action for action in actions if action.dest == "profile")
        self.assertEqual(profile.choices, ("read-only", "workspace-write"))

    def test_private_runner_sink_rejects_raw_prompt_text(self):
        with self.assertRaises(TypeError):
            M._invoke_adapter_prompt(
                args(),
                prompt="OUTSIDER-CONTENT",  # type: ignore[arg-type]
                cwd=Path("/unused"),
                artifact_dir=Path("/unused"),
                expected_exact=None,
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

    def test_argv_read_only_profile_and_prompt_absent(self):
        argv = M.build_argv(args())
        self.assertEqual(argv, [
            "claude", "-p", "--model", "fake-claude", "--effort", "low",
            "--output-format", "json", "--no-session-persistence", "--safe-mode",
            "--setting-sources", "", "--strict-mcp-config", "--tools", "Read,Glob,Grep",
        ])
        self.assertNotIn("secret prompt marker", argv)
        self.assertNotIn("--permission-mode", argv)

    def test_argv_workspace_write_profile_adds_permission_mode_and_write_tools(self):
        argv = M.build_argv(args(profile="workspace-write", result_schema="worker-report-v1"))
        self.assertIn("--permission-mode", argv)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob,Grep,Edit,Write")
        self.assertIn("--json-schema", argv)
        self.assertIn("--safe-mode", argv)
        with self.assertRaisesRegex(ValueError, "unsupported profile"):
            M.build_argv(args(profile="bypassPermissions"))

    def test_terminal_proof_rejects_non_completed_malformed_and_missing_result(self):
        bad_terminal = result_object(terminal_reason="max_turns")
        self.assertFalse(M.validate_terminal_result(args(), bad_terminal)[0])
        parsed, error = M.parse_result("{not-json")
        self.assertIsNone(parsed)
        self.assertIn("not one JSON object", error)
        for value in (result_object(result=""), result_object(result=None), {"is_error": False}):
            self.assertFalse(M.validate_terminal_result(args(), value)[0])

    def test_structured_output_missing_invalid_and_disagreement(self):
        a = args(result_schema="worker-report-v1")
        report = {"files": [], "compile": {"status": "SKIPPED", "detail": "x"}, "decisions": [], "blockers": []}
        self.assertFalse(M.validate_terminal_result(a, result_object(result=json.dumps(report)))[0])
        self.assertFalse(M.validate_terminal_result(a, result_object(result="{}", structured_output={}))[0])
        other = {**report, "files": ["other"]}
        self.assertFalse(M.validate_terminal_result(a, result_object(result=json.dumps(other), structured_output=report))[0])
        self.assertTrue(M.validate_terminal_result(a, result_object(result=json.dumps(report), structured_output=report))[0])

    def test_permission_denials_are_classified(self):
        terminal = result_object(permission_denials=[{"tool_name": "Write"}])
        ok, _, denied, _ = M.validate_terminal_result(args(), terminal)
        self.assertFalse(ok)
        self.assertTrue(denied)
        self.assertEqual(M.classify_failure("", timed_out=False, exit_code=0, receipt_ok=False, permission_denied=denied), "permission_denied")

    def test_failure_classifier_markers_and_fail_closed_default(self):
        cases = [
            ("error: unknown option --safe-mode", False, 1, "cli_contract_mismatch"),
            ("Could not resolve host api.anthropic.com", False, 1, "network_unavailable"),
            ("Authentication failed", False, 1, "authentication_failed"),
            ("", True, None, "timeout"),
            ("unrecognized provider shape", False, 1, "provider_failed"),
            ("", False, 0, "receipt_mismatch"),
        ]
        for stderr, timed, exit_code, expected in cases:
            self.assertEqual(M.classify_failure(stderr, timed_out=timed, exit_code=exit_code, receipt_ok=False), expected)

    def test_fingerprint_covers_measured_runtime_profile(self):
        fp = M.fingerprint(args(), "2.1.223")
        self.assertEqual(fp["adapter_schema"], 5)
        self.assertEqual(set(fp["adapter_files"]), {"claude_delegate.py", "delegate_common.py"})
        self.assertTrue(fp["safe_mode"])
        self.assertFalse(fp["session_persistence"])
        self.assertEqual(fp["setting_sources"], "")
        self.assertIsNone(fp["permission_mode"])
        self.assertFalse(fp["write_allowlist_required"])
        self.assertEqual(fp["env_passthrough"], [])
        self.assertIn("manifest_max_total_bytes", fp)
        self.assertEqual(fp["manifest_exclusions"], [])
        self.assertEqual(fp["external_task_contract"], C.EXTERNAL_TASK_CONTRACT)
        self.assertEqual(fp["mission_contract"], C.MISSION_CONTRACT)
        write_fp = M.fingerprint(args(profile="workspace-write"), "2.1.223")
        self.assertEqual(write_fp["permission_mode"], "acceptEdits")
        self.assertTrue(write_fp["write_allowlist_required"])
        self.assertEqual(write_fp["tools"], "Read,Glob,Grep,Edit,Write")

    def test_artifact_dir_inside_cwd_is_rejected_before_creation(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            artifact = work / "artifacts"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(M.command_run(args(cwd=str(work), artifact_dir=str(artifact))), 2)
            self.assertFalse(artifact.exists())

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
            path.write_text(json.dumps({**base, "kind": "claude_delegate_run"}), encoding="utf-8")
            ok, _, reason = M.validate_preflight(a, "fake-version")
            self.assertFalse(ok)
            self.assertEqual(reason, "preflight receipt kind is not a preflight receipt")
            path.write_text(
                json.dumps({**base, "kind": "claude_delegate_preflight", "file_probe_ok": None}),
                encoding="utf-8",
            )
            ok, _, reason = M.validate_preflight(a, "fake-version")
            self.assertFalse(ok)
            self.assertEqual(reason, "preflight receipt lacks a successful canary file probe")

    def test_preflight_receipt_age_tolerates_only_bounded_clock_rollback(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(M, "utc_epoch", return_value=1000):
            path = Path(td) / "receipt.json"
            a = args(preflight_receipt=str(path), preflight_max_age=100)
            base = {
                "ok": True,
                "kind": "claude_delegate_preflight",
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

            rejected = (
                (899, "age 101s exceeds 100s"),
                (1006, "6s in the future"),
            )
            for created_at, expected in rejected:
                path.write_text(
                    json.dumps({**base, "created_at_epoch": created_at}),
                    encoding="utf-8",
                )
                ok, _, reason = M.validate_preflight(a, "fake-version")
                self.assertFalse(ok)
                self.assertIn(expected, reason)

    def test_open_ended_task_profile_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            script = Path(M.__file__).resolve()
            preflight = root / "preflight"
            pre = subprocess.run(
                command(script, "preflight", preflight, "read-only", "none"),
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            artifact = root / "run"
            completed = subprocess.run(
                command(script, "run", artifact, "read-only", "none") + [
                    "--cwd", str(work),
                    "--preflight-receipt", str(preflight / "receipt.json"),
                    "--task-profile", "repair", "--target", "input.txt",
                ],
                env=env, input=" \n", capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 2)
            receipt = json.loads((artifact / "receipt.json").read_text())
            self.assertEqual(receipt["failure_kind"], "task_contract_invalid")

    def test_shared_module_byte_change_invalidates_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            copied = root / "scripts"
            copied.mkdir()
            shutil.copyfile(Path(M.__file__), copied / "claude_delegate.py")
            shutil.copyfile(Path(C.__file__), copied / "delegate_common.py")
            preflight = root / "preflight"
            pre = subprocess.run(command(copied / "claude_delegate.py", "preflight", preflight, "read-only", "worker-report-v1"), env=env, capture_output=True, text=True)
            self.assertEqual(pre.returncode, 0, pre.stderr)
            with (copied / "delegate_common.py").open("a", encoding="utf-8") as handle:
                handle.write("\n# changed constituent\n")
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            run_args = command(copied / "claude_delegate.py", "run", root / "run", "read-only", "worker-report-v1") + ["--cwd", str(work), "--preflight-receipt", str(preflight / "receipt.json"), "--task-profile", "inspect", "--target", "input.txt"]
            run = subprocess.run(run_args, env=env, input="task\n", capture_output=True, text=True)
            self.assertEqual(run.returncode, 4, run.stderr)
            self.assertEqual(json.loads((root / "run" / "receipt.json").read_text())["failure_kind"], "preflight_required")

    def test_fake_claude_preflights_closed_run_scope_and_receipt_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            script = Path(M.__file__).resolve()
            read_preflight = root / "read-preflight"
            read_pre = subprocess.run(command(script, "preflight", read_preflight, "read-only", "none"), env=env, capture_output=True, text=True)
            self.assertEqual(read_pre.returncode, 0, read_pre.stderr)
            read_receipt = json.loads((read_preflight / "receipt.json").read_text())
            self.assertTrue(read_receipt["file_probe_ok"])
            self.assertEqual(read_receipt["canary"]["last_message"]["matched"], True)
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            capture = root / "received-prompt.txt"
            env["FAKE_CLAUDE_PROMPT_CAPTURE"] = str(capture)
            accepted = root / "accepted"
            run_args = command(script, "run", accepted, "read-only", "none") + ["--cwd", str(work), "--task-profile", "review", "--target", "input.txt", "--preflight-receipt", str(read_preflight / "receipt.json")]
            run = subprocess.run(
                run_args, env=env, input="OUTSIDER-CONTENT\n", capture_output=True, text=True
            )
            receipt = json.loads((accepted / "receipt.json").read_text())
            self.assertEqual(run.returncode, 0, f"{run.stderr}\n{receipt}")
            self.assertEqual(receipt["kind"], "claude_delegate_run")
            self.assertEqual(receipt["fingerprint_sha256"], receipt["preflight_fingerprint_sha256"])
            self.assertEqual(receipt["preflight_receipt_sha256"], C.sha256_file(read_preflight / "receipt.json"))
            invocation = receipt["invocation"]
            received = capture.read_text(encoding="utf-8")
            self.assertEqual(received, C.render_external_task_prompt("review", ["input.txt"]).text)
            self.assertNotIn("OUTSIDER-CONTENT", received)
            self.assertEqual(invocation["prompt"]["origin"], "adapter-generated")
            self.assertEqual(invocation["prompt"]["contract"], C.EXTERNAL_TASK_CONTRACT)
            self.assertIn("argv", invocation)
            self.assertEqual(invocation["permission_denials"], [])
            self.assertFalse(invocation["stderr"]["truncated"])
            self.assertEqual(invocation["terminal_reason"], "completed")
            self.assertIn("baseline_git_metadata", receipt["change_manifest"])
            self.assertIn("final_git_metadata", receipt["change_manifest"])
            bad_env = env.copy()
            bad_env["FAKE_CLAUDE_WRITE"] = "1"
            rejected = root / "rejected"
            bad_args = [str(rejected) if value == str(accepted) else value for value in run_args]
            bad = subprocess.run(bad_args, env=bad_env, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 5)
            self.assertEqual(json.loads(bad.stdout)["scope_ok"], False)
            bad_receipt = json.loads((rejected / "receipt.json").read_text())
            self.assertEqual(bad_receipt["failure_kind"], "scope_violation")
            self.assertEqual(bad_receipt["change_manifest"]["actual_changed_paths"], ["forbidden.txt"])

            (work / "forbidden.txt").unlink()

            failed_work = root / "failed-work"
            failed_work.mkdir()
            (failed_work / "input.txt").write_text("input\n", encoding="utf-8")
            failed_artifact = root / "failed"
            failed_args = command(script, "run", failed_artifact, "read-only", "none") + [
                "--cwd", str(failed_work), "--preflight-receipt",
                str(read_preflight / "receipt.json"), "--task-profile", "inspect", "--target", "input.txt",
            ]
            failed_env = env.copy()
            failed_env["FAKE_CLAUDE_FAIL"] = "1"
            failed = subprocess.run(
                failed_args, env=failed_env, input="write\n", capture_output=True, text=True
            )
            self.assertEqual(failed.returncode, 5)
            failed_receipt = json.loads((failed_artifact / "receipt.json").read_text())
            self.assertEqual(failed_receipt["failure_kind"], "provider_failed")
            self.assertTrue(failed_receipt["change_manifest"]["scope_ok"])

    def test_read_only_run_rejects_write_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            script = Path(M.__file__).resolve()
            preflight = root / "preflight"
            pre = subprocess.run(command(script, "preflight", preflight, "read-only", "none"), env=env, capture_output=True, text=True)
            self.assertEqual(pre.returncode, 0, pre.stderr)
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            env["FAKE_CLAUDE_WRITE"] = "1"
            run_args = command(script, "run", root / "run", "read-only", "none") + ["--cwd", str(work), "--preflight-receipt", str(preflight / "receipt.json"), "--task-profile", "inspect", "--target", "input.txt"]
            run = subprocess.run(run_args, env=env, input="attempt work\n", capture_output=True, text=True)
            self.assertEqual(run.returncode, 5)
            receipt = json.loads((root / "run" / "receipt.json").read_text())
            self.assertEqual(receipt["failure_kind"], "scope_violation")
            self.assertEqual(receipt["change_manifest"]["actual_changed_paths"], ["forbidden.txt"])

    def test_read_only_run_rejects_nonempty_reported_files_without_manifest_change(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            script = Path(M.__file__).resolve()
            preflight = root / "preflight"
            pre = subprocess.run(
                command(script, "preflight", preflight, "read-only", "worker-report-v1"),
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            env["FAKE_CLAUDE_REPORTED_FILE"] = "1"
            artifact = root / "run"
            run_args = command(
                script, "run", artifact, "read-only", "worker-report-v1"
            ) + [
                "--cwd", str(work),
                "--preflight-receipt", str(preflight / "receipt.json"),
                "--task-profile", "inspect",
                "--target", "input.txt",
            ]
            run = subprocess.run(run_args, env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 5)
            receipt = json.loads((artifact / "receipt.json").read_text())
            self.assertEqual(receipt["failure_kind"], "scope_violation")
            self.assertFalse(receipt["change_manifest"]["reported_files_match"])
            self.assertEqual(receipt["change_manifest"]["actual_changed_paths"], [])

    def test_workspace_write_mission_run_enforces_allowlist_and_envelope(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            script = Path(M.__file__).resolve()
            preflight = root / "preflight"
            pre = subprocess.run(
                command(script, "preflight", preflight, "workspace-write", "worker-report-v1"),
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
            env["FAKE_CLAUDE_PROMPT_CAPTURE"] = str(capture)
            accepted = root / "accepted"
            run_args = command(script, "run", accepted, "workspace-write", "worker-report-v1") + [
                "--cwd", str(work),
                "--mission-file", str(mission), "--allowed-write", "result.txt",
                "--preflight-receipt", str(preflight / "receipt.json"),
            ]
            ok = subprocess.run(run_args, env=env, capture_output=True, text=True)
            receipt = json.loads((accepted / "receipt.json").read_text())
            self.assertEqual(ok.returncode, 0, f"{ok.stderr}\n{receipt}")
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["task_contract"]["contract"], C.MISSION_CONTRACT)
            invocation = receipt["invocation"]
            self.assertEqual(invocation["prompt"]["origin"], "coordinator-mission")
            received = capture.read_text(encoding="utf-8")
            self.assertIn("Edit result.txt to record the fake result.", received)
            self.assertIn("<<<mission ", received)
            self.assertIn('["result.txt"]', received)
            self.assertEqual(
                (accepted / "mission.txt").read_text(encoding="utf-8"),
                mission.read_text(encoding="utf-8"),
            )
            manifest = receipt["change_manifest"]
            self.assertEqual(manifest["actual_changed_paths"], ["result.txt"])
            self.assertTrue(manifest["scope_ok"])

            bad_env = env.copy()
            bad_env["FAKE_CLAUDE_EXTRA"] = "1"
            rejected = root / "rejected"
            bad_args = [str(rejected) if value == str(accepted) else value for value in run_args]
            bad = subprocess.run(bad_args, env=bad_env, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 5)
            bad_receipt = json.loads((rejected / "receipt.json").read_text())
            self.assertEqual(bad_receipt["failure_kind"], "scope_violation")
            self.assertEqual(bad_receipt["change_manifest"]["out_of_scope_paths"], ["extra.log"])

            inside = work / "mission-inside.md"
            inside.write_text("workspace-authored mission\n", encoding="utf-8")
            inside_artifact = root / "inside"
            inside_args = [str(inside_artifact) if value == str(accepted) else value for value in run_args]
            inside_args[inside_args.index("--mission-file") + 1] = str(inside)
            inside_run = subprocess.run(inside_args, env=env, capture_output=True, text=True)
            self.assertEqual(inside_run.returncode, 2)
            inside_receipt = json.loads((inside_artifact / "receipt.json").read_text())
            self.assertEqual(inside_receipt["failure_kind"], "task_contract_invalid")
            self.assertIn("outside the delegated cwd", inside_receipt["reason"])

    def test_workspace_write_manifest_exclusion_and_degraded_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            script = Path(M.__file__).resolve()
            preflight = root / "preflight"
            pre = subprocess.run(
                command(script, "preflight", preflight, "workspace-write", "worker-report-v1"),
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            mission = root / "mission.md"
            mission.write_text("Edit result.txt and generate disposable build output.\n")

            def run_case(name: str, extra: list[str]):
                work = root / f"work-{name}"; work.mkdir()
                (work / "input.txt").write_text("input\n")
                artifact = root / f"run-{name}"
                case_preflight = root / f"preflight-{name}"
                case_pre = subprocess.run(
                    command(
                        script, "preflight", case_preflight,
                        "workspace-write", "worker-report-v1"
                    ) + extra,
                    env=env, capture_output=True, text=True,
                )
                self.assertEqual(case_pre.returncode, 0, case_pre.stderr)
                run_env = env.copy()
                run_env["FAKE_CLAUDE_BUILD_BLOAT"] = "1"
                completed = subprocess.run(
                    command(script, "run", artifact, "workspace-write", "worker-report-v1")
                    + [
                        "--cwd", str(work), "--mission-file", str(mission),
                        "--allowed-write", "result.txt",
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

    def test_env_minimization_blocks_unlisted_variables(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            script = Path(M.__file__).resolve()
            preflight = root / "preflight"
            pre = subprocess.run(
                command(script, "preflight", preflight, "read-only", "none", passthrough=False),
                env=env, capture_output=True, text=True,
            )
            self.assertEqual(pre.returncode, 0, pre.stderr)
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            env["FAKE_CLAUDE_WRITE"] = "1"
            artifact = root / "run"
            run = subprocess.run(
                command(script, "run", artifact, "read-only", "none", passthrough=False) + [
                    "--cwd", str(work),
                    "--preflight-receipt", str(preflight / "receipt.json"),
                    "--task-profile", "inspect", "--target", "input.txt",
                ],
                env=env, capture_output=True, text=True,
            )
            receipt = json.loads((artifact / "receipt.json").read_text())
            self.assertEqual(run.returncode, 0, f"{run.stderr}\n{receipt}")
            self.assertEqual(receipt["change_manifest"]["actual_changed_paths"], [])

    def test_workspace_write_requires_worker_report_schema(self):
        completed = subprocess.run(
            [
                sys.executable, "-B", str(Path(M.__file__).resolve()), "run",
                "--model", "fake-model", "--profile", "workspace-write",
                "--artifact-dir", "/tmp/unused-artifacts", "--cwd", "/tmp/unused-work",
            ],
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("worker-report-v1", completed.stderr)


if __name__ == "__main__":
    unittest.main()
