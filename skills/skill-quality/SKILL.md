---
version: 2.9.0
name: skill-quality
description: Use when making evidence-driven quality decisions for a skill package or its evals from benchmark results, grader feedback, review comments, session-history patterns, trigger failures, or quality regressions; especially when deciding what to change, what not to change, how to update assertions, or whether to rerun skill evals.
---

# Skill Quality

## Overview

Turn observed skill or eval failures into small, testable contract changes,
and decide what not to change. This skill does not authorize release
preparation, version bumps, commits, committing generated workspaces, or
unrelated package rewrites. When another workflow owns the primary deliverable
(a spec, plan, review, or repair), that workflow keeps authority; apply this
skill only where evidence becomes future skill behavior, eval pressure, or
proof requirements. Each reference below is mandatory when its read-when
condition matches.

## Core Decision Record

Start from the failure signal, not from a preferred rewrite. Collect only the
evidence the decision needs and label implementation-affecting claims
`Primary source`, `Local investigation`, `Unproven`, or `Accepted risk`. Old
session memory, a plausible fix, a single pass, a relayed summary, or reviewer
preference is not proof.

Before proposing a tracked skill or eval change, state:

- the evidence map and any unsupported claims;
- one contract delta: `When <trigger/context>, the skill should <observable
  behavior>, because <stable reason>, and it must not <known degeneration>.`
  If the failure cannot be stated this way, keep investigating instead of
  adding prose;
- the smallest owning surfaces, and the surfaces that must not change;
- the proof status and what needs a later authorized run or external check.

A no-change decision may stay short: name the existing rule, eval, or artifact
that already owns the mechanism. Do not mutate artifacts to make a decision
look substantial.

Name the abstract dimension behind an example, such as `current-slice
blocker`, `artifact freshness`, or `benchmark completeness`. Do not copy
grader wording or prompt literals into skill text or self-authored assertions;
keep a concrete phrase only as a labeled example.

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

Fix the owning boundary. Stop tightening skill prose when the evidence points
elsewhere, when repeated wording-only edits leave the targeted failure
unchanged, or when the same failure moves to another case after each targeted
fix. A moving failure is one mechanism, not per-case gaps: if repeated runs
show only low-frequency scatter, classify it as run variance, prompt or runner
leakage, or measurement noise and stop editing prose; if they show a stable
mechanism, fix its broad owner once.

Two subtypes recur:

- `authority-state collapse`: distinct states were silently promoted into one
  another. Separate the selected deliverable, action authority, artifact
  lifecycle (create, track, stage, commit, release-note, publish, execute),
  bound identity, minimum proof, and active stop condition. Permission,
  capability, relevance, a conventional path, or tracked status does not
  select the next transition. Fix only the missing owner and leave skills that
  already govern the transition unchanged.
- `delivery-mode reclassification`: a response-only or supplied-state prompt
  was answered as a read-only, blocked, or chat-only phase, or expectations
  demand reads, writes, or commits the prompt forbids. Fix the owning boundary:
  the prompt's mode marker, the expectation wording (the action the response
  describes), or a package rule that keeps the phase's obligations under
  response-only delivery. The runner's `validate` delivery-mode warnings flag
  the expectation side.

Read `references/evidence-and-failure-classification.md` when the decision
depends on session history, relayed or delegated analysis, represented
workflow state, structured public output, runner affordances, or artifact
capture.

## Contract Value Test

Before retaining an existing field, ledger, fixed output shape, hash,
mandatory review count, or eval assertion, ask whether it prevents a
demonstrated failure, provides state that cannot be reconstructed at the point
of use, feeds a real machine consumer, or makes a material acceptance
criterion observable. Existing prose and a currently passing assertion are not
retention reasons. When none applies, remove it, make it risk-conditional, or
keep it internal, and preserve the underlying safety or correctness invariant
with a replacement eval or an explicit accepted loss of discrimination.

## Improvement Report Intake

