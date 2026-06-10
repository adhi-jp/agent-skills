#!/usr/bin/env python3
"""Shared skill eval CLI (slim, runner-driven).

The runner drives execution itself. For each eval x config x run it spawns a
fresh executor subprocess with the prompt only (no assertions), then a fresh
grader subprocess with a clean environment and only the executor output plus the
assertions. It aggregates a ``with_skill`` vs ``without_skill`` raw pass-rate
comparison into ``benchmark.json`` and ``benchmark.md``.

All input validation (suite shape, skill source, provider availability, run
bounds) runs before any subprocess launches; invalid input exits non-zero with
zero subprocess launches. Total work is bounded by a hard cap on ``--runs``, a
per-run timeout, and a cap on concurrent provider subprocesses, so a broken rule
cannot trigger large-token or large-parallelism fan-out.

Metrics are never hand-typed or estimated. When a provider exposes machine-
readable usage in its CLI output the runner captures it and stores it with its
source; absence is recorded as absence, never a placeholder number.

The provider selector is a registry, so adding another agent CLI is a new
adapter rather than a hard-coded branch. An optional ``--model`` is passed
through to the selected provider CLI verbatim (whatever model name that CLI
accepts); when omitted each provider uses its own default model. This script is
stdlib-only.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
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


def validate_agent_label(value: str | None) -> str:
    label = (value or DEFAULT_AGENT).strip()
    if not AGENT_LABEL_RE.match(label):
        raise CommandError(
            f"--agent {value!r}: label must match {AGENT_LABEL_RE.pattern}"
        )
    return label


def validate_model_label(value: str | None) -> str | None:
    if value is None:
        return None
    label = value.strip()
    if not label:
        return None
    if not MODEL_LABEL_RE.match(label):
        raise CommandError(
            f"--model {value!r}: model must match {MODEL_LABEL_RE.pattern}"
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


# --------------------------------------------------------------------------- #
# Prompt rendering: executor gets the task only; grader gets output + assertions.
# --------------------------------------------------------------------------- #
def render_executor_prompt(
    suite: EvalSuite,
    case: EvalCase,
    config: str,
    skill_path: str | None,
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


def render_grader_prompt(
    suite: EvalSuite,
    case: EvalCase,
    config: str,
    executor_output: str,
) -> str:
    assertions = assertions_for_case(suite, case)
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
        "- Grade the whole recorded output, not only the intended artifact inside it.",
        "- Wrapper text, headings, Markdown fences, explanations, and meta-notes are part of the output.",
        "- Do not narrow a global `Output ...` assertion to a sub-artifact unless the assertion explicitly scopes it.",
        "- Use byte-level or parser-level checks for exact JSON, verbatim output, raw commit-message, and no-fence assertions.",
        "",
        "## Recorded Output",
        "",
        "```",
        executor_output.rstrip("\n"),
        "```",
        "",
        "## Required response",
        "",
        "Respond with ONLY a JSON object and no other text:",
        '`{"expectations": [{"text": <assertion>, "passed": <true|false>, "evidence": <string>}]}`',
        "Emit every assertion below exactly once, in order, with its text unchanged.",
    ]
    if assertions:
        lines.extend(["", "## Assertions For Grading", ""])
        lines.extend(f"{index}. {assertion}" for index, assertion in enumerate(assertions, start=1))
    else:
        lines.extend(["", "There are no assertions; respond with `{\"expectations\": []}`."])
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

    def build_invocation(self, prompt: str, *, run_dir: Path, role: str, model: str | None = None) -> Invocation:  # pragma: no cover
        raise NotImplementedError

    def parse(self, *, run_dir: Path, stdout: str, stderr: str, exit_code: int | None, role: str) -> tuple[str, dict[str, Any]]:  # pragma: no cover
        raise NotImplementedError


class ClaudeProvider(Provider):
    name = "claude"

    def available(self) -> bool:
        return shutil.which("claude") is not None

    def build_invocation(self, prompt: str, *, run_dir: Path, role: str, model: str | None = None) -> Invocation:
        argv = ["claude", "-p", prompt, "--output-format", "json"]
        if model:
            argv += ["--model", model]
        return Invocation(
            argv=argv,
            env=base_env(),
            cwd=str(find_repo_root(run_dir)),
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
        output = data.get("result")
        if not isinstance(output, str):
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

    def build_invocation(self, prompt: str, *, run_dir: Path, role: str, model: str | None = None) -> Invocation:
        last_message = run_dir / f"{role}_codex_last.txt"
        argv = ["codex", "exec", "-s", "read-only", "-o", str(last_message), "--json"]
        if model:
            argv += ["--model", model]
        argv.append(prompt)
        return Invocation(
            argv=argv,
            env=base_env(),
            cwd=str(find_repo_root(run_dir)),
        )

    def parse(self, *, run_dir: Path, stdout: str, stderr: str, exit_code: int | None, role: str) -> tuple[str, dict[str, Any]]:
        last_message = run_dir / f"{role}_codex_last.txt"
        if last_message.is_file():
            output = last_message.read_text(encoding="utf-8")
        else:
            output = stdout
        # codex token usage is exposed in turn.completed events but is recorded
        # as a deferred enhancement; the slim core keeps Codex metrics absent.
        return output, metrics_absent(self.name, "codex metrics capture is not enabled in the slim core")


# A hermetic provider used by tests. It is dispatched through the exact same run
# matrix as the real adapters (no bypass) but runs a tiny stdlib subprocess
# instead of a network CLI. Its behavior is driven entirely by environment
# pointers so production runs never select it unless explicitly configured.
STUB_RUNNER_SOURCE = r'''
import json, os, re, sys, time

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
    print("%s [%s/%s]" % (text, field("Eval id"), config))
else:
    if grading_rule.get("unparseable"):
        print("this is not a JSON verdict")
    else:
        assertions = re.findall(r"^\d+\. (.+)$", prompt, re.M)
        default_pass = bool(grading_rule.get("pass", False))
        expectations = [
            {"text": text, "passed": default_pass, "evidence": "stub"} for text in assertions
        ]
        print(json.dumps({"expectations": expectations}))

record("exit")

# Test hook: a non-zero executor_exit on the with_skill side simulates an
# executor provider failure so the runner's failure handling can be exercised.
if role == "executor" and config == "with_skill":
    sys.exit(int(spec.get("executor_exit", 0) or 0))
'''


class StubProvider(Provider):
    name = "stub"

    def available(self) -> bool:
        return bool(os.environ.get("EVAL_RUNNER_STUB_FILE"))

    def build_invocation(self, prompt: str, *, run_dir: Path, role: str, model: str | None = None) -> Invocation:
        # The hermetic stub runs no real model, so `model` is accepted to honor
        # the provider contract and then ignored.
        return Invocation(
            argv=[sys.executable, "-c", STUB_RUNNER_SOURCE, role],
            env=base_env(),
            cwd=str(find_repo_root(run_dir)),
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
    # Prefer a dict that actually carries the grader contract over an incidental
    # object captured from surrounding prose.
    for data in parsed:
        if isinstance(data.get("expectations"), list):
            return data, None
    if parsed:
        return parsed[0], None
    return None, "grader output was not parseable JSON"


def summarize_grading(grading: dict[str, Any] | None, assertions: list[str]) -> dict[str, Any]:
    by_text: dict[str, dict[str, Any]] = {}
    if isinstance(grading, dict):
        for item in grading.get("expectations", []):
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                by_text.setdefault(item["text"], item)
    expectations: list[dict[str, Any]] = []
    passed = 0
    for text in assertions:
        item = by_text.get(text)
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
    model: str | None = None,
) -> dict[str, Any]:
    case, config, run_number, run_dir = task.case, task.config, task.run_number, task.run_dir
    outputs_dir = run_dir / "outputs"
    assertions = assertions_for_case(suite, case)

    executor_prompt = render_executor_prompt(suite, case, config, skill_path)
    write_text(run_dir / "prompt.md", executor_prompt)
    executor_inv = provider.build_invocation(executor_prompt, run_dir=run_dir, role="executor", model=model)
    e_stdout, e_stderr, e_exit, e_timeout = run_invocation(executor_inv, timeout)
    executor_output, metrics = provider.parse(
        run_dir=run_dir, stdout=e_stdout, stderr=e_stderr, exit_code=e_exit, role="executor"
    )
    write_text(outputs_dir / "output.txt", executor_output)

    status = "ok"
    grader_inv: Invocation | None = None
    grading: dict[str, Any] | None = None
    grader_error: str | None = None

    if e_timeout:
        status = "executor_timeout"
    elif e_exit not in (0, None):
        status = "executor_failed"
    elif metrics.get("error"):
        status = "executor_failed"
        grader_error = f"executor provider error: {metrics['error']}"

    if status == "ok":
        grader_prompt = render_grader_prompt(suite, case, config, executor_output)
        write_text(run_dir / "grader_prompt.md", grader_prompt)
        grader_inv = provider.build_invocation(grader_prompt, run_dir=run_dir, role="grader", model=model)
        g_stdout, g_stderr, g_exit, g_timeout = run_invocation(grader_inv, timeout)
        grader_output, grader_metrics = provider.parse(
            run_dir=run_dir, stdout=g_stdout, stderr=g_stderr, exit_code=g_exit, role="grader"
        )
        write_text(outputs_dir / "grader_output.txt", grader_output)
        if g_timeout:
            status = "grader_timeout"
        elif g_exit not in (0, None):
            status = "grader_failed"
        elif grader_metrics.get("error"):
            status = "grader_failed"
            grader_error = f"grader provider error: {grader_metrics['error']}"
        else:
            grading, grader_error = parse_grader_output(grader_output)
            if grading is None:
                status = "grader_unparseable"

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
        "executor_invocation": {
            "argv": executor_inv.argv,
            "env_keys": sorted(executor_inv.env),
            "stdin": executor_inv.stdin,
        },
        "grader_invocation": (
            {"argv": grader_inv.argv, "env_keys": sorted(grader_inv.env), "stdin": grader_inv.stdin}
            if grader_inv
            else None
        ),
        "grader_error": grader_error,
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
    return {
        "skill_name": suite.skill_name,
        "agent": agent,
        "model": model,
        "skill_path": skill_path,
        "generated_at": utc_now(),
        "configs": list(configs),
        "run_count": len(runs),
        "scored_run_count": status_counts.get("ok", 0),
        "error_run_count": error_run_count,
        "status_counts": status_counts,
        "metrics_captured": metrics_present,
        "overall_pass_rate": overall,
        "comparison": comparison,
        "evals": per_eval,
        "runs": runs,
    }


def format_percent(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value * 100:.1f}%"
    return "n/a"


def render_benchmark_markdown(benchmark: dict[str, Any]) -> str:
    configs = list(benchmark.get("configs", []))
    sorted_configs = sorted(configs, key=config_sort_key)
    error_run_count = benchmark.get("error_run_count", 0)
    model = benchmark.get("model")
    lines = [
        f"# Eval Benchmark: {benchmark.get('skill_name', 'unknown')}",
        "",
        f"- Agent: `{benchmark.get('agent', 'unknown')}`",
        f"- Model: {f'`{model}`' if model else 'provider default'}",
        f"- Generated: {benchmark.get('generated_at', 'unknown')}",
        f"- Runs: {benchmark.get('run_count', 0)} "
        f"({benchmark.get('scored_run_count', 0)} scored, "
        f"{error_run_count} infrastructure failures excluded from pass rate)",
        f"- Metrics captured: {'yes' if benchmark.get('metrics_captured') else 'no'}",
    ]
    if error_run_count:
        status_counts = benchmark.get("status_counts", {})
        breakdown = ", ".join(
            f"{status}={count}"
            for status, count in sorted(status_counts.items())
            if status != "ok"
        )
        lines.append(f"- Infrastructure failure breakdown: {breakdown}")
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
    skill_path = resolve_skill_source_path(suite, args.skill_path, configs)

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
        benchmark = aggregate_runs(suite, configs, [], agent=agent, skill_path=skill_path, model=model)
        write_json(iteration_dir / "benchmark.json", benchmark)
        write_text(iteration_dir / "benchmark.md", render_benchmark_markdown(benchmark))
        print(f"No evals in suite; wrote empty benchmark to {iteration_dir}")
        return 0

    tasks = build_matrix(suite, configs, runs, iteration_dir)
    write_json(
        iteration_dir / "iteration_manifest.json",
        {
            "skill_name": suite.skill_name,
            "agent": agent,
            "model": model,
            "configs": configs,
            "runs": runs,
            "timeout_seconds": args.timeout,
            "concurrency": args.concurrency,
            "skill_path": skill_path,
            "expected_executor_passes": len(tasks),
            "created_at": utc_now(),
        },
    )

    # ---- Bounded execution. The thread pool caps concurrent provider
    # subprocesses; each task runs executor then grader sequentially, so at most
    # `concurrency` subprocesses run at any instant. There are no retries. ----
    results: list[dict[str, Any]] = [None] * len(tasks)  # type: ignore[list-item]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        future_to_index = {
            pool.submit(execute_run, suite, provider, task, skill_path, args.timeout, model): index
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
    benchmark = aggregate_runs(suite, configs, runs_records, agent=agent, skill_path=skill_path, model=model)
    write_json(iteration_dir / "benchmark.json", benchmark)
    write_text(iteration_dir / "benchmark.md", render_benchmark_markdown(benchmark))

    print(f"Ran {len(runs_records)} runs into {iteration_dir}")
    comparison = benchmark.get("comparison")
    if comparison:
        print(
            f"{comparison['candidate']}={format_percent(comparison['candidate_pass_rate'])} "
            f"{comparison['baseline']}={format_percent(comparison['baseline_pass_rate'])}"
        )
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
        "(e.g. `claude-sonnet-4-6`, `gpt-5.3-codex-spark`). Omit to use the provider's default model.",
    )
    run.add_argument(
        "--config",
        action="append",
        help="Comma-separated configs to run (default: with_skill,without_skill).",
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
