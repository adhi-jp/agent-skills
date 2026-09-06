# Session Record Reference

Read this reference at a workflow's first record write and whenever the
capability map is invalidated; ordinary continuation turns need only the write
points in `SKILL.md`. It carries the rendered session-record schema block
shared with the repository checker and any user-installed hook, the router's
own conventions for filling the record, the capability-map cache, and what a
checker finding means for routing; the field table, the write procedure, and
the record-state table are in `shared/vibe-contract.md`.

## Schema

<!-- shared-contract:begin session-record-schema source=shared/vibe-contract.md -->
**Write the session record at every route decision as routing state, never as authority.**

- Before the first write of a record, read the field table and write procedure in the appendix of `shared/vibe-contract.md`.
- Keep one JSON file per workflow and worktree at `.plans/vibe-sessions/<record_id>.json` under the repository root; never commit it.
- Leave approvals, proceed decisions, and stop boundaries in the conversation; a recorded event counts only for its enumerated `source` and only while its `status` is `current`.
- Write `schema_version` as the string `"1"`.
- Set `lease.owner` equal to `workflow_id`.
- Record the active phase's effect class as `effect_mode` and its declared write boundary as `allowed_paths`.
- Record as `allowed_paths` the narrower boundary when a phase's own text declares one tighter than its class.
- Fill `goal`, `phase`, `artifact_paths`, `pending_decision`, `blocker`, and `next_route` at every write.
- Compare the stored `generation` with the last value you wrote — one you did not produce is a conflicting record — then increment it.
- Write the whole record to `<record_id>.tmp` beside it and rename that over the record, so a reader sees the previous record or the new one, never a partial file.
- Never treat the router's own record write as a gated write.
- Renew the lease on every write, immediately before any gated action, and at every phase boundary.
- Write `artifact_paths[]`, `artifact_identity[].path`, `events[].artifact.path`, and `allowed_paths[]` as canonical absolute paths — lexically normalized, no `.` or `..` segment, no trailing separator — converting repository-relative paths read from conversation state first.
- Refresh a bound artifact's `artifact_identity` digest and `refreshed_at` after any write the router or its routed specialist makes to it.
- Report a recorded digest no longer matching the opened artifact as a blocker; never reconcile it silently.
- When a digest refresh changes an artifact's digest, supersede in place every `approval`, `proceed`, or `handoff` event whose `artifact.sha256` no longer matches a current identity entry.
- Never delete such an event and never rewrite it to the new digest.
- Select the record on a continuation turn, before binding:
  - scan every `*.json` in the directory, discarding and reporting malformed files;
  - keep records that are `active`, unexpired, and belong to this worktree;
  - when both the host's session id and a record's `host_session_id` are known, select the record whose `host_session_id` equals the current host session id;
  - treat a record whose `host_session_id` is null as session-unbound;
  - treat more than one remaining eligible candidate as `conflicting`, route from conversation state, and answer every gate as for a conflicting record;
  - rebind from the latest known artifact path when no valid record exists.
- Mark the old record `superseded` with `closed_at` set and create a new workflow id when the workflow is replaced; mark it `cancelled` on cancellation, `completed` on completion.
- Set `closed_at` for every terminal status — `superseded`, `cancelled`, `completed`.
- Leave the tombstoned file in place; roll back only by deleting it.
- Treat a phase as binding-required once a bound artifact exists — always for `implementation-planning`, `plan-execution`, `plan-pre-check-walkthrough`, and for `requirements-specification` once the spec file exists.
- Leave `artifact_identity` empty only in a no-file or pre-creation state.
- Fill the capability map at a workflow's first availability check and reuse it for that workflow; invalidate it when visible specialist metadata changes or the workflow is replaced or cancelled.
- Never write a secret-like literal into any field.
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
  root. `workflow-control` records an empty list. For a row that writes
  records, `allowed_paths` also lists `docs/decisions/` and
  `docs/reports/findings/` — or the repository's existing record directory —
  as the declared supporting paths for its decision records and findings
  report.
- At the finish gate, an unpersisted carry-forward packet is reported as
  unpersisted with the one action that would persist it; the record carries no
  packet fields.
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
- Conversation state and specialist reports usually name repository-relative
  paths; the router converts them against the repository root before writing.
- Each write goes through the temporary file `<record_id>.tmp` in the record's
  directory, renamed over the record. The router's own record write is never a
  gated write; the read-only-phase write gate's exception in `SKILL.md` names
  it.
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

The record-state table in `shared/vibe-contract.md` names what each gate
returns for every state. For routing: a record the checker would reject or
flag is not used to rebind. Routing continues from conversation state and the
active artifact paths, the finding is reported, and the next route decision
writes a fresh record; a malformed file is reported and left in place; a
conflicting pair is reported, neither is selected, and every gate answers as
for a conflicting record until the user cancels or replaces one of the
workflows. An identity mismatch means the bound artifact changed outside the
recorded refresh: report it as a blocker and never overwrite the digest to make
it match.
