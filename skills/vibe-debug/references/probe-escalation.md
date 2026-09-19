# Probe Escalation

Read when bounded triage leaves live state unobserved, under the escalation gate
in `debug-workflow.md`. Probe only when it answers the next implementation-changing
question better than more static work. A dynamic symptom alone does not justify
instrumentation; existing tests, source traces, logs, or artifact inspection may
already suffice. Product intent still needs an authoritative behavior source.

## Probe Design

Use narrow, reversible observations: a branch counter, boundary state/ID,
start/end sequence labels, cleanup counts, artifact version, or focused test
assertion. Prefer existing diagnostics. Avoid broad dumps, secrets, user payloads,
noisy per-frame logs, unbounded cost, or timing changes that could mask the bug.
Prefer local proof when it answers the same question with less user burden.

## Probe Contract

Before running, name the hypothesis boundary and probe location, expected
signature for each plausible cause, where to capture evidence, and removal or
conversion plan. Prove the observed artifact contains the instrumentation using
`verification-handoff.md`; use that reference's retest contract if the user runs it.

A retained field probe requires explicit opt-in, disabled-by-default state,
bounded off-path emission cost, stable structured fields excluding secrets and
user data, documented purpose, and a countable bad signature under comparable
before/after conditions. Unsupported privacy or cost claims block retention.

## Interpreting Results

Record the signature and which hypotheses it supports or refutes; the result is
evidence, not a fix. The coordinator owns interpretation. Replace temporary
instrumentation with a product fix or regression test where feasible; remove it
before finishing unless retention was explicitly selected and meets the contract
above. Rebuild/refresh afterward and verify the final artifact lacks temporary
diagnostics. A zero count closes only the mechanism the probe observes.
