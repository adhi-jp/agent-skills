# Plan Artifact Output

## Standard Plan Artifact

Use this structure for an implementation-ready plan. Keep `light` plans compact;
requirements and tests still precede implementation. Omit conditional sections
when their trigger is absent rather than filling them with ceremony.

```markdown
# [Plan title]

## Goal
- [User-visible outcome]

## Plan depth
- Mode: `light` | `strict`
- Rationale:

## Verified facts and sources
| Claim | Evidence | Source | Impact |
| --- | --- | --- | --- |

## Requirements
- In scope:
- Out of scope:
- Constraints:

## Ambiguities, questions, and decisions
- [Only unresolved or recorded decisions that affect the contract]

## Acceptance criteria
- [Observable pass/fail criterion]

## Acceptance proof matrix
[Include only when paired paths, material state coverage, or human-owned proof
needs durable mapping.]

## Behavior contract inventory
[Include when existing behavior must be preserved or intentionally changed.]

## Behavioral equivalence analysis
[Include for replacement, restoration, refactor, or compatibility work.]

## Failure-pattern checks
[Include only selected high-risk sections and near-miss non-selections.]

## Test plan
- Acceptance tests:
- Regression tests:
- Negative and edge cases:
- Manual or visual checks:

## Plan integrity gates
- [Concise applied gates and evidence-backed not-applicable decisions]

## Capability dependencies
| Step | Capability | Availability evidence | Impact if absent | Fallback or blocker |
| --- | --- | --- | --- | --- |
| [Only when absence materially changes feasibility, safety, proof, or method] |

## Implementation plan
1. [Proof/setup step when needed]
2. [Implementation step]
3. [Verification and final diff review]

## Implementation progress
| Item | Planned scope | Status | Verification/review | Last update | Next item or blocker |
| --- | --- | --- | --- | --- | --- |
| [Only for cross-session/cross-actor or independently resumable work] |

## Reserved decisions
| Decision ID | Reserved field | Decision owner | Allowed authority | Response carrier | Proceed effect |
| --- | --- | --- | --- | --- | --- |

Each row reserves exactly one declared decision. The owner and allowed authority
define who may answer it; the response carrier defines how that answer is
recorded; the proceed effect defines what remains blocked or becomes eligible.
Reserved fields do not amend scope, acceptance criteria, tests, risks, or
implementation steps. Batch only fields that are low-risk and knowable at the
same time; permission-protected, evidence-dependent, or other human-risk
decisions remain at their later gates.

## Commit checkpoints
- [Include only when the current user or an already-approved plan item explicitly
  selects the checkpoint. Record scope and required verification. Omit otherwise.]

## Risks and unproven items
- Item:
- Evidence label: `Unproven` | `Accepted risk`
- Impact:
- Fastest proof path:
- Revisit trigger:

## Implementation handoff
- When implementing this plan, bind this path and re-read its current reviewed
  content. Re-check local facts, follow acceptance criteria and tests, honor
  material capability dependencies, and stop if evidence contradicts the plan.
- If authority-bearing requirements, criteria, risks, scope, tests, or steps
  changed without clear authority, return to plan revision before execution.

## Additional-perspective review
[Include only when risk-triggered or user-requested. Follow
`plan-multi-perspective-review-gate.md`; record perspectives, capability and
capacity evidence, requested and started batches, observed execution mode,
fallbacks, material findings, dispositions, and blockers.]

## Plan self-review
- Checks performed:
- Corrections made:
- Remaining material issues:

## Proceed condition
- [Ready, conditionally ready with accepted risk, or blocked]
```

For discovery-only work, replace `Implementation plan` with `Discovery plan` and
list proof tasks, exit criteria, and the next decision point.

## Binding and Change Review

Bind by the selected plan path and its current reviewed content. Existing commit,
revision, or host evidence may identify a reviewed state when already available.
Do not generate or maintain full-artifact hashes, section hashes, identity
sidecars, or stale-digest reconciliation.

A later actor must re-read the current plan. If authority-bearing requirements,
acceptance criteria, scope, risks, tests, or implementation steps changed and the
authority is unclear, stop for semantic plan review. Progress-only updates to an
intentional resumable ledger and harmless formatting changes do not by themselves
invalidate the contract.

## Quality Checklist

Before finalizing:

- Planning edited only the plan artifact and did not implement or commit.
- Facts and assumptions have evidence labels; current blockers remain visible.
- Requirements and observable acceptance criteria precede tests and steps.
- Tests can falsify the important behavior and include positive controls where
  absence assertions could pass vacuously.
- High-risk inventories, equivalence, recovery, security/data, migration, or
  human-review controls appear only when applicable and remain strong.
- `Capability dependencies` is omitted when empty and contains only material
  dependencies with fallback or blocker behavior.
- `Implementation progress` exists only for real resumability needs and begins
  with unverified items uncompleted.
- Additional perspectives are recorded only when risk or the user requires them;
  local self-review always occurs. Their launch record follows the single
  capacity algorithm in `plan-multi-perspective-review-gate.md` rather than
  restating a second procedure.
- Commit checkpoints appear only when explicitly selected; planning invocation,
  tracked status, or multiple slices did not select history work.
- The handoff binds the path/current content, re-checks stale local facts, and
  stops on unclear semantic drift without requiring manual digests.
- The proceed condition accurately reflects proof, accepted risk, and blockers.
