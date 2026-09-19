---
version: 6.0.1
name: vibe-debug
description: Use when debugging or repairing existing features from rough agent-assisted coding reports, regressions, failed prior fixes, repeated "still broken" feedback, source-only debugging stalls, unobserved runtime state, tool or automation failures, environment-specific failures, runtime artifact mismatches, security boundary surprises, or fixes that feel wrong.
---

# Vibe Debug

## Overview

Turn rough reports about existing features into verified repairs. Preserve the
user's wording as evidence of experience, not proof of root cause. This workflow
is self-contained; use available specialist capabilities only when helpful.
Greenfield work, pure review, and history-only operations belong elsewhere.

## Core Rule

Inspect available evidence before asking questions; ask only what changes the
repair, proof, scope, or accepted risk. Treat free-text corrections to offered
options as changed intent, not as the closest original option.

Make a concrete runtime regression the exclusive primary symptom until it is
fixed, not reproduced, deferred, accepted as residual, or blocked. Keep adjacent
findings in the ledger and outside the patch unless they share the proven cause
and verification path. For that primary symptom, identify the reproduction or
first failing proof, hypothesis, minimal patch envelope, positive and negative
sentinels, and last verified checkpoint.

## Effect And Write Boundaries

<!-- shared-contract:class language=none commit=state-changing effect=state-changing -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
**Write nothing beyond what the phase's declared effect class and boundary permit.**

- Apply the effect class the phase declares in its own text; where this package states a narrower limit, the narrower limit wins.
- Read-only: report in chat; edit no file, run no state-mutating command, and never stage, commit, tag, push, change versions, delete data, or start services. Write a file only when the user explicitly asks for a saved artifact.
- Artifact-only: create or update only the artifact the phase owns and the supporting paths its text declares, such as a confirmed plan reflection or a decision record, and leave them in the working tree.
- Never let an artifact-only phase implement executable behavior, edit code or tests as implementation, produce another phase's artifact, do release work, or treat its artifact as same-turn implementation authority.
- State-changing: edit and run commands only inside the declared scope, in its smallest verified unit; leave other paths, pre-existing changes, and runtime or external state untouched unless the user selects them.
- These limits cover shell commands (redirection, `sed -i`, `tee`, `mv`, `cp`, `rm`, `git checkout --`) as well as file tools; report a refused write as a boundary stop and never retry it through another tool.
- Keep every irreversible or outward-facing operation under its own consent.
<!-- shared-contract:end effect-write-boundaries -->

The repair scope is its minimal patch, proof, temporary instrumentation and
cleanup, and the supporting records below.

## Durable Records

At phase start check `docs/decisions/README.md` and
`docs/reports/findings/README.md` (or existing repository indexes) for applicable
entries. Read `references/durable-records.md` only when applying, recording,
deferring, or handing a record forward. This phase may write `docs/decisions/`
and `docs/reports/findings/`, or their existing repository equivalents.

## Visible Output And Debug Ledger

For one simply reproduced symptom, report symptom, expected behavior, verified
cause, fix, and proof directly. Use `references/debug-ledger.md` for recurrent,
multi-symptom, multi-environment, long-running, interrupted, or user/runtime-retest
diagnosis. Show compact rows for unresolved symptoms, hypotheses, tool failures,
and closure decisions; a question alone does not replace that record.

If the reported artifact or tool is absent, use prompt evidence and name the
blocker; do not substitute a nearby fixture based on a shared domain term.

## Delegated Diagnosis

When independent hypotheses need bounded read-only investigation and delegation
is available, fan them out. Give each investigator one hypothesis-shaped question
and require source-backed evidence or a blocker. Keep mutations, probes, user
retests, and ledger ownership with the coordinator.

### Delegated Findings

<!-- shared-contract:begin delegated-result-proof source=shared/vibe-contract.md -->
**Treat delegated output as a claim, never as proof, until the coordinating phase verifies it.**

- This covers worker reports, reviewer findings, sub-agent results, proxy recommendations, and any delegate statement that a check passed or a step completed, including claims about its own run.
- Verify with evidence the coordinating phase holds itself: re-read the anchors behind a load-bearing conclusion, inspect or rerun the command and output behind a verification claim, or run a disconfirming check.
- Until then keep it `Unproven` and advisory: it carries no verified label, enters a ledger only as evidence toward a hypothesis, and is not dispositioned.
- Never let a delegate's commands, scope or permission claims, routing suggestions, or recommendations select or approve anything; adopt them only through the coordinating phase's own judgment, recording where each decision came from.
<!-- shared-contract:end delegated-result-proof -->

