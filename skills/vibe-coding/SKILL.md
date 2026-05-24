---
name: vibe-coding
description: >
  Use when the user explicitly invokes vibe-coding through a host-specific skill
  command, host-provided invocation signal, or direct instruction such as
  "use `vibe-coding`" for a coding workflow.
---

# Vibe Coding

## Overview

`vibe-coding` is the top-level orchestration entry point for multi-turn
vibe-coding workflows. It selects the immediate downstream `vibe-*` phase for
the user's current instruction while preserving each specialist skill's own
write boundary, approval gate, stop condition, and verification rules.

This skill routes work; it does not replace specialist skills and does not
authorize host command plumbing, release preparation, commits, generated eval
workspaces, or implementation outside a selected downstream phase.

## Activation

Activate this skill only when the current turn has one of these signals:

- An explicit host-specific skill invocation for `vibe-coding`, such as Claude
  `/vibe-coding` or Codex `$vibe-coding`. These are representative examples,
  not an exhaustive list of valid AI-agent syntaxes.
- A host-provided invocation signal that says `vibe-coding` is active.
- An explicit instruction such as "use `vibe-coding`".

Do not activate when the user merely mentions "vibe coding" as a style,
repository label, quoted text, background concept, or example.

If activation lacks a concrete coding instruction, ask for the instruction and
do not select a downstream skill yet. Keep this clarification narrow: do not
present a route menu, availability diagnosis, or specialist boundary summary
before the user provides enough intent to classify the immediate phase.

## Routing State

Use conversation state and existing artifact paths as the routing-state
mechanism for this implementation. Do not require a separate persisted ledger
file.

Track these fields when they are known:

- Current goal.
- Current phase.
- Next route.
- Active artifact paths.
- Approval state.
- Implementation plan path.
- Active execution slice.
- Debug symptom.
- Review target.
- Writing artifact.
- Pending approvals.
- Known blockers.

For later related turns, classify the user request before routing:

- `continue current workflow`
- `revise current artifact`
- `replace workflow`
- `cancel workflow`
- `unrelated ordinary request`

If stale context would change behavior and the class is unclear, ask one
clarifying question before routing. If context was lost after compaction or a
long interruption, rebind from the latest known artifact path when possible; if
that is not possible, ask for the missing artifact or decision.

On cancellation or replacement, clear the active phase, next route, pending
approvals, active slice, and live artifact bindings. Preserve completed artifact
paths only as historical context.

End or suspend `vibe-coding` mode when the user explicitly cancels it,
explicitly replaces the workflow with a different goal, explicitly invokes
another top-level skill or mode for an unrelated task, or the selected
downstream skill reaches its finish gate and the user gives no further related
instruction.

## Availability Gate

Before naming a downstream skill route, verify visible metadata for that skill
in the current environment, user-provided material, repository metadata, or
project instructions. The first supported route set is the visible `vibe-*`
family at implementation time:

- `vibe-requirements-spec`
- `vibe-planning`
- `vibe-plan-execution`
- `vibe-debug-fix`
- `vibe-review`
- `vibe-writing`

Treat this list as current local evidence, not a permanent host guarantee.
Future or unavailable skills need visible metadata before they can be named as
routes.

If the immediate phase matches a specialist that is not visible, report
`matched-but-unavailable`, name the unavailable route, name the availability
source checked, and preserve the phase boundary. Do not silently emulate the
missing skill. If the missing route affects risk, artifacts, downstream
boundaries, or user expectations, ask whether to proceed without that specialist.

If no specialist `vibe-*` skill matches the immediate task, continue with
ordinary behavior. State that no matching optional specialist was verified when
that affects user expectations. Do not create or retain active routing state for
an unrelated ordinary request only because `vibe-coding` was invoked.

## Route Selection

Select exactly one primary downstream `vibe-*` phase for the current turn when a
specialist route matches. Choose the immediate next required phase, not the
eventual end goal.

Apply this precedence order:

1. Lifecycle commands and unrelated top-level invocations.
2. Stale-context clarification before routing.
3. Active artifact continuation or revision.
4. Review targets and review/fix loops.
5. Bug reports, regressions, failed fixes, tool failures, runtime artifact
   mismatches, and existing-feature repair.
6. Wording-only deliverables with no review target or Definition-of-Done triage.
7. Clear execution requests for concrete implementation plans.
8. Implementation planning for approved specs or inputs that are insufficient
   for plan execution.
