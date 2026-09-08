# Coordinator Practices

Read this reference before selecting delegated model tiers, judging the coordinator's own capability fit, decomposing substantial work, writing or auditing worker contracts, inlining facts and protected evidence, directly intervening, or handling multiple/overlapping writers.

## Frontier Coordinator And Model-Tier Loops

### Model Choice

<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a fit-for-purpose model per delegated unit by capability and context fit, not by hard-coded model name.**

- Choose only when the host lets the phase choose a delegated model and the user has not explicitly fixed one.
- Use a cheaper or faster model only for bounded, low-ambiguity work — lookups, extraction, mechanical checks, simple review — when lower capability is quality-neutral or the user prioritizes cost or latency.
- Bias upward to the strongest suitable reasoning and context tier available for judgment-heavy work: cross-artifact synthesis, adversarial review, security, data-safety, and other human-risk reasoning, contract compliance, contradiction resolution, and final recommendations or dispositions.
- Bias upward especially when the user asks for maximum performance.
- Never inherit the top model for every small unit.
- Never downshift solely to save tokens when the unit needs stronger reasoning.
- Record the model choice only for an explicit user override, degraded capability, a cost or performance constraint, or audited external execution.
- Give routine compatible choices no receipt.
<!-- shared-contract:end model-tier-selection -->

The judgment-heavy units this workflow keeps with the coordinator or the
strongest suitable tier include decomposition, non-delegable decisions,
ambiguous architecture, final synthesis, verification interpretation, review
dispositions, and user-risk choices; a token-efficient delegate is eligible only
for low-ambiguity lookup, extraction, mechanical checks, fixture comparisons,
and narrow read-only review.

### Token-Saving Loop

Good token-saving loops reduce repeated context, not proof. Prefer this loop:

1. The coordinator verifies and inlines the facts, invariants, file boundaries,
   and decision criteria that a worker would otherwise rediscover.
2. Each delegated unit receives a compact context digest, one question or work
   item, explicit allowed paths/tools, expected receipt, and escalation triggers.
3. Token-efficient or previous-generation workers handle low-ambiguity lookup,
   extraction, mechanical checks, simple fixture comparisons, or narrow
   read-only review.
4. The coordinator verifies load-bearing anchors, reconciles contradictions,
   and decides whether to close, split, retry with a narrower contract, or
   escalate to a stronger reasoning/context tier.
5. Later loop iterations send only the changed facts, unresolved blockers, and
   latest verified state instead of the full parent transcript unless full
   context is necessary and the reason is recorded.

Escalate instead of repeatedly retrying a cheap delegate when the worker reports
uncertainty, hits a scope blocker, produces contradictory findings, needs
cross-artifact synthesis, touches security/data-safety or user-risk judgment,
would make a final recommendation, or fails the same contract twice. Do not
hard-code vendor model names into the skill contract, inherit the top model for
every small worker, downshift judgment-heavy work solely to save tokens, or
claim token, quality, latency, or reliability improvement without recorded
metrics or review evidence.

## Coordinator Capability Fit

Tier choice applies to the coordinator's own seat, not only to delegates. A
coordinator running on a mid-capability or economy seat is a legitimate
configuration when its work is decomposition, contracting, receipt
verification, and integration. It becomes a defect when a load-bearing judgment
silently stays in a seat that cannot support it.

Separate two axes before routing:

- Size is the volume of bounded work. Work that is only large is decomposed
  into separately verifiable delegated units; volume alone never justifies
  moving it to a stronger seat.
- Difficulty is the reasoning the decision itself requires. Work that is small
  but hard is escalated even when it touches few files and cannot be
  decomposed.

When difficulty is not yet established, run a bounded read-only reconnaissance
before the first write-capable contract: read the named files, locate the
affected call sites, check the existing tests, and inspect working-tree and
dependency state. Change nothing during it, and bound it by what the routing
decision needs rather than by what a full investigation would want. A request
that reads as routine in prose is often not routine in the repository, so
decide the shape from observed code rather than from the request text alone.

Escalate the coordinator seat, instead of continuing, on observable signals:

- an architecture, interface, or data-model decision whose reversal would be
  expensive, or competing approaches where the wrong choice is costly to undo;
- authorization, secrets, cryptography, payment, privacy, or data migration as
  the central question rather than an incidental surface;
- concurrency, distributed state, cache coherence, or ordering as the defect
  mechanism;
- a cause that spans layers no single unit observed, or an existing design
  whose intent the coordinator cannot reconstruct from the code and its
  history;
- material ambiguity or contradiction in the requirement itself;
- delegated results that contradict each other on a load-bearing fact;
- the same contract failing twice, a premise the round was built on turning out
  false, a repair producing a new defect, or scope growing past what the round
  was contracted for.

Re-evaluate at every join gate, not only at intake. Difficulty that surfaces
after the first round is the ordinary case, and an intake judgment does not
license finishing a round whose own evidence has contradicted it.

