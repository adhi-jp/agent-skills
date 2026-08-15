---
version: 2.5.0
name: skill-quality
description: Use when making evidence-driven quality decisions for a skill package or its evals from benchmark results, grader feedback, review comments, session-history patterns, trigger failures, or quality regressions; especially when deciding what to change, what not to change, how to update assertions, or whether to rerun skill evals.
---

# Skill Quality

## Overview

Improve skills by translating observed failures into small, testable contract
changes. A good skill change explains when the behavior applies, what future
agents must do, how evals will catch regressions, and what evidence proves the
change helped.

This skill governs skill and eval quality decisions. It does not authorize
release preparation, version bumps, commits, generated workspace commits, or
unrelated package rewrites.

## Core Decision Record

Start from the failure signal, not from a preferred rewrite. Collect only the
evidence needed for the current decision and label implementation-affecting
claims as `Primary source`, `Local investigation`, `Unproven`, or `Accepted
risk`. Old session memory, a plausible fix, a single pass, or reviewer preference
is not proof.

Before proposing a tracked skill or eval change, record:

- the evidence map and any unsupported claims;
- one reusable contract delta naming the behavior and degeneration;
- the smallest owning surfaces and important surfaces that must not change;
- the current proof status and what needs a later authorized run or external
  check.

A no-change decision may stay concise. Name the existing rule, eval, or artifact
that already owns the mechanism and keep unsupported proof claims explicit. Do
not mutate artifacts merely to make the decision look substantial.

When an active workflow is primarily creating a requirements artifact,
implementation plan, review result, repair, or other deliverable, that workflow
keeps primary authority. Apply this skill as the quality lens only where
evidence is being translated into future skill behavior, eval discrimination,
or proof requirements.

## Failure Classification

Before treating a surprising, repeated, tool-related, artifact-related, or
transcript-contradicted failure as a skill defect, classify it as one of:

- skill contract gap;
- reference reachability or answer-time salience gap;
- eval prompt, assertion, fixture, or delivery-mode gap;
- measurement, recording, or proof-transport gap;
- invocation, authority, or represented-workspace mismatch;
- grader-boundary defect;
- run variance or noise.

Fix the owning boundary. Do not keep tightening skill prose when the evidence
points elsewhere.

When the decision depends on session history, relayed benchmark summaries,
delegated analysis, represented workflow state, public structured projections,
runner affordances, or artifact capture, read
`references/evidence-and-failure-classification.md` before attributing a cause.
That reference owns the detailed evidence-universe, authority, session-ledger,
and proof-transport rules.

Treat `authority-state collapse` as a subtype of invocation, authority, or
represented-workspace mismatch when evidence shows that distinct states were
silently promoted into one another. Separate the selected deliverable, action
authority, artifact lifecycle state, bound identity, evidence tier, minimum
proof, and active stop condition. Reading the right skill or having permission,
capability, relevance, a conventional path, or tracked status does not prove
that a later action or lifecycle transition was selected. Fix only the missing
owner boundary; preserve existing rules and evals that already govern other
transitions.

## Failure To Contract

Before changing skill text or eval behavior, write a one-sentence contract
delta:

```text
When <trigger/context>, the skill should <observable behavior>, because <stable reason>, and it must not <known degeneration>.
```

Use that sentence to decide which files change. If the failure cannot be stated
as an observable contract, keep investigating instead of adding prose.

Name the abstract dimension behind the example, such as `current-slice blocker`,
`artifact freshness`, `benchmark completeness`, or `local-anchor preservation`.
Keep a concrete phrase or fixture only as labeled evidence when useful; do not
copy grader wording or prompt literals into standing guidance.

## Contract Value Test

Before retaining an existing field, ledger, fixed output shape, hash, mandatory
review count, or eval assertion, ask whether it prevents a demonstrated failure,
provides state that cannot be reconstructed at the point of use, feeds a real
machine consumer, or makes a material acceptance criterion observable. Existing
prose and a currently passing assertion are not sufficient retention reasons.
When none applies, remove the contract, make it risk-conditional, or keep it
internal, then preserve the underlying safety/correctness invariant with a
replacement eval or an explicit accepted loss of discrimination.

## Change Selection

Make the smallest coupled change that closes the contract gap:

- `SKILL.md`: trigger-independent invariants, scope boundaries, stop gates, and
  short decision rules that must remain visible whenever the skill is active.
