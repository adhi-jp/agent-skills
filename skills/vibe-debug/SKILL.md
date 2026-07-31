---
version: 4.0.0
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
  outside debug/fix closure. A scoped local closure commit is part of verified
  implementation closure unless the user explicitly disables it or project rules
  forbid it, but push, amend, rebase, release, destructive cleanup, and version
  changes still need exact consent.
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

## Minimum Visible Output

Keep the workflow visible even when the immediate answer is short, blocked,
refuses an unsafe shortcut, has no local files to inspect, or handles only
debug/fix closure such as repository history. Do not replace the ledger with
general advice or a promise to fill it in later.

Before asking a narrowing question, stopping, delegating, or handing a check to
the user, include a compact current-scope record:

- Current slice: preserve the user's wording, then state the observable
  behavior or operation decision, expected source or missing source, unknowns,
  proof or preflight path, and closure criteria.
- Ledger: one row per unresolved symptom, hypothesis, failed tool decision, or
  closure decision. Use the debug-ledger fields when the row is a repair
  symptom. When repair is already verified and only repository mutation or
  cleanup remains, do not reopen the repair; record a closure-decision row with
  source evidence, owned and ambiguous paths, affected history/index state,
  required consent, preflight path, and status.
- Claim labels: when a decision depends on disputed evidence, distinguish the
  load-bearing fact, hypothesis or judgment, and proof status. Do not emit empty
  categories.
- Existing behavior or state: name only the dimensions that can change the
  current fix or proof path, and mark each as preserve, intentionally change,
  unknown, or not applicable when that status is material.

If the only available evidence is the prompt, plan, or supplied fixture, say
that explicitly and reason from it before asking for the smallest missing
decision. A narrow question is not a substitute for the current-scope record.
Do not substitute an unrelated repository fixture, generated file, or nearby
example merely because it shares a domain term or plausible constant. If the
reported tool or artifact is absent, keep the evidence prompt-only, record the
missing artifact as the blocker, and do not hand-edit a different generated
surface.

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
Record any explicit user model override or the capability/context reason for a
non-default model when the host exposes that metadata.

## Self-Review And Repository Closure

After implementing and verifying a repair, run a self-review before final repair
claims. When a matching review workflow is visible and applicable, use it;
otherwise perform a self-contained review of the repair slice: ledger closure,
minimal patch envelope, preserved behavior, verification proof, artifact
freshness, generated or temporary surfaces, and user-visible summary. Resolve
material findings and rerun affected proof before closure, or record the
remaining item as `deferred`, `accepted-residual`, or `blocked`.

Verified implementation closure includes a scoped local closure commit by
default unless the user explicitly says not to commit, project instructions
forbid commits, or a safety gate blocks the operation. This default authorizes
only staging and committing verified repair-owned paths. It does not authorize
push, amend, rebase, stash, reset, release preparation, version changes,
destructive cleanup, or mutation of unrelated or ambiguous user changes.

If the host or harness requires an additional confirmation for local commits,
ask once at debug startup when the repair can reasonably change tracked files.
Do not wait until the repair is complete or ask again at closure. Diagnosis-only,
not-reproduced, no-change, or retest-only work does not need the question and
must not create an empty commit.

Before any staging or commit, run a dirty worktree and index preflight:

- Refresh staged, unstaged, and untracked state.
- Identify the paths that belong to the verified repair slice.
- Surface unrelated or ambiguous dirty paths before staging or cleanup.
- Confirm self-review and verification are complete for the repair-owned paths.

Use matching available commit-execution and message-writing capabilities for the
commit path when they are visible and applicable. If they are unavailable, apply
the same minimum safeguards here: stage only repair-owned paths, use a
Conventional Commit message that records the repair outcome and durable proof,
transport any multi-line message as one complete payload, add trailers through
the commit command's trailer mechanism, verify the staged set before committing,
and inspect the stored message after committing.

When the final response must prove the closure commit from recorded text, show
the preflight/staged-set commands, one complete multi-line message transport
(`git commit -F - <<'EOF'` or `git commit -F <file>`), any requested
`git commit --trailer` argument, and the exact
`git show -s --format=%B HEAD` result. Do not replace these artifacts with a
summary, repeated `-m` body arguments, or a different log command.

Stop before commit when the repair-owned path set is ambiguous, unrelated staged
changes cannot be excluded, verification is degraded without accepted residual,
self-review has unresolved material findings, the commit would require push,
amend, rebase, stash, reset, release preparation, a version bump, destructive
cleanup, or project policy forbids commits. Report the preflight evidence and
the smallest decision needed. If the user explicitly disabled commits, finish
with the reviewed uncommitted state, verification status, and proposed commit
scope or message when useful.

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
- A verified implementation with repair-owned file changes has either a scoped
  local closure commit, an explicit user no-commit instruction, or a recorded
  safety blocker. Push, amend, rebase, stash, reset, release, version changes,
  destructive cleanup, and unrelated mutation still require exact consent and
  preflight evidence.
