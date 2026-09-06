#!/usr/bin/env python3
"""Render, check, list, and audit shared-contract blocks vendored into vibe-* packages.

The shared source (``shared/vibe-contract.md`` by default) declares blocks::

    <!-- shared-contract:block <id> dependents=vibe-a,vibe-b -->
    ...block body...
    <!-- shared-contract:endblock <id> -->

A dependent package carries a marker pair per block it depends on::

    <!-- shared-contract:begin <id> source=shared/vibe-contract.md -->
    <!-- shared-contract:end <id> -->

``render`` fills pristine pairs and refuses drifted ones unless ``--force``;
``check`` verifies the source and every rendered copy byte for byte, and refuses a block
that names a package discovered under ``--root`` (any ``vibe-`` token that is not a
package name, such as ``vibe-contract`` or ``vibe-sessions``, is allowed);
``audit-names`` reports roster package names cited outside the router package;
``list`` prints the blocks the source declares;
``measure`` prints per-package and per-task size against a frozen manifest.

Marker-looking lines inside a correctly matched Markdown code fence are ordinary text
for both parsers, so a file may show the marker grammar as an example. Prose outside
every block marker — the preamble and any appendix section with its headings, tables,
and fenced examples — is not part of any block and is ignored by all commands.

A source block whose first non-empty line is a bold lead (``**…**``) is in the scannable
shape and is measured against the shape caps below; a block without one keeps the legacy
shape and is only checked as before. Once any scannable block drops its closing
boilerplate, the source has adopted per-package closings: each package then carries one
synthetic ``closing`` block directly below its class line, holding the precedence
sentence and, for a package with a gate or schema block, the applicability sentence. Each
of those sentences names the blocks it binds and where they sit, so no third line explains
them, and no other generated block in the package may carry either sentence.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "shared" / "vibe-contract.md"
DEFAULT_MANIFEST = REPO_ROOT / "shared" / "measure-manifest.json"
DEFAULT_ROOT = REPO_ROOT / "skills"
ENTRY_FILE_NAME = "SKILL.md"
SOURCE_CITATION = "shared/vibe-contract.md"
ROUTER_PACKAGE = "vibe-coding"
PACKAGE_PREFIX = "vibe-"
MARKER_KEYWORD = "shared-contract"
IGNORED_DIR_NAMES = {"__pycache__"}
TEMP_SUFFIX = ".shared-contract.tmp"

PRECEDENCE_SENTENCE = (
    "Where a package declares a stricter or narrower rule in its own text, that declaration controls."
)
APPLICABILITY_SENTENCE = (
    "A package may state which of its phases this gate applies to; "
    "it may not change the gate's inputs, outcomes, or fields."
)
# The two sentences the per-package closing block renders. Each carries its own scope, so
# it binds where it stands and needs no separate line explaining which blocks it reaches.
CLOSING_PRECEDENCE_SENTENCE = (
    "For every consolidation block this package carries, here and in its references: "
    "where this package declares a stricter or narrower rule in its own text, that declaration controls."
)
CLOSING_APPLICABILITY_SENTENCE = (
    "For every gate and schema block this package carries, here and in its references: "
    "this package may state which of its phases the block applies to; "
    "it may not change the block's inputs, outcomes, or fields."
)
GATE_BLOCK_IDS = frozenset(
    {
        "history-mutation-gate",
        "commit-selection-gate",
        "read-only-phase-write-gate",
    }
)
SCHEMA_BLOCK_IDS = frozenset(
    {"session-record-schema", "decision-record-schema", "decision-record-index", "deferred-findings-schema"}
)
NON_OVERRIDABLE_BLOCK_IDS = GATE_BLOCK_IDS | SCHEMA_BLOCK_IDS
# The closing sentences the per-package closing block renders, in body order.
CLOSING_SENTENCES = (CLOSING_PRECEDENCE_SENTENCE, CLOSING_APPLICABILITY_SENTENCE)
# A block never carries any of these: the two legacy per-block tails and the two
# self-scoped sentences the closing block renders once per package.
BOILERPLATE_SENTENCES = (PRECEDENCE_SENTENCE, APPLICABILITY_SENTENCE) + CLOSING_SENTENCES
BOILERPLATE_SENTENCE_NAMES = {
    PRECEDENCE_SENTENCE: "the per-block precedence sentence",
    APPLICABILITY_SENTENCE: "the per-block applicability sentence",
    CLOSING_PRECEDENCE_SENTENCE: "the precedence sentence",
    CLOSING_APPLICABILITY_SENTENCE: "the applicability sentence",
}

# Block ids whose pre-rewrite text carried at least one negative rule, so the rewritten
# block must still open a lead, bullet, or sub-bullet with "Never" or "Only" (design v3
# rule 8). Derived from the pre-rewrite source: every block body was split into sentences
# and every block holding a never/not/no/only sentence was kept. All seventeen blocks
# qualified, so the set is the full block list.
NEGATIVE_LINE_BLOCK_IDS = frozenset(
    {
        "evidence-classes",
        "accepted-risk-semantics",
        "delegated-result-proof",
        "language-precedence-chat",
        "language-precedence-document",
        "effect-write-boundaries",
        "commit-selection-state-changing",
        "commit-selection-document-only",
        "human-risk-decisions",
        "model-tier-selection",
        "trusted-orchestration-evidence",
        "subagent-permission",
        "secret-redaction",
        "history-mutation-gate",
        "commit-selection-gate",
        "read-only-phase-write-gate",
        "session-record-schema",
        "decision-records",
        "decision-record-schema",
        "decision-record-index",
        "deferred-findings",
        "deferred-findings-schema",
    }
)

# The synthetic per-package block that carries the closing sentences once the shared
# source stops closing every block. It is never declared in the source.
CLOSING_BLOCK_ID = "closing"
CLOSING_PER_BLOCK = "per-block"
CLOSING_PER_PACKAGE = "per-package"

# Shape caps for a scannable block: a bold imperative lead, one obligation per bullet,
# and at most one exception line after the bullets.
LEAD_WORD_CAP = 25
CONSOLIDATION_BULLET_WORD_CAP = 40
GATE_BULLET_WORD_CAP = 30
SUB_BULLET_WORD_CAP = 30
EXCEPTION_WORD_CAP = 35
PARAGRAPH_WORD_CAP = 60
GATE_BLOCK_WORD_CAP = 260
# Set by the coordinator from the smallest lossless size the schema block reaches, and
# recorded in design v3: 522 words with every actor, modality, condition, and scope kept,
# plus a margin for one short bullet. A block that outgrows it after a lossless
# restoration moves this value, never the enforcement.
SCHEMA_BLOCK_WORD_CAP = 530
EXAMPLE_LINE_CAP = 1

# A bold lead opens with "Never", "Only", or a listed base-form verb, capitalised. The
# list is an allowlist: a lead opening with any other word is flagged, so a declarative
# lead ("Evidence carries one of four classes") never passes. It seeds from the first
# word of every lead the shared source carries plus common contract imperatives; add a
# verb here when a new lead needs one.
IMPERATIVE_LEAD_WORDS = frozenset({"Never", "Only"})
IMPERATIVE_LEAD_VERBS = frozenset(
    {
        "Accept", "Allow", "Apply", "Ask", "Assume", "Avoid", "Bind", "Carry", "Check",
        "Choose", "Cite", "Classify", "Close", "Commit", "Compare", "Confirm", "Count",
        "Declare", "Decide", "Defer", "Delegate", "Deliver", "Deny", "Describe",
        "Detect", "Disclose", "Do", "Document", "Drop", "Echo", "Edit", "End",
        "Enumerate", "Ensure", "Enter", "Escalate", "Exclude", "Execute", "Expand",
        "Explain", "Fill", "Fix", "Follow", "Give", "Hand", "Hold", "Identify", "Ignore",
        "Implement", "Include", "Judge", "Keep", "Label", "Leave", "Limit", "List",
        "Load", "Log", "Mark", "Match", "Move", "Name", "Note", "Observe", "Omit",
        "Open", "Pause", "Place", "Plan", "Prefer", "Present", "Preserve", "Prove",
        "Publish", "Put", "Quote", "Raise", "Read", "Record", "Redact", "Refuse",
        "Reject", "Render", "Renew", "Repeat", "Replace", "Report", "Request",
        "Require", "Rerun", "Resolve", "Restate", "Return", "Review", "Rewrite",
        "Route", "Run", "Save", "Scope", "Select", "Separate", "Set", "Show", "Split",
        "Stage", "Start", "State", "Stay", "Stop", "Store", "Summarize", "Surface",
        "Suspend", "Tag", "Take", "Tie", "Track", "Treat", "Trust", "Use", "Verify",
        "Wait", "Widen", "Write",
    }
)
# A lead, bullet, or sub-bullet that opens a negative rule, for the survival check.
NEGATIVE_LINE_RE = re.compile(r"^ *(?:[-*+]\s+|\d+\.\s+)?(?:\*\*)?(?:Never|Only)\b")

# Appendix cross-references. Every `Appendix S<n>`/`Appendix G<n>` citation resolves to
# its own `###` heading, and a block that sends the reader to "the appendix" is valid
# only while the appendix section heading exists.
APPENDIX_SECTION_HEADING = "## Appendix: hook and record contract"
APPENDIX_REF_RE = re.compile(r"\bAppendix\s+(?P<id>[SG]\d+)\b")
APPENDIX_HEADING_RE = re.compile(r"^ {0,3}###\s+Appendix\s+(?P<id>[SG]\d+)\b")
APPENDIX_MENTION_RE = re.compile(r"\bthe appendix\b", re.IGNORECASE)

CLASS_AXES = ("language", "commit", "effect")
CLASS_VALUES = {
    "language": ("chat", "document", "none"),
    "commit": ("state-changing", "document-only", "none"),
    "effect": ("read-only", "artifact-only", "state-changing"),
}
CLASS_AXIS_BLOCKS = {
    "language": {
        "language-precedence-chat": "chat",
        "language-precedence-document": "document",
    },
    "commit": {
        "commit-selection-state-changing": "state-changing",
        "commit-selection-document-only": "document-only",
    },
}

BLOCK_ID_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
PACKAGE_NAME_RE = re.compile(r"^vibe-[a-z0-9]+(-[a-z0-9]+)*$")
VIBE_TOKEN_RE = re.compile(r"vibe-[a-z0-9-]+")
MARKER_LINE_RE = re.compile(r"^\s*<!--\s*" + MARKER_KEYWORD + r":(?P<rest>.*?)\s*-->\s*$")
BEGIN_ARGS_RE = re.compile(r"^(?P<id>\S+) source=(?P<source>\S+)$")
END_ARGS_RE = re.compile(r"^(?P<id>\S+)$")
BLOCK_ARGS_RE = re.compile(r"^(?P<id>\S+) dependents=(?P<deps>\S+)$")
ENDBLOCK_ARGS_RE = re.compile(r"^(?P<id>\S+)$")
CLASS_ARGS_RE = re.compile(
    r"^language=(?P<language>\S+) commit=(?P<commit>\S+) effect=(?P<effect>\S+)$"
)
HEADING_RE = re.compile(r"^ {0,3}#{1,6}(\s|$)")
FENCE_OPEN_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
FENCE_CLOSE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})\s*$")
BOLD_LEAD_RE = re.compile(r"^ {0,3}\*\*(?P<bold>[^\s*][^*]*)\*\*")
BULLET_RE = re.compile(r"^(?P<indent> *)-\s+(?P<text>.*)$")
NUMBERED_RE = re.compile(r"^(?P<indent>\s*)\d+\.\s+(?P<text>.*)$")
TABLE_ROW_RE = re.compile(r"^ {0,3}\|")
EXAMPLE_LINE_RE = re.compile(r"^ *(?:[-*+]\s+)?(?:\*\*)?Example:")
WORD_EDGE_CHARS = "*_`~[]()<>#\"'|.,;:!?/\\…—–-“”‘’„«»‹›"

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_FATAL = 2


class ContractError(Exception):
    """Raised for fatal, user-facing failures (missing source, refused paths, bad usage)."""


@dataclass(frozen=True)
class Finding:
    level: str  # "error" or "warning"
    message: str
    detail: str = ""

    def render(self) -> str:
        text = f"{self.level}: {self.message}"
        if self.detail:
            text += "\n" + self.detail.rstrip("\n")
        return text


@dataclass(frozen=True)
class SourceBlock:
    block_id: str
    dependents: tuple[str, ...]
    body: str
    line: int

    @property
    def kind(self) -> str:
        return "non-overridable" if self.block_id in NON_OVERRIDABLE_BLOCK_IDS else "consolidation"

    @property
    def closing_sentence(self) -> str:
        return APPLICABILITY_SENTENCE if self.kind == "non-overridable" else PRECEDENCE_SENTENCE

    @property
    def is_gate(self) -> bool:
        return self.block_id in GATE_BLOCK_IDS

    @property
    def is_schema(self) -> bool:
        return self.block_id in SCHEMA_BLOCK_IDS

    @property
    def lead_line(self) -> str:
        """The first non-empty body line, stripped of its line ending."""
        for line in self.body.splitlines():
            if line.strip():
                return line
        return ""

    @property
    def is_new_shape(self) -> bool:
        """True when the body opens with a bold lead line, the scannable block shape."""
        return BOLD_LEAD_RE.match(self.lead_line) is not None

    @property
    def last_content_line(self) -> str:
        lines = [line.strip() for line in self.body.splitlines() if line.strip()]
        return lines[-1] if lines else ""

    @property
    def ends_with_closing(self) -> bool:
        return self.last_content_line == self.closing_sentence


@dataclass
class BlockSite:
    package: str
    rel: str
    block_id: str
    begin_index: int
    end_index: int
    content: str
    source_attr: str
    state: str = ""  # pristine, identical, drifted (filled by the check)


@dataclass
class ClassLine:
    index: int
    raw: str
    values: dict[str, str] | None


@dataclass
class PackageFile:
    package: str
    path: Path
    rel: str
    lines: list[str]
    sites: list[BlockSite] = field(default_factory=list)
    class_lines: list[ClassLine] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


@dataclass
class CheckResult:
    blocks: list[SourceBlock]
    packages: dict[str, Path]
    tree: dict[str, list[PackageFile]]
    findings: list[Finding]

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.level == "warning"]


# --- CLI ---------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render, check, list, and audit shared-contract blocks vendored into vibe-* packages.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render = subparsers.add_parser("render", help="fill pristine marker pairs from the shared source")
    render.add_argument("--force", action="store_true", help="overwrite drifted blocks instead of refusing")
    render.add_argument("--package", default=None, help="limit rendering to this package name")
    add_root_option(render)
    add_source_option(render)

    check = subparsers.add_parser("check", help="verify the source and every rendered block")
    check.add_argument("--strict", action="store_true", help="missing markers and class-declaration faults are errors")
    check.add_argument("--package", default=None, help="limit package checks to this package name")
    add_root_option(check)
    add_source_option(check)

    audit = subparsers.add_parser("audit-names", help="report roster package names cited outside the router package")
    add_root_option(audit)

    listing = subparsers.add_parser("list", help="print the blocks the shared source declares")
    add_source_option(listing)

    measure = subparsers.add_parser("measure", help="print package and task sizes against the frozen manifest")
    measure.add_argument("--strict", action="store_true", help="exit 1 unless every task is below its baseline words")
    measure.add_argument(
        "--manifest",
        default=None,
        help=f"frozen task manifest (default: {DEFAULT_MANIFEST})",
    )
    add_root_option(measure)

    return parser.parse_args(argv)


def add_root_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=None,
        help=f"package root holding vibe-* directories; no path component may be a symlink (default: {DEFAULT_ROOT})",
    )


def add_source_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source",
        default=None,
        help=f"shared source file (default: {DEFAULT_SOURCE})",
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "render":
            return run_render(
                resolve_source(args.source),
                resolve_root(args.root),
                force=args.force,
                package_filter=args.package,
            )
        if args.command == "check":
            return run_check(
                resolve_source(args.source),
                resolve_root(args.root),
                strict=args.strict,
                package_filter=args.package,
            )
        if args.command == "audit-names":
            return run_audit_names(resolve_root(args.root))
        if args.command == "list":
            return run_list(resolve_source(args.source))
        if args.command == "measure":
            return run_measure(
                resolve_root(args.root),
                resolve_manifest(args.manifest),
                strict=args.strict,
            )
    except ContractError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FATAL
    raise ContractError(f"unknown command: {args.command}")


# --- Paths -------------------------------------------------------------------


def resolve_root(root_arg: str | os.PathLike[str] | None) -> Path:
    candidate = DEFAULT_ROOT if root_arg is None else Path(root_arg)
    refuse_symlink_components(candidate, "root")
    if not candidate.exists():
        raise ContractError(f"root does not exist: {candidate.as_posix()}")
    if not candidate.is_dir():
        raise ContractError(f"root is not a directory: {candidate.as_posix()}")
    return candidate.resolve()


def resolve_source(source_arg: str | os.PathLike[str] | None) -> Path:
    candidate = DEFAULT_SOURCE if source_arg is None else Path(source_arg)
    if candidate.is_symlink():
        raise ContractError(f"shared source must not be a symlink: {candidate.as_posix()}")
    if not candidate.exists():
        raise ContractError(f"shared source does not exist: {candidate.as_posix()}")
    if not candidate.is_file():
        raise ContractError(f"shared source is not a regular file: {candidate.as_posix()}")
    return candidate.resolve()


def ensure_within(path: Path, root: Path) -> None:
    """Refuse any candidate path whose resolved form is not under the resolved root."""
    resolved_root = root.resolve()
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise ContractError(
            f"path resolves outside the root {resolved_root.as_posix()}: {path.as_posix()}"
        ) from exc


def refuse_symlink(path: Path, label: str, root: Path | None = None) -> None:
    """Refuse a symlinked entry; when a root is given, also report whether it escapes the root."""
    if not path.is_symlink():
        return
    message = f"{label} is a symlink: {path.as_posix()}"
    if root is not None:
        try:
            ensure_within(path, root)
        except ContractError as exc:
            message = f"{label} is a symlink and {exc}"
    raise ContractError(message)


def refuse_symlink_components(path: Path, label: str) -> None:
    """Refuse when any component of the path, walked without following links, is a symlink."""
    absolute = path if path.is_absolute() else Path.cwd() / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        if part == ".":
            continue
        if part == "..":
            current = current.parent
            continue
        current = current / part
        if current.is_symlink():
            raise ContractError(f"{label} has a symlinked component: {current.as_posix()}")


def relative_display(path: Path, root: Path) -> str:
    try:
        return f"{root.name}/{path.resolve().relative_to(root).as_posix()}"
    except ValueError:
        return path.as_posix()


def discover_packages(root: Path) -> dict[str, Path]:
    """Return every vibe-* package directory under the root, keyed by package name."""
    packages: dict[str, Path] = {}
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if not entry.name.startswith(PACKAGE_PREFIX):
            continue
        refuse_symlink(entry, "package directory", root)
        if not entry.is_dir():
            continue
        if not PACKAGE_NAME_RE.match(entry.name):
            raise ContractError(f"invalid package directory name: {relative_display(entry, root)}")
        ensure_within(entry, root)
        packages[entry.name] = entry
    return packages


def walk_package_files(package_dir: Path, root: Path) -> list[Path]:
    """Return every regular file under the package, refusing symlinks and path escape."""
    files: list[Path] = []
    for current, dir_names, file_names in os.walk(package_dir, topdown=True, followlinks=False):
        current_path = Path(current)
        kept: list[str] = []
        for dir_name in sorted(dir_names):
            path = current_path / dir_name
            refuse_symlink(path, "directory", root)
            if dir_name in IGNORED_DIR_NAMES:
                continue
            ensure_within(path, root)
            kept.append(dir_name)
        dir_names[:] = kept
        for file_name in sorted(file_names):
            path = current_path / file_name
            refuse_symlink(path, "file", root)
            if not stat.S_ISREG(path.lstat().st_mode):
                continue
            ensure_within(path, root)
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(package_dir).as_posix())


# --- Markdown helpers --------------------------------------------------------


def fenced_line_indexes(lines: list[str]) -> set[int]:
    """Indexes of the lines inside (and including) correctly matched Markdown code fences.

    An opening fence without a matching closer is ordinary text, so an unclosed fence
    never hides the markers that follow it.
    """
    fenced: set[int] = set()
    index = 0
    total = len(lines)
    while index < total:
        opening = FENCE_OPEN_RE.match(lines[index].rstrip("\r\n"))
        if opening is None:
            index += 1
            continue
        fence = opening.group("fence")
        if fence[0] == "`" and "`" in opening.group("info"):
            index += 1
            continue
        closer = None
        for candidate in range(index + 1, total):
            closing = FENCE_CLOSE_RE.match(lines[candidate].rstrip("\r\n"))
            if closing and closing.group("fence")[0] == fence[0] and len(closing.group("fence")) >= len(fence):
                closer = candidate
                break
        if closer is None:
            index += 1
            continue
        fenced.update(range(index, closer + 1))
        index = closer + 1
    return fenced


def count_words(text: str) -> int:
    """Count whitespace tokens, stripping Markdown markers and dropping punctuation-only tokens."""
    total = 0
    for token in text.split():
        cleaned = token.strip(WORD_EDGE_CHARS)
        if cleaned and any(char.isalnum() for char in cleaned):
            total += 1
    return total


def wc_counts(text: str) -> tuple[int, int]:
    """Return ``(lines, words)`` with ``wc -l`` and ``wc -w`` semantics."""
    return text.count("\n"), len(text.split())


@dataclass
class BodySegment:
    """One structural unit of a block body: the lead, a bullet, or a prose paragraph."""

    kind: str  # lead, bullet, sub-bullet, paragraph, example
    offset: int  # zero-based line offset inside the block body
    text: str


def trailing_boilerplate_offsets(lines: list[str]) -> set[int]:
    """The offset of a trailing precedence or applicability sentence, when the body has one.

    A block mid-migration may keep its closing sentence while already carrying a bold
    lead; that tail is not the block's own prose and is excluded from every shape count.
    """
    for offset in range(len(lines) - 1, -1, -1):
        stripped = lines[offset].strip()
        if not stripped:
            continue
        return {offset} if stripped in BOILERPLATE_SENTENCES else set()
    return set()


def list_item(line: str) -> re.Match[str] | None:
    """Match a ``- `` bullet or a ``1. `` numbered item; both are list items of one kind."""
    return BULLET_RE.match(line) or NUMBERED_RE.match(line)


def segment_block_body(block: SourceBlock) -> list[BodySegment]:
    """Split a block body into lead, bullets, sub-bullets, prose paragraphs, and examples.

    A numbered item counts as a bullet, so an ordered precedence list is measured against
    the same caps as a dashed list; an indented item of either kind is a sub-bullet.

    Fenced code and Markdown table rows separate segments and carry no prose of their own,
    so a table or a JSON example never reads as an over-long paragraph.
    """
    raw_lines = block.body.splitlines(keepends=True)
    fenced = fenced_line_indexes(raw_lines)
    lines = [line.rstrip("\r\n") for line in raw_lines]
    skipped = trailing_boilerplate_offsets(lines)
    segments: list[BodySegment] = []
    current: BodySegment | None = None

    for offset, line in enumerate(lines):
        if offset in skipped or offset in fenced or not line.strip() or TABLE_ROW_RE.match(line):
            current = None
            continue
        stripped = line.strip()
        if EXAMPLE_LINE_RE.match(line):
            segments.append(BodySegment("example", offset, stripped))
            current = None
            continue
        bullet = list_item(line)
        if bullet is not None:
            kind = "bullet" if not bullet.group("indent") else "sub-bullet"
            current = BodySegment(kind, offset, bullet.group("text").strip())
            segments.append(current)
            continue
        if current is not None:
            # A prose line directly under an open segment continues it: an indented bullet
            # continuation stays part of its bullet, and a wrapped paragraph stays one paragraph.
            current.text += " " + stripped
            continue
        kind = "lead" if not segments and BOLD_LEAD_RE.match(line) else "paragraph"
        current = BodySegment(kind, offset, stripped)
        segments.append(current)
    return segments


def block_word_total(block: SourceBlock) -> int:
    """Every word in the body except example lines and a trailing closing sentence.

    A list marker is not a word: a ``- `` drops out of ``count_words`` on its own, and a
    numbered item's ordinal is dropped here, so renumbering a list never changes a total.
    """
    lines = [line.rstrip("\r\n") for line in block.body.splitlines(keepends=True)]
    skipped = trailing_boilerplate_offsets(lines)
    total = 0
    for offset, line in enumerate(lines):
        if offset in skipped or EXAMPLE_LINE_RE.match(line):
            continue
        item = list_item(line)
        total += count_words(item.group("text") if item is not None else line)
    return total


def lead_starter(text: str) -> str:
    for token in text.split():
        cleaned = token.strip(WORD_EDGE_CHARS)
        if cleaned:
            return cleaned
    return ""


def lead_opens_imperatively(word: str) -> bool:
    """True only for a listed opener: ``Never``, ``Only``, or a listed imperative verb.

    The comparison is case-sensitive on the capitalised form, so a mid-sentence or
    lowercased word never passes. An unlisted imperative is a finding whose fix is to add
    the verb to ``IMPERATIVE_LEAD_VERBS``.
    """
    return word in IMPERATIVE_LEAD_WORDS or word in IMPERATIVE_LEAD_VERBS


def check_block_shape(block: SourceBlock, label: str, level: str) -> list[Finding]:
    """Shape findings for one scannable block; the caller decides warning or error."""
    findings: list[Finding] = []

    def where(offset: int) -> str:
        return f"{label}:{block.line + 1 + offset}: block {block.block_id}"

    segments = segment_block_body(block)
    bullet_cap = GATE_BULLET_WORD_CAP if block.is_gate else CONSOLIDATION_BULLET_WORD_CAP
    bullet_offsets = [index for index, segment in enumerate(segments) if segment.kind in ("bullet", "sub-bullet")]
    last_bullet = bullet_offsets[-1] if bullet_offsets else -1
    trailing: list[tuple[BodySegment, int]] = []
    examples: list[BodySegment] = []

    for index, segment in enumerate(segments):
        words = count_words(segment.text)
        if segment.kind == "lead":
            if words > LEAD_WORD_CAP:
                findings.append(Finding(level, f"{where(segment.offset)}: bold lead is {words} words (cap {LEAD_WORD_CAP})"))
            starter = lead_starter(segment.text)
            if starter and not lead_opens_imperatively(starter):
                findings.append(
                    Finding(
                        level,
                        f"{where(segment.offset)}: bold lead does not open with an imperative: {starter!r} "
                        "(use 'Never', 'Only', or a verb listed in IMPERATIVE_LEAD_VERBS)",
                    )
                )
        elif segment.kind == "bullet":
            if words > bullet_cap:
                findings.append(Finding(level, f"{where(segment.offset)}: bullet is {words} words (cap {bullet_cap})"))
        elif segment.kind == "sub-bullet":
            if words > SUB_BULLET_WORD_CAP:
                findings.append(
                    Finding(level, f"{where(segment.offset)}: sub-bullet is {words} words (cap {SUB_BULLET_WORD_CAP})")
                )
        elif segment.kind == "example":
            examples.append(segment)
        else:
            if words > PARAGRAPH_WORD_CAP:
                findings.append(
                    Finding(level, f"{where(segment.offset)}: paragraph is {words} words (cap {PARAGRAPH_WORD_CAP})")
                )
            if last_bullet >= 0 and index > last_bullet:
                trailing.append((segment, words))

    for extra, _words in trailing[1:]:
        findings.append(
            Finding(
                level,
                f"{where(extra.offset)}: more than one prose paragraph after the bullets "
                "(at most one exception line is allowed)",
            )
        )
    for segment, words in trailing:
        if words > EXCEPTION_WORD_CAP:
            findings.append(
                Finding(level, f"{where(segment.offset)}: exception line is {words} words (cap {EXCEPTION_WORD_CAP})")
            )
    for extra in examples[EXAMPLE_LINE_CAP:]:
        findings.append(
            Finding(level, f"{where(extra.offset)}: more than {EXAMPLE_LINE_CAP} 'Example:' lines in the block")
        )
    if block.is_gate:
        total = block_word_total(block)
        if total > GATE_BLOCK_WORD_CAP:
            findings.append(
                Finding(level, f"{label}:{block.line}: block {block.block_id}: gate block is {total} words (cap {GATE_BLOCK_WORD_CAP})")
            )
    if block.is_schema:
        total = block_word_total(block)
        if total > SCHEMA_BLOCK_WORD_CAP:
            findings.append(
                Finding(
                    level,
                    f"{label}:{block.line}: block {block.block_id}: schema block is {total} words "
                    f"(cap {SCHEMA_BLOCK_WORD_CAP})",
                )
            )
    if block.block_id in NEGATIVE_LINE_BLOCK_IDS and not any(
        segment.kind in ("lead", "bullet", "sub-bullet") and NEGATIVE_LINE_RE.match(segment.text)
        for segment in segments
    ):
        findings.append(
            Finding(
                level,
                f"{label}:{block.line}: block {block.block_id}: no lead, bullet, or sub-bullet opens with "
                "'Never' or 'Only'; the pre-rewrite block stated a negative rule and one must survive",
            )
        )
    return findings


def source_closing_mode(blocks: list[SourceBlock]) -> str:
    """``per-package`` once any scannable block has dropped its closing sentence."""
    for block in blocks:
        if block.is_new_shape and not block.ends_with_closing:
            return CLOSING_PER_PACKAGE
    return CLOSING_PER_BLOCK


def closing_block_for(package: str, block_map: dict[str, SourceBlock]) -> SourceBlock:
    """The synthetic per-package closing block: precedence, plus applicability when owed.

    Each sentence names the blocks it binds and where they sit, so the body is one line for
    a package carrying only consolidation blocks and two for a package that also carries a
    gate or schema block. No third line explains the first two.
    """
    lines = [CLOSING_PRECEDENCE_SENTENCE]
    carries_non_overridable = any(
        package in block_map[block_id].dependents
        for block_id in sorted(NON_OVERRIDABLE_BLOCK_IDS)
        if block_id in block_map
    )
    if carries_non_overridable:
        lines.append(CLOSING_APPLICABILITY_SENTENCE)
    body = "".join(line + "\n" for line in lines)
    return SourceBlock(CLOSING_BLOCK_ID, (package,), body, 0)


def block_for(block_map: dict[str, SourceBlock], package: str, block_id: str) -> SourceBlock | None:
    if block_id == CLOSING_BLOCK_ID:
        return closing_block_for(package, block_map)
    return block_map.get(block_id)


def validate_block_id(block_id: str) -> str | None:
    if block_id.startswith(PACKAGE_PREFIX):
        return f"block id must not start with {PACKAGE_PREFIX!r}: {block_id}"
    if not BLOCK_ID_RE.match(block_id):
        return f"invalid block id: {block_id}"
    return None


def split_marker(line: str) -> tuple[str, str] | None:
    match = MARKER_LINE_RE.match(line.rstrip("\r\n"))
    if match is None:
        return None
    rest = match.group("rest")
    keyword, _, args = rest.partition(" ")
    return keyword, args.strip()


def roster_tokens(line: str, packages: dict[str, Path], own_name: str | None = None) -> list[tuple[int, str]]:
    """Return ``(column, token)`` for every ``vibe-[a-z0-9-]+`` token equal to a discovered package name.

    Tokens are the greedy grep-style matches of ``VIBE_TOKEN_RE`` (so ``vibe-coding-extra`` is
    one token and never equals ``vibe-coding``); comparison is exact and case-sensitive; a
    token equal to ``own_name`` is skipped. Non-roster strings such as ``vibe-contract`` or
    ``vibe-sessions`` never match. Columns are 1-based.
    """
    hits: list[tuple[int, str]] = []
    for match in VIBE_TOKEN_RE.finditer(line):
        token = match.group(0)
        if token == own_name or token not in packages:
            continue
        hits.append((match.start() + 1, token))
    return hits


# --- Source parsing ----------------------------------------------------------


def read_source_text(source: Path) -> str:
    try:
        return source.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ContractError(f"cannot read shared source {source.as_posix()}: {exc}") from exc


def parse_source(source: Path) -> tuple[list[SourceBlock], list[Finding]]:
    text = read_source_text(source)
    lines = text.splitlines(keepends=True)
    fenced = fenced_line_indexes(lines)
    blocks: list[SourceBlock] = []
    findings: list[Finding] = []
    seen: dict[str, int] = {}
    open_block: tuple[str, tuple[str, ...], int] | None = None
    label = source.name

    for index, raw in enumerate(lines):
        if index in fenced:
            continue
        marker = split_marker(raw)
        if marker is None:
            continue
        keyword, args = marker
        line_no = index + 1
        if keyword == "block":
            match = BLOCK_ARGS_RE.match(args)
            if match is None:
                findings.append(Finding("error", f"{label}:{line_no}: malformed block marker: {raw.strip()}"))
                continue
            block_id = match.group("id")
            problem = validate_block_id(block_id)
            if problem:
                findings.append(Finding("error", f"{label}:{line_no}: {problem}"))
            dependents = parse_dependents(match.group("deps"), label, line_no, findings)
            if open_block is not None:
                findings.append(
                    Finding("error", f"{label}:{line_no}: nested block marker {block_id} inside {open_block[0]}")
                )
                continue
            if block_id in seen:
                findings.append(
                    Finding("error", f"{label}:{line_no}: duplicate block id {block_id} (first at line {seen[block_id]})")
                )
            seen.setdefault(block_id, line_no)
            open_block = (block_id, dependents, index)
        elif keyword == "endblock":
            match = ENDBLOCK_ARGS_RE.match(args)
            if match is None:
                findings.append(Finding("error", f"{label}:{line_no}: malformed endblock marker: {raw.strip()}"))
                continue
            block_id = match.group("id")
            if open_block is None:
                findings.append(Finding("error", f"{label}:{line_no}: unpaired endblock marker {block_id}"))
                continue
            if block_id != open_block[0]:
                findings.append(
                    Finding("error", f"{label}:{line_no}: endblock {block_id} does not close block {open_block[0]}")
                )
                open_block = None
                continue
            body = "".join(lines[open_block[2] + 1 : index])
            blocks.append(SourceBlock(block_id, open_block[1], body, open_block[2] + 1))
            open_block = None
        else:
            findings.append(
                Finding("error", f"{label}:{line_no}: unknown source marker keyword {keyword!r}: {raw.strip()}")
            )
    if open_block is not None:
        findings.append(Finding("error", f"{label}:{open_block[2] + 1}: block {open_block[0]} is never closed"))
    return blocks, findings


def parse_dependents(text: str, label: str, line_no: int, findings: list[Finding]) -> tuple[str, ...]:
    names: list[str] = []
    for name in text.split(","):
        if not PACKAGE_NAME_RE.match(name):
            findings.append(Finding("error", f"{label}:{line_no}: invalid dependent package name: {name!r}"))
            continue
        if name in names:
            findings.append(Finding("error", f"{label}:{line_no}: duplicate dependent {name}"))
            continue
        names.append(name)
    return tuple(names)


def check_source_blocks(
    blocks: list[SourceBlock], packages: dict[str, Path], label: str, *, strict: bool = False
) -> list[Finding]:
    findings: list[Finding] = []
    for block in blocks:
        where = f"{label}:{block.line}: block {block.block_id}"
        if block.block_id == CLOSING_BLOCK_ID:
            findings.append(
                Finding("error", f"{where}: block id {CLOSING_BLOCK_ID!r} is reserved for the per-package closing block")
            )
        for dependent in block.dependents:
            if dependent not in packages:
                findings.append(Finding("error", f"{where}: dependent is not an existing package: {dependent}"))
        if not block.body.strip():
            findings.append(Finding("error", f"{where}: block body is empty"))
            continue
        body_lines = block.body.splitlines(keepends=True)
        fenced = fenced_line_indexes(body_lines)
        for offset, raw_line in enumerate(body_lines):
            raw = raw_line.rstrip("\r\n")
            line_no = block.line + 1 + offset
            if offset not in fenced and HEADING_RE.match(raw):
                findings.append(
                    Finding("error", f"{label}:{line_no}: block {block.block_id} contains a Markdown heading: {raw.strip()}")
                )
            for _column, token in roster_tokens(raw, packages):
                findings.append(
                    Finding("error", f"{label}:{line_no}: block {block.block_id} names a vibe-* specialist: {token}")
                )
        if not block.is_new_shape:
            if not block.ends_with_closing:
                findings.append(
                    Finding(
                        "error",
                        f"{where}: {block.kind} block does not end with its closing sentence: {block.closing_sentence!r}",
                    )
                )
            if not strict:
                findings.append(
                    Finding(
                        "warning",
                        f"{where}: legacy-shape block (no bold lead line); the shape checks do not apply to it",
                    )
                )
            continue
        wrong_closing = next(
            (sentence for sentence in BOILERPLATE_SENTENCES if sentence != block.closing_sentence),
            "",
        )
        if block.last_content_line == wrong_closing:
            findings.append(
                Finding(
                    "error",
                    f"{where}: {block.kind} block ends with the other closing sentence; "
                    f"drop it or use {block.closing_sentence!r}",
                )
            )
        findings.extend(check_block_shape(block, label, "error" if strict else "warning"))
    return findings


def check_appendix_references(text: str, blocks: list[SourceBlock], label: str, level: str) -> list[Finding]:
    """Every appendix citation resolves, and a block sends the reader only to a real section.

    ``Appendix S<n>`` and ``Appendix G<n>`` are checked source-wide — preamble, blocks, and
    the appendix itself — against the ``###`` headings the appendix declares. A block that
    tells the reader to consult "the appendix" needs the appendix section heading, because
    the block is what a package renders and the reader follows it out of the package.
    """
    findings: list[Finding] = []
    lines = [line.rstrip("\r\n") for line in text.splitlines(keepends=True)]
    fenced = fenced_line_indexes(text.splitlines(keepends=True))
    defined: set[str] = set()
    has_section = False
    for index, line in enumerate(lines):
        if index in fenced:
            continue
        heading = APPENDIX_HEADING_RE.match(line)
        if heading is not None:
            defined.add(heading.group("id"))
        if line.strip() == APPENDIX_SECTION_HEADING:
            has_section = True
    for index, line in enumerate(lines):
        if index in fenced or APPENDIX_HEADING_RE.match(line):
            continue
        for match in APPENDIX_REF_RE.finditer(line):
            name = match.group("id")
            if name not in defined:
                findings.append(
                    Finding(
                        level,
                        f"{label}:{index + 1}: Appendix {name} is cited but the source declares no "
                        f"'### Appendix {name}' heading",
                    )
                )
    if not has_section:
        for block in blocks:
            for segment in segment_block_body(block):
                if segment.kind in ("lead", "bullet", "sub-bullet", "paragraph") and APPENDIX_MENTION_RE.search(
                    segment.text
                ):
                    findings.append(
                        Finding(
                            level,
                            f"{label}:{block.line + 1 + segment.offset}: block {block.block_id} sends the reader to "
                            f"the appendix, but the source has no '{APPENDIX_SECTION_HEADING}' heading",
                        )
                    )
    return findings


# --- Package parsing ---------------------------------------------------------


def parse_package_file(package: str, path: Path, rel: str) -> PackageFile:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return PackageFile(package, path, rel, [])
    except OSError as exc:
        raise ContractError(f"cannot read {rel}: {exc}") from exc
    package_file = PackageFile(package, path, rel, text.splitlines(keepends=True))
    findings = package_file.findings
    fenced = fenced_line_indexes(package_file.lines)
    open_site: tuple[str, int, str] | None = None

    for index, raw in enumerate(package_file.lines):
        if index in fenced:
            continue
        marker = split_marker(raw)
        if marker is None:
            continue
        keyword, args = marker
        line_no = index + 1
        if keyword == "begin":
            match = BEGIN_ARGS_RE.match(args)
            if match is None:
                findings.append(
                    Finding(
                        "error",
                        f"{rel}:{line_no}: malformed begin marker (expected "
                        f"'<!-- shared-contract:begin <id> source={SOURCE_CITATION} -->'): {raw.strip()}",
                    )
                )
                continue
            block_id = match.group("id")
            problem = validate_block_id(block_id)
            if problem:
                findings.append(Finding("error", f"{rel}:{line_no}: {problem}"))
                continue
            if open_site is not None:
                findings.append(
                    Finding("error", f"{rel}:{line_no}: nested begin marker {block_id} inside open block {open_site[0]}")
                )
                continue
            open_site = (block_id, index, match.group("source"))
        elif keyword == "end":
            match = END_ARGS_RE.match(args)
            if match is None:
                findings.append(Finding("error", f"{rel}:{line_no}: malformed end marker: {raw.strip()}"))
                continue
            block_id = match.group("id")
            if open_site is None:
                findings.append(Finding("error", f"{rel}:{line_no}: unpaired end marker {block_id}"))
                continue
            if block_id != open_site[0]:
                findings.append(
                    Finding("error", f"{rel}:{line_no}: end marker {block_id} does not close begin marker {open_site[0]}")
                )
                open_site = None
                continue
            content = "".join(package_file.lines[open_site[1] + 1 : index])
            package_file.sites.append(
                BlockSite(package, rel, block_id, open_site[1], index, content, open_site[2])
            )
            open_site = None
        elif keyword == "class":
            if open_site is not None:
                findings.append(
                    Finding("error", f"{rel}:{line_no}: class declaration inside open block {open_site[0]}")
                )
                continue
            package_file.class_lines.append(ClassLine(index, raw.strip(), parse_class_values(args)))
        else:
            findings.append(
                Finding("error", f"{rel}:{line_no}: unknown marker keyword {keyword!r}: {raw.strip()}")
            )
    if open_site is not None:
        findings.append(
            Finding("error", f"{rel}:{open_site[1] + 1}: begin marker {open_site[0]} is never closed")
        )
    return package_file


def parse_class_values(args: str) -> dict[str, str] | None:
    match = CLASS_ARGS_RE.match(args)
    if match is None:
        return None
    values = {axis: match.group(axis) for axis in CLASS_AXES}
    for axis, value in values.items():
        if value not in CLASS_VALUES[axis]:
            return None
    return values


def scan_packages(root: Path, packages: dict[str, Path], names: list[str]) -> dict[str, list[PackageFile]]:
    tree: dict[str, list[PackageFile]] = {}
    for name in names:
        package_dir = packages[name]
        files: list[PackageFile] = []
        for path in walk_package_files(package_dir, root):
            if path.suffix != ".md":
                continue
            files.append(parse_package_file(name, path, relative_display(path, root)))
        tree[name] = files
    return tree


# --- Checks ------------------------------------------------------------------


def classify_site(content: str, body: str) -> str:
    if content == body:
        return "identical"
    if not content.strip():
        return "pristine"
    return "drifted"


def drift_diff(site: BlockSite, block: SourceBlock) -> str:
    return "".join(
        difflib.unified_diff(
            block.body.splitlines(keepends=True),
            site.content.splitlines(keepends=True),
            fromfile=f"source:{block.block_id}",
            tofile=f"{site.rel}:{block.block_id}",
        )
    )


def single_class_line(files: list[PackageFile]) -> tuple[PackageFile, ClassLine] | None:
    entries = [(package_file, class_line) for package_file in files for class_line in package_file.class_lines]
    return entries[0] if len(entries) == 1 else None


def sentence_line_hits(content: str, sentence: str) -> list[int]:
    """Zero-based offsets of the content lines carrying ``sentence``, prefixed or not."""
    return [offset for offset, line in enumerate(content.splitlines()) if sentence in line]


def check_closing_sentence_counts(site: BlockSite, block: SourceBlock) -> list[Finding]:
    """Each closing sentence the package owes appears exactly once in its closing block.

    The two legacy per-block sentences are owed by no package and must not appear here.
    """
    findings: list[Finding] = []
    where = f"{site.rel}:{site.begin_index + 1}"
    owed = [line.strip() for line in block.body.splitlines() if line.strip()]
    for sentence in BOILERPLATE_SENTENCES:
        expected = 1 if sentence in owed else 0
        found = len(sentence_line_hits(site.content, sentence))
        if found != expected:
            findings.append(
                Finding(
                    "error",
                    f"{where}: block {CLOSING_BLOCK_ID} renders {BOILERPLATE_SENTENCE_NAMES[sentence]} "
                    f"{found} time(s), expected {expected}",
                )
            )
    return findings


def check_stray_closing_sentences(site: BlockSite, block: SourceBlock) -> list[Finding]:
    """No generated block outside the closing block carries a closing sentence.

    A legacy-shape block mid-migration still ends with its own tail; that one sanctioned
    line is skipped so the check reports only sentences rendered a second time.
    """
    lines = site.content.splitlines()
    tail = -1
    if block.ends_with_closing:
        for offset in range(len(lines) - 1, -1, -1):
            if lines[offset].strip():
                tail = offset
                break
    findings: list[Finding] = []
    for sentence in BOILERPLATE_SENTENCES:
        for offset in sentence_line_hits(site.content, sentence):
            if offset == tail:
                continue
            findings.append(
                Finding(
                    "error",
                    f"{site.rel}:{site.begin_index + 2 + offset}: block {site.block_id} carries "
                    f"{BOILERPLATE_SENTENCE_NAMES[sentence]}; the package renders it once, in its "
                    f"{CLOSING_BLOCK_ID} block",
                )
            )
    return findings


def check_closing_site(
    package: str,
    package_file: PackageFile,
    site: BlockSite,
    class_entry: tuple[PackageFile, ClassLine] | None,
    closing_mode: str,
) -> list[Finding]:
    """Placement and admissibility of one package's synthetic closing block."""
    where = f"{site.rel}:{site.begin_index + 1}"
    if closing_mode != CLOSING_PER_PACKAGE:
        return [
            Finding(
                "error",
                f"{where}: package {package} carries a {CLOSING_BLOCK_ID} block while every source block "
                "still ends with its own closing sentence",
            )
        ]
    if class_entry is None:
        return []
    class_file, class_line = class_entry
    if class_file is package_file and class_line.index + 1 == site.begin_index:
        return []
    return [
        Finding(
            "error",
            f"{where}: the {CLOSING_BLOCK_ID} block must be the line directly below the class declaration "
            f"({class_file.rel}:{class_line.index + 1}) with no blank line between them",
        )
    ]


