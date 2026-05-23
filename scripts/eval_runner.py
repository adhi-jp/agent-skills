#!/usr/bin/env python3
"""Shared skill eval CLI.

This script is intentionally stdlib-only and file-contract based. It prepares
agent-scoped eval prompts, records externally produced outputs, aggregates
recorded grades, and writes a static review report without starting a server.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import html
import json
import mimetypes
from pathlib import Path
import re
import shutil
import statistics
import sys
from dataclasses import dataclass
from typing import Any


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
RUN_CONTRACT_VERSION = "eval-runner-v1"
AGENT_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


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


@dataclass(frozen=True)
class IterationContext:
    path: Path
    agent: str
    iteration: int
    skill_name: str | None


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


def json_path(base: Path, *parts: Any) -> str:
    suffix = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in parts)
    return f"{base}{suffix}"


def resolve_declared_file(value: str, evals_path: Path, repo_root: Path) -> Path | None:
    declared = Path(value)
    candidates: list[Path]
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

    for field in sorted(set(data) - ALLOWED_TOP_LEVEL_FIELDS):
        errors.append(f"{json_path(evals_path, field)}: unsupported top-level field")

    raw_skill_name = data.get("skill_name")
    if isinstance(raw_skill_name, str) and raw_skill_name.strip():
        skill_name = raw_skill_name
    else:
        errors.append(f"{json_path(evals_path, 'skill_name')}: missing required non-empty string")

    common_assertions = data.get("common_assertions", [])
    if "common_assertions" in data:
        common_assertions = validate_string_list(common_assertions, json_path(evals_path, "common_assertions"), errors)
    elif not isinstance(common_assertions, list):
        common_assertions = []
    common_assertion_count = len(common_assertions)

    scoring = data.get("scoring", {})
    if "scoring" in data:
        if not isinstance(scoring, dict):
            errors.append(f"{json_path(evals_path, 'scoring')}: expected object")
        else:
            for field in sorted(set(scoring) - ALLOWED_SCORING_FIELDS):
                errors.append(f"{json_path(evals_path, 'scoring', field)}: unsupported scoring field")

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

        for field in sorted(set(item) - ALLOWED_EVAL_FIELDS):
            errors.append(f"{item_path}.{field}: unsupported eval field")

        raw_id = item.get("id")
        if not isinstance(raw_id, str) or not raw_id.strip():
            errors.append(f"{item_path}.id: missing required non-empty string")
        else:
            if raw_id in seen_ids:
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

        files = item.get("files", [])
        files = validate_string_list(files, f"{item_path}.files", errors)
        for file_value in files:
            fixture_count += 1
            if resolve_declared_file(file_value, evals_path, repo_root) is None:
                errors.append(f"{item_path}.files: missing fixture file {file_value!r}")

        expectations = item.get("expectations", [])
        validate_string_list(expectations, f"{item_path}.expectations", errors)

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


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip()).strip("-").lower()
    return slug or "unnamed"


def parse_csv_values(values: list[str] | None, default: list[str]) -> list[str]:
    if not values:
        return list(default)
    result: list[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                result.append(item)
    return result


def validate_agent_label(value: str | None) -> str:
    if value is None or not value.strip():
        raise CommandError("--agent is required")
    agent = value.strip()
    if agent in {".", ".."} or not AGENT_LABEL_RE.fullmatch(agent):
        raise CommandError(
            f"--agent {value!r}: expected a safe single path segment using only letters, digits, '.', '_', or '-'"
        )
    return agent


def next_iteration_number(workspace_root: Path) -> int:
    max_seen = 0
    if workspace_root.exists():
        for child in workspace_root.iterdir():
            if not child.is_dir():
                continue
            match = re.fullmatch(r"iteration-(\d+)", child.name)
            if match:
                max_seen = max(max_seen, int(match.group(1)))
    return max_seen + 1


def iteration_path(workspace_root: Path, iteration: str) -> tuple[int, Path]:
    if iteration == "next":
        number = next_iteration_number(workspace_root)
    else:
        raw = iteration.removeprefix("iteration-")
        if not raw.isdigit() or int(raw) < 1:
            raise CommandError("--iteration must be 'next', a positive integer, or iteration-N")
        number = int(raw)
    return number, workspace_root / f"iteration-{number}"


def parse_iteration_context(iteration_dir: Path) -> IterationContext:
    if not iteration_dir.is_dir():
        raise CommandError(f"{iteration_dir}: iteration directory does not exist")
    match = re.fullmatch(r"iteration-(\d+)", iteration_dir.name)
    if not match:
        raise CommandError(
            f"{iteration_dir}: expected an agent-scoped iteration path like evals/<skill-name>/workspace/<agent>/iteration-N"
        )

    parent = iteration_dir.parent
    if parent.name == "workspace":
        raise CommandError(
            f"{iteration_dir}: old canonical workspace layout is unsupported; use evals/<skill-name>/workspace/<agent>/iteration-N"
        )

    agent = validate_agent_label(parent.name)
    resolved_parts = iteration_dir.resolve().parts
    has_default_agent_layout = len(resolved_parts) >= 4 and resolved_parts[-3] == "workspace"
    skill_name = resolved_parts[-4] if has_default_agent_layout else None

    manifest = load_json_if_exists(iteration_dir / "iteration_manifest.json")
    manifest = manifest if isinstance(manifest, dict) else {}
    manifest_agent = manifest.get("agent")
    if manifest_agent is not None:
        if not isinstance(manifest_agent, str) or validate_agent_label(manifest_agent) != agent:
            raise CommandError(
                f"{iteration_dir}: agent mismatch: path agent {agent!r} != manifest agent {manifest_agent!r}"
            )
    elif not has_default_agent_layout:
        raise CommandError(
            f"{iteration_dir}: missing iteration_manifest.json agent; use evals/<skill-name>/workspace/<agent>/iteration-N or prepare with --agent"
        )

    manifest_skill_name = manifest.get("skill_name")
    if skill_name is None and isinstance(manifest_skill_name, str) and manifest_skill_name:
        skill_name = manifest_skill_name

    return IterationContext(
        path=iteration_dir,
        agent=agent,
        iteration=int(match.group(1)),
        skill_name=skill_name,
    )


def canonical_json_bytes(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fixture_fingerprint_entries(suite: EvalSuite, case: EvalCase) -> list[dict[str, Any]]:
    repo_root = find_repo_root(suite.path)
    entries: list[dict[str, Any]] = []
    for file_value in case.files:
        resolved = resolve_declared_file(file_value, suite.path, repo_root)
        if resolved is None:
            raise CommandError(f"{suite.path}: missing fixture file {file_value!r}")
        entries.append(
            {
                "path": file_value,
                "sha256": file_sha256(resolved),
                "size_bytes": resolved.stat().st_size,
            }
        )
    return entries


def eval_fingerprint_inputs(suite: EvalSuite, case: EvalCase) -> dict[str, Any]:
    return {
        "skill_name": suite.skill_name,
        "schema_version": suite.raw.get("schema_version"),
        "common_assertions": suite.common_assertions,
        "scoring": suite.scoring,
        "eval": {
            "id": case.eval_id,
            "name": case.raw.get("name"),
            "project_class": case.raw.get("project_class"),
            "archetype": case.raw.get("archetype"),
            "prompt": case.prompt,
            "expected_output": case.raw.get("expected_output"),
            "files": case.files,
            "expectations": case.expectations,
        },
        "fixtures": fixture_fingerprint_entries(suite, case),
    }


def build_eval_fingerprint(suite: EvalSuite, case: EvalCase) -> tuple[str, dict[str, Any]]:
    inputs = eval_fingerprint_inputs(suite, case)
    return sha256_bytes(canonical_json_bytes(inputs)), inputs


def run_fingerprint_inputs(
    eval_fingerprint: str,
    configuration: str,
    model: str | None,
    grader_model: str | None,
    agent: str,
) -> dict[str, Any]:
    return {
        "run_contract_version": RUN_CONTRACT_VERSION,
        "eval_fingerprint": eval_fingerprint,
        "configuration": configuration,
        "model": model,
        "grader_model": grader_model,
        "agent": agent,
    }


def build_run_fingerprint(
    eval_fingerprint: str,
    configuration: str,
    model: str | None,
    grader_model: str | None,
    agent: str,
) -> tuple[str, dict[str, Any]]:
    inputs = run_fingerprint_inputs(eval_fingerprint, configuration, model, grader_model, agent)
    return sha256_bytes(canonical_json_bytes(inputs)), inputs


def render_run_prompt(
    suite: EvalSuite,
    case: EvalCase,
    config: str,
    run_number: int,
    run_dir: Path,
    skill_path: str | None,
    agent: str,
) -> str:
    lines = [
        "# Eval Run Prompt",
        "",
        f"- Skill: `{suite.skill_name}`",
        f"- Agent: `{agent}`",
        f"- Eval id: `{case.eval_id}`",
        f"- Eval name: {case.name}",
        f"- Configuration: `{config}`",
        f"- Run: `{run_number}`",
        f"- Output directory: `{run_dir / 'outputs'}`",
    ]
    if skill_path:
        lines.append(f"- Skill path: `{skill_path}`")
    lines.extend(["", "## Configuration Contract", ""])
    if config == "without_skill":
        lines.append("Do not use the target skill for this run. Use only the base agent behavior and the prompt below.")
    elif config == "with_skill":
        lines.append("Use the target skill through the invoking agent's normal skill mechanism for this run.")
    else:
        lines.append("Use the behavior implied by this configuration label. Do not assume a provider-specific adapter.")
    lines.extend(["", "## User Prompt", "", case.prompt.strip(), ""])
    if case.files:
        lines.extend(["## Fixture Files", ""])
        lines.extend(f"- `{file_name}`" for file_name in case.files)
        lines.append("")
    if case.expected_output:
        lines.extend(["## Expected Output Summary", "", case.expected_output.strip(), ""])
    lines.extend(
        [
            "## Recording Contract",
            "",
            f"- Save run artifacts under `{run_dir / 'outputs'}`.",
            "- Do not grade this run or write `grading.json`; grading belongs to a separate grader pass.",
            "- After execution, the parent process should record captured metrics with:",
            f"  `python3 scripts/eval_runner.py record {run_dir} --total-tokens <N> --duration-ms <N> --output-chars <N>`",
            "- Parent metric flags also include `--total-duration-seconds`.",
            "- Accepted timing keys are `duration_ms`, `duration_seconds`, `total_duration_seconds`, `executor_duration_seconds`, and `total_tokens`.",
            f"- If external artifacts exist, attach them with `record {run_dir} --outputs <path> --timing <timing.json>`.",
            f"- A separate grader should read `{run_dir / 'grader_prompt.md'}` and write `{run_dir / 'grading.json'}`.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_grader_prompt(
    suite: EvalSuite,
    case: EvalCase,
    config: str,
    run_number: int,
    run_dir: Path,
    agent: str,
) -> str:
    assertions = suite.common_assertions + case.expectations
    lines = [
        "# Eval Grader Prompt",
        "",
        f"- Skill: `{suite.skill_name}`",
        f"- Agent: `{agent}`",
        f"- Eval id: `{case.eval_id}`",
        f"- Eval name: {case.name}",
        f"- Configuration: `{config}`",
        f"- Run: `{run_number}`",
        f"- Run directory: `{run_dir}`",
        f"- Outputs directory: `{run_dir / 'outputs'}`",
        f"- Eval metadata: `{run_dir.parents[1] / 'eval_metadata.json'}`",
        f"- Run manifest: `{run_dir / 'run_manifest.json'}`",
        f"- Write grading JSON to: `{run_dir / 'grading.json'}`",
        "",
        "Grade this run in a separate pass or agent from the executor when the host environment supports it.",
        "Read the eval metadata, run manifest, and run outputs before grading.",
        "Use programmatic checks when an expectation is objectively checkable from files.",
        "",
        "## Required grading.json schema",
        "",
        "- Top-level object.",
        "- `expectations[]` array.",
        "- Each expectation object must include `text`, `passed`, and `evidence`.",
        "- Emit every prepared assertion exactly once, in the order below.",
        "- Keep each `text` value unchanged from `eval_metadata.json.assertions`.",
    ]
    if assertions:
        lines.extend(["", "## Assertions For Grading", ""])
        lines.extend(f"{index}. {assertion}" for index, assertion in enumerate(assertions, start=1))
    return "\n".join(lines) + "\n"


def unique_eval_dir_name(case: EvalCase, used: set[str]) -> str:
    base = f"eval-{slugify(case.name if case.name else case.eval_id)}"
    candidate = base
    if candidate in used:
        candidate = f"{base}-{slugify(case.eval_id)}"
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def command_validate(args: argparse.Namespace) -> int:
    report = validate_eval_suite(Path(args.evals_json))
    print_validation_report(report)
    return 0 if report.ok else 1


def command_prepare(args: argparse.Namespace) -> int:
    suite = load_eval_suite(Path(args.evals_json))
    agent = validate_agent_label(args.agent)
    selected_ids = parse_csv_values(args.eval, [case.eval_id for case in suite.evals])
    configs = parse_csv_values(args.config, ["with_skill", "without_skill"])
    if args.runs < 1:
        raise CommandError("--runs must be at least 1")
    if not configs:
        raise CommandError("at least one --config value is required")

    cases_by_id = {case.eval_id: case for case in suite.evals}
    unknown_ids = [eval_id for eval_id in selected_ids if eval_id not in cases_by_id]
    if unknown_ids:
        raise CommandError(f"unknown eval id(s): {', '.join(unknown_ids)}")

    workspace_root = Path(args.workspace_root) if args.workspace_root else suite.path.parent / "workspace"
    agent_root = workspace_root / agent
    number, root = iteration_path(agent_root, args.iteration)
    if root.exists() and not args.force:
        raise CommandError(f"{root}: iteration already exists; choose another --iteration or pass --force")
    root.mkdir(parents=True, exist_ok=True)

    used_eval_dirs: set[str] = set()
    manifests: list[dict[str, Any]] = []
    for eval_id in selected_ids:
        case = cases_by_id[eval_id]
        eval_dir = root / unique_eval_dir_name(case, used_eval_dirs)
        eval_dir.mkdir(parents=True, exist_ok=True)
        eval_fingerprint, fingerprint_inputs = build_eval_fingerprint(suite, case)
        metadata = {
            "eval_id": case.eval_id,
            "eval_name": case.name,
            "skill_name": suite.skill_name,
            "project_class": case.project_class,
            "archetype": case.archetype,
            "prompt": case.prompt,
            "expected_output": case.expected_output,
            "files": case.files,
            "common_assertions": suite.common_assertions,
            "expectations": case.expectations,
            "assertions": suite.common_assertions + case.expectations,
            "eval_fingerprint": eval_fingerprint,
            "fingerprint_inputs": fingerprint_inputs,
        }
        write_json(eval_dir / "eval_metadata.json", metadata)

        for config in configs:
            for run_number in range(1, args.runs + 1):
                run_dir = eval_dir / config / f"run-{run_number}"
                outputs_dir = run_dir / "outputs"
                outputs_dir.mkdir(parents=True, exist_ok=True)
                run_fingerprint, run_inputs = build_run_fingerprint(
                    eval_fingerprint,
                    config,
                    args.model,
                    args.grader_model,
                    agent,
                )
                manifest = {
                    "created_at": utc_now(),
                    "agent": agent,
                    "iteration": number,
                    "iteration_dir": str(root),
                    "skill_name": suite.skill_name,
                    "skill_path": args.skill_path,
                    "model": args.model,
                    "grader_model": args.grader_model,
                    "eval_id": case.eval_id,
                    "eval_name": case.name,
                    "configuration": config,
                    "run_number": run_number,
                    "run_dir": str(run_dir),
                    "outputs_dir": str(outputs_dir),
                    "executor_prompt": str(run_dir / "prompt.md"),
                    "grader_prompt": str(run_dir / "grader_prompt.md"),
                    "eval_metadata": str(eval_dir / "eval_metadata.json"),
                    "run_contract_version": RUN_CONTRACT_VERSION,
                    "eval_fingerprint": eval_fingerprint,
                    "fingerprint_inputs": fingerprint_inputs,
                    "run_fingerprint": run_fingerprint,
                    "run_fingerprint_inputs": run_inputs,
                }
                prompt = render_run_prompt(suite, case, config, run_number, run_dir, args.skill_path, agent)
                grader_prompt = render_grader_prompt(suite, case, config, run_number, run_dir, agent)
                write_text(run_dir / "prompt.md", prompt)
                write_text(run_dir / "grader_prompt.md", grader_prompt)
                write_json(run_dir / "run_manifest.json", manifest)
                manifests.append(manifest)

    write_json(
        root / "iteration_manifest.json",
        {
            "created_at": utc_now(),
            "agent": agent,
            "skill_name": suite.skill_name,
            "source_evals_json": str(suite.path),
            "iteration": number,
            "configs": configs,
            "runs": args.runs,
            "evals": selected_ids,
            "run_count": len(manifests),
            "model": args.model,
            "grader_model": args.grader_model,
            "run_contract_version": RUN_CONTRACT_VERSION,
        },
    )
    print(f"prepared: {root}")
    print(f"runs: {len(manifests)}")
    return 0


def paths_are_same_file(source: Path, destination: Path) -> bool:
    try:
        return source.samefile(destination)
    except (FileNotFoundError, OSError):
        return False


def copy_path_into(source: Path, destination: Path) -> None:
    if paths_are_same_file(source, destination):
        return
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for child in sorted(source.iterdir()):
            copy_path_into(child, destination / child.name)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def path_contains(parent: Path, child: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def validate_grading_data(data: Any, source: Path | str) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return [f"{source}: expected object"]
    expectations = data.get("expectations")
    if not isinstance(expectations, list):
        errors.append(f"{source}.expectations: expected list")
        return errors
    for index, item in enumerate(expectations):
        item_path = f"{source}.expectations[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path}: expected object")
            continue
        for field in ("text", "passed", "evidence"):
            if field not in item:
                errors.append(f"{item_path}.{field}: missing required field")
        if "text" in item and not isinstance(item["text"], str):
            errors.append(f"{item_path}.text: expected string")
        if "passed" in item and not isinstance(item["passed"], bool):
            errors.append(f"{item_path}.passed: expected boolean")
        if "evidence" in item and not isinstance(item["evidence"], str):
            errors.append(f"{item_path}.evidence: expected string")
    return errors


def expected_assertions_from_metadata(metadata: Any) -> list[str] | None:
    if not isinstance(metadata, dict):
        return None
    assertions = metadata.get("assertions")
    if not isinstance(assertions, list) or not all(isinstance(item, str) for item in assertions):
        return None
    return assertions


def eval_metadata_path_for_run(run_dir: Path) -> Path | None:
    manifest_path = run_dir / "run_manifest.json"
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        if isinstance(manifest, dict) and isinstance(manifest.get("eval_metadata"), str):
            return Path(manifest["eval_metadata"])
    if len(run_dir.parents) >= 2:
        fallback = run_dir.parents[1] / "eval_metadata.json"
        if fallback.exists():
            return fallback
    return None


def load_expected_assertions_for_run(run_dir: Path) -> list[str] | None:
    metadata_path = eval_metadata_path_for_run(run_dir)
    if metadata_path is None or not metadata_path.exists():
        return None
    return expected_assertions_from_metadata(read_json(metadata_path))


def validate_grading_completeness(
    data: Any,
    expected_assertions: list[str] | None,
    source: Path | str,
) -> list[str]:
    if expected_assertions is None or not isinstance(data, dict):
        return []
    expectations = data.get("expectations")
    if not isinstance(expectations, list):
        return []
    actual_texts = [
        item.get("text") if isinstance(item, dict) and isinstance(item.get("text"), str) else None
        for item in expectations
    ]
    if actual_texts == expected_assertions:
        return []
    errors = [
        f"{source}.expectations: expectation text mismatch against eval_metadata.json.assertions; "
        f"expected {len(expected_assertions)} item(s), found {len(actual_texts)}"
    ]
    max_len = max(len(expected_assertions), len(actual_texts))
    for index in range(max_len):
        expected = expected_assertions[index] if index < len(expected_assertions) else None
        actual = actual_texts[index] if index < len(actual_texts) else None
        if expected != actual:
            errors.append(f"{source}.expectations[{index}].text: expected {expected!r}, got {actual!r}")
    return errors


def load_timing_data(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise CommandError(f"{path}: expected timing object")
    return data


def metric_flags_to_timing(args: argparse.Namespace) -> dict[str, int | float]:
    metrics: dict[str, int | float] = {}
    if args.total_tokens is not None:
        metrics["total_tokens"] = args.total_tokens
    if args.duration_ms is not None:
        metrics["duration_ms"] = args.duration_ms
    if args.total_duration_seconds is not None:
        metrics["total_duration_seconds"] = args.total_duration_seconds
    if args.output_chars is not None:
        metrics["output_chars"] = args.output_chars
    return metrics


def command_record(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        raise CommandError(f"{run_dir}: run directory does not exist")
    if not (run_dir / "run_manifest.json").exists():
        raise CommandError(f"{run_dir}: missing run_manifest.json; run prepare first")

    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    if args.outputs:
        source = Path(args.outputs)
        if not source.exists():
            raise CommandError(f"{source}: outputs path does not exist")
        if source.is_dir() and paths_are_same_file(source, outputs_dir):
            pass
        elif source.is_dir():
            if path_contains(source, outputs_dir):
                raise CommandError(f"{source}: outputs source contains destination {outputs_dir}")
            for child in sorted(source.iterdir()):
                copy_path_into(child, outputs_dir / child.name)
        else:
            copy_path_into(source, outputs_dir / source.name)

    timing_metrics = metric_flags_to_timing(args)
    timing_destination = run_dir / "timing.json"
    timing_data: dict[str, Any] | None = None
    if args.timing:
        timing_path = Path(args.timing)
        if not timing_path.exists():
            raise CommandError(f"{timing_path}: timing file does not exist")
        timing_data = load_timing_data(timing_path)
        if not paths_are_same_file(timing_path, timing_destination):
            write_json(timing_destination, timing_data)
    elif timing_metrics and timing_destination.exists():
        timing_data = load_timing_data(timing_destination)
    if timing_metrics:
        if timing_data is None:
            timing_data = {}
        if args.total_duration_seconds is not None and args.duration_ms is None:
            for key in ("duration_ms", "duration_seconds", "executor_duration_seconds"):
                timing_data.pop(key, None)
        timing_data.update(timing_metrics)
        write_json(timing_destination, timing_data)

    if args.grading:
        grading_path = Path(args.grading)
        if not grading_path.exists():
            raise CommandError(f"{grading_path}: grading file does not exist")
        grading_data = read_json(grading_path)
        grading_errors = validate_grading_data(grading_data, grading_path)
        grading_errors.extend(
            validate_grading_completeness(
                grading_data,
                load_expected_assertions_for_run(run_dir),
                grading_path,
            )
        )
        if grading_errors:
            raise CommandError("\n".join(grading_errors))
        grading_destination = run_dir / "grading.json"
        if not paths_are_same_file(grading_path, grading_destination):
            write_json(grading_destination, grading_data)

    print(f"recorded: {run_dir}")
    return 0


def parse_run_number(run_dir: Path) -> int:
    match = re.fullmatch(r"run-(\d+)", run_dir.name)
    return int(match.group(1)) if match else 0


def load_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    return read_json(path)


def read_eval_metadata(eval_dir: Path) -> dict[str, Any]:
    data = load_json_if_exists(eval_dir / "eval_metadata.json")
    return data if isinstance(data, dict) else {}


def extract_summary(grading: dict[str, Any]) -> dict[str, Any]:
    expectations = grading.get("expectations")
    if not isinstance(expectations, list):
        expectations = []
    passed = sum(1 for item in expectations if isinstance(item, dict) and item.get("passed") is True)
    total = len(expectations)
    failed = total - passed
    pass_rate = passed / total if total else None
    return {
        "passed": passed,
        "failed": failed,
        "total": total,
        "pass_rate": pass_rate,
    }


def first_number(*values: Any) -> float | None:
    for value in values:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return float(value)
    return None


def parse_non_negative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("expected non-negative integer")
    return parsed


def parse_non_negative_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected number") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("expected non-negative number")
    return parsed


def extract_timing_seconds(grading: dict[str, Any], timing: dict[str, Any] | None) -> float | None:
    grading_timing = grading.get("timing") if isinstance(grading.get("timing"), dict) else {}
    timing = timing if isinstance(timing, dict) else {}
    duration_ms = first_number(timing.get("duration_ms"), grading_timing.get("duration_ms"))
    if duration_ms is not None:
        return duration_ms / 1000.0
    seconds = first_number(
        timing.get("total_duration_seconds"),
        timing.get("duration_seconds"),
        timing.get("executor_duration_seconds"),
        grading_timing.get("total_duration_seconds"),
        grading_timing.get("duration_seconds"),
        grading_timing.get("executor_duration_seconds"),
    )
    if seconds is not None:
        return seconds
    return None


def extract_tokens(grading: dict[str, Any], timing: dict[str, Any] | None) -> int | None:
    timing = timing if isinstance(timing, dict) else {}
    metrics = grading.get("execution_metrics") if isinstance(grading.get("execution_metrics"), dict) else {}
    value = first_number(timing.get("total_tokens"), metrics.get("total_tokens"))
    return int(value) if value is not None else None


def extract_output_chars(grading: dict[str, Any], timing: dict[str, Any] | None) -> int | None:
    timing = timing if isinstance(timing, dict) else {}
    metrics = grading.get("execution_metrics") if isinstance(grading.get("execution_metrics"), dict) else {}
    value = first_number(timing.get("output_chars"), metrics.get("output_chars"))
    return int(value) if value is not None else None


def extract_tool_calls(grading: dict[str, Any]) -> int | None:
    metrics = grading.get("execution_metrics") if isinstance(grading.get("execution_metrics"), dict) else {}
    total = first_number(metrics.get("total_tool_calls"))
    if total is not None:
        return int(total)
    tool_calls = metrics.get("tool_calls")
    if isinstance(tool_calls, dict):
        values = [value for value in tool_calls.values() if isinstance(value, (int, float))]
        return int(sum(values)) if values else 0
    return None


def extract_errors(grading: dict[str, Any]) -> int | None:
    metrics = grading.get("execution_metrics") if isinstance(grading.get("execution_metrics"), dict) else {}
    value = first_number(metrics.get("errors_encountered"), metrics.get("errors"))
    return int(value) if value is not None else None


def config_sort_key(config: str) -> tuple[int, str]:
    order = {
        "with_skill": 0,
        "new_skill": 0,
        "candidate": 0,
        "without_skill": 1,
        "old_skill": 1,
        "baseline": 1,
    }
    return (order.get(config, 50), config)


def discover_runs(iteration_dir: Path, allow_legacy: bool) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    context = parse_iteration_context(iteration_dir)
    for eval_dir in sorted(path for path in iteration_dir.iterdir() if path.is_dir() and path.name.startswith("eval-")):
        metadata = read_eval_metadata(eval_dir)
        eval_id = str(metadata.get("eval_id") or eval_dir.name.removeprefix("eval-"))
        eval_name = str(metadata.get("eval_name") or eval_dir.name)
        for config_dir in sorted(path for path in eval_dir.iterdir() if path.is_dir() and not path.name.startswith(".")):
            if config_dir.name.startswith("run-") or config_dir.name == "outputs":
                continue
            for run_dir in sorted(path for path in config_dir.iterdir() if path.is_dir() and path.name.startswith("run-")):
                manifest = load_json_if_exists(run_dir / "run_manifest.json")
                manifest = manifest if isinstance(manifest, dict) else {}
                run_agent = manifest.get("agent") or context.agent
                if not isinstance(run_agent, str) or validate_agent_label(run_agent) != context.agent:
                    raise CommandError(
                        f"{run_dir}: agent mismatch: path agent {context.agent!r} != run manifest agent {run_agent!r}"
                    )
                grading_path = run_dir / "grading.json"
                if not grading_path.exists():
                    continue
                grading = read_json(grading_path)
                grading_errors = validate_grading_data(grading, grading_path)
                grading_errors.extend(
                    validate_grading_completeness(
                        grading,
                        expected_assertions_from_metadata(metadata),
                        grading_path,
                    )
                )
                if grading_errors:
                    raise CommandError("\n".join(grading_errors))
                timing_path = run_dir / "timing.json"
                timing = load_json_if_exists(timing_path)
                outputs_dir = run_dir / "outputs"
                layout = "canonical"
                if not outputs_dir.exists() and allow_legacy and (config_dir / "outputs").exists():
                    outputs_dir = config_dir / "outputs"
                    layout = "legacy-split"
                summary = extract_summary(grading)
                result = {
                    **summary,
                    "time_seconds": extract_timing_seconds(grading, timing if isinstance(timing, dict) else None),
                    "tokens": extract_tokens(grading, timing if isinstance(timing, dict) else None),
                    "output_chars": extract_output_chars(grading, timing if isinstance(timing, dict) else None),
                    "tool_calls": extract_tool_calls(grading),
                    "errors": extract_errors(grading),
                }
                runs.append(
                    {
                        "eval_id": eval_id,
                        "eval_name": eval_name,
                        "agent": context.agent,
                        "configuration": config_dir.name,
                        "run_number": parse_run_number(run_dir),
                        "run_dir": str(run_dir),
                        "outputs_dir": str(outputs_dir) if outputs_dir.exists() else None,
                        "layout": layout,
                        "result": result,
                        "expectations": grading.get("expectations", []),
                        "reused": False,
                        "run_contract_version": manifest.get("run_contract_version"),
                        "eval_fingerprint": manifest.get("eval_fingerprint") or metadata.get("eval_fingerprint"),
                        "run_fingerprint": manifest.get("run_fingerprint"),
                        "model": manifest.get("model"),
                        "grader_model": manifest.get("grader_model"),
                        "has_run_manifest": bool(manifest),
                    }
                )
    return runs


def source_run_key(run: dict[str, Any]) -> tuple[str, str, int]:
    return (str(run["eval_id"]), str(run["configuration"]), int(run["run_number"]))


def current_eval_run_key(run: dict[str, Any]) -> tuple[str, int]:
    return (str(run["eval_id"]), int(run["run_number"]))


def clone_reused_run(source_run: dict[str, Any], source_iteration: Path) -> dict[str, Any]:
    reused = dict(source_run)
    reused["result"] = dict(source_run.get("result", {}))
    reused["expectations"] = list(source_run.get("expectations", []))
    reused["reused"] = True
    reused["source_iteration"] = str(source_iteration)
    reused["source_run_dir"] = str(source_run.get("run_dir"))
    reused["fingerprint_match"] = True
    return reused


def choose_expected_metadata(current_run: dict[str, Any], aggregate_model: str | None, aggregate_grader_model: str | None) -> tuple[str | None, str | None]:
    if current_run.get("has_run_manifest"):
        return current_run.get("model"), current_run.get("grader_model")
    return aggregate_model, aggregate_grader_model


def validate_baseline_reuse(
    current_run: dict[str, Any],
    source_run: dict[str, Any],
    baseline_config: str,
    aggregate_model: str | None,
    aggregate_grader_model: str | None,
) -> list[str]:
    errors: list[str] = []
    current_label = f"{current_run.get('run_dir')}:"
    source_label = f"{source_run.get('run_dir')}:"
    current_eval_fingerprint = current_run.get("eval_fingerprint")
    source_eval_fingerprint = source_run.get("eval_fingerprint")
    source_run_fingerprint = source_run.get("run_fingerprint")
    current_agent = current_run.get("agent")
    source_agent = source_run.get("agent")
    if not current_agent:
        errors.append(f"{current_label} missing fingerprint metadata: agent")
        return errors
    if not source_agent:
        errors.append(f"{source_label} missing fingerprint metadata: agent")
        return errors
    if source_agent != current_agent:
        errors.append(f"{source_label} agent mismatch: source {source_agent!r} != current {current_agent!r}")
        return errors
    if not current_eval_fingerprint:
        errors.append(f"{current_label} missing fingerprint metadata: eval_fingerprint")
        return errors
    if not source_eval_fingerprint:
        errors.append(f"{source_label} missing fingerprint metadata: eval_fingerprint")
        return errors
    if not source_run_fingerprint:
        errors.append(f"{source_label} missing fingerprint metadata: run_fingerprint")
        return errors
    if source_eval_fingerprint != current_eval_fingerprint:
        errors.append(f"{source_label} eval fingerprint mismatch for {source_run.get('eval_id')}")
        return errors

    expected_model, expected_grader_model = choose_expected_metadata(
        current_run,
        aggregate_model,
        aggregate_grader_model,
    )
    if source_run.get("model") != expected_model:
        errors.append(
            f"{source_label} model mismatch: source {source_run.get('model')!r} != current {expected_model!r}"
        )
    if source_run.get("grader_model") != expected_grader_model:
        errors.append(
            f"{source_label} grader model mismatch: source {source_run.get('grader_model')!r} != current {expected_grader_model!r}"
        )
    expected_run_fingerprint, _ = build_run_fingerprint(
        str(current_eval_fingerprint),
        baseline_config,
        expected_model,
        expected_grader_model,
        str(current_agent),
    )
    if source_run_fingerprint != expected_run_fingerprint:
        errors.append(f"{source_label} run fingerprint mismatch for {source_run.get('eval_id')} {baseline_config} run-{source_run.get('run_number')}")
    if not source_run.get("outputs_dir"):
        errors.append(f"{source_label} missing canonical outputs directory")
    return errors


def reuse_baseline_runs(
    current_runs: list[dict[str, Any]],
    source_runs: list[dict[str, Any]],
    source_iteration: Path,
    baseline_config: str,
    aggregate_model: str | None,
    aggregate_grader_model: str | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    source_by_key = {source_run_key(run): run for run in source_runs}
    current_baseline_keys = {
        current_eval_run_key(run)
        for run in current_runs
        if run["configuration"] == baseline_config
    }
    candidate_keys = sorted({current_eval_run_key(run) for run in current_runs})
    additions: list[dict[str, Any]] = []
    errors: list[str] = []
    for eval_id, run_number in candidate_keys:
        if (eval_id, run_number) in current_baseline_keys:
            continue
        current_run = next(
            run for run in current_runs if run["eval_id"] == eval_id and run["run_number"] == run_number
        )
        source_run = source_by_key.get((eval_id, baseline_config, run_number))
        if source_run is None:
            errors.append(
                f"{source_iteration}: missing source run for {eval_id} {baseline_config} run-{run_number}"
            )
            continue
        validation_errors = validate_baseline_reuse(
            current_run,
            source_run,
            baseline_config,
            aggregate_model,
            aggregate_grader_model,
        )
        if validation_errors:
            errors.extend(validation_errors)
            continue
        additions.append(clone_reused_run(source_run, source_iteration))
    return additions, errors


def numeric_stats(values: list[float | int | None]) -> dict[str, Any]:
    valid = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    if not valid:
        return {"count": 0, "mean": None, "min": None, "max": None, "stdev": None, "total": None}
    total = sum(valid)
    return {
        "count": len(valid),
        "mean": total / len(valid),
        "min": min(valid),
        "max": max(valid),
        "stdev": statistics.stdev(valid) if len(valid) > 1 else 0.0,
        "total": total,
    }


def pass_rate_for_bools(values: list[bool]) -> float | None:
    if not values:
        return None
    return sum(1 for value in values if value) / len(values)


def note_message_for_rates(prefix: str, eval_id: str, text: str, rates: dict[str, float]) -> str:
    rendered = ", ".join(f"{config}={format_percent(rates[config])}" for config in sorted(rates, key=config_sort_key))
    return f"{prefix}: {eval_id} `{text}` has {rendered}."


def build_analysis(runs: list[dict[str, Any]], configs: list[str], comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    notes: list[dict[str, Any]] = []
    by_expectation: dict[tuple[str, str], dict[str, list[bool]]] = {}
    repeated_expectations: dict[tuple[str, str, str], list[bool]] = {}
    pass_rates_by_eval_config: dict[tuple[str, str], list[float]] = {}
    metrics_by_eval_config: dict[tuple[str, str, str], list[float]] = {}
    for run in runs:
        eval_id = str(run["eval_id"])
        config = str(run["configuration"])
        result = run.get("result", {})
        result = result if isinstance(result, dict) else {}
        pass_rate = result.get("pass_rate")
        if isinstance(pass_rate, (int, float)) and not isinstance(pass_rate, bool):
            pass_rates_by_eval_config.setdefault((eval_id, config), []).append(float(pass_rate))
        for metric_name in ("time_seconds", "tokens", "output_chars"):
            value = result.get(metric_name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                metrics_by_eval_config.setdefault((eval_id, config, metric_name), []).append(float(value))
        for expectation in run.get("expectations", []):
            if not isinstance(expectation, dict) or not isinstance(expectation.get("text"), str):
                continue
            passed = expectation.get("passed")
            if not isinstance(passed, bool):
                continue
            text = expectation["text"]
            by_expectation.setdefault((eval_id, text), {}).setdefault(config, []).append(passed)
            repeated_expectations.setdefault((eval_id, config, text), []).append(passed)

    for (eval_id, text), config_values in sorted(by_expectation.items()):
        rates = {
            config: pass_rate_for_bools(config_values[config])
            for config in configs
            if config in config_values
        }
        rates = {config: rate for config, rate in rates.items() if rate is not None}
        if len(rates) < 2:
            continue
        comparison_configs = [config for config in configs[:2] if config in rates]
        comparison_rates = {config: rates[config] for config in comparison_configs}
        equal_pair = len(comparison_rates) == 2 and len(set(comparison_rates.values())) == 1
        if equal_pair and all(rate == 1.0 for rate in comparison_rates.values()):
            notes.append(
                {
                    "kind": "always_passing_expectation",
                    "eval_id": eval_id,
                    "expectation": text,
                    "pass_rates": comparison_rates,
                    "message": note_message_for_rates("Always-passing expectation across candidate/baseline", eval_id, text, comparison_rates),
                }
            )
        if equal_pair and all(rate == 0.0 for rate in comparison_rates.values()):
            notes.append(
                {
                    "kind": "always_failing_expectation",
                    "eval_id": eval_id,
                    "expectation": text,
                    "pass_rates": comparison_rates,
                    "message": note_message_for_rates("Always-failing expectation across candidate/baseline", eval_id, text, comparison_rates),
                }
            )
        if equal_pair:
            notes.append(
                {
                    "kind": "equal_expectation_pass_rate",
                    "eval_id": eval_id,
                    "expectation": text,
                    "pass_rates": comparison_rates,
                    "message": note_message_for_rates("Equal expectation pass rate across candidate/baseline", eval_id, text, comparison_rates),
                }
            )

    for (eval_id, config, text), values in sorted(repeated_expectations.items()):
        if len(values) > 1 and len(set(values)) > 1:
            notes.append(
                {
                    "kind": "expectation_variance",
                    "eval_id": eval_id,
                    "configuration": config,
                    "expectation": text,
                    "passes": sum(1 for value in values if value),
                    "runs": len(values),
                    "message": f"Repeated-run expectation variance: {eval_id} `{text}` under `{config}` passed {sum(1 for value in values if value)}/{len(values)} runs.",
                }
            )

    for (eval_id, config), values in sorted(pass_rates_by_eval_config.items()):
        if len(values) > 1 and min(values) != max(values):
            notes.append(
                {
                    "kind": "pass_rate_variance",
                    "eval_id": eval_id,
                    "configuration": config,
                    "min_pass_rate": min(values),
                    "max_pass_rate": max(values),
                    "runs": len(values),
                    "message": f"Repeated-run pass-rate variance: {eval_id} under `{config}` ranged from {format_percent(min(values))} to {format_percent(max(values))}.",
                }
            )

    for (eval_id, config, metric_name), values in sorted(metrics_by_eval_config.items()):
        if len(values) > 1 and min(values) != max(values):
            notes.append(
                {
                    "kind": "metric_variance",
                    "eval_id": eval_id,
                    "configuration": config,
                    "metric": metric_name,
                    "min": min(values),
                    "max": max(values),
                    "runs": len(values),
                    "message": f"Repeated-run metric variance: {eval_id} under `{config}` {metric_name} ranged from {format_number(min(values))} to {format_number(max(values))}.",
                }
            )

    for comparison in comparisons:
        pass_delta = comparison.get("pass_rate_delta")
        time_delta = comparison.get("time_seconds_delta")
        tokens_delta = comparison.get("tokens_delta")
        pass_equal = isinstance(pass_delta, (int, float)) and not isinstance(pass_delta, bool) and abs(pass_delta) < 1e-12
        metric_delta = (
            isinstance(time_delta, (int, float))
            and not isinstance(time_delta, bool)
            and abs(time_delta) > 1e-12
        ) or (
            isinstance(tokens_delta, (int, float))
            and not isinstance(tokens_delta, bool)
            and abs(tokens_delta) > 1e-12
        )
        if pass_equal and metric_delta:
            notes.append(
                {
                    "kind": "metric_tradeoff",
                    "candidate_config": comparison.get("candidate_config"),
                    "baseline_config": comparison.get("baseline_config"),
                    "time_seconds_delta": time_delta,
                    "tokens_delta": tokens_delta,
                    "message": "Time/token tradeoff with equal pass rate: "
                    f"`{comparison.get('candidate_config')}` vs `{comparison.get('baseline_config')}` "
                    f"time delta {format_number(time_delta)}s, token delta {format_number(tokens_delta, digits=0)}.",
                }
            )

    return {"notes": notes}


def format_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def format_percent(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{float(value) * 100:.1f}%"


def aggregate_runs(
    iteration_dir: Path,
    runs: list[dict[str, Any]],
    allow_incomplete: bool,
    allow_legacy: bool,
    skill_name: str | None,
    skill_path: str | None,
    model: str | None,
    grader_model: str | None,
    baseline_from: str | None = None,
    baseline_config: str | None = None,
    baseline_reuse_errors: list[str] | None = None,
) -> dict[str, Any]:
    if not runs:
        raise CommandError(f"{iteration_dir}: no graded runs found")

    context = parse_iteration_context(iteration_dir)
    baseline_reuse_errors = baseline_reuse_errors or []
    configs = sorted({run["configuration"] for run in runs}, key=config_sort_key)
    counts = {config: sum(1 for run in runs if run["configuration"] == config) for config in configs}
    incomplete_reasons: list[str] = []
    incomplete_reasons.extend(baseline_reuse_errors)
    smoke = False
    if len(configs) < 2:
        smoke = True
        incomplete_reasons.append("single configuration smoke run")
    if len(set(counts.values())) > 1:
        incomplete_reasons.append(f"configuration run counts differ: {counts}")
    for eval_id in sorted({run["eval_id"] for run in runs}):
        eval_runs = [run for run in runs if run["eval_id"] == eval_id]
        eval_configs = {run["configuration"] for run in eval_runs}
        missing_configs = [config for config in configs if config not in eval_configs]
        if missing_configs:
            incomplete_reasons.append(f"{eval_id} missing config(s): {', '.join(missing_configs)}")
            continue
        eval_counts = {
            config: sum(1 for run in eval_runs if run["configuration"] == config)
            for config in configs
        }
        if len(set(eval_counts.values())) > 1:
            incomplete_reasons.append(f"{eval_id} run counts differ by config: {eval_counts}")
    missing_timing = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run["result"].get("time_seconds") is None
    ]
    if missing_timing:
        incomplete_reasons.append(f"missing timing for {len(missing_timing)} run(s): {', '.join(missing_timing[:5])}")
    missing_tokens = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run["result"].get("tokens") is None
    ]
    if missing_tokens:
        incomplete_reasons.append(f"missing tokens for {len(missing_tokens)} run(s): {', '.join(missing_tokens[:5])}")

    if incomplete_reasons and not allow_incomplete:
        raise CommandError(
            "incomplete benchmark: "
            + "; ".join(incomplete_reasons)
            + "; pass --allow-incomplete for a smoke/incomplete aggregate"
        )

    by_config: dict[str, dict[str, Any]] = {}
    for config in configs:
        config_runs = [run for run in runs if run["configuration"] == config]
        by_config[config] = {
            "runs": len(config_runs),
            "evals": sorted({run["eval_id"] for run in config_runs}),
            "reused_runs": sum(1 for run in config_runs if run.get("reused")),
            "pass_rate": numeric_stats([run["result"].get("pass_rate") for run in config_runs]),
            "time_seconds": numeric_stats([run["result"].get("time_seconds") for run in config_runs]),
            "tokens": numeric_stats([run["result"].get("tokens") for run in config_runs]),
            "output_chars": numeric_stats([run["result"].get("output_chars") for run in config_runs]),
            "tool_calls": numeric_stats([run["result"].get("tool_calls") for run in config_runs]),
            "passed_expectations_total": sum(int(run["result"].get("passed") or 0) for run in config_runs),
            "failed_expectations_total": sum(int(run["result"].get("failed") or 0) for run in config_runs),
            "total_expectations": sum(int(run["result"].get("total") or 0) for run in config_runs),
            "errors_total": sum(int(run["result"].get("errors") or 0) for run in config_runs),
        }

    comparisons: list[dict[str, Any]] = []
    if len(configs) >= 2 and not smoke:
        candidate, baseline = configs[0], configs[1]
        candidate_rate = by_config[candidate]["pass_rate"]["mean"]
        baseline_rate = by_config[baseline]["pass_rate"]["mean"]
        candidate_time = by_config[candidate]["time_seconds"]["mean"]
        baseline_time = by_config[baseline]["time_seconds"]["mean"]
        candidate_tokens = by_config[candidate]["tokens"]["mean"]
        baseline_tokens = by_config[baseline]["tokens"]["mean"]
        comparisons.append(
            {
                "candidate_config": candidate,
                "baseline_config": baseline,
                "pass_rate_delta": None
                if candidate_rate is None or baseline_rate is None
                else candidate_rate - baseline_rate,
                "time_seconds_delta": None
                if candidate_time is None or baseline_time is None
                else candidate_time - baseline_time,
                "tokens_delta": None
                if candidate_tokens is None or baseline_tokens is None
                else candidate_tokens - baseline_tokens,
            }
        )

    metadata: dict[str, Any] = {
        "timestamp": utc_now(),
        "iteration_dir": str(iteration_dir),
        "agent": context.agent,
        "skill_name": skill_name or context.skill_name or derive_skill_name(iteration_dir),
        "configs": configs,
        "evals_run": sorted({run["eval_id"] for run in runs}),
        "runs_per_configuration": counts,
        "incomplete": bool(incomplete_reasons),
        "smoke": smoke,
        "incomplete_reasons": incomplete_reasons,
        "allow_incomplete": allow_incomplete,
        "legacy_layout_allowed": allow_legacy,
        "baseline_from": baseline_from,
        "baseline_config": baseline_config,
        "baseline_reuse_errors": baseline_reuse_errors,
        "baseline_reused_runs": sum(1 for run in runs if run.get("reused")),
    }
    if skill_path:
        metadata["skill_path"] = skill_path
    if model:
        metadata["executor_model"] = model
    if grader_model:
        metadata["grader_model"] = grader_model

    return {
        "metadata": metadata,
        "configs": by_config,
        "comparisons": comparisons,
        "analysis": build_analysis(runs, configs, comparisons),
        "runs": runs,
    }


def derive_skill_name(iteration_dir: Path) -> str | None:
    parts = iteration_dir.resolve().parts
    if len(parts) >= 4 and parts[-3] == "workspace":
        return parts[-4]
    return None


def render_benchmark_markdown(benchmark: dict[str, Any]) -> str:
    metadata = benchmark["metadata"]
    status = "incomplete smoke" if metadata.get("smoke") else ("incomplete" if metadata.get("incomplete") else "complete")
    lines = [
        "# Eval Benchmark",
        "",
        f"- Skill: `{metadata.get('skill_name') or 'unknown'}`",
        f"- Agent: `{metadata.get('agent') or 'unknown'}`",
        f"- Iteration: `{metadata.get('iteration_dir')}`",
        f"- Status: `{status}`",
        f"- Configs: {', '.join(f'`{name}` ({count} runs)' for name, count in metadata['runs_per_configuration'].items())}",
        "",
        "## Summary",
        "",
        "| Config | Runs | Reused | Mean pass rate | Total time | Mean tokens | Total tokens | Output chars | Failed expectations | Errors |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config, stats in benchmark["configs"].items():
        lines.append(
            "| {config} | {runs} | {reused} | {pass_rate} | {time_total} | {tokens_mean} | {tokens_total} | {output_chars} | {failed}/{total_expectations} | {errors} |".format(
                config=config,
                runs=stats["runs"],
                reused=stats.get("reused_runs", 0),
                pass_rate=format_percent(stats["pass_rate"]["mean"]),
                time_total=format_number(stats["time_seconds"].get("total")),
                tokens_mean=format_number(stats["tokens"]["mean"], digits=0),
                tokens_total=format_number(stats["tokens"].get("total"), digits=0),
                output_chars=format_number(stats.get("output_chars", {}).get("total"), digits=0),
                failed=stats.get("failed_expectations_total", 0),
                total_expectations=stats.get("total_expectations", 0),
                errors=stats["errors_total"],
            )
        )

    lines.extend(["", "## Comparison", ""])
    if benchmark["comparisons"]:
        for comparison in benchmark["comparisons"]:
            lines.append(
                "- `{candidate_config}` vs `{baseline_config}`: pass-rate delta {pass_rate_delta}, time delta {time_seconds_delta}s, token delta {tokens_delta}".format(
                    candidate_config=comparison["candidate_config"],
                    baseline_config=comparison["baseline_config"],
                    pass_rate_delta=format_percent(comparison["pass_rate_delta"]),
                    time_seconds_delta=format_number(comparison["time_seconds_delta"]),
                    tokens_delta=format_number(comparison["tokens_delta"], digits=0),
                )
            )
    else:
        lines.append("- No comparative delta is reported for single-config smoke or incomplete runs.")

    analysis_notes = benchmark.get("analysis", {}).get("notes", [])
    lines.extend(["", "## Analysis", ""])
    if analysis_notes:
        for note in analysis_notes:
            if isinstance(note, dict):
                lines.append(f"- {note.get('message', '')}")
    else:
        lines.append("- No analyzer notes.")

    if metadata.get("incomplete_reasons"):
        lines.extend(["", "## Incomplete Reasons", ""])
        lines.extend(f"- {reason}" for reason in metadata["incomplete_reasons"])

    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| Eval | Config | Run | Reused | Pass rate | Time | Tokens | Output chars | Layout |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for run in benchmark["runs"]:
        result = run["result"]
        lines.append(
            "| {eval_id} | {config} | {run_number} | {reused} | {pass_rate} | {time} | {tokens} | {output_chars} | {layout} |".format(
                eval_id=run["eval_id"],
                config=run["configuration"],
                run_number=run["run_number"],
                reused="yes" if run.get("reused") else "no",
                pass_rate=format_percent(result.get("pass_rate")),
                time=format_number(result.get("time_seconds")),
                tokens=format_number(result.get("tokens"), digits=0),
                output_chars=format_number(result.get("output_chars"), digits=0),
                layout=run["layout"],
            )
        )
    return "\n".join(lines) + "\n"


def benchmark_output_paths(iteration_dir: Path, output: str | None) -> tuple[Path, Path]:
    if output is None:
        json_path_out = iteration_dir / "benchmark.json"
    else:
        requested = Path(output)
        if requested.suffix == ".md":
            return requested.with_suffix(".json"), requested
        if requested.suffix == ".json":
            json_path_out = requested
        elif requested.suffix:
            json_path_out = requested
        else:
            json_path_out = requested / "benchmark.json"
    return json_path_out, json_path_out.with_suffix(".md")


def command_aggregate(args: argparse.Namespace) -> int:
    iteration_dir = Path(args.iteration_dir)
    current_context = parse_iteration_context(iteration_dir)
    runs = discover_runs(iteration_dir, args.allow_legacy)
    baseline_errors: list[str] = []
    if args.baseline_from:
        baseline_from = Path(args.baseline_from)
        source_context = parse_iteration_context(baseline_from)
        if source_context.agent != current_context.agent:
            raise CommandError(
                f"{baseline_from}: agent mismatch: source {source_context.agent!r} != current {current_context.agent!r}"
            )
        source_runs = discover_runs(baseline_from, allow_legacy=False)
        additions, baseline_errors = reuse_baseline_runs(
            current_runs=runs,
            source_runs=source_runs,
            source_iteration=baseline_from,
            baseline_config=args.baseline_config,
            aggregate_model=args.model,
            aggregate_grader_model=args.grader_model,
        )
        runs.extend(additions)
    benchmark = aggregate_runs(
        iteration_dir=iteration_dir,
        runs=runs,
        allow_incomplete=args.allow_incomplete,
        allow_legacy=args.allow_legacy,
        skill_name=args.skill_name,
        skill_path=args.skill_path,
        model=args.model,
        grader_model=args.grader_model,
        baseline_from=args.baseline_from,
        baseline_config=args.baseline_config if args.baseline_from else None,
        baseline_reuse_errors=baseline_errors,
    )
    json_path_out, markdown_path = benchmark_output_paths(iteration_dir, args.output)
    write_json(json_path_out, benchmark)
    write_text(markdown_path, render_benchmark_markdown(benchmark))
    print(f"benchmark_json: {json_path_out}")
    print(f"benchmark_markdown: {markdown_path}")
    return 0


def read_text_preview(path: Path, max_chars: int = 20000) -> str:
    try:
        data = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        mime, _ = mimetypes.guess_type(str(path))
        size = path.stat().st_size
        return f"[binary file: {mime or 'application/octet-stream'}, {size} bytes]"
    if len(data) > max_chars:
        return data[:max_chars] + "\n[truncated]"
    return data


def output_files_for_run(run: dict[str, Any]) -> list[Path]:
    outputs_dir = run.get("outputs_dir")
    if not outputs_dir:
        return []
    root = Path(outputs_dir)
    if not root.is_dir():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def find_previous_feedback(previous_workspace: str | None) -> list[tuple[Path, str]]:
    if not previous_workspace:
        return []
    root = Path(previous_workspace)
    if not root.exists():
        return []
    candidates = []
    if root.is_file():
        candidates = [root]
    else:
        candidates = sorted(root.glob("**/feedback.json")) + sorted(root.glob("**/review_feedback.json"))
    feedback: list[tuple[Path, str]] = []
    for path in candidates[:10]:
        feedback.append((path, read_text_preview(path)))
    return feedback


def load_previous_iteration_benchmark(previous_iteration: str | None) -> dict[str, Any] | None:
    if not previous_iteration:
        return None
    path = Path(previous_iteration)
    benchmark_path = path if path.is_file() else path / "benchmark.json"
    if not benchmark_path.exists():
        return None
    data = read_json(benchmark_path)
    if not isinstance(data, dict):
        raise CommandError(f"{benchmark_path}: expected benchmark object")
    return data


def benchmark_pass_rates_by_eval_config(benchmark: dict[str, Any] | None) -> dict[tuple[str, str], float]:
    if not benchmark:
        return {}
    values: dict[tuple[str, str], list[float]] = {}
    for run in benchmark.get("runs", []):
        if not isinstance(run, dict):
            continue
        result = run.get("result") if isinstance(run.get("result"), dict) else {}
        rate = result.get("pass_rate")
        if not isinstance(rate, (int, float)) or isinstance(rate, bool):
            continue
        values.setdefault((str(run.get("eval_id")), str(run.get("configuration"))), []).append(float(rate))
    return {key: sum(rates) / len(rates) for key, rates in values.items() if rates}


def previous_runs_by_key(previous_benchmark: dict[str, Any] | None) -> dict[tuple[str, str, int], dict[str, Any]]:
    if not previous_benchmark:
        return {}
    result: dict[tuple[str, str, int], dict[str, Any]] = {}
    for run in previous_benchmark.get("runs", []):
        if not isinstance(run, dict):
            continue
        try:
            key = (str(run.get("eval_id")), str(run.get("configuration")), int(run.get("run_number")))
        except (TypeError, ValueError):
            continue
        result[key] = run
    return result


def render_feedback_script() -> str:
    return """