- `references/`: conditional procedures, detailed checklists, domain variants,
  extensive examples, tool contracts, and reusable research whose always-on
  presence would obscure the core contract.
- `scripts/` or structured gates: deterministic repeated work or constraints
  that documentation alone has repeatedly failed to enforce.
- `evals/<skill-name>/evals.json`: observable pressure and negative cases for the
  changed behavior.
- `README.md` and `CHANGELOG.md`: only when they describe the changed behavior or
  repository-visible contract.

Preserve modality, exceptions, exact paths, commands, field names, local anchors,
absence statuses, and proof boundaries. Do not bump `version` fields without an
explicit release instruction; record notable work under `## [Unreleased]`.

## SKILL.md Context Budget And Reference Boundary

Treat instruction reachability and `SKILL.md` growth as quality surfaces. After
a skill change, inspect the whole package rather than appending another local
rule automatically.

Refactor content out of `SKILL.md` when accumulated conditional procedures,
long checklists, domain-specific variants, repeated examples, tool/API detail,
or historical rationale make activation, scope, stop gates, or load-bearing
invariants harder to find. Leave a concise invariant in `SKILL.md` and add an
explicit applicability rule that tells the agent exactly when the reference
must be read.

Do not optimize for a fixed line or word count. Do not move a load-bearing
always-applicable invariant merely to shorten the file, and do not create a
reference that is never routed from `SKILL.md`. Before completing the refactor:

- audit the body and existing references for duplicate or contradictory
  authority;
- preserve the original obligation, exceptions, proof path, and failure
  behavior;
- update links, coupled README/changelog text, and targeted eval pressure when
  the routing or behavior contract changed;
- keep narrow anecdotes and session history out of standing guidance unless
  generalized and independently supported.

A size-only cleanup does not prove behavior improved. If no authorized eval is
run after a behavior or reachability change, report that effect as `Unproven`.

## Eval Quality And Proof

Before changing eval prompts, assertions, fixtures, suite coverage, proof paths,
or benchmark interpretation, read `references/eval-quality-and-proof.md`. It
owns iteration boundaries, partial-versus-closing runs, delivery-mode and grader
observability, common-assertion applicability, fixture delivery, compaction,
byte-level adjudication, result analysis, and honest aggregate reporting.

Keep these invariants visible:

- Use the repository eval runner; never hand-run and self-grade a cell.
- Keep the official aggregate unchanged when recording a diagnostic corrected
  reading.
- A run predating the latest relevant skill, assertion, prompt, fixture, or
  proof-path edit is not closing evidence for that state.
- Generated eval workspaces are not committed unless explicitly requested.
- Do not launch a fresh eval run without explicit user authorization.

## Diagnostic And Safety Findings

When the signal is a security analyzer, policy scanner, trust review,
credential-handling warning, or another source-boundary-sink finding, read
`references/diagnostic-and-safety-findings.md` before choosing prose. Prefer
by-construction prevention at the earliest owning boundary, keep exactness and
preservation subordinate to safety controls at sensitive sinks, and do not claim
host enforcement or analyzer clearance without the corresponding authoritative
check.

## Reference Routing

Read only the references whose applicability condition matches, except that the
final closure audit is mandatory for tracked changes:

- `references/evidence-and-failure-classification.md`: session history, relayed
  runs, delegation, represented state, authority, structured public output, or
  artifact proof transport.
- `references/eval-quality-and-proof.md`: any eval mutation, benchmark analysis,
  rerun decision, aggregate claim, or suite compaction.
- `references/diagnostic-and-safety-findings.md`: security, trust, credential,
  privacy, or policy findings.
- `references/session-patterns.md`: historical rationale or when a proposed
  change risks making a skill larger without making it better.
- `references/final-quality-checks.md`: before finalizing or committing any
  tracked skill or eval change.

References carry conditional detail, not weaker authority. When a route applies,
its requirements are part of this skill's contract.

## Closure

Before reporting completion for a tracked change:

1. Run a contract-collision audit across activation, applicability, workflow,
   output contracts, examples, references, evals, README, and changelog text.
2. Confirm the final proof occurred after the last relevant edit, or state the
   exact absence status (`evals not run`, `Unproven`, or equivalent).
3. Keep generated workspaces, iteration ledgers, failed hypotheses, and local run
   directories out of committed changelog prose.
4. Read and apply `references/final-quality-checks.md`.