A self-rated success probability may support the decision but does not replace
these signals, because it is an estimate produced with the same limits it is
meant to detect. Prefer the observable combination — unreconstructed design
intent, a migration with no stated rollback, two contradicting receipts — over
a number or a threshold.

Escalation is a stop, not a background upgrade. When the host cannot re-seat
the current session at a stronger tier, say so and hand off rather than
proceeding at the current seat. The handoff carries the goal, the observed
difficulty signal, verified facts with their anchors, what was already changed
and verified, the open question, and options already ruled out with their
reasons; it does not carry the accumulated transcript. Do not escalate work
that is merely large, do not escalate to avoid writing a bounded contract, and
do not report an escalation as completed work. Options already ruled out with
their reasons are written as a decision record when the choice binds later
units.

## Multi-Subagent Decomposition

For substantial work, record a compact work graph before delegation:

- `critical_path`: the next coordinator-owned step or delegated unit whose
  result is required before later decisions can be made;
- `parallel_units`: independent research, implementation, test, migration,
  documentation, or review units that do not block that next step;
- `coupling`: shared APIs, files, schemas, generated artifacts, decisions, or
  verification gates that constrain execution order;
- `execution_shape`: serial, parallel, or hybrid, with a short reason;
- `join_gate`: the coordinator check that reconciles results before dependent
  work, final verification, or user-facing claims.

Prefer a hybrid shape for large refactors: keep the immediate load-bearing
decision or tightly coupled core local or with one context-owning worker, while
launching other material independent units to separate subagents. Use multiple
read-only workers freely when their questions and evidence surfaces are
distinct. Use multiple write-capable workers only when their write sets and
generated outputs are disjoint and the host provides isolated workspaces or an
equivalent enforceable isolation boundary. Otherwise keep one shared-root
writer and parallelize read-only investigation, test design, review, or other
non-writing units.

A narrowly permitted third shape is disjoint generated-output writers in one
checkout. Use it only when every worker writes to a private per-unit
untracked/ignored output root, inputs are private materialized read-only copies,
no mutable cache or generated path is shared, concurrency is bounded, every unit
returns its own receipt, each unit's journal and scratch root is private with
foreign content in it a blocker, and the coordinator proves tracked-tree
cleanliness at each batch boundary. Record which confinement is host-enforced
and which is instruction-only. Without every condition, the
one-shared-tree-writer rule stands.

Include commit visibility in coupling analysis. An isolated worktree starts from
some committed state, not necessarily the coordinator's head: a host may create
it from the repository default, leaving the worker without the files, fixtures,
and line positions the contract describes and unable to tell a wrong contract
from a wrong workspace. Verify that base before the first isolated unit with a
read-only check reporting the workspace's resolved commit and ref decoration,
and re-verify when the isolation mechanism, host, or repository default changes.
State the expected base in every isolated unit's contract and require the worker
to echo the base observed; a mismatch is a coordinator blocker — supply the
correct base, materialize the inputs, or move the unit to the shared tree under
single-writer rules — never a worker-side workspace mutation. A unit that needs
another unit's uncommitted output is not independent and must run serially or
receive a coordinator-materialized input.
Avoid placing temporary worktrees below the repository root because glob-driven
tests, linters, formatters, and file counters can traverse the duplicate tree.
Expect repository-wide gates to fail or double-count while such a workspace
exists: do not run an authoritative gate in that window, and do not attribute a
failure observed in it to a worker's slice. Remove an isolation worktree
promptly after extracting and verifying its diff.

Each parallel unit needs its own mission, allowed paths, expected receipt,
budget, stop conditions, and verification responsibility. The coordinator must
continue meaningful non-overlapping local work after launch rather than
launching the immediate blocker and waiting reflexively. At the join gate,
verify each receipt, reconcile contradictions and interface assumptions, and
re-run the authoritative integrated gates on the combined bytes.

## Worker Contract Minimums

Every write-capable delegation contract should include:

- Mission: one sentence with the slice and expected outcome.
- Hard rules: allowed tools, commands, forbidden reads, forbidden git actions,
  and stop-as-blocker behavior.
- Verified facts: APIs, versions, local patterns, failure logs, environment
  constraints, invariants, measured versus derived values, source provenance,
  and unverified limits.
- Design contract: exact behavior, semantics, public names, or invariants that
  matter.
- Protected evidence: external parity tests, vendor artifacts, independently
  sourced fixtures, or other evidence the worker must not update, delete, or
  ignore to make the change pass.
- Numbered work items with done criteria.
- Editable file whitelist and explicit out-of-scope paths.
- Optional progress journal path.
- Fixed report sections: `FILES:`, `COMPILE:`, `DECISIONS:`, `BLOCKERS:`;
  add `DECISION-IMPACT:`, `DEVIATIONS:`, and `VERIFICATION BOUNDARY:` when
  decisions, challengeable constraints, or environment-specific proof are
  material, and `DIAGNOSIS:` for repair or investigation tasks.

