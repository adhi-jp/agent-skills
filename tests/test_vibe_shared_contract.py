import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "vibe_shared_contract.py"

PRECEDENCE = "Where a package declares a stricter or narrower rule in its own text, that declaration controls."
APPLICABILITY = (
    "A package may state which of its phases this gate applies to; "
    "it may not change the gate's inputs, outcomes, or fields."
)
CITATION = "shared/vibe-contract.md"
BODY = "Evidence carries one of four classes.\n" + PRECEDENCE + "\n"
GATE_BODY = "Observable input: a history-mutating command.\n" + APPLICABILITY + "\n"
CLASS_LINE = "<!-- shared-contract:class language=none commit=none effect=read-only -->"

# A block in the scannable shape: bold imperative lead, bullets, one exception line.
SHAPE_LEAD = "**Never let a delegated claim stand as proof.**"
SHAPE_BULLETS = (
    "- Verify every load-bearing claim against evidence this phase holds itself.\n"
    "- Keep the finding inert until that verification lands.\n"
)
SHAPE_EXCEPTION = "Exception: a claim the current user states directly needs no re-verification.\n"
NEW_BODY = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + "\n" + SHAPE_EXCEPTION + PRECEDENCE + "\n"
NEW_BODY_OPEN = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + "\n" + SHAPE_EXCEPTION


def words(count, prefix="word"):
    return " ".join(f"{prefix}{index}" for index in range(1, count + 1))


def can_create_symlink():
    if not hasattr(os, "symlink"):
        return False
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = root / "target"
        target.write_text("x", encoding="utf-8")
        link = root / "link"
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError):
            return False
        return link.is_symlink()


CAN_CREATE_SYMLINK = can_create_symlink()


