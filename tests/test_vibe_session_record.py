import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "vibe_session_record.py"

# The plan's design-contract example ("Example (complete, accepted by the checker)"), plus the
# event `status` field the shared contract added afterwards.
EXAMPLE_RECORD_JSON = """{
  "schema_version": "1",
  "record_id": "3f1c9a52-6b7e-4c1d-9a0e-2f7d4c8b1e10",
  "repository": {"root": "/home/user/repo", "worktree": "/home/user/repo", "head": "dfea569"},
  "workflow_id": "3f1c9a52-6b7e-4c1d-9a0e-2f7d4c8b1e10",
  "host_session_id": "sess-01H",
  "generation": 4,
  "lease": {"owner": "3f1c9a52-6b7e-4c1d-9a0e-2f7d4c8b1e10", "renewed_at": "2026-09-04T13:02:11Z", "expires_at": "2026-09-04T21:02:11Z"},
  "status": "active",
  "closed_at": null,
  "phase": "implementation-planning",
  "effect_mode": "artifact-only",
  "allowed_paths": ["/home/user/repo/docs/plans/2026-09-04-x-implementation-plan.md", "/tmp/scratch/unit-1"],
  "goal": "add CSV import",
  "pending_decision": null,
  "blocker": null,
  "next_route": "implementation-planning",
  "artifact_paths": ["/home/user/repo/docs/specs/2026-09-04-x-spec.md"],
  "artifact_identity": [{"path": "/home/user/repo/docs/specs/2026-09-04-x-spec.md", "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", "refreshed_at": "2026-09-04T13:02:11Z"}],
  "capability_map": {"checked_at": "2026-09-04T12:40:00Z", "source": "host skill metadata", "phases": {"implementation-planning": "vibe-planning", "commit-execution": "vibe-commit", "review": null}},
  "events": [{"kind": "approval", "source": "user-turn", "at": "2026-09-04T12:58:40Z", "artifact": {"path": "/home/user/repo/docs/specs/2026-09-04-x-spec.md", "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"}, "status": "current", "note": "spec approved in the user's own words"}]
}
"""

EXAMPLE_ID = "3f1c9a52-6b7e-4c1d-9a0e-2f7d4c8b1e10"
SPEC_PATH = "/home/user/repo/docs/specs/2026-09-04-x-spec.md"
SPEC_SHA = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
FRESH_NOW = "2026-09-04T14:00:00Z"
LATE_NOW = "2026-09-05T01:00:00Z"
OTHER_WORKFLOW = "7c2b6e1a-4d3f-4a9b-8e0c-5f6a7b8c9d0e"
UUID_V1 = "3f1c9a52-6b7e-1c1d-9a0e-2f7d4c8b1e10"
AWS_LITERAL = "AKIAIOSFODNN7EXAMPLE"

