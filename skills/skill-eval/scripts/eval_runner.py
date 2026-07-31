#!/usr/bin/env python3
"""Shared skill eval CLI (slim, runner-driven).

The runner drives execution itself. For each eval x config x run it spawns a
fresh executor subprocess with the prompt only (no assertions), then a fresh
grader subprocess with a clean environment, an isolated empty working directory,
and only the executor output plus the assertions. The executor runs inside the
per-run sandbox repo; the grader does not, so it cannot re-derive ground truth by
reading fixture files and must grade from its prompt alone. It aggregates a
``with_skill`` vs ``without_skill`` raw pass-rate comparison into
``benchmark.json`` and ``benchmark.md``.

All input validation (suite shape, skill source, provider availability, run
bounds) runs before any subprocess launches; invalid input exits non-zero with
zero subprocess launches. Total work is bounded by a hard cap on ``--runs``, a
per-run timeout, and a cap on concurrent provider subprocesses, so a broken rule
cannot trigger large-token or large-parallelism fan-out.

Metrics are never hand-typed or estimated. When a provider exposes machine-
readable usage in its CLI output the runner captures it and stores it with its
source; absence is recorded as absence, never a placeholder number.

The provider selector is a registry, so adding another agent CLI is a new
adapter rather than a hard-coded branch. Optional model flags are passed
through to the selected provider CLI verbatim (whatever model name that CLI
accepts): ``--model`` is the shared default for both roles, and
``--executor-model`` / ``--grader-model`` override it per role. When a role has
no resolved model each provider uses its own default model. This script is
stdlib-only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


ALLOWED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "skill_name",
    "purpose",
    "coverage_notes",
    "common_assertions",
    "evals",
    "scoring",
}
ALLOWED_EVAL_FIELDS = {
    "id",
    "name",
    "project_class",
    "archetype",
    "prompt",
    "expected_output",
    "files",
    "expectations",
}
ALLOWED_SCORING_FIELDS = {
    "common_assertion_weight",
    "per_eval_expectation_weight",
    "pass_threshold",
    "notes",
}

DEFAULT_CONFIGS = ("with_skill", "without_skill")
DEFAULT_AGENT = "claude"
DEFAULT_RUNS = 1
MAX_RUNS = 5
DEFAULT_TIMEOUT_SECONDS = 600.0
DEFAULT_CONCURRENCY = 4
MAX_CONCURRENCY = 16
STDERR_MAX_BYTES = 64 * 1024
SANDBOX_ROOT_ENV = "EVAL_RUNNER_SANDBOX_ROOT"
AGENT_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
# A model name is whatever the selected provider CLI accepts. Stay permissive
# enough for vendor ids like `claude-sonnet-4-6`, `gpt-5.3-codex-spark`, or
# `us.anthropic.claude-opus-4-1-20250805-v1:0`, while requiring a leading
# alphanumeric so a value can never be mistaken for a CLI flag.
MODEL_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")


class CommandError(Exception):
    """Raised for expected CLI failures that should become exit code 1."""


@dataclass
class EvalCase:
    eval_id: str
    name: str
    prompt: str
    expected_output: str
    project_class: str | None
    archetype: str | None
    files: list[str]
    expectations: list[str]
    raw: dict[str, Any]


@dataclass
class EvalSuite:
    path: Path
    skill_name: str
    common_assertions: list[str]
    evals: list[EvalCase]
    scoring: dict[str, Any]
    raw: dict[str, Any]


@dataclass
class ValidationReport:
    path: Path
    skill_name: str | None
    eval_count: int
    common_assertion_count: int
    fixture_count: int
    errors: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class SandboxContext:
    source_repo_root: Path
    repo_root: Path
    skill_path: str | None
    git_initialized: bool
    git_error: str | None = None
    baseline_commit: str | None = None
    copy_strategy: str = "copytree"
    contamination_status: str = "unverified"
    contamination_reason: str | None = None
    excluded_untracked_count: int = 0
    excluded_untracked_sample: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Small IO and path helpers
# --------------------------------------------------------------------------- #
def utc_now() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise CommandError(f"{path}: file not found") from exc
    except json.JSONDecodeError as exc:
        raise CommandError(f"{path}:{exc.lineno}:{exc.colno}: invalid JSON: {exc.msg}") from exc


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def find_repo_root(start: Path) -> Path:
    resolved = start.resolve()
    search_from = resolved if resolved.is_dir() else resolved.parent
    for candidate in (search_from, *search_from.parents):
        if (candidate / "evals").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    return Path.cwd().resolve()


def path_is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def normalize_lexical_path(path: Path) -> Path:
    return Path(os.path.abspath(path))


def path_is_lexically_relative_to(path: Path, parent: Path) -> bool:
    try:
        normalize_lexical_path(path).relative_to(normalize_lexical_path(parent))
        return True
    except ValueError:
        return False


def json_path(base: Path, *parts: Any) -> str:
    suffix = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in parts)
    return f"{base}{suffix}"


def resolve_declared_file(value: str, evals_path: Path, repo_root: Path) -> Path | None:
    declared = Path(value)
    if declared.is_absolute():
        candidates = [declared]
    else:
        candidates = [
            repo_root / declared,
            evals_path.parent / declared,
            evals_path.parent / "fixtures" / declared,
        ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def suite_fixture_roots(suite: EvalSuite, repo_root: Path) -> list[Path]:
    roots: list[Path] = []
    seen: set[Path] = set()
    fixtures_root = repo_root / "evals" / suite.skill_name / "fixtures"
    for case in suite.evals:
        for declared_file in case.files:
            resolved = resolve_declared_file(declared_file, suite.path, repo_root)
            if resolved is None:
                continue
            try:
                rel_to_fixtures = resolved.resolve().relative_to(fixtures_root.resolve())
            except ValueError:
                root = resolved
            else:
                root = fixtures_root / rel_to_fixtures.parts[0] if rel_to_fixtures.parts else fixtures_root
            root = root.resolve()
            if root not in seen:
                seen.add(root)
                roots.append(root)
    return roots


def source_fixture_status(suite: EvalSuite, repo_root: Path) -> dict[str, Any]:
    roots = suite_fixture_roots(suite, repo_root)
    result: dict[str, Any] = {
        "checked": bool(roots),
        "dirty": False,
        "paths": [str(path.relative_to(repo_root)) for path in roots],
        "entries": [],
        "error": None,
    }
    if not roots:
        return result
    git = shutil.which("git")
    if not git:
        result["error"] = "git executable not found"
        return result
    command = [git, "status", "--short", "--", *[str(path.relative_to(repo_root)) for path in roots]]
    completed = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        result["error"] = completed.stderr.strip() or completed.stdout.strip() or "git status failed"
        return result
    entries = [line for line in completed.stdout.splitlines() if line.strip()]
    result["entries"] = entries
    result["dirty"] = bool(entries)
    return result


def combine_source_fixture_status(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    entries: list[str] = []
    for phase, status in (("before", before), ("after", after)):
        for entry in status.get("entries") or []:
            entries.append(f"{phase}: {entry}")
    errors = [str(status.get("error")) for status in (before, after) if status.get("error")]
    return {
        "checked": bool(before.get("checked") or after.get("checked")),
        "dirty": bool(before.get("dirty") or after.get("dirty")),
        "paths": sorted(set(before.get("paths") or []) | set(after.get("paths") or [])),
        "entries": entries,
        "error": "; ".join(errors) if errors else None,
        "before": before,
        "after": after,
    }


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "unnamed"


def parse_csv_values(values: list[str] | None, default: tuple[str, ...]) -> list[str]:
    if not values:
        return list(default)
    result: list[str] = []
    for value in values:
        for part in value.split(","):
            part = part.strip()
            if part and part not in result:
                result.append(part)
    return result or list(default)


def select_eval_cases(
    suite: EvalSuite, values: list[str] | None
) -> tuple[EvalSuite, dict[str, Any]]:
    """Return the requested eval subset plus an explicit coverage record.

    A subset is a diagnostic measurement, not full-suite closing evidence.  The
    coverage record is persisted in the manifest and benchmark so a cheap
    targeted rerun cannot later be mistaken for a complete suite result.
    """
    suite_ids = [case.eval_id for case in suite.evals]
    if values is None:
        selected_ids = list(suite_ids)
    else:
        selected_ids = parse_csv_values(values, ())
        if not selected_ids:
            raise CommandError("--eval-id: provide at least one non-empty eval id")
        unknown = [eval_id for eval_id in selected_ids if eval_id not in suite_ids]
        if unknown:
            raise CommandError(
                "--eval-id: unknown eval id(s): "
                + ", ".join(unknown)
                + "; available ids: "
                + (", ".join(suite_ids) if suite_ids else "none")
            )

    selected_set = set(selected_ids)
    selected_cases = [case for case in suite.evals if case.eval_id in selected_set]
    selected_ids = [case.eval_id for case in selected_cases]
    partial = len(selected_cases) < len(suite.evals)
    coverage = {
        "mode": "selected" if partial else "full",
        "suite_eval_count": len(suite.evals),
        "selected_eval_count": len(selected_cases),
        "selected_eval_ids": selected_ids,
        "partial": partial,
        "closing_eligible": not partial,
    }
    if not partial:
        return suite, coverage
    return (
        EvalSuite(
            path=suite.path,
            skill_name=suite.skill_name,
            common_assertions=suite.common_assertions,
            evals=selected_cases,
            scoring=suite.scoring,
            raw=suite.raw,
        ),
        coverage,
    )


def validate_agent_label(value: str | None) -> str:
    label = (value or DEFAULT_AGENT).strip()
    if not AGENT_LABEL_RE.match(label):
        raise CommandError(
            f"--agent {value!r}: label must match {AGENT_LABEL_RE.pattern}"
        )
    return label


def validate_model_label(value: str | None, flag: str = "--model") -> str | None:
    if value is None:
        return None
    label = value.strip()
    if not label:
        return None
    if not MODEL_LABEL_RE.match(label):
        raise CommandError(
            f"{flag} {value!r}: model must match {MODEL_LABEL_RE.pattern}"
        )
    return label


# --------------------------------------------------------------------------- #
# Suite validation and loading
# --------------------------------------------------------------------------- #
def validate_string_list(value: Any, field_path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{field_path}: expected list")
        return []
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(f"{field_path}[{index}]: expected string")
            continue
        result.append(item)
    return result


def validate_eval_suite(evals_path: Path) -> ValidationReport:
    evals_path = evals_path.resolve()
    repo_root = find_repo_root(evals_path)
    errors: list[str] = []
    fixture_count = 0
    skill_name: str | None = None
    eval_count = 0
    common_assertion_count = 0

    try:
        data = read_json(evals_path)
    except CommandError as exc:
        return ValidationReport(evals_path, None, 0, 0, 0, [str(exc)])

    if not isinstance(data, dict):
        return ValidationReport(evals_path, None, 0, 0, 0, [f"{evals_path}: expected top-level object"])

    for field_name in sorted(set(data) - ALLOWED_TOP_LEVEL_FIELDS):
        errors.append(f"{json_path(evals_path, field_name)}: unsupported top-level field")

    raw_skill_name = data.get("skill_name")
    if isinstance(raw_skill_name, str) and raw_skill_name.strip():
        skill_name = raw_skill_name
    else:
        errors.append(f"{json_path(evals_path, 'skill_name')}: missing required non-empty string")

    common_assertions = data.get("common_assertions", [])
    if "common_assertions" in data:
        common_assertions = validate_string_list(
            common_assertions, json_path(evals_path, "common_assertions"), errors
        )
    elif not isinstance(common_assertions, list):
        common_assertions = []
    common_assertion_count = len(common_assertions)

    scoring = data.get("scoring", {})
    if "scoring" in data:
        if not isinstance(scoring, dict):
            errors.append(f"{json_path(evals_path, 'scoring')}: expected object")
        else:
            for field_name in sorted(set(scoring) - ALLOWED_SCORING_FIELDS):
                errors.append(f"{json_path(evals_path, 'scoring', field_name)}: unsupported scoring field")

    raw_evals = data.get("evals")
    if not isinstance(raw_evals, list):
        errors.append(f"{json_path(evals_path, 'evals')}: missing required list")
        raw_evals = []
    eval_count = len(raw_evals)

    seen_ids: dict[str, int] = {}
    for index, item in enumerate(raw_evals):
        item_path = json_path(evals_path, "evals", index)
        if not isinstance(item, dict):
            errors.append(f"{item_path}: expected object")
            continue

        for field_name in sorted(set(item) - ALLOWED_EVAL_FIELDS):
            errors.append(f"{item_path}.{field_name}: unsupported eval field")

        raw_id = item.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            errors.append(f"{item_path}.id: missing required non-empty string")
        elif raw_id in seen_ids:
            errors.append(
                f"{item_path}.id: duplicate eval id {raw_id!r}; first seen at evals[{seen_ids[raw_id]}]"
            )
        else:
            seen_ids[raw_id] = index

        raw_prompt = item.get("prompt")
        if not isinstance(raw_prompt, str) or not raw_prompt.strip():
            errors.append(f"{item_path}.prompt: missing required non-empty string")

        if "name" in item and not isinstance(item.get("name"), str):
            errors.append(f"{item_path}.name: expected string")
        if "expected_output" in item and not isinstance(item.get("expected_output"), str):
            errors.append(f"{item_path}.expected_output: expected string")
        if "project_class" in item and not isinstance(item.get("project_class"), str):
            errors.append(f"{item_path}.project_class: expected string")
        if "archetype" in item and not isinstance(item.get("archetype"), str):
            errors.append(f"{item_path}.archetype: expected string")

        files = validate_string_list(item.get("files", []), f"{item_path}.files", errors)
        for file_value in files:
            fixture_count += 1
            if resolve_declared_file(file_value, evals_path, repo_root) is None:
                errors.append(f"{item_path}.files: missing fixture file {file_value!r}")

        validate_string_list(item.get("expectations", []), f"{item_path}.expectations", errors)

    return ValidationReport(
        path=evals_path,
        skill_name=skill_name,
        eval_count=eval_count,
        common_assertion_count=common_assertion_count,
        fixture_count=fixture_count,
        errors=errors,
    )


def print_validation_report(report: ValidationReport) -> None:
    if report.ok:
        print(f"OK: {report.path}")
        print(f"skill_name: {report.skill_name}")
        print(f"evals: {report.eval_count}")
        print(f"common_assertions: {report.common_assertion_count}")
        print(f"fixtures: {report.fixture_count} checked")
        return
    for error in report.errors:
        print(error, file=sys.stderr)


def load_eval_suite(evals_path: Path) -> EvalSuite:
    report = validate_eval_suite(evals_path)
    if not report.ok:
        raise CommandError("\n".join(report.errors))
    data = read_json(report.path)
    evals: list[EvalCase] = []
    for item in data["evals"]:
        evals.append(
            EvalCase(
                eval_id=item["id"],
                name=item.get("name") or item["id"],
                prompt=item["prompt"],
                expected_output=item.get("expected_output", ""),
                project_class=item.get("project_class"),
                archetype=item.get("archetype"),
                files=list(item.get("files", [])),
                expectations=list(item.get("expectations", [])),
                raw=dict(item),
            )
        )
    return EvalSuite(
        path=report.path,
        skill_name=data["skill_name"],
        common_assertions=list(data.get("common_assertions", [])),
        evals=evals,
        scoring=dict(data.get("scoring", {})),
        raw=dict(data),
    )


# --------------------------------------------------------------------------- #
# Authoritative skill source resolution (folds the old snapshot-guard hook into
# the runner so every provider gets the same source-package guarantee).
# --------------------------------------------------------------------------- #
def normalize_skill_source_path(path: Path) -> Path:
    candidate = path
    if candidate.is_dir():
        candidate = candidate / "SKILL.md"
    if candidate.name != "SKILL.md" or not candidate.is_file():
        raise CommandError(
            f"{path}: skill path must be a SKILL.md file or a skill package directory containing SKILL.md"
        )
    return candidate.resolve()


def skill_source_candidate_file(path: Path) -> Path:
    if path.is_dir():
        return path / "SKILL.md"
    return path


def validate_skill_source_name(skill_name: str) -> None:
    if (
        not skill_name
        or skill_name in {".", ".."}
        or "/" in skill_name
        or "\\" in skill_name
        or Path(skill_name).is_absolute()
    ):
        raise CommandError(f"skill_name {skill_name!r}: with_skill requires a single skills/ path segment")


def validate_authoritative_skill_source_path(
    source_path: Path,
    repo_root: Path,
    skill_name: str,
    requested_path: Path,
) -> None:
    disallowed_roots = [repo_root / ".agents" / "skills", repo_root / ".claude" / "skills"]
    for disallowed_root in disallowed_roots:
        if path_is_lexically_relative_to(requested_path, disallowed_root) or path_is_relative_to(
            source_path, disallowed_root
        ):
            raise CommandError(
                f"{source_path}: with_skill must use an authoritative source skill, not a local skill snapshot or Claude link"
            )

    expected_source = normalize_lexical_path(repo_root / "skills" / skill_name / "SKILL.md")
    requested_source = normalize_lexical_path(skill_source_candidate_file(requested_path))
    if requested_source != expected_source:
        raise CommandError(f"{source_path}: with_skill must use the authoritative skills/{skill_name}/SKILL.md source")

    skill_root = repo_root / "skills" / skill_name
    if not path_is_relative_to(source_path, skill_root):
        raise CommandError(
            f"{source_path}: with_skill must use an authoritative source skill under {skill_root}, "
            "not an external, cached, or host-installed skill path"
        )


def resolve_skill_source_path(suite: EvalSuite, raw_skill_path: str | None, configs: list[str]) -> str | None:
    if "with_skill" not in configs:
        return None

    repo_root = find_repo_root(suite.path)
    validate_skill_source_name(suite.skill_name)
    if raw_skill_path:
        requested = Path(raw_skill_path)
        candidates = [requested] if requested.is_absolute() else [repo_root / requested]
        source_path: Path | None = None
        errors: list[str] = []
        for candidate in candidates:
            try:
                normalized = normalize_skill_source_path(candidate)
                validate_authoritative_skill_source_path(normalized, repo_root, suite.skill_name, candidate)
                source_path = normalized
                break
            except CommandError as exc:
                errors.append(str(exc))
        if source_path is None:
            raise CommandError(f"--skill-path {raw_skill_path!r}: " + "; ".join(errors))
    else:
        default_source = repo_root / "skills" / suite.skill_name / "SKILL.md"
        if not default_source.is_file():
            raise CommandError(
                "with_skill requires --skill-path or an existing "
                f"{(Path('skills') / suite.skill_name / 'SKILL.md').as_posix()} source file"
            )
        source_path = default_source.resolve()

    validate_authoritative_skill_source_path(
        source_path,
        repo_root,
        suite.skill_name,
        repo_root / "skills" / suite.skill_name / "SKILL.md",
    )
    return str(source_path)


# --------------------------------------------------------------------------- #
# Workspace layout
# --------------------------------------------------------------------------- #
def default_workspace_root(evals_path: Path, agent: str) -> Path:
    return evals_path.parent / "workspace" / agent


def next_iteration_number(workspace_root: Path) -> int:
    if not workspace_root.is_dir():
        return 1
    numbers = []
    for child in workspace_root.iterdir():
        match = re.match(r"iteration-(\d+)$", child.name)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) + 1 if numbers else 1


def unique_eval_dir_name(case: EvalCase, used: set[str]) -> str:
    base = f"eval-{slugify(case.name or case.eval_id)}"
    name = base
    counter = 2
    while name in used:
        name = f"{base}-{counter}"
        counter += 1
    used.add(name)
    return name


# Upper bound on written-artifact bytes folded into the grader prompt. Real plan
# artifacts run tens of KB; the cap only guards against a pathological file
# blowing up the grader context, and truncation is recorded, never silent.
ARTIFACT_MAX_CHARS = 400_000


# Provider subprocesses must not run in the real repository. Some eval prompts
# intentionally pressure file edits, dependency installs, and commits; executing
# those against the source checkout contaminates later runs. For git-backed
# source checkouts, each run gets tracked files copied with their current
# working-tree contents, with untracked/ignored leftovers and host-local state
# excluded. A throwaway git repository is initialized so accidental commits stay
# contained.
SANDBOX_EXCLUDED_DIR_NAMES = {
    ".git",
    ".agents",
    ".claude",
    ".codex",
    ".local-workspaces",
    "__pycache__",
    "node_modules",
}
SANDBOX_UNTRACKED_SAMPLE_LIMIT = 10


def sanitized_git_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(key, None)
    return env


def run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    git = shutil.which("git")
    if not git:
        raise CommandError("git executable not found")
    return subprocess.run(
        [git, "-C", str(repo_root), *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        env=sanitized_git_env(),
        check=False,
    )


def split_nul_paths(output: str) -> list[str]:
    return [entry for entry in output.split("\0") if entry]


def sandbox_relative_path_is_excluded(path: Path) -> bool:
    parts = path.parts
    if any(part in SANDBOX_EXCLUDED_DIR_NAMES for part in parts):
        return True
    if parts and parts[0] == "evals" and "workspace" in parts[1:]:
        return True
    return False


def sandbox_copy_ignore(repo_root: Path) -> Callable[[str, list[str]], set[str]]:
    def ignore(directory: str, names: list[str]) -> set[str]:
        current = Path(directory)
        ignored: set[str] = set()
        for name in names:
            candidate = current / name
            if candidate.is_dir() and name in SANDBOX_EXCLUDED_DIR_NAMES:
                ignored.add(name)
                continue
            if candidate.is_dir() and name == "workspace" and path_is_lexically_relative_to(
                candidate, repo_root / "evals"
            ):
                ignored.add(name)
        return ignored

    return ignore


def initialize_sandbox_git(repo_root: Path) -> tuple[bool, str | None, str | None]:
    git = shutil.which("git")
    if not git:
        return False, "git executable not found", None

    env = sanitized_git_env()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Eval Sandbox",
            "GIT_AUTHOR_EMAIL": "eval-sandbox@example.invalid",
            "GIT_COMMITTER_NAME": "Eval Sandbox",
            "GIT_COMMITTER_EMAIL": "eval-sandbox@example.invalid",
        }
    )
    commands = [
        [git, "init"],
        [git, "config", "commit.gpgsign", "false"],
        [git, "add", "-A"],
        [git, "commit", "--no-gpg-sign", "--no-verify", "-m", "eval sandbox baseline"],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            cwd=repo_root,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "unknown git error"
            return False, f"{command[:2]} failed: {stderr}", None
    baseline = subprocess.run(
        [git, "rev-parse", "--verify", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if baseline.returncode != 0:
        stderr = baseline.stderr.strip() or baseline.stdout.strip() or "git rev-parse failed"
        return False, f"baseline commit lookup failed: {stderr}", None
    return True, None, baseline.stdout.strip()


def listed_source_paths(source_repo_root: Path, args: list[str]) -> list[str]:
    result = run_git(source_repo_root, args)
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise CommandError(f"git {' '.join(args)} failed while building eval sandbox: {stderr}")
    return split_nul_paths(result.stdout)


def source_git_toplevel(source_repo_root: Path) -> Path | None:
    if not shutil.which("git"):
        if (source_repo_root / ".git").exists():
            raise CommandError(
                f"{source_repo_root}: .git exists but git executable was not found; "
                "refusing contaminated copytree fallback"
            )
        return None

    result = run_git(source_repo_root, ["rev-parse", "--show-toplevel"])
    if result.returncode != 0:
        if (source_repo_root / ".git").exists():
            stderr = result.stderr.strip() or result.stdout.strip() or "git rev-parse failed"
            raise CommandError(f"{source_repo_root}: git repository could not be inspected: {stderr}")
        return None
    return Path(result.stdout.strip()).resolve()


def collect_excluded_untracked_paths(source_repo_root: Path) -> list[str]:
    paths: set[str] = set()
    for args in (
        ["ls-files", "-z", "--others", "--exclude-standard", "--full-name"],
        ["ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--full-name"],
    ):
        paths.update(listed_source_paths(source_repo_root, args))
    return sorted(paths)


def copy_tracked_working_tree(source_repo_root: Path, sandbox_repo_root: Path) -> tuple[int, list[str]]:
    tracked_paths = listed_source_paths(source_repo_root, ["ls-files", "-z", "--full-name"])
    excluded_untracked = collect_excluded_untracked_paths(source_repo_root)
    sandbox_repo_root.mkdir(parents=True, exist_ok=True)
    for path_text in tracked_paths:
        rel_path = Path(path_text)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise CommandError(f"git tracked path is not repository-relative: {path_text!r}")
        if sandbox_relative_path_is_excluded(rel_path):
            continue
        source_path = source_repo_root / rel_path
        if not source_path.exists():
            # Preserve working-tree deletion symmetry: a tracked path deleted
            # locally must not be resurrected from HEAD in the sandbox.
            continue
        if source_path.is_symlink() or not source_path.is_file():
            # Defensive guard for non-regular tracked entries such as symlinks or
            # gitlinks. None are expected in the current repository.
            continue
        destination = sandbox_repo_root / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
    return len(excluded_untracked), excluded_untracked[:SANDBOX_UNTRACKED_SAMPLE_LIMIT]


def remap_path_into_sandbox(path: str | None, source_repo_root: Path, sandbox_repo_root: Path) -> str | None:
    if path is None:
        return None
    source_path = Path(path)
    try:
        rel = source_path.resolve().relative_to(source_repo_root.resolve())
    except ValueError:
        return path
    return str((sandbox_repo_root / rel).resolve())


def create_run_sandbox(source_repo_root: Path, run_dir: Path, skill_path: str | None) -> SandboxContext:
    source_repo_root = source_repo_root.resolve()
    run_dir = run_dir.resolve()
    sandbox_repo_root = external_sandbox_repo_root(run_dir)
    if path_is_lexically_relative_to(sandbox_repo_root, source_repo_root):
        raise CommandError(f"sandbox root must be outside the source checkout: {sandbox_repo_root}")
    if sandbox_repo_root.exists():
        shutil.rmtree(sandbox_repo_root)
    sandbox_repo_root.parent.mkdir(parents=True, exist_ok=True)
    copy_strategy = "git_tracked_working_tree"
    contamination_status = "verified_tracked_only"
    contamination_reason: str | None = None
    excluded_untracked_count = 0
    excluded_untracked_sample: list[str] = []
    git_toplevel = source_git_toplevel(source_repo_root)
    if git_toplevel is None:
        copy_strategy = "copytree"
        contamination_status = "unverified"
        contamination_reason = "source_not_git_repository"
        shutil.copytree(
            source_repo_root,
            sandbox_repo_root,
            ignore=sandbox_copy_ignore(source_repo_root),
        )
    else:
        if git_toplevel != source_repo_root:
            raise CommandError(
                f"{source_repo_root}: eval sandbox source must be the git toplevel; got {git_toplevel}"
            )
        excluded_untracked_count, excluded_untracked_sample = copy_tracked_working_tree(
            source_repo_root, sandbox_repo_root
        )
    git_initialized, git_error, baseline_commit = initialize_sandbox_git(sandbox_repo_root)
    return SandboxContext(
        source_repo_root=source_repo_root,
        repo_root=sandbox_repo_root,
        skill_path=remap_path_into_sandbox(skill_path, source_repo_root, sandbox_repo_root),
        git_initialized=git_initialized,
        git_error=git_error,
        baseline_commit=baseline_commit,
        copy_strategy=copy_strategy,
        contamination_status=contamination_status,
        contamination_reason=contamination_reason,
        excluded_untracked_count=excluded_untracked_count,
        excluded_untracked_sample=excluded_untracked_sample,
    )


def sandbox_base_dir() -> Path:
    configured = os.environ.get(SANDBOX_ROOT_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(tempfile.gettempdir()) / "eval-runner-sandboxes").resolve()


def external_sandbox_repo_root(run_dir: Path) -> Path:
    resolved_run_dir = run_dir.resolve()
    digest = hashlib.sha256(str(resolved_run_dir).encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", resolved_run_dir.name).strip("-") or "run"
    return (sandbox_base_dir() / f"{slug}-{digest}" / "repo").resolve()


def grader_working_dir(run_dir: Path) -> Path:
    """Return an empty, isolated working directory for the grader subprocess.

    The grader must decide pass/fail from its prompt alone (recorded output,
    assertions, and the runner-provided file-change/tool-evidence sections). If
    the grader ran in the sandbox repo it could re-read fixtures and grade
    against ground truth the executor never had -- and when two evals share a
    plan title (for example an inline plan and a file-backed fixture plan with
    the same heading), it can silently bind to the wrong file and fail an
    accurate executor for "inventing" text that only lives in the other file.
    Pointing the grader at an empty per-run directory removes that filesystem
    escape hatch without touching the executor's sandbox.
    """
    grader_dir = (external_sandbox_repo_root(run_dir).parent / "grader-cwd").resolve()
    if grader_dir.exists():
        shutil.rmtree(grader_dir)
    grader_dir.mkdir(parents=True, exist_ok=True)
    return grader_dir


def collect_written_artifact(artifact_file: Path) -> tuple[str | None, dict[str, Any]]:
    """Read a file the executor wrote to the designated artifact path, if any.

    Returns ``(artifact_text, info)``. ``artifact_text`` is ``None`` when no file
    was written (the common case for skills whose deliverable is the chat reply),
    so the grader prompt is unchanged for those runs. ``info`` records presence,
    byte/char counts, and whether the text was truncated for the grader.
    """
    if not artifact_file.is_file():
        return None, {"captured": False}
    raw = artifact_file.read_text(encoding="utf-8", errors="replace")
    info: dict[str, Any] = {
        "captured": True,
        "path": str(artifact_file),
        "chars": len(raw),
        "truncated": False,
    }
    if len(raw) > ARTIFACT_MAX_CHARS:
        raw = raw[:ARTIFACT_MAX_CHARS] + "\n[...artifact truncated for grading...]\n"
        info["truncated"] = True
    return raw, info


# The grader otherwise sees only the executor's chat reply plus one designated
# artifact path, so a self-narrated claim like "I reused/updated an existing
# spec" cannot be checked. This manifest is the real set of files the executor
# created, modified, or deleted in its sandbox relative to the pre-execution
# baseline commit, so the grader can verify such claims. The runtime scaffold is
# excluded because the runner itself owns those paths.
SANDBOX_MANIFEST_EXCLUDED_PREFIX = ".eval-runner/"


def sha256_path(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def collect_sandbox_change_manifest(sandbox: SandboxContext) -> dict[str, Any]:
    """Diff the sandbox working tree against its baseline commit and return the
    real created/modified/deleted file set outside the runtime scaffold.

    ``--no-renames`` keeps every entry a single-letter status so a rename is
    reported as an add plus a delete, and untracked additions are read from
    ``ls-files --others`` so a newly written file is captured without staging.
    Config-symmetric: the runner computes it identically for ``with_skill`` and
    ``without_skill``."""
    if not sandbox.git_initialized:
        return {
            "captured": False,
            "reason": sandbox.git_error or "sandbox git not initialized",
            "entries": [],
        }
    if not sandbox.baseline_commit:
        return {
            "captured": False,
            "reason": "sandbox baseline commit unavailable",
            "entries": [],
        }
    try:
        diff = run_git(
            sandbox.repo_root,
            ["diff", "--name-status", "-z", "--no-renames", sandbox.baseline_commit],
        )
        others = run_git(sandbox.repo_root, ["ls-files", "--others", "--exclude-standard", "-z"])
    except CommandError as exc:
        return {"captured": False, "reason": str(exc), "entries": []}
    if diff.returncode != 0:
        return {"captured": False, "reason": diff.stderr.strip() or "git diff failed", "entries": []}
    if others.returncode != 0:
        return {"captured": False, "reason": others.stderr.strip() or "git ls-files failed", "entries": []}

    entries: dict[str, dict[str, Any]] = {}
    tokens = diff.stdout.split("\0")
    index = 0
    while index + 1 < len(tokens):
        status_code = tokens[index]
        rel = tokens[index + 1]
        index += 2
        if not status_code or not rel or rel.startswith(SANDBOX_MANIFEST_EXCLUDED_PREFIX):
            continue
        code = status_code[0]
        if code == "D":
            entries[rel] = {"path": rel, "status": "deleted", "sha256": None}
        elif code == "A":
            entries[rel] = {"path": rel, "status": "added", "sha256": sha256_path(sandbox.repo_root / rel)}
        else:
            entries[rel] = {"path": rel, "status": "modified", "sha256": sha256_path(sandbox.repo_root / rel)}
    for rel in split_nul_paths(others.stdout):
        if rel.startswith(SANDBOX_MANIFEST_EXCLUDED_PREFIX):
            continue
        entries.setdefault(
            rel, {"path": rel, "status": "added", "sha256": sha256_path(sandbox.repo_root / rel)}
        )
    ordered = sorted(entries.values(), key=lambda entry: entry["path"])
    return {
        "captured": True,
        "excluded_prefix": SANDBOX_MANIFEST_EXCLUDED_PREFIX,
        "entries": ordered,
    }


# --------------------------------------------------------------------------- #
# Executor evidence: host-recorded tool/delegation trace.
#
# The grader otherwise sees only the executor's final response, one designated
# artifact, and the sandbox file manifest. None of those record whether the
# executor really invoked host tools or delegated sub-agents, so a grader has to
# guess whether an ``agentId``/``task ID`` a truthful executor cites is a real
# host record or a fabricated string -- and a guessing grader can wrongly rule a
# genuine host-issued id "fabricated". This collector reads the host's own
# transcript for the executor session and folds a *redacted* trace (tool names
# and host-issued ids only) into the grader prompt, so delegation-proof
# assertions score against a real record instead of a guess.
#
# Redaction is mandatory: the transcript also holds the executor's full prompt,
# reasoning, and tool results, none of which may reach the grader or the
# executor's own content would flow back into scoring. Only tool names and
# host-issued identifiers/locators leave this function.
#
# Claude-only precision: the trace is derived from the Claude CLI ``session_id``
# and the host transcript layout. Providers that expose no equivalent record
# stay ``captured=false`` with a reason, matching the additive Claude-only
# contract the metrics path already uses.
# --------------------------------------------------------------------------- #
EXECUTOR_EVIDENCE_MAX_ENTRIES = 200


def claude_config_dir() -> Path:
    """Honor CLAUDE_CONFIG_DIR; fall back to the default ~/.claude home."""
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    if configured and configured.strip():
        return Path(configured).expanduser()
    return Path.home() / ".claude"


def encode_claude_project_dir(cwd: Path) -> str:
    """Claude Code stores a session transcript under
    ``<config>/projects/<encoded-cwd>/<session_id>.jsonl``, where the project
    directory name is the absolute cwd with every non-alphanumeric character
    replaced by ``-``."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(cwd.resolve()))


