# Coordinator Practices

Read this reference before selecting delegated model tiers, judging the coordinator's own capability fit, decomposing substantial work, setting or revisiting the goal and effort envelope, writing or auditing worker contracts, inlining facts and protected evidence, directly intervening, or handling multiple/overlapping writers.

## Frontier Coordinator And Model-Tier Loops

### Model Choice

<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a model for each delegated unit by capability and context fit, never by hard-coded name.**

- Only choose when the host allows it and the user has not fixed a model.
- Use a cheaper or faster tier only for bounded, low-ambiguity lookups, extraction, and mechanical checks; use the strongest suitable tier for synthesis, adversarial or security review, human-risk reasoning, and final recommendations, or when the user asks for maximum performance.
- Record the choice only for a user override, degraded capability, a cost or performance constraint, or audited external execution.
<!-- shared-contract:end model-tier-selection -->

### Token-Saving Loop

Good token-saving loops reduce repeated context, not proof. Prefer this loop:

1. The coordinator verifies and inlines the facts, invariants, file boundaries,
   and decision criteria that a worker would otherwise rediscover.
2. Each delegated unit receives a compact context digest, one question or work
   item, explicit allowed paths/tools, expected receipt, and escalation triggers.
3. The coordinator verifies load-bearing anchors, reconciles contradictions,
   and decides whether to close, split, retry with a narrower contract, or
   escalate to a stronger reasoning/context tier.
4. Later loop iterations send only the changed facts, unresolved blockers, and
   latest verified state instead of the full parent transcript unless full
   context is necessary and the reason is recorded.

Escalate instead of retrying a cheap delegate when it reports uncertainty, hits
a scope blocker, returns contradictory findings, fails the same contract twice,
or the unit turns out to need the strongest tier. Do not give every small worker
the top model, and claim no token, quality, latency, or reliability gain without
recorded metrics or review evidence.

## Goal And Effort Checkpoints

At first material delegation, put the user outcome, remaining acceptance gates,
planned rounds, and bounded optional-tooling allowance in the existing plan,
round ledger, or first contract. Use rounds/time if measured usage is unavailable;
label estimates. No separate artifact is required.

At joins, compare progress and cumulative effort with that envelope. Repeated
findings, an overrun, exhausted tooling allowance, or completed acceptance work
trigger a scope checkpoint before optional follow-up. Preserve authorized
in-flight work and essential repairs; budgets never certify broken work.
Batch optional proposals with impact, remaining effort, and a continue/trim/defer
recommendation. Ask only for additional scope, cost, or human-risk decisions;
autonomy does not authorize unlimited optional work or accept residual risk.

A further review after initial review and targeted correction needs a named
unresolved acceptance/safety defect, changed evidence, or authorized scope.
Repeated findings in one component call for diagnosis or artifact-owner
backtracking. On user-reported drift, state removed verification work, surviving
coverage, and open gaps; changing required proof belongs to the owning artifact.

## Coordinator Capability Fit

Separate size from difficulty using bounded read-only inspection of affected
code, call sites, tests, tree, and dependencies before the first write round.
Decompose large routine work. Escalate difficult load-bearing judgments even
when few files change; volume alone is not an escalation reason.

Reassess at each join. Observable difficulty signals include costly-to-reverse
architecture or data decisions; central authorization, privacy, payment, or
migration questions; concurrency/ordering defects; unexplained cross-layer
causes or design intent; ambiguous requirements; contradictory receipts; a
false premise; two failures of the same contract; repair-induced defects; or
scope exceeding the contract. Self-rated confidence does not replace evidence.

If the current seat cannot support the judgment, stop for a stronger seat.
When the host cannot re-seat this session, hand off the goal, observed signal,
anchored facts, changed/verified state, open question, and rejected options with
reasons. Exclude accumulated transcript and do not claim escalation completed
the work. Record rejected alternatives when they qualify under Durable Records.

## Multi-Subagent Decomposition

For substantial work, record the critical path, independent units, coupling
(files, interfaces, decisions, generated outputs), serial/parallel/hybrid shape
with reason, and coordinator join gate. Keep tightly coupled work with one
context owner; use multiple workers when material units are independent and
separately verifiable. Continue non-overlapping local work after dispatch.

One shared tree permits one source-writing worker. Concurrent source writers
require isolated workspaces or an equivalent enforceable boundary, disjoint
write/generated paths, explicit merge order, and integrated verification.
Read-only investigation and review may run alongside the writer.

The same-checkout generated-output exception requires all of: private per-unit
ignored/untracked output roots, private materialized read-only inputs, no shared
mutable cache or generated path, bounded concurrency, individual receipts,
private journals/scratch with foreign content a blocker, and tracked-tree clean
checks at baseline and every batch boundary. Record host-enforced versus
instruction-only confinement; absent an adequate boundary, use isolation or
one writer.

Verify an isolated workspace's resolved commit and ref decoration before the
first unit and after host/isolation/default-base changes. Put the expected base
in each contract and require its observed base in the report. Inlined facts
about the coordinator's tree describe the worker's only at a matching base.
A mismatch is the coordinator's blocker: supply the right base, materialize
inputs, or use a bounded patch handoff/shared-tree writer; the worker must not
switch its workspace. Units needing uncommitted predecessor output are serial
unless the coordinator materializes that input.

Keep temporary worktrees outside the repository: recursive gates may traverse
a duplicate tree. While one remains inside, suspend authoritative repository-wide
gates and do not attribute their failures to a slice. Remove temporary worktrees
promptly after extracting and verifying their work, within cleanup authority.
Use explicit command workdir or `git -C`, not the host's primary cwd; verify
checkout identity after host re-seating.

## Worker Contract Minimums

Use `delegation-contracts.md` for the single contract template and variants.
For multiple units, give each its own mission, paths, receipt, effort bound,
stop conditions, and verification responsibility. At the join, reconcile
receipts and shared assumptions before integrated verification.

## Fact Inlining And Local Precedent

Inline correctness-critical APIs, versions, local patterns, failure logs,
environment limits, and invariants with anchors. Label measured, source-read,
and derived claims; derived values need assumptions and a break condition.
Separate specification invariants from configurable defaults and local choices.
Keep coordinator inference and provisional design bounds outside Verified facts.
Workers report contradictions rather than weaken protected evidence.

Uniform worker failure calls for checking the shared brief against measured
behavior and examples before blaming capability. If protected corpus/parity
proof contradicts a premise, block acceptance until the coordinator ranks
source authority, separates observation from inference, restores protected
proof, compares named sentinels, reconciles snapshots with reports, classifies
opaque artifacts, checks command effects, and reruns authoritative gates.
The detailed proof rules live in `verification-and-review.md`.

## Direct Coordinator Intervention

Direct edits are allowed for a mechanical micro-fix, repeated transport failure
on a fully specified task, temporary measurement-driven diagnosis, a fully
diagnosed bounded repair, or coordinator-only verification. They must be
behavior-neutral or apply an already-proven correction. Small line count does
not authorize new design, unresolved causes, or human-risk choices.

Disclose reason, scope, why delegation was not used, and verification; remove
temporary diagnostics. Apply normal review/gates. After a deep invariant,
control-flow, ordering, lifecycle, or guard correction, use a focused read-only
corrections pass when risk warrants: verify/refute each correction, attack its
inverse or symmetric failure, and inspect new defects. Prefer a reviewer other
than the implementer/finding author; keep it inside material acceptance risks.

## Parallel-Writer Accident Protocol

For overlapping, duplicate, or stale writers, use the quarantine and recovery
procedure in `recovery-and-monitoring.md` before accepting or discarding diffs.
