# Durable Records

Read this reference before recording a settled decision, deferring a finding, closing a unit, or starting the phase. It carries the shared decision-record and deferred-findings obligations and, where this phase reads or writes records, their formats; the phase's own boundary text in `SKILL.md` names the directories it may write.

## Decision records

<!-- shared-contract:begin decision-records source=shared/vibe-contract.md -->
**Record a settled decision that binds work beyond the current unit before the next dependent action.**

- A decision qualifies when it constrains work beyond the current unit: structure, interface or contract, data model or persisted format, dependency, build, deployment, security or permission boundary, a convention or policy another unit must follow, or a standing user constraint.
- Require, in addition, at least one of: a viable alternative was rejected; it reverses or supersedes an earlier decision or a default; it settled an ambiguous instruction or a repeated correction; it was AI-selected or proxy-selected with cross-unit effect.
- Read the unit as the piece of work the phase closes and checkpoints, and a decision as settled the moment the deciding actor's answer is recorded: the user's turn, the adopted proxy result, or the gate outcome.
- Never record a choice whose rule and reason are both evident from the code, a choice reversible in one commit with no downstream contract, task sequencing, requirements or acceptance criteria, a residual finding, or a rule with no rationale.
- Record a bug root cause or repair only when it sets a rule another unit must follow; the commit message and regression test carry the rest. Record a spec item only when it sets a durable product constraint or non-goal.
- Record a residual finding only when it sets a lasting policy, citing the finding id; put a rule with no rationale in the project instruction file and link it.
- Treat only the rule as recoverable from the code; rationale, rejected alternatives, and reversals never are, so a decision meeting both criteria is recorded even when its rule is in the diff.
- Write one decision per record and cite the record id from the spec, plan, or ledger instead of restating its rationale.
- Write the record immediately after the decision is settled and before the next dependent action; reconcile status, links, index, and consequences at unit close; sweep for unrecorded qualifying decisions at the finish gate.
- Select a checkpoint or update an implementation progress ledger only when no unrecorded qualifying decision remains.
- Read the decision index and the open-findings index when a planning, execution, repair, review, orchestration, or router-owned phase starts; open only the applicable records and findings; read an accepted record's considered options before proposing an alternative it covers.
- Perform the confirmation checks of the applicable records at review or verification; at commit time, check a diff touching an accepted record's paths for conformance or its superseding record in the same commit, and otherwise report the conflict.
- Hand a decision forward as a carry-forward packet when this phase may not write it: the decision, rejected alternatives, rationale, provenance, scope, and proposed status (`proposed | accepted`); the next writing phase records it.
- Carry a packet in the phase summary and conversation state; report an unpersisted packet at the finish gate as unpersisted, with the one action that would persist it; never claim a packet is durable.
- Ask the user once per repository, at the first checkpoint that would include a record or report, whether records and reports join that repository's checkpoints; write the answer as a record and apply it to later checkpoints.
  - Until the answer exists the file stays untracked and the summary says so; an ignore rule keeps the file local and the summary says so.
- Treat an unratified agent-selected record as an assumption to surface whenever it would narrow a live user request; it binds nothing the user has not accepted.

Example: choosing UTC for persisted timestamps after rejecting local time is recorded although the rule is visible in the code; one retry added to one call is a commit-message fact unless other call sites must follow it.

Exception: a read-only phase or commit execution writes a record only on the user's explicit saved-artifact request; otherwise it hands the packet forward.
<!-- shared-contract:end decision-records -->

## Decision-record schema

<!-- shared-contract:begin decision-record-schema source=shared/vibe-contract.md -->
**Write each decision record as one Markdown file with this front matter, these sections, and one index row.**