If a worker needs a non-whitelisted file, broader command, credential,
permission, destructive action, or user decision, it must stop and report a
blocker instead of proceeding.

The same stop rule applies when evidence found during the task contradicts a
contract premise presented as verified. A worker may report the contradiction
and its anchors; it must not silently decide that the premise, external evidence,
or protected parity test is wrong. Revising the contract premise belongs to the
coordinator.

## Fact Inlining And Local Precedent

Before delegating implementation or repair, verify facts that would be expensive
or error-prone for a worker to rediscover:

- framework and API signatures;
- version-specific behavior;
- lifecycle, storage, or test-harness rules;
- test and runtime environment limits, accepted inputs, resource ceilings, and
  helper assumptions;
- local patterns to mirror;
- failing logs and observed-versus-expected differences;
- invariants that must not change.

Use local precedent as an anchor: point to the specific file or method pattern to
mirror. For repairs, name protected invariants such as test expectations,
coordinates, budgets, ticks, fixture semantics, public behavior, data shape, and
compatibility. If those invariants appear wrong, the worker reports a blocker;
it does not weaken them to pass.

Facts remain challengeable. Attach a cheap verification anchor when available,
and instruct the worker to report a mismatch rather than inventing a correction.
For a value calculated from measured inputs, include the assumptions and a
condition that would break the derivation; do not present it as a measured fact.

Before sending the contract, demote any coordinator inference, provisional
design bound, or untested brief clause out of `Verified facts`. Validate a brief
against the measured product or its own examples before treating delegate
failures as a capability signal; uniform failure across independent workers is a
reason to inspect the shared brief first, not proof that every worker lacks the
capability.

When protected artifact or parity evidence contradicts a contract premise, use
one coordinator acceptance checklist before another worker starts: rank the
authority for the claim, separate the observed mismatch from the correctness
inference, restore protected evidence, compare named sentinels rather than pass
counts, reconcile the round snapshot with the worker receipt, classify opaque
artifacts and their generator/inspection path, check command effects against the
editable whitelist, then rerun authoritative coordinator verification. Until
all applicable items are resolved, the round remains blocked.

Record that disposition under four headings so none of the evidence boundaries
is lost in summary:

- `authority`: observed disagreement versus correctness inference, with corpus,
  normative source, and implementation ranked for the claim;
- `protected_proof`: restored parity sentinel and named-test comparison;
- `attribution`: round snapshot versus receipt, opaque-artifact classification,
  authoritative generation plus semantic inspection, and command-effect
  whitelist;
- `reverification`: coordinator-run authoritative gates before any serializer
  repair is accepted.

After a repair round changes control flow, ordering, lifecycle, or guards, run a
corrections-complete read-only pass when risk warrants it. Give that pass one
line per applied correction, require verify-or-refute plus an inverse/symmetric
failure attack and a new-defect scan, and prefer an identity different from the
implementer and original finding author when available.

## Direct Coordinator Intervention

Delegation is the default, but direct coordinator edits are allowed when they
are narrow and disclosed:

1. Mechanical micro-fix: trivial, well-understood, and cheaper than a delegation
   round.
2. Transport failure fallback: the same fully specified delegation fails
   repeatedly for runner or forwarding reasons.
3. Measurement-driven diagnosis: temporary instrumentation is needed to collect
   evidence before deciding a fix.

Disclose every direct intervention in the summary, run normal verification, and
remove temporary diagnostics before final handoff or commit.

Direct intervention must be behavior-neutral or apply one already-proven
correction. If it introduces a new design choice, or the coordinator cannot
explain why the current behavior occurs, stop and write the design evidence or
delegate the bounded change instead of treating its small line count as a
micro-fix.

## Parallel-Writer Accident Protocol

The default in one shared working tree is one source-writing worker at a time.
Concurrent source writers are an advanced isolated-workspace shape: they require
separate worktrees or sandboxes, disjoint write and generated-output paths,
explicit merge order, and an integrated verification gate before any result is
accepted into the coordinator's tree. The only same-checkout exception is the
guarded disjoint generated-output shape defined above; it never permits
concurrent source edits. If a duplicate, stale, or unexpectedly overlapping
writer may have touched the same tree:

1. Stop launching new write work and cancel every unintended overlapping writer
   with the host's named task control. A warning-only loop is not containment.
2. Identify the one intended worker and every unexpected worker handle.
3. Inspect status, diffs, journals, and file timestamps or hashes when useful.
4. Do not discard unexpected diffs blindly.
5. Adopt useful changes only after they fit the contract and pass normal gates.
6. Revert or replace unsuitable changes after inspection.
7. Re-check that no post-gate mutation happened before declaring verification.
