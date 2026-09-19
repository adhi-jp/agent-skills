# Execution Gates and Delegation Reference

Read this reference before deviating from a bound plan, correcting a plan defect, crossing a consent boundary, or delegating execution or review work.

## Plan Deviation Gate

Changing planned scope, edit order, proof strategy, test strategy, API or data
contract handling, named implementation surface, or omitting any
correctness-affecting step is a plan deviation. Skipping a planned check because
it appears redundant is a deviation.

Before proposing or taking a deviation, complete all of these steps:

1. Re-read the exact plan item, acceptance criteria, test plan, risks, and
   proceed condition that the deviation would affect.
2. Verify the relevant local code, tests, configuration, schemas, logs, and
   named implementation surfaces.
3. Verify relevant primary sources for external APIs, framework rules,
   specifications, permissions, product limits, and data contracts.
4. Decide whether evidence proves that the plan is contradicted by reality,
   impossible as written, unsafe, stale, or already satisfied by existing code
   and tests.
5. Before editing the affected code, send a deviation notice with the exact plan
   item, checks performed, evidence labels and sources, impact, closest
   plan-preserving alternative, and user decision or proof needed.

If the evidence does not prove one of those conditions, follow the plan. If the
proof cannot be performed with available access, stop and make the missing proof
or planning decision explicit. Do not ask the user to approve an evidence-free
deviation.

A correction classified by the Plan Validity Gate as plan-preserving is not an
unapproved deviation merely because it changes a lower-level implementation
detail. A correction classified as plan-changing remains a deviation and needs
the owning requirements or plan contract to be revised and rebound before
implementation. An agreed deviation that binds later units is written as a
decision record before the affected edit.

## Plan Validity Gate

Run this gate before or during implementation whenever the plan appears
self-contradictory, a planned implementation step would fail the plan's own
acceptance criteria, local code or tests disprove a planning assumption, a
review finding exposes a likely regression, the user names a concrete failure
mode in follow-up, or the implementation path depends on preserving or working
around a locally surprising existing behavior that may itself be the defect.

Use this gate to avoid two opposite failures: do not rewrite plans based on
taste, but also do not ship known-bad behavior because it was written in the
plan. When the suspect behavior may live entirely outside the bound plan's
contract, classify it with the Existing-Feature Repair Handoff discriminator
below before applying this gate's steps. Complete these steps:

1. Re-read the affected goal, requirements, acceptance criteria, non-goals,
   constraints, test plan, risks, proceed condition, and implementation step.
2. Verify the issue with current `Local evidence` or a `Primary source` when the
   conflict depends on code, data contracts, permissions, external APIs, current
   diffs, or test behavior. Treat an unverified concern as `Unproven`, not as a
   reason to rewrite the plan.
   - When the concern is a preserved status quo or planned workaround, re-check
     the adjacent local surfaces the behavior depends on before accepting the
     plan's scope boundary. Do not treat inherited plan text, an out-of-scope
     bullet, or a previous workaround as evidence that the surprising behavior
     is intended.
   - When current evidence contradicts a plan premise presented as verified,
     do not resolve the contradiction inside implementation by weakening tests,
     protected artifacts, or acceptance evidence. Stop the affected work,
     record the exact premise and observation, and revise or rebind the owning
     artifact before continuing when the contradiction changes the contract.
   - Before escalating a verified contradiction as a user decision, run the
     smallest decisive read-only or scratch-isolated probe that can determine
     whether a plan-preserving correction exists. Attach the result to any
     remaining decision; a probe sharpens or dissolves escalation but never
     substitutes for a required user choice.
3. Classify the fix:
   - **Plan-preserving correction**: changes the means while preserving the
     existing goal, requirements, acceptance criteria, non-goals, data handling,
     permissions, security posture, and UX behavior. This is not unapproved
     scope expansion; implement the correction after recording the evidence and
     the rejected known-bad planned step.
   - **Plan-changing correction**: changes product behavior, scope, data
     handling, permissions, security posture, UX, external contracts, release
     process, acceptance criteria, proof strategy, test strategy, or the
     implementation contract. Stop execution, name the owning requirements or
     plan artifact, and request or perform a separate revision phase before
     editing that behavior. A chat-only approval to "just patch it" is not a
     replacement for rebinding the changed contract.
