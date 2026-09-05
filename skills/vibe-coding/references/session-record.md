# Session Record Reference

Read this reference at a workflow's first record write and whenever the
capability map is invalidated; ordinary continuation turns need only the write
points in `SKILL.md`. It carries the session-record schema shared with the
repository checker and any user-installed hook, the router's own conventions
for filling the record, the capability-map cache, and what a checker finding
means for routing.

## Schema

<!-- shared-contract:begin session-record-schema source=shared/vibe-contract.md -->
The session record is one JSON file per workflow and worktree at `.plans/vibe-sessions/<record_id>.json` under the repository root. The workflow router writes it at every route decision; it is never committed, and the root is ignored by version control. It is a record of routing state, not authority: approvals, proceed decisions, and stop boundaries remain in the conversation, and the record names them with their `source`, so a recorded event counts only for its enumerated `source` and only while its `status` is `current`. This schema is shared by the router as writer, by `scripts/vibe_session_record.py` as checker, and by any user-installed hook as reader. Timestamps are ISO-8601 UTC with a `Z` suffix and second precision; enum values are exact strings. The router's six routing fields are `goal`, `phase`, `artifact_paths`, `pending_decision`, `blocker`, and `next_route`. The router records the active phase's effect class as `effect_mode` and its declared write boundary as `allowed_paths`; a phase whose text declares a narrower boundary than its class is read at that boundary.

| Field | Type | Required | Values and rules |
| --- | --- | --- | --- |
| `schema_version` | string | required | `"1"` |
| `record_id` | string | required | equals the file stem; `^[A-Za-z0-9._-]{1,120}$`; router default: `<workflow_id>` |
| `repository.root` | string | required | canonical absolute path of the repository top level |
| `repository.worktree` | string | required | canonical absolute path of the checkout the record belongs to |
| `repository.head` | string or null | required key | commit id at the last write, or null |
| `workflow_id` | string | required | UUIDv4 created at the first route decision of a new workflow (see the write procedure) |
| `host_session_id` | string or null | required key | host session id when exposed; null makes the record session-unbound |
| `generation` | integer ≥ 1 | required | incremented on every write; the writer compares the stored value with the last value it wrote before writing |
| `lease.owner` | string | required | equals `workflow_id` |
| `lease.renewed_at` | timestamp | required | last write time |
| `lease.expires_at` | timestamp | required | `renewed_at` + 8 h on every write, the terminal write included; expiry → stale |
| `status` | enum | required | `active`, `completed`, `cancelled`, `superseded` |
| `closed_at` | timestamp or null | required key | set when `status` ≠ `active` (the tombstone is `status` ≠ `active` with `closed_at` set; the lease fields are not altered) |
| `phase` | enum | required | row ids: `workflow-control`, `requirements-specification`, `creative-direction-exploration`, `code-investigation`, `implementation-planning`, `plan-execution`, `debug-and-repair`, `review`, `plan-pre-check-walkthrough`, `commit-execution`, `writing`, `direct-implementation`, `maintenance` |
| `effect_mode` | enum | required | `read-only`, `artifact-only`, `state-changing`, `none` |
| `allowed_paths` | array of string | required (may be empty) | canonical absolute paths the active phase may write: its declared write boundary plus the unit's scratch root |
| `goal`, `pending_decision`, `blocker`, `next_route` | string / string or null ×3 | required keys | the router's routing fields; `goal` non-empty |
| `artifact_paths` | array of string | required (may be empty) | canonical absolute paths of the active artifacts |
| `artifact_identity[]` | array of object | conditional | `{path, sha256, refreshed_at}` with a canonical absolute `path`; non-empty in a binding-required state; may be empty only in a no-file or pre-creation state; refreshed after any write to a bound artifact |
| `capability_map` | object or null | required key | `{checked_at, source, phases: {<row id>: <specialist name or null>}}` after the first availability check; null before; invalidated when visible specialist metadata changes or the workflow is replaced or cancelled |
| `events[]` | array of object | required (may be empty) | `{kind, source, at, artifact, status, note}`; `kind` ∈ `approval`, `proceed`, `handoff`, `commit-selection`, `confirmation`; `source` ∈ `user-turn`, `bound-plan-item`, `specialist-checkpoint`, `agent-proposed`; `status` ∈ `current`, `superseded` (required); `artifact` is `{path, sha256}` with a canonical absolute `path`, may be null only for `confirmation` and `commit-selection`, must match a current `artifact_identity` entry for a `current` `approval`, `proceed`, or `handoff` event, and must not match one for a `superseded` event; `note` ≤ 200 characters, no secret-like literal |