<script>
(function () {
  var button = document.getElementById("download-feedback");
  if (!button) return;
  button.addEventListener("click", function () {
    var feedback = [];
    document.querySelectorAll("textarea[data-feedback-run]").forEach(function (textarea) {
      feedback.push({
        run: textarea.getAttribute("data-feedback-run"),
        note: textarea.value
      });
    });
    var payload = {
      schema_version: "1.0",
      generated_at: new Date().toISOString(),
      feedback: feedback
    };
    var blob = new Blob([JSON.stringify(payload, null, 2) + "\\n"], {type: "application/json"});
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = "feedback.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  });
}());
</script>""".strip()


def render_report_html(
    iteration_dir: Path,
    benchmark: dict[str, Any] | None,
    previous_feedback: list[tuple[Path, str]],
    previous_benchmark: dict[str, Any] | None = None,
) -> str:
    runs = benchmark["runs"] if benchmark else discover_runs(iteration_dir, allow_legacy=True)
    previous_run_lookup = previous_runs_by_key(previous_benchmark)
    title = f"Eval Review: {iteration_dir.name}"
    parts = [
        "<!doctype html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        f"<title>{html.escape(title)}</title>",
        "<style>",
        "body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:24px;line-height:1.45;color:#1f2933;background:#fafafa}",
        "h1,h2,h3{color:#102a43}",
        "section{margin:24px 0;padding:16px;border:1px solid #d9e2ec;border-radius:6px;background:white}",
        "pre{white-space:pre-wrap;background:#f0f4f8;padding:12px;border-radius:6px;overflow:auto}",
        "table{border-collapse:collapse;width:100%;background:white}",
        "th,td{border:1px solid #d9e2ec;padding:8px;text-align:left;vertical-align:top}",
        "textarea{width:100%;min-height:90px;font:inherit}",
        "button{padding:8px 12px;border:1px solid #486581;border-radius:4px;background:#f0f4f8;color:#102a43;cursor:pointer}",
        "details{margin:8px 0}",
        ".pass{color:#0f766e;font-weight:600}.fail{color:#b42318;font-weight:600}.muted{color:#627d98}",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>{html.escape(title)}</h1>",
        f'<p class="muted">Static report generated at {html.escape(utc_now())}. No server was started.</p>',
    ]

    if benchmark:
        metadata = benchmark["metadata"]
        parts.extend(
            [
                "<section>",
                "<h2>Benchmark Summary</h2>",
                f"<p>Skill: <code>{html.escape(str(metadata.get('skill_name') or 'unknown'))}</code></p>",
                f"<p>Agent: <code>{html.escape(str(metadata.get('agent') or 'unknown'))}</code></p>",
                f"<p>Status: <code>{html.escape('incomplete' if metadata.get('incomplete') else 'complete')}</code></p>",
                "<table><thead><tr><th>Config</th><th>Runs</th><th>Reused</th><th>Mean pass rate</th><th>Total time</th><th>Mean tokens</th><th>Total tokens</th><th>Output chars</th><th>Failed expectations</th></tr></thead><tbody>",
            ]
        )
        for config, stats in benchmark["configs"].items():
            parts.append(
                "<tr><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}/{}</td></tr>".format(
                    html.escape(config),
                    stats["runs"],
                    stats.get("reused_runs", 0),
                    html.escape(format_percent(stats["pass_rate"]["mean"])),
                    html.escape(format_number(stats["time_seconds"].get("total"))),
                    html.escape(format_number(stats["tokens"]["mean"], digits=0)),
                    html.escape(format_number(stats["tokens"].get("total"), digits=0)),
                    html.escape(format_number(stats.get("output_chars", {}).get("total"), digits=0)),
                    stats.get("failed_expectations_total", 0),
                    stats.get("total_expectations", 0),
                )
            )
        parts.extend(["</tbody></table>", "</section>"])

        analysis_notes = benchmark.get("analysis", {}).get("notes", [])
        parts.extend(["<section>", "<h2>Benchmark Analysis</h2>"])
        if analysis_notes:
            parts.append("<ul>")
            for note in analysis_notes:
                if isinstance(note, dict):
                    parts.append(f"<li>{html.escape(str(note.get('message', '')))}</li>")
            parts.append("</ul>")
        else:
            parts.append('<p class="muted">No analyzer notes.</p>')
        parts.append("</section>")

    if benchmark and previous_benchmark:
        current_rates = benchmark_pass_rates_by_eval_config(benchmark)
        previous_rates = benchmark_pass_rates_by_eval_config(previous_benchmark)
        shared_keys = sorted(set(current_rates) & set(previous_rates))
        parts.extend(["<section>", "<h2>Previous Iteration Comparison</h2>"])
        if shared_keys:
            parts.append("<table><thead><tr><th>Eval</th><th>Config</th><th>Current</th><th>Previous</th><th>Delta</th></tr></thead><tbody>")
            for eval_id, config in shared_keys:
                current_rate = current_rates[(eval_id, config)]
                previous_rate = previous_rates[(eval_id, config)]
                parts.append(
                    "<tr><td>{}</td><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                        html.escape(eval_id),
                        html.escape(config),
                        html.escape(format_percent(current_rate)),
                        html.escape(format_percent(previous_rate)),
                        html.escape(format_percent(current_rate - previous_rate)),
                    )
                )
            parts.append("</tbody></table>")
        else:
            parts.append('<p class="muted">No shared eval/config pass rates found.</p>')
        parts.append("</section>")

    parts.extend(
        [
            "<section>",
            "<h2>Feedback</h2>",
            '<p class="muted">Notes are kept in this browser until downloaded.</p>',
            '<button id="download-feedback" type="button">Download feedback.json</button>',
            "</section>",
        ]
    )

    if previous_feedback:
        parts.extend(["<section>", "<h2>Previous Feedback</h2>"])
        for path, text in previous_feedback:
            parts.append(f"<h3>{html.escape(str(path))}</h3>")
            parts.append(f"<pre>{html.escape(text)}</pre>")
        parts.append("</section>")

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault((run["eval_id"], run.get("eval_name") or run["eval_id"]), []).append(run)

    for (eval_id, eval_name), eval_runs in grouped.items():
        parts.extend(
            [
                "<section>",
                f"<h2>{html.escape(eval_id)}: {html.escape(eval_name)}</h2>",
            ]
        )
        metadata_path = Path(eval_runs[0]["run_dir"]).parents[1] / "eval_metadata.json"
        metadata = read_eval_metadata(metadata_path.parent)
        if metadata.get("prompt"):
            parts.extend(["<h3>Prompt</h3>", f"<pre>{html.escape(str(metadata['prompt']))}</pre>"])
        for run in eval_runs:
            result = run["result"]
            parts.extend(
                [
                    f"<h3>{html.escape(run['configuration'])} run-{run['run_number']}</h3>",
                    f"<p>Pass rate: <strong>{html.escape(format_percent(result.get('pass_rate')))}</strong>; "
                    f"time: {html.escape(format_number(result.get('time_seconds')))}; "
                    f"tokens: {html.escape(format_number(result.get('tokens'), digits=0))}; "
                    f"output chars: {html.escape(format_number(result.get('output_chars'), digits=0))}</p>",
                    "<h4>Outputs</h4>",
                ]
            )
            output_files = output_files_for_run(run)
            if output_files:
                for path in output_files:
                    parts.append(f"<h5>{html.escape(path.name)}</h5>")
                    parts.append(f"<pre>{html.escape(read_text_preview(path))}</pre>")
            else:
                parts.append('<p class="muted">No output files found for this run.</p>')
            previous_run = previous_run_lookup.get(
                (str(run["eval_id"]), str(run["configuration"]), int(run["run_number"]))
            )
            if previous_run:
                parts.append("<details><summary>Previous outputs</summary>")
                previous_output_files = output_files_for_run(previous_run)
                if previous_output_files:
                    for path in previous_output_files:
                        parts.append(f"<h5>{html.escape(path.name)}</h5>")
                        parts.append(f"<pre>{html.escape(read_text_preview(path))}</pre>")
                else:
                    parts.append('<p class="muted">No previous output files found for this run.</p>')
                parts.append("</details>")
            parts.extend(["<h4>Grades</h4>", "<table><thead><tr><th>Status</th><th>Expectation</th><th>Evidence</th></tr></thead><tbody>"])
            for expectation in run.get("expectations", []):
                if not isinstance(expectation, dict):
                    continue
                passed = expectation.get("passed") is True
                status = "pass" if passed else "fail"
                parts.append(
                    '<tr><td class="{status}">{label}</td><td>{text}</td><td>{evidence}</td></tr>'.format(
                        status=status,
                        label="pass" if passed else "fail",
                        text=html.escape(str(expectation.get("text", ""))),
                        evidence=html.escape(str(expectation.get("evidence", ""))),
                    )
                )
            parts.append("</tbody></table>")
            feedback_key = f"{run['eval_id']}:{run['configuration']}:run-{run['run_number']}"
            parts.extend(
                [
                    "<h4>Feedback</h4>",
                    f'<textarea data-feedback-run="{html.escape(feedback_key)}"></textarea>',
                ]
            )
        parts.append("</section>")

    parts.extend([render_feedback_script(), "</body>", "</html>"])
    return "\n".join(parts) + "\n"


def command_report(args: argparse.Namespace) -> int:
    iteration_dir = Path(args.iteration_dir)
    parse_iteration_context(iteration_dir)
    benchmark_path = Path(args.benchmark) if args.benchmark else iteration_dir / "benchmark.json"
    benchmark = load_json_if_exists(benchmark_path)
    if benchmark is not None and not isinstance(benchmark, dict):
        raise CommandError(f"{benchmark_path}: expected benchmark object")
    previous_feedback = find_previous_feedback(args.previous_workspace)
    previous_benchmark = load_previous_iteration_benchmark(args.previous_iteration)
    output = Path(args.output) if args.output else iteration_dir / "review.html"
    write_text(output, render_report_html(iteration_dir, benchmark, previous_feedback, previous_benchmark))
    print(f"review_html: {output}")
    print("server: not started")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    cwd = Path.cwd()
    workspace_dirs = sorted(Path("evals").glob("*/workspace")) if Path("evals").exists() else []
    print(f"python: {sys.version.split()[0]}")
    print(f"executable: {sys.executable}")
    print(f"cwd: {cwd}")
    print(f"AGENTS.md: {'present' if (cwd / 'AGENTS.md').exists() else 'missing'}")
    print(f"CLAUDE.md: {'present' if (cwd / 'CLAUDE.md').exists() else 'missing'}")
    print(f"eval_workspaces: {len(workspace_dirs)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare, record, aggregate, and review repository skill evals.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="Validate an evals.json file.")
    validate.add_argument("evals_json")
    validate.set_defaults(func=command_validate)

    prepare = subcommands.add_parser("prepare", help="Create canonical run directories and prompts.")
    prepare.add_argument("evals_json")
    prepare.add_argument("--agent", required=True, help="Agent label for the workspace path, e.g. codex, claude, or gemini.")
    prepare.add_argument("--iteration", default="next", help="'next', a positive integer, or iteration-N.")
    prepare.add_argument("--eval", action="append", help="Eval id or comma-separated eval ids. Defaults to all evals.")
    prepare.add_argument("--config", action="append", help="Configuration label or comma-separated labels.")
    prepare.add_argument("--runs", type=int, default=1)
    prepare.add_argument("--workspace-root")
    prepare.add_argument("--skill-path")
    prepare.add_argument("--model")
    prepare.add_argument("--grader-model")
    prepare.add_argument("--force", action="store_true", help="Allow writing into an existing iteration directory.")
    prepare.set_defaults(func=command_prepare)

    record = subcommands.add_parser("record", help="Attach external outputs, timing, and grading to a prepared run.")
    record.add_argument("run_dir")
    record.add_argument("--outputs")
    record.add_argument("--timing")
    record.add_argument("--grading")
    record.add_argument("--total-tokens", type=parse_non_negative_int)
    record.add_argument("--duration-ms", type=parse_non_negative_int)
    record.add_argument("--total-duration-seconds", type=parse_non_negative_float)
    record.add_argument("--output-chars", type=parse_non_negative_int)
    record.set_defaults(func=command_record)

    aggregate = subcommands.add_parser("aggregate", help="Aggregate graded runs into benchmark JSON and Markdown.")
    aggregate.add_argument("iteration_dir")
    aggregate.add_argument("--allow-legacy", action="store_true", help="Read legacy split output directories.")
    aggregate.add_argument("--allow-incomplete", action="store_true", help="Write smoke/incomplete aggregate instead of failing.")
    aggregate.add_argument("--skill-name")
    aggregate.add_argument("--skill-path")
    aggregate.add_argument("--model")
    aggregate.add_argument("--grader-model")
    aggregate.add_argument("--baseline-from", help="Source iteration directory for explicit compatible baseline reuse.")
    aggregate.add_argument("--baseline-config", default="without_skill", help="Config label to reuse from --baseline-from.")
    aggregate.add_argument("--output", help="benchmark.json path or output directory.")
    aggregate.set_defaults(func=command_aggregate)

    report = subcommands.add_parser("report", help="Write a static review.html file. Does not start a server.")
    report.add_argument("iteration_dir")
    report.add_argument("--benchmark", help="Benchmark JSON path. Defaults to <iteration-dir>/benchmark.json.")
    report.add_argument("--output", help="Review HTML path. Defaults to <iteration-dir>/review.html.")
    report.add_argument("--previous-workspace", help="Previous workspace or feedback file to include.")
    report.add_argument("--previous-iteration", help="Previous iteration directory or benchmark JSON for pass-rate/output comparison.")
    report.set_defaults(func=command_report)

    doctor = subcommands.add_parser("doctor", help="Print local CLI environment checks.")
    doctor.set_defaults(func=command_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except CommandError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