- Store records at `docs/decisions/NNNN-<slug>.md` with the index at `docs/decisions/README.md`; reuse an existing `docs/adr/`, `doc/adr/`, `adr/`, or `decisions/` directory and its numbering when one exists; convert nothing without an explicit request.
- Allocate `id` as `ADR-NNNN`, one more than the highest id in the index or directory, never reused; after a merge exposes two records with one id, renumber the one that entered the mainline later and update its references.
- Front matter: `id`; `title`; `status` (`proposed | accepted | rejected | deprecated | superseded`); `date` (last status change); `decided-by` (`user | agent | proxy`); `ratified` (`user | pending`); `summary` (one imperative sentence, at most 140 characters).
- Then `paths` (globs the decision binds; empty means repository-wide); `tags`; `supersedes`; `superseded-by`; `confirmation` (a command or check proving compliance, or `manual:` plus the check and why no automated check exists); `revisit-when`; `sources`.
- Give every `sources` entry its authority: a user-turn date with its deciding phrase, a tracked artifact path with heading, a commit, or the proxy run identity; prefer tracked anchors and cite an ignored artifact only as a supplement.
- Body sections in order: `# ADR-NNNN. <title>`, `## Context and Problem Statement`, `## Considered Options` (one line per option, rejected ones with the reason), `## Decision Outcome` (chosen option with its reason, then the rule in imperative form).
- Then `### Consequences` (good and bad, each with its reason), `### Confirmation`, and an optional `### Amendments` list of dated later observations that do not change the decision.
- Keep each record self-contained, restating the decision and rationale so it stays readable when its sources are gone; target 40 lines and never exceed 120.
- Write `accepted` with `ratified: user` for a user decision with a recorded acceptance anchor; write `accepted` with `decided-by: agent` or `proxy` and `ratified: pending` for a delegable decision already in effect.
- Never write `accepted` for a human-risk decision without recorded user acceptance; keep it `proposed`. A user who declines a record makes it `rejected` with `ratified: user` and the reason.
- Change an accepted record only in `status`, `date`, `ratified`, `superseded-by`, `Amendments`, and typo fixes; a change of meaning is a new superseding record, and supersession is written into both records and the index together.
- Deviations from MADR 4.0.0: stable ids and two-way supersession links replace the status-string supersession because agents match by id; `paths`, `tags`, and `summary` let the index alone screen relevance.
- `decided-by` and `ratified` separate AI-selected defaults from human approval; `confirmation` is required so a reader has a check; `decision-makers`, `consulted`, and `informed` fold into `decided-by` and `sources`.
- `Decision Drivers`, `Pros and Cons of the Options`, and `More Information` are dropped; their content compresses into the outcome clause, the option lines, and `revisit-when`.

Example: front matter `id: ADR-0007`, `status: accepted`, `decided-by: agent`, `ratified: pending`, `paths: ["src/cache/**"]`, `summary: Keep the local cache in one SQLite file.`
<!-- shared-contract:end decision-record-schema -->

## Decision-record index

<!-- shared-contract:begin decision-record-index source=shared/vibe-contract.md -->
**Read records through the index and apply each by its status and ratification.**

- Index rows: one line per record with columns `id | status | decided-by/ratified | paths | tags | summary | file`; keep superseded and deprecated rows with empty `paths`.
- A record applies when a `paths` glob matches a file in the unit's scope, a tag equals a topic the unit names, or `paths` is empty and the summary concerns the unit's subject; open every applicable record.
- Stop with a finding when two applicable accepted records conflict, until one supersedes the other; a record file outranks its index row.
- Rebuild a missing or disagreeing index from the front matter before proceeding when this phase may write; otherwise reconstruct it in memory, proceed, and report the stale index in the carry-forward packet.
- Index a legacy record whose front matter is absent or unparseable with its first heading as title, `status` from a status line or section when present and `unknown` otherwise, and empty `paths` and `tags`.
- Open an `unknown` record when its title or file name names the unit's subject, apply nothing from it automatically, and report it as unclassified.
- Readers: `accepted` with `ratified: user` binds the unit; `accepted` with `ratified: pending` is applied inside its scope but surfaced as an assumption whenever it would narrow a live user request; `proposed` is not in effect and is reported.
- `rejected` is not re-proposed without new evidence; `deprecated` is ignored; `superseded` is followed to its replacement.
- Never apply a `proposed`, `rejected`, or `deprecated` record, and never treat an unratified record as the user's constraint.

