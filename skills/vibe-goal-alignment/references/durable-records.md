# Durable Records

Read this before applying, writing, or updating a decision record or findings entry, and before handing one forward as a carry-forward packet.

## Decision records

<!-- shared-contract:begin decision-records source=shared/vibe-contract.md -->
**Record a settled decision that binds later work before the next step that depends on it.**

- Record a decision that binds work beyond the current unit — structure, interface, data or file format, dependency, build, deployment, security boundary, a cross-unit convention, or a standing user constraint — when at least one holds:
  - a viable alternative was rejected;
  - it reverses an earlier decision or a default;
  - it settled an ambiguous or repeatedly corrected instruction;
  - an agent or proxy chose it.
- Never record a choice the code fully explains, a local choice one commit can reverse, task order, requirements or acceptance criteria, or a repair that sets no rule for other units; put a rule without rationale in the project instructions.
- Write one decision per file at `docs/decisions/NNNN-<slug>.md`, indexed in `docs/decisions/README.md`, or in the repository's existing ADR directory with its numbering. Allocate `ADR-NNNN` one above the highest id in the directory and index; never reuse an id.
- Write the record in this shape, self-contained and near 40 lines:

```markdown
---
id: ADR-NNNN
title: <title>
status: proposed | accepted | rejected | deprecated | superseded
date: <YYYY-MM-DD of the last status change>
decided-by: user | agent | proxy
ratified: user | pending
summary: <one imperative sentence, at most 140 characters>
paths: [<globs the decision binds; empty means repository-wide>]
tags: [<topics>]
supersedes: [<ids>]
superseded-by: <id or null>
confirmation: <command or check proving compliance, or "manual: <check>, <why no automated check exists>">
revisit-when: <trigger>
sources: [<user-turn date and deciding phrase | artifact path#heading | commit | proxy run id>]
---
# ADR-NNNN. <title>
## Context and Problem Statement
## Considered Options
- <option>: chosen | rejected, because <reason>
## Decision Outcome
Chosen: <option>, because <reason>. <The rule, in imperative form.>
### Consequences
- Good | Bad, because <reason>
### Confirmation
```

- Mark a user decision with recorded acceptance `accepted` and `ratified: user`; an agent or proxy decision already in effect is `accepted` with `ratified: pending`; a declined one is `rejected` with the reason.
- Only a user can accept a human-risk decision; without that acceptance its record stays `proposed`.
- Change an accepted record only in its status fields and an optional dated `### Amendments` list; a change of meaning is a new record, with `supersedes` and `superseded-by` updated in both records and the index.
- Add one index row per record, keeping superseded and deprecated rows with empty `paths`: `- ADR-NNNN | <status> | <decided-by>/<ratified> | <paths> | <tags> | <summary> | [file](NNNN-<slug>.md)`.
- A record applies when a `paths` glob matches a file in the unit, a tag names its topic, or its `paths` is empty and its summary concerns the unit; the file outranks its index row.
- Rebuild a missing or disagreeing index from the records' front matter, in memory when this phase may not write.
- Apply `accepted` records; surface a `ratified: pending` one as an assumption wherever it would narrow a live user request. Never apply `proposed`, `rejected`, or `deprecated` records; follow `superseded` to the replacement.
- Re-propose an option an accepted record rejected only with new evidence, and stop with a finding when two applicable accepted records conflict.
- Cite the record id from specs, plans, and ledgers instead of restating its rationale. Run applicable `confirmation` checks at review or verification.
- At commit time, report a diff touching an accepted record's `paths` unless it conforms or the same commit carries the superseding record.
- Ask the user once per repository, at the first checkpoint that would include a record or findings report, whether they are committed; record the answer as a decision, and until then leave the files untracked and say so.
- A phase that may not write hands the decision forward in its summary as a packet — decision, rejected alternatives, rationale, provenance, scope, proposed status — marked unpersisted, naming the writing phase that would record it; never call it durable.

Example: choosing UTC for persisted timestamps after rejecting local time is recorded although the rule is visible in the code; one retry added to one call is not.

Exception: a read-only phase or commit execution writes a record only when the user explicitly asks for a saved artifact.
<!-- shared-contract:end decision-records -->

## Deferred findings

<!-- shared-contract:begin deferred-findings source=shared/vibe-contract.md -->
**Write each material problem the unit deliberately leaves unaddressed to the findings report before the unit closes.**

- A finding is a deferred or blocked item, an accepted residual risk, a scope-blocked or dropped plan item, or a defect or concern outside the unit's scope that the phase chose not to fix.
- Never turn a current blocker into a finding to unblock the unit.
- Write the entry when the deferral is decided, into one report per workflow at `docs/reports/findings/YYYY-MM-DD-<goal-slug>.md` (`-2` on a name collision) with front matter `goal`, `date`, `phases`, and `source_artifacts`.
- Allocate `DF-NNNN` one above the highest id in any report or the index, closed entries included; never reuse an id. Write each entry in this shape:

```markdown
## DF-NNNN <title>
- Status: deferred | blocked | accepted-residual | resolved | invalidated | duplicate-of DF-NNNN
- Severity: critical | high | medium | low | unknown
- Scope: <paths or component>
- Evidence: <evidence class>, <anchor>, <date or commit>
- Why not addressed: <reason>
- Decided by: user | agent | proxy
- Revisit when: <trigger>
- Next action and owner: <action>, <owner or unassigned>
- Closure: <date, commit, verification; filled on resolution>
```

- Use `blocked` when the work waits on an unavailable owner, dependency, decision, or environment, and `deferred` when it is simply scheduled later; `accepted-residual` needs recorded user acceptance, and an agent-deferred item is surfaced to the user.
- Index each open finding in `docs/reports/findings/README.md` as `- DF-NNNN | <status> | <severity> | <scope> | <title> | [entry](<report>.md#<entry-anchor>)`, rebuilding a missing or disagreeing index from the reports.
- Close a finding by updating its original entry's status and closure and removing its index row; never delete or rewrite a closed entry, and point a duplicate at its canonical id.
- Cite finding ids from plans, ledgers, reviews, and worker reports instead of restating them; the chat summary names the report path and the open ids, or says that no report was needed.
- A phase that may not write hands the finding forward as a packet — title, severity, scope, evidence, why not addressed, who decided, revisit trigger — marked unpersisted, naming the writing phase that would record it.

Exception: a read-only phase or commit execution writes no report unless the user explicitly asks for a saved artifact.
<!-- shared-contract:end deferred-findings -->
