---
version: 6.0.0
name: vibe-plan-execution
description: Use when the user asks to execute, implement, continue, or apply an existing implementation plan, specification, acceptance criteria, task plan, or prior planning output. Do not use for plan creation or coding requests with no concrete plan to bind.
---

# Vibe Plan Execution

## Overview

Execute an existing implementation plan without inventing missing behavior. Bind
to the plan, verify the facts it depends on, implement the smallest safe current
slice, and stop when reality contradicts the plan.

Questioning a plan is required when its sections conflict or implementation
reveals a defect. The plan is authority for scope and intent, not proof that
every implementation instruction is correct. Deviating from it is not allowed
until verified evidence proves the plan is incorrect, stale, impossible, unsafe,
or already satisfied. Treat "this looks redundant" as a hypothesis, not as
permission to skip planned API, specification, implementation, or test work.
When the defect changes the requirements, acceptance criteria, proof strategy,
or implementation contract, return to the owning requirements or planning
artifact before editing that behavior. Do not turn a stale plan into a series of
one-off patches.

If no concrete plan exists, return to planning before coding. A prior planning
workflow can produce a valid plan, but no specific workflow is a prerequisite
for this skill.

## Effect And Write Boundaries

<!-- shared-contract:class language=chat commit=state-changing effect=state-changing -->
<!-- shared-contract:begin closing source=shared/vibe-contract.md -->
For every consolidation block this package carries, here and in its references: where this package declares a stricter or narrower rule in its own text, that declaration controls.
For every gate and schema block this package carries, here and in its references: this package may state which of its phases the block applies to; it may not change the block's inputs, outcomes, or fields.
<!-- shared-contract:end closing -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
**Write nothing beyond what the phase's own effect class and its declared boundary permit.**

- Declare exactly one effect class for every workflow phase, in that phase's own text.
- In a read-only phase, read and report; make chat the deliverable — findings, alignment, or direction.
- In a read-only phase, edit no source, test, config, doc, or other file, and run no command that mutates runtime or repository state.
- In a read-only phase, never stage, commit, tag, push, change versions, delete data, or start services.
- In a read-only phase, write a file only when the current user explicitly asks for a saved artifact.
- In an artifact-only phase, create or update the artifact it owns: the requirements spec, the plan, the plan-review state, the instruction files, or the text artifacts the request names.
- In an artifact-only phase, write the supporting paths its own text declares:
  - the text it was asked to revise (comments, docstrings, docs);
  - a confirmed reflection into the bound plan;
  - an ignore file it previewed and the user confirmed;
  - a narrowly confirmed configuration edit its text names;
  - a decision record or findings report its own text declares.
- In an artifact-only phase, leave those verified changes in the working tree.
- In an artifact-only phase, never implement executable behavior, never edit application code or tests as implementation, never produce an artifact another phase owns, and never perform release work.
- Never let an artifact-only phase's artifact authorize same-turn implementation.
- In a state-changing phase, edit files and run commands inside the scope its own text declares — the unit it implements, the repair it proves, the fixes it applies, the round it integrates, or the commit it executes.
- In a state-changing phase, keep its edits to the smallest verified unit of that scope.
- In a state-changing phase, leave paths outside the scope, pre-existing working-tree changes the phase did not make, and runtime or external state beyond the scope unwritten unless the current user selects them.
- Keep every irreversible or outward-facing operation under its own consent.
<!-- shared-contract:end effect-write-boundaries -->

The scope this phase declares is the current slice the bound plan authorizes,
implemented as the smallest coherent unit of that slice that can be tested,
plus the decision records and findings reports named under `Durable Records`.

## Durable Records

Before recording a settled decision, deferring a finding, closing a unit, or
starting this phase, read `references/durable-records.md`. This phase writes
`docs/decisions/` and `docs/reports/findings/`, or the repository's existing
record directory, as declared supporting paths.

## Commit Selection

<!-- shared-contract:begin commit-selection-state-changing source=shared/vibe-contract.md -->
**Only an explicit user request, a bound plan item, or a workflow's own verified checkpoint selects a commit.**

