---
version: 5.0.0
name: vibe-debug
description: Use when debugging or repairing existing features from rough agent-assisted coding reports, regressions, failed prior fixes, repeated "still broken" feedback, source-only debugging stalls, unobserved runtime state, tool or automation failures, environment-specific failures, runtime artifact mismatches, security boundary surprises, or fixes that feel wrong.
---

# Vibe Debug

## Overview

Turn rough bug reports into verified repair work. Preserve the user's wording as
product evidence, then translate it into observable symptoms, expected
behavior, unknowns, proof paths, and closure criteria before changing code.

This skill is self-contained. Use useful project rules, docs, tools, and
available skills when they clearly apply, but do not require any other skill to
debug, fix, verify, or hand off the issue.

For recurrent symptoms observable only in the user's runtime, retained probes
are exceptional: explicit opt-in, disabled by default, bounded and privacy-safe,
with a countable comparable discriminator. After a verified fix, preserve a
still-green prior discriminator and open a new cause layer instead of rewriting
the closed cause.

## When to Use

Use this for existing-feature repair when the user reports any of these:

- "Still broken", "not fixed", "looks wrong", "feels wrong", or similarly rough
  feedback after real use.
- A regression, failed previous fix, repeated symptom, environment-specific
  behavior, stale runtime artifact, tool failure, or automation failure.
- A bug where the first report is an example rather than a full reproduction.
- Debugging is drifting into broad source reading, repeated patching, or
  approach changes while runtime ordering, artifacts, cleanup, or environment
  state remains unobserved.
- A fix that might affect existing behavior, contracts, state, permissions,
  artifacts, lifecycle, or user-visible output.

Examples are not boundaries. Name the abstract dimension before the concrete
domain example: UI/web, auth origin, asset path, encoding, worker, deploy
artifact, animation, or async cleanup. Do not turn that domain into a universal
requirement for unrelated bugs.

## When Not to Use

- Greenfield feature work with no existing behavior or reported symptom.
- Pure review cycles where an active review workflow is already sufficient.
- General commit-only work, history rewrite, push, cleanup, or release decisions
  outside debug/fix closure. Debugging leaves verified changes uncommitted unless
  the current user explicitly asks for a commit.
- One-line mechanical edits where no symptom, regression, or existing behavior
  is at stake.

## Core Rule

The user's report is valuable evidence of experience, not a verified root
cause. Investigate available code, tests, logs, screenshots, docs, artifacts,
history, and tool output before asking questions. Ask only questions that change
the fix, proof path, risk acceptance, or current-scope closure.

When the user reports a concrete runtime regression during another workflow or
while adjacent findings are pending, make that regression the exclusive primary
symptom until it is fixed, not reproduced, deferred, accepted as residual, or
blocked. Record the primary symptom, reproduction or first failing proof,
root-cause hypothesis, minimal patch envelope, positive sentinel, negative
sentinel, and last verified checkpoint. Adjacent findings stay ledger-only and
must not enter the same patch unless evidence proves they share the same root
cause and verification path.

Use probes only when they provide better proof than more static work. First run
bounded triage: nearest code, relevant tests, existing logs, artifacts, and the
expected-behavior source. After triage, propose the smallest diagnostic probe or
equivalent runtime observation before changing behavior again when multiple
live-state hypotheses remain, static proof would sprawl across interacting
surfaces, evidence contradicts the original approach, or the next source-only
patch would be a guess.

Stop before implementation when the current issue lacks any of these:

- A reproducible symptom, isolation proof, source trace, or exact manual proof
  path.
- An authoritative expected behavior source.
- A verification path that can observe the claimed fix.
- A representative observation regime for any claimed cause, or an explicit
  statement of why the fixture/runtime conditions differ and keep the cause
  unproven.
- Current-scope closure criteria for each reported symptom.

Explain blockers in user-impact terms: what the user could still see, lose,
misconfigure, trust incorrectly, or be unable to verify.

## Visible Output And Debug Ledger

For a simple reproduced bug with one symptom and one credible proof path, report
symptom, expected behavior, verified cause, fix, and proof directly. Do not add a
multi-row ledger merely because debugging occurred.

Use the visible debug ledger when diagnosis is recurrent, multi-symptom,
multi-environment, long-running, interrupted, or dependent on a user/runtime
retest. In that branch, keep one row per unresolved symptom, hypothesis, tool
failure, or closure decision and preserve the primary symptom, reproduction,
proof path, status, last verified checkpoint, and next discriminator. A narrow
question is not a substitute for the applicable current-scope record.

If the reported tool or artifact is absent, keep evidence prompt-only, record the
missing artifact as the blocker, and do not substitute a nearby fixture merely
because it shares a domain term.

## Delegated Diagnosis

When several independent hypotheses each need bounded read-only investigation
and the host exposes a delegation or sub-agent capability, fan the
investigations out instead of reading everything serially. The fan-out may run
as ad-hoc sub-agent calls or as one scripted orchestration run: a host
mechanism that runs the investigators under a single deterministic,
independently recorded run and returns their results. Do not require a
specific host orchestration tool.

