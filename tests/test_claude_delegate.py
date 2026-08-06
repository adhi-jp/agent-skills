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
        allowed_write=[],
        prompt_file=None,
        expected_exact=None,
        cwd="/tmp/work",
    )
    base.update(overrides)
    return argparse.Namespace(**base)


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
import sys
a=sys.argv[1:]
if a[:1] == ['init']: raise SystemExit(0)
if a == ['rev-parse','--verify','HEAD']: print('a'*40); raise SystemExit(0)
if a == ['symbolic-ref','--quiet','HEAD']: print('refs/heads/main'); raise SystemExit(0)
if a and a[0] == 'for-each-ref': print('refs/heads/main\\0'+'a'*40); raise SystemExit(0)
if a == ['ls-files','--stage','-z']: sys.stdout.write('100644 '+'b'*40+' 0\\tinput.txt\\0'); raise SystemExit(0)
if a == ['ls-files','-v','-z']: sys.stdout.write('H input.txt\\0'); raise SystemExit(0)
if a in (['diff','--name-only','-z','HEAD'], ['ls-files','--others','--exclude-standard','-z']): raise SystemExit(0)
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
        if os.environ.get('FAKE_CLAUDE_EXTRA') == '1':
            (cwd/'extra.log').write_text('scope violation\\n')
    elif os.environ.get('FAKE_CLAUDE_WRITE') == '1':
        (cwd/'forbidden.txt').write_text('write attempt\\n')
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


def command(script: Path, subcommand: str, artifact: Path, profile: str, schema: str) -> list[str]:
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
    ]