- Select a commit from exactly three sources: an explicit current-user request; a bound approved plan item requiring that checkpoint; or a state-changing workflow closing its own verified, reviewed, in-scope unit under its checkpoint default.
- Never let routing or invocation, edit permission, a convenient stopping point, tracked changes in the working tree, or an available commit-execution workflow select a commit.
- Never treat an unverified unit as a handoff.
- Execute in commit-execution only the commits those sources select; that phase has no checkpoint default of its own.
- Close a self-contained unit of the workflow's own work with a local commit of exactly that unit once it is implemented, verified, reviewed, and its material findings dispositioned.
- Commit that unit without waiting for a separate commit instruction.
- Never let a multi-unit run accumulate as one undifferentiated working tree.
- When the default is suspended, leave the verified changes in the working tree and report the reason.
- Let the checkpoint default reach only local commits of the unit's own verified changes.
- Select no commit from discovery-only, blocked, unchanged, failing, unverified, or work-in-progress state.
- Never widen the staged set beyond the verified unit.
- Exclude pre-existing working-tree changes the workflow did not make, an artifact whose tracked status would itself be new, and paths outside the unit.
- Never treat an available commit-execution workflow or ambient tracked status as a reason to include them.
- When the unit's changes cannot be separated from unrelated working-tree state, report the mixed state and ask instead of committing.
- Route every selected commit through the commit-execution workflow with the verified scope, its test and review evidence, its unrelated-path exclusions, and any proposed message.
- Leave staging, file-set and exact-diff review, message transport, history safety, and post-commit verification to that workflow.
- Never read a request to commit as a request to push.
- Keep push, release preparation, version changes, tags, amend, rebase, reset, stash, squash, destructive actions including cleanup, force-adds, tracking a newly created artifact, external side effects, and unrelated or ambiguous paths separately consent-bound even when a checkpoint was selected.
- Never let a route, checkpoint, or handoff implicitly authorize them.

Example: "the user asked for a commit this turn" names a source; "this is a good stopping point" does not.

Exception: a current no-commit instruction, a bound plan that forbids commits, or project policy against commits suspends the checkpoint default.
<!-- shared-contract:end commit-selection-state-changing -->

The unit this workflow closes is a verified, reviewed execution unit of the
bound plan; this phase hands it to the commit-execution workflow and neither
stages nor commits itself. Use plan-authored `Commit checkpoints` when they
exist; otherwise close on the natural independently verified slice boundaries.

If the host or harness requires separate confirmation for local commits,
ask once at startup before the first edit that can produce tracked changes, not
again at each checkpoint. That startup confirmation is in addition to the gate's
per-commit ask and never replaces it.

### Commit-Selection Gate

<!-- shared-contract:begin commit-selection-gate source=shared/vibe-contract.md -->
**Never run a plain `git commit` without naming the selection source it rests on.**

- With no user-installed hook enforcing this gate, this wording is the whole gate: apply it yourself before the command runs.
- Name one recorded source before committing: the current user's request (`user-turn`), the bound plan item (`bound-plan-item`), or the workflow's own checkpoint of a verified unit (`specialist-checkpoint`).
- Treat `agent-proposed` as a recorded proposal, never a selection.
- When the workflow is router-bound, have the router record that source as a `commit-selection` event before the command runs.
- For a standalone commit with no router active, name the direct current-user request or the verified checkpoint handoff and follow the phase's ordinary confirmation policy.
- When no source can be named, do not commit; ask the user whether a commit is wanted.
- Return `allow` when the command is not a commit.
- Return `ask` on every plain commit, quoting from the session record under `.plans/vibe-sessions/` the recorded `phase` and the most recent recorded `commit-selection` event's `source`, `at`, and `note`.
- Or state that no `commit-selection` event is recorded, or that the record is absent, malformed, stale, foreign, session-unbound, or conflicting.
- Never return `deny` from this gate.
- Never allow a plain commit silently: surface the recorded `source` at the prompt so a self-attested selection is caught there.
- Answer `ask`, never `deny`, for a record in any invalid state.

Exception: an amend or other history rewrite belongs to the history-mutation gate, not this one.
<!-- shared-contract:end commit-selection-gate -->

This gate applies to the plan-execution phase's checkpoint commit.

## Plan Sources