### Model Choice

<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a model for each delegated unit by capability and context fit, never by hard-coded name.**

- Only choose when the host allows it and the user has not fixed a model.
- Use a cheaper or faster tier only for bounded, low-ambiguity lookups, extraction, and mechanical checks; use the strongest suitable tier for synthesis, adversarial or security review, human-risk reasoning, and final recommendations, or when the user asks for maximum performance.
- Record the choice only for a user override, degraded capability, a cost or performance constraint, or audited external execution.
<!-- shared-contract:end model-tier-selection -->

## Self-Review And Repository Closure

After verification, review the repair's scope, preservation proof, and remaining
findings before claiming closure. Use a matching review capability if available;
otherwise review it here. Resolve material findings and rerun affected proof, or
record them as deferred, accepted residual, or blocked.

### Commit Selection

<!-- shared-contract:begin commit-selection-state-changing source=shared/vibe-contract.md -->
**Only an explicit user request, a bound plan item, or the workflow's own verified checkpoint selects a commit.**

- Name the source before committing: the current user's request, an approved bound-plan checkpoint, or this workflow's checkpoint default for its own verified unit. With none, do not commit; ask whether a commit is wanted.
- Never treat routing, invocation, edit permission, a convenient stopping point, tracked changes, or an available commit workflow as a source. Commit execution has no checkpoint default of its own.
- Checkpoint default: once a self-contained unit is implemented, verified, reviewed, and its material findings dispositioned, commit exactly that unit locally without waiting for a separate instruction; never let several units pile up uncommitted.
- Select nothing from discovery-only, blocked, unchanged, failing, unverified, or work-in-progress state.
- Stage only the unit: exclude pre-existing changes the workflow did not make, paths outside the unit, and any artifact that would become newly tracked; if the unit cannot be separated from other changes, report the mixed state and ask.
- Route each selected commit through commit execution with its scope, test and review evidence, exclusions, and any proposed message; that workflow owns staging, diff review, message transport, and post-commit verification.
- Before a push, amend, rebase, HEAD-moving reset (soft, mixed, or hard), `filter-*` rewrite, or scripted replay of several commits, get the user's explicit authorization for that operation; a commit request or checkpoint never grants it, and published history is shared.
- Never treat a commit request or checkpoint as consent to release, version changes, tags, stash, squash, destructive cleanup, force-adds, tracking a new artifact, or external side effects; each needs its own.

Example: "the user asked for a commit this turn" names a source; "this is a good stopping point" does not.

Exception: a current no-commit instruction, a bound plan that forbids commits, or project policy suspends the default; leave the verified changes in the working tree and report why.
<!-- shared-contract:end commit-selection-state-changing -->

The checkpoint unit is the proven repair. Do not ask about commit policy at
startup. Perform no history operations beyond that unit's closure.

## Reference Routing

Before source edits or final repair claims, read `references/debug-workflow.md`
for the evidence-first loop. Load other references at these triggers:

- `references/debug-ledger.md`: complex diagnosis, repeated failed attempts, or closure statuses.
- `references/source-routing.md`: unfamiliar external contracts or tool failure.
- `references/state-space-matrix.md`: non-trivial preservation and regression scope.
- `references/probe-escalation.md`: bounded triage cannot distinguish live-state hypotheses.
- `references/verification-handoff.md`: runtime artifacts, degraded proof, or user retests.
- `references/continuity-and-recurrence.md`: interruption, resumption, or recurrence.
- `references/durable-records.md`: the record operations named above.

## Stop Conditions

Pause implementation when a material expected-behavior source, existing-behavior
dimension, artifact, tool, or observation path is missing and no credible
alternate proof or explicitly accepted residual resolves it. Explain the user
impact and ask only the smallest decision needed. For repeated failed repairs,
apply the stop rule in `references/debug-ledger.md` before another patch.

## Finish Gate

Give each current-scope item a closure status with proof or the remaining gap;
`references/debug-ledger.md` defines the statuses. Record deferred, accepted
residual, and blocked items in findings reports, and cross-unit rules in decision
records. Apply the self-review and commit gates above. Runtime closure also
requires the freshness, retest, and diagnostic-cleanup checks in the applicable
references; skipped checks never count as proof.