Example: `- ADR-0007 | accepted | agent/pending | src/cache/** | storage | Keep the local cache in one SQLite file. | [file](0007-single-sqlite-cache.md)`
<!-- shared-contract:end decision-record-index -->

## Deferred findings

<!-- shared-contract:begin deferred-findings source=shared/vibe-contract.md -->
**Write every defect or concern discovered but deliberately not addressed to the findings report before the unit closes.**

- Count as a finding a deferred or blocked item, an accepted residual, a scope-blocked plan item, a dropped or later-round contracted item, and any defect or concern outside the unit's scope that the phase chose not to fix.
- Write the entry immediately when the deferral is decided; reconcile entries and the index at unit close and at the finish gate; the chat report names the report path and repeats the open ids.
- Write the report from every state-changing phase except commit execution and from every artifact-only phase, inside the report directory the phase's own text declares.
- Hand a finding forward as a carry-forward packet from a read-only phase or commit execution, carrying its title, severity, scope, evidence, why it was not addressed, who decided, and revisit trigger; write a file only on the user's saved-artifact request.
- Keep the report the one durable carrier for deferred, blocked, unresolved, and accepted-residual items; a plan ledger, debug ledger, review summary, or worker report cites the finding id instead of restating it.
- Never convert a current blocker into a finding to unblock the unit; a finding records work the unit legitimately does not do.
- Read the open-findings index when a planning, execution, repair, review, orchestration, or router-owned phase starts and open the findings whose scope names a path or component the unit touches or whose title names its subject.
- Close a finding by updating its original entry's status and closure fields and its index row when a later unit resolves it; a read-only phase proposes the closure in its packet.
- Record who decided the deferral (`user`, `agent`, or `proxy`); an accepted residual needs recorded user acceptance, and an agent-deferred item is surfaced to the user in the summary.

Exception: when no material unaddressed finding exists at unit close, no report file is created and the summary says so.
<!-- shared-contract:end deferred-findings -->

## Deferred-findings schema

<!-- shared-contract:begin deferred-findings-schema source=shared/vibe-contract.md -->
**Write each findings report as one file per workflow with these entry fields and one index row per finding.**

- Store the report at `docs/reports/findings/YYYY-MM-DD-<goal-slug>.md`, adding `-2` on a name collision, with the open-findings index at `docs/reports/findings/README.md`; create the file only when at least one material finding exists.
- Give the report front matter `goal`, `date`, `phases`, and `source_artifacts`, and head each finding with `## DF-NNNN <title>`.
- Allocate `DF-NNNN` as one more than the highest id in the index or any report, never reused; after a merge exposes two entries with one id, renumber the later-merged entry and update its references.
- Fields per finding: status (`deferred | blocked | accepted-residual | resolved | invalidated | duplicate-of DF-NNNN`); severity (`critical | high | medium | low | unknown`); scope (paths or component); evidence (class, anchor, date or commit).
- Then why not addressed; decided by (`user | agent | proxy`); revisit when; next action and owner (`unassigned` allowed); closure (date, commit, verification), filled on resolution.
- Index rows: one line per open finding, removed when the entry closes, with columns `id | status | severity | scope | title | file`, the file link pointing at the entry heading.
- A finding applies to a unit when its scope names a path or component the unit touches or its title names the unit's subject; an index that is missing or disagrees with the reports follows the decision-index rebuild rule.
- Never delete or rewrite a closed entry; closure appends the closure fields and flips the status, and a duplicate points at its canonical id.
- Keep entries self-contained: the evidence anchor and the reason it was not addressed stay readable when the workflow's spec or plan is gone.

Example: `- DF-0012 | deferred | high | src/sync/** | Retry loop can starve the writer | [entry](2026-09-06-csv-import.md#df-0012-retry-loop-can-starve-the-writer)`
<!-- shared-contract:end deferred-findings-schema -->

When choosing between `blocked` and `deferred`, use `blocked` when work requires an unavailable external owner, dependency, decision, or environment, and `deferred` when no external prerequisite is missing and the work is simply scheduled for a later cycle.