This skill executes any concrete bound implementation plan. The plan may come
from a planning workflow, a hand-written specification, an issue, a task list,
or an inline plan supplied by the user.

Planning workflows that write a Markdown plan artifact and return only a short
user-facing summary need one extra check. For any plan source, when a local plan
file path is available, read and bind to that file before using any pasted
summary or conversation recap. When the plan has these sections, read them
directly:

- `Goal`, `Requirements`, and `Acceptance criteria` define the behavior
  contract for the current slice.
- `Verified facts and sources` is reusable plan evidence. Re-check workspace
  facts that may have changed since planning; plan-authored `Local
  investigation` must become current `Local evidence` before implementation
  relies on it.
- `Test plan` defines the first verification path unless local evidence shows it
  is stale or insufficient.
- `Capability dependencies`, when present, names exceptional capabilities whose
  absence materially changes feasibility, safety, proof strength, or method.
  Re-check availability and use the recorded fallback or blocker.
- `Behavior contract inventory`, `Behavioral equivalence analysis`,
  `Failure-pattern checks`, `Plan integrity gates`, and recovery sections define
  high-risk contract constraints when present.
- `Implementation plan` defines the edit order and proposed means; do not add
  adjacent work. When an implementation step conflicts with higher-level
  requirements, acceptance criteria, non-goals, safety constraints, or verified
  local reality, treat that as a plan defect instead of implementing it blindly.
- `Implementation progress`, when present, is an intentional durable resume
  ledger. Read and verify it before choosing the current item. Its absence is
  normal for same-session work and does not authorize creating one.
- `Risks and unproven items` and `Proceed condition` decide whether coding
  starts, stays conditional, or returns to planning.

When the current task is an execution/deviation decision rather than editing,
name the bound plan and the material sections that control the decision. Keep
the affected existing-behavior or lifecycle dimensions, current out-of-scope
items, and explicitly non-selected checks visible when omitting them could make
the proposed shortcut look authorized.

When the user explicitly asks for a response-only analysis of supplied plan
and repository state and forbids mutating this checkout, evaluate that
represented state under this execution phase's normal obligations: describe the
applicable edits, verification, records, findings entries, index rows, and
checkpoint decision or handoff without performing any mutation or claiming that
a described action occurred, and describe the artifacts this phase would itself
write rather than substituting carry-forward packets merely because delivery is
response-only. This changes delivery only; during actual execution a
description satisfies no required write or verification.

If the bound plan says implementation is blocked, do not start coding. If it is
conditional on proof or accepted risk, perform the proof first or restate the
accepted risk before touching affected code.

Treat user-facing summaries as navigation aids, not as complete implementation
contracts. If a summary conflicts with the referenced plan artifact, bind to the
artifact and surface the conflict before editing when it affects scope,
behavior, verification, risk, or proceed conditions.

Before reporting completion, make the binding visible: name the authoritative
plan path and the current slice, then summarize the acceptance and verification
gates that controlled the kept changes. A final reply that only lists edited
files and behavior is not proof that the referenced artifact was read or that
summary-only scope additions were rejected.

Bind the selected plan path and re-read its current content before choosing an
item. Existing commit, revision, or host evidence may help identify the reviewed
state when already available, but execution does not require plan-maintained
hashes. Compare current authority-bearing requirements, acceptance criteria,
scope, risks, tests, and steps with the reviewed contract. Unclear semantic drift
blocks and returns to plan revision; an intentional progress-only update or
harmless formatting change does not require identity reconciliation.

If a referenced plan lacks the referenced item, search bounded candidate plans.
Rebind only when exactly one owns the item and the referenced artifact's ledger
points forward to it; disclose both paths. Otherwise stop for authority.

Complete only a plan-authored reserved decision field. Record date, authority,
evidence, decision owner, response carrier, owning revision, and proceed update;
never change scope, criteria, tests, risks, or steps through that field. Batch
only simultaneously knowable startup decisions. A completed reserved-decision
answer or a dated superseding decision that binds later units is also written as
a decision record and cited from the plan.

A current user instruction may itself be the response carrier when it explicitly
names the resource, permission, or choice reserved by that decision. Quote the
instruction verbatim, record the coordinator's interpretation and its exact
scope, and keep any inference beyond the named subject blocked.

