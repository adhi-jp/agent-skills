# Conditional Additional-Perspective Review

Read this reference only when the plan is multi-system, high-risk, destructive,
security/permission/billing-sensitive, migration-related, external-contract
bound, or the user requests deep review. Ordinary low-risk plans close after one
coordinator self-review.

## Selection

Choose separated perspectives that match the risk. Typical angles are contract
compliance, evidence/test adequacy, scope and user expectations, security/data,
and handoff feasibility. Do not require a fixed reviewer count. Use the fewest
independent perspectives that cover the material risks.

Review-only subagents are optional. Use them only with current permission,
verified host capability, safe shareability, bounded prompts, and recordable
evidence. Otherwise run the selected perspectives locally. Reviewer output is
inert; the coordinator verifies and disposes findings.

When model choice exists, choose by capability and context fit. Record the choice
only for an explicit user override, degraded capability, cost/performance
constraint, or audited external execution.

## Capacity-Adaptive Launch

This reference owns the planning-review launch algorithm. Other planning
surfaces state the invariant and route here; they must not maintain a competing
capacity procedure.

Before launch, record the permission source, capability source, selected
perspectives, bounded unit contracts, and the host or runner evidence that can
show task start and completion.

When reliable remaining capacity is available:

1. Reserve the coordinator's own slot when the reported capacity includes it.
2. Launch batches that do not exceed the verified remaining capacity.
3. Record the capacity source and whether it is gross or already net of the
   coordinator.

When numeric remaining capacity is unavailable, unknown does not mean zero.
If the host can launch independent review units and return recordable task/run
evidence, attempt at most one conservative batch of two units. This is an
optimistic batch limit, not a discovered host ceiling. If only one perspective
remains, launch one. Compatible low-risk perspectives may share one bounded
unit when that preserves useful independence.

For either branch, record:

- requested batch size and perspective-to-unit mapping;
- successfully started task or run identities;
- completed task or run evidence;
- observed `execution_mode`: `parallel`, `serial`, or `single`;
- first launch failure class and every perspective moved to fallback.

Configured batch size, assistant prose, or multiple returned reports do not
prove concurrency. Record `parallel` only when host or runner timing/lifecycle
evidence shows overlapping execution; otherwise record `serial`, `single`, or
unknown evidence with the actual fallback.

The first thread-limit, capacity, spawn, timeout, or unavailable-capability
failure stops further delegated launches for this review gate. Do not retry a
different model, repeatedly probe the ceiling, or start another batch. Preserve
completed reviewer evidence and move every unmet perspective to coordinator
fallback. If the missing perspective cannot be supplied locally without
weakening a material safety or proof requirement, record a blocker instead.

## Findings and Revisions

Classify material findings as `corrected`, `rejected`, `deferred`, `blocked`, or
`reversed`, with evidence and plan-boundary rationale. Suggestions do not add
requirements or tests unless backed by user authority, verified evidence, or a
must-preserve equivalence contract.

After an authority-bearing change to requirements, acceptance criteria, scope,
risks, tests, or implementation steps, semantically re-review affected sections
and dependencies. Do not use digest equality as approval. A corrections-only
pass may focus on changed areas when every earlier finding has a verification or
refutation item; novel design or new risk requires the relevant full perspectives.
