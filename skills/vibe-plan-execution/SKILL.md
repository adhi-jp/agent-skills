---
version: 6.0.3
name: vibe-plan-execution
description: Use when the user asks to execute, implement, continue, or apply an existing implementation plan, specification, acceptance criteria, task plan, or prior planning output. Do not use for plan creation or coding requests with no concrete plan to bind.
---

# Vibe Plan Execution

## Overview

Execute a concrete implementation plan slice by slice without inventing
behavior, and stop when current evidence contradicts it. The plan governs scope
and intent, not known-bad implementation details. If no concrete plan exists,
return to planning before coding; this skill does not create or review plans.

## Effect And Write Boundaries

<!-- shared-contract:class language=chat commit=state-changing effect=state-changing -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
**Write nothing beyond what the phase's declared effect class and boundary permit.**

- Apply the effect class the phase declares in its own text; where this package states a narrower limit, the narrower limit wins.
- Read-only: report in chat; edit no file, run no state-mutating command, and never stage, commit, tag, push, change versions, delete data, or start services. Write a file only when the user explicitly asks for a saved artifact.
- Artifact-only: create or update only the artifact the phase owns and the supporting paths its text declares, such as a confirmed plan reflection or a decision record, and leave them in the working tree.
- Never let an artifact-only phase implement executable behavior, edit code or tests as implementation, produce another phase's artifact, do release work, or treat its artifact as same-turn implementation authority.
- State-changing: edit and run commands only inside the declared scope, in its smallest verified unit; leave other paths, pre-existing changes, and runtime or external state untouched unless the user selects them.
- These limits cover shell commands (redirection, `sed -i`, `tee`, `mv`, `cp`, `rm`, `git checkout --`) as well as file tools; report a refused write as a boundary stop and never retry it through another tool.
- Keep every irreversible or outward-facing operation under its own consent.
<!-- shared-contract:end effect-write-boundaries -->

The scope this phase declares is the current slice the bound plan authorizes,
implemented as its smallest coherent testable unit, plus the decision records
and findings reports named under `Durable Records`.

## Chat Language

<!-- shared-contract:begin language-precedence-chat source=shared/vibe-contract.md -->
**Resolve the language of user-facing chat text separately from any artifact's language, in this order:**

1. An explicit current-user instruction for chat, response, or output language.
2. `VIBE_CHAT_LANGUAGE`, a language name or BCP47 tag such as `ja` or `pt-BR`, when readable or set by the user for this request; an empty or invalid value is unset.
3. The user's active conversational language, else the last clear one in this workflow.
4. English.

- Never infer chat language from artifacts, file contents, paths, commands, code, skill invocations, or host-wrapper text unless the user makes them the language contract.
- Keep paths, commands, identifiers, environment variables, locale tags, message keys, product names, and code verbatim unless the user asks to translate them.
<!-- shared-contract:end language-precedence-chat -->

Also keep evidence labels and plan headings verbatim.

## Durable Records