class ClaudeDelegateTests(unittest.TestCase):
    def test_argv_read_only_profile_and_prompt_absent(self):
        argv = M.build_argv(args())
        self.assertEqual(argv, [
            "claude", "-p", "--model", "fake-claude", "--effort", "low",
            "--output-format", "json", "--no-session-persistence", "--safe-mode",
            "--setting-sources", "", "--strict-mcp-config", "--tools", "Read,Glob,Grep",
        ])
        self.assertNotIn("secret prompt marker", argv)
        self.assertNotIn("--permission-mode", argv)

    def test_argv_workspace_write_profile_and_schema(self):
        argv = M.build_argv(args(profile="workspace-write", result_schema="worker-report-v1"))
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob,Grep,Edit,Write")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "acceptEdits")
        schema = json.loads(argv[argv.index("--json-schema") + 1])
        self.assertEqual(schema, M.worker_report_schema())
        self.assertNotIn("--dangerously-skip-permissions", argv)

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
        self.assertEqual(fp["adapter_schema"], 1)
        self.assertEqual(set(fp["adapter_files"]), {"claude_delegate.py", "delegate_common.py"})
        self.assertTrue(fp["safe_mode"])
        self.assertFalse(fp["session_persistence"])
        self.assertEqual(fp["setting_sources"], "")
        self.assertIsNone(fp["permission_mode"])
        self.assertIn("manifest_max_total_bytes", fp)

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

    def test_empty_prompt_is_rejected(self):
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
                ],
                env=env, input=" \n", capture_output=True, text=True,
            )
            self.assertEqual(completed.returncode, 2)
            receipt = json.loads((artifact / "receipt.json").read_text())
            self.assertEqual(receipt["failure_kind"], "prompt_empty")

    def test_shared_module_byte_change_invalidates_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            env = fake_env(root)
            copied = root / "scripts"
            copied.mkdir()
            shutil.copyfile(Path(M.__file__), copied / "claude_delegate.py")
            shutil.copyfile(Path(C.__file__), copied / "delegate_common.py")
            preflight = root / "preflight"
            pre = subprocess.run(command(copied / "claude_delegate.py", "preflight", preflight, "workspace-write", "worker-report-v1"), env=env, capture_output=True, text=True)
            self.assertEqual(pre.returncode, 0, pre.stderr)
            with (copied / "delegate_common.py").open("a", encoding="utf-8") as handle:
                handle.write("\n# changed constituent\n")
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            run_args = command(copied / "claude_delegate.py", "run", root / "run", "workspace-write", "worker-report-v1") + ["--cwd", str(work), "--preflight-receipt", str(preflight / "receipt.json"), "--allowed-write", "result.txt"]
            run = subprocess.run(run_args, env=env, input="task\n", capture_output=True, text=True)
            self.assertEqual(run.returncode, 4, run.stderr)
            self.assertEqual(json.loads((root / "run" / "receipt.json").read_text())["failure_kind"], "preflight_required")

    def test_fake_claude_preflights_run_scope_and_receipt_persistence(self):
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
            write_preflight = root / "write-preflight"
            write_pre = subprocess.run(command(script, "preflight", write_preflight, "workspace-write", "worker-report-v1"), env=env, capture_output=True, text=True)
            self.assertEqual(write_pre.returncode, 0, write_pre.stderr)
            work = root / "work"
            work.mkdir()
            (work / "input.txt").write_text("input\n", encoding="utf-8")
            prompt = root / "prompt.txt"
            prompt.write_text("write the result\n", encoding="utf-8")
            accepted = root / "accepted"
            run_args = command(script, "run", accepted, "workspace-write", "worker-report-v1") + ["--cwd", str(work), "--prompt-file", str(prompt), "--preflight-receipt", str(write_preflight / "receipt.json"), "--allowed-write", "result.txt"]
            run = subprocess.run(run_args, env=env, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            receipt = json.loads((accepted / "receipt.json").read_text())
            self.assertEqual(receipt["kind"], "claude_delegate_run")
            self.assertEqual(receipt["fingerprint_sha256"], receipt["preflight_fingerprint_sha256"])
            self.assertEqual(receipt["preflight_receipt_sha256"], C.sha256_file(write_preflight / "receipt.json"))
            invocation = receipt["invocation"]
            self.assertEqual(invocation["prompt"]["sha256"], C.sha256_file(prompt))
            self.assertIn("argv", invocation)
            self.assertEqual(invocation["permission_denials"], [])
            self.assertFalse(invocation["stderr"]["truncated"])
            self.assertEqual(invocation["terminal_reason"], "completed")
            self.assertIn("baseline_git_metadata", receipt["change_manifest"])
            self.assertIn("final_git_metadata", receipt["change_manifest"])
            (work / "result.txt").unlink()
            bad_env = env.copy()
            bad_env["FAKE_CLAUDE_EXTRA"] = "1"
            rejected = root / "rejected"
            bad_args = [str(rejected) if value == str(accepted) else value for value in run_args]
            bad = subprocess.run(bad_args, env=bad_env, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 5)
            self.assertEqual(json.loads(bad.stdout)["scope_ok"], False)
            bad_receipt = json.loads((rejected / "receipt.json").read_text())
            self.assertEqual(bad_receipt["failure_kind"], "scope_violation")
            self.assertEqual(bad_receipt["change_manifest"]["actual_changed_paths"], ["extra.log", "result.txt"])

            failed_work = root / "failed-work"
            failed_work.mkdir()
            (failed_work / "input.txt").write_text("input\n", encoding="utf-8")
            failed_artifact = root / "failed"
            failed_args = command(script, "run", failed_artifact, "workspace-write", "worker-report-v1") + [
                "--cwd", str(failed_work), "--preflight-receipt",
                str(write_preflight / "receipt.json"), "--allowed-write", "result.txt",
            ]
            failed_env = env.copy()
            failed_env["FAKE_CLAUDE_EXTRA"] = "1"
            failed_env["FAKE_CLAUDE_FAIL"] = "1"
            failed = subprocess.run(
                failed_args, env=failed_env, input="write\n", capture_output=True, text=True
            )
            self.assertEqual(failed.returncode, 5)
            failed_receipt = json.loads((failed_artifact / "receipt.json").read_text())
            self.assertEqual(failed_receipt["failure_kind"], "provider_failed")
            self.assertFalse(failed_receipt["change_manifest"]["scope_ok"])
            self.assertEqual(json.loads(failed.stdout)["scope_ok"], False)

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
            run_args = command(script, "run", root / "run", "read-only", "none") + ["--cwd", str(work), "--preflight-receipt", str(preflight / "receipt.json")]
            run = subprocess.run(run_args, env=env, input="attempt work\n", capture_output=True, text=True)
            self.assertEqual(run.returncode, 5)
            receipt = json.loads((root / "run" / "receipt.json").read_text())
            self.assertEqual(receipt["failure_kind"], "scope_violation")
            self.assertEqual(receipt["change_manifest"]["actual_changed_paths"], ["forbidden.txt"])


if __name__ == "__main__":
    unittest.main()