def check_packages(
    blocks: list[SourceBlock],
    tree: dict[str, list[PackageFile]],
    *,
    strict: bool,
    report_states: bool = True,
) -> list[Finding]:
    block_map = {block.block_id: block for block in blocks}
    closing_mode = source_closing_mode(blocks)
    findings: list[Finding] = []
    for package, files in tree.items():
        seen: dict[str, str] = {}
        class_entry = single_class_line(files)
        for package_file in files:
            findings.extend(package_file.findings)
            for site in package_file.sites:
                where = f"{site.rel}:{site.begin_index + 1}"
                if site.block_id in seen:
                    findings.append(
                        Finding(
                            "error",
                            f"{where}: duplicate block {site.block_id} in package {package} (first in {seen[site.block_id]})",
                        )
                    )
                    continue
                seen[site.block_id] = site.rel
                block = block_for(block_map, package, site.block_id)
                if block is None:
                    findings.append(Finding("error", f"{where}: unknown block id {site.block_id}"))
                    continue
                if site.block_id == CLOSING_BLOCK_ID:
                    findings.extend(check_closing_site(package, package_file, site, class_entry, closing_mode))
                elif package not in block.dependents:
                    findings.append(
                        Finding("error", f"{where}: package {package} is not a listed dependent of block {site.block_id}")
                    )
                if site.source_attr != SOURCE_CITATION:
                    findings.append(
                        Finding(
                            "error",
                            f"{where}: begin marker source must be {SOURCE_CITATION}: {site.source_attr}",
                        )
                    )
                if site.block_id == CLOSING_BLOCK_ID and closing_mode != CLOSING_PER_PACKAGE:
                    continue
                site.state = classify_site(site.content, block.body)
                if not report_states:
                    continue
                if closing_mode == CLOSING_PER_PACKAGE and site.state != "pristine":
                    if site.block_id == CLOSING_BLOCK_ID:
                        findings.extend(check_closing_sentence_counts(site, block))
                    else:
                        findings.extend(check_stray_closing_sentences(site, block))
                if site.state == "drifted":
                    findings.append(
                        Finding("error", f"{where}: block {site.block_id} drifted from the source", drift_diff(site, block))
                    )
                elif site.state == "pristine":
                    findings.append(
                        Finding("error", f"{where}: block {site.block_id} is pristine (not rendered)")
                    )
        for block in blocks:
            if package in block.dependents and block.block_id not in seen:
                level = "error" if strict else "warning"
                findings.append(
                    Finding(level, f"package {package} is a listed dependent of block {block.block_id} but has no marker")
                )
        if closing_mode == CLOSING_PER_PACKAGE and CLOSING_BLOCK_ID not in seen:
            level = "error" if strict else "warning"
            findings.append(
                Finding(
                    level,
                    f"package {package} has no {CLOSING_BLOCK_ID} block; the shared source closes its blocks "
                    "once per package",
                )
            )
        if strict:
            findings.extend(check_class_declaration(package, files, block_map))
    return findings


