#!/usr/bin/env python3
"""Sync repository skill packages into local agent skill directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


MANIFEST_NAME = ".agent-skills-sync.json"
MANIFEST_SCHEMA = "agent-skills-sync-v1"
SCRIPT_ID = "scripts/sync_dev_agent_skills.py"
CLAUDE_LINK_PREFIX = "../../.agents/skills"
IGNORED_FILE_NAMES = {".DS_Store"}
IGNORED_DIR_NAMES = {"__pycache__"}
COMMANDS = ("add", "update", "remove")


class SyncError(Exception):
    """Raised for safe, user-facing sync failures."""


@dataclass(frozen=True)
class SkillSync:
    name: str
    source: Path
    destination: Path
    temp_destination: Path
    backup_destination: Path
    claude_link: Path
    temp_claude_link: Path
    claude_target: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    argv, command_dry_run = extract_subcommand_dry_run(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        description="Manage repo skill snapshots in .agents/skills and Claude skill links.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root to sync. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="global_dry_run",
        help="Print planned operations without writing files.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in COMMANDS:
        subparser = subparsers.add_parser(command, help=f"{command} selected skill snapshots")
        subparser.add_argument("skills", nargs="+", help="Skill name(s) to operate on.")
        subparser.add_argument(
            "--dry-run",
            action="store_true",
            dest="command_dry_run",
            help="Print planned operations without writing files.",
        )
    args = parser.parse_args(argv)
    if command_dry_run:
        args.command_dry_run = True
    return args


def extract_subcommand_dry_run(argv: list[str]) -> tuple[list[str], bool]:
    command_index = find_command_index(argv)
    if command_index is None:
        return list(argv), False
    before_and_command = list(argv[: command_index + 1])
    after_command = argv[command_index + 1 :]
    stripped_after_command = [arg for arg in after_command if arg != "--dry-run"]
    return before_and_command + stripped_after_command, len(stripped_after_command) != len(after_command)


def find_command_index(argv: list[str]) -> int | None:
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--repo-root":
            index += 2
            continue
        if arg.startswith("--repo-root="):
            index += 1
            continue
        if arg in COMMANDS:
            return index
        index += 1
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = (args.repo_root or Path.cwd()).resolve()
    dry_run = args.global_dry_run or getattr(args, "command_dry_run", False)
    try:
        syncs = build_selected_sync_plan(repo_root, args.command, args.skills)
        if dry_run:
            print_dry_run(args.command, syncs, repo_root)
            return 0
        results = apply_sync(args.command, syncs)
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print_results(results)
    return 0


def build_sync_plan(repo_root: Path) -> list[SkillSync]:
    skills = [path.name for path in discover_source_skills(repo_root / "skills")]
    return build_selected_sync_plan(repo_root, "update", skills, require_clean_source=False)


def build_selected_sync_plan(
    repo_root: Path,
    command: str,
    skill_names: list[str],
    *,
    require_clean_source: bool = True,
) -> list[SkillSync]:
    skills_root = repo_root / "skills"
    agent_root = repo_root / ".agents"
    agent_skills = agent_root / "skills"
    claude_root = repo_root / ".claude"
    claude_skills = claude_root / "skills"

    validate_managed_root(agent_root, ".agents")
    validate_managed_root(agent_skills, ".agents/skills")
    validate_managed_root(claude_root, ".claude")
    validate_managed_root(claude_skills, ".claude/skills")

    normalized_names = normalize_skill_names(skill_names)
    syncs: list[SkillSync] = []
    for name in normalized_names:
        source = skills_root / name
        if command in {"add", "update"}:
            validate_selected_source_skill(source, skills_root)
            if require_clean_source:
                validate_source_clean(repo_root, name)
        destination = agent_skills / name
        sync = SkillSync(
            name=name,
            source=source,
            destination=destination,
            temp_destination=agent_skills / f".{name}.agent-skills-sync.tmp",
            backup_destination=agent_skills / f".{name}.agent-skills-sync.backup",
            claude_link=claude_skills / name,
            temp_claude_link=claude_skills / f".{name}.agent-skills-sync.tmp",
            claude_target=f"{CLAUDE_LINK_PREFIX}/{name}",
        )
        validate_sync_paths(sync, agent_skills, claude_skills)
        if command == "add":
            validate_add_state(sync)
        elif command == "update":
            validate_update_state(sync)
        elif command == "remove":
            validate_remove_state(sync)
        else:
            raise SyncError(f"unknown command: {command}")
        syncs.append(sync)

    validate_planned_path_collisions(syncs)
    return syncs


def normalize_skill_names(skill_names: list[str]) -> list[str]:
    if not skill_names:
        raise SyncError("at least one skill name is required")
    names: list[str] = []
    seen: set[str] = set()
    for name in skill_names:
        assert_simple_name(name)
        if name in seen:
            raise SyncError(f"duplicate skill name: {name}")
        seen.add(name)
        names.append(name)
    return names


def validate_selected_source_skill(source: Path, skills_root: Path) -> None:
    if source.is_symlink():
        raise SyncError(f"source skill directory is a symlink: {relative_display(source)}")
    if not source.exists():
        raise SyncError(f"source skill does not exist: {relative_display(source)}")
    if not source.is_dir():
        raise SyncError(f"source skill is not a directory: {relative_display(source)}")
    skill_file = source / "SKILL.md"
    if skill_file.is_symlink():
        raise SyncError(f"source skill contains a symlink: {relative_display(skill_file)}")
    if not skill_file.is_file():
        raise SyncError(f"source skill is missing SKILL.md: {relative_display(source)}")
    validate_source_tree(source, skills_root)


def validate_source_clean(repo_root: Path, skill_name: str) -> None:
    rel_path = f"skills/{skill_name}"
    pathspec = f":(literal){rel_path}"
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--",
                pathspec,
            ],
            text=False,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise SyncError(f"cannot prove source skill is clean for {skill_name}: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise SyncError(f"cannot prove source skill is clean for {skill_name}{suffix}")
    if result.stdout:
        entries = [entry for entry in result.stdout.decode("utf-8", errors="replace").split("\0") if entry]
        preview = ", ".join(entries[:5])
        if len(entries) > 5:
            preview += ", ..."
        raise SyncError(f"source skill has working tree changes: {skill_name} ({preview})")


def validate_managed_root(path: Path, label: str) -> None:
    if path.is_symlink():
        raise SyncError(f"{label} must not be a symlink")
    if path.exists() and not path.is_dir():
        raise SyncError(f"{label} exists but is not a directory")


def discover_source_skills(skills_root: Path) -> list[Path]:
    if skills_root.is_symlink():
        raise SyncError("skills must not be a symlink")
    if not skills_root.exists():
        raise SyncError("missing skills directory")
    if not skills_root.is_dir():
        raise SyncError("skills exists but is not a directory")

    source_skills: list[Path] = []
    for entry in sorted(skills_root.iterdir(), key=lambda path: path.name):
        skill_file = entry / "SKILL.md"
        if entry.is_symlink():
            if skill_file.exists() or skill_file.is_symlink():
                raise SyncError(f"source skill directory is a symlink: {relative_display(entry)}")
            continue
        if not entry.is_dir():
            continue
        if skill_file.is_symlink():
            raise SyncError(f"source skill contains a symlink: {relative_display(skill_file)}")
        if skill_file.exists() and not skill_file.is_file():
            raise SyncError(f"source skill SKILL.md is not a regular file: {relative_display(skill_file)}")
        if skill_file.is_file() and not skill_file.is_symlink():
            source_skills.append(entry)

    if not source_skills:
        raise SyncError("no skill packages found under skills/")
    return source_skills


def assert_simple_name(name: str) -> None:
    if name in {"", ".", ".."} or "/" in name or os.sep in name:
        raise SyncError(f"invalid skill package name: {name!r}")
    if os.altsep and os.altsep in name:
        raise SyncError(f"invalid skill package name: {name!r}")


def validate_source_tree(source: Path, skills_root: Path) -> None:
    if source.is_symlink():
        raise SyncError(f"source skill directory is a symlink: {relative_display(source)}")
    try:
        source.resolve().relative_to(skills_root.resolve())
    except ValueError as exc:
        raise SyncError(f"source skill resolves outside skills/: {relative_display(source)}") from exc

    reserved_manifest = source / MANIFEST_NAME
    if reserved_manifest.exists() or reserved_manifest.is_symlink():
        raise SyncError(f"source skill contains reserved manifest path: {relative_display(reserved_manifest)}")

    for path in walk_included_tree(source, source.name):
        st = path.lstat()
        mode = st.st_mode
        if stat.S_ISLNK(mode):
            raise SyncError(f"source skill contains a symlink: {relative_display(path)}")
        if stat.S_ISDIR(mode) or stat.S_ISREG(mode):
            continue
        raise SyncError(f"source skill contains a non-regular file: {relative_display(path)}")


def walk_included_tree(root: Path, skill_name: str) -> list[Path]:
    entries: list[Path] = [root]
    for current, dir_names, file_names in os.walk(root, topdown=True, followlinks=False, onerror=raise_walk_error):
        current_path = Path(current)
        rel_current = current_path.relative_to(root)
        kept_dirs: list[str] = []
        for dir_name in sorted(dir_names):
            path = current_path / dir_name
            rel_parts = (rel_current / dir_name).parts
            if should_exclude(rel_parts, skill_name):
                continue
            entries.append(path)
            if not path.is_symlink() and path.is_dir():
                kept_dirs.append(dir_name)
        dir_names[:] = kept_dirs
        for file_name in sorted(file_names):
            path = current_path / file_name
            rel_parts = (rel_current / file_name).parts
            if should_exclude(rel_parts, skill_name):
                continue
            entries.append(path)
    return entries


def raise_walk_error(error: OSError) -> None:
    raise SyncError(f"failed to read directory {error.filename}: {error.strerror}") from error


def validate_sync_paths(sync: SkillSync, agent_skills: Path, claude_skills: Path) -> None:
    for path, root, label in (
        (sync.destination, agent_skills, "destination"),
        (sync.temp_destination, agent_skills, "temporary destination"),
        (sync.backup_destination, agent_skills, "backup destination"),
        (sync.claude_link, claude_skills, "Claude link"),
        (sync.temp_claude_link, claude_skills, "temporary Claude link"),
    ):
        ensure_within(path, root, label)

    for path, label in (
        (sync.temp_destination, "temporary destination"),
        (sync.backup_destination, "backup destination"),
        (sync.temp_claude_link, "temporary Claude link"),
    ):
        if path_exists_no_follow(path):
            raise SyncError(f"{label} already exists: {relative_display(path)}")


def validate_planned_path_collisions(syncs: list[SkillSync]) -> None:
    seen: dict[Path, str] = {}
    for sync in syncs:
        planned_paths = {
            "destination": sync.destination,
            "temporary destination": sync.temp_destination,
            "backup destination": sync.backup_destination,
            "Claude link": sync.claude_link,
            "temporary Claude link": sync.temp_claude_link,
        }
        for label, path in planned_paths.items():
            key = Path(os.path.abspath(path))
            owner = f"{sync.name} {label}"
            previous = seen.get(key)
            if previous is not None:
                raise SyncError(
                    "planned path collision between "
                    f"{previous} and {owner}: {relative_display(path)}"
                )
            seen[key] = owner


def ensure_within(path: Path, root: Path, label: str) -> None:
    try:
        path.parent.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError as exc:
        raise SyncError(f"{label} resolves outside its managed root: {relative_display(path)}") from exc


def validate_destination_state(sync: SkillSync) -> None:
    destination = sync.destination
    if destination.is_symlink():
        raise SyncError(f"destination exists as a symlink: {relative_display(destination)}")
    if not destination.exists():
        return
    if not destination.is_dir():
        raise SyncError(f"destination exists but is not a directory: {relative_display(destination)}")

    manifest = read_owned_manifest(destination, sync.name)
    current_digest = tree_digest(destination, sync.name)
    if current_digest != manifest["tree_digest"]:
        raise SyncError(
            "destination has local changes or stale manifest digest: "
            f"{relative_display(destination)}"
        )


def validate_add_state(sync: SkillSync) -> None:
    if path_exists_no_follow(sync.destination):
        raise SyncError(f"destination already exists; use update: {relative_display(sync.destination)}")
    if path_exists_no_follow(sync.claude_link):
        raise SyncError(f"Claude skill path already exists; use update: {relative_display(sync.claude_link)}")


def validate_update_state(sync: SkillSync) -> None:
    if not sync.destination.exists() and not sync.destination.is_symlink():
        raise SyncError(f"destination is not installed; use add: {relative_display(sync.destination)}")
    validate_destination_state(sync)
    validate_claude_link_state(sync)


def validate_remove_state(sync: SkillSync) -> None:
    if not sync.destination.exists() and not sync.destination.is_symlink():
        raise SyncError(f"destination is not installed: {relative_display(sync.destination)}")
    validate_destination_state(sync)
    link = sync.claude_link
    if link.is_symlink():
        target = os.readlink(link)
        if target != sync.claude_target:
            raise SyncError(
                "refusing to remove unmanaged Claude skill symlink: "
                f"{relative_display(link)} -> {target}"
            )
        return
    if link.exists():
        raise SyncError(f"Claude skill path exists but is not a symlink: {relative_display(link)}")


def read_owned_manifest(destination: Path, skill_name: str) -> dict[str, str]:
    manifest_path = destination / MANIFEST_NAME
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise SyncError(f"refusing to replace unowned destination: {relative_display(destination)}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"invalid ownership manifest: {relative_display(manifest_path)}") from exc
    if not isinstance(manifest, dict):
        raise SyncError(f"invalid ownership manifest: {relative_display(manifest_path)}")
    expected = {
        "schema_version": MANIFEST_SCHEMA,
        "script": SCRIPT_ID,
        "skill_name": skill_name,
        "source": f"skills/{skill_name}",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise SyncError(f"invalid ownership manifest: {relative_display(manifest_path)}")
    digest = manifest.get("tree_digest")
    if not isinstance(digest, str) or len(digest) != 64:
        raise SyncError(f"invalid ownership manifest: {relative_display(manifest_path)}")
    return manifest


def validate_claude_link_state(sync: SkillSync) -> None:
    link = sync.claude_link
    if link.is_symlink():
        return
    if link.exists():
        raise SyncError(f"Claude skill path exists but is not a symlink: {relative_display(link)}")


def apply_sync(command: str, syncs: list[SkillSync], *, symlink_capability_func=None) -> dict[str, list[str]]:
    if symlink_capability_func is None:
        symlink_capability_func = validate_symlink_capability
    if command in {"add", "update"}:
        symlink_capability_func()
        ensure_write_roots(syncs)
    results = {"copied": [], "linked": [], "skipped": [], "removed": []}
    if command == "remove":
        for sync in syncs:
            remove_install(sync)
            results["removed"].append(sync.name)
        return results
    for sync in syncs:
        status = replace_snapshot_and_link(sync)
        results["copied"].append(sync.name)
        results["linked" if status != "unchanged" else "skipped"].append(sync.name)
    return results


def validate_symlink_capability(symlink_func=None) -> None:
    if symlink_func is None:
        symlink_func = getattr(os, "symlink", None)
    if symlink_func is None:
        raise SyncError("this platform does not expose os.symlink; cannot create Claude skill links")
    try:
        with tempfile.TemporaryDirectory(prefix="agent-skills-sync-") as tmp:
            tmp_root = Path(tmp)
            target = tmp_root / "target"
            link = tmp_root / "link"
            target.mkdir()
            symlink_func("target", link, target_is_directory=True)
            if not link.is_symlink() or os.readlink(link) != "target":
                raise SyncError("temporary symlink capability check produced an unexpected link")
    except Exception as exc:
        if isinstance(exc, SyncError):
            raise
        raise SyncError(f"cannot create Claude skill symlinks on this platform: {exc}") from exc


def ensure_write_roots(syncs: list[SkillSync]) -> None:
    if not syncs:
        return
    agent_skills = syncs[0].destination.parent
    claude_skills = syncs[0].claude_link.parent
    agent_skills.mkdir(parents=True, exist_ok=True)
    claude_skills.mkdir(parents=True, exist_ok=True)


def replace_snapshot_and_link(
    sync: SkillSync,
    *,
    copy_func=None,
    replace_func=os.replace,
    rmtree_func=shutil.rmtree,
    link_func=None,
) -> str:
    if copy_func is None:
        copy_func = copy_skill_tree
    if link_func is None:
        link_func = replace_claude_link

    backup_made = False
    new_destination_installed = False
    removing_backup = False
    try:
        copy_func(sync.source, sync.temp_destination, sync.name)
        copied_digest = tree_digest(sync.temp_destination, sync.name)
        write_manifest(sync.temp_destination, sync.name, copied_digest)

        if sync.destination.exists():
            replace_func(sync.destination, sync.backup_destination)
            backup_made = True
        replace_func(sync.temp_destination, sync.destination)
        new_destination_installed = True

        link_status = link_func(sync)
        if backup_made and sync.backup_destination.exists():
            removing_backup = True
            rmtree_func(sync.backup_destination)
            backup_made = False
            removing_backup = False
        return link_status
    except Exception as exc:
        cleanup_path(sync.temp_destination, rmtree_func)
        cleanup_path(sync.temp_claude_link, rmtree_func)
        if removing_backup:
            if isinstance(exc, SyncError):
                raise
            raise SyncError(f"synced {sync.name} but failed to remove backup: {exc}") from exc
        if new_destination_installed:
            restore_backup(sync, replace_func)
        elif backup_made:
            restore_backup(sync, replace_func)
        if isinstance(exc, SyncError):
            raise
        raise SyncError(f"failed to sync skill snapshot {sync.name}: {exc}") from exc

def restore_backup(sync: SkillSync, replace_func) -> None:
    try:
        if sync.destination.exists():
            cleanup_path(sync.destination, shutil.rmtree)
        if sync.backup_destination.exists():
            replace_func(sync.backup_destination, sync.destination)
    except Exception as exc:
        raise SyncError(f"failed to restore previous skill snapshot {sync.name}: {exc}") from exc


def cleanup_path(path: Path, rmtree_func) -> None:
    if path.is_symlink():
        path.unlink()
    elif path.is_dir():
        rmtree_func(path)
    elif path.exists():
        path.unlink()


def remove_install(
    sync: SkillSync,
    *,
    replace_func=os.replace,
    rmtree_func=shutil.rmtree,
    symlink_func=None,
) -> None:
    if symlink_func is None:
        symlink_func = getattr(os, "symlink", None)
    link_removed = False
    old_link_target: str | None = None
    backup_made = False
    try:
        if sync.claude_link.is_symlink():
            old_link_target = os.readlink(sync.claude_link)
            sync.claude_link.unlink()
            link_removed = True
        replace_func(sync.destination, sync.backup_destination)
        backup_made = True
        rmtree_func(sync.backup_destination)
        backup_made = False
    except Exception as exc:
        restored_destination = not backup_made
        if backup_made and sync.backup_destination.exists():
            try:
                replace_func(sync.backup_destination, sync.destination)
                restored_destination = True
            except Exception as restore_exc:
                raise SyncError(f"failed to restore removed skill snapshot {sync.name}: {restore_exc}") from exc
        if (
            restored_destination
            and link_removed
            and old_link_target is not None
            and not path_exists_no_follow(sync.claude_link)
        ):
            if symlink_func is None:
                raise SyncError(f"failed to restore Claude skill link {sync.name}: os.symlink unavailable") from exc
            symlink_func(old_link_target, sync.claude_link, target_is_directory=True)
        if backup_made and not restored_destination:
            raise SyncError(f"removed {sync.name} but failed to clean backup: {exc}") from exc
        if isinstance(exc, SyncError):
            raise
        raise SyncError(f"failed to remove skill snapshot {sync.name}: {exc}") from exc


def copy_skill_tree(source: Path, destination: Path, skill_name: str) -> None:
    if path_exists_no_follow(destination):
        raise SyncError(f"temporary destination already exists: {relative_display(destination)}")
    destination.mkdir(parents=True)

    for current, dir_names, file_names in os.walk(source, topdown=True, followlinks=False, onerror=raise_walk_error):
        current_path = Path(current)
        rel_current = current_path.relative_to(source)
        target_current = destination / rel_current
        if rel_current != Path("."):
            target_current.mkdir(exist_ok=True)

        kept_dirs: list[str] = []
        for dir_name in sorted(dir_names):
            source_dir = current_path / dir_name
            rel_parts = (rel_current / dir_name).parts
            if should_exclude(rel_parts, skill_name):
                continue
            mode = source_dir.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise SyncError(f"source skill contains a symlink: {relative_display(source_dir)}")
            if not stat.S_ISDIR(mode):
                raise SyncError(f"source skill contains a non-directory entry: {relative_display(source_dir)}")
            kept_dirs.append(dir_name)
        dir_names[:] = kept_dirs

        for file_name in sorted(file_names):
            source_file = current_path / file_name
            rel_parts = (rel_current / file_name).parts
            if should_exclude(rel_parts, skill_name):
                continue
            mode = source_file.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise SyncError(f"source skill contains a symlink: {relative_display(source_file)}")
            if not stat.S_ISREG(mode):
                raise SyncError(f"source skill contains a non-regular file: {relative_display(source_file)}")
            shutil.copy2(source_file, target_current / file_name, follow_symlinks=False)


def should_exclude(rel_parts: tuple[str, ...], skill_name: str) -> bool:
    if not rel_parts:
        return False
    if any(part in IGNORED_DIR_NAMES for part in rel_parts):
        return True
    name = rel_parts[-1]
    if name in IGNORED_FILE_NAMES or name.endswith(":Zone.Identifier"):
        return True
    for index, part in enumerate(rel_parts):
        if part == "evals" and len(rel_parts) > index + 2 and rel_parts[index + 2] == "workspace":
            return True
    return False


def write_manifest(destination: Path, skill_name: str, digest: str) -> None:
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "script": SCRIPT_ID,
        "skill_name": skill_name,
        "source": f"skills/{skill_name}",
        "tree_digest": digest,
    }
    (destination / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def replace_claude_link(
    sync: SkillSync,
    *,
    symlink_func=None,
    replace_func=os.replace,
) -> str:
    if symlink_func is None:
        symlink_func = getattr(os, "symlink", None)
    if symlink_func is None:
        raise SyncError("this platform does not expose os.symlink; cannot create Claude skill links")
    if sync.claude_link.is_symlink() and os.readlink(sync.claude_link) == sync.claude_target:
        return "unchanged"

    try:
        symlink_func(sync.claude_target, sync.temp_claude_link, target_is_directory=True)
        if os.readlink(sync.temp_claude_link) != sync.claude_target:
            raise SyncError(f"temporary Claude link has unexpected target: {relative_display(sync.temp_claude_link)}")
        replace_func(sync.temp_claude_link, sync.claude_link)
    except Exception as exc:
        if sync.temp_claude_link.is_symlink() or sync.temp_claude_link.exists():
            cleanup_path(sync.temp_claude_link, shutil.rmtree)
        if isinstance(exc, SyncError):
            raise
        raise SyncError(f"failed to replace Claude skill link {sync.name}: {exc}") from exc
    return "refreshed"


def tree_digest(root: Path, skill_name: str | None = None) -> str:
    skill_name = skill_name or root.name
    digest = hashlib.sha256()
    for path in walk_included_tree(root, skill_name):
        if path == root:
            continue
        rel = path.relative_to(root).as_posix()
        if rel == MANIFEST_NAME:
            continue
        st = path.lstat()
        mode = st.st_mode
        if stat.S_ISLNK(mode):
            raise SyncError(f"tree contains a symlink: {relative_display(path)}")
        if stat.S_ISDIR(mode):
            digest.update(b"D\0")
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(stat.S_IMODE(mode)).encode("ascii"))
            digest.update(b"\0")
            continue
        if stat.S_ISREG(mode):
            digest.update(b"F\0")
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(stat.S_IMODE(mode)).encode("ascii"))
            digest.update(b"\0")
            with path.open("rb") as file_obj:
                for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
            continue
        raise SyncError(f"tree contains a non-regular file: {relative_display(path)}")
    return digest.hexdigest()


def print_dry_run(command: str, syncs: list[SkillSync], repo_root: Path) -> None:
    print(f"Dry run: {command} {len(syncs)} skill package(s).")
    for sync in syncs:
        if command == "remove":
            print(f"  remove {sync.destination.relative_to(repo_root).as_posix()}")
            print(f"  unlink {sync.claude_link.relative_to(repo_root).as_posix()}")
        else:
            print(
                "  copy "
                f"{sync.source.relative_to(repo_root).as_posix()} -> "
                f"{sync.destination.relative_to(repo_root).as_posix()}"
            )
            print(
                "  link "
                f"{sync.claude_link.relative_to(repo_root).as_posix()} -> "
                f"{sync.claude_target}"
            )


def print_results(results: dict[str, list[str]]) -> None:
    total = len(results["copied"]) + len(results["removed"])
    print(f"Processed {total} skill package(s).")
    for label in ("copied", "linked", "skipped", "removed"):
        values = results[label]
        print(f"{label}: {', '.join(values) if values else 'none'}")


def path_exists_no_follow(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def relative_display(path: Path) -> str:
    return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