If faithful execution proves a recorded human-selected mechanism unavailable,
unsafe, or contradictory, return to that decision owner with evidence and
bounded alternatives. Do not silently substitute or erase it; record a dated
superseding decision through the owning artifact revision.

## Concrete Plan Requirements

A plan is concrete enough to execute only when the current slice has:

- A goal and user-visible outcome.
- In-scope and out-of-scope behavior.
- Acceptance criteria or equivalent pass/fail checks.
- A test, proof, or manual verification path.
- Implementation steps or a named code area to inspect first.
- Open risks, unproven items, or a statement that none are known.

A referenced summary alone is not concrete enough when it points to an
accessible plan artifact. Read the artifact first. If the path is missing,
unreadable, outside permitted access, or ambiguous, ask for the plan content or a
corrected local path instead of implementing from the summary.

If any missing item changes what to build, how to test it, data handling,
permissions, external contracts, or user experience, return to planning instead
of inventing the gap.

When execution stops because the target source or proof surface is absent, keep
the bound plan intact. Report the current plan item, the exact missing local
evidence, the verification or review that could not run, the evidence-backed
progress status, any current no-commit instruction, and the path or artifact
needed to resume. Do not rewrite requirements, acceptance criteria, or plan
steps merely to create a progress artifact.

When a current instruction says `Do not commit`, preserve that exact reason in
the execution summary and, when an intentional progress ledger exists, in its
commit-action field. Do not replace it with `No commit requested`, missing
verification, or another inferred reason.

## When Not to Use

Do not use this skill for:

- Creating the initial plan, specification, acceptance criteria, or test plan.
- Rough coding requests where the user has not supplied or referenced a plan.
- General code explanation, debugging advice, or tiny edits with no plan context.
- Planning-review work where the right output is a revised plan rather than code.

## Core Rules

- Identify the implementation plan before editing files. If the user references
  a local plan file path, read it before editing. If multiple plans could apply,
  ask the user which one is authoritative.
- Treat the user's words as intent, not verified fact. Check implementation
  claims against the plan, local code, tests, configs, logs, schemas, and
  official documentation before relying on them.
- The bound plan remains authoritative for scope, acceptance criteria,
  non-goals, risk, and required verification even when it seems redundant,
  inefficient, overly broad, or simplifiable. It is not a shield for known-bad
  implementation details. Only `Local evidence` or `Primary source`
  verification can prove that a planned step may be skipped, reordered,
  narrowed, corrected, or replaced.
- Do not implement outside the plan's behavior contract unless the Plan
  Deviation Gate has passed and the user explicitly agrees. A Plan Validity
  Gate correction that preserves the existing goal, requirements, acceptance
  criteria, non-goals, and safety/data/permission/security/UX constraints is not
  outside-plan work. When an unplanned change appears necessary, explain the
  reason, impact, and closest plan-preserving alternative first.
- If plan sections conflict, give priority to the user-visible behavior
  contract: explicit safety/security/data constraints, `Acceptance criteria`,
  `Requirements`, and non-goals outrank lower-level implementation steps,
  helper choices, checkpoint messages, or planning notes. Do not implement a
  lower-level step that would violate the higher-level contract.
- Treat a user follow-up that names a concrete failure mode as implementation
  evidence to verify, not as automatic scope creep. Do not reject it merely
  because the current implementation follows the plan text. Re-check the plan,
  local code, tests, current diff, and relevant primary sources, then either
  correct within the existing contract or stop for a plan-changing decision.
- Do not treat a plan's status-quo or out-of-scope statement as proof that a
  locally surprising existing behavior should be preserved. If implementation
  relies on a workaround for that behavior, or current evidence shows it
  conflicts with the higher-level behavior contract, run the Plan Validity Gate
  instead of finishing the workaround because the plan scoped the behavior out.
- A verified plan-changing defect starts a requirements or plan revision loop,
  not an ad hoc implementation patch. Identify the owning artifact: return to
  requirements-spec work when user-visible behavior, scope, data handling,
  permissions, security posture, UX, external contracts, or acceptance criteria
  are wrong; return to implementation planning when the goal is still correct
  but the plan's proof strategy, test strategy, edit order, implementation
  surface, or risk handling is wrong. Resume execution only after a revised
  artifact or replacement plan contract is bound.