def check_class_declaration(
    package: str, files: list[PackageFile], block_map: dict[str, SourceBlock]
) -> list[Finding]:
    findings: list[Finding] = []
    entries = [(package_file, class_line) for package_file in files for class_line in package_file.class_lines]
    if not entries:
        return [Finding("error", f"package {package} has no class declaration")]
    if len(entries) > 1:
        places = ", ".join(f"{package_file.rel}:{class_line.index + 1}" for package_file, class_line in entries)
        return [Finding("error", f"package {package} has duplicate class declarations: {places}")]
    package_file, class_line = entries[0]
    where = f"{package_file.rel}:{class_line.index + 1}"
    if class_line.values is None:
        return [Finding("error", f"{where}: invalid class declaration: {class_line.raw}")]

    first: tuple[PackageFile, BlockSite] | None = None
    for candidate in files:
        if candidate.sites:
            first = (candidate, candidate.sites[0])
            break
    if first is None:
        findings.append(Finding("error", f"{where}: class declaration without a generated block in package {package}"))
    else:
        first_file, first_site = first
        adjacent = first_file is package_file and class_line.index + 1 == first_site.begin_index
        if not adjacent:
            findings.append(
                Finding(
                    "error",
                    f"{where}: class declaration is not immediately above the first generated block "
                    f"({first_file.rel}:{first_site.begin_index + 1}); it must be the line directly above it",
                )
            )

    for axis, mapping in CLASS_AXIS_BLOCKS.items():
        listed = [
            value
            for block_id, value in mapping.items()
            if block_id in block_map and package in block_map[block_id].dependents
        ]
        if len(listed) > 1:
            findings.append(
                Finding("error", f"package {package} is a dependent of mutually exclusive {axis} blocks")
            )
            continue
        expected = listed[0] if listed else "none"
        declared = class_line.values[axis]
        if declared != expected:
            findings.append(
                Finding(
                    "error",
                    f"{where}: class declaration {axis}={declared} conflicts with the dependents lists "
                    f"(expected {axis}={expected})",
                )
            )
    return findings


