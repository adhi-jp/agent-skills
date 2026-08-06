#!/usr/bin/env python3
"""Shared receipt, fingerprint, Git, and filesystem scope-proof helpers."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any

MAX_STDERR_BYTES = 64 * 1024
WORKER_REPORT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["files", "compile", "decisions", "blockers"],
    "properties": {
        "files": {"type": "array", "items": {"type": "string"}},
        "compile": {
            "type": "object",
            "additionalProperties": False,
            "required": ["status", "detail"],
            "properties": {
                "status": {"type": "string", "enum": ["PASS", "FAIL", "SKIPPED"]},
                "detail": {"type": "string"},
            },
        },
        "decisions": {"type": "array", "items": {"type": "string"}},
        "blockers": {"type": "array", "items": {"type": "string"}},
    },
}


def utc_epoch() -> int:
    return int(time.time())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def adapter_files_sha256(paths: list[Path]) -> dict[str, str]:
    return {path.name: sha256_file(path.resolve()) for path in paths}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def print_receipt(args: argparse.Namespace, receipt_path: Path, report: dict[str, Any]) -> None:
    if args.print_full_receipt:
        print(json.dumps(report, ensure_ascii=False))
        return
    invocation = report.get("canary") or report.get("invocation")
    summary: dict[str, Any] = {
        "ok": report.get("ok"),
        "failure_kind": report.get("failure_kind"),
        "receipt": str(receipt_path.resolve()),
    }
    if isinstance(invocation, dict):
        summary.update(
            {
                "thread_id": invocation.get("thread_id") or invocation.get("session_id"),
                "duration_seconds": invocation.get("duration_seconds"),
                "usage": invocation.get("usage"),
                "last_message": (invocation.get("last_message") or {}).get("path"),
            }
        )
    change_manifest = report.get("change_manifest")
    if isinstance(change_manifest, dict) and change_manifest.get("scope_ok") is False:
        summary["scope_ok"] = False
    print(json.dumps(summary, ensure_ascii=False))


def bounded(text: str, limit: int = MAX_STDERR_BYTES) -> tuple[str, bool]:
    raw = text.encode("utf-8", "replace")
    if len(raw) <= limit:
        return text, False
    marker = b"\n[...truncated...]\n"
    kept = raw[: max(0, limit - len(marker))].decode("utf-8", "ignore")
    return kept + marker.decode(), True


def probe_writable_directory(path: Path) -> tuple[bool, str | None]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".vibe-orchestrate-write-probe-", dir=path)
        os.close(fd)
        Path(name).unlink()
        return True, None
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"


def run_git(cwd: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *arguments], cwd=cwd, capture_output=True, check=False)


def git_head(cwd: Path) -> str | None:
    result = run_git(cwd, "rev-parse", "--verify", "HEAD")
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "replace").strip()


def git_changed_paths(cwd: Path) -> list[str] | None:
    tracked = run_git(cwd, "diff", "--name-only", "-z", "HEAD")
    untracked = run_git(cwd, "ls-files", "--others", "--exclude-standard", "-z")
    if tracked.returncode != 0 or untracked.returncode != 0:
        return None
    paths: set[str] = set()
    for payload in (tracked.stdout, untracked.stdout):
        for raw in payload.split(b"\0"):
            if raw:
                paths.add(raw.decode("utf-8", "surrogateescape"))
    return sorted(paths)


def git_metadata_snapshot(cwd: Path) -> dict[str, str | None] | None:
    head = git_head(cwd)
    head_ref = run_git(cwd, "symbolic-ref", "--quiet", "HEAD")
    if head_ref.returncode not in (0, 1):
        return None
    refs = run_git(cwd, "for-each-ref", "--format=%(refname)%00%(objectname)")
    index_entries = run_git(cwd, "ls-files", "--stage", "-z")
    index_flags = run_git(cwd, "ls-files", "-v", "-z")
    if head is None or refs.returncode != 0 or index_entries.returncode != 0 or index_flags.returncode != 0:
        return None
    return {
        "head": head,
        "head_ref": (
            head_ref.stdout.decode("utf-8", "replace").strip()
            if head_ref.returncode == 0
            else None
        ),
        "refs_sha256": hashlib.sha256(refs.stdout).hexdigest(),
        "index_sha256": hashlib.sha256(index_entries.stdout + b"\0" + index_flags.stdout).hexdigest(),
    }


def directory_manifest_value(path: Path) -> str:
    info = path.lstat()
    return ":".join(
        ("dir", f"{info.st_mode & 0o7777:o}", str(info.st_uid), str(info.st_gid), str(info.st_ino))
    )


def leaf_manifest_value(path: Path, kind: str, payload_sha256: str) -> str:
    info = path.lstat()
    return ":".join(
        (
            kind,
            f"{info.st_mode & 0o7777:o}",
            str(info.st_uid),
            str(info.st_gid),
            str(info.st_size),
            str(info.st_mtime_ns),
            str(info.st_ctime_ns),
            str(info.st_ino),
            payload_sha256,
        )
    )


def filesystem_manifest(
    cwd: Path, max_files: int, max_total_bytes: int = 536870912
) -> tuple[dict[str, str] | None, str | None]:
    entries: dict[str, str] = {}
    total_bytes = 0

    def raise_walk_error(error: OSError) -> None:
        raise error

    try:
        for root, dirs, files in os.walk(
            cwd, topdown=True, onerror=raise_walk_error, followlinks=False
        ):
            root_path = Path(root)
            if root_path == cwd:
                entries["."] = directory_manifest_value(root_path)
            dirs[:] = [name for name in dirs if not (root_path == cwd and name == ".git")]
            for name in sorted(set(dirs + files)):
                path = root_path / name
                rel = path.relative_to(cwd).as_posix()
                if rel == ".git" or rel.startswith(".git/"):
                    continue
                if path.is_symlink():
                    payload = os.readlink(path).encode("utf-8", "surrogateescape")
                    entries[rel] = leaf_manifest_value(
                        path, "symlink", hashlib.sha256(payload).hexdigest()
                    )
                elif path.is_file():
                    size = path.lstat().st_size
                    total_bytes += size
                    if total_bytes > max_total_bytes:
                        return None, f"manifest total bytes exceeds {max_total_bytes}"
                    entries[rel] = leaf_manifest_value(path, "file", sha256_file(path))
                elif path.is_dir():
                    entries[rel] = directory_manifest_value(path)
                else:
                    return None, f"unsupported filesystem entry: {rel}"
                if len(entries) > max_files:
                    return None, f"manifest file count exceeds {max_files}"
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return entries, None


def manifest_changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def normalize_allowed_paths(values: list[str]) -> tuple[list[str] | None, str | None]:
    normalized: list[str] = []
    for value in values:
        path = Path(value)
        if path.is_absolute() or value in ("", ".") or ".." in path.parts:
            return None, f"allowed write path must be a non-root relative path: {value!r}"
        normalized.append(path.as_posix())
    return sorted(set(normalized)), None


def worker_report_schema() -> dict[str, Any]:
    return json.loads(json.dumps(WORKER_REPORT_SCHEMA))


def validate_worker_report(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"files", "compile", "decisions", "blockers"}:
        return False
    if not isinstance(value["files"], list) or not all(isinstance(item, str) for item in value["files"]):
        return False
    compile_value = value["compile"]
    if (
        not isinstance(compile_value, dict)
        or set(compile_value) != {"status", "detail"}
        or compile_value.get("status") not in {"PASS", "FAIL", "SKIPPED"}
        or not isinstance(compile_value.get("detail"), str)
    ):
        return False
    for key in ("decisions", "blockers"):
        if not isinstance(value[key], list) or not all(isinstance(item, str) for item in value[key]):
            return False
    return True


def fingerprint_digest(value: dict[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()
