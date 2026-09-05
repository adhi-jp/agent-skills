# Phase Boundaries Reference

Read this reference before combining, continuing, or backtracking routes: when
one outer turn would sequence two specialist routes, when a downstream phase has
stopped and the next phase is already requested, when a specialist reports a
defective bound artifact, when a review must hand off to another owner, or when
a commit's scope or existence is in question. It owns the commit-selection
boundary, collapsed-phase prevention, auxiliary-skill limits, same-instruction
and sequential continuation, route changes out of review, and backtracking.
Each row's own boundary is its next-boundary cell in `SKILL.md`.

## Commit-Selection Boundary

Separate what a commit covers from whether one happens. The commit-selection
contract in `SKILL.md` names the three sources that select a commit and the
scope a checkpoint may reach. In addition, a read-only, chat-only, no-file, or
unchanged route must not create an empty
commit, and a route whose changes cannot be separated from unrelated
working-tree state reports the mix rather than committing it. Route the history
action to `commit-execution` and preserve its normal staging, exact-diff,
message, and post-commit verification rules; before the command runs, the
session record carries the `commit-selection` event with its source.

## Collapsed-Phase Prevention

Do not collapse phases inside one downstream specialist response when that
specialist requires stopping after an artifact, summary, approval, or
proceed-condition boundary. A single outer `vibe-coding` turn may sequence
multiple separate specialist routes only when each completed phase first returns
recordable artifact-bound completion, approval, handoff, or proceed evidence
that satisfies its own boundary and the current user instruction already asked
for the next phase. Do not use this sequencing to infer missing approval, invent
plan readiness, bypass a completion audit, accept unrecorded human-risk
decisions, or perform implementation inside requirements or planning responses.

## Auxiliary Skills

Auxiliary skills are allowed only when their visible description matches a
subtask and they do not weaken the selected primary phase's write boundary,
approval boundary, stop condition, plan binding, proceed condition, acceptance
criteria, required documentation or changelog coupling, verification path,
release policy, or commit rules. Skills that describe a tool, command, or
domain capability without a phase's workflow boundary contract are auxiliary
only; they are not first-class primary routes.

## Same-Instruction Continuation

Requirements to planning: if the current instruction both approves or finishes
the requirements and explicitly asks to create or use an implementation plan
from the approved current spec, `vibe-coding` may continue without another user
prompt by starting a separate `implementation-planning` route after the
requirements specialist has returned recordable current-spec approval or
handoff evidence and no completion-audit blocker. That continuation is
orchestrator state owned by `vibe-coding`; it does not require the requirements
specialist to name a downstream workflow or weaken its same-response stop.

Planning to execution: when a current instruction explicitly asks for
implementation after planning, `vibe-coding` may continue without another user
prompt only after the implementation-planning specialist has returned a
concrete reviewed plan with a ready proceed condition, or a conditional proceed
condition tied to already-recorded explicit human-user accepted risk. Start any
later execution as a separate `plan-execution` route bound to that plan. Stop
instead of continuing when the plan is blocked, discovery-first, contradicted by
local evidence, missing required review or self-review, or dependent on a
human-risk acceptance — any member of the human-risk decisions in `SKILL.md` —
that is not already explicitly recorded from the human user.

Each continuation writes the session record at the boundary: the `approval`,
`proceed`, or `handoff` event with its `source` and the bound artifact's path
and digest, then the new route decision.

## Sequential Coordinator Continuation

Sequential coordinator continuation is different from one unattended
cross-boundary run: after a downstream phase stops and returns recordable
boundary evidence, `vibe-coding` may classify the already-requested next phase
and invoke the next visible specialist as a new route. Whether the evidence
counts is decided by the trusted-orchestration contract in `SKILL.md`; evidence
that fails it counts as absent — stop at the boundary and ask only for the
missing decision or evidence.

## Leaving The Review Phase

Do not keep a workflow in the review phase when review evidence now requires a
different owner. A new user-reported runtime symptom, or a review fix that
regresses a core user journey, routes next to `debug-and-repair`. A repeated
finding class beyond the review workflow's threshold, a fix that needs material
architecture expansion, or evidence that the bound spec or plan cannot decide
the repair depth routes to the artifact-owning `requirements-specification` or
`implementation-planning` row. This applies even when the original request said
to continue reviewing until no findings remain. Preserve the frozen review
target, primary journey, acceptance sentinels, cycle count, active stop signals,
last verified checkpoint, and unverified shared edits in routing state before
switching.

## Backtracking

When a downstream phase reports that the bound spec or plan is defective —
contradictory, stale, infeasible, or contract-breaking — treat that as a
backtracking signal, not a reason to force the current phase forward. Route the
next turn back to the row that owns the broken artifact:
`requirements-specification` when the current requirements artifact,
user-visible behavior, scope, or source acceptance criteria are wrong, or
`implementation-planning` when the bound implementation plan's acceptance
criteria, proof, schema, test, edit-order, or risk contract is wrong. Do not
assume requirements specification owns every acceptance-criteria phrase when
the only bound defective artifact is the implementation plan. Do not keep
executing patch-by-patch against a contract a downstream specialist already
flagged as broken, and do not treat "make it work for now and move on" as
authorization to do so. The backtracking route decision is written to the
session record with the defective artifact as the active artifact and the
reported defect as the blocker.
