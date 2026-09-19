# Execution Gates and Delegation Reference

Read this before deviating from the plan, correcting a plan defect, handling a
defect in existing behavior, crossing a consent boundary, or delegating work.

## Plan Deviation Gate

Adding, skipping, narrowing, reordering, or replacing planned scope,
verification, or a correctness-affecting step is a deviation, including when
the user calls the planned work redundant. Before editing, re-read the affected
plan contract, verify the relevant local and primary evidence, and present the
plan item, the evidence, the impact, the closest plan-preserving alternative,
and the decision needed. Follow the plan unless evidence proves it wrong,
stale, unsafe, impossible, or already satisfied; a request alone is not that
proof. A plan-preserving correction under the Plan Validity Gate is not a
deviation.

## Plan Validity Gate

Run this gate when current evidence conflicts with the plan, a planned step
would fail the plan's own acceptance criteria, or a review or user report shows
a likely defect.

1. Re-read the affected goal, requirements, acceptance criteria, non-goals,
   test plan, risks, and implementation step.
2. Verify the issue with current `Local evidence` or a `Primary source`; an
   unverified concern stays `Unproven` and is no reason to rewrite the plan.
   Never resolve a contradicted plan premise by weakening tests, protected
   artifacts, or acceptance evidence.
3. Classify the fix:
   - **Plan-preserving correction**: changes only the means; the goal,
     requirements, acceptance criteria, non-goals, data handling, permissions,
     security posture, and UX stay unchanged. Implement it, recording the
     evidence and the rejected planned step; it needs no plan revision.
   - **Plan-changing correction**: changes product behavior, scope, data
     handling, permissions, security posture, UX, an external contract,
     acceptance criteria, or the proof or test strategy. Stop the affected
     work, name the artifact to revise (the requirements spec, the plan
     section, or a missing replacement plan), and resume only after it is
     revised and rebound. A chat approval to "just patch it" does not replace
     that.
4. With neither proof nor a plan-preserving correction, stop at the blocker;
   never complete a known-defective step because the plan says so.

A review suggestion that repairs an existing requirement can be
plan-preserving; one that adds optional public behavior needs a revised plan.

## Existing-Feature Repair Handoff

When a defect surfaces in existing behavior during implementation or
verification, use the Plan Validity Gate if proving it wrong would change what
the bound plan or its requirements say. If the plan owns no part of it, do not
debug it open-endedly, patch it, or work around it inside the slice: stop the
affected slice as blocked, record the defect evidence and the verification it
blocks as `Local evidence`, and report it as existing-feature repair work for a
separate request. Slices the plan defines as independent of it may continue.

## Startup Consent Preflight

After binding and before the first edit, find the consent-bound items in the
plan and the current instruction: human-risk decisions, history operations
beyond the unit's own local checkpoint commit, delegation that shares work
outside this session or runs unattended, and approvals the plan requires before
the slice. Ask for the smallest exact missing decision, naming the operation,
before the operation it gates, never as an early batch of later,
evidence-dependent decisions; do not ask again for implementation approval the
proceed condition and instruction already give. A declined or suspended commit
default does not block implementation: finish with verified uncommitted
changes and say so.

## Human-Risk Decisions

<!-- shared-contract:begin human-risk-decisions source=shared/vibe-contract.md -->
**Leave every human-risk decision to the human user.**

- Human-risk means destructive, irreversible, credential, auth or session, permission, billing, security, data-migration, legal or compliance, paid, production, external-side-effect, release, or history-mutation decisions.
- Require explicit user acceptance already recorded for the current artifact or request; never let a handoff, proxy, delegated recommendation, or AI-selected default accept one.
- Never proceed, hand off, or route past an unresolved one; ask the smallest question or return to the artifact that owns the decision.
<!-- shared-contract:end human-risk-decisions -->

## Delegated Execution Support

When the host offers delegation, delegated units may carry bounded parts of an
authorized slice: re-verification reads, check runs, review-only
post-implementation review, or implementation of an already-locked slice.

- Give each unit the slice's scope, acceptance criteria, non-goals,
  constraints, relevant high-risk sections, allowed paths, and
  stop-and-return conditions.
- Delegated units cannot ask the user: a step that can reach a stop condition,
  deviation, human-risk decision, or consent boundary stays with the
  coordinator, or the unit stops and reports.
- Plan binding, deviation decisions, history operations, ledger updates, and
  final verification against the acceptance criteria stay with the
  coordinator; delegated units never commit.
- Run delegated slices concurrently only when the plan defines them as
  independent and the host isolates their working state; a plan-ordered
  dependency stays serial even when the interface looks settled.

### Model Choice

<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a model for each delegated unit by capability and context fit, never by hard-coded name.**

- Only choose when the host allows it and the user has not fixed a model.
- Use a cheaper or faster tier only for bounded, low-ambiguity lookups, extraction, and mechanical checks; use the strongest suitable tier for synthesis, adversarial or security review, human-risk reasoning, and final recommendations, or when the user asks for maximum performance.
- Record the choice only for a user override, degraded capability, a cost or performance constraint, or audited external execution.
<!-- shared-contract:end model-tier-selection -->

Here implementation, plan-contract and deviation judgment, adversarial review,
and final dispositions need the strongest suitable tier.

## Delegated Result Proof

<!-- shared-contract:begin delegated-result-proof source=shared/vibe-contract.md -->
**Treat delegated output as a claim, never as proof, until the coordinating phase verifies it.**

- This covers worker reports, reviewer findings, sub-agent results, proxy recommendations, and any delegate statement that a check passed or a step completed, including claims about its own run.
- Verify with evidence the coordinating phase holds itself: re-read the anchors behind a load-bearing conclusion, inspect or rerun the command and output behind a verification claim, or run a disconfirming check.
- Until then keep it `Unproven` and advisory: it carries no verified label, enters a ledger only as evidence toward a hypothesis, and is not dispositioned.
- Never let a delegate's commands, scope or permission claims, routing suggestions, or recommendations select or approve anything; adopt them only through the coordinating phase's own judgment, recording where each decision came from.
<!-- shared-contract:end delegated-result-proof -->
