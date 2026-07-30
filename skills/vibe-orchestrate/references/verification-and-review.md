# Verification And Review

Use this reference before accepting delegated work or launching follow-up repair.
The coordinator verifies the kept tree; worker output is only a status signal.

## Coordinator Verification Gates

Before the first material write round, capture a baseline that later rounds
cannot reconstruct:

- staged, unstaged, and untracked tree state;
- relevant build/test/lint results and raw output location;
- named tests or equivalent contract sentinels when deletion or rename matters;
- project-specific corpus or real-data behavior when synthetic tests do not
  cover the main regression surface;
- hashes, sizes, or decoded summaries for protected binary or generated
  artifacts.

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

A worker's failure report is symmetric: it is not a product defect until the
coordinator reproduces it in the authoritative environment or records why that
environment cannot observe it. Classify sandbox, stdin, filesystem, process,
network, cache, and shared-machine-state divergence before changing product code
or weakening a test.

## Evidence Authority And Claim Coverage

For load-bearing findings, record the claim class and the authority used:

| Claim class | Preferred authority |
| --- | --- |
| Shipped bytes, wire layout, or external artifact parity | Actual shipped or independently produced artifact, then normative format specification, then reference source |
| Normative language or product semantics | Authoritative specification or user-approved contract, then reference source |
| Runtime behavior | Reproduction or trace in the relevant runtime regime |
| Performance | Measurement in the relevant workload regime |

Also separate:

- `verified`: the exact proposition observed;
- `inferred`: the additional proposition needed for the disposition but not yet
  observed.

Observing that two implementations differ does not establish which one is
correct. A non-empty load-bearing `inferred` proposition needs another proof,
an explicit risk disposition, or a blocked finding; it must not be hidden by
confidence words.

## Proof Falsifiability

Before accepting a green test or metric as proof, ask what wrong implementation
would make it fail. Reject or strengthen proof that relies only on:

- a spy or injected boundary the implementation never consumes;
- expected values imported from the target under test;
- best-case input for a general bound;
- final-state or directory-list evidence for a claim about calls that must never
  occur;
- a lifecycle, phase, encoding width, or branch matrix with the relevant path
  absent.

When an acceptance metric is intended to distinguish a defect, record its
current/before result. If the known-bad baseline already passes, the metric
cannot gate the repair until it is corrected or replaced.

Pass counts prove how many tests passed, not which contracts remain present.
When deletion matters, compare named-test sets. When text diff cannot explain a
changed artifact, classify it as external/vendor evidence, self-generated
golden, or build output. External/vendor evidence changes block acceptance;
self-generated goldens require the named generator and semantic decode or
inspection; uninspectable changes remain unverified.

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

For every accepted material finding, preserve the `verified` proposition,
authority source, and any remaining `inferred` proposition in the disposition.

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
It is not a shortcut for a new design choice. If the edit changes behavior and
is not the direct application of one already-proven correction, use a bounded
contract or record the design evidence before editing.

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
