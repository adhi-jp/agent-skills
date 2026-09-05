# Route Selection Reference

Read this reference when the decision table's cells in `SKILL.md` do not settle
the classification: two rows could accept the instruction, an exclusion needs
its tie-break, or a row's fallback behavior is in play. It owns the precedence
order in detail and each row's triggers and exclusions; handling between routes
is in `phase-boundaries.md`.

## Precedence

Select exactly one primary row for the current turn. Choose the immediate next
required phase, not the eventual end goal. The order is the mapping list in
`SKILL.md`: items 1–14 in that order, with the router-owned rows
`direct-implementation` and then `maintenance` classified between item 12
(implementation planning) and item 13 (requirements specification), and always
before item 14, the `no matching specialist` fallback. The goal-alignment gate
precedes every item; an instruction that fires it is classified only after the
confirmation is recorded.

Tie-breaks the order alone does not decide:

- A reported symptom or repair request outranks investigation, planning,
  creative exploration, and execution of a plan the request only mentions; a
  plan file named in a repair request is evidence, not execution authority.
- An active artifact is continued only when the instruction continues or
  revises it. A new goal, or an explicitly different deliverable, is
  `replace workflow` or a fresh row, not a continuation.
- Implementation planning versus `direct-implementation`: a request that names
  a plan, supplies a specification, acceptance criteria, or task list, touches
  more than one surface, or leaves acceptance or verification neither stated
  nor obvious is planning. A single-surface edit whose acceptance and
  verification are stated or obvious is direct implementation. The user saying
  that no plan is wanted does not turn vague or multi-surface work into a
  direct edit; it stays planning or requirements work.
- `direct-implementation` versus `maintenance`: a behavior change the user
  names as the deliverable is direct implementation; an edit whose purpose is
  dependencies, the build, tests only, release preparation, or repository
  housekeeping with no behavior change is maintenance. When both could apply,
  direct implementation is classified first.
- `maintenance` versus `debug-and-repair`: a reported defect, failing
  behavior, or regression is repair even when the fix turns out to be a
  dependency or build change; a build or tool that fails with no reported
  behavior defect is maintenance.
- Commit execution versus `writing`: a commit request that also needs message
  wording is commit execution with writing as auxiliary; message wording alone,
  with no history action, is writing.
- Review versus the walkthrough: a saved plan artifact examined item by item
  with the user is the walkthrough; the same plan as a git-backed diff, branch,
  or base-ref target is review.
- The terminal fallback is reached only after every row, the router-owned rows
  included, was refused.

## Requirements Specification

During the requirements-specification phase, do not treat "looks good",
"ready", "continue", "go ahead", completed checklists, or similar wording as
approval unless it clearly approves the current spec artifact.

After the phase records explicit approval evidence, or an unambiguous
instruction to create or use an implementation plan from the current spec
provides that evidence, preserve its stop-after-spec boundary: no
implementation plan is created inside the requirements specialist's response.
If the current instruction only approves or finishes requirements, stop the
outer response after the requirements summary and record that the next related
instruction routes to `implementation-planning`. A same-instruction
continuation to planning is described in `phase-boundaries.md`.

## Creative Direction Exploration

A confirmed direction from this phase is input to later requirements or
planning work, not implementation scope. A trusted orchestration proxy selection
from that specialist is also input only; the receiving phase must record it as
AI-selected direction, not as explicit human-user confirmation. When the user
asks to capture the chosen direction durably, route the next related instruction
to `requirements-specification`.

## Code Investigation

A reported symptom or repair request outranks investigation and routes to
`debug-and-repair`. Investigation findings are evidence for later phases; they
do not authorize edits.

## Implementation Planning

Route to this row when a requirements spec has explicit approval evidence or a
legacy `Approved` state and the next related instruction asks to move forward;
when the user supplies a specification, acceptance criteria, task list, or
rough request that needs a plan before execution; or when the user clearly asks
to create or revise an implementation plan.

When the next step could be either plan revision or plan execution, ask whether
the user wants to revise the plan or start execution. A same-instruction
continuation from planning to execution is described in
`phase-boundaries.md`.

## Plan Execution

Route to this row only when all of these are true: the user clearly asks to
execute, implement, apply, or continue execution of a known plan or current
slice; a concrete bound implementation plan is available under the execution
specialist's concrete-plan requirements; and the plan's `Proceed condition` is
ready, or the plan's accepted-risk condition is satisfied for the requested
slice. Bare post-planning handoff wording such as "continue", "go ahead",
"ready", or "looks good" is insufficient unless it clearly asks to execute the
known plan or current slice and the proceed condition allows execution.

Plan execution prepares and verifies each checkpoint, then routes the history
action to the visible commit-execution specialist without requiring a second
generic "commit" instruction — whether the checkpoint came from a plan-authored
`Commit checkpoints` item or from the specialist closing a natural verified
slice under its own checkpoint default. Standalone commit requests and
specialist checkpoints alike remain subject to the commit workflow's file-set,
verification, message, and history-safety gates, and none of them widens the
scope past the closing unit's own verified changes.

