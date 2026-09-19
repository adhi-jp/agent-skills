# Conditional Additional-Perspective Review

Read this reference only when the plan is multi-system, high-risk, destructive,
security/permission/billing-sensitive, migration-related, external-contract
bound, or the user requests deep review. Ordinary low-risk plans close after one
coordinator self-review.

## Selection

Choose the fewest separated perspectives that cover the material risks, such as
contract compliance, evidence and test adequacy, scope and user expectations,
security and data, and handoff feasibility. There is no fixed reviewer count.

Run the perspectives locally unless review-only subagents have current
permission, verified host capability, plan content that is safe to share,
bounded prompts, and host or runner evidence that can show each task started and
completed.

## Launching Delegated Reviewers

- With a verified remaining-capacity figure, reserve the coordinator's own slot
  when the figure includes it, and launch no more units than remain.
- Without one, unknown capacity is not zero: launch at most one batch of two
  units, or one when only one perspective remains. Two is a conservative limit,
  not a discovered host ceiling. Compatible low-risk perspectives may share one
  bounded unit.
- The first thread-limit, capacity, spawn, timeout, or unavailable-capability
  failure ends delegated launches for this gate: no retry with another model, no
  probing for the ceiling, no further batch. Keep completed reviewer results and
  run every unmet perspective locally, or record a blocker when the local
  substitute would weaken a material safety or proof requirement.
- Record, for each perspective, whether it ran delegated with its task identity
  or locally, and any launch failure. Requested batch size, assistant prose, or
  several returned reports do not prove parallel execution; claim it only when
  host timing shows overlap.

## Findings and Revisions

Classify material findings as `corrected`, `rejected`, `deferred`, `blocked`, or
`reversed`, with evidence and a plan-boundary rationale. A suggestion adds a
requirement or test only when backed by user authority, verified evidence, or a
must-preserve equivalence contract.

After an authority-bearing change to requirements, acceptance criteria, scope,
risks, tests, or implementation steps, semantically re-review the affected
sections and their dependents. A corrections-only pass may focus on changed
areas when every earlier finding has a verification or refutation item; a novel
design or new risk needs the relevant full perspectives.
