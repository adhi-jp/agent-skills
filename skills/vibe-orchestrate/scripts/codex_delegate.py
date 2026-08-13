#!/usr/bin/env python3
"""Bounded Codex CLI delegation adapter for external workers.

The adapter never elevates itself. It fails before a model call when Codex
runtime state is not writable and records structured receipts. Tasks arrive
either as a closed read-only profile over validated target paths, or as a
coordinator-authored mission wrapped in a hardened envelope; write access
requires the workspace-write sandbox plus an explicit write allowlist that is
reconciled against observed filesystem and Git changes after the run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any

from delegate_common import (
    AdapterPrompt,
    adapter_files_sha256,
    bounded,
    EXTERNAL_TASK_CONTRACT,
    MISSION_CONTRACT,
    filesystem_manifest,
    fingerprint_digest,
    git_changed_paths,
    git_head,
    git_metadata_snapshot,
    manifest_changed_paths,
    minimal_child_env,
    normalize_allowed_write_paths,
    normalize_manifest_exclusions,
    preflight_receipt_age_error,
    print_receipt,
    probe_writable_directory,
    resolve_run_task,
    sha256_file,
    utc_epoch,
    render_adapter_canary_prompt,
    validate_worker_report,
    vcs_degraded_scope_ok,
    worker_report_schema,
    write_json,
)

READY_TEXT = "CODEX_DELEGATE_READY"
ADAPTER_SCHEMA = 12
ENV_RUNNER_PREFIXES = ("CODEX_", "OPENAI_")
DEFAULT_MANIFEST_MAX_TOTAL_BYTES = 536870912
MINIMAL_FEATURES = (
    "apps",
    "plugins",
    "remote_plugin",
    "plugin_sharing",
    "in_app_browser",
    "browser_use",
    "browser_use_full_cdp_access",
    "browser_use_external",
    "computer_use",
    "image_generation",
    "workspace_dependencies",
    "skill_mcp_dependency_install",
    "skill_search",
    "memories",
    "hooks",
    "goals",
)


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()


def codex_version(binary: str) -> tuple[str | None, str | None]:
    try:
        result = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, str(exc)
    text = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        return None, text or f"exit {result.returncode}"
    return text[:512], None


def login_status(binary: str) -> tuple[bool, str, int | None]:
    try:
        result = subprocess.run(
            [binary, "login", "status"], capture_output=True, text=True, timeout=15, check=False
        )
    except subprocess.TimeoutExpired as exc:
        return False, f"login status timed out: {exc}", None
    except OSError as exc:
        return False, str(exc), None
    output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
    return result.returncode == 0, output[:4096], result.returncode


def parse_jsonl(path: Path) -> dict[str, Any]:
    thread_id = None
    usage = None
    event_types: list[str] = []
    turn_completed = False
    turn_failed = False
    if not path.is_file():
        return {
            "thread_id": None,
            "usage": None,
            "event_types": [],
            "turn_completed": False,
            "turn_failed": False,
        }
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        if isinstance(event_type, str):
            event_types.append(event_type)
        if event_type == "thread.started":
            candidate = event.get("thread_id")
            if not isinstance(candidate, str):
                thread = event.get("thread")
                candidate = thread.get("id") if isinstance(thread, dict) else None
            if isinstance(candidate, str):
                thread_id = candidate
        elif event_type == "turn.completed":
            turn_completed = True
            if isinstance(event.get("usage"), dict):
                usage = event["usage"]
        elif event_type == "turn.failed":
            turn_failed = True
    return {
        "thread_id": thread_id,
        "usage": usage,
        "event_types": event_types,
        "turn_completed": turn_completed,
        "turn_failed": turn_failed,
    }


def classify_failure(stderr: str, *, timed_out: bool, exit_code: int | None, receipt_ok: bool) -> str:
    text = stderr.lower()
    if timed_out:
        return "timeout"
    if "failed to initialize in-process app-server client" in text and "read-only file system" in text:
        return "codex_state_not_writable"
    if "could not resolve host" in text or "operation not permitted" in text or "connect failed" in text:
        return "network_unavailable"
    if "not logged in" in text or "authentication" in text or "unauthorized" in text:
        return "authentication_failed"
    if (
        "unexpected argument" in text
        or "strict-config" in text
        or "unknown feature" in text
        or "unrecognized feature" in text
    ):
        return "cli_contract_mismatch"
    if exit_code == 0 and not receipt_ok:
        return "receipt_mismatch"
    return "provider_failed"


def fingerprint(args: argparse.Namespace, version: str) -> dict[str, Any]:
    return {
        "adapter_schema": ADAPTER_SCHEMA,
        "adapter_files": adapter_files_sha256(
            [Path(__file__).resolve(), Path(__file__).with_name("delegate_common.py").resolve()]
        ),
        "codex_version": version,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "sandbox": args.sandbox,
        "runtime_profile": "minimal",
        "result_schema": args.result_schema,
        "user_config": "disabled",
        "rules_profile": "disabled",
        "project_instructions": "disabled",
        "web_search": "disabled",
        "workspace_write_network": "disabled",
        "write_allowlist_required": args.sandbox == "workspace-write",
        "env_passthrough": sorted(set(args.env_passthrough)),
        "external_task_contract": EXTERNAL_TASK_CONTRACT,
        "mission_contract": MISSION_CONTRACT,
        "manifest_max_files": args.manifest_max_files,
        "manifest_max_total_bytes": args.manifest_max_total_bytes,
        "manifest_exclusions": sorted(set(getattr(args, "manifest_exclude", []))),
        "codex_home": str(codex_home()),
    }


def build_argv(
    args: argparse.Namespace,
    *,
    output_last: Path,
    output_schema: Path | None,
    ephemeral: bool,
) -> list[str]:
    argv = [args.codex_binary, "-a", "never"]
    for feature in MINIMAL_FEATURES:
        argv += ["--disable", feature]
    argv.append("exec")
    argv += ["-s", args.sandbox, "-o", str(output_last.resolve()), "--json", "--skip-git-repo-check"]
    if ephemeral:
        argv.append("--ephemeral")
    argv += ["--strict-config", "--ignore-user-config", "--ignore-rules"]
    argv += ["--model", args.model, "-c", f'model_reasoning_effort="{args.reasoning_effort}"']
    argv += [
        "-c", "features.multi_agent=false",
        "-c", "agents.enabled=false",
        "-c", 'web_search="disabled"',
        "-c", "project_doc_max_bytes=0",
        "-c", "project_doc_fallback_filenames=[]",
    ]
    if args.sandbox == "workspace-write":
        argv += ["-c", "sandbox_workspace_write.network_access=false"]
    if output_schema is not None:
        argv += ["--output-schema", str(output_schema.resolve())]
    argv.append("-")
    return argv


def result_schema(args: argparse.Namespace) -> dict[str, Any] | None:
    return worker_report_schema() if args.result_schema == "worker-report-v1" else None


def validate_structured_last(args: argparse.Namespace, last: str) -> tuple[bool, Any | None]:
    if args.result_schema == "none":
        return True, None
    try:
        value = json.loads(last)
    except json.JSONDecodeError:
        return False, None
    return validate_worker_report(value), value


def _invoke_adapter_prompt(
    args: argparse.Namespace,
    *,
    prompt: AdapterPrompt,
    cwd: Path,
    artifact_dir: Path,
    expected_exact: str | None,
    ephemeral: bool,
) -> dict[str, Any]:
    if not isinstance(prompt, AdapterPrompt):
        raise TypeError("runner input must be a renderer-produced AdapterPrompt")
    prompt_text = prompt.text
    artifact_dir = artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        artifact_dir.chmod(0o700)
    except OSError:
        pass
    stdout_path = artifact_dir / "stdout.jsonl"
    stderr_path = artifact_dir / "stderr.txt"
    output_last = artifact_dir / "last_message.txt"
    schema = result_schema(args)
    schema_path = artifact_dir / "output_schema.json" if schema is not None else None
    if schema_path is not None:
        write_json(schema_path, schema)
    argv = build_argv(
        args,
        output_last=output_last,
        output_schema=schema_path,
        ephemeral=ephemeral,
    )
    env = minimal_child_env(ENV_RUNNER_PREFIXES, args.env_passthrough)
    env["PWD"] = str(cwd.resolve())
    started = time.monotonic()
    timed_out = False
    exit_code: int | None
    stdout = ""
    stderr = ""
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            env=env,
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
    duration = time.monotonic() - started
    stdout_path.write_text(stdout, encoding="utf-8")
    rendered_stderr, stderr_truncated = bounded(stderr)
    stderr_path.write_text(rendered_stderr, encoding="utf-8")
    last = output_last.read_text(encoding="utf-8", errors="replace") if output_last.is_file() else ""
    events = parse_jsonl(stdout_path)
    structured_ok, structured_value = validate_structured_last(args, last)
    expected_ok = expected_exact is None or last.strip() == expected_exact
    receipt_ok = (
        exit_code == 0
        and not timed_out
        and bool(last.strip())
        and events["turn_completed"]
        and not events["turn_failed"]
        and expected_ok
        and structured_ok
    )
    failure_kind = None if receipt_ok else classify_failure(
        stderr, timed_out=timed_out, exit_code=exit_code, receipt_ok=receipt_ok
    )
    return {
        "ok": receipt_ok,
        "failure_kind": failure_kind,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_seconds": round(duration, 3),
        "cwd": str(cwd.resolve()),
        "argv": argv,
        "prompt": {
            "origin": (
                "coordinator-mission" if prompt.contract == MISSION_CONTRACT else "adapter-generated"
            ),
            "contract": prompt.contract,
            "bytes": len(prompt_text.encode("utf-8")),
            "sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
            "stored": False,
        },
        "expected_exact": expected_exact,
        "result_schema": args.result_schema,
        "structured_result": structured_value,
        "last_message": {
            "path": str(output_last),
            "present": output_last.is_file(),
            "bytes": len(last.encode("utf-8")),
            "matched": expected_ok,
        },
        "stdout_jsonl": str(stdout_path),
        "stderr": {
            "path": str(stderr_path),
            "bytes": len(stderr.encode("utf-8", "replace")),
            "truncated": stderr_truncated,
        },
        **events,
    }


def static_preflight(args: argparse.Namespace) -> tuple[dict[str, Any], str | None]:
    binary = shutil.which(args.codex_binary)
    if binary is None:
        return {"ok": False, "failure_kind": "codex_not_found"}, None
    version, version_error = codex_version(binary)
    if version is None:
        return {"ok": False, "failure_kind": "codex_version_failed", "reason": version_error}, None
    home = codex_home()
    writable, write_error = probe_writable_directory(home)
    if not writable:
        return {
            "ok": False,
            "failure_kind": "codex_state_not_writable",
            "codex_version": version,
            "codex_home": str(home),
            "reason": write_error,
            "next_action": "rerun the same adapter command through the host's explicit escalation path",
        }, version
    auth_ok, auth_output, auth_exit = login_status(binary)
    if not auth_ok:
        return {
            "ok": False,
            "failure_kind": "authentication_failed",
            "codex_version": version,
            "codex_home": str(home),
            "login_status": auth_output,
            "login_exit_code": auth_exit,
        }, version
    return {
        "ok": True,
        "codex_version": version,
        "codex_home": str(home),
        "login_status": auth_output,
    }, version


def command_preflight(args: argparse.Namespace) -> int:
    artifact_dir = Path(args.artifact_dir).resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    artifact_dir.chmod(0o700)
    static, version = static_preflight(args)
    report: dict[str, Any] = {
        "schema_version": 1,
        "kind": "codex_delegate_preflight",
        "created_at_epoch": utc_epoch(),
        "static": static,
        "ok": False,
    }
    if not static.get("ok") or version is None:
        report["failure_kind"] = static.get("failure_kind")
        receipt_path = artifact_dir / "receipt.json"
        write_json(receipt_path, report)
        print_receipt(args, receipt_path, report)
        return 2
    fp = fingerprint(args, version)
    report["fingerprint"] = fp
    report["fingerprint_sha256"] = fingerprint_digest(fp)
    with tempfile.TemporaryDirectory(prefix="vibe-orchestrate-codex-canary-") as tmp:
        cwd = Path(tmp)
        subprocess.run(["git", "init", "--quiet"], cwd=cwd, check=True)
        marker = cwd / "probe-marker.txt"
        marker.write_text("CODEX_CANARY_MARKER\n", encoding="utf-8")
        write_capable = args.sandbox == "workspace-write"
        prompt = render_adapter_canary_prompt("codex", args.result_schema, write_capable)
        expected = None if args.result_schema == "worker-report-v1" else READY_TEXT
        invocation = _invoke_adapter_prompt(
            args,
            prompt=prompt,
            cwd=cwd,
            artifact_dir=artifact_dir / "canary",
            expected_exact=expected,
            ephemeral=True,
        )
        output = cwd / "probe-output.txt"
        file_probe_ok = marker.read_text(encoding="utf-8") == "CODEX_CANARY_MARKER\n"
        if write_capable:
            file_probe_ok = (
                file_probe_ok
                and output.is_file()
                and output.read_text(encoding="utf-8").strip() == "CODEX_CANARY_WRITE"
                and ((invocation.get("structured_result") or {}).get("files") == ["probe-output.txt"])
            )
        else:
            file_probe_ok = file_probe_ok and not output.exists()
            if args.result_schema == "worker-report-v1":
                file_probe_ok = file_probe_ok and (
                    (invocation.get("structured_result") or {}).get("files") == []
                )
        report["canary"] = invocation
        report["file_probe_ok"] = file_probe_ok
        report["ok"] = bool(invocation["ok"] and file_probe_ok)
        if not report["ok"]:
            report["failure_kind"] = invocation.get("failure_kind") or "file_probe_failed"
    receipt_path = artifact_dir / "receipt.json"
    write_json(receipt_path, report)
    print_receipt(args, receipt_path, report)
    return 0 if report["ok"] else 3


def validate_preflight(
    args: argparse.Namespace, version: str
) -> tuple[bool, dict[str, Any] | None, str | None]:
    if not args.preflight_receipt:
        return False, None, "--preflight-receipt is required"
    path = Path(args.preflight_receipt).resolve()
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, None, f"invalid preflight receipt: {exc}"
    if not isinstance(receipt, dict):
        return False, None, "invalid preflight receipt: root must be an object"
    if receipt.get("ok") is not True:
        return False, receipt, "preflight receipt is not successful"
    try:
        created_at_epoch = int(receipt.get("created_at_epoch", 0))
    except (TypeError, ValueError) as exc:
        return False, receipt, f"invalid preflight receipt timestamp: {exc}"
    age_error = preflight_receipt_age_error(
        current_epoch=utc_epoch(),
        created_at_epoch=created_at_epoch,
        max_age_seconds=args.preflight_max_age,
    )
    if age_error:
        return False, receipt, age_error
    expected = fingerprint(args, version)
    if receipt.get("fingerprint_sha256") != fingerprint_digest(expected):
        return False, receipt, "preflight fingerprint does not match this run"
    if receipt.get("kind") != "codex_delegate_preflight":
        return False, receipt, "preflight receipt kind is not a preflight receipt"
    if receipt.get("file_probe_ok") is not True:
        return False, receipt, "preflight receipt lacks a successful canary file probe"
    return True, receipt, None


def _write_report(args: argparse.Namespace, artifact_dir: Path, report: dict[str, Any]) -> None:
    receipt_path = artifact_dir / "receipt.json"
    write_json(receipt_path, report)
    print_receipt(args, receipt_path, report)


def command_run(args: argparse.Namespace) -> int:
    artifact_dir = Path(args.artifact_dir).resolve()
    cwd = Path(args.cwd).resolve()
    if cwd.is_dir() and (artifact_dir == cwd or cwd in artifact_dir.parents):
        print(json.dumps({
            "ok": False,
            "failure_kind": "artifact_dir_inside_cwd",
            "receipt": None,
            "reason": "--artifact-dir must be outside --cwd to avoid self-authored workspace changes",
        }, ensure_ascii=False))
        return 2
    artifact_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    artifact_dir.chmod(0o700)
    static, version = static_preflight(args)
    report: dict[str, Any] = {
        "schema_version": 1,
        "kind": "codex_delegate_run",
        "created_at_epoch": utc_epoch(),
        "static": static,
        "ok": False,
    }
    if not static.get("ok") or version is None:
        report["failure_kind"] = static.get("failure_kind")
        _write_report(args, artifact_dir, report)
        return 2
    preflight_ok, preflight, reason = validate_preflight(args, version)
    if not preflight_ok:
        report.update({"failure_kind": "preflight_required", "reason": reason, "preflight": preflight})
        _write_report(args, artifact_dir, report)
        return 4
    effective_fingerprint = fingerprint(args, version)
    report["fingerprint"] = effective_fingerprint
    report["fingerprint_sha256"] = fingerprint_digest(effective_fingerprint)
    report["preflight_fingerprint_sha256"] = preflight.get("fingerprint_sha256")
    report["preflight_receipt_sha256"] = sha256_file(Path(args.preflight_receipt).resolve())
    if not cwd.is_dir():
        report.update({"failure_kind": "cwd_invalid", "reason": f"not a directory: {cwd}"})
        _write_report(args, artifact_dir, report)
        return 2
    before_head = git_head(cwd)
    before_changed = git_changed_paths(cwd)
    before_git_metadata = git_metadata_snapshot(cwd)
    if before_head is None or before_changed is None or before_git_metadata is None:
        report.update({
            "failure_kind": "git_baseline_unavailable",
            "reason": "delegation cwd must be a Git repository with a HEAD commit",
        })
        _write_report(args, artifact_dir, report)
        return 2
    manifest_exclusions, exclusion_error = normalize_manifest_exclusions(
        cwd, getattr(args, "manifest_exclude", [])
    )
    if exclusion_error:
        report.update({"failure_kind": "invalid_manifest_exclusion", "reason": exclusion_error})
        _write_report(args, artifact_dir, report)
        return 2
    if manifest_exclusions and args.sandbox != "workspace-write":
        report.update({
            "failure_kind": "invalid_manifest_exclusion",
            "reason": "--manifest-exclude is allowed only for workspace-write runs",
        })
        _write_report(args, artifact_dir, report)
        return 2
    before_manifest, manifest_error = filesystem_manifest(
        cwd,
        args.manifest_max_files,
        args.manifest_max_total_bytes,
        manifest_exclusions,
    )
    if before_manifest is None:
        report.update({"failure_kind": "manifest_unavailable", "reason": manifest_error})
        _write_report(args, artifact_dir, report)
        return 2
    if before_changed:
        report.update({
            "failure_kind": "worktree_not_clean",
            "reason": "workspace-write and read-only delegation require a clean baseline",
            "baseline_changed_paths": before_changed,
        })
        _write_report(args, artifact_dir, report)
        return 2
    allowed, allowed_error = normalize_allowed_write_paths(cwd, args.allowed_write)
    if allowed_error:
        report.update({"failure_kind": "invalid_write_allowlist", "reason": allowed_error})
        _write_report(args, artifact_dir, report)
        return 2
    if args.sandbox == "workspace-write" and not allowed:
        report.update({
            "failure_kind": "write_allowlist_required",
            "reason": "workspace-write requires at least one --allowed-write path",
        })
        _write_report(args, artifact_dir, report)
        return 2
    prompt, task_contract, task_error = resolve_run_task(
        args,
        cwd,
        artifact_dir,
        write_capable=args.sandbox == "workspace-write",
        allowed=allowed or [],
    )
    if task_error or prompt is None:
        report.update({"failure_kind": "task_contract_invalid", "reason": task_error})
        _write_report(args, artifact_dir, report)
        return 2
    report["task_contract"] = task_contract
    invocation = _invoke_adapter_prompt(
        args,
        prompt=prompt,
        cwd=cwd,
        artifact_dir=artifact_dir / "run",
        expected_exact=args.expected_exact,
        ephemeral=True,
    )
    report["preflight_receipt"] = str(Path(args.preflight_receipt).resolve())
    report["invocation"] = invocation
    after_head = git_head(cwd)
    after_changed = git_changed_paths(cwd)
    after_git_metadata = git_metadata_snapshot(cwd)
    after_manifest, final_manifest_error = filesystem_manifest(
        cwd,
        args.manifest_max_files,
        args.manifest_max_total_bytes,
        manifest_exclusions,
    )
    if after_manifest is None:
        actual_changed: list[str] = []
        manifest_ok = False
    else:
        actual_changed = manifest_changed_paths(before_manifest, after_manifest)
        manifest_ok = True
    reported_files = (
        (invocation.get("structured_result") or {}).get("files")
        if args.result_schema == "worker-report-v1"
        else None
    )
    head_unchanged = after_head == before_head
    git_metadata_unchanged = after_git_metadata is not None and after_git_metadata == before_git_metadata
    if args.sandbox == "workspace-write":
        reported_files_match = sorted(reported_files or []) == actual_changed
        if manifest_ok:
            scope_ok = (
                head_unchanged
                and git_metadata_unchanged
                and set(actual_changed).issubset(set(allowed or []))
                and reported_files_match
            )
            reconciliation_mode = "filesystem_manifest"
        else:
            scope_ok = vcs_degraded_scope_ok(
                write_capable=True,
                head_unchanged=head_unchanged,
                git_metadata_unchanged=git_metadata_unchanged,
                changed_paths=after_changed,
                allowed_write_paths=allowed or [],
                reported_files=reported_files,
            )
            actual_changed = after_changed or []
            reported_files_match = sorted(reported_files or []) == actual_changed
            reconciliation_mode = "vcs_degraded" if scope_ok else "unavailable"
    else:
        reported_files_match = reported_files is None or reported_files == []
        scope_ok = (
            manifest_ok
            and head_unchanged
            and git_metadata_unchanged
            and actual_changed == []
            and reported_files_match
        )
        reconciliation_mode = "filesystem_manifest" if manifest_ok else "unavailable"
    report["change_manifest"] = {
        "baseline_head": before_head,
        "final_head": after_head,
        "head_unchanged": head_unchanged,
        "baseline_git_metadata": before_git_metadata,
        "final_git_metadata": after_git_metadata,
        "git_metadata_unchanged": git_metadata_unchanged,
        "allowed_write_paths": allowed,
        "manifest_exclusions": manifest_exclusions,
        "actual_changed_paths": actual_changed,
        "out_of_scope_paths": sorted(set(actual_changed) - set(allowed or [])),
        "reported_files": reported_files,
        "reported_files_match": reported_files_match,
        "scope_ok": scope_ok,
        "manifest_ok": manifest_ok,
        "manifest_error": final_manifest_error,
        "reconciliation_mode": reconciliation_mode,
        "degraded_reconciliation": reconciliation_mode == "vcs_degraded",
        "manifest_max_files": args.manifest_max_files,
        "manifest_max_total_bytes": args.manifest_max_total_bytes,
    }
    report["ok"] = bool(invocation["ok"] and scope_ok)
    report["failure_kind"] = (
        invocation.get("failure_kind") if not invocation["ok"] else (None if scope_ok else "scope_violation")
    )
    _write_report(args, artifact_dir, report)
    return 0 if report["ok"] else 5


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning-effort", choices=("low", "medium", "high", "xhigh"), default="low")
    parser.add_argument("--sandbox", choices=("read-only", "workspace-write"), default="read-only")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--codex-binary", default="codex")
    parser.add_argument("--result-schema", choices=("none", "worker-report-v1"), default="none")
    parser.add_argument("--print-full-receipt", action="store_true")
    parser.add_argument("--env-passthrough", action="append", default=[])
    parser.add_argument("--manifest-max-files", type=int, default=20000)
    parser.add_argument("--manifest-exclude", action="append", default=[])
    parser.add_argument(
        "--manifest-max-total-bytes", type=int, default=DEFAULT_MANIFEST_MAX_TOTAL_BYTES
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    preflight = sub.add_parser("preflight", help="run static checks and one tool-capable canary")
    add_common(preflight)
    preflight.set_defaults(func=command_preflight)
    run = sub.add_parser("run", help="run one bounded Codex delegation")
    add_common(run)
    run.add_argument("--cwd", required=True)
    run.add_argument("--task-profile")
    run.add_argument("--target", action="append", default=[])
    run.add_argument("--mission-file")
    run.add_argument("--mission-stdin", action="store_true")
    run.add_argument("--allowed-write", action="append", default=[])
    run.add_argument("--preflight-receipt")
    run.add_argument("--preflight-max-age", type=int, default=1800)
    run.add_argument("--expected-exact")
    run.set_defaults(func=command_run)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")
    if args.manifest_max_files <= 0:
        raise SystemExit("--manifest-max-files must be positive")
    if args.manifest_max_total_bytes <= 0:
        raise SystemExit("--manifest-max-total-bytes must be positive")
    if args.sandbox == "workspace-write" and args.result_schema != "worker-report-v1":
        raise SystemExit("workspace-write requires --result-schema worker-report-v1")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