def analyze(
    source: Path,
    root: Path,
    *,
    strict: bool,
    package_filter: str | None,
    report_states: bool = True,
) -> CheckResult:
    blocks, findings = parse_source(source)
    packages = discover_packages(root)
    findings.extend(check_source_blocks(blocks, packages, source.name, strict=strict))
    findings.extend(
        check_appendix_references(
            read_source_text(source), blocks, source.name, "error" if strict else "warning"
        )
    )
    if package_filter is not None and package_filter not in packages:
        raise ContractError(f"unknown package: {package_filter}")
    names = [package_filter] if package_filter else sorted(packages)
    tree = scan_packages(root, packages, names)
    findings.extend(check_packages(blocks, tree, strict=strict, report_states=report_states))
    return CheckResult(blocks, packages, tree, findings)


def print_findings(findings: list[Finding]) -> None:
    for finding in findings:
        print(finding.render())


# --- Commands ----------------------------------------------------------------


def run_check(source: Path, root: Path, *, strict: bool, package_filter: str | None) -> int:
    result = analyze(source, root, strict=strict, package_filter=package_filter)
    print_findings(result.findings)
    scope = f"package {package_filter}" if package_filter else f"{len(result.tree)} package(s)"
    mode = "strict" if strict else "non-strict"
    print(
        f"check ({mode}, {scope}): {len(result.errors)} error(s), {len(result.warnings)} warning(s)"
    )
    return EXIT_FINDINGS if result.errors else EXIT_OK