Write procedure, owned by the workflow router:

- Creation. `workflow_id` is a UUIDv4 created at the first route decision of a new workflow; `record_id` defaults to it; `generation` starts at 1. Concurrent sessions in one checkout each write their own record; there is no exclusive lease, and one workflow claimed by two active records is `conflicting`.
- Every write. Read the stored record and compare its `generation` with the last value this writer wrote — a stored value this writer did not produce is treated as a conflicting record — then increment it, set `lease.renewed_at` to now and `lease.expires_at` to now plus 8 hours, and write the whole record to a temporary file in the same directory under the record's own stem (`<record_id>.tmp`) that is renamed over the record, so a reader sees either the previous record or the new one and never a partial file. The router's own record write is never a gated write. The lease is renewed on every write, immediately before any gated action, and at every phase boundary.
- Paths. `artifact_paths[]`, `artifact_identity[].path`, `events[].artifact.path`, and `allowed_paths[]` are canonical absolute paths: absolute and lexically normalized, with no `.` or `..` segments and no trailing separator. The checker rejects a relative or non-normalized value, and the router converts repository-relative paths it reads from conversation state before writing.
- Digest refresh. After any write the router or its routed specialist makes to a bound artifact, recompute the SHA-256 of the artifact bytes and update its `artifact_identity` entry with a new `refreshed_at`. A recorded digest that no longer matches the opened artifact is a blocker to report, never a gap the router reconciles silently.
- Event lifecycle. Every event is written with `status` `current`. When a digest refresh changes an artifact's digest, every `approval`, `proceed`, or `handoff` event whose `artifact.sha256` no longer matches a current identity entry is marked `superseded` in place — never deleted, never rewritten to the new digest. A superseded event carries no authority; a new approval, proceed, or handoff needs a new event carrying the current digest and its own `source`. `confirmation` and `commit-selection` events are `current` when written and are superseded only when the workflow is replaced.
- Selection on a continuation turn. Before binding, scan every `*.json` in the directory; discard malformed files and report them; keep records that are `active`, unexpired, and belong to this worktree; when both the host's session id and a record's `host_session_id` are known, select the record whose `host_session_id` equals the current host session id. More than one remaining candidate is `conflicting`; routing then continues from conversation state and every gate answers as for a conflicting record. A null `host_session_id` makes the record session-unbound. When no valid record exists, rebind from the latest known artifact path as before.
- Lifecycle. Replacing the workflow marks the old record `superseded` with `closed_at` set and creates a new workflow id; cancelling marks it `cancelled`; completion marks it `completed`. The terminal write renews the lease like any other write; the tombstone is `status` other than `active` with `closed_at` set, and the file stays in place. Rollback is deleting the file.
- Binding state. A phase is binding-required once a bound artifact exists — always for `implementation-planning`, `plan-execution`, and `plan-pre-check-walkthrough`, and for `requirements-specification` once the spec file exists — and is otherwise in a no-file or pre-creation state: a chat-only or no-file requirements phase, any phase before its artifact's first write, and every phase that binds no artifact. `artifact_identity` may be empty only in a no-file or pre-creation state, and every `approval`, `proceed`, or `handoff` event carries an `artifact` whose path and digest match a current identity entry.
- Capability map. Filled at the first availability check of a workflow and reused for the rest of it; invalidated when visible specialist metadata changes or the workflow is replaced or cancelled.
- No field may carry a secret-like literal — an API key, access token, password, private key, bearer value, or env-style secret assignment — and the checker rejects a record whose free text carries one.

Record states, the checker's outcome and exit code, and what each gate returns:

| Record state | Checker outcome and exit | History-mutation gate | Commit-selection gate | Read-only-phase write gate |
| --- | --- | --- | --- | --- |
| absent | not applicable | `ask` | `ask` | `allow` |
| malformed (unparseable or schema failure) | reject, 2 | `ask` | `ask` | `allow` |
| empty `artifact_identity` in a binding-required state; `approval`, `proceed`, or `handoff` event whose `artifact` is null; `current` event of those kinds whose `artifact` matches no current identity entry; `superseded` event whose `artifact` still matches one; missing or invalid `source` or `status` | reject, 2 | `ask` | `ask` | `allow` |
| stale (`lease.expires_at` past) or tombstoned (`status` ≠ `active` with `closed_at` set) | flag, 1 | `ask` | `ask` | `allow` |
| foreign (worktree or host session mismatch) | flag, 1 | `ask` | `ask` | `allow` |
| session-unbound (`host_session_id` null) | accept with note, 0 | `ask` | `ask` | `allow` |
| conflicting (another active, unexpired record for this worktree claims the same workflow, or cannot be told apart by host session) | flag, 1 | `ask` | `ask` | `allow` |
| identity mismatch (recorded SHA-256 differs from the opened artifact) | flag as blocker, 1 | `ask` | `ask` | `allow` |
| generation not greater than the supplied prior record | flag, 1 | `ask` | `ask` | `allow` |
| valid, active, session-bound; `effect_mode` `read-only` or `artifact-only`; target path outside `allowed_paths` | accept, 0 | `ask` quoting the determination | `ask` quoting `source` | `deny` quoting `phase` and `allowed_paths` |
| valid, active, session-bound; `effect_mode` `state-changing` | accept, 0 | `ask` quoting the determination | `ask` quoting `source` | `allow` |

Example (complete; accepted by the checker with an `artifact-not-readable` note because the artifact path is illustrative; the specialist names in `capability_map.phases` are placeholders for whatever the host exposes):

```json
{
  "schema_version": "1",
  "record_id": "3f1c9a52-6b7e-4c1d-9a0e-2f7d4c8b1e10",
  "repository": {"root": "/home/user/repo", "worktree": "/home/user/repo", "head": "a1b2c3d"},
  "workflow_id": "3f1c9a52-6b7e-4c1d-9a0e-2f7d4c8b1e10",
  "host_session_id": "host-session-01",
  "generation": 4,
  "lease": {"owner": "3f1c9a52-6b7e-4c1d-9a0e-2f7d4c8b1e10", "renewed_at": "2026-09-04T13:02:11Z", "expires_at": "2026-09-04T21:02:11Z"},
  "status": "active",
  "closed_at": null,
  "phase": "implementation-planning",
  "effect_mode": "artifact-only",
  "allowed_paths": ["/home/user/repo/docs/plans/2026-09-04-csv-import-implementation-plan.md", "/tmp/scratch/unit-1"],
  "goal": "add CSV import",
  "pending_decision": null,
  "blocker": null,
  "next_route": "implementation-planning",
  "artifact_paths": ["/home/user/repo/docs/specs/2026-09-04-csv-import-spec.md"],
  "artifact_identity": [{"path": "/home/user/repo/docs/specs/2026-09-04-csv-import-spec.md", "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", "refreshed_at": "2026-09-04T13:02:11Z"}],
  "capability_map": {"checked_at": "2026-09-04T12:40:00Z", "source": "host skill metadata", "phases": {"implementation-planning": "planning-specialist", "commit-execution": "commit-specialist", "review": null}},
  "events": [{"kind": "approval", "source": "user-turn", "at": "2026-09-04T12:58:40Z", "artifact": {"path": "/home/user/repo/docs/specs/2026-09-04-csv-import-spec.md", "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"}, "status": "current", "note": "spec approved in the user's own words"}]
}
```

A package may state which of its phases this gate applies to; it may not change the gate's inputs, outcomes, or fields.
<!-- shared-contract:end session-record-schema -->

## Router Conventions

