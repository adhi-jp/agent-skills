"""Execute the read-only history-query examples against disposable Git objects."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path(os.environ.get(
    "VIBE_COMMIT_HISTORY_REFERENCE",
    REPO_ROOT / "skills/vibe-commit/references/history-and-trailers.md",
))
GIT = shutil.which("git")
BASH = shutil.which("bash")


def source_block(marker):
    blocks = re.findall(r"```(?:sh|bash)\n(.*?)\n```", REFERENCE.read_text(), re.S)
    matches = [block for block in blocks if marker in block]
    if len(matches) != 1:
        raise AssertionError(f"Expected one source block containing {marker!r}")
    return matches[0]


@unittest.skipUnless(GIT and BASH, "Git and Bash are required")
class HistoryPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="vibe-history-example-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.scratch = self.root / "scratch"
        self.scratch.mkdir()
        self.env = os.environ.copy()
        self.env.update({
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@example.test",
            "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@example.test",
            "GIT_AUTHOR_DATE": "2001-01-01T00:00:00+0000",
            "GIT_COMMITTER_DATE": "2001-01-01T00:00:00+0000",
            "TMPDIR": str(self.scratch),
        })
        # Object plumbing supplies history without staging, branch updates, or rewrites.
        self.git("init", "-q")
        blob = self.git("hash-object", "-w", "--stdin", data=b"fixture\n")
        empty = self.tree({})
        self.base = self.commit(empty)
        nested = self.tree({"child.md": ("blob", blob)})
        names = ["normal.md", "space name.md", "line\nbreak.md", "tab\tname.md", "-leading.md"]
        targets = {name: ("blob", blob) for name in names}
        targets["nested"] = ("tree", nested)
        docs = self.tree({
            "investigations": ("tree", self.tree(targets)),
            "investigations-other": ("tree", nested),
        })
        first_tree = self.tree({"docs": ("tree", docs)})
        self.first = self.commit(first_tree, self.base)
        # The next commit inherits all target paths without changing them.
        second_tree = self.tree({"docs": ("tree", docs), "unrelated.txt": ("blob", blob)})
        self.head = self.commit(second_tree, self.first)
        self.empty_head = self.commit(self.tree({"unrelated.txt": ("blob", blob)}), self.base)
        self.paths = {f"docs/investigations/{name}".encode() for name in names}
        self.paths.add(b"docs/investigations/nested/child.md")
        self.sentinel = self.repo / "live-untracked.txt"
        self.sentinel.write_bytes(b"must remain untouched\n")
        self.head_bytes = (self.repo / ".git/HEAD").read_bytes()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.trace = self.root / "commands.jsonl"
        shim = self.bin / "git"
        shim.write_text("#!/usr/bin/env python3\n" + '''import json, os, sys
args = sys.argv[1:]
with open(os.environ["HISTORY_QUERY_TRACE"], "a") as stream:
    stream.write(json.dumps(args) + "\\n")
if not args or args[0] not in {"rev-list", "ls-tree"}:
    sys.exit("non-query Git operation forbidden in preview test")
fault = os.environ.get("HISTORY_QUERY_FAULT", "")
if args[0] == "ls-tree":
    if fault == "invalid-tree":
        args[args.index("--") - 1] = "missing-tree-for-test"
    elif fault == "invalid-option":
        args.insert(1, "--exit-code")
    elif fault == "partial-query":
        os.write(1, b"docs/investigations/partial.md\\0")
        sys.exit(2)
os.execv(os.environ["HISTORY_REAL_GIT"], [os.environ["HISTORY_REAL_GIT"], *args])
''')
        shim.chmod(0o755)
        self.env.update({
            "PATH": str(self.bin) + os.pathsep + self.env.get("PATH", ""),
            "HISTORY_QUERY_TRACE": str(self.trace), "HISTORY_REAL_GIT": GIT,
        })

    def git(self, *args, data=None):
        result = subprocess.run([GIT, *args], cwd=self.repo, env=self.env,
                                input=data, capture_output=True, check=True)
        return result.stdout.decode().strip()

    def tree(self, entries):
        payload = b"".join(
            f"{'040000' if kind == 'tree' else '100644'} {kind} {oid}\t".encode()
            + name.encode() + b"\0"
            for name, (kind, oid) in sorted(entries.items())
        )
        return self.git("mktree", "-z", data=payload)

    def commit(self, tree, parent=None):
        args = ["commit-tree", tree]
        if parent:
            args += ["-p", parent]
        return self.git(*args, data=b"fixture history\n")

    def preview(self, base=None, head=None, fault=""):
        env = self.env | {"base": base or self.base, "old_head": head or self.head,
                          "HISTORY_QUERY_FAULT": fault}
        result = subprocess.run([BASH, "-c", source_block("# Pass 1:")],
                                cwd=self.repo, env=env, capture_output=True)
        self.assertEqual(self.sentinel.read_bytes(), b"must remain untouched\n")
        self.assertEqual((self.repo / ".git/HEAD").read_bytes(), self.head_bytes)
        self.assertFalse((self.repo / ".git/index").exists())
        commands = [json.loads(line) for line in self.trace.read_text().splitlines()]
        self.assertTrue(all(command[0] in {"rev-list", "ls-tree"} for command in commands))
        return result

    def preview_dir(self):
        directories = list(self.scratch.glob("rewrite-preview.*"))
        self.assertEqual(len(directories), 1)
        return directories[0]

    def test_full_trees_include_inherited_paths_and_preserve_nul_names(self):
        result = self.preview()
        self.assertEqual(result.returncode, 0, result.stderr)
        directory = self.preview_dir()
        for commit in (self.first, self.head):
            data = (directory / f"{commit}.paths").read_bytes()
            self.assertTrue(data.endswith(b"\0"))
            self.assertEqual(set(data[:-1].split(b"\0")), self.paths)
        lines = (directory / "targets.txt").read_text().splitlines()
        self.assertEqual(len(lines), 2 * len(self.paths))
        recovered = set()
        for line in lines:
            commit, quoted_path = line.split("\t", 1)
            # Decode only Bash's own %q output, never an arbitrary generated command.
            decoded = subprocess.run([BASH, "-c", 'printf "%s" ' + quoted_path],
                                     capture_output=True, check=True).stdout
            recovered.add((commit, decoded))
        self.assertEqual(recovered, {(commit, path) for commit in (self.first, self.head)
                                     for path in self.paths})

    def test_valid_trees_with_no_targets_produce_empty_successful_preview(self):
        result = self.preview(head=self.empty_head)
        self.assertEqual(result.returncode, 0, result.stderr)
        directory = self.preview_dir()
        self.assertEqual((directory / "targets.txt").read_bytes(), b"")
        self.assertEqual((directory / f"{self.empty_head}.paths").read_bytes(), b"")

    def test_empty_range_is_success_without_tree_queries(self):
        result = self.preview(head=self.base)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.preview_dir() / "targets.txt").read_bytes(), b"")
        self.assertNotIn('"ls-tree"', self.trace.read_text())

    def test_invalid_range_stops_before_tree_queries_or_preview(self):
        result = self.preview(base="missing-base-for-test")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"cannot enumerate the requested range", result.stderr)
        self.assertEqual(list(self.scratch.iterdir()), [])
        self.assertNotIn('"ls-tree"', self.trace.read_text())

    def test_invalid_tree_is_not_an_empty_success(self):
        self.assert_failed_tree_query("invalid-tree")

    def test_invalid_option_is_not_an_empty_success(self):
        self.assert_failed_tree_query("invalid-option")

    def test_partial_output_from_failed_query_is_not_published(self):
        self.assert_failed_tree_query("partial-query")

    def assert_failed_tree_query(self, fault):
        result = self.preview(fault=fault)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"preview incomplete", result.stderr)
        self.assertEqual(result.stdout, b"")
        self.assertFalse((self.preview_dir() / "targets.txt").exists())

    def test_other_range_consumers_check_queries_before_using_results(self):
        reference = REFERENCE.read_text()
        self.assertNotRegex(reference, r"for \w+ in \$\(git rev-list")
        # Exercise the real query guards, stopping before their mutation-bearing loops.
        blocks = [source_block("new_commits=$(git rev-list"),
                  source_block("parents=$(git rev-list")]
        for block, assignment, message, env in [
            (blocks[0], "new_commits=", "cannot enumerate the rewritten range",
             {"base": "missing-base-for-test"}),
            (blocks[1], "parents=", "cannot inspect parents",
             {"old_commit": "missing-commit-for-test"}),
        ]:
            with self.subTest(assignment=assignment):
                guard = re.search(r"(?m)^\s*if ! " + assignment + r".*?\n\s*fi", block, re.S)
                self.assertIsNotNone(guard)
                result = subprocess.run([BASH, "-c", guard.group() + '\nprintf "consumed"'],
                                        cwd=self.repo, env=self.env | env, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message.encode(), result.stderr)
                self.assertEqual(result.stdout, b"")


if __name__ == "__main__":
    unittest.main()