def run_render(source: Path, root: Path, *, force: bool, package_filter: str | None = None) -> int:
    result = analyze(source, root, strict=False, package_filter=package_filter, report_states=False)
    if result.errors:
        print_findings(result.errors)
        print(f"render refused: {len(result.errors)} error(s)")
        return EXIT_FINDINGS
    block_map = {block.block_id: block for block in result.blocks}

    refusals: list[Finding] = []
    planned: list[tuple[PackageFile, list[BlockSite]]] = []
    for files in result.tree.values():
        for package_file in files:
            changed: list[BlockSite] = []
            for site in package_file.sites:
                block = block_for(block_map, package_file.package, site.block_id)
                if block is None:
                    continue
                if site.state == "pristine":
                    changed.append(site)
                elif site.state == "drifted":
                    if force:
                        changed.append(site)
                    else:
                        refusals.append(
                            Finding(
                                "error",
                                f"{site.rel}:{site.begin_index + 1}: block {site.block_id} drifted; "
                                "re-run with --force to overwrite",
                                drift_diff(site, block),
                            )
                        )
            if changed:
                planned.append((package_file, changed))
    if refusals:
        print_findings(refusals)
        print(f"render refused: {len(refusals)} drifted block(s)")
        return EXIT_FINDINGS

    for package_file, changed in planned:
        new_text = rebuild_file(package_file, block_map)
        try:
            atomic_write(package_file.path, new_text, root)
        except OSError as exc:
            raise ContractError(f"failed to write {package_file.rel}: {exc}") from exc
        for site in changed:
            print(f"rendered {site.rel} {site.block_id} ({site.state})")
    for files in result.tree.values():
        for package_file in files:
            for site in package_file.sites:
                if site.state == "identical":
                    print(f"unchanged {site.rel} {site.block_id}")
    print(f"render: {sum(len(changed) for _, changed in planned)} block(s) written")
    return EXIT_OK