def find_claude_transcript(session_id: str, cwd: Path) -> Path | None:
    """Locate the host transcript for a Claude session id. Prefer the encoded
    cwd directory; fall back to scanning every project dir so a small encoding
    mismatch does not lose the record."""
    projects = claude_config_dir() / "projects"
    if not projects.is_dir():
        return None
    preferred = projects / encode_claude_project_dir(cwd) / f"{session_id}.jsonl"
    if preferred.is_file():
        return preferred
    try:
        matches = sorted(projects.glob(f"*/{session_id}.jsonl"))
    except OSError:
        return None
    return matches[0] if matches else None


def _iter_jsonl(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def extract_claude_tool_evidence(transcript: Path) -> list[dict[str, Any]]:
    """Pull only tool names and host-issued tool-use ids from a transcript.

    Deliberately ignores every other field -- prompt text, assistant reasoning,
    and tool_result payloads never leave this function -- so the executor's own
    content cannot flow back into grading."""
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in _iter_jsonl(transcript):
        if not isinstance(record, dict):
            continue
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "tool_use":
                continue
            tool_id = item.get("id")
            name = item.get("name")
            if not isinstance(tool_id, str) or tool_id in seen:
                continue
            seen.add(tool_id)
            entry: dict[str, Any] = {"type": "tool_use", "id": tool_id}
            if isinstance(name, str) and name.strip():
                entry["name"] = name.strip()
            entries.append(entry)
            if len(entries) >= EXECUTOR_EVIDENCE_MAX_ENTRIES:
                return entries
    return entries


def extract_claude_subagent_evidence(transcript: Path, session_id: str) -> list[dict[str, Any]]:
    """List host-created sub-agent record files by their host-issued id.

    Only the id (from the file name) and the record path are emitted; the
    sub-agent transcript contents are never read into the grader prompt."""
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    candidate_dirs = [
        transcript.parent / session_id / "subagents",
        transcript.with_suffix("") / "subagents",
        transcript.parent / "subagents",
    ]
    for directory in candidate_dirs:
        if not directory.is_dir():
            continue
        try:
            files = sorted(directory.glob("agent-*.jsonl"))
        except OSError:
            continue
        for record_file in files:
            agent_id = record_file.stem[len("agent-"):]
            if not agent_id or agent_id in seen:
                continue
            seen.add(agent_id)
            entries.append(
                {"type": "subagent", "id": agent_id, "record_path": str(record_file)}
            )
            if len(entries) >= EXECUTOR_EVIDENCE_MAX_ENTRIES:
                return entries
    return entries


def collect_executor_evidence(metrics: dict[str, Any], cwd: Path) -> dict[str, Any]:
    """Return a redacted, host-recorded tool/delegation trace for the executor.

    Reads host state (the Claude transcript under the config home), not sandbox
    state, so the record is flagged ``source: host`` to keep that boundary
    explicit. Providers without an exposed session locator, or runs whose
    transcript cannot be found, stay ``captured=false`` with a reason so the
    grader never treats absence as disproof."""
    provider = metrics.get("provider")
    if provider != "claude":
        return {
            "captured": False,
            "source": "host",
            "reason": f"executor evidence capture is not available for provider {provider!r}",
            "entries": [],
        }
    session_id = metrics.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        return {
            "captured": False,
            "source": "host",
            "reason": "provider did not expose a session id",
            "entries": [],
        }
    session_id = session_id.strip()
    transcript = find_claude_transcript(session_id, cwd)
    if transcript is None:
        return {
            "captured": False,
            "source": "host",
            "session_id": session_id,
            "reason": "host transcript not found for session id",
            "entries": [],
        }
    entries = extract_claude_tool_evidence(transcript)
    entries.extend(extract_claude_subagent_evidence(transcript, session_id))
    return {
        "captured": True,
        "source": "host",
        "session_id": session_id,
        "transcript_path": str(transcript),
        "note": "Host-recorded trace read from the Claude transcript home, not the sandbox. Only tool names and host-issued ids are included; prompt text, reasoning, and tool results are redacted.",
        "entries": entries,
    }


# --------------------------------------------------------------------------- #
# Prompt rendering: executor gets the task only; grader gets output + assertions.
# --------------------------------------------------------------------------- #
def render_executor_prompt(
    suite: EvalSuite,
    case: EvalCase,
    config: str,
    skill_path: str | None,
    artifact_path: str | None = None,
) -> str:
    lines = ["# Eval Run Prompt", ""]
    if config == "with_skill":
        lines.append(f"- Skill: `{suite.skill_name}`")
    lines.extend(
        [
            f"- Eval id: `{case.eval_id}`",
            f"- Eval name: {case.name}",
            f"- Configuration: `{config}`",
        ]
    )
    if config == "with_skill" and skill_path:
        lines.append(f"- Skill path: `{skill_path}`")
    lines.extend(["", "## Configuration Contract", ""])
    if config == "without_skill":
        lines.append(
            "Do not use any skill package, local skill file, installed skill tool, "
            "`.agents/skills` snapshot, `.claude/skills` link, or cached skill copy for this "
            "run. Use only the base agent behavior and the prompt below."
        )
    elif config == "with_skill" and skill_path:
        lines.extend(
            [
                "Read the target skill directly from the Skill path listed above before answering. "
                "Treat that source file and the referenced files in its skill package as the skill content for this run.",
                "Do not invoke an installed host skill tool, host skill picker, `.agents/skills` snapshot, "
                "`.claude/skills` link, or cached skill copy as a substitute for the listed source path.",
            ]
        )
    else:
        lines.append("Use the target skill content available to the invoking agent for this run.")
    lines.extend(["", "## User Prompt", "", case.prompt.strip(), ""])
    if case.files:
        lines.extend(["## Fixture Files", ""])
        lines.extend(f"- `{file_name}`" for file_name in case.files)
        lines.append("")
    lines.extend(
        [
            "## Response Contract",
            "",
            "- Answer the user prompt directly as your final response.",
            "- Do not grade your own output, score it, or judge pass/fail; a separate grader handles that.",
        ]
    )
    if artifact_path:
        # Config-symmetric capture hook: when a workflow's deliverable is a
        # written file (an implementation plan, spec, or other primary Markdown
        # artifact) rather than the chat reply, the grader otherwise only sees
        # the concise chat summary and cannot credit the artifact's contents.
        # Naming a fixed path lets the runner fold the written file into the
        # grader's recorded output without leaking any target behavior.
        lines.append(
            "- If your workflow writes a plan, specification, or other primary Markdown "
            f"artifact to a file as its deliverable, write that file to this exact path: `{artifact_path}`. "
            "The grader is shown both your final response and the contents of any file written to that "
            "path, so a concise final response that points to that file is graded together with the "
            "file's contents. This is a capture destination, not a request to create an artifact: "
            "write it only when the user prompt or the workflow's normal deliverable contract independently "
            "requires a file; otherwise answer in chat and leave the path unused."
        )
    return "\n".join(lines) + "\n"


def assertions_for_case(suite: EvalSuite, case: EvalCase) -> list[str]:
    # De-duplicate while preserving first-seen order so a common assertion that
    # also appears as a per-eval expectation is graded and counted once, not
    # twice (which would skew the per-run pass-rate denominator).
    seen: set[str] = set()
    assertions: list[str] = []
    for assertion in list(suite.common_assertions) + list(case.expectations):
        if assertion not in seen:
            seen.add(assertion)
            assertions.append(assertion)
    return assertions


def grader_schema() -> dict[str, Any]:
    """JSON Schema for the grader's structured verdict. Verdicts are keyed by the
    assertion's 1-based ``id`` rather than an echoed assertion string, so a
    grader cannot break grading by re-numbering or paraphrasing the assertion
    text. Providers that enforce a response schema (codex ``--output-schema``,
    claude ``--json-schema``) guarantee the shape; the prompt and the tolerant
    parser carry the same contract for providers that do not."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["verdicts"],
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "passed", "evidence"],
                    "properties": {
                        "id": {"type": "integer"},
                        "passed": {"type": "boolean"},
                        "evidence": {"type": "string"},
                    },
                },
            }
        },
    }


def render_grader_prompt(
    suite: EvalSuite,
    case: EvalCase,
    config: str,
    executor_output: str,
    artifact_text: str | None = None,
    change_manifest: dict[str, Any] | None = None,
    executor_evidence: dict[str, Any] | None = None,
) -> str:
    assertions = assertions_for_case(suite, case)
    boundary_rules = [
        "- Grade the whole recorded output, not only the intended artifact inside it.",
        "- Wrapper text, headings, Markdown fences, explanations, and meta-notes are part of the output.",
        "- Do not narrow a global `Output ...` assertion to a sub-artifact unless the assertion explicitly scopes it.",
        "- Use byte-level or parser-level checks for exact JSON, verbatim output, raw commit-message, and no-fence assertions.",
    ]
    if artifact_text is not None:
        boundary_rules.append(
            "- The agent wrote its primary artifact to a file. Both the chat response and the written "
            "artifact below are the agent's output: grade them together. Assertions about the chat "
            "response (for example concise-summary or no-duplication rules) apply to the recorded "
            "response, and assertions about the plan/spec artifact apply to the written artifact."
        )
    manifest_entries = (change_manifest or {}).get("entries") if change_manifest else None
    if change_manifest is not None and change_manifest.get("captured"):
        boundary_rules.append(
            "- The Sandbox File Changes section below is the runner's own record of every file the "
            "agent created, modified, or deleted, derived from the sandbox baseline, not from the "
            "agent's narration. Use it to verify claims about writing, reusing, or updating files: a "
            "claim to have created or updated a file is only supported when that path appears there, "
            "and a claim to have reused a pre-existing file is contradicted when that path is listed "
            "as added."
        )
    evidence_entries = (executor_evidence or {}).get("entries") if executor_evidence else None
    if executor_evidence is not None and executor_evidence.get("captured"):
        boundary_rules.append(
            "- The Executor Tool/Delegation Evidence section below is the runner's own record, read "
            "from the host session transcript, of the tool calls and sub-agents the executor actually "
            "invoked. Every id listed there is host-issued, not authored by the executor: do not judge "
            "any id in that section as fabricated or 'generated-looking'. When the executor cites an id "
            "that appears there, treat its delegation/tool claim as backed by a real host record. Only "
            "an id or run/task record that appears in NO runner-provided evidence section may be "
            "treated as unproven; executor prose in the recorded output is not runner evidence."
        )
    lines = [
        "# Eval Grader Prompt",
        "",
        f"- Skill: `{suite.skill_name}`",
        f"- Eval id: `{case.eval_id}`",
        f"- Eval name: {case.name}",
        f"- Configuration: `{config}`",
        "",
        "You are grading an output that another agent produced. You did not produce it.",
        "Grade only from the recorded output below and the assertions; do not re-run the task.",
        "",
        "## Grading Boundary Rules",
        "",
        *boundary_rules,
        "",
        "## Recorded Output",
        "",
        "```",
        executor_output.rstrip("\n"),
        "```",
    ]
    if artifact_text is not None:
        # The written artifact is itself Markdown with its own ``` fences, so a
        # fenced block would nest ambiguously; bracket it with explicit sentinels
        # the grader can read as a single verbatim section.
        lines.extend(
            [
                "",
                "## Written Plan Artifact",
                "",
                "The agent wrote its primary artifact to the designated file path. Its full contents:",
                "",
                "----- BEGIN WRITTEN ARTIFACT -----",
                artifact_text.rstrip("\n"),
                "----- END WRITTEN ARTIFACT -----",
            ]
        )
    if change_manifest is not None and change_manifest.get("captured"):
        lines.extend(["", "## Sandbox File Changes", ""])
        if manifest_entries:
            lines.append(
                "The runner recorded these file changes the agent made in its sandbox "
                "(status, path, and content hash for existing files):"
            )
            lines.append("")
            for entry in manifest_entries:
                sha = entry.get("sha256")
                sha_text = f" sha256={sha[:12]}" if isinstance(sha, str) else ""
                lines.append(f"- {entry['status']}: `{entry['path']}`{sha_text}")
        else:
            lines.append("The agent made no file changes in its sandbox outside the runtime scaffold.")
    if executor_evidence is not None and executor_evidence.get("captured"):
        lines.extend(["", "## Executor Tool/Delegation Evidence", ""])
        lines.append(
            "Host-recorded trace of the executor's tool calls and sub-agents (host state, not sandbox "
            "state). Only tool names and host-issued ids are shown; prompt text, reasoning, and tool "
            "results are redacted. Every id here is host-issued and must not be judged fabricated:"
        )
        lines.append("")
        if evidence_entries:
            for entry in evidence_entries:
                kind = entry.get("type", "record")
                name = entry.get("name")
                name_text = f" {name}" if isinstance(name, str) else ""
                lines.append(f"- {kind}{name_text}: `{entry.get('id')}`")
        else:
            lines.append(
                "The transcript recorded no tool calls or sub-agents for this run, so any claim that "
                "sub-agents ran is unproven."
            )
    lines += [
        "",
        "## Required response",
        "",
        "Respond with ONLY a JSON object and no other text:",
        '`{"verdicts": [{"id": <assertion number>, "passed": <true|false>, "evidence": <string>}]}`',
        "Emit exactly one verdict per assertion below, using the assertion's number as `id`.",
        "Do not echo or restate the assertion text. Keep `evidence` to one short sentence,",
        "and avoid backticks and line breaks inside it so the JSON stays well-formed.",
    ]
    if assertions:
        lines.extend(["", "## Assertions For Grading", ""])
        lines.extend(f"{index}. {assertion}" for index, assertion in enumerate(assertions, start=1))
    else:
        lines.extend(["", "There are no assertions; respond with `{\"verdicts\": []}`."])
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Provider registry. Each provider builds an Invocation (argv + env + optional
# stdin) and parses the completed subprocess into (output_text, metrics|None).
# The runner spawns and times out invocations; providers never spawn.
# --------------------------------------------------------------------------- #
@dataclass
class Invocation:
    argv: list[str]
    env: dict[str, str]
    cwd: str
    stdin: str | None = None


@dataclass
class ProviderResult:
    output: str
    exit_code: int | None
    timed_out: bool
    metrics: dict[str, Any]
    stderr: str = ""


def base_env() -> dict[str, str]:
    # Strip CLAUDECODE so a nested provider CLI runs as a fresh top-level process
    # rather than inheriting this runner's session, and so executor and grader
    # never share a parent session id.
    return {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}


def invocation_env(cwd: Path | None = None) -> dict[str, str]:
    env = base_env()
    if cwd is not None:
        env["PWD"] = str(cwd.resolve())
    return env


def metrics_absent(provider: str, reason: str) -> dict[str, Any]:
    return {"captured": False, "source": None, "provider": provider, "reason": reason}


def extract_json_object(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    return text[start : end + 1]


class Provider:
    name = "base"

    def available(self) -> bool:  # pragma: no cover - overridden
        raise NotImplementedError

    def build_invocation(
        self,
        prompt: str,
        *,
        run_dir: Path,
        role: str,
        model: str | None = None,
        schema: dict[str, Any] | None = None,
        cwd: Path | None = None,
    ) -> Invocation:  # pragma: no cover
        raise NotImplementedError

    def parse(self, *, run_dir: Path, stdout: str, stderr: str, exit_code: int | None, role: str) -> tuple[str, dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError


class ClaudeProvider(Provider):
    name = "claude"

    def available(self) -> bool:
        return shutil.which("claude") is not None

    def build_invocation(
        self,
        prompt: str,
        *,
        run_dir: Path,
        role: str,
        model: str | None = None,
        schema: dict[str, Any] | None = None,
        cwd: Path | None = None,
    ) -> Invocation:
        argv = ["claude", "-p", prompt, "--output-format", "json"]
        if model:
            argv += ["--model", model]
        # Constrain the grader's final response to the verdict schema when one is
        # supplied, so the provider returns well-formed structured JSON instead
        # of hand-written JSON that can break (for example a dropped closing
        # quote inside an evidence string).
        if schema is not None:
            argv += ["--json-schema", json.dumps(schema)]
        resolved_cwd = (cwd or find_repo_root(run_dir)).resolve()
        return Invocation(
            argv=argv,
            env=invocation_env(resolved_cwd),
            cwd=str(resolved_cwd),
        )

    def parse(self, *, run_dir: Path, stdout: str, stderr: str, exit_code: int | None, role: str) -> tuple[str, dict[str, Any]]:
        candidate = stdout.strip()
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            blob = extract_json_object(candidate)
            try:
                data = json.loads(blob) if blob else None
            except json.JSONDecodeError:
                data = None
        if not isinstance(data, dict):
            return stdout, metrics_absent(self.name, "claude output was not a JSON envelope")
        result = data.get("result")
        structured = data.get("structured_output")
        if isinstance(structured, (dict, list)):
            # Newer claude CLIs (for example 2.1.x) place ``--json-schema``
            # output under ``structured_output`` and leave ``result`` an empty
            # string. Prefer the structured envelope and re-serialize it so the
            # downstream grader parser sees JSON text. Executor runs carry no
            # schema, so this key is absent and the ``result`` paths below apply.
            output = json.dumps(structured)
        elif isinstance(result, str):
            output = result
        elif isinstance(result, (dict, list)):
            # Older CLIs returned the schema-conforming verdict as a nested
            # object inside ``result``; re-serialize it for the grader parser.
            output = json.dumps(result)
        else:
            output = stdout
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        metrics: dict[str, Any] = {
            "captured": True,
            "source": "claude -p --output-format json",
            "provider": self.name,
        }
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if isinstance(input_tokens, int):
            metrics["input_tokens"] = input_tokens
        if isinstance(output_tokens, int):
            metrics["output_tokens"] = output_tokens
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            metrics["total_tokens"] = input_tokens + output_tokens
        if isinstance(data.get("duration_ms"), (int, float)):
            metrics["duration_ms"] = data["duration_ms"]
        if isinstance(data.get("total_cost_usd"), (int, float)):
            metrics["total_cost_usd"] = data["total_cost_usd"]
        # The session id keys the host transcript at
        # ``<config>/projects/<encoded-cwd>/<session_id>.jsonl``. It is the only
        # pointer the runner needs to fold host-issued delegation/tool evidence
        # into the grader prompt, so record it when the CLI exposes it. It is a
        # non-sensitive locator, never a usage number.
        session_id = data.get("session_id")
        if isinstance(session_id, str) and session_id.strip():
            metrics["session_id"] = session_id.strip()
        # `claude -p --output-format json` reports an errored turn (for example
        # error_max_turns or error_during_execution) via is_error while still
        # exiting 0 and putting an error message in `result`. Flag it so the
        # runner records a provider failure instead of grading the error text.
        if data.get("is_error") is True:
            metrics["error"] = str(data.get("subtype") or "is_error")
        return output, metrics


class CodexProvider(Provider):
    name = "codex"

    def available(self) -> bool:
        return shutil.which("codex") is not None

    def build_invocation(
        self,
        prompt: str,
        *,
        run_dir: Path,
        role: str,
        model: str | None = None,
        schema: dict[str, Any] | None = None,
        cwd: Path | None = None,
    ) -> Invocation:
        last_message = (run_dir / f"{role}_codex_last.txt").resolve()
        sandbox_mode = "workspace-write" if role == "executor" else "read-only"
        argv = [
            "codex", "exec", "-s", sandbox_mode, "-o", str(last_message),
            "--json", "--skip-git-repo-check",
        ]
        if model:
            argv += ["--model", model]
        # Constrain the grader's final response to the verdict schema when one is
        # supplied. codex reads the schema from a file, so write it next to the
        # run before pointing ``--output-schema`` at it.
        if schema is not None:
            schema_path = (run_dir / f"{role}_schema.json").resolve()
            run_dir.mkdir(parents=True, exist_ok=True)
            write_text(schema_path, json.dumps(schema, indent=2) + "\n")
            argv += ["--output-schema", str(schema_path)]
        argv.append("-")
        resolved_cwd = (cwd or find_repo_root(run_dir)).resolve()
        return Invocation(
            argv=argv,
            env=invocation_env(resolved_cwd),
            cwd=str(resolved_cwd),
            stdin=prompt,
        )

    def parse(self, *, run_dir: Path, stdout: str, stderr: str, exit_code: int | None, role: str) -> tuple[str, dict[str, Any]]:
        last_message = run_dir / f"{role}_codex_last.txt"
        if last_message.is_file():
            output = last_message.read_text(encoding="utf-8")
        else:
            output = codex_final_agent_message(stdout) or stdout
        usage: dict[str, Any] | None = None
        for event in codex_jsonl_events(stdout):
            if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
                usage = event["usage"]
        if usage is None:
            metrics = metrics_absent(self.name, "codex JSONL had no numeric turn.completed usage")
        else:
            numeric = {
                key: value for key in (
                    "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens"
                ) if isinstance((value := usage.get(key)), (int, float)) and not isinstance(value, bool)
            }
            if numeric:
                metrics = {
                    "captured": True,
                    "source": "codex exec --json turn.completed",
                    "provider": self.name,
                    **numeric,
                }
                if "input_tokens" in numeric and "output_tokens" in numeric:
                    metrics["total_tokens"] = numeric["input_tokens"] + numeric["output_tokens"]
            else:
                metrics = metrics_absent(self.name, "codex turn.completed usage had no numeric fields")
        return output, metrics


def codex_jsonl_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def codex_final_agent_message(stdout: str) -> str | None:
    final: str | None = None
    for event in codex_jsonl_events(stdout):
        item = event.get("item")
        if event.get("type") == "item.completed" and isinstance(item, dict):
            if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                final = item["text"]
        if event.get("type") in ("agent_message", "message.completed"):
            text = event.get("text") or event.get("message")
            if isinstance(text, str):
                final = text
    return final


# A hermetic provider used by tests. It is dispatched through the exact same run
# matrix as the real adapters (no bypass) but runs a tiny stdlib subprocess
# instead of a network CLI. Its behavior is driven entirely by environment
# pointers so production runs never select it unless explicitly configured.
STUB_RUNNER_SOURCE = r'''
import json, os, re, subprocess, sys, time

role = sys.argv[1]
prompt = sys.stdin.read()

log_path = os.environ.get("EVAL_RUNNER_STUB_LOG")


def record(event):
    if log_path:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write("%s %s %d %f\n" % (event, role, os.getpid(), time.monotonic()))


record("enter")
time.sleep(float(os.environ.get("EVAL_RUNNER_STUB_SLEEP", "0") or 0))

spec = {}
spec_path = os.environ.get("EVAL_RUNNER_STUB_FILE")
if spec_path and os.path.isfile(spec_path):
    with open(spec_path, encoding="utf-8") as handle:
        spec = json.load(handle)


def field(name):
    match = re.search(r"- " + name + r": `([^`]*)`", prompt)
    return match.group(1) if match else None


config = field("Configuration")
grading_rule = (spec.get("grading") or {}).get(config, {})

if role == "executor":
    if config == "with_skill" and float(os.environ.get("EVAL_RUNNER_STUB_TIMEOUT", "0") or 0):
        time.sleep(float(os.environ["EVAL_RUNNER_STUB_TIMEOUT"]))
    text = spec.get("executor_output", "stub output")
    # When the spec asks for it, emulate a skill whose deliverable is a written
    # file: parse the designated artifact path out of the Response Contract and
    # write there, so the runner's artifact-collection path is exercised.
    artifact = (spec.get("write_artifact") or {}).get(config)
    if artifact is not None:
        match = re.search(r"exact path: `([^`]*)`", prompt)
        if match:
            with open(match.group(1), "w", encoding="utf-8") as handle:
                handle.write(artifact)
    touch = spec.get("touch_cwd")
    if touch:
        with open(os.path.join(os.getcwd(), touch), "w", encoding="utf-8") as handle:
            handle.write("stub touched cwd\n")
    # Emulate a skill that creates/modifies several sandbox files, so the
    # runner's change-manifest capture can be exercised end to end.
    for item in (spec.get("write_files") or {}).get(config) or []:
        target = os.path.join(os.getcwd(), item["path"])
        os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(item["content"])
    for rel in (spec.get("delete_files") or {}).get(config) or []:
        target = os.path.join(os.getcwd(), rel)
        if os.path.isfile(target):
            os.remove(target)
    if (spec.get("commit_changes") or {}).get(config):
        subprocess.run(["git", "add", "-A"], cwd=os.getcwd(), check=True, capture_output=True, text=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Eval Stub",
                "-c",
                "user.email=eval-stub@example.invalid",
                "commit",
                "--no-gpg-sign",
                "--no-verify",
                "-m",
                "stub executor commit",
            ],
            cwd=os.getcwd(),
            check=True,
            capture_output=True,
            text=True,
        )
    touch_absolute = spec.get("touch_absolute")
    if touch_absolute:
        with open(touch_absolute, "w", encoding="utf-8") as handle:
            handle.write("stub touched absolute path\n")
    print("%s [%s/%s]" % (text, field("Eval id"), config))
else:
    if grading_rule.get("unparseable"):
        print("this is not a JSON verdict")
    else:
        assertions = re.findall(r"^\d+\. (.+)$", prompt, re.M)
        default_pass = bool(grading_rule.get("pass", False))
        verdicts = [
            {"id": index, "passed": default_pass, "evidence": "stub"}
            for index, _text in enumerate(assertions, start=1)
        ]
        print(json.dumps({"verdicts": verdicts}))

record("exit")

# Test hooks: non-zero exits on the with_skill side simulate provider/process
# failures so the runner's failure handling can be exercised.
if config == "with_skill":
    if role == "executor":
        sys.stderr.write(str(spec.get("executor_stderr", "")))
        sys.exit(int(spec.get("executor_exit", 0) or 0))
    if role == "grader":
        sys.stderr.write(str(spec.get("grader_stderr", "")))
        sys.exit(int(spec.get("grader_exit", 0) or 0))
'''


class StubProvider(Provider):
    name = "stub"

    def available(self) -> bool:
        return bool(os.environ.get("EVAL_RUNNER_STUB_FILE"))

    def build_invocation(
        self,
        prompt: str,
        *,
        run_dir: Path,
        role: str,
        model: str | None = None,
        schema: dict[str, Any] | None = None,
        cwd: Path | None = None,
    ) -> Invocation:
        # The hermetic stub runs no real model. A provided model is appended to
        # argv anyway — the stub script reads only argv[1] (the role), so the
        # extra entry is inert at runtime but lands in run.json, making the
        # runner's role-level model wiring auditable end to end. `schema` is
        # accepted to honor the provider contract and then ignored.
        argv = [sys.executable, "-c", STUB_RUNNER_SOURCE, role]
        if model:
            argv.append(model)
        return Invocation(
            argv=argv,
            env=invocation_env((cwd or find_repo_root(run_dir)).resolve()),
            cwd=str((cwd or find_repo_root(run_dir)).resolve()),
            stdin=prompt,
        )

    def parse(self, *, run_dir: Path, stdout: str, stderr: str, exit_code: int | None, role: str) -> tuple[str, dict[str, Any]]:
        return stdout, metrics_absent(self.name, "stub provider does not expose metrics")


PROVIDERS: dict[str, Callable[[], Provider]] = {
    "claude": ClaudeProvider,
    "codex": CodexProvider,
    "stub": StubProvider,
}


def get_provider(name: str) -> Provider:
    factory = PROVIDERS.get(name)
    if factory is None:
        known = ", ".join(sorted(PROVIDERS))
        raise CommandError(f"--agent {name!r}: unknown provider; known providers: {known}")
    return factory()


# --------------------------------------------------------------------------- #
# Subprocess execution and grading
# --------------------------------------------------------------------------- #
def run_invocation(invocation: Invocation, timeout: float) -> tuple[str, str, int | None, bool]:
    try:
        completed = subprocess.run(
            invocation.argv,
            env=invocation.env,
            cwd=invocation.cwd,
            input=invocation.stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return completed.stdout, completed.stderr, completed.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        return stdout, stderr, None, True


def bounded_utf8_text(text: str, max_bytes: int = STDERR_MAX_BYTES) -> tuple[str, dict[str, Any]]:
    raw = text.encode("utf-8", "replace")
    truncated = len(raw) > max_bytes
    kept = raw[:max_bytes]
    if truncated:
        kept = kept.decode("utf-8", "ignore").encode("utf-8")
    rendered = kept.decode("utf-8")
    if truncated:
        marker = "\n[...stderr truncated to 64 KiB...]\n"
        marker_bytes = marker.encode("utf-8")
        kept = kept[: max(0, max_bytes - len(marker_bytes))]
        rendered = kept.decode("utf-8", "ignore") + marker
    return rendered, {
        "captured": True,
        "original_bytes": len(raw),
        "stored_bytes": len(rendered.encode("utf-8")),
        "truncated": truncated,
        "limit_bytes": max_bytes,
    }


def persist_failure_stderr(outputs_dir: Path, role: str, stderr: str) -> dict[str, Any]:
    rendered, metadata = bounded_utf8_text(stderr)
    path = (outputs_dir / f"{role}_stderr.txt").resolve()
    write_text(path, rendered)
    return {**metadata, "path": str(path)}


def provider_failure_reason(summary: str, stderr: str) -> str:
    detail = " ".join(stderr.strip().split())
    return f"{summary}: {detail[:512]}" if detail else summary


def failure_record(
    role: str,
    status: str,
    exit_code: int | None,
    timed_out: bool,
    reason: str,
    stderr_metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "role": role,
        "kind": "timeout" if timed_out else "provider_error",
        "status": status,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "reason": reason,
        "stderr": stderr_metadata,
    }


def balanced_json_objects(text: str) -> list[str]:
    """Return every top-level brace-balanced ``{...}`` substring, honoring string
    literals and escapes, so a JSON object survives prose that also contains
    braces (a common grader output shape)."""
    objects: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        if text[index] != "{":
            index += 1
            continue
        depth = 0
        in_string = False
        escaped = False
        for position in range(index, length):
            char = text[position]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    objects.append(text[index : position + 1])
                    index = position
                    break
        index += 1
    return objects


def parse_grader_output(text: str) -> tuple[dict[str, Any] | None, str | None]:
    candidate = text.strip()
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    blobs = [candidate, *fenced, *balanced_json_objects(candidate)]
    parsed: list[dict[str, Any]] = []
    for blob in blobs:
        if not blob:
            continue
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            parsed.append(data)
    # Only a dict that carries the grader contract counts as a verdict: the
    # structured ``verdicts`` list (id-keyed, the current contract) or the legacy
    # ``expectations`` list (text-keyed, still accepted for backward
    # compatibility). A brace-balanced fragment salvaged from malformed output --
    # for example a single ``{"text", "passed", "evidence"}`` entry recovered
    # when an unterminated evidence string broke the enclosing array -- carries
    # neither list. Returning such a fragment would slip past the caller's
    # ``grading is None`` guard and let ``summarize_grading`` record a zero-match
    # scored 0% instead of the intended ``grader_unparseable`` exclusion,
    # silently deflating the benchmark.
    for data in parsed:
        if grader_verdict_list(data) is not None:
            return data, None
    return None, "grader output had no parseable verdict list"


def grader_verdict_list(data: Any) -> list[Any] | None:
    """Return the grader verdict list from either the structured ``verdicts``
    contract or the legacy ``expectations`` contract, or None when the object
    carries neither."""
    if not isinstance(data, dict):
        return None
    verdicts = data.get("verdicts")
    if isinstance(verdicts, list):
        return verdicts
    expectations = data.get("expectations")
    if isinstance(expectations, list):
        return expectations
    return None


_ENUM_PREFIX_RE = re.compile(r"^\s*\d+[.)]\s+")


def normalize_assertion_text(text: str) -> str:
    """Strip a leading enumeration prefix such as ``1. `` or ``2) `` that a
    grader may prepend when it echoes the numbered "Assertions For Grading"
    list instead of the verbatim assertion text. Only the leading list marker
    is removed; the assertion body must still match exactly, so this recovers a
    known grader serialization quirk without loosening any assertion."""
    return _ENUM_PREFIX_RE.sub("", text).strip()


def summarize_grading(grading: dict[str, Any] | None, assertions: list[str]) -> dict[str, Any]:
    by_index: dict[int, dict[str, Any]] = {}
    by_text: dict[str, dict[str, Any]] = {}
    by_norm: dict[str, dict[str, Any]] = {}
    for item in grader_verdict_list(grading) or []:
        if not isinstance(item, dict):
            continue
        ident = item.get("id")
        if isinstance(ident, int) and not isinstance(ident, bool):
            by_index.setdefault(ident, item)
        if isinstance(item.get("text"), str):
            by_text.setdefault(item["text"], item)
            by_norm.setdefault(normalize_assertion_text(item["text"]), item)
    expectations: list[dict[str, Any]] = []
    passed = 0
    # Assertions are presented to the grader as a 1-based numbered list, so the
    # structured ``id`` matches the assertion position. Prefer id matching (the
    # current contract), then fall back to exact and enumeration-tolerant text
    # matching for legacy text-keyed verdicts.
    for position, text in enumerate(assertions, start=1):
        item = by_index.get(position)
        if item is None:
            item = by_text.get(text) or by_norm.get(normalize_assertion_text(text))
        is_pass = bool(item and item.get("passed") is True)
        if is_pass:
            passed += 1
        evidence = item.get("evidence") if isinstance(item, dict) else None
        expectations.append(
            {"text": text, "passed": is_pass, "evidence": evidence if isinstance(evidence, str) else ""}
        )
    total = len(assertions)
    return {
        "expectations": expectations,
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "pass_rate": passed / total if total else None,
    }


@dataclass
class RunTask:
    case: EvalCase
    config: str
    run_number: int
    run_dir: Path


def execute_run(
    suite: EvalSuite,
    provider: Provider,
    task: RunTask,
    skill_path: str | None,
    timeout: float,
    executor_model: str | None = None,
    grader_model: str | None = None,
) -> dict[str, Any]:
    case, config, run_number, run_dir = task.case, task.config, task.run_number, task.run_dir
    outputs_dir = run_dir / "outputs"
    assertions = assertions_for_case(suite, case)
    source_repo_root = find_repo_root(suite.path)
    sandbox = create_run_sandbox(source_repo_root, run_dir, skill_path)

    # Designate a fixed, config-symmetric path for a file deliverable inside the
    # sandbox. After execution the runner persists any captured artifact under
    # the run outputs and folds its text into the grader prompt.
    outputs_dir.mkdir(parents=True, exist_ok=True)
    artifact_capture_file = sandbox.repo_root / ".eval-runner" / "outputs" / "plan.md"
    artifact_capture_file.parent.mkdir(parents=True, exist_ok=True)
    artifact_path = str(artifact_capture_file)

    executor_prompt = render_executor_prompt(suite, case, config, sandbox.skill_path, artifact_path)
    write_text(run_dir / "prompt.md", executor_prompt)
    executor_inv = provider.build_invocation(
        executor_prompt,
        run_dir=run_dir,
        role="executor",
        model=executor_model,
        cwd=sandbox.repo_root,
    )
    executor_started = time.perf_counter()
    e_stdout, e_stderr, e_exit, e_timeout = run_invocation(executor_inv, timeout)
    executor_duration_ms = (time.perf_counter() - executor_started) * 1000
    executor_output, metrics = provider.parse(
        run_dir=run_dir, stdout=e_stdout, stderr=e_stderr, exit_code=e_exit, role="executor"
    )
    if isinstance(provider, CodexProvider):
        usage_captured = metrics.get("captured") is True
        if not usage_captured:
            metrics["usage_reason"] = metrics.pop("reason", "codex usage was not captured")
        metrics["usage_captured"] = usage_captured
        metrics["captured"] = True
        metrics["source"] = (
            "codex exec --json turn.completed + runner wall clock"
            if usage_captured
            else "runner wall clock"
        )
        metrics["duration_ms"] = executor_duration_ms
    write_text(outputs_dir / "output.txt", executor_output)
    artifact_text, artifact_info = collect_written_artifact(artifact_capture_file)
    if artifact_text is not None:
        output_artifact_file = outputs_dir / "plan.md"
        shutil.copyfile(artifact_capture_file, output_artifact_file)
        artifact_info["capture_path"] = artifact_info.get("path")
        artifact_info["path"] = str(output_artifact_file.resolve())
    change_manifest = collect_sandbox_change_manifest(sandbox)
    executor_evidence = collect_executor_evidence(metrics, sandbox.repo_root)

    status = "ok"
    grader_inv: Invocation | None = None
    grading: dict[str, Any] | None = None
    grader_error: str | None = None
    failure: dict[str, Any] | None = None

    if e_timeout:
        status = "executor_timeout"
        reason = provider_failure_reason("executor provider invocation timed out", e_stderr)
        failure = failure_record(
            "executor", status, e_exit, True, reason,
            persist_failure_stderr(outputs_dir, "executor", e_stderr),
        )
    elif e_exit not in (0, None):
        status = "executor_failed"
        reason = provider_failure_reason(f"executor provider exited with code {e_exit}", e_stderr)
        failure = failure_record(
            "executor", status, e_exit, False, reason,
            persist_failure_stderr(outputs_dir, "executor", e_stderr),
        )
    elif metrics.get("error"):
        status = "executor_failed"
        grader_error = f"executor provider error: {metrics['error']}"
        reason = provider_failure_reason(grader_error, e_stderr)
        failure = failure_record(
            "executor", status, e_exit, False, reason,
            persist_failure_stderr(outputs_dir, "executor", e_stderr),
        )

    if status == "ok":
        grader_prompt = render_grader_prompt(
            suite, case, config, executor_output, artifact_text, change_manifest, executor_evidence
        )
        write_text(run_dir / "grader_prompt.md", grader_prompt)
        grader_inv = provider.build_invocation(
            grader_prompt,
            run_dir=run_dir,
            role="grader",
            model=grader_model,
            schema=grader_schema(),
            cwd=grader_working_dir(run_dir),
        )
        g_stdout, g_stderr, g_exit, g_timeout = run_invocation(grader_inv, timeout)
        grader_output, grader_metrics = provider.parse(
            run_dir=run_dir, stdout=g_stdout, stderr=g_stderr, exit_code=g_exit, role="grader"
        )
        write_text(outputs_dir / "grader_output.txt", grader_output)
        if g_timeout:
            status = "grader_timeout"
            reason = provider_failure_reason("grader provider invocation timed out", g_stderr)
            failure = failure_record(
                "grader", status, g_exit, True, reason,
                persist_failure_stderr(outputs_dir, "grader", g_stderr),
            )
        elif grader_metrics.get("error"):
            status = "grader_failed"
            grader_error = f"grader provider error: {grader_metrics['error']}"
            reason = provider_failure_reason(grader_error, g_stderr)
            failure = failure_record(
                "grader", status, g_exit, False, reason,
                persist_failure_stderr(outputs_dir, "grader", g_stderr),
            )
        elif g_exit not in (0, None):
            status = "grader_failed"
            grader_error = f"grader provider exited with code {g_exit}"
            reason = provider_failure_reason(grader_error, g_stderr)
            failure = failure_record(
                "grader", status, g_exit, False, reason,
                persist_failure_stderr(outputs_dir, "grader", g_stderr),
            )
        else:
            grading, grader_error = parse_grader_output(grader_output)
            if grading is None:
                status = "grader_unparseable"
                reason = provider_failure_reason(
                    grader_error or "grader output was not parseable", g_stderr
                )
                failure = failure_record(
                    "grader", status, g_exit, False, reason,
                    persist_failure_stderr(outputs_dir, "grader", g_stderr),
                )

    summary = summarize_grading(grading, assertions)
    write_json(run_dir / "grading.json", summary)
    write_json(run_dir / "metrics.json", metrics)

    # A run contributes a pass rate only when execution and grading both
    # completed. Infrastructure failures (timeout, crash, provider error,
    # unparseable verdict) keep their status but record pass_rate=None, so they
    # surface as failures and never fold into the comparison mean as a real 0%.
    scored = status == "ok"
    record = {
        "eval_id": case.eval_id,
        "eval_name": case.name,
        "configuration": config,
        "run_number": run_number,
        "status": status,
        "scored": scored,
        "passed": summary["passed"],
        "failed": summary["failed"],
        "total": summary["total"],
        "pass_rate": summary["pass_rate"] if scored else None,
        "expectations": summary["expectations"],
        "metrics": metrics,
        "written_artifact": artifact_info,
        "change_manifest": change_manifest,
        "executor_evidence": executor_evidence,
        "sandbox": {
            "source_repo_root": str(sandbox.source_repo_root),
            "repo_root": str(sandbox.repo_root),
            "skill_path": sandbox.skill_path,
            "git_initialized": sandbox.git_initialized,
            "git_error": sandbox.git_error,
            "copy_strategy": sandbox.copy_strategy,
            "contamination_status": sandbox.contamination_status,
            "contamination_reason": sandbox.contamination_reason,
            "excluded_untracked_count": sandbox.excluded_untracked_count,
            "excluded_untracked_sample": sandbox.excluded_untracked_sample,
        },
        "executor_invocation": {
            "argv": executor_inv.argv,
            "env_keys": sorted(executor_inv.env),
            "cwd": executor_inv.cwd,
            "stdin": executor_inv.stdin,
        },
        "grader_invocation": (
            {
                "argv": grader_inv.argv,
                "env_keys": sorted(grader_inv.env),
                "cwd": grader_inv.cwd,
                "stdin": grader_inv.stdin,
            }
            if grader_inv
            else None
        ),
        "grader_error": grader_error,
        "failure": failure,
        "run_dir": str(run_dir),
    }
    write_json(run_dir / "run.json", record)
    return record


# --------------------------------------------------------------------------- #
# Aggregation: raw pass-rate comparison, with_skill vs without_skill.
# --------------------------------------------------------------------------- #
def config_sort_key(config: str) -> tuple[int, str]:
    order = {"with_skill": 0, "without_skill": 1}
    return (order.get(config, 2), config)


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def aggregate_runs(
    suite: EvalSuite,
    configs: list[str],
    runs: list[dict[str, Any]],
    *,
    agent: str,
    skill_path: str | None,
    model: str | None = None,
    executor_model: str | None = None,
    grader_model: str | None = None,
    source_fixtures: dict[str, Any] | None = None,
    suite_coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rates_by_eval_config: dict[tuple[str, str], list[float]] = {}
    runs_by_eval_config: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in runs:
        key = (run["eval_id"], run["configuration"])
        runs_by_eval_config.setdefault(key, []).append(run)
        rate = run.get("pass_rate")
        if isinstance(rate, (int, float)):
            rates_by_eval_config.setdefault(key, []).append(float(rate))

    per_eval: list[dict[str, Any]] = []
    for case in suite.evals:
        entry: dict[str, Any] = {"eval_id": case.eval_id, "eval_name": case.name, "configs": {}}
        for config in configs:
            rates = rates_by_eval_config.get((case.eval_id, config), [])
            config_runs = runs_by_eval_config.get((case.eval_id, config), [])
            entry["configs"][config] = {
                "pass_rate": mean(rates),
                "runs": len(config_runs),
                "scored_runs": len(rates),
                "error_runs": len(config_runs) - len(rates),
            }
        per_eval.append(entry)

    overall: dict[str, Any] = {}
    for config in configs:
        rates = [
            rate
            for (eval_id, run_config), values in rates_by_eval_config.items()
            if run_config == config
            for rate in values
        ]
        overall[config] = mean(rates)

    comparison: dict[str, Any] | None = None
    if len(configs) >= 2:
        candidate, baseline = configs[0], configs[1]
        cand_rate = overall.get(candidate)
        base_rate = overall.get(baseline)
        delta = None
        if isinstance(cand_rate, (int, float)) and isinstance(base_rate, (int, float)):
            delta = cand_rate - base_rate
        comparison = {
            "candidate": candidate,
            "baseline": baseline,
            "candidate_pass_rate": cand_rate,
            "baseline_pass_rate": base_rate,
            "delta": delta,
        }

    metrics_present = any(run.get("metrics", {}).get("captured") for run in runs)
    status_counts: dict[str, int] = {}
    for run in runs:
        status = str(run.get("status", "unknown"))
        status_counts[status] = status_counts.get(status, 0) + 1
    error_run_count = sum(count for status, count in status_counts.items() if status != "ok")
    coverage = suite_coverage or {
        "mode": "full",
        "suite_eval_count": len(suite.evals),
        "selected_eval_count": len(suite.evals),
        "selected_eval_ids": [case.eval_id for case in suite.evals],
        "partial": False,
        "closing_eligible": True,
    }
    sanity_checks = compute_sanity_checks(
        configs,
        runs,
        per_eval,
        source_fixtures=source_fixtures,
        suite_coverage=coverage,
    )
    return {
        "skill_name": suite.skill_name,
        "agent": agent,
        "model": model,
        "executor_model": executor_model,
        "grader_model": grader_model,
        "skill_path": skill_path,
        "source_fixtures": source_fixtures,
        "suite_coverage": coverage,
        "generated_at": utc_now(),
        "configs": list(configs),
        "run_count": len(runs),
        "scored_run_count": status_counts.get("ok", 0),
        "error_run_count": error_run_count,
        "status_counts": status_counts,
        "metrics_captured": metrics_present,
        "overall_pass_rate": overall,
        "comparison": comparison,
        "sanity_checks": sanity_checks,
        "evals": per_eval,
        "runs": runs,
    }


def compute_sanity_checks(
    configs: list[str],
    runs: list[dict[str, Any]],
    per_eval: list[dict[str, Any]],
    *,
    source_fixtures: dict[str, Any] | None = None,
    suite_coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Surface anomalies a supervising reviewer must inspect before reporting a
    run as a clean result. These are deterministic signals derived from the run
    records, not pass/fail judgments: a run that produced them may still be
    fine, but it must not be summarized as ``+X% delta`` without explaining
    them. Catches the failure that motivated this check -- a masked grader
    failure or 0% cell silently folded into the comparison mean."""
    infra: list[dict[str, Any]] = []
    seen_infra: set[tuple[Any, Any, Any]] = set()
    for run in runs:
        if run.get("scored", False):
            continue
        key = (run.get("eval_id"), run.get("configuration"), run.get("status"))
        if key in seen_infra:
            continue
        seen_infra.add(key)
        infra.append({"eval_id": run.get("eval_id"), "configuration": run.get("configuration"), "status": run.get("status")})

    zero_cells: list[dict[str, Any]] = []
    for entry in per_eval:
        for config, data in entry["configs"].items():
            rate = data.get("pass_rate")
            if isinstance(rate, (int, float)) and rate == 0.0 and data.get("scored_runs", 0) > 0:
                zero_cells.append({"eval_id": entry["eval_id"], "configuration": config})

    inversions: list[dict[str, Any]] = []
    if len(configs) >= 2:
        candidate, baseline = configs[0], configs[1]
        for entry in per_eval:
            cand = entry["configs"].get(candidate, {}).get("pass_rate")
            base = entry["configs"].get(baseline, {}).get("pass_rate")
            if isinstance(cand, (int, float)) and isinstance(base, (int, float)) and cand < base:
                inversions.append(
                    {"eval_id": entry["eval_id"], "candidate_pass_rate": cand, "baseline_pass_rate": base}
                )

    source_dirty: list[dict[str, Any]] = []
    if isinstance(source_fixtures, dict) and source_fixtures.get("dirty"):
        source_dirty.append(
            {
                "paths": source_fixtures.get("paths", []),
                "entries": source_fixtures.get("entries", []),
            }
        )

    partial_selection: list[dict[str, Any]] = []
    if isinstance(suite_coverage, dict) and suite_coverage.get("partial"):
        partial_selection.append(dict(suite_coverage))

    return {
        "ok": not (infra or zero_cells or inversions or source_dirty or partial_selection),
        "infrastructure_failures": infra,
        "zero_scored_cells": zero_cells,
        "candidate_below_baseline": inversions,
        "source_fixture_dirty": source_dirty,
        "partial_suite_selection": partial_selection,
    }