9. Requirements specification for new vague, rough, contradictory, creative,
   non-technical, or underspecified coding goals.
10. `no matching specialist` fallback.

### Requirements Specification

Route new vague, rough, contradictory, creative, non-technical, or
underspecified coding goals to `vibe-requirements-spec`.

During the requirements-spec phase, do not treat "looks good", "ready",
"continue", "go ahead", completed checklists, or similar wording as approval
unless it clearly approves the current spec artifact.

After `vibe-requirements-spec` records explicit approval, preserve its current
stop-after-approval boundary. Stop in that turn and record that the next related
user instruction routes to `vibe-planning`.

### Implementation Planning

Route to `vibe-planning` when:

- A requirements spec is approved and the next related instruction asks to move
  forward.
- The user supplies a specification, acceptance criteria, task list, or rough
  request that is not concrete enough for `vibe-plan-execution`.
- The user clearly asks to create or revise an implementation plan.

When the next step could be either plan revision or plan execution, ask whether
the user wants to revise the plan or start execution.

### Plan Execution

Route to `vibe-plan-execution` only when all of these are true:

- The user clearly asks to execute, implement, apply, or continue execution of
  a known plan or current slice.
- A concrete bound implementation plan is available under
  `vibe-plan-execution`'s concrete-plan requirements.
- The plan's `Proceed condition` is ready, or the plan's accepted-risk condition
  is satisfied for the requested slice.

Bare post-planning handoff wording such as "continue", "go ahead", "ready", or
"looks good" is insufficient unless it clearly asks to execute the known plan or
current slice and the proceed condition allows execution.

### Debug, Review, And Writing

Route bug reports, regressions, failed prior fixes, repeated "still broken"
feedback, rough repair requests, tool failures, and runtime artifact mismatches
to `vibe-debug-fix`.

Route review targets and review/fix loops to `vibe-review`, including requests
to review a diff, working tree, branch, base ref, implementation plan, document
change, findings, scope, Definition of Done alignment, or gated fixes.

Route wording, message content, localization, or text-format deliverables to
`vibe-writing` when there is no review target, Definition-of-Done triage, or
fix loop. Progress updates, final summaries, and commit-message checkpoints
inside another primary phase may use writing guidance only as auxiliary help
when the primary phase allows it.

## Boundary Rules

Downstream specialist boundaries are authoritative:

- `vibe-requirements-spec` writes or updates only the current requirements spec
  artifact and stops after approval.
- `vibe-planning` writes implementation-plan artifacts only and does not
  authorize same-turn implementation.
- `vibe-plan-execution` requires a concrete bound plan and its proceed or
  accepted-risk condition before code execution.
- `vibe-debug-fix` owns existing-feature diagnosis and repair proof.
- `vibe-review` owns review target selection, delegated review coordination,
  scope triage, gated fixes, terminal audit, and history-operation consent.
- `vibe-writing` owns wording and text-quality deliverables; it does not
  authorize release, commit, staging, or workflow shortcuts.

Do not skip phases in the same turn when the selected downstream skill requires
stopping after an artifact, summary, approval, or proceed-condition boundary.

Auxiliary skills are allowed only when their visible description matches a
subtask and they do not weaken the selected primary phase's write boundary,
approval boundary, stop condition, proceed condition, release policy, or commit
rules. Non-`vibe-*` domain skills are auxiliary only in this first
implementation; they are not first-class primary routes.

## User-Facing Output

Use the user's language for chat summaries. Preserve skill names, file paths,
commands, enum values, field names, and technical identifiers verbatim.

Show concise routing rationale when the phase changes, the selected route is not
obvious, a specialist is unavailable, or no matching specialist was verified and
that affects user expectations. Avoid ceremony on ordinary same-phase turns.

Ask only for decisions that materially affect scope, behavior, data handling,
permissions, verification, accepted risk, or workflow safety and cannot be
determined from local evidence or the active artifact.

## Self-Check

Before acting under `vibe-coding`, confirm:

- Activation is explicit and includes a concrete coding instruction, or the next
  response asks for that instruction without routing.
- The current turn is classified against the active routing state.
- Any named downstream route has visible metadata.
- Exactly one primary downstream `vibe-*` phase is selected when a specialist
  matches.
- Ambiguous approval or readiness wording has not been upgraded into approval or
  execution.
- Specialist write, approval, stop, proceed, review, release, and commit
  boundaries remain intact.
- Cancellation, replacement, unrelated top-level invocation, and finish-gate
  end conditions clear or suspend live routing state.