- A Plan Validity stop is visible in the handoff: name the conflicting `Plan`
  claim, the `Local evidence` or `Primary source` that contradicts it, the
  contract surfaces affected, the owning artifact to revise, and the condition
  for rebinding execution. Do not silently rewrite the plan and report only the
  corrected conclusion.
- Each verified, reviewed, self-contained unit closes under the checkpoint
  default in the Commit Selection section; staging, message transport,
  trailers, and stored-commit inspection stay with the commit-execution
  workflow.
- An acceptance metric is executable proof only after current `Local evidence`
  shows it distinguishes the before state from the required after state. A
  known-bad baseline that already passes the metric blocks completion and
  returns to the plan's proof strategy.
- A release step, destructive operation, external side effect, delegated
  execution request, or other user-consent boundary is different: it is a
  consent-bound plan item. If exact authorization is missing, run the Startup
  Consent Preflight before editing the affected slice. Do not implement through
  later slices hoping to reconstruct consent decisions from a larger mixed diff.
- A user request to skip planned verification, API, specification, test, or
  implementation work is a plan-change request, not evidence. Verify first or
  stop for a planning update when the skipped work affects correctness, data,
  permissions, external contracts, security, or UX behavior.
- Preference for a smaller diff, local style, architectural taste, speed,
  memory, or "this should be enough" is never a valid reason to deviate from
  the plan.
- Do not silently "fix" an incorrect or impossible plan. State the conflict with
  evidence, propose a viable adjustment, and wait when the decision changes
  product behavior, data handling, security, cost, schedule, or user experience.
- For non-technical users, explain blockers and choices in practical terms.
  Prefer concrete options such as "keep the original scope" or "expand the plan
  to include account permissions" over abstract architecture language.
- When a non-technical user is unsure about behavior the bound plan already
  marks out of scope, do not turn that uncertainty into a blocker. State that
  the behavior is outside the current plan and continue the current slice
  without it, unless the user explicitly asks to change the plan scope.
- Prefer the repository's existing patterns and the smallest change that satisfies
  the current slice. Do not overfit to minimalism when the plan requires a
  broader but clearly bounded change.
- Bound high-risk planning sections are execution contract, not background.
  Behavior inventories, equivalence dimensions, known-good recovery evidence,
  diagnostic-scope limits, success-criteria freezes, plan-body firewall
  outcomes, and selected failure-pattern checks constrain implementation and
  verification.
- A current-slice implementation assumption the bound plan leaves `Unproven`
  lets that slice proceed only under the Accepted-Risk Semantics section.
- When the bound plan intentionally includes `Implementation progress`, update
  only that section with evidence-backed status when safe and when no
  unrecorded qualifying decision remains. Do not edit scope,
  requirements, acceptance criteria, tests, risks, or steps as a status update.
  When the section is absent, keep progress in the execution summary unless
  cross-session/cross-actor resumability or an explicit user/project request
  requires returning to planning to add durable progress state.
- A progress update is evidence-backed status, not proof by itself. Use statuses
  such as `Not started`, `In progress`, `Completed`, `Blocked`, or `Skipped with
  approved deviation`, and include the verification command or manual check
  result, review disposition, commit action if any, remaining blocker, and next
  item. Do not mark an item `Completed` when verification was skipped, failing,
  unavailable, only self-reported by delegated output, or when any core acceptance sentinel from the bound plan is missing, failed, stale, or unmapped even though the broader suite is green.

## Evidence Classes

<!-- shared-contract:begin evidence-classes source=shared/vibe-contract.md -->
**Label every load-bearing claim with one of the four shared base evidence classes.**