def load_module():
    spec = importlib.util.spec_from_file_location("vibe_shared_contract", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def begin_marker(block_id, cite=True):
    if cite:
        return f"<!-- shared-contract:begin {block_id} source={CITATION} -->"
    return f"<!-- shared-contract:begin {block_id} -->"


def end_marker(block_id):
    return f"<!-- shared-contract:end {block_id} -->"


def marked_file(name, block_id, content="", class_line=CLASS_LINE, cite=True, heading="# Skill"):
    lines = [f"---\nname: {name}\n---\n\n{heading}\n\nIntro text.\n\n"]
    if class_line:
        lines.append(class_line + "\n")
    lines.append(begin_marker(block_id, cite) + "\n")
    lines.append(content)
    lines.append(end_marker(block_id) + "\n\nTrailing text.\n")
    return "".join(lines)


def closing_file(name, block_id, content="", closing="", class_line=CLASS_LINE, gap=""):
    """A package entry file whose class line is followed by the closing block, then one block."""
    lines = [f"---\nname: {name}\n---\n\n# Skill\n\nIntro text.\n\n"]
    lines.append(class_line + "\n" + gap)
    lines.append(begin_marker("closing") + "\n")
    lines.append(closing)
    lines.append(end_marker("closing") + "\n\n")
    lines.append(begin_marker(block_id) + "\n")
    lines.append(content)
    lines.append(end_marker(block_id) + "\n\nTrailing text.\n")
    return "".join(lines)


class VibeSharedContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "skills"
        self.root.mkdir()
        self.source = self.base / "vibe-contract.md"

    def tearDown(self):
        self.tmp.cleanup()

    # --- fixture helpers -----------------------------------------------------

    def write_source(self, blocks, preamble="# Shared contract\n\nProse mentions `shared-contract:begin` safely.\n\n"):
        parts = [preamble]
        for block_id, dependents, body in blocks:
            parts.append(f"<!-- shared-contract:block {block_id} dependents={','.join(dependents)} -->\n")
            parts.append(body)
            parts.append(f"<!-- shared-contract:endblock {block_id} -->\n\n")
        self.source.write_text("".join(parts), encoding="utf-8")
        return self.source

    def write_raw_source(self, text):
        self.source.write_text(text, encoding="utf-8")
        return self.source

    def write_package(self, name, files=None):
        files = files or {"SKILL.md": f"---\nname: {name}\n---\n\n# {name}\n\nPlain package text.\n"}
        package_dir = self.root / name
        for rel, content in files.items():
            path = package_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="")
        return package_dir

    def run_cli(self, *args, root=None, source=None, expect=None):
        command = [sys.executable, str(SCRIPT), *map(str, args)]
        if root is not False:
            command += ["--root", str(root or self.root)]
        if source is not False and args[0] != "audit-names":
            command += ["--source", str(source or self.source)]
        result = subprocess.run(command, cwd=self.base, text=True, capture_output=True, check=False)
        if expect is not None and result.returncode != expect:
            self.fail(
                f"expected exit {expect}, got {result.returncode}: {command}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def check(self, *extra, expect=None, root=None):
        return self.run_cli("check", *extra, expect=expect, root=root)

    def render(self, *extra, expect=None):
        return self.run_cli("render", *extra, expect=expect)

    def standard_tree(self, content=BODY, class_line=CLASS_LINE):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", content, class_line)})
        return self.root / "vibe-alpha" / "SKILL.md"

    # --- generator states ----------------------------------------------------

    def test_render_pristine_pair_is_filled_byte_equal_to_source(self):
        skill = self.standard_tree(content="")
        before = skill.read_bytes()
        self.assertIn(b"-->\n<!-- shared-contract:end", before)
        result = self.render(expect=0)
        self.assertIn("rendered skills/vibe-alpha/SKILL.md evidence-classes (pristine)", result.stdout)
        after = skill.read_text(encoding="utf-8")
        expected = marked_file("vibe-alpha", "evidence-classes", BODY)
        self.assertEqual(after, expected)
        self.assertIn(begin_marker("evidence-classes") + "\n" + BODY + end_marker("evidence-classes"), after)
        self.check(expect=0)

    def test_render_pristine_pair_holding_only_blank_lines_is_filled(self):
        skill = self.standard_tree(content="\n\n")
        self.render(expect=0)
        self.assertEqual(skill.read_text(encoding="utf-8"), marked_file("vibe-alpha", "evidence-classes", BODY))

    def test_render_identical_block_is_noop_bytes_and_mtime_unchanged(self):
        skill = self.standard_tree(content=BODY)
        before = skill.read_bytes()
        stamp = 1_600_000_000
        os.utime(skill, (stamp, stamp))
        result = self.render(expect=0)
        self.assertIn("unchanged skills/vibe-alpha/SKILL.md evidence-classes", result.stdout)
        self.assertIn("0 block(s) written", result.stdout)
        self.assertEqual(skill.read_bytes(), before)
        self.assertEqual(int(skill.stat().st_mtime), stamp)

    def test_render_drifted_block_refuses_with_unified_diff(self):
        drifted = "Evidence carries one of four classes.\nHand-edited line.\n" + PRECEDENCE + "\n"
        skill = self.standard_tree(content=drifted)
        before = skill.read_bytes()
        result = self.render(expect=1)
        self.assertIn("drifted", result.stdout)
        self.assertIn("--- source:evidence-classes", result.stdout)
        self.assertIn("+++ skills/vibe-alpha/SKILL.md:evidence-classes", result.stdout)
        self.assertIn("+Hand-edited line.", result.stdout)
        self.assertEqual(skill.read_bytes(), before)

    def test_render_drifted_block_force_overwrites(self):
        drifted = "Completely different text.\n"
        skill = self.standard_tree(content=drifted)
        result = self.render("--force", expect=0)
        self.assertIn("rendered skills/vibe-alpha/SKILL.md evidence-classes (drifted)", result.stdout)
        self.assertEqual(skill.read_text(encoding="utf-8"), marked_file("vibe-alpha", "evidence-classes", BODY))

    def test_render_refuses_before_writing_when_any_check_error_exists(self):
        self.write_source([("evidence-classes", ["vibe-alpha", "vibe-beta"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", "")})
        self.write_package("vibe-beta", {"SKILL.md": marked_file("vibe-beta", "no-such-block", "")})
        alpha = self.root / "vibe-alpha" / "SKILL.md"
        before = alpha.read_bytes()
        result = self.render(expect=1)
        self.assertIn("unknown block id no-such-block", result.stdout)
        self.assertEqual(alpha.read_bytes(), before)

    def test_render_atomic_write_leaves_no_partial_file_on_failure(self):
        module = load_module()
        skill = self.standard_tree(content="")
        before = skill.read_bytes()
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(module.os, "replace", side_effect=OSError("simulated rename failure")):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                code = module.main(["render", "--root", str(self.root), "--source", str(self.source)])
        self.assertEqual(code, 2)
        self.assertIn("failed to write skills/vibe-alpha/SKILL.md", stderr.getvalue())
        self.assertEqual(skill.read_bytes(), before)
        leftovers = [p.name for p in skill.parent.iterdir() if p.name != "SKILL.md"]
        self.assertEqual(leftovers, [])

    def test_render_package_filter_writes_only_that_package(self):
        self.write_source([("evidence-classes", ["vibe-alpha", "vibe-beta"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", "")})
        beta = self.write_package("vibe-beta", {"SKILL.md": marked_file("vibe-beta", "evidence-classes", "")})
        beta_before = (beta / "SKILL.md").read_bytes()
        result = self.render("--package", "vibe-alpha", expect=0)
        self.assertIn("rendered skills/vibe-alpha/SKILL.md evidence-classes (pristine)", result.stdout)
        self.assertNotIn("vibe-beta", result.stdout)
        self.assertEqual((beta / "SKILL.md").read_bytes(), beta_before)
        self.assertEqual(
            (self.root / "vibe-alpha" / "SKILL.md").read_text(encoding="utf-8"),
            marked_file("vibe-alpha", "evidence-classes", BODY),
        )
        self.check("--package", "vibe-alpha", expect=0)
        self.check("--package", "vibe-beta", expect=1)
        self.render("--package", "vibe-gamma", expect=2)

    # --- check: marker refusals ----------------------------------------------

    def test_check_pristine_pair_fails_check(self):
        self.standard_tree(content="")
        result = self.check(expect=1)
        self.assertIn("block evidence-classes is pristine (not rendered)", result.stdout)

    def test_check_drifted_block_fails_check_with_diff(self):
        self.standard_tree(content="Different.\n")
        result = self.check(expect=1)
        self.assertIn("block evidence-classes drifted from the source", result.stdout)
        self.assertIn("-Evidence carries one of four classes.", result.stdout)

    def test_check_identical_block_passes(self):
        self.standard_tree(content=BODY)
        result = self.check(expect=0)
        self.assertIn("0 error(s), 1 warning(s)", result.stdout)
        self.assertIn("legacy-shape block (no bold lead line)", result.stdout)
        strict = self.check("--strict", expect=0)
        self.assertIn("0 error(s), 0 warning(s)", strict.stdout)

    def test_check_unknown_block_id_in_marker_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "mystery-block", BODY)})
        result = self.check(expect=1)
        self.assertIn("unknown block id mystery-block", result.stdout)

    def test_check_duplicate_package_block_pair_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package(
            "vibe-alpha",
            {
                "SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY),
                "references/extra.md": marked_file("vibe-alpha", "evidence-classes", BODY, class_line=None),
            },
        )
        result = self.check(expect=1)
        self.assertIn("duplicate block evidence-classes in package vibe-alpha", result.stdout)

    def test_check_unbalanced_begin_without_end_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": f"# a\n\n{begin_marker('evidence-classes')}\n{BODY}"})
        result = self.check(expect=1)
        self.assertIn("begin marker evidence-classes is never closed", result.stdout)

    def test_check_nested_markers_fail(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY), ("model-tier-selection", ["vibe-alpha"], BODY)])
        text = (
            f"# a\n\n{begin_marker('evidence-classes')}\n{begin_marker('model-tier-selection')}\n{BODY}"
            f"{end_marker('model-tier-selection')}\n{end_marker('evidence-classes')}\n"
        )
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.check(expect=1)
        self.assertIn("nested begin marker model-tier-selection inside open block evidence-classes", result.stdout)

    def test_check_unpaired_end_marker_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": f"# a\n\n{BODY}{end_marker('evidence-classes')}\n"})
        result = self.check(expect=1)
        self.assertIn("unpaired end marker evidence-classes", result.stdout)

    def test_check_end_marker_id_mismatch_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        text = f"# a\n\n{begin_marker('evidence-classes')}\n{BODY}{end_marker('other-id')}\n"
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.check(expect=1)
        self.assertIn("end marker other-id does not close begin marker evidence-classes", result.stdout)

    def test_check_marker_block_id_starting_with_vibe_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "vibe-evidence", BODY)})
        result = self.check(expect=1)
        self.assertIn("block id must not start with 'vibe-': vibe-evidence", result.stdout)

    def test_check_source_block_id_starting_with_vibe_fails(self):
        self.write_source([("vibe-evidence", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("block id must not start with 'vibe-': vibe-evidence", result.stdout)

    def test_check_marker_keyword_starting_with_vibe_is_malformed(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        text = f"# a\n\n<!-- shared-contract:vibe-begin evidence-classes -->\n{BODY}{end_marker('evidence-classes')}\n"
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.check(expect=1)
        self.assertIn("unknown marker keyword 'vibe-begin'", result.stdout)

    def test_check_invalid_block_id_format_fails(self):
        self.write_source([("Evidence--Classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("invalid block id: Evidence--Classes", result.stdout)

    def test_check_duplicate_block_id_in_source_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY), ("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("duplicate block id evidence-classes", result.stdout)

    def test_check_unclosed_source_block_fails(self):
        self.write_raw_source(f"<!-- shared-contract:block evidence-classes dependents=vibe-alpha -->\n{BODY}")
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("block evidence-classes is never closed", result.stdout)

    def test_check_dependent_not_existing_package_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha", "vibe-ghost"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY)})
        result = self.check(expect=1)
        self.assertIn("dependent is not an existing package: vibe-ghost", result.stdout)

    def test_check_marker_in_package_not_listed_as_dependent_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY)})
        self.write_package("vibe-beta", {"SKILL.md": marked_file("vibe-beta", "evidence-classes", BODY)})
        result = self.check(expect=1)
        self.assertIn("package vibe-beta is not a listed dependent of block evidence-classes", result.stdout)

    def test_check_wrong_begin_marker_source_attribute_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        text = f"# a\n\n<!-- shared-contract:begin evidence-classes source=elsewhere.md -->\n{BODY}{end_marker('evidence-classes')}\n"
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.check(expect=1)
        self.assertIn("begin marker source must be shared/vibe-contract.md: elsewhere.md", result.stdout)

    def test_check_begin_marker_without_source_attribute_is_malformed(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY, cite=False)})
        result = self.check(expect=1)
        self.assertIn("malformed begin marker (expected '<!-- shared-contract:begin <id> source=shared/vibe-contract.md -->')", result.stdout)

    def test_check_fenced_marker_example_in_source_block_is_not_a_marker(self):
        body = (
            "Dependents carry a pair like this:\n\n```markdown\n"
            f"{begin_marker('evidence-classes')}\n{end_marker('evidence-classes')}\n"
            "<!-- shared-contract:endblock evidence-classes -->\n```\n\n" + PRECEDENCE + "\n"
        )
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", body)})
        result = self.check("--strict", expect=0)
        self.assertIn("0 error(s), 0 warning(s)", result.stdout)
        listing = self.run_cli("list", root=False, expect=0)
        self.assertEqual(listing.stdout.count("\n"), 1)

    def test_check_fenced_marker_example_in_package_file_is_not_a_marker(self):
        example = (
            "\n## Marker grammar\n\n~~~\n"
            f"{begin_marker('model-tier-selection')}\n{end_marker('model-tier-selection')}\n"
            "<!-- shared-contract:class language=chat commit=none effect=read-only -->\n~~~\n"
        )
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY) + example})
        result = self.check("--strict", expect=0)
        self.assertIn("0 error(s), 0 warning(s)", result.stdout)

    def test_check_unclosed_fence_does_not_hide_markers(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        text = "# a\n\n```\nnever closed\n\n" + marked_file("vibe-alpha", "evidence-classes", BODY, heading="")
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.check("--strict", expect=0)
        self.assertIn("0 error(s), 0 warning(s)", result.stdout)

    # --- check: containment --------------------------------------------------

    @unittest.skipUnless(CAN_CREATE_SYMLINK, "symlink support required")
    def test_check_symlinked_file_on_candidate_path_refused(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY)})
        outside = self.base / "outside.md"
        outside.write_text("# outside\n", encoding="utf-8")
        (self.root / "vibe-alpha" / "references").mkdir()
        os.symlink(outside, self.root / "vibe-alpha" / "references" / "linked.md")
        result = self.check(expect=2)
        self.assertIn("is a symlink", result.stderr)
        self.assertIn("linked.md", result.stderr)

    @unittest.skipUnless(CAN_CREATE_SYMLINK, "symlink support required")
    def test_check_symlinked_package_directory_escaping_temporary_root_refused(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY)})
        outside = self.base / "outside-package"
        outside.mkdir()
        (outside / "SKILL.md").write_text("# outside\n", encoding="utf-8")
        os.symlink(outside, self.root / "vibe-linked", target_is_directory=True)
        result = self.check(expect=2)
        self.assertIn("package directory is a symlink", result.stderr)
        for command in (("render",), ("audit-names",)):
            result = self.run_cli(*command, expect=2)
            self.assertIn("package directory is a symlink", result.stderr)

    def test_containment_refuses_path_outside_default_root(self):
        module = load_module()
        default_root = module.resolve_root(None)
        self.assertEqual(default_root, (REPO_ROOT / "skills").resolve())
        with self.assertRaises(module.ContractError) as ctx:
            module.ensure_within(REPO_ROOT / "skills" / ".." / "README.md", default_root)
        self.assertIn("resolves outside the root", str(ctx.exception))
        module.ensure_within(REPO_ROOT / "skills" / "vibe-coding" / "SKILL.md", default_root)

    def test_containment_refuses_path_outside_temporary_root(self):
        module = load_module()
        root = module.resolve_root(self.root)
        with self.assertRaises(module.ContractError) as ctx:
            module.ensure_within(self.root / "vibe-alpha" / ".." / ".." / "escaped.md", root)
        self.assertIn("resolves outside the root", str(ctx.exception))
        module.ensure_within(self.root / "vibe-alpha" / "SKILL.md", root)

    def test_check_missing_root_is_fatal(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        result = self.check(expect=2, root=self.base / "nowhere")
        self.assertIn("root does not exist", result.stderr)

    @unittest.skipUnless(CAN_CREATE_SYMLINK, "symlink support required")
    def test_root_beneath_intermediate_symlink_is_refused(self):
        real = self.base / "real"
        (real / "skills").mkdir(parents=True)
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        (real / "skills" / "vibe-alpha").mkdir()
        (real / "skills" / "vibe-alpha" / "SKILL.md").write_text(marked_file("vibe-alpha", "evidence-classes", BODY), encoding="utf-8")
        os.symlink(real, self.base / "link", target_is_directory=True)
        linked_root = self.base / "link" / "skills"
        for command in (("check",), ("render",), ("audit-names",)):
            with self.subTest(command=command[0]):
                result = self.run_cli(*command, root=linked_root, expect=2)
                self.assertIn(f"root has a symlinked component: {(self.base / 'link').as_posix()}", result.stderr)
        self.run_cli("check", root=real / "skills", expect=0)

    @unittest.skipUnless(CAN_CREATE_SYMLINK, "symlink support required")
    def test_check_symlinked_entry_escaping_root_reports_containment_refusal(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", "")})
        outside = self.base / "outside.md"
        outside.write_text("# outside\n", encoding="utf-8")
        (self.root / "vibe-alpha" / "references").mkdir()
        os.symlink(outside, self.root / "vibe-alpha" / "references" / "escape.md")
        for command in (("check",), ("render",)):
            with self.subTest(command=command[0]):
                result = self.run_cli(*command, expect=2)
                self.assertIn(f"resolves outside the root {self.root.as_posix()}", result.stderr)
        self.assertIn(b"-->\n<!-- shared-contract:end", (self.root / "vibe-alpha" / "SKILL.md").read_bytes())

    # --- check: source block content -----------------------------------------

    def test_check_heading_inside_source_block_fails(self):
        body = "## Not allowed\n\nText.\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("block evidence-classes contains a Markdown heading: ## Not allowed", result.stdout)

    def test_check_heading_like_line_inside_fenced_code_is_not_a_heading(self):
        body = "Example:\n\n```sh\n# a shell comment\n```\n\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        self.check(expect=0)

    def test_check_specialist_name_inside_source_block_fails(self):
        body = "Hand off to vibe-beta when done.\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        self.write_package("vibe-beta")
        result = self.check(expect=1)
        self.assertIn("block evidence-classes names a vibe-* specialist: vibe-beta", result.stdout)

    def test_check_router_package_name_inside_source_block_fails(self):
        body = "Only vibe-coding may route.\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        self.write_package("vibe-coding")
        result = self.check(expect=1)
        self.assertIn("block evidence-classes names a vibe-* specialist: vibe-coding", result.stdout)

    def test_check_non_roster_vibe_token_inside_source_block_passes(self):
        body = "Records live under `.plans/vibe-sessions/`; vibe-beta is not a package here.\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        result = self.check(expect=0)
        self.assertNotIn("specialist", result.stdout)

    def test_check_token_extending_past_a_roster_name_is_not_that_name(self):
        body = "The vibe-alpha-extension label is not a package name.\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-beta"], body)])
        self.write_package("vibe-alpha")
        self.write_package("vibe-beta")
        self.check(expect=0)

    def test_check_digit_bearing_roster_name_inside_source_block_fails(self):
        body = "Hand off to vibe-x2 when done; vibe-x9 is not a package.\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        self.write_package("vibe-x2")
        result = self.check(expect=1)
        self.assertIn("block evidence-classes names a vibe-* specialist: vibe-x2", result.stdout)
        self.assertNotIn("vibe-x9", result.stdout)

    def test_check_source_block_may_cite_the_shared_source_path(self):
        body = "Edit `shared/vibe-contract.md` and re-render.\n" + PRECEDENCE + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        self.check(expect=0)

    def test_check_consolidation_block_with_wrong_closing_sentence_fails(self):
        body = "Text.\n" + APPLICABILITY + "\n"
        self.write_source([("evidence-classes", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("consolidation block does not end with its closing sentence", result.stdout)
        self.assertIn(PRECEDENCE, result.stdout)

    def test_check_gate_block_with_wrong_closing_sentence_fails(self):
        for block_id in ("history-mutation-gate", "commit-selection-gate", "read-only-phase-write-gate"):
            with self.subTest(block_id=block_id):
                body = "Text.\n" + PRECEDENCE + "\n"
                self.write_source([(block_id, ["vibe-alpha"], body)])
                self.write_package("vibe-alpha")
                result = self.check(expect=1)
                self.assertIn(f"block {block_id}: non-overridable block does not end with its closing sentence", result.stdout)
                self.assertIn(APPLICABILITY, result.stdout)

    def test_check_schema_block_with_wrong_closing_sentence_fails(self):
        body = "| Field | Type |\n| --- | --- |\n| `schema_version` | string |\n" + PRECEDENCE + "\n"
        self.write_source([("session-record-schema", ["vibe-alpha"], body)])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("block session-record-schema: non-overridable block does not end with its closing sentence", result.stdout)

    def test_check_gate_block_with_applicability_sentence_passes(self):
        self.write_source([("history-mutation-gate", ["vibe-alpha"], GATE_BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "history-mutation-gate", GATE_BODY)})
        self.check(expect=0)

    def test_check_block_missing_closing_sentence_entirely_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], "Text without a closing sentence.\n")])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("does not end with its closing sentence", result.stdout)

    def test_check_closing_sentence_with_prefix_on_the_last_line_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], "Text.\nNote: " + PRECEDENCE + "\n")])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("consolidation block does not end with its closing sentence", result.stdout)
        self.write_source([("history-mutation-gate", ["vibe-alpha"], "Text.\n" + APPLICABILITY + " Really.\n")])
        result = self.check(expect=1)
        self.assertIn("non-overridable block does not end with its closing sentence", result.stdout)

    # --- check: warnings, strict, and scoping --------------------------------

    def test_check_nonstrict_warns_on_listed_dependent_without_marker_exit_zero(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha")
        result = self.check(expect=0)
        self.assertIn("warning: package vibe-alpha is a listed dependent of block evidence-classes but has no marker", result.stdout)
        self.assertIn("0 error(s), 2 warning(s)", result.stdout)

    def test_check_tree_with_no_markers_passes_vacuously(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY), ("model-tier-selection", ["vibe-beta"], BODY)])
        self.write_package("vibe-alpha")
        self.write_package("vibe-beta")
        result = self.check(expect=0)
        self.assertEqual(result.stdout.count("but has no marker"), 2)

    def test_check_strict_listed_dependent_without_marker_is_error(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": f"# a\n\n{CLASS_LINE}\n"})
        result = self.check("--strict", expect=1)
        self.assertIn("error: package vibe-alpha is a listed dependent of block evidence-classes but has no marker", result.stdout)

    def test_check_strict_complete_package_passes(self):
        self.standard_tree(content=BODY)
        result = self.check("--strict", expect=0)
        self.assertIn("check (strict", result.stdout)

    def test_check_strict_missing_class_declaration_fails(self):
        self.standard_tree(content=BODY, class_line=None)
        self.check(expect=0)
        result = self.check("--strict", expect=1)
        self.assertIn("package vibe-alpha has no class declaration", result.stdout)

    def test_check_strict_duplicate_class_declaration_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package(
            "vibe-alpha",
            {
                "SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY),
                "references/notes.md": f"# notes\n\n{CLASS_LINE}\n",
            },
        )
        self.check(expect=0)
        result = self.check("--strict", expect=1)
        self.assertIn("package vibe-alpha has duplicate class declarations", result.stdout)

    def test_check_strict_invalid_class_declaration_fails(self):
        bad = "<!-- shared-contract:class language=english commit=none effect=read-only -->"
        self.standard_tree(content=BODY, class_line=bad)
        self.check(expect=0)
        result = self.check("--strict", expect=1)
        self.assertIn("invalid class declaration: " + bad, result.stdout)

    def test_check_strict_class_declaration_conflicting_with_dependents_fails(self):
        cases = [
            ("commit-selection-state-changing", "commit=document-only", "commit=state-changing"),
            ("commit-selection-document-only", "commit=none", "commit=document-only"),
            ("language-precedence-chat", "language=document", "language=chat"),
            ("language-precedence-document", "language=none", "language=document"),
        ]
        for block_id, declared, expected in cases:
            with self.subTest(block_id=block_id):
                axes = {"language": "none", "commit": "none"}
                axis, value = declared.split("=")
                axes[axis] = value
                class_line = (
                    f"<!-- shared-contract:class language={axes['language']} commit={axes['commit']} "
                    "effect=state-changing -->"
                )
                self.write_source([(block_id, ["vibe-alpha"], BODY)])
                self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", block_id, BODY, class_line)})
                result = self.check("--strict", expect=1)
                self.assertIn(f"class declaration {declared} conflicts with the dependents lists (expected {expected})", result.stdout)

    def test_check_strict_class_declaration_claiming_axis_without_dependency_fails(self):
        class_line = "<!-- shared-contract:class language=chat commit=none effect=read-only -->"
        self.standard_tree(content=BODY, class_line=class_line)
        result = self.check("--strict", expect=1)
        self.assertIn("class declaration language=chat conflicts with the dependents lists (expected language=none)", result.stdout)

    def test_check_strict_class_declaration_matching_dependents_passes(self):
        class_line = "<!-- shared-contract:class language=chat commit=state-changing effect=state-changing -->"
        self.write_source(
            [
                ("commit-selection-state-changing", ["vibe-alpha"], BODY),
                ("language-precedence-chat", ["vibe-alpha"], BODY),
            ]
        )
        text = (
            f"# a\n\n{class_line}\n{begin_marker('commit-selection-state-changing')}\n{BODY}"
            f"{end_marker('commit-selection-state-changing')}\n\n{begin_marker('language-precedence-chat')}\n{BODY}"
            f"{end_marker('language-precedence-chat')}\n"
        )
        self.write_package("vibe-alpha", {"SKILL.md": text})
        self.check("--strict", expect=0)

    def test_check_strict_class_declaration_not_immediately_above_first_block_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        text = f"# a\n\n{CLASS_LINE}\n\nSome prose in between.\n\n{begin_marker('evidence-classes')}\n{BODY}{end_marker('evidence-classes')}\n"
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.check("--strict", expect=1)
        self.assertIn("class declaration is not immediately above the first generated block", result.stdout)

    def test_check_strict_class_declaration_separated_by_one_blank_line_fails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        text = f"# a\n\n{CLASS_LINE}\n\n{begin_marker('evidence-classes')}\n{BODY}{end_marker('evidence-classes')}\n"
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.check("--strict", expect=1)
        self.assertIn("it must be the line directly above it", result.stdout)

    def test_check_strict_global_fails_with_unmigrated_sibling_but_package_scoped_passes(self):
        self.write_source([("evidence-classes", ["vibe-alpha", "vibe-beta"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY)})
        self.write_package("vibe-beta")
        result = self.check("--strict", expect=1)
        self.assertIn("package vibe-beta is a listed dependent of block evidence-classes but has no marker", result.stdout)
        self.assertIn("package vibe-beta has no class declaration", result.stdout)
        scoped = self.check("--strict", "--package", "vibe-alpha", expect=0)
        self.assertNotIn("vibe-beta", scoped.stdout)
        self.assertIn("check (strict, package vibe-alpha): 0 error(s), 0 warning(s)", scoped.stdout)
        self.check(expect=0)

    def test_check_package_scope_still_reports_that_packages_faults(self):
        self.write_source([("evidence-classes", ["vibe-alpha", "vibe-beta"], BODY)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", "Drift.\n")})
        self.write_package("vibe-beta")
        result = self.check("--strict", "--package", "vibe-alpha", expect=1)
        self.assertIn("block evidence-classes drifted from the source", result.stdout)

    def test_check_unknown_package_filter_is_fatal(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha")
        result = self.check("--strict", "--package", "vibe-nope", expect=2)
        self.assertIn("unknown package: vibe-nope", result.stderr)

    def test_check_missing_source_reports_error_nonzero(self):
        self.write_package("vibe-alpha")
        result = self.check(expect=2, root=self.root)
        self.assertIn("shared source does not exist", result.stderr)
        self.assertIn("vibe-contract.md", result.stderr)

    def test_check_default_source_resolves_under_repository_root(self):
        module = load_module()
        self.assertEqual(module.DEFAULT_SOURCE, REPO_ROOT / "shared" / "vibe-contract.md")

    # --- audit-names -----------------------------------------------------------

    def test_audit_names_reports_only_sibling_on_line_with_self_name(self):
        self.write_package("vibe-alpha", {"SKILL.md": "# alpha\n\nvibe-alpha hands off to vibe-beta after review.\n"})
        self.write_package("vibe-beta")
        result = self.run_cli("audit-names", expect=1)
        lines = result.stdout.strip().splitlines()
        self.assertEqual(len(lines), 1)
        location, token = lines[0].rsplit(": ", 1)
        self.assertEqual(token, "vibe-beta")
        self.assertEqual(location, "skills/vibe-alpha/SKILL.md:3:25")

    def test_audit_names_allows_shared_source_citation_and_router_package(self):
        self.write_package("vibe-alpha", {"SKILL.md": "# alpha\n\nSee `shared/vibe-contract.md` for vibe-alpha rules.\n"})
        self.write_package("vibe-coding", {"SKILL.md": "# router\n\nRoute to vibe-alpha or vibe-beta.\n"})
        self.write_package("vibe-beta")
        result = self.run_cli("audit-names", expect=0)
        self.assertEqual(result.stdout, "")

    def test_audit_names_reports_every_occurrence_across_reference_files(self):
        self.write_package(
            "vibe-alpha",
            {
                "SKILL.md": "# alpha\n",
                "references/a.md": "vibe-beta and vibe-gamma.\nvibe-beta again.\n",
            },
        )
        self.write_package("vibe-beta")
        self.write_package("vibe-gamma")
        result = self.run_cli("audit-names", expect=1)
        tokens = [line.rsplit(": ", 1)[1] for line in result.stdout.strip().splitlines()]
        self.assertEqual(tokens, ["vibe-beta", "vibe-gamma", "vibe-beta"])

    def test_audit_names_allows_non_roster_token_such_as_vibe_sessions(self):
        text = "# alpha\n\nRecords live under `.plans/vibe-sessions/` per `shared/vibe-contract.md`.\n"
        self.write_package("vibe-alpha", {"SKILL.md": text})
        self.write_package("vibe-beta")
        result = self.run_cli("audit-names", expect=0)
        self.assertEqual(result.stdout, "")

    def test_audit_names_reports_roster_sibling_name_but_not_the_same_name_off_roster(self):
        text = "# alpha\n\nAfter review hand off to vibe-gamma.\n"
        self.write_package("vibe-alpha", {"SKILL.md": text})
        result = self.run_cli("audit-names", expect=0)
        self.assertEqual(result.stdout, "")
        self.write_package("vibe-gamma")
        result = self.run_cli("audit-names", expect=1)
        self.assertEqual(result.stdout.strip(), "skills/vibe-alpha/SKILL.md:3:26: vibe-gamma")

    def test_audit_names_reports_digit_bearing_roster_sibling(self):
        self.write_package("vibe-alpha", {"SKILL.md": "# alpha\n\nUse vibe-x2 next; vibe-x9 is nobody.\n"})
        self.write_package("vibe-x2")
        result = self.run_cli("audit-names", expect=1)
        self.assertEqual(result.stdout.strip(), "skills/vibe-alpha/SKILL.md:3:5: vibe-x2")

    def test_audit_names_clean_tree_prints_nothing_exit_zero(self):
        self.write_package("vibe-alpha")
        self.write_package("vibe-beta")
        result = self.run_cli("audit-names", expect=0)
        self.assertEqual(result.stdout, "")

    # --- list ------------------------------------------------------------------

    def test_list_prints_block_ids_kinds_and_dependents(self):
        self.write_source(
            [
                ("evidence-classes", ["vibe-alpha", "vibe-beta"], BODY),
                ("history-mutation-gate", ["vibe-alpha"], GATE_BODY),
            ]
        )
        result = self.run_cli("list", root=False, expect=0)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "evidence-classes\tkind=consolidation\tdependents=vibe-alpha,vibe-beta",
                "history-mutation-gate\tkind=non-overridable\tdependents=vibe-alpha",
            ],
        )

    def test_list_reports_malformed_source(self):
        self.write_raw_source("<!-- shared-contract:block broken -->\ntext\n")
        result = self.run_cli("list", root=False, expect=1)
        self.assertIn("malformed block marker", result.stdout)

    def test_list_reports_the_shape_state_and_per_package_closing(self):
        self.write_source(
            [
                ("evidence-classes", ["vibe-alpha"], NEW_BODY_OPEN),
                ("accepted-risk-semantics", ["vibe-alpha"], BODY),
            ]
        )
        result = self.run_cli("list", root=False, expect=0)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                "evidence-classes\tkind=consolidation\tshape=new\tdependents=vibe-alpha",
                "accepted-risk-semantics\tkind=consolidation\tdependents=vibe-alpha",
                "closing=per-package",
            ],
        )

    def test_list_omits_the_closing_line_while_the_shape_keeps_its_tails(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], NEW_BODY)])
        result = self.run_cli("list", root=False, expect=0)
        self.assertEqual(
            result.stdout.splitlines(),
            ["evidence-classes\tkind=consolidation\tshape=new\tdependents=vibe-alpha"],
        )

    # --- block shape ------------------------------------------------------------

    def shape_check(self, body, block_id="evidence-classes", strict=False, expect=1):
        self.write_source([(block_id, ["vibe-alpha"], body)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", block_id, body)})
        return self.check(*(("--strict",) if strict else ()), expect=expect)

    def test_check_new_shape_block_passes_without_a_legacy_warning(self):
        result = self.shape_check(NEW_BODY, expect=0)
        self.assertNotIn("legacy-shape", result.stdout)
        self.assertIn("0 error(s), 0 warning(s)", result.stdout)
        self.shape_check(NEW_BODY, strict=True, expect=0)

    def test_check_legacy_shape_block_warns_only_outside_strict_and_never_errors(self):
        warned = self.shape_check(BODY, expect=0)
        self.assertIn("warning: vibe-contract.md:5: block evidence-classes: legacy-shape block", warned.stdout)
        strict = self.shape_check(BODY, strict=True, expect=0)
        self.assertNotIn("legacy-shape", strict.stdout)
        self.assertIn("0 error(s), 0 warning(s)", strict.stdout)

    def test_check_shape_finding_is_a_warning_by_default_and_an_error_under_strict(self):
        body = "**Never " + words(28) + ".**\n\n" + SHAPE_BULLETS + PRECEDENCE + "\n"
        warned = self.shape_check(body, expect=0)
        self.assertIn("warning: vibe-contract.md:6: block evidence-classes: bold lead is 29 words (cap 25)", warned.stdout)
        strict = self.shape_check(body, strict=True, expect=1)
        self.assertIn("error: vibe-contract.md:6: block evidence-classes: bold lead is 29 words (cap 25)", strict.stdout)

    def test_check_bold_lead_starter_flags_only_an_article_or_pronoun(self):
        flagged = {
            "**The gate covers every history rewrite.**": "The",
            "**It never allows a silent rewrite.**": "It",
            "**A commit needs a named selection source.**": "A",
            "**This gate covers plain commits.**": "This",
        }
        for lead, starter in flagged.items():
            with self.subTest(lead=lead):
                result = self.shape_check(lead + "\n\n" + SHAPE_BULLETS + PRECEDENCE + "\n", strict=True, expect=1)
                self.assertIn(f"bold lead does not open with an imperative: {starter!r}", result.stdout)
        for lead in (
            "**Never rewrite published history without asking.**",
            "**Only a recorded source selects a commit.**",
            "**Verify every delegated claim before it counts.**",
            "**Prioritize the smallest verified unit.**",
        ):
            with self.subTest(lead=lead):
                result = self.shape_check(lead + "\n\n" + SHAPE_BULLETS + PRECEDENCE + "\n", strict=True, expect=0)
                self.assertNotIn("imperative", result.stdout)

    def test_check_bullet_cap_is_forty_words_in_a_consolidation_block(self):
        passing = SHAPE_LEAD + "\n\n- " + words(40) + "\n" + PRECEDENCE + "\n"
        self.shape_check(passing, strict=True, expect=0)
        failing = SHAPE_LEAD + "\n\n- " + words(41) + "\n" + PRECEDENCE + "\n"
        result = self.shape_check(failing, strict=True, expect=1)
        self.assertIn("bullet is 41 words (cap 40)", result.stdout)

    def test_check_bullet_cap_is_thirty_words_in_a_gate_block(self):
        passing = SHAPE_LEAD + "\n\n- " + words(30) + "\n" + APPLICABILITY + "\n"
        self.shape_check(passing, block_id="commit-selection-gate", strict=True, expect=0)
        failing = SHAPE_LEAD + "\n\n- " + words(31) + "\n" + APPLICABILITY + "\n"
        result = self.shape_check(failing, block_id="commit-selection-gate", strict=True, expect=1)
        self.assertIn("bullet is 31 words (cap 30)", result.stdout)

    def test_check_sub_bullet_cap_is_thirty_words_and_the_parent_keeps_its_own_cap(self):
        passing = SHAPE_LEAD + "\n\n- " + words(40) + "\n  - " + words(30) + "\n" + PRECEDENCE + "\n"
        self.shape_check(passing, strict=True, expect=0)
        failing = SHAPE_LEAD + "\n\n- " + words(10) + "\n  - " + words(31) + "\n" + PRECEDENCE + "\n"
        result = self.shape_check(failing, strict=True, expect=1)
        self.assertIn("sub-bullet is 31 words (cap 30)", result.stdout)
        self.assertNotIn("bullet is 31", result.stdout.replace("sub-bullet is 31", ""))

    def test_check_at_most_one_prose_paragraph_may_follow_the_bullets(self):
        body = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + "\n" + SHAPE_EXCEPTION + "\nA second tail paragraph.\n" + PRECEDENCE + "\n"
        result = self.shape_check(body, strict=True, expect=1)
        self.assertIn("more than one prose paragraph after the bullets", result.stdout)
        self.assertIn("(at most one exception line is allowed)", result.stdout)

    def test_check_exception_line_cap_is_thirty_five_words(self):
        passing = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + "\nException: " + words(34) + "\n" + PRECEDENCE + "\n"
        self.shape_check(passing, strict=True, expect=0)
        failing = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + "\nException: " + words(35) + "\n" + PRECEDENCE + "\n"
        result = self.shape_check(failing, strict=True, expect=1)
        self.assertIn("exception line is 36 words (cap 35)", result.stdout)

    def test_check_prose_paragraph_cap_is_sixty_words(self):
        passing = SHAPE_LEAD + "\n\n" + words(60) + "\n\n" + SHAPE_BULLETS + PRECEDENCE + "\n"
        self.shape_check(passing, strict=True, expect=0)
        failing = SHAPE_LEAD + "\n\n" + words(61) + "\n\n" + SHAPE_BULLETS + PRECEDENCE + "\n"
        result = self.shape_check(failing, strict=True, expect=1)
        self.assertIn("paragraph is 61 words (cap 60)", result.stdout)
        self.assertNotIn("exception line", result.stdout)

    def test_check_gate_block_total_cap_is_two_hundred_sixty_words(self):
        bullets = "".join("- " + words(30) + "\n" for _ in range(8))
        passing = SHAPE_LEAD + "\n\n" + bullets + APPLICABILITY + "\n"
        self.shape_check(passing, block_id="history-mutation-gate", strict=True, expect=0)
        failing = SHAPE_LEAD + "\n\n" + bullets + "- " + words(20) + "\n" + APPLICABILITY + "\n"
        result = self.shape_check(failing, block_id="history-mutation-gate", strict=True, expect=1)
        self.assertIn("gate block is 268 words (cap 260)", result.stdout)

    def test_check_example_lines_are_excluded_from_the_counts_and_capped_at_two(self):
        example = "Example: " + words(80) + "\n"
        passing = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + example + example + APPLICABILITY + "\n"
        self.shape_check(passing, block_id="history-mutation-gate", strict=True, expect=0)
        failing = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + example + example + example + APPLICABILITY + "\n"
        result = self.shape_check(failing, block_id="history-mutation-gate", strict=True, expect=1)
        self.assertIn("more than 2 'Example:' lines in the block", result.stdout)

    def test_check_new_shape_block_ending_with_the_other_closing_sentence_fails(self):
        body = SHAPE_LEAD + "\n\n" + SHAPE_BULLETS + APPLICABILITY + "\n"
        result = self.shape_check(body, expect=1)
        self.assertIn("consolidation block ends with the other closing sentence", result.stdout)

    def test_check_table_rows_and_fenced_code_inside_a_block_are_not_prose_paragraphs(self):
        body = (
            SHAPE_LEAD
            + "\n\n| Field | Type | Notes |\n| --- | --- | --- |\n| `phase` | string | "
            + words(70)
            + " |\n\n```json\n{\"phase\": \"review\", \"note\": \""
            + words(70)
            + "\"}\n```\n\n"
            + SHAPE_BULLETS
            + APPLICABILITY
            + "\n"
        )
        self.shape_check(body, block_id="session-record-schema", strict=True, expect=0)

    def test_count_words_drops_markdown_markers_and_punctuation_only_tokens(self):
        module = load_module()
        self.assertEqual(module.count_words("**Never** — the `phase` field, and 3 items."), 7)
        self.assertEqual(module.count_words("- a bullet marker is not a word"), 7)
        self.assertEqual(module.wc_counts("one two\nthree\n"), (2, 3))

    # --- closing block ----------------------------------------------------------

    def test_check_closing_block_is_refused_while_every_source_block_keeps_its_tail(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package(
            "vibe-alpha",
            {"SKILL.md": closing_file("vibe-alpha", "evidence-classes", BODY, PRECEDENCE + "\n")},
        )
        result = self.check(expect=1)
        self.assertIn(
            "package vibe-alpha carries a closing block while every source block still ends with its own closing sentence",
            result.stdout,
        )
        refused = self.render(expect=1)
        self.assertIn("render refused", refused.stdout)

    def test_check_new_shape_block_without_a_tail_needs_no_closing_sentence(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], NEW_BODY_OPEN)])
        self.write_package(
            "vibe-alpha",
            {"SKILL.md": closing_file("vibe-alpha", "evidence-classes", NEW_BODY_OPEN, PRECEDENCE + "\n")},
        )
        result = self.check("--strict", expect=0)
        self.assertNotIn("closing sentence", result.stdout)

    def test_check_strict_requires_one_closing_block_per_package_once_the_tails_are_gone(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], NEW_BODY_OPEN)])
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", NEW_BODY_OPEN)})
        warned = self.check(expect=0)
        self.assertIn("warning: package vibe-alpha has no closing block", warned.stdout)
        strict = self.check("--strict", expect=1)
        self.assertIn("error: package vibe-alpha has no closing block", strict.stdout)

    def test_render_fills_a_pristine_closing_block_with_the_precedence_sentence(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], NEW_BODY_OPEN)])
        self.write_package(
            "vibe-alpha",
            {"SKILL.md": closing_file("vibe-alpha", "evidence-classes", NEW_BODY_OPEN, "")},
        )
        result = self.render(expect=0)
        self.assertIn("rendered skills/vibe-alpha/SKILL.md closing (pristine)", result.stdout)
        text = (self.root / "vibe-alpha" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(begin_marker("closing") + "\n" + PRECEDENCE + "\n" + end_marker("closing"), text)
        self.assertNotIn(APPLICABILITY, text)
        self.check("--strict", expect=0)

    def test_render_closing_block_adds_the_applicability_sentence_for_a_gate_package(self):
        gate_body = "**Never rewrite published history without asking.**\n\n- Stop before a matched command and name it.\n"
        self.write_source(
            [
                ("evidence-classes", ["vibe-alpha"], NEW_BODY_OPEN),
                ("history-mutation-gate", ["vibe-alpha"], gate_body),
            ]
        )
        text = (
            f"# a\n\n{CLASS_LINE}\n{begin_marker('closing')}\n{end_marker('closing')}\n\n"
            f"{begin_marker('evidence-classes')}\n{NEW_BODY_OPEN}{end_marker('evidence-classes')}\n\n"
            f"{begin_marker('history-mutation-gate')}\n{gate_body}{end_marker('history-mutation-gate')}\n"
        )
        self.write_package("vibe-alpha", {"SKILL.md": text})
        self.render(expect=0)
        rendered = (self.root / "vibe-alpha" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            begin_marker("closing") + "\n" + PRECEDENCE + "\n" + APPLICABILITY + "\n" + end_marker("closing"),
            rendered,
        )
        self.check("--strict", expect=0)

    def test_check_closing_block_must_sit_directly_below_the_class_line(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], NEW_BODY_OPEN)])
        self.write_package(
            "vibe-alpha",
            {
                "SKILL.md": closing_file(
                    "vibe-alpha", "evidence-classes", NEW_BODY_OPEN, PRECEDENCE + "\n", gap="\n"
                )
            },
        )
        result = self.check(expect=1)
        self.assertIn("the closing block must be the line directly below the class declaration", result.stdout)
        self.assertIn("with no blank line between them", result.stdout)

    def test_check_drifted_closing_block_fails_and_force_render_repairs_it(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], NEW_BODY_OPEN)])
        self.write_package(
            "vibe-alpha",
            {"SKILL.md": closing_file("vibe-alpha", "evidence-classes", NEW_BODY_OPEN, "Hand-written tail.\n")},
        )
        result = self.check(expect=1)
        self.assertIn("block closing drifted from the source", result.stdout)
        self.render("--force", expect=0)
        self.check("--strict", expect=0)

    def test_check_source_block_id_closing_is_reserved(self):
        self.write_source([("closing", ["vibe-alpha"], BODY)])
        self.write_package("vibe-alpha")
        result = self.check(expect=1)
        self.assertIn("block id 'closing' is reserved for the per-package closing block", result.stdout)

    # --- appendix ---------------------------------------------------------------

    def test_appendix_outside_every_block_is_ignored_by_list_render_and_check(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        appendix = (
            "\n## Appendix: hook contract\n\n"
            "| Field | Type | Notes |\n"
            "| --- | --- | --- |\n"
            "| `phase` | string | the recorded phase |\n"
            "| `source` | string | one of the three selecting values |\n\n"
            "The appendix may show the marker grammar itself:\n\n"
            "```markdown\n"
            "<!-- shared-contract:block appendix-example dependents=vibe-alpha -->\n"
            "**Never treat this appendix as a block.**\n"
            "<!-- shared-contract:endblock appendix-example -->\n"
            "```\n\n"
            "```json\n"
            '{"schema_version": "1", "phase": "review", "effect_mode": "read-only"}\n'
            "```\n"
        )
        self.source.write_text(self.source.read_text(encoding="utf-8") + appendix, encoding="utf-8")
        self.write_package("vibe-alpha", {"SKILL.md": marked_file("vibe-alpha", "evidence-classes", "")})
        listing = self.run_cli("list", root=False, expect=0)
        self.assertEqual(
            listing.stdout.splitlines(),
            ["evidence-classes\tkind=consolidation\tdependents=vibe-alpha"],
        )
        self.render(expect=0)
        self.check("--strict", expect=0)
        self.assertEqual(
            (self.root / "vibe-alpha" / "SKILL.md").read_text(encoding="utf-8"),
            marked_file("vibe-alpha", "evidence-classes", BODY),
        )

    # --- measure ----------------------------------------------------------------

    def write_manifest(self, tasks, name="measure-manifest.json"):
        path = self.base / name
        path.write_text(json.dumps({"schema_version": 1, "tasks": tasks}, indent=2), encoding="utf-8")
        return path

    def measure(self, *extra, manifest, expect=None):
        return self.run_cli("measure", "--manifest", str(manifest), *extra, source=False, expect=expect)

    def measured_package(self):
        self.write_source([("evidence-classes", ["vibe-alpha"], BODY)])
        self.write_package(
            "vibe-alpha",
            {
                "SKILL.md": marked_file("vibe-alpha", "evidence-classes", BODY),
                "references/notes.md": "# notes\n\nA short reference file.\n",
            },
        )
        return (self.root / "vibe-alpha" / "SKILL.md").read_text(encoding="utf-8")

    def test_measure_reports_package_rows_and_task_sums(self):
        entry = self.measured_package()
        reference = (self.root / "vibe-alpha" / "references" / "notes.md").read_text(encoding="utf-8")
        manifest = self.write_manifest(
            [
                {
                    "id": "T1",
                    "files": ["skills/vibe-alpha/SKILL.md", "skills/vibe-alpha/references/notes.md"],
                    "baseline": {"lines": 999, "words": 9999},
                    "pre_change": {"words": 11111},
                }
            ]
        )
        result = self.measure(manifest=manifest, expect=0)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "package\tentry_lines\tentry_words\tblock_words\treference_words")
        self.assertEqual(
            lines[1],
            "vibe-alpha\t{}\t{}\t{}\t{}".format(
                entry.count("\n"), len(entry.split()), len(BODY.split()), len(reference.split())
            ),
        )
        self.assertEqual(lines[3], "task\tlines\twords\tbaseline_lines\tbaseline_words\tpre_change_words\tdelta_words")
        total_lines = entry.count("\n") + reference.count("\n")
        total_words = len(entry.split()) + len(reference.split())
        self.assertEqual(lines[4], f"T1\t{total_lines}\t{total_words}\t999\t9999\t11111\t{total_words - 9999:+d}")
        self.assertIn("measure (non-strict): 1 package(s), 1 task(s), 0 task(s) not below baseline", result.stdout)

    def test_measure_strict_exits_one_unless_every_task_is_below_baseline(self):
        entry = self.measured_package()
        entry_words = len(entry.split())
        task = {"id": "T1", "files": ["skills/vibe-alpha/SKILL.md"], "baseline": {"lines": 1, "words": entry_words + 1}}
        below = self.write_manifest([task])
        self.measure("--strict", manifest=below, expect=0)
        task["baseline"]["words"] = entry_words
        equal = self.write_manifest([task], name="equal.json")
        result = self.measure("--strict", manifest=equal, expect=1)
        self.assertIn("1 task(s) not below baseline", result.stdout)
        self.measure(manifest=equal, expect=0)

    def test_measure_refuses_a_missing_manifest_or_a_missing_measured_file(self):
        self.measured_package()
        missing = self.measure(manifest=self.base / "nowhere.json", expect=2)
        self.assertIn("measure manifest does not exist", missing.stderr)
        empty = self.write_manifest([], name="empty.json")
        self.assertIn("has no tasks", self.measure(manifest=empty, expect=2).stderr)
        gone = self.write_manifest(
            [{"id": "T1", "files": ["skills/vibe-alpha/gone.md"], "baseline": {"lines": 1, "words": 1}}],
            name="gone.json",
        )
        result = self.measure(manifest=gone, expect=2)
        self.assertIn("measure manifest task T1 lists a missing file: skills/vibe-alpha/gone.md", result.stderr)

    def test_measure_manifest_file_outside_the_root_is_refused(self):
        self.measured_package()
        (self.base / "outside.md").write_text("# outside\n", encoding="utf-8")
        escaping = self.write_manifest(
            [{"id": "T1", "files": ["skills/../outside.md"], "baseline": {"lines": 1, "words": 1}}],
            name="escape.json",
        )
        result = self.measure(manifest=escaping, expect=2)
        self.assertIn("resolves outside the root", result.stderr)

    def test_measure_reproduces_the_repository_manifest_baselines(self):
        module = load_module()
        self.assertEqual(module.DEFAULT_MANIFEST, REPO_ROOT / "shared" / "measure-manifest.json")
        manifest = json.loads(module.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "measure"], cwd=REPO_ROOT, text=True, capture_output=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = {line.split("\t")[0]: line.split("\t") for line in result.stdout.splitlines() if "\t" in line}
        for task in manifest["tasks"]:
            with self.subTest(task=task["id"]):
                text = [(REPO_ROOT / rel).read_text(encoding="utf-8") for rel in task["files"]]
                row = rows[task["id"]]
                self.assertEqual(int(row[1]), sum(item.count("\n") for item in text))
                self.assertEqual(int(row[2]), sum(len(item.split()) for item in text))
                self.assertEqual(int(row[3]), task["baseline"]["lines"])
                self.assertEqual(int(row[4]), task["baseline"]["words"])
                self.assertEqual(int(row[5]), task["pre_change"]["words"])


if __name__ == "__main__":
    unittest.main()