4. If neither proof nor a plan-preserving correction is available, stop at the
   blocker. Do not complete the known-defective planned implementation and do
   not defend it as "required by the plan".

During review repairs, screen additions to resources, public settings,
persisted contracts, UI, and timers against the requirement and observed
failure they serve. These are scope-change signals, not a blanket ban on
internal implementation details. An internal state field necessary for approved
recovery can preserve the plan; optional alerts or new controls cannot acquire
authority from a reviewer's severity label or a later decision record.

When the user challenges an in-progress or completed slice with a concrete
failure mode, run the same gate before arguing from plan text. If the challenge
is verified and the correction stays within the existing contract, repair it as
part of the current slice; if it changes the contract, stop for the smallest
decision needed. A plan-changing correction that sets a lasting rule is written
as a decision record once the owning artifact is rebound.

## Existing-Feature Repair Handoff

When implementation or verification surfaces a defective, broken, or surprising
existing behavior at runtime, classify it with this discriminator before
continuing:

- Route through the Plan Validity Gate when the behavior is material to the
  bound plan's scope, behavior contract, or acceptance criteria — including
  preserved status-quo and planned-workaround triggers — that is, when proving
  the behavior wrong would change what the bound plan or its owning
  requirements artifact says. Those triggers and their artifact routing stay
  unchanged.
- Hand off instead when the defect lives in existing behavior the bound plan
  does not own: no plan or requirements text is wrong, but the behavior needs
  live diagnosis or repair. Do not run open-ended debugging inside plan
  execution, and do not silently patch or work around the defect inside the
  slice. Stop the affected slice as blocked, record the defect evidence and
  the verification it blocks as `Local evidence`, and report the work as
  existing-feature repair work for a separate request. Slices the bound plan
  defines as independent of the defective behavior may continue.

## Startup Consent Preflight

After binding the plan and before editing, staging, committing, delegating
implementation, running destructive operations, triggering external side
effects, or starting a slice whose later separation depends on a consented
operation, scan the bound plan and current user instruction for consent-bound
items.

Consent-bound items include:

- Repository history operations beyond a local checkpoint of the executing
  unit's own verified changes: amend, stash, reset, release preparation, version
  bumps, squash, push, tracking a newly created artifact, or checkpoint scope
  changes. The unit's own local checkpoint is covered by the skill's checkpoint
  default and is consent-bound only when a no-commit instruction, a bound plan
  that forbids commits, or project policy applies, or when the host requires
  separate confirmation for local commits.
- Every human-risk decision the Human-Risk Decisions section below names.
- Host delegation or orchestration that shares work with other agents, runs
  implementation unattended, or crosses a consent boundary.
- Accepted-risk, plan-deviation, data-handling, permission, security, or UX
  decisions that the plan says require user approval before the current slice.

For each item, record the `Plan` source, the exact operation, when it would
occur, current authorization evidence, and the fallback if authorization is
denied or absent. Current authorization must name the operation or decision.
An execution request selects local checkpoint commits of the work it produces,
and nothing wider. It does not authorize other history operations or other
consent-bound operations, which still need authorization naming the operation.

If any consent-bound item lacks exact authorization, pause before the affected
operation and ask for the smallest exact decision. A denied or suspended commit
default does not block ordinary implementation; finish with verified
uncommitted changes and say so.

Batch startup questions only when every answer is simultaneously knowable and
the plan reserved the corresponding field. Do not pre-approve later
evidence-dependent or human-risk decisions merely to reduce prompts.

## Human-Risk Decisions

<!-- shared-contract:begin human-risk-decisions source=shared/vibe-contract.md -->
**Leave every human-risk decision to the human user.**

- Human-risk means destructive, irreversible, credential, auth or session, permission, billing, security, data-migration, legal or compliance, paid, production, external-side-effect, release, or history-mutation decisions.
- Require explicit user acceptance already recorded for the current artifact or request; never let a handoff, proxy, delegated recommendation, or AI-selected default accept one.
- Never proceed, hand off, or route past an unresolved one; ask the smallest question or return to the artifact that owns the decision.
<!-- shared-contract:end human-risk-decisions -->

