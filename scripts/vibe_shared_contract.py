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
``list`` prints the blocks the source declares.

Marker-looking lines inside a correctly matched Markdown code fence are ordinary text
for both parsers, so a file may show the marker grammar as an example.
"""

from __future__ import annotations

import argparse
import difflib
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
DEFAULT_ROOT = REPO_ROOT / "skills"
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
NON_OVERRIDABLE_BLOCK_IDS = frozenset(
    {
        "session-record-schema",
        "history-mutation-gate",
        "commit-selection-gate",
        "read-only-phase-write-gate",
    }
)
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
            return run_render(resolve_source(args.source), resolve_root(args.root), force=args.force)
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


def parse_source(source: Path) -> tuple[list[SourceBlock], list[Finding]]:
    try:
        text = source.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ContractError(f"cannot read shared source {source.as_posix()}: {exc}") from exc
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


def check_source_blocks(blocks: list[SourceBlock], packages: dict[str, Path], label: str) -> list[Finding]:
    findings: list[Finding] = []
    for block in blocks:
        where = f"{label}:{block.line}: block {block.block_id}"
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
        last_line = [line for line in block.body.splitlines() if line.strip()][-1].strip()
        if last_line != block.closing_sentence:
            findings.append(
                Finding(
                    "error",
                    f"{where}: {block.kind} block does not end with its closing sentence: {block.closing_sentence!r}",
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


def check_packages(
    blocks: list[SourceBlock],
    tree: dict[str, list[PackageFile]],
    *,
    strict: bool,
    report_states: bool = True,
) -> list[Finding]:
    block_map = {block.block_id: block for block in blocks}
    findings: list[Finding] = []
    for package, files in tree.items():
        seen: dict[str, str] = {}
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
                block = block_map.get(site.block_id)
                if block is None:
                    findings.append(Finding("error", f"{where}: unknown block id {site.block_id}"))
                    continue
                if package not in block.dependents:
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
                site.state = classify_site(site.content, block.body)
                if not report_states:
                    continue
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
    findings.extend(check_source_blocks(blocks, packages, source.name))
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


def run_render(source: Path, root: Path, *, force: bool) -> int:
    result = analyze(source, root, strict=False, package_filter=None, report_states=False)
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
                block = block_map[site.block_id]
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
        parts.append("".join(package_file.lines[cursor : site.begin_index + 1]))
        parts.append(block_map[site.block_id].body)
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
        print(f"{block.block_id}\tkind={block.kind}\tdependents={','.join(block.dependents)}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