- `phase` is the row id from the decision table. While the goal-alignment gate
  is pending, `phase` is `workflow-control`, `effect_mode` is `none`,
  `pending_decision` names the confirming question, and `next_route` is null;
  the `confirmation` event is appended after the user's answer, and the
  instruction is then classified.
- `effect_mode` per row: `workflow-control` `none`;
  `creative-direction-exploration` and `code-investigation` `read-only`;
  `requirements-specification`, `implementation-planning`,
  `plan-pre-check-walkthrough`, and `writing` `artifact-only`;
  `plan-execution`, `debug-and-repair`, `review`, `commit-execution`,
  `direct-implementation`, and `maintenance` `state-changing`.
- `allowed_paths` are canonical absolute paths. For an artifact-only row: the
  bound artifact path — the spec, the plan, the plan under walkthrough, or the
  text artifacts the request names — plus the supporting paths the specialist's
  own text declares and the unit's scratch root. For a read-only row: only a
  saved artifact the user explicitly asked for, else empty. For a
  state-changing row: the surfaces the row's scope declares, plus the scratch
  root. `workflow-control` records an empty list.
- `goal` is the current goal in the user's terms and is never empty once a
  workflow exists; `artifact_paths` are the active artifact paths;
  `pending_decision`, `blocker`, and `next_route` are null when none exists.
- `host_session_id` is the host's session id when the host exposes one in the
  environment or the invocation, else null. Never invent one; a null value is
  reported once as session-unbound when a gated action is first reached.
- Every event is written with `status: current`. `approval`, `proceed`, and
  `handoff` events carry `artifact` with the canonical absolute path and digest
  of the artifact they concern, matching a current `artifact_identity` entry;
  `commit-selection` and `confirmation` events may carry null. A digest refresh
  marks every `approval`, `proceed`, or `handoff` event whose digest no longer
  matches `superseded` in place — never deleted, never rewritten to the new
  digest — and a superseded event carries no authority: the approval, proceed,
  or handoff must be recorded again as a new event carrying the current digest
  and its own `source`. `note` states where the event came from in at most 200
  characters and never carries a secret-like literal. A router-owned row's own
  checkpoint is recorded with `source: specialist-checkpoint`.
- All recorded paths — `artifact_paths`, `artifact_identity[].path`,
  `events[].artifact.path`, `allowed_paths` — are canonical absolute paths.
  Conversation state and specialist reports usually name repository-relative
  paths; the router converts them against the repository root before writing.
- Each write goes through the temporary file `<record_id>.tmp` in the record's
  directory, renamed over the record. The router's own record write is never a
  gated write; the read-only-phase write gate's control-plane exception in
  `SKILL.md` names it.
- The plan's implementation-progress ledger is plan-execution state and stays
  in the plan; the record carries the routing fields only, never a copy of the
  ledger, and rebinding the active slice still goes through the execution
  specialist's own verification.

## Capability Map

At the workflow's first availability check, fill `capability_map` with
`checked_at`, the `source` checked — the environment's visible skill metadata,
user-provided material, repository metadata, or project instructions — and
`phases`: each specialist-owned row id mapped to the visible specialist's name
exactly as its metadata states it, or null when none matches. Router-owned rows
have no entry. Reuse the map for every later route decision in the workflow;
a `matched-but-unavailable` report for a row reads the cached null for that
row, and the user's decision to proceed without the specialist is recorded as a
`confirmation` event with `source: user-turn`, not as a change to the map.

Invalidate the map — set it to null and verify again at the next route
decision — when visible specialist metadata changes (a specialist appears,
disappears, or its description changes) or when the workflow is replaced or
cancelled; a replacement's new workflow starts with a null map.

## Checker Findings And Routing

The record-state table in the schema names what each gate returns for every
state. For routing: a record the checker would reject or flag is not used to
rebind. Routing continues from conversation state and the active artifact
paths, the finding is reported, and the next route decision writes a fresh
record; a malformed file is reported and left in place; a conflicting pair is
reported, neither is selected, and every gate answers as for a conflicting
record until the user cancels or replaces one of the workflows. An identity
mismatch means the bound artifact changed outside the recorded refresh: report
it as a blocker and never overwrite the digest to make it match.