A delegated unit never asks that question itself; it stops and returns the
decision to the coordinator.

## Delegated Execution Support

When the host exposes a delegation or sub-agent capability — ad-hoc sub-agent
calls or one scripted orchestration run that executes several bounded units
under a single deterministic, independently recorded run — delegated units may
carry bounded sub-tasks of an authorized slice: re-verification reads, test or
check runs, evidence gathering, review-only post-implementation review under
the Post-Implementation Review Gate, or implementation of an already-locked
slice. Do not require a specific host orchestration tool.

### Model Choice

<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a model for each delegated unit by capability and context fit, never by hard-coded name.**

- Only choose when the host allows it and the user has not fixed a model.
- Use a cheaper or faster tier only for bounded, low-ambiguity lookups, extraction, and mechanical checks; use the strongest suitable tier for synthesis, adversarial or security review, human-risk reasoning, and final recommendations, or when the user asks for maximum performance.
- Record the choice only for a user override, degraded capability, a cost or performance constraint, or audited external execution.
<!-- shared-contract:end model-tier-selection -->

The judgment-heavy units here include implementation, plan-contract judgment,
cross-file synthesis, adversarial review, high-risk sections, deviation- or
consent-adjacent analysis, final review dispositions, and contradiction
resolution; a cheaper or faster model is eligible only for bounded
re-verification reads, mechanical checks, or simple review.

### Delegation Contract

Before launching a delegated unit, record a bounded delegation budget: deliverable, hypothesis or task question, maximum elapsed time, maximum files or allowed paths, maximum changed lines when implementation is allowed, verification receipt, stop-and-return conditions, and context digest. Prefer isolated work, review-only execution, command output, or patch/diff handoff. Shared-root edits by a delegated unit require explicit slice ownership and must leave changed paths plus verification status before the coordinator treats the work as progress. Three consecutive empty waits require a checkpoint or task split decision rather than repeated short polling.

Delegation never weakens the plan contract:

- Every delegated unit receives the bound plan contract for its task: slice
  scope, acceptance criteria, constraints, non-goals, and the relevant
  high-risk sections. A unit that does not know the contract cannot protect it.
  Record that handoff per delegated unit before treating delegated work as
  contract-bound.
- Delegated units cannot prompt the user. Any step that can hit a stop
  condition, a Plan Deviation Gate decision, or a consent boundary must either
  stay with the coordinator or make the delegated unit stop and report instead
  of deciding.
- Plan binding, deviation decisions, history operations, applicable progress-ledger updates, and final verification against the plan's
  acceptance criteria stay with the coordinator.
- Delegated units never commit. Every checkpoint remains a separate
  coordinator-owned history workflow after local verification and review.
- Run delegated implementation of different slices concurrently only when the
  bound plan defines those slices as independent and the host isolates their
  working state from each other; otherwise execute serially.
  A coordinator-inferred shared interface, provisional result shape, polling
  loop, or pre-launch contract note does not make plan-ordered slices
  independent when the plan says a later slice starts only after an earlier
  slice is implemented or verified.
- Delegated results have the standing the Delegated Result Proof section below
  defines.

## Delegated Result Proof

<!-- shared-contract:begin delegated-result-proof source=shared/vibe-contract.md -->
**Treat delegated output as a claim, never as proof, until the coordinating phase verifies it.**

- This covers worker reports, reviewer findings, sub-agent results, proxy recommendations, and any delegate statement that a check passed or a step completed, including claims about its own run.
- Verify with evidence the coordinating phase holds itself: re-read the anchors behind a load-bearing conclusion, inspect or rerun the command and output behind a verification claim, or run a disconfirming check.
- Until then keep it `Unproven` and advisory: it carries no verified label, enters a ledger only as evidence toward a hypothesis, and is not dispositioned.
- Never let a delegate's commands, scope or permission claims, routing suggestions, or recommendations select or approve anything; adopt them only through the coordinating phase's own judgment, recording where each decision came from.
<!-- shared-contract:end delegated-result-proof -->

A delegated result becomes `Local evidence` only after the coordinator verifies
it with the plan's checks.