ALL_PHASES = (
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
ALL_STATUSES = ("active", "completed", "cancelled", "superseded")
ALL_EFFECT_MODES = ("read-only", "artifact-only", "state-changing", "none")
ALL_EVENT_KINDS = ("approval", "proceed", "handoff", "commit-selection", "confirmation")
ALL_EVENT_SOURCES = ("user-turn", "bound-plan-item", "specialist-checkpoint", "agent-proposed")
ALL_EVENT_STATUSES = ("current", "superseded")
STALE_SHA = "0" * 64
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


def load_module():
    spec = importlib.util.spec_from_file_location("vibe_session_record", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def example_record():
    return json.loads(EXAMPLE_RECORD_JSON)


def can_create_symlink():
    if not hasattr(os, "symlink"):
        return False
    with tempfile.TemporaryDirectory() as tmp:
        link = Path(tmp) / "link"
        try:
            os.symlink("link", link)
        except (OSError, NotImplementedError):
            return False
        return link.is_symlink()


CAN_CREATE_SYMLINK = can_create_symlink()


class VibeSessionRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name).resolve()

    def tearDown(self):
        self.tmp.cleanup()

    # --- helpers -------------------------------------------------------------

    def write_record(self, record, name=None, directory=None):
        directory = directory or self.dir
        directory.mkdir(parents=True, exist_ok=True)
        if name is None:
            name = f"{record['record_id']}.json"
        path = directory / name
        text = record if isinstance(record, str) else json.dumps(record, indent=2)
        path.write_text(text, encoding="utf-8")
        return path

    def run_check(self, path, *args, now=FRESH_NOW, expect=None):
        command = [sys.executable, str(SCRIPT), "check", str(path), *map(str, args)]
        if now is not None:
            command += ["--now", now]
        result = subprocess.run(command, cwd=self.dir, text=True, capture_output=True, check=False)
        if expect is not None and result.returncode != expect:
            self.fail(
                f"expected exit {expect}, got {result.returncode}: {command}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
        return result

    def assert_outcome(self, result, outcome):
        self.assertIn(f"outcome: {outcome}", result.stdout.splitlines()[-1])

    def variant(self, **changes):
        record = example_record()
        record.update(changes)
        return record

    def record_with_event(self, kind, artifact="match", source="user-turn", status="current"):
        record = example_record()
        if artifact == "match":
            artifact = {"path": SPEC_PATH, "sha256": SPEC_SHA}
        record["events"] = [
            {"kind": kind, "source": source, "at": "2026-09-04T12:58:40Z", "artifact": artifact, "status": status, "note": "n"}
        ]
        return record

    def bound_temp_artifact(self, content=b"the bound spec bytes\n", name="spec.md"):
        artifact = self.dir / name
        artifact.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        return str(artifact), digest

    def record_bound_to(self, path, digest, **changes):
        record = self.variant(
            artifact_paths=[path],
            artifact_identity=[{"path": path, "sha256": digest, "refreshed_at": "2026-09-04T13:02:11Z"}],
            events=[{"kind": "approval", "source": "user-turn", "at": "2026-09-04T12:58:40Z", "artifact": {"path": path, "sha256": digest}, "status": "current", "note": "ok"}],
        )
        record.update(changes)
        return record

    # --- accept rows -----------------------------------------------------------

    def test_accept_plan_example_record_exit_zero(self):
        path = self.write_record(EXAMPLE_RECORD_JSON, name=f"{EXAMPLE_ID}.json")
        result = self.run_check(path, expect=0)
        self.assert_outcome(result, "accept")
        self.assertNotIn("flag:", result.stdout)
        self.assertNotIn("reject:", result.stdout)

    def test_accept_every_phase_row_id(self):
        for phase in ALL_PHASES:
            with self.subTest(phase=phase):
                result = self.run_check(self.write_record(self.variant(phase=phase)), expect=0)
                self.assert_outcome(result, "accept")

    def test_accept_valid_active_session_bound_state_changing_record(self):
        record = self.variant(phase="plan-execution", effect_mode="state-changing", next_route="plan-execution")
        result = self.run_check(self.write_record(record), expect=0)
        self.assert_outcome(result, "accept")

    def test_accept_valid_active_session_bound_read_only_record(self):
        record = self.variant(phase="code-investigation", effect_mode="read-only", artifact_paths=[], artifact_identity=[], events=[])
        result = self.run_check(self.write_record(record), expect=0)
        self.assert_outcome(result, "accept")

    def test_accept_chat_only_requirements_specification_with_empty_identity(self):
        record = self.variant(
            phase="requirements-specification",
            effect_mode="none",
            artifact_paths=[],
            artifact_identity=[],
            events=[{"kind": "confirmation", "source": "user-turn", "at": "2026-09-04T12:58:40Z", "artifact": None, "status": "current", "note": "chat-only"}],
        )
        result = self.run_check(self.write_record(record), expect=0)
        self.assert_outcome(result, "accept")

    def test_accept_pre_creation_phase_with_no_artifact_and_empty_identity(self):
        record = self.variant(phase="debug-and-repair", effect_mode="state-changing", artifact_paths=[], artifact_identity=[], events=[])
        self.run_check(self.write_record(record), expect=0)

    def test_accept_pre_creation_listed_path_not_yet_on_disk_with_empty_identity(self):
        missing = str(self.dir / "not-written-yet-spec.md")
        record = self.variant(phase="requirements-specification", artifact_paths=[missing], artifact_identity=[], events=[])
        result = self.run_check(self.write_record(record), expect=0)
        self.assert_outcome(result, "accept")

    def test_accept_matching_worktree_and_session_expectations(self):
        path = self.write_record(example_record())
        result = self.run_check(path, "--expect-worktree", "/home/user/repo", "--expect-session", "sess-01H", expect=0)
        self.assert_outcome(result, "accept")

    def test_accept_expect_worktree_normalized_on_the_expectation_side(self):
        path = self.write_record(example_record())
        self.run_check(path, "--expect-worktree", "/home/user/repo/", expect=0)
        self.run_check(path, "--expect-worktree", "/home/user/other/../repo", expect=0)

    def test_accept_note_of_exactly_200_characters(self):
        record = example_record()
        record["events"][0]["note"] = "x" * 200
        self.run_check(self.write_record(record), expect=0)

    # --- reject: absent, malformed, schema ----------------------------------

    def test_reject_absent_record_file(self):
        missing = self.dir / f"{EXAMPLE_ID}.json"
        result = self.run_check(missing, expect=2)
        self.assertIn(f"reject: absent: {missing.as_posix()}", result.stdout)
        self.assert_outcome(result, "reject")

    def test_reject_malformed_json_exit_two(self):
        path = self.write_record("{not json", name=f"{EXAMPLE_ID}.json")
        result = self.run_check(path, expect=2)
        self.assertIn("reject: malformed-json:", result.stdout)
        self.assert_outcome(result, "reject")

    def test_reject_top_level_array(self):
        path = self.write_record("[]", name=f"{EXAMPLE_ID}.json")
        result = self.run_check(path, expect=2)
        self.assertIn("reject: schema: top-level value is not an object", result.stdout)

    def test_reject_unknown_schema_version(self):
        result = self.run_check(self.write_record(self.variant(schema_version="2")), expect=2)
        self.assertIn("reject: schema-version:", result.stdout)

    def test_reject_missing_required_key(self):
        for key in REQUIRED_KEYS:
            with self.subTest(key=key):
                record = example_record()
                del record[key]
                result = self.run_check(self.write_record(record, name=f"{EXAMPLE_ID}.json"), expect=2)
                self.assertIn(f"reject: missing-key: required key {key} is absent", result.stdout)

    def test_reject_missing_nested_required_key(self):
        record = example_record()
        del record["repository"]["head"]
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: missing-key: required key repository.head is absent", result.stdout)

    def test_enum_value_lists_are_pinned(self):
        module = load_module()
        self.assertEqual(module.PHASES, ALL_PHASES)
        self.assertEqual(module.STATUSES, ALL_STATUSES)
        self.assertEqual(module.EFFECT_MODES, ALL_EFFECT_MODES)
        self.assertEqual(module.EVENT_KINDS, ALL_EVENT_KINDS)
        self.assertEqual(module.EVENT_SOURCES, ALL_EVENT_SOURCES)
        self.assertEqual(module.EVENT_STATUSES, ALL_EVENT_STATUSES)
        self.assertEqual(module.REQUIRED_KEYS, REQUIRED_KEYS)

    def test_reject_invalid_enum_values(self):
        cases = (("status", "open"), ("phase", "planning"), ("effect_mode", "write"))
        for key, value in cases:
            with self.subTest(key=key):
                result = self.run_check(self.write_record(self.variant(**{key: value})), expect=2)
                self.assertIn(f"reject: enum: {key} must be one of", result.stdout)
                self.assertIn(f'got "{value}"', result.stdout)

    def test_reject_record_id_not_matching_file_stem(self):
        path = self.write_record(example_record(), name="other-name.json")
        result = self.run_check(path, expect=2)
        self.assertIn("reject: record-id:", result.stdout)
        self.assertIn('does not equal the file stem "other-name"', result.stdout)

    def test_reject_record_id_with_invalid_characters(self):
        record = self.variant(record_id="bad id")
        path = self.write_record(record, name="bad id.json")
        result = self.run_check(path, expect=2)
        self.assertIn("reject: record-id: record_id does not match", result.stdout)

    def test_reject_values_with_trailing_newline_via_fullmatch(self):
        record = self.variant(record_id=EXAMPLE_ID + "\n")
        result = self.run_check(self.write_record(record, name=f"{EXAMPLE_ID}.json"), expect=2)
        self.assertIn("reject: record-id: record_id does not match", result.stdout)

        record = self.variant(workflow_id=EXAMPLE_ID + "\n")
        record["lease"]["owner"] = EXAMPLE_ID + "\n"
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: workflow-id:", result.stdout)

        record = example_record()
        record["artifact_identity"][0]["sha256"] = SPEC_SHA + "\n"
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: schema: artifact_identity[0].sha256 must be 64 lowercase hex characters", result.stdout)

        record = example_record()
        record["lease"]["renewed_at"] = "2026-09-04T13:02:11Z\n"
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: timestamp: lease.renewed_at", result.stdout)

    def test_reject_workflow_id_that_is_not_uuid4(self):
        record = self.variant(workflow_id="workflow-1")
        record["lease"]["owner"] = "workflow-1"
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: workflow-id: workflow_id must be a UUIDv4", result.stdout)

    def test_reject_well_formed_non_v4_uuid(self):
        record = self.variant(workflow_id=UUID_V1)
        record["lease"]["owner"] = UUID_V1
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: workflow-id: workflow_id must be a UUIDv4", result.stdout)

    def test_reject_uppercase_digest(self):
        record = example_record()
        record["artifact_identity"][0]["sha256"] = SPEC_SHA.upper()
        record["events"][0]["artifact"]["sha256"] = SPEC_SHA.upper()
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: schema: artifact_identity[0].sha256 must be 64 lowercase hex characters", result.stdout)
        self.assertIn("reject: schema: events[0].artifact.sha256 must be 64 lowercase hex characters", result.stdout)

    def test_reject_generation_below_one_or_non_integer(self):
        for value in (0, -1, "4", 4.0, True):
            with self.subTest(value=value):
                result = self.run_check(self.write_record(self.variant(generation=value)), expect=2)
                self.assertIn("reject: generation: generation must be an integer >= 1", result.stdout)

    def test_reject_lease_owner_not_workflow_id(self):
        record = example_record()
        record["lease"]["owner"] = OTHER_WORKFLOW
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: lease-owner:", result.stdout)

    def test_reject_lease_expiry_not_renewed_plus_eight_hours(self):
        record = example_record()
        record["lease"]["expires_at"] = "2026-09-04T22:02:11Z"
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: lease-expiry: lease.expires_at 2026-09-04T22:02:11Z is not lease.renewed_at + 8h (2026-09-04T21:02:11Z)", result.stdout)

    def test_reject_timestamp_without_z_suffix_or_second_precision(self):
        for value in ("2026-09-04T13:02:11+00:00", "2026-09-04T13:02:11.000Z", "2026-09-04 13:02:11Z"):
            with self.subTest(value=value):
                record = example_record()
                record["lease"]["renewed_at"] = value
                result = self.run_check(self.write_record(record), expect=2)
                self.assertIn("reject: timestamp: lease.renewed_at must be an ISO-8601 UTC timestamp", result.stdout)

    def test_reject_non_active_status_without_closed_at(self):
        result = self.run_check(self.write_record(self.variant(status="cancelled")), expect=2)
        self.assertIn("reject: closed-at: status cancelled requires closed_at to be set", result.stdout)

    def test_reject_active_status_with_closed_at_set(self):
        result = self.run_check(self.write_record(self.variant(closed_at="2026-09-04T13:30:00Z")), expect=2)
        self.assertIn("reject: closed-at: status active requires closed_at to be null", result.stdout)

    def test_reject_non_canonical_paths(self):
        cases = (
            ("allowed_paths[0]", lambda r: r.__setitem__("allowed_paths", ["docs/plans"]), "docs/plans"),
            ("allowed_paths[0]", lambda r: r.__setitem__("allowed_paths", ["/a/../b"]), "/a/../b"),
            ("repository.root", lambda r: r["repository"].__setitem__("root", "/home/user/repo/"), "/home/user/repo/"),
            ("repository.worktree", lambda r: r["repository"].__setitem__("worktree", "/home/user/./repo"), "/home/user/./repo"),
            ("artifact_paths[0]", lambda r: r.__setitem__("artifact_paths", ["/home/user/repo/docs/../docs/spec.md"]), "/home/user/repo/docs/../docs/spec.md"),
            ("artifact_identity[0].path", lambda r: r["artifact_identity"][0].__setitem__("path", "/a/../b"), "/a/../b"),
            ("events[0].artifact.path", lambda r: r["events"][0]["artifact"].__setitem__("path", "relative/spec.md"), "relative/spec.md"),
        )
        for label, mutate, value in cases:
            with self.subTest(label=label, value=value):
                record = example_record()
                mutate(record)
                result = self.run_check(self.write_record(record), expect=2)
                self.assertIn(f'reject: path: {label} must be a canonical absolute path: "{value}"', result.stdout)

    def test_reject_empty_goal(self):
        result = self.run_check(self.write_record(self.variant(goal="")), expect=2)
        self.assertIn("reject: schema: goal must be non-empty", result.stdout)

    def test_reject_capability_map_with_unknown_phase_key(self):
        record = example_record()
        record["capability_map"]["phases"]["deploy"] = "deploy-specialist"
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn('reject: enum: capability_map.phases key must be a phase row id; got "deploy"', result.stdout)

    def test_accept_null_capability_map_before_first_availability_check(self):
        self.run_check(self.write_record(self.variant(capability_map=None)), expect=0)

    # --- reject: string hygiene ---------------------------------------------

    def test_reject_control_character_yields_one_reason_line(self):
        record = self.variant(host_session_id="sess\n01H")
        result = self.run_check(self.write_record(record), expect=2)
        lines = result.stdout.splitlines()
        self.assertEqual(lines, ["reject: control-character: host_session_id contains a control character", "outcome: reject"])

    def test_reason_lines_stay_single_lines_for_embedded_newlines(self):
        record = self.variant(status="act\nive")
        result = self.run_check(self.write_record(record), expect=2)
        for line in result.stdout.splitlines():
            self.assertTrue(line.startswith(("reject:", "outcome:")), line)
        self.assertIn('got "act\\nive"', result.stdout)

    def secret_field_cases(self):
        def set_paths(record, value):
            record["artifact_paths"] = [value]
            record["artifact_identity"][0]["path"] = value
            record["events"][0]["artifact"]["path"] = value

        return (
            ("goal", lambda r, v: r.__setitem__("goal", v), "rotate the key {}", "rotate the key later"),
            ("pending_decision", lambda r, v: r.__setitem__("pending_decision", v), "approve {}", "approve scope"),
            ("blocker", lambda r, v: r.__setitem__("blocker", v), "blocked on {}", "blocked on review"),
            ("next_route", lambda r, v: r.__setitem__("next_route", v), "review {}", "review"),
            ("events[0].note", lambda r, v: r["events"][0].__setitem__("note", v), "note {}", "note plain"),
            ("repository.root", lambda r, v: r["repository"].__setitem__("root", v), "/home/user/{}/repo", "/home/user/repo"),
            ("repository.worktree", lambda r, v: r["repository"].__setitem__("worktree", v), "/home/user/{}/repo", "/home/user/repo"),
            ("allowed_paths[0]", lambda r, v: r.__setitem__("allowed_paths", [v]), "/home/user/repo/{}", "/home/user/repo/docs"),
            ("artifact_paths[0]", set_paths, "/home/user/repo/{}.md", SPEC_PATH),
            ("artifact_identity[0].path", set_paths, "/home/user/repo/{}.md", SPEC_PATH),
            ("events[0].artifact.path", set_paths, "/home/user/repo/{}.md", SPEC_PATH),
        )

    def test_reject_secret_like_literal_in_every_free_text_and_path_field(self):
        for label, mutate, template, _benign in self.secret_field_cases():
            with self.subTest(field=label):
                record = example_record()
                mutate(record, template.format(AWS_LITERAL))
                result = self.run_check(self.write_record(record), expect=2)
                self.assertIn(f"reject: secret: {label} carries a secret-like literal (aws-access-key)", result.stdout)
                self.assertNotIn(AWS_LITERAL, result.stdout)
                self.assertNotIn(AWS_LITERAL, result.stderr)

    def test_accept_benign_values_in_every_free_text_and_path_field(self):
        for label, mutate, _template, benign in self.secret_field_cases():
            with self.subTest(field=label):
                record = example_record()
                mutate(record, benign)
                result = self.run_check(self.write_record(record), expect=0)
                self.assertNotIn("reject: secret", result.stdout)

    def test_reject_secret_detection_classes_in_event_note(self):
        literals = (
            ("github-token", "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
            ("aws-access-key", AWS_LITERAL, AWS_LITERAL),
            ("credential-assignment", "password: hunter2", "hunter2"),
            ("private-key", "-----BEGIN RSA PRIVATE KEY-----", "BEGIN RSA PRIVATE KEY"),
            ("bearer-token", "Authorization Bearer eyJhbGciOiJIUzI1NiJ9.abc.def", "eyJhbGciOiJIUzI1NiJ9"),
            ("slack-token", "xoxb-123456789012-abcdefghijkl", "xoxb-123456789012"),
            ("api-key-prefix", "sk-live-ABCDEFGHIJKLMNOPQRSTUVWXYZ", "sk-live-ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        )
        for expected_class, literal, fragment in literals:
            with self.subTest(literal=literal):
                record = example_record()
                record["events"][0]["note"] = f"approved with {literal}"
                result = self.run_check(self.write_record(record), expect=2)
                self.assertIn("reject: secret: events[0].note carries a secret-like literal (", result.stdout)
                self.assertIn(f"({expected_class})", result.stdout)
                self.assertNotIn(fragment, result.stdout)

    def test_reject_note_longer_than_200_characters(self):
        record = example_record()
        record["events"][0]["note"] = "x" * 201
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: note-length: events[0].note exceeds 200 characters (201)", result.stdout)

    # --- reject: binding and events -----------------------------------------

    def test_reject_empty_identity_in_binding_required_state(self):
        for phase in ("implementation-planning", "plan-execution", "plan-pre-check-walkthrough"):
            with self.subTest(phase=phase):
                record = self.variant(phase=phase, artifact_paths=[], artifact_identity=[], events=[])
                result = self.run_check(self.write_record(record), expect=2)
                self.assertIn(f"reject: binding: artifact_identity is empty in a binding-required state (phase {phase}", result.stdout)

    def test_reject_existing_spec_file_with_empty_identity_in_requirements_specification(self):
        spec, _digest = self.bound_temp_artifact()
        record = self.variant(phase="requirements-specification", artifact_paths=[spec], artifact_identity=[], events=[])
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: binding:", result.stdout)
        self.assertIn("phase requirements-specification, 1 artifact path(s)", result.stdout)

    def test_reject_existing_artifact_in_non_binding_phase_without_identity(self):
        artifact, _digest = self.bound_temp_artifact(name="notes.md")
        record = self.variant(phase="review", effect_mode="state-changing", artifact_paths=[artifact], artifact_identity=[], events=[])
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: binding: artifact_identity is empty in a binding-required state (phase review", result.stdout)

    def test_reject_binding_required_artifact_path_without_identity_entry(self):
        spec, digest = self.bound_temp_artifact()
        plan = str(self.dir / "plan.md")
        record = self.record_bound_to(spec, digest, artifact_paths=[spec, plan])
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn(f'reject: binding: artifact path "{plan}" has no artifact_identity entry in a binding-required state', result.stdout)

    def test_reject_identity_entry_not_listed_in_artifact_paths(self):
        spec, digest = self.bound_temp_artifact()
        record = self.record_bound_to(spec, digest, artifact_paths=[str(self.dir / "other.md")])
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn(f'reject: binding: artifact_identity entry "{spec}" is not listed in artifact_paths', result.stdout)

    def test_reject_duplicate_identity_path(self):
        spec, digest = self.bound_temp_artifact()
        record = self.record_bound_to(spec, digest)
        record["artifact_identity"].append(dict(record["artifact_identity"][0]))
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn(f'reject: binding: artifact_identity has duplicate entries for "{spec}"', result.stdout)

    def test_accept_every_bound_artifact_with_exactly_one_identity_entry(self):
        spec, spec_digest = self.bound_temp_artifact()
        plan, plan_digest = self.bound_temp_artifact(content=b"plan\n", name="plan.md")
        record = self.record_bound_to(spec, spec_digest, artifact_paths=[spec, plan])
        record["artifact_identity"].append({"path": plan, "sha256": plan_digest, "refreshed_at": "2026-09-04T13:02:11Z"})
        result = self.run_check(self.write_record(record), expect=0)
        self.assert_outcome(result, "accept")

    def test_reject_approval_event_with_null_artifact(self):
        result = self.run_check(self.write_record(self.record_with_event("approval", artifact=None)), expect=2)
        self.assertIn("reject: event-artifact: events[0].artifact is null for a approval event", result.stdout)

    def test_reject_proceed_and_handoff_events_with_null_artifact(self):
        for kind in ("proceed", "handoff"):
            with self.subTest(kind=kind):
                result = self.run_check(self.write_record(self.record_with_event(kind, artifact=None)), expect=2)
                self.assertIn(f"reject: event-artifact: events[0].artifact is null for a {kind} event", result.stdout)

    def test_reject_approval_event_artifact_matching_no_identity_entry(self):
        wrong_sha = {"path": SPEC_PATH, "sha256": "0" * 64}
        wrong_path = {"path": "/home/user/repo/docs/specs/other.md", "sha256": SPEC_SHA}
        for label, artifact in (("sha", wrong_sha), ("path", wrong_path)):
            with self.subTest(mismatch=label):
                result = self.run_check(self.write_record(self.record_with_event("approval", artifact=artifact)), expect=2)
                self.assertIn("reject: event-artifact: events[0].artifact", result.stdout)
                self.assertIn("matches no current artifact_identity entry", result.stdout)

    def test_accept_proceed_event_matching_identity_entry(self):
        result = self.run_check(self.write_record(self.record_with_event("proceed")), expect=0)
        self.assert_outcome(result, "accept")

    def test_accept_confirmation_event_with_null_artifact(self):
        result = self.run_check(self.write_record(self.record_with_event("confirmation", artifact=None)), expect=0)
        self.assert_outcome(result, "accept")

    def test_accept_commit_selection_event_with_null_artifact(self):
        record = self.record_with_event("commit-selection", artifact=None, source="specialist-checkpoint")
        self.run_check(self.write_record(record), expect=0)

    def test_reject_event_with_missing_source(self):
        record = example_record()
        del record["events"][0]["source"]
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: event-source: required key events[0].source is absent", result.stdout)

    def test_reject_event_with_invalid_source(self):
        record = self.record_with_event("approval", source="assistant")
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn('reject: event-source: events[0].source must be one of user-turn, bound-plan-item, specialist-checkpoint, agent-proposed; got "assistant"', result.stdout)

    def test_reject_event_with_invalid_kind(self):
        record = self.record_with_event("cheer")
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: enum: events[0].kind must be one of", result.stdout)

    # --- event status lifecycle -----------------------------------------------

    def test_accept_superseded_event_with_stale_digest(self):
        record = example_record()
        record["events"].append(
            {"kind": "approval", "source": "user-turn", "at": "2026-09-04T12:00:00Z", "artifact": {"path": SPEC_PATH, "sha256": STALE_SHA}, "status": "superseded", "note": "before the last refresh"}
        )
        result = self.run_check(self.write_record(record), expect=0)
        self.assert_outcome(result, "accept")
        self.assertNotIn("reject:", result.stdout)

    def test_accept_superseded_confirmation_and_commit_selection_with_null_artifact(self):
        for kind, source in (("confirmation", "user-turn"), ("commit-selection", "specialist-checkpoint")):
            with self.subTest(kind=kind):
                record = self.record_with_event(kind, artifact=None, source=source, status="superseded")
                result = self.run_check(self.write_record(record), expect=0)
                self.assert_outcome(result, "accept")

    def test_reject_superseded_event_with_current_digest(self):
        for kind in ("approval", "proceed", "handoff"):
            with self.subTest(kind=kind):
                record = self.record_with_event(kind, status="superseded")
                result = self.run_check(self.write_record(record), expect=2)
                self.assertIn(f'reject: event-status: events[0] is superseded but its artifact ("{SPEC_PATH}", {SPEC_SHA[:12]}...) matches a current artifact_identity entry', result.stdout)

    def test_reject_current_event_with_stale_digest(self):
        for kind in ("approval", "proceed", "handoff"):
            with self.subTest(kind=kind):
                record = self.record_with_event(kind, artifact={"path": SPEC_PATH, "sha256": STALE_SHA}, status="current")
                result = self.run_check(self.write_record(record), expect=2)
                self.assertIn("reject: event-artifact: events[0].artifact", result.stdout)
                self.assertIn("matches no current artifact_identity entry", result.stdout)

    def test_reject_superseded_event_with_null_artifact_for_bound_kinds(self):
        result = self.run_check(self.write_record(self.record_with_event("approval", artifact=None, status="superseded")), expect=2)
        self.assertIn("reject: event-artifact: events[0].artifact is null for a approval event", result.stdout)

    def test_reject_event_with_missing_status(self):
        record = example_record()
        del record["events"][0]["status"]
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn("reject: missing-key: required key events[0].status is absent", result.stdout)

    def test_reject_event_with_invalid_status(self):
        record = self.record_with_event("approval", status="stale")
        result = self.run_check(self.write_record(record), expect=2)
        self.assertIn('reject: enum: events[0].status must be one of current, superseded; got "stale"', result.stdout)

    def test_reject_dominates_flag(self):
        record = self.variant(status="open")
        result = self.run_check(self.write_record(record), now=LATE_NOW, expect=2)
        self.assert_outcome(result, "reject")
        self.assertNotIn("flag:", result.stdout)

    # --- flag rows ---------------------------------------------------------------

    def test_flag_stale_lease_exit_one(self):
        result = self.run_check(self.write_record(example_record()), now=LATE_NOW, expect=1)
        self.assertIn("flag: stale: lease.expires_at 2026-09-04T21:02:11Z is not after now 2026-09-05T01:00:00Z", result.stdout)
        self.assert_outcome(result, "flag")

    def test_now_injection_switches_accept_to_stale(self):
        path = self.write_record(example_record())
        self.run_check(path, now="2026-09-04T21:02:10Z", expect=0)
        result = self.run_check(path, now="2026-09-04T21:02:11Z", expect=1)
        self.assertIn("flag: stale:", result.stdout)

    def test_invalid_now_is_fatal(self):
        result = self.run_check(self.write_record(example_record()), now="yesterday", expect=2)
        self.assertIn("error: --now is not an ISO-8601 instant", result.stderr)
        self.assertIn("outcome: reject", result.stdout)

    def test_now_requires_the_record_timestamp_form(self):
        path = self.write_record(example_record())
        for value in ("2026-09-04T14:00:00+00:00", "2026-09-04T14:00:00", "2026-09-04T14:00:00.000Z", "2026-09-04"):
            with self.subTest(value=value):
                result = self.run_check(path, now=value, expect=2)
                self.assertIn("error: --now is not an ISO-8601 instant with second precision and a Z suffix", result.stderr)
                self.assertIn("outcome: reject", result.stdout)

    def test_flag_tombstone_completed_with_closed_at_and_renewed_lease_not_rejected(self):
        record = self.variant(status="completed", closed_at="2026-09-04T13:02:11Z")
        result = self.run_check(self.write_record(record), expect=1)
        self.assertIn("flag: tombstoned: status completed with closed_at 2026-09-04T13:02:11Z", result.stdout)
        self.assertNotIn("reject:", result.stdout)
        self.assert_outcome(result, "flag")

    def test_flag_superseded_and_cancelled_tombstones(self):
        for status in ("cancelled", "superseded"):
            with self.subTest(status=status):
                record = self.variant(status=status, closed_at="2026-09-04T13:02:11Z")
                result = self.run_check(self.write_record(record), expect=1)
                self.assertIn(f"flag: tombstoned: status {status}", result.stdout)

    def test_flag_foreign_worktree(self):
        result = self.run_check(self.write_record(example_record()), "--expect-worktree", "/home/user/other", expect=1)
        self.assertIn('flag: foreign-worktree: repository.worktree "/home/user/repo" is not the expected "/home/user/other"', result.stdout)

    def test_flag_foreign_session(self):
        result = self.run_check(self.write_record(example_record()), "--expect-session", "sess-02X", expect=1)
        self.assertIn('flag: foreign-session: host_session_id "sess-01H" is not the expected "sess-02X"', result.stdout)

    def test_session_unbound_null_host_session_accepted_with_note(self):
        record = self.variant(host_session_id=None)
        result = self.run_check(self.write_record(record), "--expect-session", "sess-02X", expect=0)
        self.assertIn("note: session-unbound: host_session_id is null; the history-mutation gate and the commit-selection gate ask", result.stdout)
        self.assertNotIn("flag:", result.stdout)
        self.assert_outcome(result, "accept")

    def test_flag_identity_mismatch_against_temporary_artifact(self):
        artifact, _digest = self.bound_temp_artifact(content=b"changed after the last refresh\n")
        record = self.record_bound_to(artifact, SPEC_SHA, events=[])
        result = self.run_check(self.write_record(record), expect=1)
        self.assertIn(f'flag: identity-mismatch: blocker: "{artifact}"', result.stdout)
        self.assert_outcome(result, "flag")

    def test_accept_identity_match_against_temporary_artifact(self):
        artifact, digest = self.bound_temp_artifact()
        record = self.record_bound_to(artifact, digest)
        result = self.run_check(self.write_record(record), expect=0)
        self.assertNotIn("identity-mismatch", result.stdout)
        self.assertNotIn("artifact-not-readable", result.stdout)
        self.assert_outcome(result, "accept")

    def test_unreadable_bound_artifact_is_noted_not_flagged(self):
        result = self.run_check(self.write_record(example_record()), expect=0)
        self.assertIn(f'note: artifact-not-readable: "{SPEC_PATH}"', result.stdout)

    def test_flag_generation_not_greater_than_prior(self):
        for prior_generation in (4, 9):
            with self.subTest(prior_generation=prior_generation):
                prior = self.write_record(self.variant(generation=prior_generation), name="prior.json", directory=self.dir / "prior")
                result = self.run_check(self.write_record(example_record()), "--prior", prior, expect=1)
                self.assertIn(f"flag: generation: generation 4 is not greater than the prior record's {prior_generation}", result.stdout)

    def test_accept_generation_greater_than_prior(self):
        prior = self.write_record(self.variant(generation=3), name="prior.json", directory=self.dir / "prior")
        result = self.run_check(self.write_record(example_record()), "--prior", prior, expect=0)
        self.assert_outcome(result, "accept")

    def test_prior_record_for_another_workflow_is_fatal(self):
        prior_record = self.variant(generation=1, workflow_id=OTHER_WORKFLOW)
        prior = self.write_record(prior_record, name="prior.json", directory=self.dir / "prior")
        result = self.run_check(self.write_record(example_record()), "--prior", prior, expect=2)
        self.assertIn("error: prior record belongs to workflow", result.stderr)
        self.assertIn("outcome: reject", result.stdout)

    def test_malformed_prior_record_is_fatal(self):
        prior = self.write_record("{", name="prior.json", directory=self.dir / "prior")
        result = self.run_check(self.write_record(example_record()), "--prior", prior, expect=2)
        self.assertIn("error: prior record is unreadable or malformed", result.stderr)
        self.assertIn("outcome: reject", result.stdout)

    # --- records-dir conflicts ------------------------------------------------------

    def sibling(self, record_id, **changes):
        record = self.variant(record_id=record_id, **changes)
        return self.write_record(record)

    def test_flag_conflicting_same_workflow_in_records_dir(self):
        path = self.write_record(example_record())
        self.sibling("twin")
        result = self.run_check(path, "--records-dir", self.dir, expect=1)
        self.assertIn(f'flag: conflicting: twin.json is another active record claiming workflow "{EXAMPLE_ID}"', result.stdout)

    def test_flag_conflicting_same_worktree_other_workflow_in_records_dir(self):
        path = self.write_record(example_record())
        self.sibling("other", workflow_id=OTHER_WORKFLOW, lease={"owner": OTHER_WORKFLOW, "renewed_at": "2026-09-04T13:02:11Z", "expires_at": "2026-09-04T21:02:11Z"}, host_session_id=None)
        result = self.run_check(path, "--records-dir", self.dir, expect=1)
        self.assertIn('flag: conflicting: other.json is another active record for worktree "/home/user/repo"', result.stdout)

    def test_records_dir_ignores_tombstoned_expired_and_other_worktree_siblings(self):
        path = self.write_record(example_record())
        self.sibling("done", status="completed", closed_at="2026-09-04T13:02:11Z")
        self.sibling("old", lease={"owner": EXAMPLE_ID, "renewed_at": "2026-09-03T13:02:11Z", "expires_at": "2026-09-03T21:02:11Z"})
        self.sibling("elsewhere", repository={"root": "/home/user/other", "worktree": "/home/user/other", "head": None})
        result = self.run_check(path, "--records-dir", self.dir, expect=0)
        self.assertNotIn("conflicting", result.stdout)

    def test_records_dir_reports_malformed_sibling_and_continues(self):
        path = self.write_record(example_record())
        (self.dir / "broken.json").write_text("{", encoding="utf-8")
        result = self.run_check(path, "--records-dir", self.dir, expect=0)
        self.assertIn("note: sibling-discarded: broken.json is malformed", result.stdout)
        self.assert_outcome(result, "accept")

    def test_records_dir_discards_schema_invalid_sibling_instead_of_conflicting(self):
        path = self.write_record(example_record())
        self.sibling("gen0", generation=0)
        result = self.run_check(path, "--records-dir", self.dir, expect=0)
        self.assertIn("note: sibling-discarded: gen0.json fails the schema (generation)", result.stdout)
        self.assertNotIn("conflicting", result.stdout)

    @unittest.skipUnless(CAN_CREATE_SYMLINK, "symlink support required")
    def test_records_dir_discards_self_referential_symlink_entry(self):
        path = self.write_record(example_record())
        os.symlink("loop.json", self.dir / "loop.json")
        result = self.run_check(path, "--records-dir", self.dir, expect=0)
        self.assertIn("note: sibling-discarded: loop.json is a symlink", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assert_outcome(result, "accept")

    def test_records_dir_excludes_sibling_bound_to_another_session_when_expected_session_given(self):
        path = self.write_record(example_record())
        self.sibling("other", workflow_id=OTHER_WORKFLOW, lease={"owner": OTHER_WORKFLOW, "renewed_at": "2026-09-04T13:02:11Z", "expires_at": "2026-09-04T21:02:11Z"}, host_session_id="sess-02X")
        self.run_check(path, "--records-dir", self.dir, "--expect-session", "sess-01H", expect=0)
        result = self.run_check(path, "--records-dir", self.dir, expect=1)
        self.assertIn("flag: conflicting: other.json", result.stdout)

    def test_records_dir_skips_conflict_scan_for_tombstoned_record(self):
        record = self.variant(status="completed", closed_at="2026-09-04T13:02:11Z")
        path = self.write_record(record)
        self.sibling("successor")
        result = self.run_check(path, "--records-dir", self.dir, expect=1)
        self.assertIn("flag: tombstoned:", result.stdout)
        self.assertNotIn("conflicting", result.stdout)

    def test_missing_records_dir_is_fatal(self):
        result = self.run_check(self.write_record(example_record()), "--records-dir", self.dir / "nowhere", expect=2)
        self.assertIn("error: --records-dir is not a directory", result.stderr)
        self.assertIn("outcome: reject", result.stdout)

    # --- module-level behavior ---------------------------------------------------

    def test_summarize_maps_levels_to_exit_codes(self):
        module = load_module()
        finding = module.Finding
        self.assertEqual(module.summarize([]), ("accept", 0))
        self.assertEqual(module.summarize([finding("note", "x", "y")]), ("accept", 0))
        self.assertEqual(module.summarize([finding("flag", "x", "y"), finding("note", "x", "y")]), ("flag", 1))
        self.assertEqual(module.summarize([finding("flag", "x", "y"), finding("reject", "x", "y")]), ("reject", 2))

    def test_one_reason_line_per_finding(self):
        record = self.variant(host_session_id=None, status="completed", closed_at="2026-09-04T13:02:11Z")
        result = self.run_check(self.write_record(record), "--expect-worktree", "/elsewhere", now=LATE_NOW, expect=1)
        lines = result.stdout.splitlines()
        codes = [line.split(": ")[1] for line in lines if line.startswith(("flag:", "note:"))]
        self.assertEqual(codes, ["stale", "tombstoned", "foreign-worktree", "session-unbound", "artifact-not-readable"])
        self.assertEqual(lines[-1], "outcome: flag")


if __name__ == "__main__":
    unittest.main()
