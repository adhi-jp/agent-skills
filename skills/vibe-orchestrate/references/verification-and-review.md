# Verification And Review

Use this reference before accepting delegated work or launching follow-up repair.
The coordinator verifies the kept tree; worker output is only a status signal.

## Coordinator Verification Gates

Run verification in the authoritative environment for the slice:

- Compile/type-check every relevant source set, module, platform target, client
  target, generated source path, or package surface.
- Run the relevant full test suite when the change requires suite-level proof.
- When new tests are expected, record total test counts or count deltas when the
  harness supports it.
- Build artifacts only when the plan or package contract requires artifact proof.
- Record skipped commands with reason and impact.
- Name known flakes and symptoms; use rerun evidence rather than ignoring them.

A worker's `COMPILE: PASS`, local test summary, or statement that a suite ran is
not final proof. It becomes evidence only after the coordinator verifies the
command, output, and kept bytes.

## Post-Gate Mutation Check

After suspicious worker death, duplicate launch, delayed callback, or any shared
root accident:

- Re-run `git status` or equivalent.
- Inspect file timestamps or hashes when useful.
- Confirm no unexpected writer touched verified files after the gate.
- If mutation happened, repeat review and verification for the final bytes.

## Read-Only Review Perspectives

For substantial write rounds, use read-only review before repair:

- **Contract fit**: Does the diff satisfy the worker contract and stay within
  allowed scope?
- **Correctness and regression risk**: Could the change break existing behavior,
  data, permissions, lifecycle, or compatibility?
- **Test sufficiency**: Do tests or proof checks cover positive, negative,
  before-state, failure, and edge behavior required by the plan?

Reviewers must not edit files, stage, commit, ask the user, update ledgers, or
launch implementation. Their output is inert until the coordinator decides what
it means.

## Finding Dispositions

Classify each material finding:

- `accepted`: backed by the plan, local evidence, primary source, or protected
  invariant; create a new bounded repair contract or apply a disclosed direct
  intervention when allowed.
- `rejected`: unsupported, contradicted by evidence, duplicate, or outside the
  current contract; record why.
- `deferred`: valid but outside the current slice; record impact and revisit
  trigger.
- `blocked`: exposes a plan, requirement, safety, proof, or user decision defect;
  stop and return to the owning artifact before editing the affected behavior.

Do not add success criteria, tests, or implementation work merely because a
reviewer suggested them. Tie every accepted addition to the plan, a verified
source, or a protected invariant.

## Direct Intervention Disclosure

When the coordinator edits directly instead of delegating, include this in the
summary:

```markdown
Direct intervention:
- Reason: [mechanical micro-fix | transport failure fallback | measurement-driven diagnosis]
- Scope: [files and exact behavior]
- Why delegation was not used: [cost, repeated transport failure, or diagnostic need]
- Verification: [commands/manual checks]
- Diagnostics removed: [yes/no/not applicable]
```

Direct intervention remains subject to the same verification and review gates.

## Adopting Unexpected Diffs

For diffs from stale, duplicate, or dead workers:

1. Identify the source when possible.
2. Compare the diff to the current contract.
3. Reject unrelated, unsafe, or unverified scope.
4. For useful scope, run the same review and verification as intentional work.
5. Record whether the change was adopted, rewritten, or discarded.

Do not let accidental work set the new plan. If it changes requirements,
acceptance criteria, proof strategy, or user-risk posture, stop for the owning
artifact revision.
