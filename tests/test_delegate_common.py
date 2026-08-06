"""Hermetic tests for shared delegation scope and fingerprint helpers."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "vibe-orchestrate" / "scripts"
if not SCRIPT_DIR.is_dir():
    SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import delegate_common as M  # noqa: E402


def completed(stdout: bytes = b"", returncode: int = 0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(["git"], returncode, stdout, b"")


class DelegateCommonTests(unittest.TestCase):
    def test_manifest_full_record_detects_mode_empty_directory_and_symlink_target(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            tracked = work / "tracked.txt"
            tracked.write_text("same bytes\n", encoding="utf-8")
            link = work / "link"
            link.symlink_to("tracked.txt")
            baseline, error = M.filesystem_manifest(work, 20, 1000)
            self.assertIsNone(error)
            self.assertEqual(len(baseline["tracked.txt"].split(":")), 9)
            tracked.chmod(0o755)
            changed, error = M.filesystem_manifest(work, 20, 1000)
            self.assertIsNone(error)
            self.assertEqual(M.manifest_changed_paths(baseline, changed), ["tracked.txt"])
            tracked.chmod(0o644)
            restored, _ = M.filesystem_manifest(work, 20, 1000)
            (work / "empty").mkdir()
            with_empty, _ = M.filesystem_manifest(work, 20, 1000)
            self.assertEqual(M.manifest_changed_paths(restored, with_empty), ["empty"])
            os.unlink(link)
            link.symlink_to("other.txt")
            retargeted, _ = M.filesystem_manifest(work, 20, 1000)
            self.assertIn("link", M.manifest_changed_paths(with_empty, retargeted))

    def test_manifest_entry_count_ceiling(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            (work / "one").write_text("1", encoding="utf-8")
            manifest, error = M.filesystem_manifest(work, 1, 100)
            self.assertIsNone(manifest)
            self.assertIn("file count exceeds 1", error)

    def test_manifest_total_byte_ceiling(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            (work / "one").write_bytes(b"1234")
            (work / "two").write_bytes(b"5678")
            manifest, error = M.filesystem_manifest(work, 20, 7)
            self.assertIsNone(manifest)
            self.assertEqual(error, "manifest total bytes exceeds 7")

    def test_manifest_unreadable_directory_is_unavailable(self):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            unreadable = work / "unreadable"
            unreadable.mkdir()
            (unreadable / "hidden.txt").write_text("hidden\n", encoding="utf-8")
            unreadable.chmod(0)
            try:
                manifest, error = M.filesystem_manifest(work, 20, 1000)
                self.assertIsNone(manifest)
                self.assertIn("PermissionError", error)
            finally:
                unreadable.chmod(0o700)

    def test_git_metadata_snapshot_detects_staged_file_and_new_ref(self):
        state = {"index": b"baseline", "refs": b"refs/heads/main\0aaa\n"}

        def fake_run_git(_cwd, *arguments):
            if arguments == ("rev-parse", "--verify", "HEAD"):
                return completed(b"aaa\n")
            if arguments == ("symbolic-ref", "--quiet", "HEAD"):
                return completed(b"refs/heads/main\n")
            if arguments[0] == "for-each-ref":
                return completed(state["refs"])
            if arguments == ("ls-files", "--stage", "-z"):
                return completed(state["index"])
            if arguments == ("ls-files", "-v", "-z"):
                return completed(b"H tracked.txt\0")
            raise AssertionError(arguments)

        with mock.patch.object(M, "run_git", side_effect=fake_run_git):
            baseline = M.git_metadata_snapshot(Path("/unused"))
            state["index"] = b"staged"
            self.assertNotEqual(M.git_metadata_snapshot(Path("/unused")), baseline)
            state["index"] = b"baseline"
            state["refs"] += b"refs/heads/worker\0aaa\n"
            self.assertNotEqual(M.git_metadata_snapshot(Path("/unused")), baseline)

    def test_normalize_allowed_paths_rejects_root_absolute_and_traversal(self):
        self.assertEqual(
            M.normalize_allowed_paths(["result.txt", "docs/report.md", "result.txt"]),
            (["docs/report.md", "result.txt"], None),
        )
        for value in ("", ".", "/tmp/result.txt", "../result.txt", "docs/../../x"):
            self.assertIsNotNone(M.normalize_allowed_paths([value])[1])

    def test_fingerprint_digest_stability_and_constituent_byte_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = root / "entry.py"
            second = root / "common.py"
            first.write_bytes(b"entry-v1")
            second.write_bytes(b"common-v1")
            value = {"adapter_files": M.adapter_files_sha256([first, second]), "setting": True}
            self.assertEqual(M.fingerprint_digest(value), M.fingerprint_digest(dict(value)))
            original = M.fingerprint_digest(value)
            first.write_bytes(b"entry-v2")
            changed_entry = {"adapter_files": M.adapter_files_sha256([first, second]), "setting": True}
            self.assertNotEqual(M.fingerprint_digest(changed_entry), original)
            first.write_bytes(b"entry-v1")
            second.write_bytes(b"common-v2")
            changed_common = {"adapter_files": M.adapter_files_sha256([first, second]), "setting": True}
            self.assertNotEqual(M.fingerprint_digest(changed_common), original)

    def test_worker_report_schema_and_validation(self):
        good = {
            "files": ["x"],
            "compile": {"status": "SKIPPED", "detail": "n/a"},
            "decisions": [],
            "blockers": [],
        }
        self.assertTrue(M.validate_worker_report(good))
        self.assertEqual(M.worker_report_schema()["required"], ["files", "compile", "decisions", "blockers"])
        self.assertFalse(M.validate_worker_report({**good, "extra": True}))


if __name__ == "__main__":
    unittest.main()