def rebuild_file(package_file: PackageFile, block_map: dict[str, SourceBlock]) -> str:
    parts: list[str] = []
    cursor = 0
    for site in package_file.sites:
        block = block_for(block_map, package_file.package, site.block_id)
        if block is None:
            continue
        parts.append("".join(package_file.lines[cursor : site.begin_index + 1]))
        parts.append(block.body)
        cursor = site.end_index
    parts.append("".join(package_file.lines[cursor:]))
    return "".join(parts)


def atomic_write(path: Path, text: str, root: Path) -> None:
    """Write text to a temporary file beside the target, then rename it into place.

    The target's directory components and the target itself are re-validated against
    symlinks and containment immediately before the temporary file is created.
    """
    refuse_symlink_components(path.parent, "target directory")
    refuse_symlink(path, "target file", root)
    ensure_within(path, root)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=TEMP_SUFFIX, dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "wb") as file_obj:
            file_obj.write(text.encode("utf-8"))
            file_obj.flush()
            os.fsync(file_obj.fileno())
        if path.exists():
            shutil.copymode(path, temp_path)
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def run_audit_names(root: Path) -> int:
    packages = discover_packages(root)
    hits: list[str] = []
    for name, package_dir in sorted(packages.items()):
        if name == ROUTER_PACKAGE:
            continue
        for path in walk_package_files(package_dir, root):
            if path.suffix != ".md":
                continue
            try:
                text = path.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                continue
            rel = relative_display(path, root)
            for line_no, line in enumerate(text.splitlines(), 1):
                for column, token in roster_tokens(line, packages, own_name=name):
                    hits.append(f"{rel}:{line_no}:{column}: {token}")
    for hit in hits:
        print(hit)
    return EXIT_FINDINGS if hits else EXIT_OK