At phase start, check `docs/decisions/README.md` and
`docs/reports/findings/README.md` (or the repository's existing indexes) for
entries whose paths, tags, or subject match this unit. Read
`references/durable-records.md` before applying such an entry, recording a
settled decision, deferring a finding, or handing either forward. This phase
may write `docs/decisions/` and `docs/reports/findings/` (or the repository's
existing record directories).

## Plan Sources

Bind one plan before editing and name it in the first progress note: its path
when it is a file, otherwise its title. When a local plan artifact exists, read
it; a chat summary is only a navigation aid, so follow the artifact and flag
anything the summary adds or contradicts. Read the current slice's scope,
acceptance criteria, non-goals, verification, risks, and proceed condition.
High-risk sections such as a behavior inventory, equivalence analysis,
recovery evidence, or selected failure-pattern checks are contract too; a
stale or missing one whose precondition still applies is a plan problem, never
permission for weaker proof. Treat user claims as intent until checked.

- Complete only a plan-authored `Reserved decisions` row within its stated
  carrier; never change scope, criteria, tests, risks, or steps through it.
- Satisfy a blocked or conditional proceed condition first; a request to
  implement anyway does not satisfy it.
- A slice is concrete when it has a goal, scope, acceptance checks, a
  verification path, and an implementation direction. If a missing element
  could change behavior, proof, data, permissions, contracts, or UX, return to
  planning instead of inventing it, and report the plan item, the missing
  evidence, and what is needed to resume.
- If the plan's contract changed since it was last reviewed or bound, rebind
  only a change with clear user or revision authority, after re-reading the
  sections it affects; otherwise stop for plan revision. Progress-ledger edits
  are status, never contract authority.
- If the named item is missing, rebind only when exactly one plan owns it, such
  as the one the named plan's ledger points to, and disclose both paths.

## Evidence Classes

<!-- shared-contract:begin evidence-classes source=shared/vibe-contract.md -->
**Label every load-bearing claim with one of four evidence classes.**

- A claim is load-bearing when it affects scope, feasibility, behavior, verification, risk, order of work, commit authorization, or whether work may proceed.
- `Primary source`: official or upstream documentation, specification, or source code; user-provided source material; a known-good prior implementation.
- `Local investigation`: what this workspace shows — files, configs, schemas, logs, existing tests, non-mutating command output, reproduced behavior.
- `Unproven`: memory, inference, secondhand or unchecked claims, stale documentation, missing access, hypotheses.
- `Accepted risk`: an `Unproven` item the user explicitly chose to proceed on after its impact was explained, or that the bound plan records as accepted.
- Never rename or redefine these classes; a package may add its own disjoint labels or freshness qualifiers in its own text.
<!-- shared-contract:end evidence-classes -->

This phase adds two labels: `Plan` (stated by the bound plan, specification,
acceptance criteria, or task list) and `Local evidence` (verified in the
current workspace by reading code, tests, configs, schemas, or logs, or by
running checks). Implementation may rely only on `Plan`, `Local evidence`,
`Primary source`, and `Accepted risk` as Accepted-Risk Semantics allows. Label
load-bearing claims even in responses that edit nothing.

## Execution Loop

1. **Bind** the plan under Plan Sources; when the plan or instruction touches
   consent-bound work, run the Startup Consent Preflight before the first edit.
2. **Verify before editing.** Inspect the files, tests, configs, and schemas
   the slice touches; re-check the plan facts and capability dependencies it
   relies on; check external APIs and other unstable facts against official
   docs or upstream source. If a required inspection cannot be done, stop at
   that blocker and draft no code or tests for the slice. When evidence
   conflicts with a planned step, run the Plan Validity Gate.
3. **Implement only the current slice**, reusing local conventions and leaving
   future phases, extras, and adjacent cleanup out. A request to add, skip,
   narrow, or replace planned work, including planned tests called redundant,
   is a deviation: run the Plan Deviation Gate before acting on it. Start a
   slice the plan marks atomic (non-green inside, green at its end) only with
   enough session and context runway to reach its verification gate;
   otherwise stop at the preceding verified checkpoint, record the no-start
   decision there, and do not split the slice to fit the session.
4. **Prove it** with the plan's verification and the repository's relevant
   lint, type, and build checks. A metric is evidence only if it separates the
   required result from the known-bad baseline: record the baseline first, and
   if it already passes, stop and correct the proof strategy through the Plan
   Validity Gate. A green broad suite does not complete a slice whose planned
   acceptance check is missing or unrun.

   - Preserve every gate's exit status independently; never let a truncating
     filter carry the gate status or a later successful gate mask a failure.
   - Reconcile every named frozen baseline class as verified now, deferred to
     a named later gate, or a manual-only hole with an owner and residual risk.
     If intentional edits land after an empirical run, rerun the affected
     empirical gate on final bytes or record the exact delta; static reruns
     do not extend empirical proof.

5. **Review** the verified slice under the Post-Implementation Review Gate
   before its summary, the next slice, or any commit.
6. **Close the checkpoint**: update an existing `Implementation progress`
   ledger, then select the unit's commit under Commit Selection. When a defect
   in existing behavior that the plan does not own blocks verification, use
   the Existing-Feature Repair Handoff.
7. **Report** the bound plan, the slice, the verification and its result (suite
   status and acceptance coverage separately; a skipped check with its reason
   and residual risk), the review mode and finding dispositions, deviations or
   blockers, commits made, and the remaining plan steps.

## Commit Selection

<!-- shared-contract:begin commit-selection-state-changing source=shared/vibe-contract.md -->
**Only an explicit user request, a bound plan item, or the workflow's own verified checkpoint selects a commit.**

- Name the source before committing: the current user's request, an approved bound-plan checkpoint, or this workflow's checkpoint default for its own verified unit. With none, do not commit; ask whether a commit is wanted.
- Never treat routing, invocation, edit permission, a convenient stopping point, tracked changes, or an available commit workflow as a source. Commit execution has no checkpoint default of its own.
- Checkpoint default: once a self-contained unit is implemented, verified, reviewed, and its material findings dispositioned, commit exactly that unit locally without waiting for a separate instruction; never let several units pile up uncommitted.
- Select nothing from discovery-only, blocked, unchanged, failing, unverified, or work-in-progress state.
- Stage only the unit: exclude pre-existing changes the workflow did not make, paths outside the unit, and any artifact that would become newly tracked; if the unit cannot be separated from other changes, report the mixed state and ask.
- Route each selected commit through commit execution with its scope, test and review evidence, exclusions, and any proposed message; that workflow owns staging, diff review, message transport, and post-commit verification.
- Before a push, amend, rebase, HEAD-moving reset (soft, mixed, or hard), `filter-*` rewrite, or scripted replay of several commits, get the user's explicit authorization for that operation; a commit request or checkpoint never grants it, and published history is shared.
- Never treat a commit request or checkpoint as consent to release, version changes, tags, stash, squash, destructive cleanup, force-adds, tracking a new artifact, or external side effects; each needs its own.

Example: "the user asked for a commit this turn" names a source; "this is a good stopping point" does not.

Exception: a current no-commit instruction, a bound plan that forbids commits, or project policy suspends the default; leave the verified changes in the working tree and report why.
<!-- shared-contract:end commit-selection-state-changing -->

Close units on the plan's `Commit checkpoints` when it has them; otherwise on
the natural independently verified slice boundaries. When a runtime or user
test of a built/deployed artifact is a checkpoint prerequisite, carry which
artifact was tested and the inputs it was built from into the commit handoff
so a partially staged checkpoint can be matched to them.

## Accepted-Risk Semantics

<!-- shared-contract:begin accepted-risk-semantics source=shared/vibe-contract.md -->
**Only `Accepted risk` lets an `Unproven` item support work that depends on it.**

- Accept only on the human user's explicit choice after the impact was explained, or on the bound plan's recorded acceptance for this request; never on a proxy, delegate, AI-selected default, or a low-risk judgment.
- Record the assumption, who accepted it and why, the impact area, the fastest proof path, and the revisit trigger, tied to the conditional steps it supports; the item stays `Accepted risk`, never verified fact.
- Turn every other `Unproven` item that blocks current work into proof work, a question, or a blocker; defer decisions the current work does not need.
- Never use it for irreversible, destructive, unsafe, illegal, or credential-exposing actions: those need proof, a safer alternative, or the user's explicit human-risk decision.
<!-- shared-contract:end accepted-risk-semantics -->

Record an acceptance given only in conversation in the bound plan before
implementing the slice it supports.

## References

- `references/execution-workflow-and-quality.md` (proof rules,
  Post-Implementation Review Gate, progress ledger): read when
  proving, reviewing, or closing a slice.
- `references/execution-gates-and-delegation.md` (Plan Deviation Gate, Plan
  Validity Gate, Existing-Feature Repair Handoff, Startup Consent Preflight,
  delegation): read before deviating from or correcting the plan, handling a
  defect in existing behavior, crossing a consent boundary, or delegating
  work.