- Label a claim with its class wherever it is load-bearing: where it affects scope, feasibility, behavior, verification, risk, implementation order, commit authorization, or whether work may proceed.
- `Primary source`: official documentation, an authoritative specification, upstream source, vendor documentation, user-provided source material, or a known-good historical implementation.
- `Local investigation`: repository inspection, non-mutating command output, reproduced behavior, or existing tests, configs, schemas, and logs read in the current workspace.
- `Unproven`: memory, inference, secondhand claims or summaries, stale documentation, unchecked user claims, training-data recall, missing access, or hypotheses.
- `Accepted risk`: an `Unproven` item the user explicitly chose to proceed with after its impact was explained, or that the bound plan already records as accepted for the active request, with its impact and revisit trigger preserved.
- Extend this set only by a package's declaration, in its own text, of a disjoint extension or a freshness qualifier.
- Never let such a declaration rename or redefine a base class.
- Read an execution phase's `Plan` class as authority by binding to the bound plan, and its `Local evidence` label as an execution-freshness label; neither is a rename or a redefinition of a base class.
<!-- shared-contract:end evidence-classes -->

The two labels below are this phase's own:

- `Plan`: stated by the bound implementation plan, specification, acceptance
  criteria, or task list.
- `Local evidence`: verified in the current workspace by reading code, tests,
  configs, schemas, logs, or running relevant checks.

Use all six labels internally and in user-facing blockers, questions, plan
deviation notices, commit-checkpoint decisions, and execution summaries when
provenance affects scope, behavior, verification, risk, commit authorization,
or whether implementation may proceed. Label the load-bearing claims; do not
list unused classes merely to satisfy a template.

Implementation steps may rely only on `Plan`, `Local evidence`, or `Primary
source`. `Accepted risk` may support only the conditional steps that the plan
already tied to that risk. Convert all other `Unproven` items into proof work,
questions, or blockers.

When execution writes verified facts back into a planning-owned artifact, keep
that artifact's `Local investigation` label and add the verification date and
source. Use `Local evidence` for execution receipts, summaries, blockers, and
current-session decisions; do not introduce a second taxonomy into the plan.

Do not omit evidence labels only because no files were edited. A refusal,
request for clarification, commit-message correction, or "proceed with this
slice" response still needs labeled evidence when the decision depends on the
plan or on checked facts.

## Accepted-Risk Semantics

<!-- shared-contract:begin accepted-risk-semantics source=shared/vibe-contract.md -->
**Only `Accepted risk` lets an `Unproven` item support work that depends on it.**

- Label an item `Accepted risk` only on the human user's explicit choice to proceed after its impact was explained, or on the bound plan's already-recorded acceptance for the active request.
- Never let a proxy decision, an AI-selected default, or a risk judged low make the acceptance.
- Record the exact assumption, who accepted it and why, the impact area (feasibility, behavior, data, integration, performance, security, UX, cost, or schedule), the fastest proof path, and the revisit trigger.
- Tie the acceptance to the conditional step, deferred decision, or follow-up it affects.
- Keep the label `Accepted risk`; never convert the item into verified fact.
- Support only the conditional steps already tied to the accepted risk, and keep those steps conditional wherever the assumption could invalidate them.
- Turn every other `Unproven` item that blocks the current work into proof work, a question, or a blocker.
- Never let risk level by itself clear such a blocker.
- Defer decisions the bounded current work does not need rather than letting them block it.
- Never use accepted risk for irreversible, destructive, unsafe, illegal, or credential-exposing actions; those require proof or a safer alternative.
- Record a human deliberately selecting a known destructive action as a human-risk decision.
- Never let accepted risk stand in for that decision or excuse an unproven safety or legality premise.
<!-- shared-contract:end accepted-risk-semantics -->

Here the acceptance must be recorded in the bound plan itself before the
affected slice is implemented; an acceptance given only in conversation is
written into the plan first.

## Execution Gates And Delegation Reference

Before deviating from a bound plan, correcting a plan defect, crossing a consent
boundary, or delegating execution or review work, read
`references/execution-gates-and-delegation.md`. That reference owns the Plan
Deviation Gate, Plan Validity Gate, Existing-Feature Repair Handoff, Startup
Consent Preflight, human-risk decisions, Delegated Execution Support, and
delegated-result proof rules.

## Execution Workflow, Review, And Quality Reference

Before executing a bound plan slice, launching post-implementation review,
updating an applicable resumable-progress ledger, communicating completion or
blockers, or applying final quality checks, read
`references/execution-workflow-and-quality.md`. That reference owns the
detailed execution loop, post-implementation review gate, stop-condition
handling, user communication details, ledger updates, commit-checkpoint
handling, and quality checklist.