Give each delegated unit one hypothesis-shaped question and a read-only
boundary: inspect code, tests, logs, artifacts, and history, and return
evidence with sources suitable for the debug ledger. Include a compact budget:
deliverable, hypothesis, maximum elapsed time, allowed paths, context digest,
verification receipt, and stop-and-return conditions. Three empty waits for the
same unit require a checkpoint or split decision, not repeated no-change
notifications. Probes that mutate state,
temporary instrumentation, user-environment retests, edits, and ledger
ownership stay with the coordinator. A delegated finding enters the ledger as
recorded evidence for a hypothesis, not as the proven cause; the disconfirming
check and closure decisions still run in this workflow.

When the host lets you choose a delegated model and the user has not explicitly
fixed one, choose a fit-for-purpose model per hypothesis by capability and
context fit, not by hard-coded model name. Use a cheaper or faster model for
bounded file/log lookup or mechanical reproduction checks only when lower
capability is quality-neutral or the user prioritizes cost/latency. Bias upward
to the strongest suitable reasoning/context tier available for contradicted
prior fixes, cross-layer diagnosis, security/data-loss risk, environment-sensitive
behavior, final cause selection, contradiction resolution, or other
judgment-heavy hypotheses, especially when the user asks for maximum
performance. Do not spend the top model on every narrow reader, and do not
downshift solely to save tokens when the investigation needs stronger reasoning.
Record model choice only for an explicit user override, degraded capability,
cost/performance constraint, or audited external execution.

## Self-Review And Repository Closure

After implementing and verifying a repair, run a self-review before final repair
claims. When a matching review workflow is visible and applicable, use it;
otherwise perform a self-contained review of the repair slice: ledger closure,
minimal patch envelope, preserved behavior, verification proof, artifact
freshness, generated or temporary surfaces, and user-visible summary. Resolve
material findings and rerun affected proof before closure, or record the
remaining item as `deferred`, `accepted-residual`, or `blocked`.

Verified implementation closure leaves repair-owned changes in the working tree
unless the current user explicitly asks for a commit. Invocation, successful
proof, and tracked status do not select history work. When a commit is explicitly
selected, hand the verified repair scope and evidence to the commit-execution
workflow; do not duplicate staging or message procedures here.

## Reference Routing

Read these bundled references only when their details are needed:

- `references/debug-ledger.md` - ledger template, closure statuses, and
  repeated-attempt handling.
- `references/source-routing.md` - source-of-truth routing and tool-confidence
  ledger.
- `references/state-space-matrix.md` - state-space dimensions for static,
  dynamic, environment, representation, and lifecycle bugs.
- `references/probe-escalation.md` - temporary probes, traces, logs,
  assertions, runtime observations, and cleanup.
- `references/verification-handoff.md` - artifact freshness,
  verification-degradation, and user retest contracts.
- `references/continuity-and-recurrence.md` - resume handling and repeated-class
  self-review.

## Workflow

Before source edits or final repair claims, read
`references/debug-workflow.md`. That reference owns the detailed
inspect/reproduce/instrument/repair/verify/handoff loop and the proof
requirements inside the loop.

## Stop Conditions

Stop and report a blocker or ask the smallest plan-changing question when:

- Expected behavior has no source and the difference affects product behavior,
  data, permissions, security, external contracts, or user experience.
- The symptom cannot be reproduced, isolated, source-traced, or handed off with
  exact manual proof.
- A repeated report arrives and you cannot explain why the prior fix failed.
- Two consecutive repair attempts under the same cause hypothesis leave the
  acceptance discriminator unchanged, and neither the discriminator nor the
  observation regime has been revalidated.
- A needed source, artifact, tool, or runtime path is unavailable and no
  alternate proof is credible.
- A needed diagnostic probe, trace, log, assertion, or runtime observation is
  unavailable and no source trace or alternate proof can observe the unknown.
- A current-scope existing-behavior dimension remains `unknown`.

## Finish Gate

Before ending:

- Every current-scope ledger item has status `fixed`, `not-reproduced`,
  `deferred`, `accepted-residual`, or `blocked`.
- Every `fixed` item has proof and artifact freshness when runtime artifacts are
  involved.
- Temporary probes are removed before finishing, or any retained diagnostic
  surface is intentional, disabled or bounded, documented, and verified not to
  expose secrets or user data.
- Every preserved or intentionally changed behavior dimension has verification
  or an explicit residual.
- Skipped or degraded checks are reported as non-proof with next action.
- User-side retests, when needed, include exact steps and expected observations.
- Implemented repairs were self-reviewed before closure, or the missing review
  is recorded as blocked or explicitly skipped by the user.
- Verified repair-owned changes are reported as uncommitted unless the current
  user explicitly selected a commit; other history and release operations remain
  separately consent-bound.
