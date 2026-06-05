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
RUN_CONTRACT_VERSION = "eval-runner-v6"
RECEIPT_SCHEMA_VERSION = "eval-runner-receipt-v1"
GRADING_AUDIT_STATUSES = ("clean", "warning", "error", "opted-out", "not-applicable")
METRIC_AUDIT_STATUSES = ("clean", "warning", "error", "opted-out", "not-applicable")
GRADER_MATERIAL_PENDING = "pending"
GRADER_MATERIAL_READY = "ready"
AGENT_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
USAGE_FIELD_MAP = {
    "duration_ms": "duration_ms",
    "duration_seconds": "duration_seconds",
    "total_duration_seconds": "total_duration_seconds",
    "executor_duration_seconds": "executor_duration_seconds",
    "total_tokens": "total_tokens",
    "output_chars": "output_chars",
    "tool_uses": "total_tool_calls",
    "total_tool_calls": "total_tool_calls",
}
DURATION_KEYS = ("duration_ms", "duration_seconds", "total_duration_seconds", "executor_duration_seconds")
SECOND_DURATION_KEYS = ("total_duration_seconds", "duration_seconds", "executor_duration_seconds")
KNOWN_PLACEHOLDER_METRICS = (
    {
        "id": "placeholder-30000ms-5000tokens",
        "duration_seconds": 30.0,
        "total_tokens": 5000,
        "display": "30000ms/5000 tokens",
    },
    {
        "id": "placeholder-60000ms-15000tokens",
        "duration_seconds": 60.0,
        "total_tokens": 15000,
        "display": "60000ms/15000 tokens",
    },
)


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


def build_executor_metadata(suite: EvalSuite, case: EvalCase, eval_fingerprint: str) -> dict[str, Any]:
    return {
        "schema_version": "eval-runner-executor-metadata-v1",
        "run_contract_version": RUN_CONTRACT_VERSION,
        "eval_id": case.eval_id,
        "eval_name": case.name,
        "project_class": case.project_class,
        "archetype": case.archetype,
        "prompt": case.prompt,
        "files": case.files,
        "fixtures": fixture_fingerprint_entries(suite, case),
        "eval_fingerprint": eval_fingerprint,
    }


def build_grader_metadata(
    suite: EvalSuite,
    case: EvalCase,
    eval_fingerprint: str,
    fingerprint_inputs: dict[str, Any],
) -> dict[str, Any]:
    return {
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


def build_prepare_signature(
    *,
    agent: str,
    configs: list[str],
    runs: int,
    model: str | None,
    grader_model: str | None,
    eval_fingerprints: dict[str, str],
) -> dict[str, Any]:
    return {
        "agent": agent,
        "configs": configs,
        "runs": runs,
        "model": model,
        "grader_model": grader_model,
        "run_contract_version": RUN_CONTRACT_VERSION,
        "eval_fingerprints": eval_fingerprints,
    }


def load_previous_prepare_signature(iteration_dir: Path) -> dict[str, Any]:
    parse_iteration_context(iteration_dir)
    manifest_path = iteration_dir / "iteration_manifest.json"
    if not manifest_path.exists():
        raise CommandError(f"{iteration_dir}: missing iteration_manifest.json for --rerun-of comparison")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise CommandError(f"{manifest_path}: expected object")
    eval_fingerprints: dict[str, str] = {}
    manifest_fingerprints = manifest.get("eval_fingerprints")
    if isinstance(manifest_fingerprints, dict) and all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in manifest_fingerprints.items()
    ):
        eval_fingerprints = dict(manifest_fingerprints)
    else:
        for eval_dir in sorted(path for path in iteration_dir.iterdir() if path.is_dir() and path.name.startswith("eval-")):
            metadata = read_eval_metadata(eval_dir)
            eval_id = metadata.get("eval_id")
            eval_fingerprint = metadata.get("eval_fingerprint")
            if isinstance(eval_id, str) and isinstance(eval_fingerprint, str):
                eval_fingerprints[eval_id] = eval_fingerprint
    return {
        "agent": manifest.get("agent"),
        "configs": manifest.get("configs"),
        "runs": manifest.get("runs"),
        "model": manifest.get("model"),
        "grader_model": manifest.get("grader_model"),
        "run_contract_version": manifest.get("run_contract_version"),
        "eval_fingerprints": eval_fingerprints,
    }


def compare_prepare_signatures(current: dict[str, Any], previous: dict[str, Any]) -> list[str]:
    differences: list[str] = []
    labels = {
        "agent": "agent",
        "configs": "configs",
        "runs": "run count",
        "model": "executor model",
        "grader_model": "grader model",
        "run_contract_version": "run contract",
    }
    for key, label in labels.items():
        if current.get(key) != previous.get(key):
            differences.append(f"{label}: previous {previous.get(key)!r} != current {current.get(key)!r}")

    current_fingerprints = current.get("eval_fingerprints") if isinstance(current.get("eval_fingerprints"), dict) else {}
    previous_fingerprints = previous.get("eval_fingerprints") if isinstance(previous.get("eval_fingerprints"), dict) else {}
    current_ids = set(current_fingerprints)
    previous_ids = set(previous_fingerprints)
    missing = sorted(previous_ids - current_ids)
    added = sorted(current_ids - previous_ids)
    if missing:
        differences.append(f"evals removed from rerun: {', '.join(missing)}")
    if added:
        differences.append(f"evals added to rerun: {', '.join(added)}")
    for eval_id in sorted(current_ids & previous_ids):
        if current_fingerprints.get(eval_id) != previous_fingerprints.get(eval_id):
            differences.append(f"{eval_id}: eval fingerprint changed")
    return differences


def default_evals_json_for_iteration(iteration_dir: Path) -> Path | None:
    resolved_parts = iteration_dir.resolve().parts
    if len(resolved_parts) >= 4 and resolved_parts[-3] == "workspace":
        candidate = iteration_dir.parents[2] / "evals.json"
        if candidate.exists():
            return candidate
    return None


def prepare_grading_command_for_run(run_dir: Path) -> str:
    evals_json_arg = " --evals-json <evals.json>"
    if len(run_dir.parents) >= 3 and default_evals_json_for_iteration(run_dir.parents[2]) is not None:
        evals_json_arg = ""
    return f"python3 scripts/eval_runner.py prepare-grading {run_dir}{evals_json_arg}"


def build_run_index(root: Path, iteration_manifest: dict[str, Any], manifests: list[dict[str, Any]]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for manifest in manifests:
        record_command = (
            "python3 scripts/eval_runner.py record "
            f"{manifest['run_dir']} --outputs <outputs-dir> --total-tokens <N> "
            "--duration-ms <N> --output-chars <N>"
        )
        receipt_payload = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "run_dir": manifest["run_dir"],
            "prompt_sha256": manifest.get("prompt_sha256"),
            "run_fingerprint": manifest.get("run_fingerprint"),
        }
        grader_material_status = str(manifest.get("grader_material_status") or GRADER_MATERIAL_READY)
        grader_prompt = manifest.get("grader_prompt") if isinstance(manifest.get("grader_prompt"), str) else None
        grading_json = str(Path(str(manifest["run_dir"])) / "grading.json")
        record_grading_command = (
            "python3 scripts/eval_runner.py record "
            f"{manifest['run_dir']} --grading <grading.json>"
        )
        entries.append(
            {
                "eval_id": manifest.get("eval_id"),
                "eval_name": manifest.get("eval_name"),
                "eval_dir": str(Path(str(manifest["run_dir"])).parents[1]),
                "configuration": manifest.get("configuration"),
                "run_number": manifest.get("run_number"),
                "run_dir": manifest.get("run_dir"),
                "prompt": manifest.get("executor_prompt"),
                "executor_metadata": manifest.get("executor_metadata"),
                "grader_material_status": grader_material_status,
                "grader_prompt": grader_prompt,
                "outputs_dir": manifest.get("outputs_dir"),
                "grading_json": grading_json,
                "receipt_json": str(Path(str(manifest["run_dir"])) / "outputs" / "run_receipt.json"),
                "receipt_payload": receipt_payload,
                "record_command": record_command,
                "prepare_grading_command": prepare_grading_command_for_run(Path(str(manifest["run_dir"]))),
                "grading_template_command": f"python3 scripts/eval_runner.py grading-template {manifest['run_dir']}",
                "record_grading_command": record_grading_command,
            }
        )
    return {
        "schema_version": "eval-runner-run-index-v1",
        "created_at": utc_now(),
        "iteration_dir": str(root),
        "agent": iteration_manifest.get("agent"),
        "skill_name": iteration_manifest.get("skill_name"),
        "selected_eval_ids": iteration_manifest.get("evals"),
        "configs": iteration_manifest.get("configs"),
        "runs_per_config": iteration_manifest.get("runs"),
        "run_count": len(entries),
        "run_contract_version": iteration_manifest.get("run_contract_version"),
        "run_entries": entries,
    }