When the bound plan has a durable implementation-progress ledger, keep that
ledger inside the plan-execution phase. Use it to rebind the active execution
slice after interruptions, compaction, or later related turns, and update
routing state from the ledger status reported by the plan-execution phase. Do
not treat progress-ledger text as a new plan, a separate commit route, or proof
that a slice is complete until the execution specialist has verified the status
under its plan-binding rules. The ledger lives in the plan and is the
specialist's; the session record carries only the routing fields.

## Debug And Repair

This row is for existing-feature behavior and repair proof, not for continuing
execution against a bound plan after the plan contract itself is reported
wrong; those turns use the backtracking rule in `phase-boundaries.md`. The
repair route asks no startup commit question: a proven repair closes under the
checkpoint default, and a diagnosis with no fix commits nothing.

## Review

Excluding a finding, proposed repair, target path, package, or subsystem does
not exclude the review workflow itself unless the user explicitly excludes that
workflow. Keep the excluded surface non-editable and outside selectable fixes
while review triage continues under the specialist's ordinary availability,
consent, stop, and write boundaries. Leaving the review phase for another owner
is described in `phase-boundaries.md`.

## Plan Pre-Check Walkthrough

Keep neighboring boundaries intact: reviewing a plan change as a git-backed
diff, branch, or base-ref target stays in `review`; revising plan content from
new requirements or evidence stays in `implementation-planning`; executing the
plan stays in `plan-execution`. This phase has no proxy-decision branch. Under
unattended orchestration or delegated transport, report the interactive
requirement and stop rather than emulating item decisions, batching approvals,
or recording AI-selected item dispositions.

## Commit Execution

When a commit-execution turn needs message wording and `vibe-writing` is
verified visible, `vibe-writing` and
`skills/vibe-writing/references/commit-messages.md` are auxiliary authority for
the message artifact only: subject wording, body value, verification wording,
durable references, trailers as content, and multi-line transport shape.
History authority stays with the commit-execution phase, project rules, and
explicit user consent.

When no commit-execution specialist is visible but a `vibe-coding` turn
prepares or inspects a commit message, use verified visible `vibe-writing` as
mandatory auxiliary guidance for the message artifact, and keep history
authority with the applicable commit workflow, project rules, and explicit user
consent. If neither specialist is visible, state the fallback when that affects
user expectations and use repository commit rules, recent local history, and
supplied checkpoint messages. A skill that offers only a commit command
capability may take part in that fallback operation; it is never the primary
route. When the user chooses to proceed without the commit specialist, the
router records the `commit-selection` event with its source and runs the commit
under the commit-selection gate's wording and the fallback's own file-set,
message, and post-commit checks.

This explicit `vibe-writing` dependency is an orchestration-only exception for
`vibe-coding`. It does not authorize standalone `vibe-*` specialists to require
or name companion skills in their own contracts.

## Writing

Progress updates, final summaries, and commit-message checkpoints inside another
primary phase may use writing guidance only as auxiliary help when the primary
phase allows it.

Do not route a non-deliverable wording check to the writing phase only because
it concerns words. If the user asks for a direct judgment about a name, label,
identifier, or short phrase and explicitly excludes workflow surfaces such as
editing, review, planning, debugging, or written deliverables, handle it as
ordinary behavior or `no matching specialist`; do not create active routing
state for that request.

## Direct Implementation

The router performs this row itself. Establish the surface, the acceptance, and
the verification from the request or from local evidence before editing; when
the surface is clear but acceptance or verification is neither stated nor
obvious, ask that one question rather than reclassifying, unless the answer
would open more than one surface, in which case the work is planning. Make the
smallest change that satisfies the stated acceptance, run the stated or obvious
verification, and report the result. No requirements spec or implementation
plan is created for this row, and no `matched-but-unavailable` report is made
for it. If the edit reveals a defect in existing behavior, a second surface, or
an unsettled acceptance, stop, report it, and reclassify the next turn to the
row that owns it.

## Maintenance

The router performs this row itself under the repository's own policy: a
dependency update includes its lockfile and the verification that proves the
tree still builds and tests; a build repair without a reported defect fixes the
build and nothing else; a test-only edit changes tests and their fixtures only;
release preparation happens only on the user's explicit request and each
release, version, tag, or push action inside it stays separately consent-bound;
a chore stays within the paths the request names. Reader-visible coupling the
repository requires (a changelog or README line, for example) is part of the
unit. If a maintenance edit reveals a defect in existing behavior, the next
turn is `debug-and-repair`.

## Workflow Control

The router performs this row itself. `cancel workflow` clears live routing
state and tombstones the record; `replace workflow` does the same and starts a
new workflow id for the new goal; an explicit invocation of another top-level
skill or mode for an unrelated task, or a selected specialist reaching its
finish gate with no further related instruction, ends or suspends
`vibe-coding` mode. A stale-context clarification asks one question and routes
nothing until it is answered. An `unrelated ordinary request` is handled as
ordinary behavior with no routing state created or retained for it. The
`no matching specialist` fallback continues with ordinary behavior, states that
no matching optional specialist was verified when that affects user
expectations, and likewise creates or retains no active routing state for an
unrelated ordinary request only because `vibe-coding` was invoked.