An improvement report from earlier work is evidence, not a change list.
Accept, narrow, park, or reject each proposal on its own; a proposal without
a demonstrated failure that a capable agent actually makes is not accepted
because the report is confident. Apply the contract value test per proposal,
and prefer editing or replacing an existing rule to adding one. An addition
to an always-loaded file names what it replaces or deletes, or cites the
evidence that no existing rule covers the failure; a batch of proposals that
only adds is itself a signal to consolidate first. Report back which
proposals were applied, narrowed, parked, or rejected, so the maintainer sees
the discarded ones. Read `references/improvement-report.md` when writing such
a report or applying one.

## Change Selection

Make the smallest coupled change that closes the contract gap:

- `SKILL.md`: invariants, scope boundaries, stop gates, and short decision
  rules that must be visible whenever the skill is active.
- `references/`: conditional procedures, checklists, domain variants,
  examples, and tool contracts, each routed from `SKILL.md` with an explicit
  read-when condition.
- `scripts/` or structured gates: constraints that documentation alone has
  repeatedly failed to enforce.
- `evals/<skill-name>/evals.json`: discriminating pressure for the changed
  behavior, in the same change set.
- `README.md` and `CHANGELOG.md`: only when they describe the changed
  behavior. Record notable work under `## [Unreleased]`; never bump `version`
  without an explicit release instruction.
- frontmatter `description`: trigger conditions only, never workflow steps.

When moving, condensing, or restating rules, preserve modality, exceptions,
exact paths, commands, field names, local anchors, absence statuses, and proof
boundaries; then audit the body, references, evals, README, and changelog for
duplicate or stale authority, and add eval pressure for the moved rule's
reachability and for over-compression.

`SKILL.md` size is a quality surface: every always-loaded word costs salience
and eval tokens. Move conditional detail out when it hides activation, scope,
stop gates, or load-bearing invariants, and delete rules that fail the
contract value test, repeat another statement in the package, or only record
session history. Do not move a load-bearing always-applicable invariant out
merely to reach a size target. Promote a single sampled case, or a reference
rule after one miss, into `SKILL.md` only on multiple independent evidence or
user-approved scope, and then only as one concise invariant.

When a `with_skill` regression lands on rules the skill still states but
generated or shared blocks now push down the file, test placement before
adding a contract: a minimal relocation or a one-sentence restatement of the
obligation near the top, never a hand edit of the generated blocks, checked by
an authorized partial diagnostic on the regressed cases, with variance and
grader causes kept open. Revert a restatement the diagnostic does not move and
report the placement question to the maintainer instead of trying another
wording.

A size-only cleanup does not prove behavior improved; without an authorized
post-edit run, report the behavioral effect `Unproven`.

## Eval Quality And Proof

Read `references/eval-quality-and-proof.md` before changing eval prompts,
assertions, fixtures, or suite coverage, and before interpreting a benchmark
or deciding on a rerun. Validate, run, grade, and report evals only through
`skills/skill-eval/scripts/eval_runner.py` as the `skill-eval` skill defines.
Always:

- never hand-run and self-grade a cell;
- never launch a fresh eval run without explicit user authorization;
- a run predating the latest relevant skill, assertion, prompt, fixture, or
  proof-path edit is not closing evidence for that state;
- keep the official aggregate unchanged when recording a diagnostic corrected
  reading;
- do not commit generated eval workspaces unless explicitly requested.

## Diagnostic And Safety Findings

For a security analyzer, policy scanner, trust review, credential-handling
warning, or another source-boundary-sink finding, read
`references/diagnostic-and-safety-findings.md` before choosing prose.

## Closure

Before reporting a tracked change complete:

1. Audit the changed rule against activation, workflow, output contracts,
   examples, references, evals, README, and changelog text for stale or
   contradictory obligations.
2. Confirm the cited proof ran after the last relevant edit, or state the
   exact absence status (`evals not run`, `Unproven`, or equivalent).
3. Keep changelog text to the final durable behavior, validation, and honest
   proof status; iteration ledgers, intermediate scores, failed hypotheses,
   and local run directories stay out.
