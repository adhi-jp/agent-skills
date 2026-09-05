#!/usr/bin/env python3
"""Check a vibe session record (`.plans/vibe-sessions/<record-id>.json`) against the shared schema.

The schema, the write procedure, and the record states are the `session-record-schema`
block of `shared/vibe-contract.md`; this checker implements the "Checker outcome and exit"
column of that block's table "Record states, the checker's outcome and exit code, and what
each gate returns": ``accept`` (0), ``flag`` (1), ``reject`` (2). Every finding is printed
as one ``<level>: <code>: <detail>`` line on stdout (untrusted values are JSON-encoded so a
line stays a line), followed by ``outcome: <name>``. A fatal usage error prints
``error: ...`` on stderr and ``outcome: reject`` on stdout with exit 2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = "1"
LEASE_DURATION = timedelta(hours=8)
NOTE_MAX_LENGTH = 200

RECORD_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,120}")
UUID4_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
CONTROL_CHAR_RE = re.compile(r"[\x00-\x1f\x7f]")

STATUSES = ("active", "completed", "cancelled", "superseded")
PHASES = (
    "workflow-control",
    "requirements-specification",
    "creative-direction-exploration",
    "code-investigation",
    "implementation-planning",
    "plan-execution",
    "debug-and-repair",
    "review",
    "plan-pre-check-walkthrough",
    "commit-execution",
    "writing",
    "direct-implementation",
    "maintenance",
)
EFFECT_MODES = ("read-only", "artifact-only", "state-changing", "none")
EVENT_KINDS = ("approval", "proceed", "handoff", "commit-selection", "confirmation")
EVENT_SOURCES = ("user-turn", "bound-plan-item", "specialist-checkpoint", "agent-proposed")
EVENT_STATUSES = ("current", "superseded")
ARTIFACT_BOUND_EVENT_KINDS = ("approval", "proceed", "handoff")
ALWAYS_BINDING_PHASES = ("implementation-planning", "plan-execution", "plan-pre-check-walkthrough")

REQUIRED_KEYS = (
    "schema_version",
    "record_id",
    "repository",
    "workflow_id",
    "host_session_id",
    "generation",
    "lease",
    "status",
    "closed_at",
    "phase",
    "effect_mode",
    "allowed_paths",
    "goal",
    "pending_decision",
    "blocker",
    "next_route",
    "artifact_paths",
    "capability_map",
    "events",
)

SECRET_PATTERNS = (
    ("aws-access-key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("api-key-prefix", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "credential-assignment",
        re.compile(
            r"(?i)\b(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret)"
            r"\b\s*[:=]\s*\S+"
        ),
    ),
    ("bearer-token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{16,}=*")),
)

EXIT_ACCEPT = 0
EXIT_FLAG = 1
EXIT_REJECT = 2


class RecordError(Exception):
    """Raised for fatal usage failures (bad --now, unreadable prior, missing directory)."""


@dataclass(frozen=True)
class Finding:
    level: str  # reject, flag, note
    code: str
    detail: str

    def render(self) -> str:
        text = f"{self.level}: {self.code}: {self.detail}"
        return CONTROL_CHAR_RE.sub(lambda match: "\\u%04x" % ord(match.group(0)), text)


def quote(value: object) -> str:
    """JSON-encode an untrusted value so it renders on one line."""
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True)
    except (TypeError, ValueError):
        return json.dumps(str(value), ensure_ascii=True)


# --- CLI ---------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a vibe session record against the session-record-schema block of "
            "shared/vibe-contract.md; outcomes accept (0), flag (1), reject (2)."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="validate one record and report accept, flag, or reject")
    check.add_argument("record", help="path to <record-id>.json (a missing file is 'reject: absent')")
    check.add_argument(
        "--now",
        default=None,
        help="instant used for lease checks, in the record's own timestamp form "
        "(ISO-8601 UTC, second precision, Z suffix; default: current time)",
    )
    check.add_argument(
        "--expect-worktree",
        default=None,
        help="worktree the record must belong to; the expectation is normalized "
        "(absolute, lexically normalized, symlinks resolved) before comparison, the record value is not",
    )
    check.add_argument("--expect-session", default=None, help="host session id the record must be bound to")
    check.add_argument(
        "--records-dir",
        default=None,
        help="directory of sibling records scanned for conflicts; each sibling must pass the full schema "
        "to count, malformed or symlinked entries are discarded with a note, and the scan is skipped "
        "when the record under check is itself stale or tombstoned",
    )
    check.add_argument(
        "--prior",
        default=None,
        help="previously written record of the same workflow; generation must exceed its value "
        "(a prior for another workflow, or an unreadable prior, is a fatal usage error)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        now = parse_now(args.now)
        findings = check_record(
            Path(args.record),
            now=now,
            expect_worktree=args.expect_worktree,
            expect_session=args.expect_session,
            records_dir=Path(args.records_dir) if args.records_dir else None,
            prior=Path(args.prior) if args.prior else None,
        )
    except RecordError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("outcome: reject")
        return EXIT_REJECT
    for finding in findings:
        print(finding.render())
    outcome, code = summarize(findings)
    print(f"outcome: {outcome}")
    return code


def summarize(findings: list[Finding]) -> tuple[str, int]:
    levels = {finding.level for finding in findings}
    if "reject" in levels:
        return "reject", EXIT_REJECT
    if "flag" in levels:
        return "flag", EXIT_FLAG
    return "accept", EXIT_ACCEPT


def parse_now(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0)
    parsed = parse_timestamp(value)
    if parsed is None:
        raise RecordError(
            f"--now is not an ISO-8601 instant with second precision and a Z suffix: {quote(value)}"
        )
    return parsed


# --- Record loading ----------------------------------------------------------


def load_record(path: Path, findings: list[Finding]) -> dict | None:
    if not path.exists():
        findings.append(Finding("reject", "absent", path.as_posix()))
        return None
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        findings.append(Finding("reject", "unreadable", f"{path.as_posix()}: {exc}"))
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        findings.append(Finding("reject", "malformed-json", f"{path.as_posix()}: {exc}"))
        return None
    if not isinstance(data, dict):
        findings.append(Finding("reject", "schema", "top-level value is not an object"))
        return None
    return data


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or TIMESTAMP_RE.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(value, TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)


def is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_canonical_path(value: str) -> bool:
    return bool(value) and os.path.isabs(value) and os.path.normpath(value) == value


def find_secret_class(text: str) -> str | None:
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return name
    return None


def walk_strings(value: object, label: str) -> Iterator[tuple[str, str]]:
    """Yield ``(label, string)`` for every string value anywhere inside a JSON value."""
    if isinstance(value, str):
        yield label, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from walk_strings(item, f"{label}.{key}" if label else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_strings(item, f"{label}[{index}]")


def readable_file(path: str) -> bool:
    try:
        return os.path.isfile(path) and os.access(path, os.R_OK)
    except (OSError, ValueError):
        return False


# --- Schema validation -------------------------------------------------------


class SchemaValidator:
    def __init__(self, record: dict, path: Path) -> None:
        self.record = record
        self.path = path
        self.findings: list[Finding] = []

    def reject(self, code: str, detail: str) -> None:
        self.findings.append(Finding("reject", code, detail))

    def string(self, container: dict, key: str, label: str, *, nullable: bool = False, nonempty: bool = True) -> str | None:
        value = container.get(key)
        if value is None and nullable:
            return None
        if not isinstance(value, str):
            self.reject("schema", f"{label} must be a string{' or null' if nullable else ''}")
            return None
        if nonempty and not value:
            self.reject("schema", f"{label} must be non-empty")
            return None
        return value

    def timestamp(self, container: dict, key: str, label: str, *, nullable: bool = False) -> datetime | None:
        value = container.get(key)
        if value is None and nullable:
            return None
        parsed = parse_timestamp(value)
        if parsed is None:
            self.reject("timestamp", f"{label} must be an ISO-8601 UTC timestamp with second precision and a Z suffix")
        return parsed

    def enum(self, container: dict, key: str, label: str, allowed: tuple[str, ...]) -> str | None:
        value = container.get(key)
        if not isinstance(value, str) or value not in allowed:
            self.reject("enum", f"{label} must be one of {', '.join(allowed)}; got {quote(value)}")
            return None
        return value

    def canonical_path(self, container: dict, key: str, label: str) -> str | None:
        value = self.string(container, key, label)
        if value is None:
            return None
        if not is_canonical_path(value):
            self.reject("path", f"{label} must be a canonical absolute path: {quote(value)}")
            return None
        return value

    def canonical_path_list(self, container: dict, key: str, label: str) -> list[str]:
        value = container.get(key)
        if not isinstance(value, list):
            self.reject("schema", f"{label} must be an array of strings")
            return []
        result: list[str] = []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item:
                self.reject("schema", f"{label}[{index}] must be a non-empty string")
                continue
            if not is_canonical_path(item):
                self.reject("path", f"{label}[{index}] must be a canonical absolute path: {quote(item)}")
                continue
            result.append(item)
        return result

    def check_string_hygiene(self) -> None:
        for label, value in walk_strings(self.record, ""):
            if CONTROL_CHAR_RE.search(value):
                self.reject("control-character", f"{label} contains a control character")
            secret_class = find_secret_class(value)
            if secret_class:
                self.reject("secret", f"{label} carries a secret-like literal ({secret_class})")

    def validate(self) -> None:
        record = self.record
        for key in REQUIRED_KEYS:
            if key not in record:
                self.reject("missing-key", f"required key {key} is absent")
        if self.findings:
            return
        self.check_string_hygiene()

        if record.get("schema_version") != SCHEMA_VERSION:
            self.reject("schema-version", f"schema_version must be {quote(SCHEMA_VERSION)}; got {quote(record.get('schema_version'))}")

        record_id = self.string(record, "record_id", "record_id")
        if record_id is not None:
            if RECORD_ID_RE.fullmatch(record_id) is None:
                self.reject("record-id", f"record_id does not match ^[A-Za-z0-9._-]{{1,120}}$: {quote(record_id)}")
            elif record_id != self.path.stem:
                self.reject("record-id", f"record_id {quote(record_id)} does not equal the file stem {quote(self.path.stem)}")

        repository = record.get("repository")
        if not isinstance(repository, dict):
            self.reject("schema", "repository must be an object")
        else:
            for key in ("root", "worktree"):
                if key not in repository:
                    self.reject("missing-key", f"required key repository.{key} is absent")
                    continue
                self.canonical_path(repository, key, f"repository.{key}")
            if "head" not in repository:
                self.reject("missing-key", "required key repository.head is absent")
            else:
                self.string(repository, "head", "repository.head", nullable=True)

        workflow_id = self.string(record, "workflow_id", "workflow_id")
        if workflow_id is not None and UUID4_RE.fullmatch(workflow_id) is None:
            self.reject("workflow-id", f"workflow_id must be a UUIDv4: {quote(workflow_id)}")

        self.string(record, "host_session_id", "host_session_id", nullable=True)

        generation = record.get("generation")
        if not is_int(generation) or generation < 1:
            self.reject("generation", f"generation must be an integer >= 1; got {quote(generation)}")

        lease = record.get("lease")
        if not isinstance(lease, dict):
            self.reject("schema", "lease must be an object")
        else:
            for key in ("owner", "renewed_at", "expires_at"):
                if key not in lease:
                    self.reject("missing-key", f"required key lease.{key} is absent")
            owner = self.string(lease, "owner", "lease.owner") if "owner" in lease else None
            if owner is not None and workflow_id is not None and owner != workflow_id:
                self.reject("lease-owner", f"lease.owner {quote(owner)} does not equal workflow_id {quote(workflow_id)}")
            renewed = self.timestamp(lease, "renewed_at", "lease.renewed_at") if "renewed_at" in lease else None
            expires = self.timestamp(lease, "expires_at", "lease.expires_at") if "expires_at" in lease else None
            if renewed is not None and expires is not None and expires != renewed + LEASE_DURATION:
                self.reject(
                    "lease-expiry",
                    f"lease.expires_at {format_timestamp(expires)} is not lease.renewed_at + 8h "
                    f"({format_timestamp(renewed + LEASE_DURATION)})",
                )

        status = self.enum(record, "status", "status", STATUSES)
        self.timestamp(record, "closed_at", "closed_at", nullable=True)
        if status is not None and "closed_at" in record:
            if status != "active" and record.get("closed_at") is None:
                self.reject("closed-at", f"status {status} requires closed_at to be set")
            if status == "active" and record.get("closed_at") is not None:
                self.reject("closed-at", "status active requires closed_at to be null")

        phase = self.enum(record, "phase", "phase", PHASES)
        self.enum(record, "effect_mode", "effect_mode", EFFECT_MODES)
        self.canonical_path_list(record, "allowed_paths", "allowed_paths")

        self.string(record, "goal", "goal")
        for key in ("pending_decision", "blocker", "next_route"):
            self.string(record, key, key, nullable=True, nonempty=False)

        artifact_paths = self.canonical_path_list(record, "artifact_paths", "artifact_paths")
        identity = self.validate_identity(record)
        self.validate_binding(phase, artifact_paths, identity)
        self.validate_capability_map(record)
        self.validate_events(record, identity)

    def validate_identity(self, record: dict) -> list[tuple[str, str]]:
        value = record.get("artifact_identity", [])
        if not isinstance(value, list):
            self.reject("schema", "artifact_identity must be an array of objects")
            return []
        entries: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            label = f"artifact_identity[{index}]"
            if not isinstance(item, dict):
                self.reject("schema", f"{label} must be an object")
                continue
            for key in ("path", "sha256", "refreshed_at"):
                if key not in item:
                    self.reject("missing-key", f"required key {label}.{key} is absent")
            path = self.canonical_path(item, "path", f"{label}.path") if "path" in item else None
            digest = self.string(item, "sha256", f"{label}.sha256") if "sha256" in item else None
            if digest is not None and SHA256_RE.fullmatch(digest) is None:
                self.reject("schema", f"{label}.sha256 must be 64 lowercase hex characters")
                digest = None
            if "refreshed_at" in item:
                self.timestamp(item, "refreshed_at", f"{label}.refreshed_at")
            if path is not None and digest is not None:
                entries.append((path, digest))
        return entries

    def validate_binding(self, phase: str | None, artifact_paths: list[str], identity: list[tuple[str, str]]) -> None:
        identity_paths = [path for path, _ in identity]
        seen: set[str] = set()
        for path in identity_paths:
            if path in seen:
                self.reject("binding", f"artifact_identity has duplicate entries for {quote(path)}")
            seen.add(path)
            if path not in artifact_paths:
                self.reject("binding", f"artifact_identity entry {quote(path)} is not listed in artifact_paths")
        if phase is None:
            return
        binding_required = phase in ALWAYS_BINDING_PHASES or any(readable_file(path) for path in artifact_paths)
        if not binding_required:
            return
        if not identity:
            self.reject(
                "binding",
                f"artifact_identity is empty in a binding-required state (phase {phase}, "
                f"{len(artifact_paths)} artifact path(s))",
            )
            return
        for path in artifact_paths:
            if path not in identity_paths:
                self.reject(
                    "binding",
                    f"artifact path {quote(path)} has no artifact_identity entry in a binding-required state (phase {phase})",
                )

    def validate_capability_map(self, record: dict) -> None:
        value = record.get("capability_map")
        if value is None:
            return
        if not isinstance(value, dict):
            self.reject("schema", "capability_map must be an object or null")
            return
        for key in ("checked_at", "source", "phases"):
            if key not in value:
                self.reject("missing-key", f"required key capability_map.{key} is absent")
        if "checked_at" in value:
            self.timestamp(value, "checked_at", "capability_map.checked_at")
        if "source" in value:
            self.string(value, "source", "capability_map.source")
        phases = value.get("phases")
        if "phases" in value:
            if not isinstance(phases, dict):
                self.reject("schema", "capability_map.phases must be an object")
                return
            for phase, specialist in phases.items():
                if phase not in PHASES:
                    self.reject("enum", f"capability_map.phases key must be a phase row id; got {quote(phase)}")
                if specialist is not None and (not isinstance(specialist, str) or not specialist):
                    self.reject("schema", f"capability_map.phases[{quote(phase)}] must be a non-empty string or null")

    def validate_events(self, record: dict, identity: list[tuple[str, str]]) -> None:
        events = record.get("events")
        if not isinstance(events, list):
            self.reject("schema", "events must be an array of objects")
            return
        for index, event in enumerate(events):
            label = f"events[{index}]"
            if not isinstance(event, dict):
                self.reject("schema", f"{label} must be an object")
                continue
            for key in ("kind", "source", "at", "artifact", "note", "status"):
                if key not in event:
                    code = "event-source" if key == "source" else "missing-key"
                    self.reject(code, f"required key {label}.{key} is absent")
            kind = self.enum(event, "kind", f"{label}.kind", EVENT_KINDS) if "kind" in event else None
            status = self.enum(event, "status", f"{label}.status", EVENT_STATUSES) if "status" in event else None
            if "source" in event:
                source = event.get("source")
                if not isinstance(source, str) or source not in EVENT_SOURCES:
                    self.reject(
                        "event-source",
                        f"{label}.source must be one of {', '.join(EVENT_SOURCES)}; got {quote(source)}",
                    )
            if "at" in event:
                self.timestamp(event, "at", f"{label}.at")
            if "note" in event:
                note = event.get("note")
                if not isinstance(note, str):
                    self.reject("schema", f"{label}.note must be a string")
                elif len(note) > NOTE_MAX_LENGTH:
                    self.reject("note-length", f"{label}.note exceeds {NOTE_MAX_LENGTH} characters ({len(note)})")
            if "artifact" in event:
                self.validate_event_artifact(label, kind, status, event.get("artifact"), identity)

    def validate_event_artifact(
        self,
        label: str,
        kind: str | None,
        status: str | None,
        artifact: object,
        identity: list[tuple[str, str]],
    ) -> None:
        """Check an event's artifact binding.

        A ``current`` approval, proceed, or handoff event must match a current
        ``artifact_identity`` entry; a ``superseded`` one must not (an event cannot be
        superseded while its digest is current). A null artifact is rejected for those
        kinds whatever the status.
        """
        if artifact is None:
            if kind in ARTIFACT_BOUND_EVENT_KINDS:
                self.reject("event-artifact", f"{label}.artifact is null for a {kind} event")
            return
        if not isinstance(artifact, dict):
            self.reject("schema", f"{label}.artifact must be an object or null")
            return
        for key in ("path", "sha256"):
            if key not in artifact:
                self.reject("missing-key", f"required key {label}.artifact.{key} is absent")
        path = self.canonical_path(artifact, "path", f"{label}.artifact.path") if "path" in artifact else None
        digest = self.string(artifact, "sha256", f"{label}.artifact.sha256") if "sha256" in artifact else None
        if digest is not None and SHA256_RE.fullmatch(digest) is None:
            self.reject("schema", f"{label}.artifact.sha256 must be 64 lowercase hex characters")
            digest = None
        if kind in ARTIFACT_BOUND_EVENT_KINDS and path is not None and digest is not None:
            matches_current = (path, digest) in identity
            if status == "current" and not matches_current:
                self.reject(
                    "event-artifact",
                    f"{label}.artifact ({quote(path)}, {digest[:12]}...) matches no current artifact_identity entry",
                )
            elif status == "superseded" and matches_current:
                self.reject(
                    "event-status",
                    f"{label} is superseded but its artifact ({quote(path)}, {digest[:12]}...) "
                    "matches a current artifact_identity entry",
                )


# --- Flags -------------------------------------------------------------------


def sha256_of(path: str) -> str | None:
    try:
        if not os.path.isfile(path):
            return None
        digest = hashlib.sha256()
        with open(path, "rb") as file_obj:
            for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except (OSError, ValueError):
        return None


def normalize_expectation(value: str) -> set[str]:
    absolute = os.path.abspath(value)
    return {value, os.path.normpath(absolute), os.path.realpath(absolute)}


def check_flags(
    record: dict,
    *,
    now: datetime,
    expect_worktree: str | None,
    expect_session: str | None,
) -> list[Finding]:
    findings: list[Finding] = []
    expires = parse_timestamp(record["lease"]["expires_at"])
    if expires is not None and expires <= now:
        findings.append(
            Finding("flag", "stale", f"lease.expires_at {format_timestamp(expires)} is not after now {format_timestamp(now)}")
        )
    if record["status"] != "active":
        findings.append(
            Finding("flag", "tombstoned", f"status {record['status']} with closed_at {record['closed_at']}")
        )
    worktree = record["repository"]["worktree"]
    if expect_worktree is not None and worktree not in normalize_expectation(expect_worktree):
        findings.append(
            Finding(
                "flag",
                "foreign-worktree",
                f"repository.worktree {quote(worktree)} is not the expected {quote(expect_worktree)}",
            )
        )
    session = record["host_session_id"]
    if session is None:
        findings.append(
            Finding(
                "note",
                "session-unbound",
                "host_session_id is null; the history-mutation gate and the commit-selection gate ask, "
                "the read-only-phase write gate allows",
            )
        )
    elif expect_session is not None and session != expect_session:
        findings.append(
            Finding(
                "flag",
                "foreign-session",
                f"host_session_id {quote(session)} is not the expected {quote(expect_session)}",
            )
        )
    for entry in record.get("artifact_identity", []):
        actual = sha256_of(entry["path"])
        if actual is None:
            findings.append(Finding("note", "artifact-not-readable", f"{quote(entry['path'])} was not recomputed"))
        elif actual != entry["sha256"]:
            findings.append(
                Finding(
                    "flag",
                    "identity-mismatch",
                    f"blocker: {quote(entry['path'])} recorded {entry['sha256'][:12]}... but reads {actual[:12]}...",
                )
            )
    return findings


def check_prior(record: dict, prior_path: Path) -> list[Finding]:
    try:
        prior = json.loads(prior_path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecordError(f"prior record is unreadable or malformed: {prior_path.as_posix()}: {exc}") from exc
    if not isinstance(prior, dict) or not is_int(prior.get("generation")):
        raise RecordError(f"prior record has no integer generation: {prior_path.as_posix()}")
    if prior.get("workflow_id") != record["workflow_id"]:
        raise RecordError(
            f"prior record belongs to workflow {quote(prior.get('workflow_id'))}, not {quote(record['workflow_id'])}: "
            f"{prior_path.as_posix()}"
        )
    if record["generation"] <= prior["generation"]:
        return [
            Finding(
                "flag",
                "generation",
                f"generation {record['generation']} is not greater than the prior record's {prior['generation']}",
            )
        ]
    return []


def load_sibling(entry: Path, own: Path | None) -> tuple[dict | None, str | None]:
    """Return (record, None) for a schema-valid sibling, (None, reason) to discard, (None, None) to skip self."""
    try:
        if entry.is_symlink():
            return None, "is a symlink"
        if own is not None and entry.resolve() == own:
            return None, None
        if not entry.is_file():
            return None, "is not a regular file"
        data = json.loads(entry.read_bytes().decode("utf-8"))
    except json.JSONDecodeError:
        return None, "is malformed"
    except (OSError, RuntimeError, UnicodeDecodeError):
        return None, "cannot be read"
    if not isinstance(data, dict):
        return None, "is malformed"
    validator = SchemaValidator(data, entry)
    validator.validate()
    if validator.findings:
        return None, f"fails the schema ({validator.findings[0].code})"
    return data, None


def check_siblings(
    record: dict,
    record_path: Path,
    records_dir: Path,
    *,
    now: datetime,
    expect_session: str | None,
) -> list[Finding]:
    if records_dir.is_symlink() or not records_dir.is_dir():
        raise RecordError(f"--records-dir is not a directory: {records_dir.as_posix()}")
    findings: list[Finding] = []
    try:
        own: Path | None = record_path.resolve()
    except (OSError, RuntimeError):
        own = None
    try:
        entries = sorted(records_dir.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise RecordError(f"--records-dir cannot be listed: {records_dir.as_posix()}: {exc}") from exc
    for entry in entries:
        if entry.suffix != ".json":
            continue
        sibling, reason = load_sibling(entry, own)
        if sibling is None:
            if reason is not None:
                findings.append(Finding("note", "sibling-discarded", f"{entry.name} {reason}"))
            continue
        expires = parse_timestamp(sibling["lease"]["expires_at"])
        if sibling["status"] != "active" or expires is None or expires <= now:
            continue
        if sibling["repository"]["worktree"] != record["repository"]["worktree"]:
            continue
        sibling_session = sibling["host_session_id"]
        if expect_session is not None and sibling_session is not None and sibling_session != expect_session:
            continue
        if sibling["workflow_id"] == record["workflow_id"]:
            findings.append(
                Finding(
                    "flag",
                    "conflicting",
                    f"{entry.name} is another active record claiming workflow {quote(record['workflow_id'])}",
                )
            )
        else:
            findings.append(
                Finding(
                    "flag",
                    "conflicting",
                    f"{entry.name} is another active record for worktree {quote(sibling['repository']['worktree'])} "
                    f"(workflow {quote(sibling['workflow_id'])}, host_session_id {quote(sibling_session)})",
                )
            )
    return findings


# --- Entry point -------------------------------------------------------------


def check_record(
    path: Path,
    *,
    now: datetime,
    expect_worktree: str | None = None,
    expect_session: str | None = None,
    records_dir: Path | None = None,
    prior: Path | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    record = load_record(path, findings)
    if record is None:
        return findings
    validator = SchemaValidator(record, path)
    validator.validate()
    findings.extend(validator.findings)
    if validator.findings:
        return findings

    findings.extend(check_flags(record, now=now, expect_worktree=expect_worktree, expect_session=expect_session))
    if prior is not None:
        findings.extend(check_prior(record, prior))
    if records_dir is not None:
        active_and_fresh = not any(finding.code in {"stale", "tombstoned"} for finding in findings)
        if active_and_fresh:
            findings.extend(check_siblings(record, path, records_dir, now=now, expect_session=expect_session))
    return findings


if __name__ == "__main__":
    raise SystemExit(main())
