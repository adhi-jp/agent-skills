# Coordinator Practices

Read this reference before selecting delegated model tiers, decomposing substantial work, writing or auditing worker contracts, inlining facts and protected evidence, directly intervening, or handling multiple/overlapping writers.

## Frontier Coordinator And Model-Tier Loops

When the host exposes both high-capability frontier models and cheaper, faster,
or previous-generation models, treat model choice as part of the delegation
contract. Keep decomposition, non-delegable decisions, final synthesis,
verification interpretation, review dispositions, and user-risk choices with the
coordinator or the strongest suitable reasoning/context tier available. Use
token-efficient delegated models for bounded work only when lower capability is
quality-neutral or the user has prioritized cost or latency.

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
  add `DIAGNOSIS:` for repair or investigation tasks.

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

The default in one shared working tree is one write-capable worker at a time.
Concurrent writers are an advanced isolated-workspace shape: they require
separate worktrees or sandboxes, disjoint write and generated-output paths,
explicit merge order, and an integrated verification gate before any result is
accepted into the coordinator's tree. If a duplicate, stale, or unexpectedly
overlapping writer may have touched the same tree:

1. Stop launching new write work and cancel every unintended overlapping writer
   with the host's named task control. A warning-only loop is not containment.
2. Identify the one intended worker and every unexpected worker handle.
3. Inspect status, diffs, journals, and file timestamps or hashes when useful.
4. Do not discard unexpected diffs blindly.
5. Adopt useful changes only after they fit the contract and pass normal gates.
6. Revert or replace unsuitable changes after inspection.
7. Re-check that no post-gate mutation happened before declaring verification.