def render_next_steps(run_index: dict[str, Any]) -> str:
    lines = [
        "# Eval Runner Next Steps",
        "",
        f"- Iteration: `{run_index['iteration_dir']}`",
        f"- Agent: `{run_index.get('agent')}`",
        f"- Run contract: `{run_index.get('run_contract_version')}`",
        "",
        "Run each executor from its `prompt.md` only. Do not reuse prompt text from a prior iteration.",
        "When a response may rely on host-visible tool, sub-agent, delegated-review, or other invocation records, attach the host- or parent-captured trace or metadata as a non-response artifact under `outputs/` before `prepare-grading`; executor-authored reconstructions, final-response prose, copied IDs, or self-reported counts are not trace evidence.",
        "After executor outputs and `outputs/run_receipt.json` exist, run `prepare-grading` before any grader pass.",
        "Record only parent-captured or usage-derived token/duration metrics. Placeholder, guessed, reused, or executor-estimated token/duration values are invalid for complete proof.",
        "If real token/duration metrics are unavailable, record the run as incomplete with the explicit missing or suspicious metric opt-out instead of inventing numbers.",
        "",
        "## Runs",
        "",
    ]
    for entry in run_index.get("run_entries", []):
        grader_ready = entry.get("grader_material_status") == GRADER_MATERIAL_READY
        lines.extend(
            [
                f"### {entry['eval_id']} / {entry['configuration']} / run-{entry['run_number']}",
                "",
                f"- Run dir: `{entry['run_dir']}`",
                f"- Prompt: `{entry['prompt']}`",
                f"- Executor metadata: `{entry['executor_metadata']}`",
                f"- Grader materials: `{entry['grader_material_status']}`",
                f"- Outputs dir: `{entry['outputs_dir']}`",
                f"- Receipt path: `{entry['receipt_json']}`",
                f"- Record executor metrics/output command: `{entry['record_command']}`",
                f"- Prepare grading command: `{entry['prepare_grading_command']}`",
                "- Receipt payload:",
                "",
                "```json",
                json.dumps(entry["receipt_payload"], indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )
        if grader_ready:
            lines.extend(
                [
                    f"- Grader prompt: `{entry['grader_prompt']}`",
                    f"- Grading template command: `{entry['grading_template_command']}`",
                    f"- Record grading command: `{entry['record_grading_command']}`",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def render_run_prompt(
    suite: EvalSuite,
    case: EvalCase,
    config: str,
    run_number: int,
    run_dir: Path,
    skill_path: str | None,
    agent: str,
) -> str:
    lines = ["# Eval Run Prompt", ""]
    if config == "with_skill":
        lines.append(f"- Skill: `{suite.skill_name}`")
    lines.extend(
        [
            f"- Agent: `{agent}`",
            f"- Eval id: `{case.eval_id}`",
            f"- Eval name: {case.name}",
            f"- Configuration: `{config}`",
            f"- Run: `{run_number}`",
            f"- Output directory: `{run_dir / 'outputs'}`",
        ]
    )
    if config == "with_skill" and skill_path:
        lines.append(f"- Skill path: `{skill_path}`")
    lines.extend(["", "## Configuration Contract", ""])
    if config == "without_skill":
        lines.append("Do not use any skill package or local skill file for this run. Use only the base agent behavior and the prompt below.")
    elif config == "with_skill":
        lines.append("Use the target skill through the invoking agent's normal skill mechanism for this run.")
    else:
        lines.append("Use the behavior implied by this configuration label. Do not assume a provider-specific adapter.")
    lines.extend(["", "## User Prompt", "", case.prompt.strip(), ""])
    if case.files:
        lines.extend(["## Fixture Files", ""])
        lines.extend(f"- `{file_name}`" for file_name in case.files)
        lines.append("")
    lines.extend(
        [
            "## Recording Contract",
            "",
            f"- Save run artifacts under `{run_dir / 'outputs'}`.",
            f"- Save the primary text answer at `{run_dir / 'outputs' / 'response.md'}` when the run has a text response.",
            "- When the host or parent runner exports tool, sub-agent, delegated-review, or other invocation records and the response may rely on those records, attach that host- or parent-captured trace or metadata as a non-response artifact under the output directory, such as `tool_trace.json`.",
            "- Do not create or reconstruct trace artifacts from executor memory, final-response prose, copied invocation IDs, or self-reported call counts.",
            f"- Save a prompt receipt at `{run_dir / 'outputs' / 'run_receipt.json'}` using the `schema_version`, `run_dir`, `prompt_sha256`, and `run_fingerprint` values from `run_manifest.json` or `next_steps.md`.",
            "- Do not grade this run or write `grading.json`; grading belongs to a separate grader pass.",
            "- After execution, the parent process should record captured metrics with:",
            f"  `python3 scripts/eval_runner.py record {run_dir} --total-tokens <N> --duration-ms <N> --output-chars <N>`",
            "- Parent metric flags also include `--total-duration-seconds`.",
            "- Accepted timing keys are `duration_ms`, `duration_seconds`, `total_duration_seconds`, `executor_duration_seconds`, and `total_tokens`.",
            "- The executor should not estimate tokens or duration. Placeholder, guessed, reused, or self-reported token/duration values are invalid for complete proof.",
            f"- If external artifacts exist, attach them with `python3 scripts/eval_runner.py record {run_dir} --outputs <path> --timing <timing.json>`.",
            f"- After outputs and the prompt receipt exist, prepare grader-only materials with `{prepare_grading_command_for_run(run_dir)}`.",
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
        "## Grading Boundary Rules",
        "",
        "- Grade the whole primary response, not only the intended artifact inside it.",
        "- Wrapper text, headings, Markdown fences, explanations, and meta-notes are part of the recorded output.",
        "- Do not narrow a global `Output ...` assertion to a sub-artifact unless that assertion explicitly scopes it that way.",
        "- Do not treat executor claims such as \"the real artifact would be different\" as evidence that the recorded output complies.",
        "- Treat recorded non-response artifacts as part of the output set when present; treat invocation traces as host/tool/delegation proof only when they are recorded host/runner evidence or carry parent/host provenance. Executor-authored reconstructions, final-response prose, copied invocation IDs, and self-reported call counts do not prove host/tool/delegation execution.",
        "- Requests to show, inspect, or answer in multiple parts do not automatically authorize Markdown fences or prompt-local references.",
        "- Use byte-level or parser-level checks for exact JSON, verbatim output, raw commit-message, and no-fence assertions.",
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

    current_eval_fingerprints: dict[str, str] = {}
    for eval_id in selected_ids:
        eval_fingerprint, _fingerprint_inputs = build_eval_fingerprint(suite, cases_by_id[eval_id])
        current_eval_fingerprints[eval_id] = eval_fingerprint

    workspace_root = Path(args.workspace_root) if args.workspace_root else suite.path.parent / "workspace"
    agent_root = workspace_root / agent
    number, root = iteration_path(agent_root, args.iteration)
    accepted_input_changes: list[str] = []
    if args.rerun_of:
        if args.force:
            raise CommandError("prepare --rerun-of cannot be combined with --force")
        if root.exists():
            raise CommandError(f"{root}: prepare --rerun-of requires a fresh target iteration")
        current_signature = build_prepare_signature(
            agent=agent,
            configs=configs,
            runs=args.runs,
            model=args.model,
            grader_model=args.grader_model,
            eval_fingerprints=current_eval_fingerprints,
        )
        previous_signature = load_previous_prepare_signature(Path(args.rerun_of))
        accepted_input_changes = compare_prepare_signatures(current_signature, previous_signature)
        if accepted_input_changes and not args.accept_input_changes:
            raise CommandError(
                "prepare --rerun-of input changes detected:\n"
                + "\n".join(f"- {difference}" for difference in accepted_input_changes)
                + "\nPass --accept-input-changes to prepare a new iteration with these changes recorded."
            )
    if root.exists() and not args.force:
        raise CommandError(f"{root}: iteration already exists; choose another --iteration or pass --force")
    root.mkdir(parents=True, exist_ok=True)

    used_eval_dirs: set[str] = set()
    manifests: list[dict[str, Any]] = []
    eval_slug_mapping: list[tuple[str, str]] = []
    for eval_id in selected_ids:
        case = cases_by_id[eval_id]
        eval_dir = root / unique_eval_dir_name(case, used_eval_dirs)
        eval_slug_mapping.append((eval_id, eval_dir.name))
        eval_dir.mkdir(parents=True, exist_ok=True)
        eval_fingerprint = current_eval_fingerprints[eval_id]
        executor_metadata_path = eval_dir / "executor_metadata.json"
        write_json(executor_metadata_path, build_executor_metadata(suite, case, eval_fingerprint))
        executor_metadata_sha256 = file_sha256(executor_metadata_path)

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
                    "skill_path": args.skill_path if config == "with_skill" else None,
                    "model": args.model,
                    "grader_model": args.grader_model,
                    "eval_id": case.eval_id,
                    "eval_name": case.name,
                    "configuration": config,
                    "run_number": run_number,
                    "run_dir": str(run_dir),
                    "outputs_dir": str(outputs_dir),
                    "executor_prompt": str(run_dir / "prompt.md"),
                    "executor_metadata": str(executor_metadata_path),
                    "grader_prompt": None,
                    "grader_metadata": None,
                    "eval_metadata": None,
                    "grader_material_status": GRADER_MATERIAL_PENDING,
                    "run_contract_version": RUN_CONTRACT_VERSION,
                    "eval_fingerprint": eval_fingerprint,
                    "run_fingerprint": run_fingerprint,
                    "run_fingerprint_inputs": run_inputs,
                    "executor_visible_files": [
                        str(run_dir / "prompt.md"),
                        str(run_dir / "run_manifest.json"),
                        str(outputs_dir),
                        str(executor_metadata_path),
                    ],
                }
                prompt = render_run_prompt(suite, case, config, run_number, run_dir, args.skill_path, agent)
                write_text(run_dir / "prompt.md", prompt)
                manifest["prompt_sha256"] = file_sha256(run_dir / "prompt.md")
                manifest["executor_metadata_sha256"] = executor_metadata_sha256
                write_json(run_dir / "run_manifest.json", manifest)
                manifests.append(manifest)

    iteration_manifest = {
        "created_at": utc_now(),
        "agent": agent,
        "skill_name": suite.skill_name,
        "iteration": number,
        "configs": configs,
        "runs": args.runs,
        "evals": selected_ids,
        "run_count": len(manifests),
        "model": args.model,
        "grader_model": args.grader_model,
        "run_contract_version": RUN_CONTRACT_VERSION,
        "eval_fingerprints": current_eval_fingerprints,
    }
    if args.rerun_of:
        iteration_manifest["rerun_of"] = str(Path(args.rerun_of))
        iteration_manifest["accepted_input_changes"] = accepted_input_changes
    write_json(root / "iteration_manifest.json", iteration_manifest)
    run_index = build_run_index(root, iteration_manifest, manifests)
    write_json(root / "run_index.json", run_index)
    write_text(root / "next_steps.md", render_next_steps(run_index))
    print(f"prepared: {root}")
    print(f"runs: {len(manifests)}")
    if eval_slug_mapping:
        print("evals:")
        for eval_id, slug in eval_slug_mapping:
            print(f"  {eval_id}: {slug}")
    return 0


def iteration_dir_for_run(run_dir: Path, manifest: dict[str, Any] | None = None) -> Path:
    manifest = manifest if isinstance(manifest, dict) else load_json_if_exists(run_dir / "run_manifest.json")
    if isinstance(manifest, dict) and isinstance(manifest.get("iteration_dir"), str):
        return Path(manifest["iteration_dir"])
    if len(run_dir.parents) >= 3:
        return run_dir.parents[2]
    raise CommandError(f"{run_dir}: cannot determine iteration directory")


def load_iteration_manifest(iteration_dir: Path) -> dict[str, Any]:
    manifest_path = iteration_dir / "iteration_manifest.json"
    data = read_json(manifest_path)
    if not isinstance(data, dict):
        raise CommandError(f"{manifest_path}: expected object")
    return data


def load_suite_for_iteration(iteration_dir: Path, evals_json: str | None = None) -> EvalSuite:
    if evals_json:
        return load_eval_suite(Path(evals_json))
    iteration_manifest = load_iteration_manifest(iteration_dir)
    source = iteration_manifest.get("source_evals_json")
    if not isinstance(source, str) or not source:
        default_source = default_evals_json_for_iteration(iteration_dir)
        if default_source is not None:
            return load_eval_suite(default_source)
        raise CommandError(
            f"{iteration_dir}: cannot determine evals.json for grading materials; "
            "pass --evals-json <path> to prepare-grading"
        )
    return load_eval_suite(Path(source))


def manifests_for_iteration(iteration_dir: Path) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for run_dir in discover_prepared_run_dirs(iteration_dir):
        manifest = load_json_if_exists(run_dir / "run_manifest.json")
        if isinstance(manifest, dict):
            manifests.append(manifest)
    return manifests


def refresh_iteration_operator_files(iteration_dir: Path) -> None:
    iteration_manifest = load_iteration_manifest(iteration_dir)
    run_index = build_run_index(iteration_dir, iteration_manifest, manifests_for_iteration(iteration_dir))
    write_json(iteration_dir / "run_index.json", run_index)
    write_text(iteration_dir / "next_steps.md", render_next_steps(run_index))


def grading_materials_missing_message(run_dir: Path) -> str:
    return (
        f"{run_dir}: grading materials are not prepared; run "
        f"`python3 scripts/eval_runner.py prepare-grading {run_dir}` after executor outputs and "
        "`outputs/run_receipt.json` exist"
    )


def current_run_requires_grading_materials(run_dir: Path, manifest: dict[str, Any]) -> bool:
    return is_current_run(manifest) and manifest.get("grader_material_status") != GRADER_MATERIAL_READY


def validate_prepare_grading_preconditions(run_dirs: list[Path], allow_missing_receipt: bool) -> list[str]:
    errors: list[str] = []
    for run_dir in run_dirs:
        manifest = load_run_manifest(run_dir)
        if not is_current_run(manifest):
            errors.append(
                f"{run_dir}: prepare-grading only supports {RUN_CONTRACT_VERSION} runs; "
                "legacy workspaces already contain their grading materials"
            )
            continue
        if manifest.get("grader_material_status") == GRADER_MATERIAL_READY:
            continue
        if not allow_missing_receipt:
            receipt_errors = validate_prompt_receipt(run_dir, manifest)
            if receipt_errors:
                errors.append(
                    f"{run_dir}: executor receipt is required before preparing grader materials:\n"
                    + "\n".join(f"  - {error}" for error in receipt_errors)
                )
    return errors


def write_grading_materials_for_run(run_dir: Path, suite: EvalSuite) -> None:
    manifest = load_run_manifest(run_dir)
    cases_by_id = {case.eval_id: case for case in suite.evals}
    eval_id = manifest.get("eval_id")
    if not isinstance(eval_id, str) or eval_id not in cases_by_id:
        raise CommandError(f"{run_dir}: eval id {eval_id!r} is not present in {suite.path}")
    case = cases_by_id[eval_id]
    eval_fingerprint, fingerprint_inputs = build_eval_fingerprint(suite, case)
    if manifest.get("eval_fingerprint") != eval_fingerprint:
        raise CommandError(
            f"{run_dir}: eval fingerprint changed since prepare; rerun prepare instead of preparing grader materials"
        )

    eval_dir = run_dir.parents[1]
    metadata_path = eval_dir / "eval_metadata.json"
    write_json(metadata_path, build_grader_metadata(suite, case, eval_fingerprint, fingerprint_inputs))
    grader_prompt_path = run_dir / "grader_prompt.md"
    write_text(
        grader_prompt_path,
        render_grader_prompt(
            suite,
            case,
            str(manifest.get("configuration") or ""),
            int(manifest.get("run_number") or parse_run_number(run_dir)),
            run_dir,
            str(manifest.get("agent") or ""),
        ),
    )

    manifest.update(
        {
            "grader_prompt": str(grader_prompt_path),
            "grader_metadata": str(metadata_path),
            "eval_metadata": str(metadata_path),
            "grader_material_status": GRADER_MATERIAL_READY,
            "grader_prompt_sha256": file_sha256(grader_prompt_path),
            "eval_metadata_sha256": file_sha256(metadata_path),
            "grader_material_files": [
                str(grader_prompt_path),
                str(metadata_path),
            ],
        }
    )
    write_json(run_dir / "run_manifest.json", manifest)


def command_prepare_grading(args: argparse.Namespace) -> int:
    target = Path(args.target)
    if not target.exists():
        raise CommandError(f"{target}: target does not exist")
    if (target / "run_manifest.json").exists():
        run_dirs = [target]
        iteration_dir = iteration_dir_for_run(target)
    else:
        parse_iteration_context(target)
        iteration_dir = target
        run_dirs = discover_prepared_run_dirs(iteration_dir)
    if not run_dirs:
        raise CommandError(f"{target}: no prepared run directories found")

    precondition_errors = validate_prepare_grading_preconditions(run_dirs, args.allow_missing_receipt)
    if precondition_errors:
        raise CommandError("prepare-grading preconditions failed:\n" + "\n".join(f"- {error}" for error in precondition_errors))

    suite = load_suite_for_iteration(iteration_dir, args.evals_json)
    for run_dir in run_dirs:
        write_grading_materials_for_run(run_dir, suite)
    refresh_iteration_operator_files(iteration_dir)
    print(f"prepared_grading: {target}")
    print(f"runs: {len(run_dirs)}")
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
        if isinstance(manifest, dict):
            if is_current_run(manifest):
                if manifest.get("grader_material_status") != GRADER_MATERIAL_READY:
                    return None
                for key in ("grader_metadata", "eval_metadata"):
                    if isinstance(manifest.get(key), str):
                        return Path(manifest[key])
                return None
            for key in ("grader_metadata", "eval_metadata"):
                if isinstance(manifest.get(key), str):
                    return Path(manifest[key])
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
        f"expected {len(expected_assertions)} item(s), found {len(actual_texts)}. "
        "Do not hand-edit assertion text; regenerate from grader_prompt.md or "
        "`python3 scripts/eval_runner.py grading-template <run-dir>`."
    ]
    max_len = max(len(expected_assertions), len(actual_texts))
    for index in range(max_len):
        expected = expected_assertions[index] if index < len(expected_assertions) else None
        actual = actual_texts[index] if index < len(actual_texts) else None
        if expected != actual:
            errors.append(f"{source}.expectations[{index}].text: expected {expected!r}, got {actual!r}")
    return errors


CONVENTIONAL_COMMIT_SUBJECT_RE = re.compile(
    r"(?m)^\s*(build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\([^)]+\))?!?:\s+\S"
)
MARKDOWN_FENCE_RE = re.compile(r"```[^\n]*\n?(.*?)```", re.DOTALL)
PROMPT_LOCAL_ERROR_PHRASES = (
    "the fenced block above",
    "this eval",
    "this prompt",
)
PROMPT_LOCAL_WARNING_PHRASES = (
    "the provided text",
    "as requested",
)
BOUNDARY_NARROWING_PHRASES = (
    "the committed artifact",
    "inside the fence",
    "outside the artifact",
    "outside the code block",
    "does not count",
    "would be raw",
    "real command would",
    "real commit",
)


def grading_expectations(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("expectations"), list):
        return []
    return [item for item in data["expectations"] if isinstance(item, dict)]


def read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def auditable_output_files(outputs_dir: Path) -> list[Path]:
    if not outputs_dir.is_dir():
        return []
    return sorted(
        path
        for path in outputs_dir.rglob("*")
        if path.is_file() and path.name != "run_receipt.json"
    )


def audit_output_bundle(outputs_dir: Path) -> dict[str, Any]:
    files = auditable_output_files(outputs_dir)
    text_files: list[dict[str, str]] = []
    primary_response: str | None = None
    for path in files:
        text = read_text_or_none(path)
        if text is None:
            continue
        rel_path = str(path.relative_to(outputs_dir))
        text_files.append({"path": rel_path, "text": text})
        if rel_path == "response.md":
            primary_response = text
    combined_text = primary_response
    if combined_text is None and text_files:
        combined_text = "\n\n".join(f"# {item['path']}\n{item['text']}" for item in text_files)
    return {
        "files": [str(path.relative_to(outputs_dir)) for path in files],
        "text_files": text_files,
        "primary_response": primary_response,
        "combined_text": combined_text,
    }


def markdown_fence_blocks(text: str) -> list[str]:
    return [match.group(1) for match in MARKDOWN_FENCE_RE.finditer(text)]


def has_markdown_fence(text: str | None) -> bool:
    return bool(text and "```" in text)


def fenced_conventional_commit_blocks(text: str | None) -> list[str]:
    if not text:
        return []
    return [block for block in markdown_fence_blocks(text) if CONVENTIONAL_COMMIT_SUBJECT_RE.search(block.strip())]


def prose_without_fences_or_quotes(text: str) -> str:
    without_fences = MARKDOWN_FENCE_RE.sub("", text)
    lines = [line for line in without_fences.splitlines() if not line.lstrip().startswith(">")]
    return "\n".join(lines)


def audit_snippet(text: str, needle: str | None = None, max_chars: int = 180) -> str:
    if not text:
        return ""
    start = 0
    if needle:
        index = text.lower().find(needle.lower())
        if index >= 0:
            start = max(0, index - 40)
    snippet = text[start : start + max_chars].replace("\n", "\\n")
    if start > 0:
        snippet = "..." + snippet
    if start + max_chars < len(text):
        snippet += "..."
    return snippet


def assertion_has_no_fence_contract(assertion: str) -> bool:
    lower = assertion.lower()
    return any(
        phrase in lower
        for phrase in (
            "does not wrap",
            "do not wrap",
            "no markdown fence",
            "no markdown code fence",
            "without markdown fence",
            "without a markdown fence",
            "not wrapped in markdown",
        )
    )


def assertion_has_raw_commit_contract(assertion: str) -> bool:
    lower = assertion.lower()
    return (
        "commit message" in lower
        and (
            "raw" in lower
            or assertion_has_no_fence_contract(assertion)
            or "plain text" in lower
            or "standalone conventional commit" in lower
        )
    )


def prompt_has_raw_commit_contract(prompt: str) -> bool:
    lower = prompt.lower()
    return "commit message" in lower and any(
        phrase in lower
        for phrase in (
            "raw",
            "plain text",
            "no markdown",
            "without markdown",
            "do not wrap",
            "don't wrap",
        )
    )


def prompt_explicitly_allows_fenced_commit(prompt: str) -> bool:
    lower = prompt.lower()
    if "commit message" not in lower:
        return False
    if "no markdown" in lower or "without markdown" in lower or "do not wrap" in lower:
        return False
    return "fenced" in lower or "markdown fence" in lower or "code block" in lower


def assertion_is_standalone_contract(assertion: str) -> bool:
    lower = assertion.lower()
    return any(
        phrase in lower
        for phrase in (
            "standalone",
            "stands alone",
            "self-contained",
            "prompt-only",
            "without relying on the prompt",
            "without prompt context",
        )
    )


def assertion_is_json_only_contract(assertion: str) -> bool:
    lower = assertion.lower()
    return "json" in lower and any(
        phrase in lower
        for phrase in (
            "valid json only",
            "json only",
            "exact json",
            "machine-readable",
            "no surrounding prose",
            "without surrounding prose",
            "nothing but json",
        )
    )


def assertion_is_verbatim_no_wrapper_contract(assertion: str) -> bool:
    lower = assertion.lower()
    exactish = "verbatim" in lower or "exact output" in lower or "exactly" in lower
    wrapperless = any(
        phrase in lower
        for phrase in (
            "no wrapper",
            "without wrapper",
            "does not wrap",
            "no surrounding prose",
            "without surrounding prose",
            "raw text",
            "no markdown",
        )
    )
    return exactish and wrapperless


def assertion_is_file_artifact_claim(assertion: str) -> bool:
    lower = assertion.lower()
    return bool(re.search(r"\b(file|artifact|path)\b", lower)) and any(
        phrase in lower
        for phrase in (
            "exists",
            "created",
            "written",
            "changed",
            "modified",
            "produced",
            "no extra",
            "only the",
        )
    )


def response_has_obvious_wrapper(text: str | None) -> bool:
    if not text:
        return False
    stripped_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not stripped_lines:
        return False
    first = stripped_lines[0].lower()
    return (
        first.startswith("#")
        or first.startswith("here is")
        or first.startswith("here's")
        or first.startswith("as requested")
        or first.startswith("the requested")
        or has_markdown_fence(text)
    )


def add_audit_finding(
    findings: list[dict[str, Any]],
    *,
    severity: str,
    rule_id: str,
    assertion_index: int,
    assertion_text: str,
    message: str,
    evidence: str,
    recommendation: str,
) -> None:
    findings.append(
        {
            "severity": severity,
            "rule_id": rule_id,
            "assertion_index": assertion_index,
            "assertion_text": assertion_text,
            "message": message,
            "evidence": evidence,
            "recommendation": recommendation,
        }
    )


def grading_audit_status(findings: list[dict[str, Any]], *, opted_out: bool, applicable: bool) -> str:
    if opted_out:
        return "opted-out"
    if any(finding.get("severity") == "error" for finding in findings):
        return "error"
    if any(finding.get("severity") == "warning" for finding in findings):
        return "warning"
    return "clean" if applicable else "not-applicable"


def audit_grading_for_run(
    run_dir: Path,
    grading_data: dict[str, Any] | None = None,
    *,
    outputs_dir: Path | None = None,
    record_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    run_dir = Path(run_dir)
    outputs_dir = outputs_dir or run_dir / "outputs"
    record_metadata = record_metadata if isinstance(record_metadata, dict) else {}
    grading_path = run_dir / "grading.json"
    if grading_data is None:
        if not grading_path.exists():
            return {
                "status": "not-applicable",
                "opted_out": bool(record_metadata.get("allow_suspicious_grading")),
                "applicable": False,
                "errors": 0,
                "warnings": 0,
                "findings": [],
                "reason": "grading.json is missing",
            }
        loaded = read_json(grading_path)
        grading_data = loaded if isinstance(loaded, dict) else None
    expectations = grading_expectations(grading_data)
    if not expectations:
        return {
            "status": "not-applicable",
            "opted_out": bool(record_metadata.get("allow_suspicious_grading")),
            "applicable": False,
            "errors": 0,
            "warnings": 0,
            "findings": [],
            "reason": "grading expectations are missing",
        }

    metadata_path = eval_metadata_path_for_run(run_dir)
    metadata = read_json(metadata_path) if metadata_path and metadata_path.exists() else {}
    metadata = metadata if isinstance(metadata, dict) else {}
    prompt = str(metadata.get("prompt") or "")
    prompt_lower = prompt.lower()
    output_bundle = audit_output_bundle(outputs_dir)
    response_text = output_bundle.get("primary_response")
    combined_text = output_bundle.get("combined_text")
    scan_text = response_text if isinstance(response_text, str) else combined_text
    scan_text = scan_text if isinstance(scan_text, str) else None
    prose_text = prose_without_fences_or_quotes(scan_text) if scan_text is not None else ""
    output_files = output_bundle.get("files") if isinstance(output_bundle.get("files"), list) else []
    non_response_outputs = [
        path for path in output_files if path not in {"response.md", "run_receipt.json"}
    ]
    findings: list[dict[str, Any]] = []
    applicable = bool(scan_text)
    fenced_commit_blocks = fenced_conventional_commit_blocks(scan_text)

    for index, item in enumerate(expectations):
        if item.get("passed") is not True:
            continue
        assertion = item.get("text") if isinstance(item.get("text"), str) else ""
        evidence_text = item.get("evidence") if isinstance(item.get("evidence"), str) else ""
        assertion_lower = assertion.lower()
        evidence_lower = evidence_text.lower()

        if scan_text and fenced_commit_blocks and "commit message" in assertion_lower:
            raw_assertion = assertion_has_raw_commit_contract(assertion)
            raw_prompt = prompt_has_raw_commit_contract(prompt)
            if raw_assertion or raw_prompt:
                severity = "error" if raw_assertion else "warning"
                add_audit_finding(
                    findings,
                    severity=severity,
                    rule_id="raw-commit-message-fence",
                    assertion_index=index,
                    assertion_text=assertion,
                    message="A passed commit-message assertion conflicts with a Markdown-fenced Conventional Commit subject in the recorded response.",
                    evidence=audit_snippet(fenced_commit_blocks[0]),
                    recommendation="Fail the assertion unless the prompt and assertion explicitly allow a fenced commit-message example.",
                )
            elif "commit message" in prompt_lower and not prompt_explicitly_allows_fenced_commit(prompt):
                add_audit_finding(
                    findings,
                    severity="warning",
                    rule_id="raw-commit-message-fence",
                    assertion_index=index,
                    assertion_text=assertion,
                    message="The response fences a Conventional Commit-like subject even though the prompt only asks for a commit message.",
                    evidence=audit_snippet(fenced_commit_blocks[0]),
                    recommendation="Check whether the assertion should require raw commit-message output.",
                )

        if scan_text and assertion_has_no_fence_contract(assertion) and has_markdown_fence(scan_text):
            add_audit_finding(
                findings,
                severity="error",
                rule_id="no-fence-assertion-fence",
                assertion_index=index,
                assertion_text=assertion,
                message="A passed no-fence assertion conflicts with Markdown fence bytes in the recorded response.",
                evidence=audit_snippet(scan_text, "```"),
                recommendation="Fail the assertion or narrow it only if the assertion itself excludes wrapper text.",
            )

        if scan_text and assertion_is_standalone_contract(assertion):
            for phrase in PROMPT_LOCAL_ERROR_PHRASES:
                if phrase in prose_text.lower():
                    add_audit_finding(
                        findings,
                        severity="error",
                        rule_id="standalone-prompt-local-reference",
                        assertion_index=index,
                        assertion_text=assertion,
                        message=f"A passed standalone-output assertion conflicts with prompt-local phrase {phrase!r}.",
                        evidence=audit_snippet(prose_text, phrase),
                        recommendation="Fail the assertion unless the phrase is required verbatim source content.",
                    )
                    break
            else:
                for phrase in PROMPT_LOCAL_WARNING_PHRASES:
                    if phrase in prose_text.lower():
                        add_audit_finding(
                            findings,
                            severity="warning",
                            rule_id="standalone-prompt-local-reference",
                            assertion_index=index,
                            assertion_text=assertion,
                            message=f"The response contains prompt-local phrase {phrase!r} under a passed standalone-output assertion.",
                            evidence=audit_snippet(prose_text, phrase),
                            recommendation="Verify the output stands alone without prompt context.",
                        )
                        break

        if scan_text and any(phrase in evidence_lower for phrase in BOUNDARY_NARROWING_PHRASES):
            severity = "error" if has_markdown_fence(scan_text) or any(phrase in prose_text.lower() for phrase in PROMPT_LOCAL_ERROR_PHRASES) else "warning"
            add_audit_finding(
                findings,
                severity=severity,
                rule_id="evidence-boundary-narrowing",
                assertion_index=index,
                assertion_text=assertion,
                message="Grader evidence appears to narrow a passed global assertion to a sub-artifact or hypothetical artifact.",
                evidence=audit_snippet(evidence_text),
                recommendation="Regrade against the full recorded output set instead of executor intent or a selected sub-artifact.",
            )

        if scan_text and assertion_is_json_only_contract(assertion):
            stripped = scan_text.strip()
            json_error: str | None = None
            if stripped.startswith("```"):
                json_error = "response starts with a Markdown fence"
            else:
                try:
                    json.loads(stripped)
                except json.JSONDecodeError as exc:
                    json_error = f"entire stripped response is not valid JSON: {exc.msg}"
            if json_error:
                add_audit_finding(
                    findings,
                    severity="error",
                    rule_id="json-only-contract",
                    assertion_index=index,
                    assertion_text=assertion,
                    message=f"A passed JSON-only assertion conflicts with the recorded response: {json_error}.",
                    evidence=audit_snippet(scan_text),
                    recommendation="Fail the assertion unless the whole recorded response is parseable JSON with no surrounding prose or fences.",
                )

        if scan_text and assertion_is_verbatim_no_wrapper_contract(assertion) and response_has_obvious_wrapper(scan_text):
            add_audit_finding(
                findings,
                severity="error",
                rule_id="verbatim-no-wrapper",
                assertion_index=index,
                assertion_text=assertion,
                message="A passed exact/verbatim no-wrapper assertion conflicts with obvious wrapper text or Markdown fences.",
                evidence=audit_snippet(scan_text),
                recommendation="Fail the assertion unless the expected verbatim payload includes the wrapper.",
            )

        if assertion_is_file_artifact_claim(assertion):
            applicable = True
            if not non_response_outputs:
                add_audit_finding(
                    findings,
                    severity="warning",
                    rule_id="file-artifact-boundary",
                    assertion_index=index,
                    assertion_text=assertion,
                    message="A passed file/artifact assertion lacks a recorded non-response artifact to verify the claim.",
                    evidence=f"recorded output files: {', '.join(output_files) if output_files else 'none'}",
                    recommendation="Record the relevant artifact or downgrade the grading evidence to a manual/unsupported claim.",
                )

    opted_out = bool(record_metadata.get("allow_suspicious_grading"))
    errors = sum(1 for finding in findings if finding.get("severity") == "error")
    warnings = sum(1 for finding in findings if finding.get("severity") == "warning")
    return {
        "status": grading_audit_status(findings, opted_out=opted_out, applicable=applicable),
        "opted_out": opted_out,
        "applicable": applicable,
        "errors": errors,
        "warnings": warnings,
        "findings": findings,
        "output_files_checked": output_files,
    }


def grading_audit_blocking_messages(run_dir: Path, audit: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    for finding in audit.get("findings", []):
        if not isinstance(finding, dict) or finding.get("severity") != "error":
            continue
        assertion_number = int(finding.get("assertion_index", 0)) + 1
        messages.append(
            f"{run_dir}: grading audit {finding.get('rule_id')} assertion {assertion_number}: "
            f"{finding.get('message')} Evidence: {finding.get('evidence')}"
        )
    return messages


def audit_status_counts(runs: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in GRADING_AUDIT_STATUSES}
    for run in runs:
        audit = run.get("grading_audit") if isinstance(run, dict) else None
        status = audit.get("status") if isinstance(audit, dict) else "not-applicable"
        if status not in counts:
            status = "not-applicable"
        counts[str(status)] += 1
    return counts


def format_audit_counts(counts: dict[str, int] | None) -> str:
    counts = counts if isinstance(counts, dict) else {}
    return ", ".join(f"{status}={int(counts.get(status, 0))}" for status in GRADING_AUDIT_STATUSES)


def metric_audit_status(findings: list[dict[str, Any]], *, opted_out: bool, applicable: bool) -> str:
    if not applicable:
        return "not-applicable"
    if opted_out:
        return "opted-out"
    if any(finding.get("severity") == "error" for finding in findings):
        return "error"
    if any(finding.get("severity") == "warning" for finding in findings):
        return "warning"
    return "clean"


def resolve_duration_seconds(timing_data: dict[str, Any] | None) -> tuple[float | None, str | None]:
    timing_data = timing_data if isinstance(timing_data, dict) else {}
    duration_ms = first_number(timing_data.get("duration_ms"))
    if duration_ms is not None:
        return duration_ms / 1000.0, "duration_ms"
    for key in SECOND_DURATION_KEYS:
        seconds = first_number(timing_data.get(key))
        if seconds is not None:
            return seconds, key
    return None, None


def known_placeholder_metric(duration_seconds: float | None, total_tokens: float | None) -> dict[str, Any] | None:
    if duration_seconds is None or total_tokens is None:
        return None
    if duration_seconds <= 0 or total_tokens <= 0:
        return None
    for placeholder in KNOWN_PLACEHOLDER_METRICS:
        if (
            abs(duration_seconds - float(placeholder["duration_seconds"])) < 1e-9
            and abs(total_tokens - float(placeholder["total_tokens"])) < 1e-9
        ):
            return placeholder
    return None


def audit_metric_integrity(
    timing_data: dict[str, Any] | None,
    *,
    current_contract: bool,
    record_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record_metadata = record_metadata if isinstance(record_metadata, dict) else {}
    findings: list[dict[str, Any]] = []
    duration_seconds, duration_key = resolve_duration_seconds(timing_data)
    total_tokens = first_number((timing_data or {}).get("total_tokens")) if isinstance(timing_data, dict) else None
    if current_contract and duration_seconds is not None and duration_seconds <= 0:
        findings.append(
            {
                "severity": "error",
                "rule_id": "non-positive-duration",
                "message": f"Resolved duration from {duration_key} must be greater than zero for complete proof.",
                "evidence": f"{duration_key} resolved to {format_number(duration_seconds)} seconds",
            }
        )
    if current_contract and total_tokens is not None and total_tokens <= 0:
        findings.append(
            {
                "severity": "error",
                "rule_id": "non-positive-total-tokens",
                "message": "total_tokens must be greater than zero for complete proof.",
                "evidence": f"total_tokens={format_number(total_tokens, digits=0)}",
            }
        )
    placeholder = known_placeholder_metric(duration_seconds, total_tokens)
    if current_contract and placeholder is not None:
        findings.append(
            {
                "severity": "warning",
                "rule_id": "known-placeholder-metrics",
                "placeholder_id": placeholder["id"],
                "display": placeholder["display"],
                "duration_seconds": placeholder["duration_seconds"],
                "total_tokens": placeholder["total_tokens"],
                "message": f"Metrics match the known placeholder pair {placeholder['display']}.",
                "evidence": f"duration={format_number(duration_seconds)}s, total_tokens={format_number(total_tokens, digits=0)}",
            }
        )
    errors = sum(1 for finding in findings if finding.get("severity") == "error")
    warnings = sum(1 for finding in findings if finding.get("severity") == "warning")
    opted_out = bool(record_metadata.get("allow_suspicious_metrics"))
    return {
        "status": metric_audit_status(findings, opted_out=opted_out, applicable=current_contract),
        "opted_out": opted_out,
        "applicable": current_contract,
        "errors": errors,
        "warnings": warnings,
        "duration_seconds": duration_seconds,
        "duration_source": duration_key,
        "total_tokens": total_tokens,
        "findings": findings,
    }


def metric_audit_blocking_messages(run_dir: Path, audit: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    for finding in audit.get("findings", []):
        if not isinstance(finding, dict) or finding.get("severity") != "error":
            continue
        messages.append(
            f"{run_dir}: metric audit {finding.get('rule_id')}: "
            f"{finding.get('message')} Evidence: {finding.get('evidence')}"
        )
    return messages


def metric_audit_status_counts(runs: list[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in METRIC_AUDIT_STATUSES}
    for run in runs:
        audit = run.get("metrics_audit") if isinstance(run, dict) else None
        status = audit.get("status") if isinstance(audit, dict) else "not-applicable"
        if status not in counts:
            status = "not-applicable"
        counts[str(status)] += 1
    return counts


def format_metric_audit_counts(counts: dict[str, int] | None) -> str:
    counts = counts if isinstance(counts, dict) else {}
    return ", ".join(f"{status}={int(counts.get(status, 0))}" for status in METRIC_AUDIT_STATUSES)


def repeated_known_placeholder_metric_reasons(
    items: list[dict[str, Any]],
    label_for_item: Callable[[dict[str, Any]], str],
) -> list[str]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in items:
        if item.get("run_contract_version") != RUN_CONTRACT_VERSION:
            continue
        audit = item.get("metrics_audit") if isinstance(item.get("metrics_audit"), dict) else {}
        for finding in audit.get("findings", []):
            if not isinstance(finding, dict) or finding.get("rule_id") != "known-placeholder-metrics":
                continue
            placeholder_id = str(finding.get("placeholder_id") or finding.get("display") or "known-placeholder")
            group = grouped.setdefault(
                placeholder_id,
                {
                    "display": finding.get("display") or placeholder_id,
                    "labels": [],
                },
            )
            group["labels"].append(label_for_item(item))
    reasons: list[str] = []
    for group in grouped.values():
        labels = group["labels"]
        if len(labels) > 1:
            reasons.append(
                f"repeated known placeholder metrics {group['display']} for {len(labels)} current-contract run(s): {', '.join(labels[:5])}"
            )
    return reasons


def load_timing_data(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise CommandError(f"{path}: expected timing object")
    return data


def normalize_metric_value(key: str, value: Any, source: Path | str) -> int | float:
    if isinstance(value, bool):
        raise CommandError(f"{source}: {key} must be numeric, got boolean")
    if not isinstance(value, (int, float)):
        raise CommandError(f"{source}: {key} must be numeric")
    if value < 0:
        raise CommandError(f"{source}: {key} must be non-negative")
    if key in {"duration_seconds", "total_duration_seconds", "executor_duration_seconds"}:
        return float(value)
    return int(value)


def parse_usage_data(data: Any, source: Path | str) -> dict[str, int | float]:
    if not isinstance(data, dict):
        raise CommandError(f"{source}: expected usage object")
    metrics: dict[str, int | float] = {}
    for raw_key, target_key in USAGE_FIELD_MAP.items():
        if raw_key not in data:
            continue
        metrics[target_key] = normalize_metric_value(target_key, data[raw_key], source)
    return metrics


def parse_usage_text(text: str, source: Path | str) -> dict[str, int | float]:
    stripped = text.strip()
    if not stripped:
        return {}
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if parsed is not None:
        return parse_usage_data(parsed, source)

    metrics: dict[str, int | float] = {}
    for raw_key, target_key in USAGE_FIELD_MAP.items():
        pattern = re.compile(rf"\b{re.escape(raw_key)}\b\s*[:=]\s*([^,\s<>]+)")
        for match in pattern.finditer(text):
            raw_value = match.group(1)
            try:
                value = float(raw_value) if "." in raw_value else int(raw_value)
            except ValueError as exc:
                raise CommandError(f"{source}: {raw_key} must be numeric") from exc
            metrics[target_key] = normalize_metric_value(target_key, value, source)
    return metrics


def usage_inputs_to_timing(args: argparse.Namespace) -> dict[str, int | float]:
    metrics: dict[str, int | float] = {}
    if getattr(args, "usage_file", None):
        usage_path = Path(args.usage_file)
        if not usage_path.exists():
            raise CommandError(f"{usage_path}: usage file does not exist")
        metrics.update(parse_usage_text(usage_path.read_text(encoding="utf-8"), usage_path))
    if getattr(args, "usage_text", None):
        metrics.update(parse_usage_text(str(args.usage_text), "--usage-text"))
    return metrics


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


def timing_metrics_for_record(args: argparse.Namespace) -> dict[str, int | float]:
    timing_metrics = usage_inputs_to_timing(args)
    timing_metrics.update(metric_flags_to_timing(args))
    return timing_metrics


def load_run_manifest(run_dir: Path) -> dict[str, Any]:
    manifest = read_json(run_dir / "run_manifest.json")
    if not isinstance(manifest, dict):
        raise CommandError(f"{run_dir / 'run_manifest.json'}: expected object")
    return manifest


def is_current_run(manifest: dict[str, Any]) -> bool:
    return manifest.get("run_contract_version") == RUN_CONTRACT_VERSION


def normalized_path_string(path: Path) -> str:
    try:
        return str(path.resolve())
    except OSError:
        return str(path)


def validate_prompt_receipt(run_dir: Path, manifest: dict[str, Any]) -> list[str]:
    receipt_path = run_dir / "outputs" / "run_receipt.json"
    if not receipt_path.exists():
        return [f"{receipt_path}: missing prompt receipt"]
    try:
        receipt = read_json(receipt_path)
    except CommandError as exc:
        return [str(exc)]
    if not isinstance(receipt, dict):
        return [f"{receipt_path}: expected receipt object"]
    errors: list[str] = []
    if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        errors.append(f"{receipt_path}.schema_version: expected {RECEIPT_SCHEMA_VERSION!r}, got {receipt.get('schema_version')!r}")
    if receipt.get("prompt_sha256") != manifest.get("prompt_sha256"):
        errors.append(f"{receipt_path}.prompt_sha256: expected {manifest.get('prompt_sha256')!r}, got {receipt.get('prompt_sha256')!r}")
    if receipt.get("run_fingerprint") != manifest.get("run_fingerprint"):
        errors.append(f"{receipt_path}.run_fingerprint: expected {manifest.get('run_fingerprint')!r}, got {receipt.get('run_fingerprint')!r}")
    receipt_run_dir = receipt.get("run_dir")
    if receipt_run_dir is not None and normalized_path_string(Path(str(receipt_run_dir))) != normalized_path_string(run_dir):
        errors.append(f"{receipt_path}.run_dir: expected {run_dir}, got {receipt_run_dir!r}")
    return errors


def ensure_output_chars_from_response(run_dir: Path, timing_data: dict[str, Any] | None) -> dict[str, Any] | None:
    if timing_data is not None and isinstance(timing_data.get("output_chars"), (int, float)) and not isinstance(timing_data.get("output_chars"), bool):
        return timing_data
    response_path = run_dir / "outputs" / "response.md"
    if not response_path.exists():
        return timing_data
    text = response_path.read_text(encoding="utf-8")
    if timing_data is None:
        timing_data = {}
    timing_data["output_chars"] = len(text)
    write_json(run_dir / "timing.json", timing_data)
    return timing_data


def final_metric_errors(timing_data: dict[str, Any] | None) -> list[str]:
    timing_data = timing_data if isinstance(timing_data, dict) else {}
    errors: list[str] = []
    has_duration = any(first_number(timing_data.get(key)) is not None for key in DURATION_KEYS)
    if not has_duration:
        errors.append("missing duration metric: duration_ms, duration_seconds, total_duration_seconds, or executor_duration_seconds")
    if first_number(timing_data.get("total_tokens")) is None:
        errors.append("missing total_tokens")
    if first_number(timing_data.get("output_chars")) is None:
        errors.append("missing output_chars")
    return errors


def write_record_metadata(
    run_dir: Path,
    *,
    finalized: bool,
    allow_missing_prompt_receipt: bool,
    allow_missing_metrics: bool,
    allow_suspicious_grading: bool,
    allow_suspicious_metrics: bool,
    missing_metrics: list[str],
    grading_audit: dict[str, Any] | None = None,
    metrics_audit: dict[str, Any] | None = None,
) -> None:
    existing = load_json_if_exists(run_dir / "record_metadata.json")
    metadata = existing if isinstance(existing, dict) else {}
    existing_allow_suspicious = bool(metadata.get("allow_suspicious_grading"))
    existing_allow_suspicious_metrics = bool(metadata.get("allow_suspicious_metrics"))
    metadata.update(
        {
            "updated_at": utc_now(),
            "finalized": bool(finalized or metadata.get("finalized")),
            "allow_missing_prompt_receipt": bool(allow_missing_prompt_receipt or metadata.get("allow_missing_prompt_receipt")),
            "allow_missing_metrics": bool(allow_missing_metrics or metadata.get("allow_missing_metrics")),
            "allow_suspicious_grading": bool(allow_suspicious_grading or existing_allow_suspicious),
            "allow_suspicious_metrics": bool(allow_suspicious_metrics or existing_allow_suspicious_metrics),
            "missing_metrics": missing_metrics,
            "noncanonical": bool(
                allow_missing_prompt_receipt
                or allow_missing_metrics
                or allow_suspicious_grading
                or allow_suspicious_metrics
                or metadata.get("allow_missing_prompt_receipt")
                or metadata.get("allow_missing_metrics")
                or existing_allow_suspicious
                or existing_allow_suspicious_metrics
            ),
        }
    )
    if grading_audit is not None:
        metadata["grading_audit"] = {
            "status": grading_audit.get("status"),
            "errors": grading_audit.get("errors", 0),
            "warnings": grading_audit.get("warnings", 0),
        }
    if metrics_audit is not None:
        metadata["metrics_audit"] = {
            "status": metrics_audit.get("status"),
            "errors": metrics_audit.get("errors", 0),
            "warnings": metrics_audit.get("warnings", 0),
            "findings": metrics_audit.get("findings", []),
        }
    write_json(run_dir / "record_metadata.json", metadata)


def command_record(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        raise CommandError(f"{run_dir}: run directory does not exist")
    if not (run_dir / "run_manifest.json").exists():
        raise CommandError(f"{run_dir}: missing run_manifest.json; run prepare first")
    manifest = load_run_manifest(run_dir)

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

    timing_destination = run_dir / "timing.json"
    finalizing = bool(args.finalize or args.grading)
    timing_data, timing_changed = candidate_timing_for_record(run_dir, args, autofill_output_chars=finalizing)
    if timing_changed and not finalizing and timing_data is not None:
        write_json(timing_destination, timing_data)

    grading_data: dict[str, Any] | None = None
    grading_destination = run_dir / "grading.json"
    grading_source_path: Path | None = None
    if args.grading:
        grading_path = Path(args.grading)
        if not grading_path.exists():
            raise CommandError(f"{grading_path}: grading file does not exist")
        expected_assertions = load_expected_assertions_for_run(run_dir)
        if is_current_run(manifest) and expected_assertions is None:
            raise CommandError(grading_materials_missing_message(run_dir))
        grading_source_path = grading_path
        raw_grading_data = read_json(grading_path)
        grading_data = raw_grading_data if isinstance(raw_grading_data, dict) else None
        grading_errors = validate_grading_data(grading_data, grading_path)
        grading_errors.extend(
            validate_grading_completeness(
                grading_data,
                expected_assertions,
                grading_path,
            )
        )
        if grading_errors:
            raise CommandError("\n".join(grading_errors))

    missing_metrics: list[str] = []
    grading_audit: dict[str, Any] | None = None
    metrics_audit: dict[str, Any] | None = None
    if finalizing:
        record_metadata = load_json_if_exists(run_dir / "record_metadata.json")
        record_metadata = record_metadata if isinstance(record_metadata, dict) else {}
        if args.allow_suspicious_grading:
            record_metadata = dict(record_metadata)
            record_metadata["allow_suspicious_grading"] = True
        if args.allow_suspicious_metrics:
            record_metadata = dict(record_metadata)
            record_metadata["allow_suspicious_metrics"] = True
        if grading_data is None and grading_destination.exists():
            expected_assertions = load_expected_assertions_for_run(run_dir)
            if is_current_run(manifest) and expected_assertions is None:
                raise CommandError(grading_materials_missing_message(run_dir))
            existing_grading = read_json(grading_destination)
            grading_data = existing_grading if isinstance(existing_grading, dict) else None
            grading_errors = validate_grading_data(grading_data, grading_destination)
            grading_errors.extend(
                validate_grading_completeness(
                    grading_data,
                    expected_assertions,
                    grading_destination,
                )
            )
            if grading_errors:
                raise CommandError("\n".join(grading_errors))
        if grading_data is not None:
            grading_audit = audit_grading_for_run(run_dir, grading_data, record_metadata=record_metadata)
            audit_blockers = grading_audit_blocking_messages(run_dir, grading_audit)
            if audit_blockers and is_current_run(manifest) and not args.allow_suspicious_grading:
                raise CommandError(
                    "record finalization found suspicious grading:\n"
                    + "\n".join(f"- {message}" for message in audit_blockers)
                    + "\nPass --allow-suspicious-grading only for legacy/manual smoke runs."
                )
        receipt_errors: list[str] = []
        if is_current_run(manifest):
            receipt_errors = validate_prompt_receipt(run_dir, manifest)
        if receipt_errors and not args.allow_missing_prompt_receipt:
            raise CommandError("\n".join(receipt_errors) + "\nPass --allow-missing-prompt-receipt only for legacy/manual smoke runs.")
        missing_metrics = final_metric_errors(timing_data)
        if missing_metrics and not args.allow_missing_metrics:
            raise CommandError(
                "record finalization missing required metrics:\n"
                + "\n".join(f"- {error}" for error in missing_metrics)
                + "\nPass --allow-missing-metrics only for partial or smoke runs."
            )
        metrics_audit = audit_metric_integrity(
            timing_data,
            current_contract=is_current_run(manifest),
            record_metadata=record_metadata,
        )
        metric_blockers = metric_audit_blocking_messages(run_dir, metrics_audit)
        if metric_blockers and is_current_run(manifest) and not args.allow_suspicious_metrics:
            raise CommandError(
                "record finalization found invalid or suspicious metrics:\n"
                + "\n".join(f"- {message}" for message in metric_blockers)
                + "\nPass --allow-suspicious-metrics only for legacy/manual smoke runs with present-but-invalid metrics."
            )
    if finalizing and timing_changed and timing_data is not None:
        write_json(timing_destination, timing_data)
    if grading_data is not None and grading_source_path is not None and not paths_are_same_file(grading_source_path, grading_destination):
        write_json(grading_destination, grading_data)
    write_record_metadata(
        run_dir,
        finalized=finalizing,
        allow_missing_prompt_receipt=bool(finalizing and args.allow_missing_prompt_receipt),
        allow_missing_metrics=bool(finalizing and args.allow_missing_metrics),
        allow_suspicious_grading=bool(finalizing and args.allow_suspicious_grading),
        allow_suspicious_metrics=bool(finalizing and args.allow_suspicious_metrics),
        missing_metrics=missing_metrics,
        grading_audit=grading_audit,
        metrics_audit=metrics_audit,
    )
    print(f"recorded: {run_dir}")
    return 0


def command_grading_template(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        raise CommandError(f"{run_dir}: run directory does not exist")
    assertions = load_expected_assertions_for_run(run_dir)
    if assertions is None:
        manifest = load_json_if_exists(run_dir / "run_manifest.json")
        if isinstance(manifest, dict) and is_current_run(manifest):
            raise CommandError(grading_materials_missing_message(run_dir))
        raise CommandError(f"{run_dir}: cannot find eval_metadata.json.assertions")
    template = {
        "expectations": [
            {
                "text": assertion,
                "passed": None,
                "evidence": "",
            }
            for assertion in assertions
        ]
    }
    output = Path(args.output) if args.output else run_dir / "grading-template.json"
    write_json(output, template)
    print(f"grading_template: {output}")
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


def parse_tool_call_count(value: Any, source: Path | str, key: str) -> int:
    if isinstance(value, bool):
        raise CommandError(f"{source}: {key} must be a non-negative integer, got boolean")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, float) and value.is_integer():
        parsed = int(value)
    else:
        raise CommandError(f"{source}: {key} must be a non-negative integer")
    if parsed < 0:
        raise CommandError(f"{source}: {key} must be a non-negative integer")
    return parsed


def sum_tool_call_count_map(values: dict[str, Any], source: Path | str, key: str) -> int:
    return sum(parse_tool_call_count(value, source, f"{key}.{name}") for name, value in values.items())


def extract_tool_calls_from_outputs(outputs_dir: Path) -> int | None:
    trace_path = outputs_dir / "tool_trace.json"
    if not trace_path.exists():
        return None
    trace = load_json_if_exists(trace_path)
    if not isinstance(trace, dict):
        return None
    for key in ("total_tool_calls", "tool_call_count", "invocation_count", "delegated_invocation_count"):
        if key in trace:
            return parse_tool_call_count(trace[key], trace_path, key)
    tool_calls = trace.get("tool_calls")
    if isinstance(tool_calls, list):
        return len(tool_calls)
    if isinstance(tool_calls, dict):
        return sum_tool_call_count_map(tool_calls, trace_path, "tool_calls")
    for key in ("tool_invocations", "invocations", "delegated_invocations", "delegated_reviews"):
        if key in trace:
            invocations = trace[key]
            if not isinstance(invocations, list):
                raise CommandError(f"{trace_path}: {key} must be a list when used for tool-call fallback")
            return len(invocations)
    return None


def extract_tool_calls(grading: dict[str, Any], timing: dict[str, Any] | None, outputs_dir: Path | None = None) -> int | None:
    timing = timing if isinstance(timing, dict) else {}
    if "total_tool_calls" in timing:
        return parse_tool_call_count(timing["total_tool_calls"], "timing.json", "total_tool_calls")
    metrics = grading.get("execution_metrics") if isinstance(grading.get("execution_metrics"), dict) else {}
    if "total_tool_calls" in metrics:
        return parse_tool_call_count(metrics["total_tool_calls"], "grading.json execution_metrics", "total_tool_calls")
    tool_calls = metrics.get("tool_calls")
    if isinstance(tool_calls, dict):
        return sum_tool_call_count_map(tool_calls, "grading.json execution_metrics", "tool_calls")
    if outputs_dir is not None:
        return extract_tool_calls_from_outputs(outputs_dir)
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
                        load_expected_assertions_for_run(run_dir),
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
                    "tool_calls": extract_tool_calls(
                        grading,
                        timing if isinstance(timing, dict) else None,
                        outputs_dir if outputs_dir.exists() else None,
                    ),
                    "errors": extract_errors(grading),
                }
                record_metadata = load_json_if_exists(run_dir / "record_metadata.json")
                record_metadata = record_metadata if isinstance(record_metadata, dict) else {}
                metrics_audit = audit_metric_integrity(
                    timing if isinstance(timing, dict) else None,
                    current_contract=is_current_run(manifest),
                    record_metadata=record_metadata,
                )
                grading_audit = audit_grading_for_run(
                    run_dir,
                    grading,
                    outputs_dir=outputs_dir,
                    record_metadata=record_metadata,
                )
                receipt_errors = validate_prompt_receipt(run_dir, manifest) if is_current_run(manifest) else []
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
                        "grading_audit": grading_audit,
                        "metrics_audit": metrics_audit,
                        "reused": False,
                        "run_contract_version": manifest.get("run_contract_version"),
                        "record_metadata": record_metadata,
                        "prompt_receipt_status": "valid" if is_current_run(manifest) and not receipt_errors else ("not-required" if not is_current_run(manifest) else "missing-or-invalid"),
                        "prompt_receipt_errors": receipt_errors,
                        "prompt_receipt_opt_out": bool(record_metadata.get("allow_missing_prompt_receipt")),
                        "metrics_opt_out": bool(record_metadata.get("allow_missing_metrics")),
                        "metrics_audit_opt_out": bool(record_metadata.get("allow_suspicious_metrics")),
                        "grading_audit_opt_out": bool(record_metadata.get("allow_suspicious_grading")),
                        "grader_material_status": manifest.get("grader_material_status"),
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
    if isinstance(source_run.get("grading_audit"), dict):
        reused["grading_audit"] = json.loads(json.dumps(source_run["grading_audit"]))
    if isinstance(source_run.get("metrics_audit"), dict):
        reused["metrics_audit"] = json.loads(json.dumps(source_run["metrics_audit"]))
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
    current_contract = current_run.get("run_contract_version")
    source_contract = source_run.get("run_contract_version")
    if current_contract != source_contract:
        errors.append(f"{source_label} run contract mismatch: source {source_contract!r} != current {current_contract!r}")
    if current_contract != RUN_CONTRACT_VERSION:
        errors.append(
            f"{current_label} baseline reuse for run contract {current_contract!r} is unsupported by this runner; "
            f"current contract is {RUN_CONTRACT_VERSION!r}"
        )
        return errors
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
    failed_evidence: dict[tuple[str, int, str, str], list[str]] = {}
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
        for index, expectation in enumerate(run.get("expectations", [])):
            if not isinstance(expectation, dict) or not isinstance(expectation.get("text"), str):
                continue
            passed = expectation.get("passed")
            if not isinstance(passed, bool):
                continue
            text = expectation["text"]
            by_expectation.setdefault((eval_id, text), {}).setdefault(config, []).append(passed)
            repeated_expectations.setdefault((eval_id, config, text), []).append(passed)
            evidence = expectation.get("evidence")
            if passed is False and isinstance(evidence, str) and evidence.strip():
                failed_evidence.setdefault((eval_id, index, text, evidence.strip()), []).append(
                    f"{config} run-{run.get('run_number')}"
                )

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

    for (eval_id, index, text, evidence), occurrences in sorted(failed_evidence.items()):
        if len(occurrences) > 1:
            notes.append(
                {
                    "kind": "systematic_failure_suspected",
                    "eval_id": eval_id,
                    "assertion_index": index,
                    "expectation": text,
                    "evidence": evidence,
                    "occurrences": occurrences,
                    "message": "Repeated identical failed evidence may indicate a prompt/config/input mismatch before rerun: "
                    f"{eval_id} assertion {index + 1} `{text}` failed in {', '.join(occurrences)}. "
                    "Compare current and previous eval_metadata.json, prompt.md, and config labels.",
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

    metric_tuple_groups: dict[tuple[float, int], list[str]] = {}
    for run in runs:
        if run.get("run_contract_version") != RUN_CONTRACT_VERSION:
            continue
        result = run.get("result", {})
        result = result if isinstance(result, dict) else {}
        seconds = result.get("time_seconds")
        tokens = result.get("tokens")
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
            continue
        if not isinstance(tokens, (int, float)) or isinstance(tokens, bool):
            continue
        if seconds <= 0 or tokens <= 0:
            continue
        key = (round(float(seconds), 9), int(tokens))
        metric_tuple_groups.setdefault(key, []).append(
            f"{run.get('eval_id')} `{run.get('configuration')}` run-{run.get('run_number')}"
        )
    for (seconds, tokens), labels in sorted(metric_tuple_groups.items()):
        if len(labels) <= 1:
            continue
        placeholder = known_placeholder_metric(seconds, tokens)
        if placeholder is not None:
            notes.append(
                {
                    "kind": "known_placeholder_metric_repetition",
                    "duration_seconds": seconds,
                    "total_tokens": tokens,
                    "runs": labels,
                    "message": f"Repeated known placeholder metrics {placeholder['display']}: {', '.join(labels[:5])}.",
                }
            )
        else:
            notes.append(
                {
                    "kind": "repeated_metric_tuple",
                    "duration_seconds": seconds,
                    "total_tokens": tokens,
                    "runs": labels,
                    "message": f"Repeated identical metric tuple {format_number(seconds)}s/{tokens} tokens: {', '.join(labels[:5])}. Verify the metrics are parent-captured, not reused placeholders.",
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
    prepared_incomplete_reasons: list[str] | None = None,
) -> dict[str, Any]:
    context = parse_iteration_context(iteration_dir)
    baseline_reuse_errors = baseline_reuse_errors or []
    prepared_incomplete_reasons = prepared_incomplete_reasons or []
    if not runs:
        incomplete_reasons = ["no graded runs found", *baseline_reuse_errors, *prepared_incomplete_reasons]
        if not allow_incomplete:
            raise CommandError(
                "incomplete benchmark: "
                + "; ".join(incomplete_reasons)
                + "; pass --allow-incomplete for a smoke/incomplete aggregate"
            )
        metadata: dict[str, Any] = {
            "timestamp": utc_now(),
            "iteration_dir": str(iteration_dir),
            "agent": context.agent,
            "skill_name": skill_name or context.skill_name or derive_skill_name(iteration_dir),
            "configs": [],
            "evals_run": [],
            "runs_per_configuration": {},
            "incomplete": True,
            "smoke": True,
            "incomplete_reasons": incomplete_reasons,
            "allow_incomplete": allow_incomplete,
            "legacy_layout_allowed": allow_legacy,
            "baseline_from": baseline_from,
            "baseline_config": baseline_config,
            "baseline_reuse_errors": baseline_reuse_errors,
            "baseline_reused_runs": 0,
            "grading_audit": audit_status_counts([]),
            "metrics_audit": metric_audit_status_counts([]),
        }
        if skill_path:
            metadata["skill_path"] = skill_path
        if model:
            metadata["executor_model"] = model
        if grader_model:
            metadata["grader_model"] = grader_model
        return {
            "metadata": metadata,
            "configs": {},
            "comparisons": [],
            "analysis": {"notes": []},
            "runs": [],
        }

    configs = sorted({run["configuration"] for run in runs}, key=config_sort_key)
    counts = {config: sum(1 for run in runs if run["configuration"] == config) for config in configs}
    incomplete_reasons: list[str] = []
    incomplete_reasons.extend(baseline_reuse_errors)
    incomplete_reasons.extend(prepared_incomplete_reasons)
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
    missing_output_chars = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION and run["result"].get("output_chars") is None
    ]
    if missing_output_chars:
        incomplete_reasons.append(f"missing output_chars for {len(missing_output_chars)} current-contract run(s): {', '.join(missing_output_chars[:5])}")
    missing_receipts = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION and run.get("prompt_receipt_status") != "valid"
    ]
    if missing_receipts:
        incomplete_reasons.append(f"missing or invalid prompt receipt for {len(missing_receipts)} current-contract run(s): {', '.join(missing_receipts[:5])}")
    receipt_opt_outs = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION and run.get("prompt_receipt_opt_out")
    ]
    if receipt_opt_outs:
        incomplete_reasons.append(f"prompt receipt opt-out for {len(receipt_opt_outs)} current-contract run(s): {', '.join(receipt_opt_outs[:5])}")
    metric_opt_outs = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION and run.get("metrics_opt_out")
    ]
    if metric_opt_outs:
        incomplete_reasons.append(f"missing-metrics opt-out for {len(metric_opt_outs)} current-contract run(s): {', '.join(metric_opt_outs[:5])}")
    metric_audit_errors = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION
        and isinstance(run.get("metrics_audit"), dict)
        and run["metrics_audit"].get("status") == "error"
    ]
    if metric_audit_errors:
        incomplete_reasons.append(f"metric integrity error for {len(metric_audit_errors)} current-contract run(s): {', '.join(metric_audit_errors[:5])}")
    metric_audit_opt_outs = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION
        and (
            run.get("metrics_audit_opt_out")
            or (
                isinstance(run.get("metrics_audit"), dict)
                and run["metrics_audit"].get("status") == "opted-out"
            )
        )
    ]
    if metric_audit_opt_outs:
        incomplete_reasons.append(f"suspicious-metrics opt-out for {len(metric_audit_opt_outs)} current-contract run(s): {', '.join(metric_audit_opt_outs[:5])}")
    incomplete_reasons.extend(
        repeated_known_placeholder_metric_reasons(
            runs,
            lambda run: f"{run['eval_id']} {run['configuration']} run-{run['run_number']}",
        )
    )
    audit_errors = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION
        and isinstance(run.get("grading_audit"), dict)
        and run["grading_audit"].get("status") == "error"
    ]
    if audit_errors:
        incomplete_reasons.append(f"grading audit error for {len(audit_errors)} current-contract run(s): {', '.join(audit_errors[:5])}")
    audit_opt_outs = [
        f"{run['eval_id']} {run['configuration']} run-{run['run_number']}"
        for run in runs
        if run.get("run_contract_version") == RUN_CONTRACT_VERSION
        and (
            run.get("grading_audit_opt_out")
            or (
                isinstance(run.get("grading_audit"), dict)
                and run["grading_audit"].get("status") == "opted-out"
            )
        )
    ]
    if audit_opt_outs:
        incomplete_reasons.append(f"suspicious-grading opt-out for {len(audit_opt_outs)} current-contract run(s): {', '.join(audit_opt_outs[:5])}")

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
            "grading_audit": audit_status_counts(config_runs),
            "metrics_audit": metric_audit_status_counts(config_runs),
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
        "grading_audit": audit_status_counts(runs),
        "metrics_audit": metric_audit_status_counts(runs),
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
        "| Config | Runs | Reused | Mean pass rate | Total time | Mean tokens | Total tokens | Output chars | Tool calls | Failed expectations | Errors | Grading audit | Metric integrity |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for config, stats in benchmark["configs"].items():
        lines.append(
            "| {config} | {runs} | {reused} | {pass_rate} | {time_total} | {tokens_mean} | {tokens_total} | {output_chars} | {tool_calls} | {failed}/{total_expectations} | {errors} | {audit} | {metric_audit} |".format(
                config=config,
                runs=stats["runs"],
                reused=stats.get("reused_runs", 0),
                pass_rate=format_percent(stats["pass_rate"]["mean"]),
                time_total=format_number(stats["time_seconds"].get("total")),
                tokens_mean=format_number(stats["tokens"]["mean"], digits=0),
                tokens_total=format_number(stats["tokens"].get("total"), digits=0),
                output_chars=format_number(stats.get("output_chars", {}).get("total"), digits=0),
                tool_calls=format_number(stats.get("tool_calls", {}).get("total"), digits=0),
                failed=stats.get("failed_expectations_total", 0),
                total_expectations=stats.get("total_expectations", 0),
                errors=stats["errors_total"],
                audit=format_audit_counts(stats.get("grading_audit")),
                metric_audit=format_metric_audit_counts(stats.get("metrics_audit")),
            )
        )

    lines.extend(["", "## Grading Audit", ""])
    lines.append(f"- Overall: {format_audit_counts(metadata.get('grading_audit'))}")
    audit_findings = [
        (run, finding)
        for run in benchmark["runs"]
        if isinstance(run.get("grading_audit"), dict)
        for finding in run["grading_audit"].get("findings", [])
        if isinstance(finding, dict)
    ]
    if audit_findings:
        for run, finding in audit_findings:
            lines.append(
                "- {severity} `{rule}` in {eval_id} `{config}` run-{run_number} assertion {assertion}: {message}".format(
                    severity=finding.get("severity"),
                    rule=finding.get("rule_id"),
                    eval_id=run.get("eval_id"),
                    config=run.get("configuration"),
                    run_number=run.get("run_number"),
                    assertion=int(finding.get("assertion_index", 0)) + 1,
                    message=finding.get("message"),
                )
            )
    else:
        lines.append("- No grading audit findings.")

    lines.extend(["", "## Metric Integrity", ""])
    lines.append(f"- Overall: {format_metric_audit_counts(metadata.get('metrics_audit'))}")
    metric_findings = [
        (run, finding)
        for run in benchmark["runs"]
        if isinstance(run.get("metrics_audit"), dict)
        for finding in run["metrics_audit"].get("findings", [])
        if isinstance(finding, dict)
    ]
    if metric_findings:
        for run, finding in metric_findings:
            lines.append(
                "- {severity} `{rule}` in {eval_id} `{config}` run-{run_number}: {message}".format(
                    severity=finding.get("severity"),
                    rule=finding.get("rule_id"),
                    eval_id=run.get("eval_id"),
                    config=run.get("configuration"),
                    run_number=run.get("run_number"),
                    message=finding.get("message"),
                )
            )
    else:
        lines.append("- No metric-integrity findings.")

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
            "| Eval | Config | Run | Reused | Pass rate | Time | Tokens | Output chars | Tool calls | Audit | Metric integrity | Layout |",
            "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
        ]
    )
    for run in benchmark["runs"]:
        result = run["result"]
        lines.append(
            "| {eval_id} | {config} | {run_number} | {reused} | {pass_rate} | {time} | {tokens} | {output_chars} | {tool_calls} | {audit} | {metric_audit} | {layout} |".format(
                eval_id=run["eval_id"],
                config=run["configuration"],
                run_number=run["run_number"],
                reused="yes" if run.get("reused") else "no",
                pass_rate=format_percent(result.get("pass_rate")),
                time=format_number(result.get("time_seconds")),
                tokens=format_number(result.get("tokens"), digits=0),
                output_chars=format_number(result.get("output_chars"), digits=0),
                tool_calls=format_number(result.get("tool_calls"), digits=0),
                audit=(run.get("grading_audit") if isinstance(run.get("grading_audit"), dict) else {}).get("status", "not-applicable"),
                metric_audit=(run.get("metrics_audit") if isinstance(run.get("metrics_audit"), dict) else {}).get("status", "not-applicable"),
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


def summarize_prepared_incomplete_reasons(iteration_dir: Path) -> list[str]:
    run_dirs = discover_prepared_run_dirs(iteration_dir)
    if not run_dirs:
        return []
    statuses = [inspect_prepared_run(run_dir) for run_dir in run_dirs]
    missing_materials = [
        f"{Path(status['run_dir']).parents[1].name} {Path(status['run_dir']).parents[0].name} {Path(status['run_dir']).name}"
        for status in statuses
        if status.get("run_contract_version") == RUN_CONTRACT_VERSION
        and status.get("grader_material_status") != GRADER_MATERIAL_READY
    ]
    missing_grading = [
        f"{Path(status['run_dir']).parents[1].name} {Path(status['run_dir']).parents[0].name} {Path(status['run_dir']).name}"
        for status in statuses
        if status.get("run_contract_version") == RUN_CONTRACT_VERSION
        and status.get("grader_material_status") == GRADER_MATERIAL_READY
        and status.get("grading") == "missing"
    ]
    reasons: list[str] = []
    if missing_materials:
        reasons.append(
            f"missing grading materials for {len(missing_materials)} current-contract run(s): {', '.join(missing_materials[:5])}"
        )
    if missing_grading:
        reasons.append(
            f"missing grading output for {len(missing_grading)} current-contract run(s): {', '.join(missing_grading[:5])}"
        )
    return reasons


def command_aggregate(args: argparse.Namespace) -> int:
    iteration_dir = Path(args.iteration_dir)
    current_context = parse_iteration_context(iteration_dir)
    runs = discover_runs(iteration_dir, args.allow_legacy)
    prepared_incomplete_reasons = summarize_prepared_incomplete_reasons(iteration_dir)
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
        prepared_incomplete_reasons=prepared_incomplete_reasons,
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


def resolve_auto_previous_iteration(iteration_dir: Path) -> Path:
    context = parse_iteration_context(iteration_dir)
    if context.iteration <= 1:
        raise CommandError(f"{iteration_dir}: --previous-iteration auto has no previous iteration before iteration-{context.iteration}")
    previous = iteration_dir.parent / f"iteration-{context.iteration - 1}"
    if not previous.exists():
        raise CommandError(f"{previous}: previous iteration for --previous-iteration auto does not exist")
    if not (previous / "benchmark.json").exists():
        raise CommandError(f"{previous / 'benchmark.json'}: previous benchmark missing for --previous-iteration auto")
    return previous


def validate_previous_benchmark_compatibility(current: dict[str, Any] | None, previous: dict[str, Any] | None) -> list[str]:
    if not current or not previous:
        return []
    previous_lookup = previous_runs_by_key(previous)
    errors: list[str] = []
    for run in current.get("runs", []):
        if not isinstance(run, dict):
            continue
        try:
            key = (str(run.get("eval_id")), str(run.get("configuration")), int(run.get("run_number")))
        except (TypeError, ValueError):
            continue
        previous_run = previous_lookup.get(key)
        if not previous_run:
            continue
        current_eval_fingerprint = run.get("eval_fingerprint")
        previous_eval_fingerprint = previous_run.get("eval_fingerprint")
        if current_eval_fingerprint and previous_eval_fingerprint and current_eval_fingerprint != previous_eval_fingerprint:
            errors.append(f"{key[0]} {key[1]} run-{key[2]} eval fingerprint mismatch")
        current_contract = run.get("run_contract_version")
        previous_contract = previous_run.get("run_contract_version")
        if current_contract and previous_contract and current_contract != previous_contract:
            errors.append(f"{key[0]} {key[1]} run-{key[2]} run contract mismatch")
    return errors


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


def previous_expectations_by_key(previous_benchmark: dict[str, Any] | None) -> dict[tuple[str, str, int, int, str], dict[str, Any]]:
    if not previous_benchmark:
        return {}
    result: dict[tuple[str, str, int, int, str], dict[str, Any]] = {}
    for run in previous_benchmark.get("runs", []):
        if not isinstance(run, dict):
            continue
        try:
            eval_id = str(run.get("eval_id"))
            config = str(run.get("configuration"))
            run_number = int(run.get("run_number"))
        except (TypeError, ValueError):
            continue
        for index, expectation in enumerate(run.get("expectations", [])):
            if not isinstance(expectation, dict) or not isinstance(expectation.get("text"), str):
                continue
            result[(eval_id, config, run_number, index, expectation["text"])] = expectation
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
    previous_expectation_lookup = previous_expectations_by_key(previous_benchmark)
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
                f"<p>Grading audit: <code>{html.escape(format_audit_counts(metadata.get('grading_audit')))}</code></p>",
                f"<p>Metric integrity: <code>{html.escape(format_metric_audit_counts(metadata.get('metrics_audit')))}</code></p>",
                "<table><thead><tr><th>Config</th><th>Runs</th><th>Reused</th><th>Mean pass rate</th><th>Total time</th><th>Mean tokens</th><th>Total tokens</th><th>Output chars</th><th>Tool calls</th><th>Failed expectations</th><th>Grading audit</th><th>Metric integrity</th></tr></thead><tbody>",
            ]
        )
        for config, stats in benchmark["configs"].items():
            parts.append(
                "<tr><td><code>{}</code></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}/{}</td><td>{}</td><td>{}</td></tr>".format(
                    html.escape(config),
                    stats["runs"],
                    stats.get("reused_runs", 0),
                    html.escape(format_percent(stats["pass_rate"]["mean"])),
                    html.escape(format_number(stats["time_seconds"].get("total"))),
                    html.escape(format_number(stats["tokens"]["mean"], digits=0)),
                    html.escape(format_number(stats["tokens"].get("total"), digits=0)),
                    html.escape(format_number(stats.get("output_chars", {}).get("total"), digits=0)),
                    html.escape(format_number(stats.get("tool_calls", {}).get("total"), digits=0)),
                    stats.get("failed_expectations_total", 0),
                    stats.get("total_expectations", 0),
                    html.escape(format_audit_counts(stats.get("grading_audit"))),
                    html.escape(format_metric_audit_counts(stats.get("metrics_audit"))),
                )
            )
        parts.extend(["</tbody></table>", "</section>"])

        incomplete_reasons = metadata.get("incomplete_reasons") if isinstance(metadata.get("incomplete_reasons"), list) else []
        if incomplete_reasons:
            parts.extend(["<section>", "<h2>Incomplete Reasons</h2>", "<ul>"])
            for reason in incomplete_reasons:
                parts.append(f"<li>{html.escape(str(reason))}</li>")
            parts.extend(["</ul>", "</section>"])

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
                    f"output chars: {html.escape(format_number(result.get('output_chars'), digits=0))}; "
                    f"tool calls: {html.escape(format_number(result.get('tool_calls'), digits=0))}</p>",
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
            audit = run.get("grading_audit") if isinstance(run.get("grading_audit"), dict) else {}
            parts.extend(["<h4>Grading Audit</h4>"])
            parts.append(
                "<p>Status: <code>{}</code>; errors: {}; warnings: {}; opted out: <code>{}</code></p>".format(
                    html.escape(str(audit.get("status", "not-applicable"))),
                    html.escape(str(audit.get("errors", 0))),
                    html.escape(str(audit.get("warnings", 0))),
                    html.escape(str(bool(audit.get("opted_out"))).lower()),
                )
            )
            findings = audit.get("findings") if isinstance(audit.get("findings"), list) else []
            if findings:
                parts.append("<ul>")
                for finding in findings:
                    if not isinstance(finding, dict):
                        continue
                    parts.append(
                        "<li><strong>{}</strong> <code>{}</code> assertion {}: {}<br><span class=\"muted\">{}</span></li>".format(
                            html.escape(str(finding.get("severity", ""))),
                            html.escape(str(finding.get("rule_id", ""))),
                            html.escape(str(int(finding.get("assertion_index", 0)) + 1)),
                            html.escape(str(finding.get("message", ""))),
                            html.escape(str(finding.get("evidence", ""))),
                        )
                    )
                parts.append("</ul>")
            else:
                parts.append('<p class="muted">No grading audit findings.</p>')
            metric_audit = run.get("metrics_audit") if isinstance(run.get("metrics_audit"), dict) else {}
            parts.extend(["<h4>Metric Integrity</h4>"])
            parts.append(
                "<p>Status: <code>{}</code>; errors: {}; warnings: {}; opted out: <code>{}</code></p>".format(
                    html.escape(str(metric_audit.get("status", "not-applicable"))),
                    html.escape(str(metric_audit.get("errors", 0))),
                    html.escape(str(metric_audit.get("warnings", 0))),
                    html.escape(str(bool(metric_audit.get("opted_out"))).lower()),
                )
            )
            metric_findings = metric_audit.get("findings") if isinstance(metric_audit.get("findings"), list) else []
            if metric_findings:
                parts.append("<ul>")
                for finding in metric_findings:
                    if not isinstance(finding, dict):
                        continue
                    parts.append(
                        "<li><strong>{}</strong> <code>{}</code>: {}<br><span class=\"muted\">{}</span></li>".format(
                            html.escape(str(finding.get("severity", ""))),
                            html.escape(str(finding.get("rule_id", ""))),
                            html.escape(str(finding.get("message", ""))),
                            html.escape(str(finding.get("evidence", ""))),
                        )
                    )
                parts.append("</ul>")
            else:
                parts.append('<p class="muted">No metric-integrity findings.</p>')
            parts.extend(["<h4>Grades</h4>", "<table><thead><tr><th>Status</th><th>Expectation</th><th>Evidence</th><th>Previous</th></tr></thead><tbody>"])
            for index, expectation in enumerate(run.get("expectations", [])):
                if not isinstance(expectation, dict):
                    continue
                passed = expectation.get("passed") is True
                status = "pass" if passed else "fail"
                previous_expectation = previous_expectation_lookup.get(
                    (
                        str(run["eval_id"]),
                        str(run["configuration"]),
                        int(run["run_number"]),
                        index,
                        str(expectation.get("text", "")),
                    )
                )
                previous_cell = "n/a"
                if isinstance(previous_expectation, dict):
                    previous_status = "pass" if previous_expectation.get("passed") is True else "fail"
                    previous_cell = f"{previous_status}: {previous_expectation.get('evidence', '')}"
                parts.append(
                    '<tr><td class="{status}">{label}</td><td>{text}</td><td>{evidence}</td><td>{previous}</td></tr>'.format(
                        status=status,
                        label="pass" if passed else "fail",
                        text=html.escape(str(expectation.get("text", ""))),
                        evidence=html.escape(str(expectation.get("evidence", ""))),
                        previous=html.escape(previous_cell),
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


def timing_data_for_benchmark_run(run: dict[str, Any]) -> dict[str, Any] | None:
    run_dir_value = run.get("run_dir")
    if isinstance(run_dir_value, str):
        timing_path = Path(run_dir_value) / "timing.json"
        timing = load_json_if_exists(timing_path)
        if isinstance(timing, dict):
            return timing
    result = run.get("result") if isinstance(run.get("result"), dict) else {}
    timing: dict[str, Any] = {}
    if isinstance(result.get("time_seconds"), (int, float)) and not isinstance(result.get("time_seconds"), bool):
        timing["total_duration_seconds"] = result["time_seconds"]
    if isinstance(result.get("tokens"), (int, float)) and not isinstance(result.get("tokens"), bool):
        timing["total_tokens"] = result["tokens"]
    if isinstance(result.get("output_chars"), (int, float)) and not isinstance(result.get("output_chars"), bool):
        timing["output_chars"] = result["output_chars"]
    return timing or None


def benchmark_with_metric_audit(benchmark: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(benchmark, dict):
        return benchmark
    updated = json.loads(json.dumps(benchmark))
    runs = updated.get("runs") if isinstance(updated.get("runs"), list) else []
    for run in runs:
        if not isinstance(run, dict) or isinstance(run.get("metrics_audit"), dict):
            continue
        run_dir_value = run.get("run_dir")
        record_metadata = {}
        if isinstance(run_dir_value, str):
            loaded_metadata = load_json_if_exists(Path(run_dir_value) / "record_metadata.json")
            record_metadata = loaded_metadata if isinstance(loaded_metadata, dict) else {}
        timing = timing_data_for_benchmark_run(run)
        current_contract = run.get("run_contract_version") == RUN_CONTRACT_VERSION
        if timing is None and current_contract:
            run["metrics_audit"] = {
                "status": "warning",
                "opted_out": False,
                "applicable": True,
                "errors": 0,
                "warnings": 1,
                "findings": [
                    {
                        "severity": "warning",
                        "rule_id": "metric-audit-unverified",
                        "message": "Metric integrity could not be re-audited from benchmark data or timing.json.",
                        "evidence": f"run_dir={run_dir_value!r}",
                    }
                ],
            }
        else:
            run["metrics_audit"] = audit_metric_integrity(
                timing,
                current_contract=current_contract,
                record_metadata=record_metadata,
            )
        run["metrics_audit_opt_out"] = bool(record_metadata.get("allow_suspicious_metrics"))
    metadata = updated.get("metadata") if isinstance(updated.get("metadata"), dict) else {}
    metadata["metrics_audit"] = metric_audit_status_counts([run for run in runs if isinstance(run, dict)])
    reasons = metadata.get("incomplete_reasons") if isinstance(metadata.get("incomplete_reasons"), list) else []
    reasons = list(reasons)
    if not any("repeated known placeholder metrics" in str(reason) for reason in reasons):
        reasons.extend(
            repeated_known_placeholder_metric_reasons(
                [run for run in runs if isinstance(run, dict)],
                lambda run: f"{run.get('eval_id')} {run.get('configuration')} run-{run.get('run_number')}",
            )
        )
    metadata["incomplete_reasons"] = reasons
    if reasons:
        metadata["incomplete"] = True
    updated["metadata"] = metadata
    configs = updated.get("configs") if isinstance(updated.get("configs"), dict) else {}
    for config, stats in configs.items():
        if not isinstance(stats, dict):
            continue
        config_runs = [run for run in runs if isinstance(run, dict) and run.get("configuration") == config]
        stats["metrics_audit"] = metric_audit_status_counts(config_runs)
    return updated


def command_report(args: argparse.Namespace) -> int:
    iteration_dir = Path(args.iteration_dir)
    parse_iteration_context(iteration_dir)
    benchmark_path = Path(args.benchmark) if args.benchmark else iteration_dir / "benchmark.json"
    benchmark = load_json_if_exists(benchmark_path)
    if benchmark is not None and not isinstance(benchmark, dict):
        raise CommandError(f"{benchmark_path}: expected benchmark object")
    benchmark = benchmark_with_metric_audit(benchmark)
    previous_feedback = find_previous_feedback(args.previous_workspace)
    previous_iteration = args.previous_iteration
    if previous_iteration == "auto":
        previous_iteration = str(resolve_auto_previous_iteration(iteration_dir))
    previous_benchmark = load_previous_iteration_benchmark(previous_iteration)
    compatibility_errors = validate_previous_benchmark_compatibility(
        benchmark if isinstance(benchmark, dict) else None,
        previous_benchmark,
    )
    if compatibility_errors:
        raise CommandError(
            "previous iteration is incompatible for comparison:\n"
            + "\n".join(f"- {error}" for error in compatibility_errors)
        )
    output = Path(args.output) if args.output else iteration_dir / "review.html"
    write_text(output, render_report_html(iteration_dir, benchmark, previous_feedback, previous_benchmark))
    print(f"review_html: {output}")
    print("server: not started")
    return 0


def discover_prepared_run_dirs(iteration_dir: Path) -> list[Path]:
    parse_iteration_context(iteration_dir)
    result: list[Path] = []
    for eval_dir in sorted(path for path in iteration_dir.iterdir() if path.is_dir() and path.name.startswith("eval-")):
        for config_dir in sorted(path for path in eval_dir.iterdir() if path.is_dir() and not path.name.startswith(".")):
            if config_dir.name.startswith("run-") or config_dir.name == "outputs":
                continue
            result.extend(sorted(path for path in config_dir.iterdir() if path.is_dir() and path.name.startswith("run-")))
    return result


def run_phase_status(status: dict[str, Any]) -> str:
    if status.get("run_contract_version") != RUN_CONTRACT_VERSION:
        return "legacy"
    if status.get("grader_material_status") != GRADER_MATERIAL_READY:
        if status.get("prompt_receipt") == "valid":
            return "pending-grading-material"
        return "executor-prepared"
    if status.get("grading") == "valid":
        if (
            status.get("prompt_receipt") == "valid"
            and status.get("metrics") == "complete"
            and status.get("metrics_audit") not in {"error", "opted-out"}
            and status.get("grading_audit") not in {"error", "opted-out"}
        ):
            return "complete"
        return "graded"
    if status.get("grading") == "missing":
        return "grading-material-ready"
    return "incomplete"


def inspect_prepared_run(run_dir: Path) -> dict[str, Any]:
    status: dict[str, Any] = {
        "run_dir": str(run_dir),
        "errors": [],
        "blockers": [],
    }
    manifest_path = run_dir / "run_manifest.json"
    manifest = load_json_if_exists(manifest_path)
    manifest = manifest if isinstance(manifest, dict) else {}
    status["has_run_manifest"] = bool(manifest)
    status["run_contract_version"] = manifest.get("run_contract_version")
    status["grader_material_status"] = manifest.get("grader_material_status") or (
        GRADER_MATERIAL_READY if manifest.get("grader_prompt") else "legacy-or-missing"
    )
    outputs_dir = run_dir / "outputs"
    status["outputs_present"] = outputs_dir.exists() and any(outputs_dir.iterdir())
    status["primary_response"] = "present" if (outputs_dir / "response.md").exists() else "missing"
    record_metadata = load_json_if_exists(run_dir / "record_metadata.json")
    record_metadata = record_metadata if isinstance(record_metadata, dict) else {}
    status["prompt_receipt_opt_out"] = bool(record_metadata.get("allow_missing_prompt_receipt"))
    status["grading_audit_opt_out"] = bool(record_metadata.get("allow_suspicious_grading"))
    status["metrics_audit_opt_out"] = bool(record_metadata.get("allow_suspicious_metrics"))
    if is_current_run(manifest):
        receipt_errors = validate_prompt_receipt(run_dir, manifest)
        if receipt_errors:
            status["prompt_receipt"] = "opted-out" if status["prompt_receipt_opt_out"] else "missing-or-invalid"
            status["blockers"].extend(receipt_errors)
        else:
            status["prompt_receipt"] = "valid"
    else:
        status["prompt_receipt"] = "not-required"

    grading_path = run_dir / "grading.json"
    if grading_path.exists():
        grading_data = read_json(grading_path)
        grading_errors = validate_grading_data(grading_data, grading_path)
        grading_errors.extend(
            validate_grading_completeness(
                grading_data,
                load_expected_assertions_for_run(run_dir),
                grading_path,
            )
        )
        status["grading"] = "invalid" if grading_errors else "valid"
        status["errors"].extend(grading_errors)
        if grading_errors:
            status["grading_audit"] = "not-applicable"
            status["grading_audit_errors"] = 0
            status["grading_audit_warnings"] = 0
            status["grading_audit_findings"] = []
        else:
            grading_audit = audit_grading_for_run(run_dir, grading_data if isinstance(grading_data, dict) else None, record_metadata=record_metadata)
            status["grading_audit"] = grading_audit.get("status", "not-applicable")
            status["grading_audit_errors"] = grading_audit.get("errors", 0)
            status["grading_audit_warnings"] = grading_audit.get("warnings", 0)
            status["grading_audit_findings"] = grading_audit.get("findings", [])
    else:
        status["grading"] = "missing"
        status["grading_audit"] = "not-applicable"
        status["grading_audit_errors"] = 0
        status["grading_audit_warnings"] = 0
        status["grading_audit_findings"] = []

    timing_data = load_json_if_exists(run_dir / "timing.json")
    timing_data = timing_data if isinstance(timing_data, dict) else None
    metric_errors = final_metric_errors(timing_data)
    metrics_audit = audit_metric_integrity(
        timing_data,
        current_contract=is_current_run(manifest),
        record_metadata=record_metadata,
    )
    status["metrics_audit"] = metrics_audit.get("status", "not-applicable")
    status["metrics_audit_errors"] = metrics_audit.get("errors", 0)
    status["metrics_audit_warnings"] = metrics_audit.get("warnings", 0)
    status["metrics_audit_findings"] = metrics_audit.get("findings", [])
    if metric_errors:
        status["metrics"] = "missing"
    elif status["metrics_audit"] == "error":
        status["metrics"] = "invalid"
    elif status["metrics_audit"] == "opted-out":
        status["metrics"] = "opted-out"
    else:
        status["metrics"] = "complete"
    status["missing_metrics"] = metric_errors
    status["metrics_opt_out"] = bool(record_metadata.get("allow_missing_metrics"))
    status["phase"] = run_phase_status(status)
    return status


def command_doctor(args: argparse.Namespace) -> int:
    cwd = Path.cwd()
    workspace_dirs = sorted(Path("evals").glob("*/workspace")) if Path("evals").exists() else []
    print(f"python: {sys.version.split()[0]}")
    print(f"executable: {sys.executable}")
    print(f"cwd: {cwd}")
    print(f"AGENTS.md: {'present' if (cwd / 'AGENTS.md').exists() else 'missing'}")
    print(f"CLAUDE.md: {'present' if (cwd / 'CLAUDE.md').exists() else 'missing'}")
    print(f"eval_workspaces: {len(workspace_dirs)}")
    if not args.iteration_dir:
        return 0

    iteration_dir = Path(args.iteration_dir)
    context = parse_iteration_context(iteration_dir)
    run_dirs = discover_prepared_run_dirs(iteration_dir)
    statuses = [inspect_prepared_run(run_dir) for run_dir in run_dirs]
    print(f"iteration: {iteration_dir}")
    print(f"agent: {context.agent}")
    print(f"prepared_runs: {len(statuses)}")
    print(f"outputs_present: {sum(1 for status in statuses if status['outputs_present'])}")
    print(f"primary_response_present: {sum(1 for status in statuses if status['primary_response'] == 'present')}")
    print(f"prompt_receipts_valid: {sum(1 for status in statuses if status['prompt_receipt'] == 'valid')}")
    print(f"prompt_receipt_opt_outs: {sum(1 for status in statuses if status.get('prompt_receipt_opt_out'))}")
    print(f"grading_material_ready: {sum(1 for status in statuses if status.get('grader_material_status') == GRADER_MATERIAL_READY)}")
    print(f"grading_material_pending: {sum(1 for status in statuses if status.get('run_contract_version') == RUN_CONTRACT_VERSION and status.get('grader_material_status') != GRADER_MATERIAL_READY)}")
    print(f"grading_valid: {sum(1 for status in statuses if status['grading'] == 'valid')}")
    print(f"grading_missing: {sum(1 for status in statuses if status['grading'] == 'missing')}")
    for audit_status in GRADING_AUDIT_STATUSES:
        print(f"grading_audit_{audit_status}: {sum(1 for status in statuses if status.get('grading_audit') == audit_status)}")
    print(f"metrics_complete: {sum(1 for status in statuses if status['metrics'] == 'complete')}")
    for audit_status in METRIC_AUDIT_STATUSES:
        print(f"metrics_audit_{audit_status}: {sum(1 for status in statuses if status.get('metrics_audit') == audit_status)}")
    phases = sorted({str(status.get("phase")) for status in statuses})
    for phase in phases:
        print(f"phase_{phase}: {sum(1 for status in statuses if status.get('phase') == phase)}")
    invalid_errors: list[str] = []
    completion_blockers: list[str] = []
    for status in statuses:
        invalid_errors.extend(f"{status['run_dir']}: {error}" for error in status["errors"])
        receipt_path = Path(status["run_dir"]) / "outputs" / "run_receipt.json"
        if status["prompt_receipt"] == "missing-or-invalid" and receipt_path.exists():
            invalid_errors.extend(f"{status['run_dir']}: {error}" for error in status["blockers"])
        if args.require_complete:
            if (
                status.get("run_contract_version") == RUN_CONTRACT_VERSION
                and status.get("grader_material_status") != GRADER_MATERIAL_READY
            ):
                completion_blockers.append(f"{status['run_dir']}: grading materials pending")
            if status["grading"] != "valid":
                completion_blockers.append(f"{status['run_dir']}: grading {status['grading']}")
            if status["metrics"] != "complete":
                metric_details = [
                    f"{finding.get('rule_id')}: {finding.get('message')}"
                    for finding in status.get("metrics_audit_findings", [])
                    if isinstance(finding, dict) and finding.get("severity") == "error"
                ]
                if status.get("metrics") == "opted-out":
                    metric_details.append("suspicious metrics opted-out")
                completion_blockers.append(
                    f"{status['run_dir']}: {', '.join(status['missing_metrics'] or metric_details)}"
                )
            if status["prompt_receipt"] in {"missing-or-invalid", "opted-out"}:
                completion_blockers.append(f"{status['run_dir']}: prompt receipt {status['prompt_receipt']}")
        require_audit = args.require_clean_grading_audit or (
            args.require_complete and status.get("run_contract_version") == RUN_CONTRACT_VERSION
        )
        if require_audit and status.get("grading_audit") in {"error", "opted-out"}:
            completion_blockers.append(f"{status['run_dir']}: grading audit {status.get('grading_audit')}")

    if args.require_complete:
        metric_items = [
            {
                "run_contract_version": status.get("run_contract_version"),
                "metrics_audit": {"findings": status.get("metrics_audit_findings", [])},
                "run_dir": status.get("run_dir"),
            }
            for status in statuses
        ]
        completion_blockers.extend(
            repeated_known_placeholder_metric_reasons(
                metric_items,
                lambda item: str(item.get("run_dir")),
            )
        )

    if args.baseline_from:
        current_runs = discover_runs(iteration_dir, args.allow_legacy)
        source_runs = discover_runs(Path(args.baseline_from), allow_legacy=args.allow_legacy)
        _, baseline_errors = reuse_baseline_runs(
            current_runs=current_runs,
            source_runs=source_runs,
            source_iteration=Path(args.baseline_from),
            baseline_config=args.baseline_config,
            aggregate_model=None,
            aggregate_grader_model=None,
        )
        invalid_errors.extend(baseline_errors)
        print(f"baseline_compatibility: {'ok' if not baseline_errors else 'invalid'}")

    benchmark = load_json_if_exists(iteration_dir / "benchmark.json")
    notes = benchmark.get("analysis", {}).get("notes", []) if isinstance(benchmark, dict) else []
    systematic_notes = [note for note in notes if isinstance(note, dict) and note.get("kind") == "systematic_failure_suspected"]
    if systematic_notes:
        print("systematic_failure_diagnostics:")
        for note in systematic_notes:
            print(f"- {note.get('message')}")

    if invalid_errors:
        print("invalid_artifacts:")
        for error in invalid_errors:
            print(f"- {error}")
    if completion_blockers:
        print("completion_blockers:")
        for blocker in completion_blockers:
            print(f"- {blocker}")
    return 1 if invalid_errors or completion_blockers else 0


def batch_entry_namespace(entry: dict[str, Any]) -> argparse.Namespace:
    allowed = {
        "run_dir",
        "timing",
        "grading",
        "usage_file",
        "usage_text",
        "total_tokens",
        "duration_ms",
        "total_duration_seconds",
        "output_chars",
        "finalize",
        "allow_missing_prompt_receipt",
        "allow_missing_metrics",
        "allow_suspicious_grading",
        "allow_suspicious_metrics",
    }
    unknown = sorted(set(entry) - allowed)
    if unknown:
        raise CommandError(f"unsupported record-batch field(s): {', '.join(unknown)}")
    if not isinstance(entry.get("run_dir"), str):
        raise CommandError("record-batch entry requires string run_dir")
    for key in ("total_tokens", "duration_ms", "output_chars"):
        if key in entry and (isinstance(entry[key], bool) or not isinstance(entry[key], int) or entry[key] < 0):
            raise CommandError(f"{key} must be a non-negative integer")
    if "total_duration_seconds" in entry and (
        isinstance(entry["total_duration_seconds"], bool)
        or not isinstance(entry["total_duration_seconds"], (int, float))
        or entry["total_duration_seconds"] < 0
    ):
        raise CommandError("total_duration_seconds must be a non-negative number")
    return argparse.Namespace(
        run_dir=entry["run_dir"],
        outputs=None,
        timing=entry.get("timing"),
        grading=entry.get("grading"),
        usage_file=entry.get("usage_file"),
        usage_text=entry.get("usage_text"),
        total_tokens=entry.get("total_tokens"),
        duration_ms=entry.get("duration_ms"),
        total_duration_seconds=entry.get("total_duration_seconds"),
        output_chars=entry.get("output_chars"),
        finalize=bool(entry.get("finalize", False)),
        allow_missing_prompt_receipt=bool(entry.get("allow_missing_prompt_receipt", False)),
        allow_missing_metrics=bool(entry.get("allow_missing_metrics", False)),
        allow_suspicious_grading=bool(entry.get("allow_suspicious_grading", False)),
        allow_suspicious_metrics=bool(entry.get("allow_suspicious_metrics", False)),
    )


def candidate_timing_for_record(
    run_dir: Path,
    args: argparse.Namespace,
    *,
    autofill_output_chars: bool = False,
) -> tuple[dict[str, Any] | None, bool]:
    timing_data: dict[str, Any] | None = None
    timing_destination = run_dir / "timing.json"
    changed = False
    if args.timing:
        timing_path = Path(args.timing)
        if not timing_path.exists():
            raise CommandError(f"{timing_path}: timing file does not exist")
        timing_data = load_timing_data(timing_path)
        if not paths_are_same_file(timing_path, timing_destination):
            changed = True
    elif timing_destination.exists():
        timing_data = load_timing_data(timing_destination)
    timing_metrics = timing_metrics_for_record(args)
    if timing_metrics:
        if timing_data is None:
            timing_data = {}
        if args.total_duration_seconds is not None and args.duration_ms is None:
            for key in ("duration_ms", "duration_seconds", "executor_duration_seconds"):
                timing_data.pop(key, None)
        timing_data.update(timing_metrics)
        changed = True
    if autofill_output_chars and (timing_data is None or first_number(timing_data.get("output_chars")) is None):
        response_path = run_dir / "outputs" / "response.md"
        if response_path.exists():
            timing_data = dict(timing_data or {})
            timing_data["output_chars"] = len(response_path.read_text(encoding="utf-8"))
            changed = True
    return timing_data, changed


def validate_record_batch_namespaces(namespaces: list[argparse.Namespace]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    batch_metric_items: list[dict[str, Any]] = []
    for index, namespace in enumerate(namespaces):
        label = f"records[{index}]"
        run_dir = Path(namespace.run_dir)
        resolved = normalized_path_string(run_dir)
        if resolved in seen:
            errors.append(f"{label}: duplicate run_dir {run_dir}")
            continue
        seen.add(resolved)
        if not run_dir.is_dir():
            errors.append(f"{label}: run directory does not exist: {run_dir}")
            continue
        if not (run_dir / "run_manifest.json").exists():
            errors.append(f"{label}: missing run_manifest.json: {run_dir}")
            continue
        try:
            manifest = load_run_manifest(run_dir)
            candidate_timing, _ = candidate_timing_for_record(
                run_dir,
                namespace,
                autofill_output_chars=bool(namespace.finalize or namespace.grading),
            )
            grading_data: dict[str, Any] | None = None
            if namespace.grading:
                grading_path = Path(namespace.grading)
                if not grading_path.exists():
                    errors.append(f"{label}: grading file does not exist: {grading_path}")
                else:
                    expected_assertions = load_expected_assertions_for_run(run_dir)
                    if is_current_run(manifest) and expected_assertions is None:
                        errors.append(f"{label}: {grading_materials_missing_message(run_dir)}")
                        continue
                    raw_grading_data = read_json(grading_path)
                    grading_data = raw_grading_data if isinstance(raw_grading_data, dict) else None
                    grading_errors = validate_grading_data(grading_data, grading_path)
                    grading_errors.extend(
                        validate_grading_completeness(
                            grading_data,
                            expected_assertions,
                            grading_path,
                        )
                    )
                    errors.extend(f"{label}: {error}" for error in grading_errors)
            finalizing = bool(namespace.finalize or namespace.grading)
            if finalizing:
                record_metadata = load_json_if_exists(run_dir / "record_metadata.json")
                record_metadata = record_metadata if isinstance(record_metadata, dict) else {}
                if namespace.allow_suspicious_grading:
                    record_metadata = dict(record_metadata)
                    record_metadata["allow_suspicious_grading"] = True
                if namespace.allow_suspicious_metrics:
                    record_metadata = dict(record_metadata)
                    record_metadata["allow_suspicious_metrics"] = True
                if grading_data is None and (run_dir / "grading.json").exists():
                    expected_assertions = load_expected_assertions_for_run(run_dir)
                    if is_current_run(manifest) and expected_assertions is None:
                        errors.append(f"{label}: {grading_materials_missing_message(run_dir)}")
                        continue
                    raw_existing_grading = read_json(run_dir / "grading.json")
                    grading_data = raw_existing_grading if isinstance(raw_existing_grading, dict) else None
                    grading_errors = validate_grading_data(grading_data, run_dir / "grading.json")
                    grading_errors.extend(
                        validate_grading_completeness(
                            grading_data,
                            expected_assertions,
                            run_dir / "grading.json",
                        )
                    )
                    errors.extend(f"{label}: {error}" for error in grading_errors)
                if grading_data is not None:
                    grading_audit = audit_grading_for_run(run_dir, grading_data, record_metadata=record_metadata)
                    audit_blockers = grading_audit_blocking_messages(run_dir, grading_audit)
                    if audit_blockers and is_current_run(manifest) and not namespace.allow_suspicious_grading:
                        errors.extend(f"{label}: {error}" for error in audit_blockers)
                receipt_errors = validate_prompt_receipt(run_dir, manifest) if is_current_run(manifest) else []
                if receipt_errors and not namespace.allow_missing_prompt_receipt:
                    errors.extend(f"{label}: {error}" for error in receipt_errors)
                metric_errors = final_metric_errors(candidate_timing)
                if metric_errors and not namespace.allow_missing_metrics:
                    errors.extend(f"{label}: {error}" for error in metric_errors)
                metrics_audit = audit_metric_integrity(
                    candidate_timing,
                    current_contract=is_current_run(manifest),
                    record_metadata=record_metadata,
                )
                metric_blockers = metric_audit_blocking_messages(run_dir, metrics_audit)
                if metric_blockers and is_current_run(manifest) and not namespace.allow_suspicious_metrics:
                    errors.extend(f"{label}: {error}" for error in metric_blockers)
                if is_current_run(manifest) and not record_metadata.get("allow_suspicious_metrics"):
                    batch_metric_items.append(
                        {
                            "run_contract_version": RUN_CONTRACT_VERSION,
                            "metrics_audit": metrics_audit,
                            "label": f"{label} {run_dir.name}",
                        }
                    )
        except CommandError as exc:
            errors.append(f"{label}: {exc}")
    for reason in repeated_known_placeholder_metric_reasons(batch_metric_items, lambda item: str(item["label"])):
        errors.append(f"record-batch metric integrity: {reason}; set allow_suspicious_metrics for affected partial or smoke records")
    return errors


def command_record_batch(args: argparse.Namespace) -> int:
    data = read_json(Path(args.records_json))
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        raise CommandError(f"{args.records_json}: expected list or object with records list")
    namespaces: list[argparse.Namespace] = []
    for index, entry in enumerate(records):
        if not isinstance(entry, dict):
            raise CommandError(f"records[{index}]: expected object")
        try:
            namespaces.append(batch_entry_namespace(entry))
        except CommandError as exc:
            raise CommandError(f"records[{index}]: {exc}") from exc
    errors = validate_record_batch_namespaces(namespaces)
    if errors:
        raise CommandError("record-batch prevalidation failed:\n" + "\n".join(f"- {error}" for error in errors))
    for namespace in namespaces:
        command_record(namespace)
    print(f"recorded_batch: {len(namespaces)}")
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
    prepare.add_argument("--rerun-of", help="Previous iteration directory to compare before preparing a fresh rerun.")
    prepare.add_argument("--accept-input-changes", action="store_true", help="Prepare despite --rerun-of input changes and record the differences.")
    prepare.set_defaults(func=command_prepare)

    prepare_grading = subcommands.add_parser("prepare-grading", help="Create grader-only prompts and assertion metadata after executor output exists.")
    prepare_grading.add_argument("target", help="Run directory or iteration directory to prepare for grading.")
    prepare_grading.add_argument("--evals-json", help="Eval suite path when the iteration is outside evals/<skill-name>/workspace/<agent>/iteration-N.")
    prepare_grading.add_argument("--allow-missing-receipt", action="store_true", help="Prepare grader materials without a valid executor prompt receipt for legacy/manual smoke workflows.")
    prepare_grading.set_defaults(func=command_prepare_grading)

    record = subcommands.add_parser("record", help="Attach external outputs, timing, and grading to a prepared run.")
    record.add_argument("run_dir")
    record.add_argument("--outputs")
    record.add_argument("--timing")
    record.add_argument("--grading")
    record.add_argument("--total-tokens", type=parse_non_negative_int)
    record.add_argument("--duration-ms", type=parse_non_negative_int)
    record.add_argument("--total-duration-seconds", type=parse_non_negative_float)
    record.add_argument("--output-chars", type=parse_non_negative_int)
    record.add_argument("--usage-file")
    record.add_argument("--usage-text")
    record.add_argument("--finalize", action="store_true", help="Validate receipt and final metrics without attaching grading.")
    record.add_argument("--allow-missing-prompt-receipt", action="store_true", help="Mark a finalized run as noncanonical when no matching prompt receipt is available.")
    record.add_argument("--allow-missing-metrics", action="store_true", help="Mark a finalized run as partial when required metrics are unavailable.")
    record.add_argument("--allow-suspicious-grading", action="store_true", help="Mark a finalized run as noncanonical when static grading audit errors are intentionally accepted.")
    record.add_argument("--allow-suspicious-metrics", action="store_true", help="Mark a finalized run as noncanonical when present metrics are invalid or known to be placeholder data.")
    record.set_defaults(func=command_record)

    grading_template = subcommands.add_parser(
        "grading-template",
        help="Write a grading.json template for a run after prepare-grading.",
        description="Write a grading.json template for a run after prepare-grading.",
    )
    grading_template.add_argument("run_dir")
    grading_template.add_argument("--output")
    grading_template.set_defaults(func=command_grading_template)

    record_batch = subcommands.add_parser("record-batch", help="Record metrics, usage, grading, and finalization metadata for multiple runs.")
    record_batch.add_argument("records_json")
    record_batch.set_defaults(func=command_record_batch)

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

    doctor = subcommands.add_parser("doctor", help="Print local CLI environment and optional iteration checks.")
    doctor.add_argument("iteration_dir", nargs="?")
    doctor.add_argument("--baseline-from")
    doctor.add_argument("--baseline-config", default="without_skill")
    doctor.add_argument("--allow-legacy", action="store_true")
    doctor.add_argument("--require-complete", action="store_true")
    doctor.add_argument("--require-clean-grading-audit", action="store_true", help="Fail on grading audit errors or opt-outs for any readable run contract.")
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
