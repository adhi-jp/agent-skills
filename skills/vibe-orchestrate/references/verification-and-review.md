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

- Preserve every input-named touched path, source target, test target, and
  generated surface in the receipt. A generic "relevant files/gates" summary
  is insufficient when the contract named concrete surfaces.
- Match gate granularity to those concrete surfaces. Name both server and client
  compile/type-check targets when both changed, and request quantitative test
  inclusion evidence when a named new or changed test is expected and the
  harness can report it.
- Compile/type-check every relevant source set, module, platform target, client
  target, generated source path, or package surface.
- Run the relevant full test suite when the change requires suite-level proof.
- When new tests are expected, record total test counts or count deltas when the
  harness supports it.
- Reconcile new artifact discovery or registration. When stable counts are
  exposed, compare the observed total with the frozen baseline plus expected
  delta; an unchanged total cannot prove that the new artifact ran merely
  because the suite is green. Do not require count arithmetic from harnesses
  that cannot expose a stable count.
- Build artifacts only when the plan or package contract requires artifact proof.
- Record skipped commands with reason and impact.
- Name known flakes and symptoms; use rerun evidence rather than ignoring them.

Verification receipts must preserve each gate's own exit status. In shells that
do not propagate pipeline failures, piping a gate through an output filter such
as `tail`, `head`, or `grep` can make the pipeline report the filter's status
instead of the failing gate's status, allowing an `&&` chain to continue and
produce a false-green aggregate. Keep every gate independently inspectable by
using separate invocations, explicit pipeline-status capture, or unambiguous
per-gate status records. Output filtering is presentation: neither a rendered
`PASS` line nor the absence of failure text can replace the gate verdict.

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

For correctness, security, resource, or lifecycle repairs, run an independent
attack on the original defect with an unambiguous verdict and concrete
path/input evidence. Previously green aggregate gates are not repair proof.
When a broad new suite fails first, compare relevant default and
serial/isolated modes before attributing the failure to product code; record
the execution mode without universalizing serial runs.

For new concurrency/process/timing/isolation suites, choose repeatability from
risk rather than a fixed run count and record per-run spread and exact
recurrence. A clean repeated series bounds residual risk but does not identify
an unexplained flake; the first recurrence stops verification for diagnosis.
Freeze characterization assertion identity before repair. Ask which protected
behavior could be deleted while the test still passed, pair absence checks with
same-channel presence evidence, and bound non-termination regressions.

For proof-only repair, when product behavior is already correct and the
assertion/oracle is strengthened, deliberately perturb the exact asserted
surface so the new assertion is observed failing. Record assertion identity,
command/test, failure status/text, revert the perturbation, prove no bytes
remain, then rerun the real check. If that safe reversible failure cannot be
observed, keep the proof item blocked/`Unproven`; prose review and historical
failures are not substitutes.

## Post-Gate Mutation Check

After suspicious worker death, duplicate launch, delayed callback, or any shared
root accident:

- Re-run `git status` or equivalent.
- Inspect file timestamps or hashes when useful.
- Confirm no unexpected writer touched verified files after the gate.
- If mutation happened, repeat review and verification for the final bytes.

When a round is failed, timed out, resumed, receipt-less, or metadata-ambiguous,
accept it only after runner, report, journal, named task or process, and tree
evidence, executed role, and host-exposed launch metadata reconcile. Requested
model, effort, write access, cwd, role, or flags are not proof of observed
execution.

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

For every material finding, record these fields separately: verified
proposition, authority, remaining inference, severity, current-scope basis,
introduced assumption, disposition, and repair authorization. Validity,
severity, confidence, or reviewer agreement cannot authorize repair by itself.

Coordinator-noticed contract deviations are findings too. Give each an explicit
disposition, rationale, and falsification or revisit trigger instead of silently
waiving it. Reviewer convergence is a reason to inspect cited evidence, not a
vote: record a citation-inspection receipt with finding id, cited anchor,
artifact identity/revision inspected, observed support/contradiction/absence,
evidence label, remaining inference, and coordinator disposition.

When a rejected finding is likely to recur and the bound artifact owns future
review context, write back only the load-bearing verified refutation and anchor.
Do not turn routine review narration into artifact history.

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

Permitted reasons also include a diagnosis-complete fully specified bounded
repair and an authoritative verification capability available only to the
coordinator. New design, human-risk decisions, and unverified root causes remain
outside direct intervention. After changing a deep shared invariant, run a
focused rereview and attack the inverse or symmetric failure mode; reviewer
self-report never closes executable gates.

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
