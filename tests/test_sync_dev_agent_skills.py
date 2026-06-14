import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_dev_agent_skills.py"


def can_create_dir_symlink():
    if not hasattr(os, "symlink"):
        return False
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "target"
        link = root / "link"
        target.mkdir()
        try:
            os.symlink(target, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            return False
        return link.is_symlink()


CAN_CREATE_DIR_SYMLINK = can_create_dir_symlink()


def make_dir_symlink(target, link):
    os.symlink(target, link, target_is_directory=True)


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_dev_agent_skills", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(CAN_CREATE_DIR_SYMLINK, "directory symlink support required")
class SyncDevAgentSkillsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args, check=True, repo_root=None):
        repo_root = repo_root or self.root
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo-root", repo_root, *map(str, args)],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if check and result.returncode != 0:
            self.fail(f"command failed: {result.args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def git(self, *args, repo_root=None):
        repo_root = repo_root or self.root
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            self.fail(f"git failed: {result.args}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def init_git(self):
        self.git("init")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test User")

    def commit_all(self, message="snapshot"):
        self.git("add", ".")
        self.git("commit", "-m", message)

    def write_skill(self, name="foo", files=None):
        files = files or {"SKILL.md": f"---\nname: {name}\n---\n# {name}\n"}
        root = self.root / "skills" / name
        for rel_path, content in files.items():
            path = root / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root

    def snapshot(self, path=None):
        path = path or self.root
        if not path.exists():
            return {}
        result = {}
        for item in sorted(path.rglob("*"), key=lambda p: p.relative_to(path).as_posix()):
            rel = item.relative_to(path).as_posix()
            if ".git/" in f"{rel}/" or rel == ".git":
                continue
            if item.is_symlink():
                result[rel] = ("link", os.readlink(item))
            elif item.is_dir():
                result[rel] = ("dir", None)
            else:
                result[rel] = ("file", item.read_bytes())
        return result

    def prepare_repo(self):
        self.write_skill("foo", {"SKILL.md": "# Foo\n", "references/guide.md": "guide\n"})
        self.write_skill("bar", {"SKILL.md": "# Bar\n"})
        self.init_git()
        self.commit_all()

    def test_help_lists_subcommands_and_missing_subcommand_fails(self):
        self.prepare_repo()

        help_result = self.run_cli("--help")
        self.assertIn("add", help_result.stdout)
        self.assertIn("update", help_result.stdout)
        self.assertIn("remove", help_result.stdout)

        before = self.snapshot()
        result = self.run_cli("--dry-run", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_add_dry_run_works_after_subcommand_and_writes_nothing(self):
        self.prepare_repo()
        before = self.snapshot()

        result = self.run_cli("add", "foo", "--dry-run")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry run: add 1 skill package", result.stdout)
        self.assertIn("copy skills/foo -> .agents/skills/foo", result.stdout)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_global_dry_run_also_works_with_subcommand(self):
        self.prepare_repo()

        result = self.run_cli("--dry-run", "add", "foo")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry run: add 1 skill package", result.stdout)
        self.assertFalse((self.root / ".agents").exists())

    def test_subcommand_dry_run_can_appear_between_selected_skills(self):
        self.prepare_repo()

        result = self.run_cli("add", "foo", "--dry-run", "bar")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry run: add 2 skill package", result.stdout)
        self.assertIn("copy skills/foo -> .agents/skills/foo", result.stdout)
        self.assertIn("copy skills/bar -> .agents/skills/bar", result.stdout)
        self.assertFalse((self.root / ".agents").exists())

    def test_subcommands_require_selected_skill_names(self):
        self.prepare_repo()

        for command in ("add", "update", "remove"):
            with self.subTest(command=command):
                result = self.run_cli(command, "--dry-run", check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("required", result.stderr)
                self.assertFalse((self.root / ".agents").exists())

    def test_add_installs_only_selected_skill_and_claude_link(self):
        self.prepare_repo()

        self.run_cli("add", "foo")

        module = load_sync_module()
        destination = self.root / ".agents" / "skills" / "foo"
        self.assertTrue(destination.is_dir())
        self.assertFalse(destination.is_symlink())
        self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "# Foo\n")
        self.assertEqual(os.readlink(self.root / ".claude" / "skills" / "foo"), "../../.agents/skills/foo")
        self.assertFalse((self.root / ".agents" / "skills" / "bar").exists())
        manifest = json.loads((destination / module.MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["skill_name"], "foo")
        self.assertEqual(manifest["tree_digest"], module.tree_digest(destination))

    def test_add_existing_destination_fails_without_changes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        before = self.snapshot()

        result = self.run_cli("add", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination already exists", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_add_dirty_source_fails_before_writes(self):
        self.prepare_repo()
        (self.root / "skills" / "foo" / "new.md").write_text("dirty\n", encoding="utf-8")

        result = self.run_cli("add", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_add_ignores_dirty_non_selected_source(self):
        self.prepare_repo()
        (self.root / "skills" / "bar" / "SKILL.md").write_text("# Dirty Bar\n", encoding="utf-8")

        self.run_cli("add", "foo")

        self.assertTrue((self.root / ".agents" / "skills" / "foo").is_dir())
        self.assertFalse((self.root / ".agents" / "skills" / "bar").exists())

    def test_add_uses_literal_git_pathspec_for_selected_source(self):
        self.write_skill("foo*", {"SKILL.md": "# Foo Star\n"})
        self.write_skill("foobar", {"SKILL.md": "# Foobar\n"})
        self.init_git()
        self.commit_all()
        (self.root / "skills" / "foobar" / "SKILL.md").write_text("# Dirty Foobar\n", encoding="utf-8")

        self.run_cli("add", "foo*")

        self.assertTrue((self.root / ".agents" / "skills" / "foo*").exists())
        self.assertFalse((self.root / ".agents" / "skills" / "foobar").exists())

    def test_add_literal_git_pathspec_detects_dirty_metacharacter_source(self):
        self.write_skill("foo[bar]", {"SKILL.md": "# Foo Bracket\n"})
        self.init_git()
        self.commit_all()
        (self.root / "skills" / "foo[bar]" / "SKILL.md").write_text("# Dirty Foo Bracket\n", encoding="utf-8")

        result = self.run_cli("add", "foo[bar]", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertFalse((self.root / ".agents").exists())

    def test_add_without_git_cleanliness_proof_fails_before_writes(self):
        self.write_skill("foo", {"SKILL.md": "# Foo\n"})

        result = self.run_cli("add", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot prove source skill is clean", result.stderr)
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_add_dry_run_does_not_require_symlink_capability(self):
        module = load_sync_module()
        self.prepare_repo()

        stdout = io.StringIO()
        with mock.patch.object(module.os, "symlink", None):
            with contextlib.redirect_stdout(stdout):
                result = module.main(["--repo-root", str(self.root), "add", "foo", "--dry-run"])

        self.assertEqual(result, 0)
        self.assertIn("Dry run: add 1 skill package", stdout.getvalue())
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_add_write_mode_requires_symlink_capability_before_writes(self):
        module = load_sync_module()
        self.prepare_repo()

        stderr = io.StringIO()
        with mock.patch.object(module.os, "symlink", None):
            with contextlib.redirect_stderr(stderr):
                result = module.main(["--repo-root", str(self.root), "add", "foo"])

        self.assertEqual(result, 1)
        self.assertIn("does not expose os.symlink", stderr.getvalue())
        self.assertFalse((self.root / ".agents").exists())
        self.assertFalse((self.root / ".claude").exists())

    def test_update_refreshes_owned_snapshot_and_repairs_link(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        skill = self.root / "skills" / "foo"
        (skill / "references" / "guide.md").unlink()
        (skill / "new.md").write_text("new\n", encoding="utf-8")
        self.commit_all("update foo")
        destination = self.root / ".agents" / "skills" / "foo"
        link = self.root / ".claude" / "skills" / "foo"
        link.unlink()
        make_dir_symlink("../../wrong", link)

        self.run_cli("update", "foo")

        self.assertFalse((destination / "references" / "guide.md").exists())
        self.assertEqual((destination / "new.md").read_text(encoding="utf-8"), "new\n")
        self.assertEqual(os.readlink(link), "../../.agents/skills/foo")

    def test_update_dirty_source_fails_before_writes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        destination = self.root / ".agents" / "skills" / "foo"
        before_content = (destination / "SKILL.md").read_text(encoding="utf-8")
        (self.root / "skills" / "foo" / "SKILL.md").write_text("# Dirty\n", encoding="utf-8")

        result = self.run_cli("update", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), before_content)

    def test_update_deleted_tracked_source_file_fails_before_writes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        destination = self.root / ".agents" / "skills" / "foo"
        (self.root / "skills" / "foo" / "references" / "guide.md").unlink()

        result = self.run_cli("update", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertTrue((destination / "references" / "guide.md").exists())

    def test_update_renamed_tracked_source_file_fails_before_writes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        destination = self.root / ".agents" / "skills" / "foo"
        self.git("mv", "skills/foo/references/guide.md", "skills/foo/references/renamed.md")

        result = self.run_cli("update", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertTrue((destination / "references" / "guide.md").exists())
        self.assertFalse((destination / "references" / "renamed.md").exists())

    def test_update_source_type_change_fails_before_writes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        destination = self.root / ".agents" / "skills" / "foo"
        guide = self.root / "skills" / "foo" / "references" / "guide.md"
        guide.unlink()
        guide.mkdir()
        (guide / "nested.md").write_text("changed type\n", encoding="utf-8")

        result = self.run_cli("update", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertTrue((destination / "references" / "guide.md").is_file())

    def test_update_dry_run_works_after_subcommand_and_writes_nothing(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        before = self.snapshot()

        result = self.run_cli("update", "foo", "--dry-run")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry run: update 1 skill package", result.stdout)
        self.assertEqual(before, self.snapshot())

    def test_update_missing_destination_fails_use_add(self):
        self.prepare_repo()

        result = self.run_cli("update", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination is not installed; use add", result.stderr)
        self.assertFalse((self.root / ".agents").exists())

    def test_update_refuses_dirty_owned_destination_without_changes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        destination = self.root / ".agents" / "skills" / "foo"
        before = self.snapshot()
        (destination / "local.txt").write_text("local change\n", encoding="utf-8")

        result = self.run_cli("update", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination has local changes", result.stderr)
        after = self.snapshot()
        self.assertEqual(after[".agents/skills/foo/SKILL.md"], before[".agents/skills/foo/SKILL.md"])
        self.assertIn(".agents/skills/foo/local.txt", after)

    def test_add_link_failure_rolls_back_snapshot(self):
        module = load_sync_module()
        self.prepare_repo()
        sync = module.build_selected_sync_plan(self.root, "add", ["foo"])[0]

        def fail_link(_sync):
            raise module.SyncError("forced link failure")

        with self.assertRaises(module.SyncError):
            module.replace_snapshot_and_link(sync, link_func=fail_link)

        self.assertFalse(sync.destination.exists())
        self.assertFalse(sync.backup_destination.exists())
        self.assertFalse(sync.temp_destination.exists())
        self.assertFalse(sync.temp_claude_link.exists())

    def test_update_link_failure_restores_previous_snapshot(self):
        module = load_sync_module()
        self.prepare_repo()
        self.run_cli("add", "foo")
        destination = self.root / ".agents" / "skills" / "foo"
        before = self.snapshot(destination)
        (self.root / "skills" / "foo" / "new.md").write_text("new\n", encoding="utf-8")
        self.commit_all("update foo")
        sync = module.build_selected_sync_plan(self.root, "update", ["foo"])[0]

        def fail_link(_sync):
            raise module.SyncError("forced link failure")

        with self.assertRaises(module.SyncError):
            module.replace_snapshot_and_link(sync, link_func=fail_link)

        self.assertEqual(before, self.snapshot(destination))
        self.assertFalse((destination / "new.md").exists())
        self.assertFalse(sync.backup_destination.exists())
        self.assertEqual(os.readlink(sync.claude_link), "../../.agents/skills/foo")

    def test_remove_deletes_owned_snapshot_and_link_even_when_source_dirty(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        (self.root / "skills" / "foo" / "SKILL.md").write_text("# Dirty\n", encoding="utf-8")

        self.run_cli("remove", "foo")

        self.assertFalse((self.root / ".agents" / "skills" / "foo").exists())
        self.assertFalse((self.root / ".claude" / "skills" / "foo").exists())

    def test_remove_dry_run_writes_nothing(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        before = self.snapshot()

        result = self.run_cli("remove", "foo", "--dry-run")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry run: remove 1 skill package", result.stdout)
        self.assertEqual(before, self.snapshot())

    def test_remove_refuses_unowned_destination_and_wrong_link(self):
        self.prepare_repo()
        destination = self.root / ".agents" / "skills" / "foo"
        destination.mkdir(parents=True)
        (destination / "SKILL.md").write_text("local\n", encoding="utf-8")
        link = self.root / ".claude" / "skills" / "foo"
        link.parent.mkdir(parents=True)
        make_dir_symlink("../../wrong", link)

        result = self.run_cli("remove", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to replace unowned destination", result.stderr)
        self.assertTrue(destination.exists())
        self.assertEqual(os.readlink(link), "../../wrong")

    def test_remove_wrong_managed_link_is_refused_after_owned_destination(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        link = self.root / ".claude" / "skills" / "foo"
        link.unlink()
        make_dir_symlink("../../wrong", link)

        result = self.run_cli("remove", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to remove unmanaged Claude skill symlink", result.stderr)
        self.assertTrue((self.root / ".agents" / "skills" / "foo").exists())
        self.assertEqual(os.readlink(link), "../../wrong")

    def test_remove_refuses_dirty_owned_destination_without_changes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        destination = self.root / ".agents" / "skills" / "foo"
        (destination / "local.txt").write_text("local change\n", encoding="utf-8")

        result = self.run_cli("remove", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination has local changes", result.stderr)
        self.assertTrue(destination.exists())
        self.assertTrue((destination / "local.txt").exists())
        self.assertEqual(os.readlink(self.root / ".claude" / "skills" / "foo"), "../../.agents/skills/foo")

    def test_multi_skill_preflight_blocks_all_writes(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        (self.root / "skills" / "bar" / "new.md").write_text("dirty\n", encoding="utf-8")

        result = self.run_cli("update", "foo", "bar", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertFalse((self.root / ".agents" / "skills" / "bar").exists())

    def test_multi_remove_preflight_blocks_all_deletes(self):
        self.prepare_repo()
        self.run_cli("add", "foo", "bar")
        (self.root / ".agents" / "skills" / "bar" / "local.txt").write_text("local change\n", encoding="utf-8")

        result = self.run_cli("remove", "foo", "bar", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination has local changes", result.stderr)
        self.assertTrue((self.root / ".agents" / "skills" / "foo").exists())
        self.assertTrue((self.root / ".claude" / "skills" / "foo").is_symlink())
        self.assertTrue((self.root / ".agents" / "skills" / "bar").exists())

    def test_selected_operations_preserve_unrelated_local_entries(self):
        self.prepare_repo()
        unrelated = self.root / ".agents" / "skills" / "local-only"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("local\n", encoding="utf-8")
        unrelated_link = self.root / ".claude" / "skills" / "local-only"
        unrelated_link.parent.mkdir(parents=True)
        make_dir_symlink("../../.agents/skills/local-only", unrelated_link)
        unrelated_before = self.snapshot(unrelated)
        unrelated_link_target = os.readlink(unrelated_link)

        self.run_cli("add", "foo")
        self.run_cli("update", "foo")
        self.run_cli("remove", "foo")

        self.assertEqual(unrelated_before, self.snapshot(unrelated))
        self.assertTrue(unrelated_link.is_symlink())
        self.assertEqual(os.readlink(unrelated_link), unrelated_link_target)
        self.assertFalse((self.root / ".agents" / "skills" / "foo").exists())

    def test_duplicate_and_invalid_names_fail(self):
        self.prepare_repo()

        duplicate = self.run_cli("add", "foo", "foo", check=False)
        invalid = self.run_cli("add", "../foo", check=False)

        self.assertNotEqual(duplicate.returncode, 0)
        self.assertIn("duplicate skill name", duplicate.stderr)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("invalid skill package name", invalid.stderr)

    def test_source_safety_checks_still_apply(self):
        self.prepare_repo()
        skill = self.root / "skills" / "foo"
        os.symlink("SKILL.md", skill / "linked.md")

        result = self.run_cli("add", "foo", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill contains a symlink", result.stderr)
        self.assertFalse((self.root / ".agents").exists())

    def test_excluded_workspace_is_not_traversed(self):
        self.write_skill(
            "foo",
            {
                "SKILL.md": "# Foo\n",
                "evals/foo/workspace/generated.txt": "generated\n",
            },
        )
        workspace = self.root / "skills" / "foo" / "evals" / "foo" / "workspace"
        os.symlink("generated.txt", workspace / "generated-link")
        self.init_git()
        self.commit_all()

        self.run_cli("add", "foo")

        self.assertTrue((self.root / ".agents" / "skills" / "foo" / "SKILL.md").exists())
        self.assertFalse((self.root / ".agents" / "skills" / "foo" / "evals" / "foo" / "workspace").exists())

    def test_remove_failure_restores_snapshot_and_link_before_final_delete(self):
        module = load_sync_module()
        self.prepare_repo()
        self.run_cli("add", "foo")
        sync = module.build_selected_sync_plan(self.root, "remove", ["foo"])[0]

        def fail_replace(src, dst):
            raise OSError("forced remove failure")

        with self.assertRaises(module.SyncError):
            module.remove_install(sync, replace_func=fail_replace)

        self.assertTrue((self.root / ".agents" / "skills" / "foo").exists())
        self.assertEqual(os.readlink(self.root / ".claude" / "skills" / "foo"), "../../.agents/skills/foo")

    def test_remove_backup_delete_failure_restores_snapshot_and_link(self):
        module = load_sync_module()
        self.prepare_repo()
        self.run_cli("add", "foo")
        sync = module.build_selected_sync_plan(self.root, "remove", ["foo"])[0]

        def fail_rmtree(path):
            raise OSError(f"forced delete failure: {path}")

        with self.assertRaises(module.SyncError):
            module.remove_install(sync, rmtree_func=fail_rmtree)

        self.assertTrue(sync.destination.exists())
        self.assertFalse(sync.backup_destination.exists())
        self.assertEqual(os.readlink(sync.claude_link), "../../.agents/skills/foo")

    def test_add_results_report_snapshot_copied_and_link_created(self):
        self.prepare_repo()

        result = self.run_cli("add", "foo")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Added 1 skill package", result.stdout)
        self.assertIn("foo: snapshot copied, link created", result.stdout)
        self.assertNotIn("none", result.stdout)

    def test_update_results_report_link_already_up_to_date_without_contradiction(self):
        self.prepare_repo()
        self.run_cli("add", "foo")

        result = self.run_cli("update", "foo")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Updated 1 skill package", result.stdout)
        self.assertIn("foo: snapshot copied, link already up to date", result.stdout)
        self.assertNotIn("skipped:", result.stdout)
        self.assertNotIn("copied:", result.stdout)
        skill_lines = [line for line in result.stdout.splitlines() if "foo" in line]
        self.assertEqual(len(skill_lines), 1)

    def test_update_results_report_link_refreshed_when_link_repaired(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        link = self.root / ".claude" / "skills" / "foo"
        link.unlink()
        make_dir_symlink("../../wrong", link)

        result = self.run_cli("update", "foo")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Updated 1 skill package", result.stdout)
        self.assertIn("foo: snapshot copied, link refreshed", result.stdout)

    def test_remove_results_report_snapshot_and_link_removed(self):
        self.prepare_repo()
        self.run_cli("add", "foo")

        result = self.run_cli("remove", "foo")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Removed 1 skill package", result.stdout)
        self.assertIn("foo: snapshot removed, link removed", result.stdout)
        self.assertNotIn("none", result.stdout)

    def test_add_multiple_results_list_one_line_per_skill(self):
        self.prepare_repo()

        result = self.run_cli("add", "foo", "bar")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Added 2 skill package", result.stdout)
        self.assertIn("foo: snapshot copied, link created", result.stdout)
        self.assertIn("bar: snapshot copied, link created", result.stdout)
        per_skill_lines = [line for line in result.stdout.splitlines() if line.startswith("  ")]
        self.assertEqual(len(per_skill_lines), 2)

    def test_add_all_installs_all_sources(self):
        self.prepare_repo()

        self.run_cli("add", "--all")

        for name in ("foo", "bar"):
            destination = self.root / ".agents" / "skills" / name
            self.assertTrue(destination.is_dir())
            self.assertFalse(destination.is_symlink())
            self.assertEqual(
                os.readlink(self.root / ".claude" / "skills" / name),
                f"../../.agents/skills/{name}",
            )

    def test_update_all_refreshes_all_installed(self):
        self.prepare_repo()
        self.run_cli("add", "foo", "bar")
        (self.root / "skills" / "foo" / "new.md").write_text("new\n", encoding="utf-8")
        (self.root / "skills" / "bar" / "extra.md").write_text("extra\n", encoding="utf-8")
        self.commit_all("update sources")

        self.run_cli("update", "--all")

        self.assertEqual(
            (self.root / ".agents" / "skills" / "foo" / "new.md").read_text(encoding="utf-8"),
            "new\n",
        )
        self.assertEqual(
            (self.root / ".agents" / "skills" / "bar" / "extra.md").read_text(encoding="utf-8"),
            "extra\n",
        )

    def test_remove_all_removes_managed_preserves_unmanaged(self):
        self.prepare_repo()
        self.run_cli("add", "foo", "bar")
        unrelated = self.root / ".agents" / "skills" / "local-only"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("local\n", encoding="utf-8")
        unrelated_link = self.root / ".claude" / "skills" / "local-only"
        make_dir_symlink("../../.agents/skills/local-only", unrelated_link)
        unrelated_before = self.snapshot(unrelated)
        unrelated_link_target = os.readlink(unrelated_link)

        self.run_cli("remove", "--all")

        self.assertFalse((self.root / ".agents" / "skills" / "foo").exists())
        self.assertFalse((self.root / ".agents" / "skills" / "bar").exists())
        self.assertFalse((self.root / ".claude" / "skills" / "foo").exists())
        self.assertFalse((self.root / ".claude" / "skills" / "bar").exists())
        self.assertEqual(unrelated_before, self.snapshot(unrelated))
        self.assertTrue(unrelated_link.is_symlink())
        self.assertEqual(os.readlink(unrelated_link), unrelated_link_target)

    def test_all_dry_run_writes_nothing(self):
        self.prepare_repo()
        before = self.snapshot()

        for args in (
            ("--dry-run", "add", "--all"),
            ("add", "--all", "--dry-run"),
            ("add", "--dry-run", "--all"),
        ):
            with self.subTest(args=args):
                result = self.run_cli(*args)

                self.assertEqual(result.returncode, 0)
                self.assertIn("Dry run: add 2 skill package", result.stdout)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.root / ".agents").exists())
                self.assertFalse((self.root / ".claude").exists())

    def test_subcommand_all_appears_in_help(self):
        self.prepare_repo()

        for command in ("add", "update", "remove"):
            with self.subTest(command=command):
                result = self.run_cli(command, "--help")

                self.assertIn("--all", result.stdout)

    def test_all_and_explicit_names_mutually_exclusive(self):
        self.prepare_repo()

        for command in ("add", "update", "remove"):
            with self.subTest(command=command):
                result = self.run_cli(command, "--all", "foo", check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("mutually exclusive", result.stderr)
                self.assertFalse((self.root / ".agents").exists())

    def test_subcommand_requires_names_or_all(self):
        self.prepare_repo()

        for command in ("add", "update", "remove"):
            with self.subTest(command=command):
                result = self.run_cli(command, check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("required", result.stderr)
                self.assertFalse((self.root / ".agents").exists())

    def test_add_all_empty_skills_dir_errors(self):
        (self.root / "skills").mkdir()
        before = self.snapshot()

        for command in ("add", "update"):
            with self.subTest(command=command):
                result = self.run_cli(command, "--all", check=False)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("no skill packages found under skills/", result.stderr)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.root / ".agents").exists())

    def test_remove_all_no_managed_snapshots_errors(self):
        self.prepare_repo()
        before = self.snapshot()

        result = self.run_cli("remove", "--all", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no managed skill snapshots found under .agents/skills/", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_remove_all_skips_reserved_temp_backup_and_unmanaged(self):
        module = load_sync_module()
        self.prepare_repo()
        self.run_cli("add", "foo")
        agent_skills = self.root / ".agents" / "skills"
        # Crash-leftover backup carrying a manifest valid for its own name, so the
        # leading-dot exclusion is the only thing keeping it out of the discovered
        # set (the manifest filter and per-skill validation would both accept it).
        leftover = agent_skills / ".bar.agent-skills-sync.backup"
        shutil.copytree(agent_skills / "foo", leftover)
        digest = json.loads(
            (leftover / module.MANIFEST_NAME).read_text(encoding="utf-8")
        )["tree_digest"]
        module.write_manifest(leftover, leftover.name, digest)
        self.assertTrue((leftover / module.MANIFEST_NAME).is_file())
        unmanaged = agent_skills / "local-only"
        unmanaged.mkdir()
        (unmanaged / "SKILL.md").write_text("local\n", encoding="utf-8")

        self.run_cli("remove", "--all")

        self.assertFalse((agent_skills / "foo").exists())
        self.assertTrue(leftover.exists())
        self.assertTrue((leftover / module.MANIFEST_NAME).is_file())
        self.assertTrue(unmanaged.exists())

    def test_remove_all_skips_symlinked_entry(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        agent_skills = self.root / ".agents" / "skills"
        external = self.root / "external-skill"
        external.mkdir()
        (external / "SKILL.md").write_text("external\n", encoding="utf-8")
        # The symlink target carries a regular-file manifest, so only the symlink
        # exclusion (not the manifest filter) keeps the symlinked entry out of the
        # discovered set.
        (external / ".agent-skills-sync.json").write_text("{}\n", encoding="utf-8")
        make_dir_symlink("../../external-skill", agent_skills / "linked")

        self.run_cli("remove", "--all")

        self.assertFalse((agent_skills / "foo").exists())
        self.assertTrue((agent_skills / "linked").is_symlink())

    def test_update_all_preflight_blocks_on_one_dirty_source(self):
        self.prepare_repo()
        self.run_cli("add", "foo", "bar")
        # bar sorts first and has a committed update that an interleaved
        # (non-atomic) impl would apply before reaching the dirty member.
        bar_dest = self.root / ".agents" / "skills" / "bar"
        bar_before = self.snapshot(bar_dest)
        (self.root / "skills" / "bar" / "new.md").write_text("new\n", encoding="utf-8")
        self.commit_all("update bar source")
        # foo sorts last and has a dirty (uncommitted) source that must block the
        # whole batch at preflight.
        (self.root / "skills" / "foo" / "SKILL.md").write_text("# Dirty Foo\n", encoding="utf-8")

        result = self.run_cli("update", "--all", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source skill has working tree changes", result.stderr)
        self.assertEqual(bar_before, self.snapshot(bar_dest))
        self.assertFalse((bar_dest / "new.md").exists())

    def test_remove_all_preflight_blocks_on_one_owned_dirty_member(self):
        self.prepare_repo()
        self.run_cli("add", "foo", "bar")
        # foo sorts last and is the invalid (dirty) member; bar sorts first and is
        # valid, so an interleaved (non-atomic) impl would delete bar before
        # failing on foo.
        (self.root / ".agents" / "skills" / "foo" / "local.txt").write_text(
            "local change\n", encoding="utf-8"
        )

        result = self.run_cli("remove", "--all", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination has local changes", result.stderr)
        self.assertTrue((self.root / ".agents" / "skills" / "bar").exists())
        self.assertTrue((self.root / ".claude" / "skills" / "bar").is_symlink())
        self.assertTrue((self.root / ".agents" / "skills" / "foo").exists())

    def test_update_all_errors_when_a_source_not_installed(self):
        self.prepare_repo()
        self.run_cli("add", "foo")
        before = self.snapshot()

        result = self.run_cli("update", "--all", check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination is not installed; use add", result.stderr)
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main()
