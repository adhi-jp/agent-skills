# Verification Handoff

Read for runtime artifacts, incomplete local proof, or user-environment retests.

## Artifact-Freshness Gate

Before declaring a runtime fix or requesting retest, trace the change through
source-to-build, build-to-running-process, and runtime-to-user environment. Use
observable version/hash, package contents, process, cache, migration, or deployment
evidence appropriate to that path. If freshness is unproven, keep the item blocked
or include a freshness marker in the user retest.

## Verification-Degradation Gate

Skipped, unavailable, flaky, environment-limited, and unperformed manual checks
are non-proof. Choose the strongest credible path now: alternate proof of the
same contract; narrow local proof with explicit uncovered risk; a user retest
when only their environment can observe it; otherwise a blocker. An accepted
residual requires explicit user acceptance. Do not offer a proof-path menu or
promise instructions later when the available evidence determines the path.

## User Retest Contract

If the user asks what to test and only their environment can observe the behavior,
give the contract now and keep the item blocked until evidence returns:

1. Setup, including environment/version, artifact freshness marker, and relevant
   account, data, cache, or restart conditions.
2. Exact action sequence and relevant variants.
3. Expected output, state, or absence that would prove the symptom closed.
4. Failure evidence to capture: logs, screenshot, IDs, timestamps, or inputs.

Unknown commands or paths may use labeled assumptions or placeholders with
adaptation instructions; never present a bare placeholder as a runnable command.
Tie the retest to the unresolved symptom without requiring a ledger id for every
step. "Please retest" alone is insufficient.

Retained diagnostics must satisfy `probe-escalation.md` before shipping.
