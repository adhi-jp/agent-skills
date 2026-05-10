---
name: vibe-debug-fix
description: Use when debugging, bug fixing, or repairing existing features from vibe-coding feedback, rough bug reports, regressions, "still broken" or failed prior fixes, tool-confidence or automation failures, environment-specific failures, runtime artifact mismatches, security boundary surprises, or fixes that feel wrong.
---

# Vibe Debug Fix

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
- A fix that might affect existing behavior, contracts, state, permissions,
  artifacts, lifecycle, or user-visible output.

Examples are not boundaries. Concrete examples such as UI glitches, auth
origins, asset paths, encodings, worker restarts, deploy bundles, and async
cleanup are only instances of broader dimensions. Generalize them before using
them.

## When Not to Use

- Greenfield feature work with no existing behavior or reported symptom.
- Pure review cycles where an active review workflow is already sufficient.
- General commit, history rewrite, or release decisions unless they are part of
  debug/fix closure.
- One-line mechanical edits where no symptom, regression, or existing behavior
  is at stake.

## Core Rule

The user's report is valuable evidence of experience, not a verified root
cause. Investigate available code, tests, logs, screenshots, docs, artifacts,
history, and tool output before asking questions. Ask only questions that change
the fix, proof path, risk acceptance, or current-scope closure.

Stop before implementation when the current issue lacks any of these:

- A reproducible symptom, isolation proof, source trace, or exact manual proof
  path.
- An authoritative expected behavior source.
- A verification path that can observe the claimed fix.
- Current-scope closure criteria for each reported symptom.

Explain blockers in user-impact terms: what the user could still see, lose,
misconfigure, trust incorrectly, or be unable to verify.

## Reference Routing

Read these bundled references only when their details are needed:

- `references/debug-ledger.md` - ledger template, closure statuses, and
  repeated-attempt handling.
- `references/source-routing.md` - source-of-truth routing and tool-confidence
  ledger.
- `references/state-space-matrix.md` - state-space dimensions for static,
  dynamic, environment, representation, and lifecycle bugs.
- `references/verification-handoff.md` - artifact freshness,
  verification-degradation, and user retest contracts.
- `references/continuity-and-recurrence.md` - resume handling and repeated-class
  self-review.

## Workflow

1. **Continuity preflight**
   - After resume, interruption, context compaction, or a "continue" request,
     re-read the latest user request, outstanding symptoms, ledger statuses,
     and next proof/action before doing new work.
   - Do not drop unresolved symptoms because a prior subtask was completed.

2. **Capture vibe intent**
   - Preserve the user's wording for symptoms, UX concerns, "feels wrong"
     observations, and corrections to offered choices.
   - Translate the wording into observable behavior, expected behavior,
     unknowns, affected users or contexts, and current-scope closure criteria.
   - Treat user free-text changes to offered options as signal. Re-check what
     changed instead of mapping the answer back to the closest original option.

3. **Optional useful-skill and rule preflight**
   - Check project instructions, local docs, and visible skill metadata for
     task-relevant guidance.
   - Use matching available skills only when they directly help with the current
     stack, proof method, writing pass, or tool path.
   - If none apply or one is unavailable, continue with this workflow.

4. **Open the debug ledger**
   - Maintain a ledger with these fields for each current-scope symptom:
     reported symptom; expected behavior and source; observed behavior and
     source; prior attempts and why each failed or remains unproven; suspected
     causes; proven cause; affected state-space dimensions; verification path;
     closure status.
   - Closure status is exactly one of `fixed`, `not-reproduced`, `deferred`,
     `accepted-residual`, or `blocked`.
   - Do not claim "fixed" until every current-scope ledger item has proof and a
     closure status.

5. **Analyze existing behavior**
   - Identify current behavior to preserve before changing code.
   - Split it into user-visible output, internal state transition,
     persistence/lifecycle behavior, external contracts, and
     operational/runtime artifacts.
   - Mark each dimension as `preserve`, `change intentionally`, `unknown`, or
     `not applicable`.
   - Treat an `unknown` dimension that affects the current fix as a blocker
     until source trace, local reproduction, or accepted residual resolves it.
   - Add at least one verification item for every `preserve` or
     `change intentionally` dimension that can regress.

