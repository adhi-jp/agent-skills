# Plan Artifact Output

## Standard Plan Artifact

Use this structure for an implementation plan. Omit a conditional section when
its trigger is absent rather than filling it with ceremony; `light` plans keep
every section short. Requirements and acceptance criteria precede tests, and
tests precede implementation steps.

```markdown
# [Plan title]

## Goal
- [User-visible outcome]

## Plan depth
- Mode: `light` | `strict` — [rationale]

## Verified facts and sources
| Claim | Evidence | Source | Impact |
| --- | --- | --- | --- |

## Requirements
- In scope:
- Out of scope:
- Constraints:

## Ambiguities, questions, and decisions
- [Only unresolved or recorded decisions that affect the contract: who decides,
  what stays blocked until then, and any decision-record id]

## Acceptance criteria
- [Observable pass/fail criterion]

## Behavior contract inventory
## Behavioral equivalence analysis
## Failure-pattern checks
[Only when the matching high-risk control applies.]

## Test plan
[Each entry names what it proves and the criterion, required proof, or failure
mode it closes, marked `new`, `extends <test>`, or `reuses <test>`; cite a
reused or extended test from local evidence. Manual or visual checks name their
executor, setup, time, and infrastructure.]

## Plan integrity gates
- [Investigation surfaces and their status; gate outcomes that changed or
  blocked the plan]

## Capability dependencies
| Step | Capability | Availability evidence | Impact if absent | Fallback or blocker |
| --- | --- | --- | --- | --- |
[Only when absence materially changes feasibility, safety, proof, or method.]

## Implementation plan
1. [Proof or discovery step while feasibility is unproven]
2. [Implementation steps in edit order]
3. [Verification and final diff review]

## Implementation progress
| Item | Planned scope | Status | Verification/review | Last update | Next item or blocker |
| --- | --- | --- | --- | --- | --- |
[Only for cross-session, cross-actor, or independently resumable work.]

## Reserved decisions
| Decision ID | Reserved field | Decision owner | Allowed authority | Response carrier | Proceed effect |
| --- | --- | --- | --- | --- | --- |
[Only for decisions deliberately left for a later answer. Each row reserves one
decision and never amends scope, criteria, tests, risks, or steps; cite a
decision-record id instead of restating rationale.]

## Commit checkpoints
- [Only when explicitly selected: scope and required verification.]

## Risks and unproven items
- [Item — `Unproven` | `Accepted risk`; phase relevance; impact; fastest proof
  path; revisit trigger]

## Implementation handoff
- When implementing this plan, [binding, re-checks, scope, and stop conditions]

## Additional-perspective review
[Only when risk-triggered or user-requested: perspectives, how each ran,
material findings and dispositions, blockers.]

## Plan self-review
- Checks performed, corrections made, remaining material issues.

## Proceed condition
- [Ready, conditionally ready with accepted risk, or blocked — and why]
```

For discovery-only work, replace `Implementation plan` with `Discovery plan`:
proof tasks, exit criteria, and the next decision point.