def run_list(source: Path) -> int:
    blocks, findings = parse_source(source)
    errors = [finding for finding in findings if finding.level == "error"]
    if errors:
        print_findings(errors)
        return EXIT_FINDINGS
    for block in blocks:
        fields = [block.block_id, f"kind={block.kind}"]
        if block.is_new_shape:
            fields.append("shape=new")
        fields.append(f"dependents={','.join(block.dependents)}")
        print("\t".join(fields))
    if source_closing_mode(blocks) == CLOSING_PER_PACKAGE:
        print(f"closing={CLOSING_PER_PACKAGE}")
    return EXIT_OK


# --- measure -----------------------------------------------------------------


def resolve_manifest(manifest_arg: str | os.PathLike[str] | None) -> Path:
    candidate = DEFAULT_MANIFEST if manifest_arg is None else Path(manifest_arg)
    if candidate.is_symlink():
        raise ContractError(f"measure manifest must not be a symlink: {candidate.as_posix()}")
    if not candidate.is_file():
        raise ContractError(f"measure manifest does not exist: {candidate.as_posix()}")
    return candidate.resolve()


def load_manifest(manifest: Path) -> list[dict]:
    try:
        data = json.loads(manifest.read_bytes().decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read measure manifest {manifest.as_posix()}: {exc}") from exc
    tasks = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(tasks, list) or not tasks:
        raise ContractError(f"measure manifest has no tasks: {manifest.as_posix()}")
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            raise ContractError(f"measure manifest task is missing its id: {manifest.as_posix()}")
        files = task.get("files")
        if not isinstance(files, list) or not all(isinstance(item, str) for item in files):
            raise ContractError(f"measure manifest task {task['id']} has no file list")
        baseline = task.get("baseline")
        if not isinstance(baseline, dict) or not isinstance(baseline.get("words"), int):
            raise ContractError(f"measure manifest task {task['id']} has no baseline words")
    return tasks


def package_measurements(root: Path, tree: dict[str, list[PackageFile]], packages: dict[str, Path]) -> list[tuple]:
    rows: list[tuple] = []
    for package in sorted(tree):
        entry_lines = entry_words = block_words = reference_words = 0
        for package_file in tree[package]:
            text = "".join(package_file.lines)
            lines, words = wc_counts(text)
            if package_file.path.parent == packages[package] and package_file.path.name == ENTRY_FILE_NAME:
                entry_lines, entry_words = lines, words
            else:
                reference_words += words
            for site in package_file.sites:
                block_words += wc_counts(site.content)[1]
        rows.append((package, entry_lines, entry_words, block_words, reference_words))
    return rows


def task_measurements(tasks: list[dict], root: Path) -> list[tuple]:
    rows: list[tuple] = []
    for task in tasks:
        lines = words = 0
        for rel in task["files"]:
            path = root.parent / rel
            refuse_symlink_components(path.parent, "measured file directory")
            refuse_symlink(path, "measured file", root)
            ensure_within(path, root)
            if not path.is_file():
                raise ContractError(f"measure manifest task {task['id']} lists a missing file: {rel}")
            try:
                text = path.read_bytes().decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise ContractError(f"cannot read {rel}: {exc}") from exc
            file_lines, file_words = wc_counts(text)
            lines += file_lines
            words += file_words
        rows.append((task, lines, words))
    return rows


def run_measure(root: Path, manifest: Path, *, strict: bool) -> int:
    tasks = load_manifest(manifest)
    packages = discover_packages(root)
    tree = scan_packages(root, packages, sorted(packages))

    print("package\tentry_lines\tentry_words\tblock_words\treference_words")
    for row in package_measurements(root, tree, packages):
        print("\t".join(str(field) for field in row))

    print()
    print("task\tlines\twords\tbaseline_lines\tbaseline_words\tpre_change_words\tdelta_words")
    above = 0
    for task, lines, words in task_measurements(tasks, root):
        baseline = task["baseline"]
        pre_change = task.get("pre_change") or {}
        baseline_words = baseline["words"]
        baseline_lines = baseline.get("lines", "-")
        delta = words - baseline_words
        if delta >= 0:
            above += 1
        print(
            f"{task['id']}\t{lines}\t{words}\t{baseline_lines}\t{baseline_words}"
            f"\t{pre_change.get('words', '-')}\t{delta:+d}"
        )
    mode = "strict" if strict else "non-strict"
    print(
        f"measure ({mode}): {len(tree)} package(s), {len(tasks)} task(s), "
        f"{above} task(s) not below baseline"
    )
    return EXIT_FINDINGS if strict and above else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