6. **Route sources and tool confidence**
   - Before editing unfamiliar external API, framework, protocol, data contract,
     permission, build, deploy, or tool behavior, check the authoritative
     source: official docs, upstream source, local project code, CLI help,
     changelog, useful available skill, or user-provided source material.
   - If a tool fails, classify the failure narrowly: failed command, failed
     mode, failed input shape, unavailable service, missing permission, stale
     artifact, or flaky environment.
   - Choose a narrower retry, fallback proof, or blocker. Do not abandon all
     related tools because one mode or invocation failed.

7. **Build the state-space matrix**
   - For non-trivial fixes, convert user examples into dimensions rather than
     fixing only the named example.
   - Include relevant dimensions such as input representation, encoding,
     environment/origin, platform/runtime, direction, lifecycle state,
     cache/artifact freshness, permission/role, sync/async path, and
     error/cancel path.
   - For dynamic, visual, streaming, event-driven, queue, cache, or lifecycle
     bugs, include temporal sequence, ordering, overlapping events, per-entity
     identity, reset/cancel behavior, and stale-state cleanup after the final
     event.

8. **Control speculation**
   - Classify each implementation-affecting statement as `verified fact`,
     `hypothesis`, `expert judgment`, `expected outcome`, or `proof result`.
   - Do not act on a `hypothesis`, `expert judgment`, or `expected outcome`
     unless the next step is explicitly a proof step, the user accepts the
     residual risk, or the item is outside the current fix.
   - Convert optimistic language into proof requirements. "This should fix it"
     becomes "the proof needed is ..."; "looks fixed" becomes a recorded manual
     or automated observation.
   - Name one fast disconfirming check that could show the chosen cause or fix
     is wrong.

9. **Handle failed attempts**
   - On repeated reports or "still broken" feedback, explain why the last fix
     did not address the symptom before proposing another fix.
   - The next fix must be tied to new proof, a source trace, or a state-space
     finding. Do not make another independent guess.

10. **Fix the smallest verified slice**
    - Prefer reproduction first. If local reproduction is not feasible, use a
      source trace, isolation proof, or exact manual proof path.
    - Keep edits close to the proven cause and existing local patterns.
    - Preserve unrelated behavior and defer adjacent hardening unless it is
      needed to close a current ledger item.

11. **Prove artifact freshness**
    - Before asking the user to retest or declaring a runtime issue fixed,
      prove the tested artifact includes the change: rebuilt package or binary,
      refreshed dev-server bundle, migrated local data, regenerated assets,
      updated lockfile, restarted process, cleared stale cache, or equivalent.

12. **Handle degraded verification**
    - Skipped, unavailable, flaky, environment-limited, or manual-only checks
      are not proof.
    - For each degraded check, choose alternate proof, narrower local proof plus
      explicit residual, user retest contract, accepted residual, or blocker.
    - Do not count "manual smoke skipped", "not locally reproducible", or "test
      environment cannot observe this" as a pass.

13. **Use a concrete user retest contract when needed**
    - If local proof cannot observe the behavior, give the user exact setup,
      action sequence, expected observation, artifact/version freshness marker,
      failure evidence to capture, and which ledger item each check closes.
    - Avoid vague requests such as "please retest".

14. **Review recurrence before finishing**
    - If the same class of bug, review finding, or user complaint appears at
      least twice, scan adjacent surfaces for the class of omission before
      finishing.
    - Add at least one disconfirming or negative check for the neighboring case
      most likely to have been missed.

## Stop Conditions

Stop and report a blocker or ask the smallest plan-changing question when:

- Expected behavior has no source and the difference affects product behavior,
  data, permissions, security, external contracts, or user experience.
- The symptom cannot be reproduced, isolated, source-traced, or handed off with
  exact manual proof.
- A repeated report arrives and you cannot explain why the prior fix failed.
- A needed source, artifact, tool, or runtime path is unavailable and no
  alternate proof is credible.
- A current-scope existing-behavior dimension remains `unknown`.

## Finish Gate

Before ending:

- Every current-scope ledger item has status `fixed`, `not-reproduced`,
  `deferred`, `accepted-residual`, or `blocked`.
- Every `fixed` item has proof and artifact freshness when runtime artifacts are
  involved.
- Every preserved or intentionally changed behavior dimension has verification
  or an explicit residual.
- Skipped or degraded checks are reported as non-proof with next action.
- User-side retests, when needed, include exact steps and expected observations.