def format_percent(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "n/a"


def render_sanity_checks_markdown(sanity: Any) -> list[str]:
    if not isinstance(sanity, dict):
        return []
    infra = sanity.get("infrastructure_failures") or []
    zero = sanity.get("zero_scored_cells") or []
    inversions = sanity.get("candidate_below_baseline") or []
    source_dirty = sanity.get("source_fixture_dirty") or []
    partial_selection = sanity.get("partial_suite_selection") or []
    total = len(infra) + len(zero) + len(inversions) + len(source_dirty) + len(partial_selection)
    lines = ["", "## Sanity checks", ""]
    if total == 0 and sanity.get("ok"):
        lines.append("- Status: OK — no anomalies detected")
        return lines
    lines.append(
        f"- Status: REVIEW REQUIRED — {total} anomaly signal(s); do not report this run "
        "as a clean result without investigating and explaining each one"
    )
    if infra:
        cells = ", ".join(f"{f['eval_id']}/{f['configuration']} ({f['status']})" for f in infra)
        lines.append(f"- Infrastructure failures (excluded from pass rate): {cells}")
    if zero:
        cells = ", ".join(f"{c['eval_id']}/{c['configuration']}" for c in zero)
        lines.append(f"- Scored 0% cells (verify grader verdict and executor output): {cells}")
    if inversions:
        cells = ", ".join(
            f"{i['eval_id']} ({format_percent(i['candidate_pass_rate'])} < {format_percent(i['baseline_pass_rate'])})"
            for i in inversions
        )
        lines.append(f"- Candidate below baseline (candidate < baseline): {cells}")
    if source_dirty:
        details = []
        for item in source_dirty:
            entries = item.get("entries") or []
            if entries:
                details.append("; ".join(entries[:8]) + ("; ..." if len(entries) > 8 else ""))
            else:
                details.append(", ".join(item.get("paths") or []))
        lines.append(
            "- Source fixture dirtiness (source fixtures were dirty before or after execution; "
            f"do not treat as clean-source proof): {' | '.join(details)}"
        )
    if partial_selection:
        coverage = partial_selection[0]
        selected = ", ".join(coverage.get("selected_eval_ids") or []) or "none"
        lines.append(
            "- Partial suite selection: "
            f"{coverage.get('selected_eval_count', 0)}/{coverage.get('suite_eval_count', 0)} evals "
            f"({selected}); diagnostic only, not full-suite closing evidence"
        )
    return lines


# --------------------------------------------------------------------------- #
# Execution metrics rendering (executor-only).
#
# The per-run ``metrics`` persisted under each run record holds the *executor*
# subprocess usage only; the grader runs as a separate subprocess whose usage is
# read for error detection but never folded into ``metrics``. Rendering
# therefore reports the skill-run (executor) cost, not whole-run cost, and is
# labeled executor-only so it is not misread as total. Aggregation reads
# ``benchmark["runs"][i]["metrics"]`` (always present) rather than any new
# top-level field, so ``report`` re-renders older ``benchmark.json`` files that
# predate these metric rows.
# --------------------------------------------------------------------------- #
def _format_duration(value: float) -> str:
    return f"{value / 1000:.1f}s"


def _format_tokens(value: float) -> str:
    return f"{int(round(value)):,}"


def _format_cost(value: float) -> str:
    return f"${value:.4f}"


# (metric key in the executor metrics dict, display label, value formatter)
METRIC_DISPLAY: list[tuple[str, str, Callable[[float], str]]] = [
    ("duration_ms", "Execution time", _format_duration),
    ("total_tokens", "Total tokens", _format_tokens),
    ("total_cost_usd", "Cost (USD)", _format_cost),
]


def runs_by_config(configs: list[str], runs: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {config: [] for config in configs}
    for run in runs:
        config = run.get("configuration")
        if config in grouped:
            grouped[config].append(run)
    return grouped


def metric_field_stats(config_runs: list[dict[str, Any]], field: str) -> dict[str, Any]:
    """Aggregate one executor metric field across a config's runs.

    Counts only runs that captured a numeric value for *this specific* field, so
    an absent run (claude non-JSON, codex, a failed/timed-out run) or a captured
    run missing this sub-field is never coerced to 0. ``stddev`` is populated
    only when at least two runs carry a value for the field, so the n=1 default
    never feeds a single-element list into stdev."""
    values: list[float] = []
    reasons: list[str] = []
    for run in config_runs:
        metrics = run.get("metrics") or {}
        if metrics.get("captured") is True:
            value = metrics.get(field)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                values.append(float(value))
            else:
                reasons.append("field not reported by provider")
        else:
            reasons.append(str(metrics.get("reason") or "metrics not captured"))
    return {
        "n": len(values),
        "total": len(config_runs),
        "mean": mean(values),
        "stddev": statistics.stdev(values) if len(values) > 1 else None,
        "reasons": reasons,
    }


def format_metric_cell(stats: dict[str, Any], formatter: Callable[[float], str]) -> str:
    if stats["n"] == 0:
        if stats["total"] == 0:
            return "not captured (no runs)"
        unique = list(dict.fromkeys(stats["reasons"]))
        joined = "; ".join(unique[:3]) + ("; ..." if len(unique) > 3 else "")
        return f"not captured ({joined})"
    cell = formatter(stats["mean"])
    if stats["stddev"] is not None:
        cell += f" ± {formatter(stats['stddev'])}"
    if stats["n"] < stats["total"]:
        cell += f" (n={stats['n']}/{stats['total']})"
    return cell


def format_metric_delta(
    cand_stats: dict[str, Any] | None,
    base_stats: dict[str, Any] | None,
    formatter: Callable[[float], str],
) -> str:
    if not cand_stats or not base_stats or cand_stats["n"] == 0 or base_stats["n"] == 0:
        return "n/a"
    diff = cand_stats["mean"] - base_stats["mean"]
    sign = "+" if diff >= 0 else "-"
    return f"{sign}{formatter(abs(diff))}"


def render_metrics_markdown(
    sorted_configs: list[str],
    runs: list[dict[str, Any]],
    comparison: dict[str, Any] | None,
) -> list[str]:
    grouped = runs_by_config(sorted_configs, runs)
    lines = [
        "",
        "## Execution metrics (executor-only)",
        "",
        "Executor subprocess usage only; grader scoring cost is excluded, so these "
        "are the skill run's own time and tokens, not total run cost. The "
        "`with_skill` vs `without_skill` delta is the meaningful signal. Uncaptured "
        "provider metrics are shown as absent with a reason, never zero.",
        "",
    ]
    include_delta = bool(comparison)
    columns = [f"`{c}`" for c in sorted_configs]
    if include_delta:
        columns.append("Delta")
    lines.append("| Metric | " + " | ".join(columns) + " |")
    lines.append("| --- | " + " | ".join("---" for _ in columns) + " |")
    for field, label, formatter in METRIC_DISPLAY:
        stats_by_config = {c: metric_field_stats(grouped[c], field) for c in sorted_configs}
        cells = [format_metric_cell(stats_by_config[c], formatter) for c in sorted_configs]
        if include_delta:
            cells.append(
                format_metric_delta(
                    stats_by_config.get(comparison["candidate"]),
                    stats_by_config.get(comparison["baseline"]),
                    formatter,
                )
            )
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return lines


def render_metrics_stdout(sorted_configs: list[str], runs: list[dict[str, Any]]) -> list[str]:
    grouped = runs_by_config(sorted_configs, runs)
    lines = ["Execution metrics (executor-only; grader excluded):"]
    for config in sorted_configs:
        parts = [
            f"{label}: {format_metric_cell(metric_field_stats(grouped[config], field), formatter)}"
            for field, label, formatter in METRIC_DISPLAY
        ]
        lines.append(f"  {config}: " + "; ".join(parts))
    return lines


def format_model_value(model: Any) -> str:
    return f"`{model}`" if model else "provider default"


def render_model_lines(benchmark: dict[str, Any]) -> list[str]:
    """Render the benchmark model line(s). Per-role keys fall back to the
    legacy shared ``model`` key so older ``benchmark.json`` files keep their
    current single-line rendering; a two-line executor/grader form appears only
    when the resolved role models differ."""
    model = benchmark.get("model")
    executor_model = benchmark.get("executor_model", model)
    grader_model = benchmark.get("grader_model", model)
    if executor_model == grader_model:
        return [f"- Model: {format_model_value(executor_model)}"]
    return [
        f"- Executor model: {format_model_value(executor_model)}",
        f"- Grader model: {format_model_value(grader_model)}",
    ]


def render_benchmark_markdown(benchmark: dict[str, Any]) -> str:
    configs = list(benchmark.get("configs", []))
    sorted_configs = sorted(configs, key=config_sort_key)
    error_run_count = benchmark.get("error_run_count", 0)
    lines = [
        f"# Eval Benchmark: {benchmark.get('skill_name', 'unknown')}",
        "",
        f"- Agent: `{benchmark.get('agent', 'unknown')}`",
        *render_model_lines(benchmark),
        f"- Generated: {benchmark.get('generated_at', 'unknown')}",
        f"- Runs: {benchmark.get('run_count', 0)} "
        f"({benchmark.get('scored_run_count', 0)} scored, "
        f"{error_run_count} infrastructure failures excluded from pass rate)",
        f"- Metrics captured: {'yes' if benchmark.get('metrics_captured') else 'no'}",
    ]
    coverage = benchmark.get("suite_coverage")
    if isinstance(coverage, dict):
        selected = coverage.get("selected_eval_ids") or []
        if coverage.get("partial"):
            lines.append(
                f"- Suite coverage: {coverage.get('selected_eval_count', 0)}/"
                f"{coverage.get('suite_eval_count', 0)} evals selected "
                f"({', '.join(selected)}); diagnostic subset, not full-suite closing evidence"
            )
        else:
            lines.append(
                f"- Suite coverage: {coverage.get('selected_eval_count', 0)}/"
                f"{coverage.get('suite_eval_count', 0)} evals (full suite)"
            )
    if error_run_count:
        status_counts = benchmark.get("status_counts", {})
        breakdown = ", ".join(
            f"{status}={count}"
            for status, count in sorted(status_counts.items())
            if status != "ok"
        )
        lines.append(f"- Infrastructure failure breakdown: {breakdown}")
    lines.extend(render_sanity_checks_markdown(benchmark.get("sanity_checks")))
    lines.extend(["", "## Overall raw pass rate", ""])
    overall = benchmark.get("overall_pass_rate", {})
    for config in sorted_configs:
        lines.append(f"- `{config}`: {format_percent(overall.get(config))}")
    comparison = benchmark.get("comparison")
    if comparison:
        lines.extend(
            [
                "",
                "## Comparison",
                "",
                f"- Candidate `{comparison['candidate']}`: {format_percent(comparison['candidate_pass_rate'])}",
                f"- Baseline `{comparison['baseline']}`: {format_percent(comparison['baseline_pass_rate'])}",
                f"- Delta: {format_percent(comparison['delta']) if isinstance(comparison.get('delta'), (int, float)) else 'n/a'}",
            ]
        )
    lines.extend(render_metrics_markdown(sorted_configs, benchmark.get("runs", []), comparison))
    lines.extend(["", "## Per-eval raw pass rate", "", "| Eval | " + " | ".join(f"`{c}`" for c in sorted_configs) + " |"])
    lines.append("| --- | " + " | ".join("---" for _ in sorted_configs) + " |")
    for entry in benchmark.get("evals", []):
        cells = [format_percent(entry["configs"].get(c, {}).get("pass_rate")) for c in sorted_configs]
        lines.append(f"| {entry['eval_id']} {entry['eval_name']} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def command_validate(args: argparse.Namespace) -> int:
    report = validate_eval_suite(Path(args.evals_json))
    print_validation_report(report)
    return 0 if report.ok else 1


def build_matrix(suite: EvalSuite, configs: list[str], runs: int, iteration_dir: Path) -> list[RunTask]:
    tasks: list[RunTask] = []
    used_names: set[str] = set()
    for case in suite.evals:
        eval_dir_name = unique_eval_dir_name(case, used_names)
        for config in configs:
            for run_number in range(1, runs + 1):
                run_dir = iteration_dir / eval_dir_name / config / f"run-{run_number}"
                tasks.append(RunTask(case=case, config=config, run_number=run_number, run_dir=run_dir))
    return tasks


def codex_cli_version() -> str | None:
    try:
        completed = subprocess.run(
            ["codex", "--version"], capture_output=True, text=True, timeout=5, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    text = (completed.stdout or completed.stderr).strip()
    return text[:512] if text else None


def run_codex_preflight(
    provider: CodexProvider,
    workspace_root: Path,
    executor_model: str | None,
    grader_model: str | None,
    timeout: float,
) -> bool:
    report: dict[str, Any] = {
        "provider": "codex",
        "attempted_at": utc_now(),
        "cli_version": codex_cli_version(),
        "models": {"executor": executor_model, "grader": grader_model},
        "probes": [],
        "ok": False,
    }
    with tempfile.TemporaryDirectory(prefix="eval-runner-codex-preflight-") as tmp:
        root = Path(tmp)
        executor_cwd = root / "executor-repo"
        executor_cwd.mkdir()
        try:
            git_result = subprocess.run(
                ["git", "init", "--quiet"],
                cwd=executor_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            stderr_text, stderr_meta = bounded_utf8_text(str(exc))
            report["probes"].append({
                "role": "executor", "cwd_shape": "git-backed", "status": "setup_failed",
                "exit_code": None, "timed_out": False,
                "reason": "could not start git for the disposable executor repository",
                "stderr": {**stderr_meta, "text": stderr_text},
            })
            write_json(workspace_root / "preflight.json", report)
            return False
        if git_result.returncode != 0:
            stderr_text, stderr_meta = bounded_utf8_text(git_result.stderr)
            report["probes"].append({
                "role": "executor", "cwd_shape": "git-backed", "status": "setup_failed",
                "exit_code": git_result.returncode, "timed_out": False,
                "reason": "could not initialize disposable git repository",
                "stderr": {**stderr_meta, "text": stderr_text},
            })
            write_json(workspace_root / "preflight.json", report)
            return False

        probe_specs = [
            (
                "executor",
                executor_cwd,
                "git-backed",
                executor_model,
                None,
                "Reply with exactly CODEX_PREFLIGHT_EXECUTOR and no other text.",
                "CODEX_PREFLIGHT_EXECUTOR",
            ),
            (
                "grader",
                root / "grader-empty",
                "empty-non-git",
                grader_model,
                grader_schema(),
                'Return exactly {"verdicts": []} and no other text.',
                '{"verdicts": []}',
            ),
        ]
        (root / "grader-empty").mkdir()
        for role, cwd, cwd_shape, model, schema, prompt, expected in probe_specs:
            run_dir = root / f"{role}-artifacts"
            run_dir.mkdir()
            invocation = provider.build_invocation(
                prompt, run_dir=run_dir, role=role, model=model, schema=schema, cwd=cwd
            )
            stdout, stderr, exit_code, timed_out = run_invocation(invocation, min(timeout, 60.0))
            parsed, _metrics = provider.parse(
                run_dir=run_dir, stdout=stdout, stderr=stderr, exit_code=exit_code, role=role
            )
            output_path = run_dir / f"{role}_codex_last.txt"
            if role == "grader":
                try:
                    parsed_value = json.loads(parsed)
                    expected_value = json.loads(expected)
                except json.JSONDecodeError:
                    parse_ok = False
                else:
                    parse_ok = parsed_value == expected_value
            else:
                parse_ok = parsed.strip() == expected
            parse_ok = parse_ok and output_path.is_file()
            ok = exit_code == 0 and not timed_out and parse_ok
            stderr_text, stderr_meta = bounded_utf8_text(stderr)
            output_text, output_meta = bounded_utf8_text(parsed, 4096)
            probe = {
                "role": role,
                "model": model,
                "cwd_shape": cwd_shape,
                "status": "ok" if ok else ("timeout" if timed_out else "failed"),
                "exit_code": exit_code,
                "timed_out": timed_out,
                "output_file": str(output_path.resolve()),
                "output_file_present": output_path.is_file(),
                "parsed_expected_output": parse_ok,
                "reason": None if ok else "provider readiness probe did not produce the expected output",
                "stderr": {**stderr_meta, "text": stderr_text},
                "parsed_output": {**output_meta, "text": output_text},
            }
            report["probes"].append(probe)
            if not ok:
                write_json(workspace_root / "preflight.json", report)
                return False
    report["ok"] = True
    write_json(workspace_root / "preflight.json", report)
    return True


def command_run(args: argparse.Namespace) -> int:
    # ---- Fail-fast pre-flight: no subprocess launches past this point until
    # every check passes. ----
    evals_path = Path(args.evals_json)
    report = validate_eval_suite(evals_path)
    if not report.ok:
        for error in report.errors:
            print(error, file=sys.stderr)
        return 2

    agent = validate_agent_label(args.agent)
    model = validate_model_label(args.model)
    executor_model = validate_model_label(args.executor_model, "--executor-model") or model
    grader_model = validate_model_label(args.grader_model, "--grader-model") or model
    configs = parse_csv_values(args.config, DEFAULT_CONFIGS)

    runs = args.runs
    if runs < 1 or runs > MAX_RUNS:
        print(f"--runs {runs}: must be between 1 and {MAX_RUNS}", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print(f"--timeout {args.timeout}: must be greater than 0", file=sys.stderr)
        return 2
    if args.concurrency < 1 or args.concurrency > MAX_CONCURRENCY:
        print(f"--concurrency {args.concurrency}: must be between 1 and {MAX_CONCURRENCY}", file=sys.stderr)
        return 2

    suite = load_eval_suite(evals_path)
    suite, suite_coverage = select_eval_cases(suite, args.eval_id)
    skill_path = resolve_skill_source_path(suite, args.skill_path, configs)
    repo_root = find_repo_root(evals_path)
    source_fixtures_before = source_fixture_status(suite, repo_root)

    provider = get_provider(agent)
    if not provider.available():
        print(f"--agent {agent}: provider CLI is not available on this system", file=sys.stderr)
        return 2

    if args.workspace:
        workspace_root = Path(args.workspace)
    else:
        workspace_root = default_workspace_root(evals_path, agent)
    iteration_number = next_iteration_number(workspace_root)
    iteration_dir = workspace_root / f"iteration-{iteration_number}"

    # Empty suite is not an error: exit 0 with an explicit empty result and zero
    # subprocess launches.
    if not suite.evals:
        source_fixtures_after = source_fixture_status(suite, repo_root)
        source_fixtures = combine_source_fixture_status(source_fixtures_before, source_fixtures_after)
        benchmark = aggregate_runs(
            suite,
            configs,
            [],
            agent=agent,
            skill_path=skill_path,
            model=model,
            executor_model=executor_model,
            grader_model=grader_model,
            source_fixtures=source_fixtures,
            suite_coverage=suite_coverage,
        )
        write_json(iteration_dir / "benchmark.json", benchmark)
        write_text(iteration_dir / "benchmark.md", render_benchmark_markdown(benchmark))
        print(f"No evals in suite; wrote empty benchmark to {iteration_dir}")
        return 0

    if isinstance(provider, CodexProvider) and not run_codex_preflight(
        provider, workspace_root, executor_model, grader_model, args.timeout
    ):
        print(
            f"--agent codex: readiness preflight failed; see {workspace_root / 'preflight.json'}",
            file=sys.stderr,
        )
        return 2

    tasks = build_matrix(suite, configs, runs, iteration_dir)
    write_json(
        iteration_dir / "iteration_manifest.json",
        {
            "skill_name": suite.skill_name,
            "agent": agent,
            "model": model,
            "executor_model": executor_model,
            "grader_model": grader_model,
            "configs": configs,
            "runs": runs,
            "timeout_seconds": args.timeout,
            "concurrency": args.concurrency,
            "skill_path": skill_path,
            "source_fixtures": source_fixtures_before,
            "source_fixtures_before": source_fixtures_before,
            "suite_coverage": suite_coverage,
            "expected_executor_passes": len(tasks),
            "created_at": utc_now(),
        },
    )

    # ---- Bounded execution. The thread pool caps concurrent provider
    # subprocesses; each task runs executor then grader sequentially, so at most
    # `concurrency` subprocesses run at any instant. There are no retries. ----
    results: list[dict[str, Any] | None] = [None] * len(tasks)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        future_to_index = {
            pool.submit(
                execute_run, suite, provider, task, skill_path, args.timeout, executor_model, grader_model
            ): index
            for index, task in enumerate(tasks)
        }
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            task = tasks[index]
            try:
                results[index] = future.result()
            except Exception as exc:  # one crashing task must not discard the rest
                total = len(assertions_for_case(suite, task.case))
                results[index] = {
                    "eval_id": task.case.eval_id,
                    "eval_name": task.case.name,
                    "configuration": task.config,
                    "run_number": task.run_number,
                    "status": "runner_error",
                    "scored": False,
                    "passed": 0,
                    "failed": total,
                    "total": total,
                    "pass_rate": None,
                    "expectations": [],
                    "metrics": metrics_absent(agent, "runner error before metrics capture"),
                    "executor_invocation": None,
                    "grader_invocation": None,
                    "grader_error": f"runner error: {exc}",
                    "run_dir": str(task.run_dir),
                }

    runs_records = [record for record in results if record is not None]
    source_fixtures_after = source_fixture_status(suite, repo_root)
    source_fixtures = combine_source_fixture_status(source_fixtures_before, source_fixtures_after)
    benchmark = aggregate_runs(
        suite,
        configs,
        runs_records,
        agent=agent,
        skill_path=skill_path,
        model=model,
        executor_model=executor_model,
        grader_model=grader_model,
        source_fixtures=source_fixtures,
        suite_coverage=suite_coverage,
    )
    write_json(iteration_dir / "benchmark.json", benchmark)
    write_text(iteration_dir / "benchmark.md", render_benchmark_markdown(benchmark))

    print(f"Ran {len(runs_records)} runs into {iteration_dir}")
    comparison = benchmark.get("comparison")
    if comparison:
        print(
            f"{comparison['candidate']}={format_percent(comparison['candidate_pass_rate'])} "
            f"{comparison['baseline']}={format_percent(comparison['baseline_pass_rate'])}"
        )
    sanity = benchmark.get("sanity_checks") or {}
    if sanity.get("ok"):
        print("Sanity checks: OK — no anomalies detected")
    else:
        counts = (
            len(sanity.get("infrastructure_failures") or []),
            len(sanity.get("zero_scored_cells") or []),
            len(sanity.get("candidate_below_baseline") or []),
            len(sanity.get("source_fixture_dirty") or []),
            len(sanity.get("partial_suite_selection") or []),
        )
        print(
            f"Sanity checks: REVIEW REQUIRED — {counts[0]} infra failure(s), "
            f"{counts[1]} zero-scored cell(s), {counts[2]} candidate-below-baseline cell(s), "
            f"{counts[3]} source-fixture dirty signal(s), {counts[4]} partial-suite selection(s); "
            f"see Sanity checks in {iteration_dir / 'benchmark.md'}"
        )
    for line in render_metrics_stdout(sorted(configs, key=config_sort_key), runs_records):
        print(line)
    return 0


def command_report(args: argparse.Namespace) -> int:
    iteration_dir = Path(args.iteration_dir)
    benchmark_path = iteration_dir / "benchmark.json"
    if not benchmark_path.is_file():
        raise CommandError(f"{benchmark_path}: no benchmark.json; run the eval first")
    benchmark = read_json(benchmark_path)
    if not isinstance(benchmark, dict):
        raise CommandError(f"{benchmark_path}: expected a benchmark object")
    markdown = render_benchmark_markdown(benchmark)
    output_path = Path(args.output) if args.output else iteration_dir / "benchmark.md"
    write_text(output_path, markdown)
    print(markdown, end="")
    print(f"Wrote {output_path}", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared skill eval CLI (runner-driven).")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="Validate an evals.json file.")
    validate.add_argument("evals_json", help="Path to an evals.json suite.")
    validate.set_defaults(func=command_validate)

    run = subcommands.add_parser(
        "run", help="Run the bounded eval matrix end to end (execute, grade, aggregate)."
    )
    run.add_argument("evals_json", help="Path to an evals.json suite.")
    run.add_argument("--agent", default=DEFAULT_AGENT, help=f"Provider to run (default: {DEFAULT_AGENT}).")
    run.add_argument(
        "--model",
        default=None,
        help="Model name passed through to the provider CLI verbatim "
        "(e.g. `claude-sonnet-4-6`, `gpt-5.3-codex-spark`). Shared default for the "
        "executor and grader; omit to use the provider's default model.",
    )
    run.add_argument(
        "--executor-model",
        default=None,
        help="Model for the executor subprocess only; overrides --model for that role.",
    )
    run.add_argument(
        "--grader-model",
        default=None,
        help="Model for the grader subprocess only; overrides --model for that role.",
    )
    run.add_argument(
        "--config",
        action="append",
        help="Comma-separated configs to run (default: with_skill,without_skill).",
    )
    run.add_argument(
        "--eval-id",
        action="append",
        help="Comma-separated eval ids for a diagnostic subset. Partial runs are recorded as non-closing.",
    )
    run.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"Runs per eval/config (1..{MAX_RUNS}).")
    run.add_argument("--skill-path", default=None, help="Authoritative skills/<name>/SKILL.md source for with_skill.")
    run.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-subprocess timeout in seconds.",
    )
    run.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Max concurrent provider subprocesses (1..{MAX_CONCURRENCY}).",
    )
    run.add_argument("--workspace", default=None, help="Override the workspace root (default: evals/<skill>/workspace/<agent>).")
    run.set_defaults(func=command_run)

    report = subcommands.add_parser("report", help="Re-render benchmark.md from an iteration's benchmark.json.")
    report.add_argument("iteration_dir", help="Iteration directory containing benchmark.json.")
    report.add_argument("--output", default=None, help="Output markdown path (default: <iteration>/benchmark.md).")
    report.set_defaults(func=command_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
