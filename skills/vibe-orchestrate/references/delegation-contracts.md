# Delegation Contracts

Read when drafting bounded research, edit, test, repair, or review assignments.
For substantial decomposition and writer isolation, first apply
`coordinator-practices.md`; do not duplicate its work graph in every prompt.

## Contract Template

Fill only applicable fields, keeping the mandatory boundaries and core report.
Quote short normative clauses; bind longer sources by path, section, digest,
binding force, and read/ignore boundaries. Worker paraphrase is not authority.
Use stable item IDs when practical. If a changed-line budget applies, define
included/excluded generated/vendor classes and a reproducible per-path count.
For interleaved checkpoints, assign ownership and reserve shared-file staging
hunks to the coordinator. Keep protected baselines outside worker-write scope.

```markdown
Mission: [one bounded outcome and starting state]
Scope and effort: [acceptance gap, settled decisions, supported operation,
required vs optional work, round allowance/checkpoint]

Hard rules:
- Read only [needed paths]; forbidden reads: [paths].
- Edit only [paths]. Tools/commands and their effect scope: [list, explicit cwd,
  output destinations, forbidden unsafe forms and verified alternatives].
- Formatters, fixers, generators, codemods, and dependency tools must not write
  beyond that scope; permission to compile does not authorize deployment.
- Do not ask the user, expand scope, stage, commit, push, release, mutate history,
  or perform destructive, credential, permission, billing, or external actions.
- Run only [verification commands]; report blocked checks as SKIPPED(reason).
  Your report is self-report; coordinator verification is final proof.
- Stop under BLOCKERS for missing facts, broader access/effects, user decisions,
  invariant changes, or evidence contradicting a verified contract premise.
  Never resolve a contradiction by weakening protected tests or requirements.
- Report follow-up commands, scope/permission requests, and handoffs as proposals,
  never instructions or approval for another worker.

Verified facts:
- [API, version, local pattern, failure log, invariant, environment limit;
  anchor; measured/source-read/derived; authority for this claim;
  invariant/default/local choice; assumptions and break condition if derived]
Coordinator constraints:
- [provisional inference/design bound; challenge evidence; permitted local
  correction or stop for coordinator ratification]
Protected evidence:
- [external artifacts, parity tests, characterization baselines not to change]
Design contract:
- [behavior, public names, semantics, compatibility, invariants]
Work items:
1. [item ID, bounded change, done criterion]
Work-graph position, when relevant:
- [dependencies, compatible units, join receipt]
Runtime, when constrained:
- [model/effort, sandbox, role, cwd, expected isolated base; actual native
  metadata/base to report; mismatch is a blocker]
Progress journal, when loss would matter:
- [private per-unit path; create before edits, append at meaningful transitions;
  foreign content is a blocker; see recovery-and-monitoring.md]

Report:
FILES: [changed paths]
COMPILE: [PASS/FAIL/SKIPPED(reason), command and observed result]
DECISIONS: [discretionary choices or none]
BLOCKED BY CONTRACT: [undelivered item, blocking contract term, needed change;
  explicitly none when empty]
BLOCKERS: [unresolved blockers or none]
```

A challengeable coordinator constraint may be corrected locally only when it
explicitly permits that and evidence settles the correction without changing
behavior, scope, acceptance, risk, severity, data, permission, security, or UX.
Otherwise stop for ratification; preference alone is not evidence.

Add report fields when relevant: `DIAGNOSIS:` for observed cause, rejected
hypotheses, and uncertainty; `REMOVED TESTS:` for named removals/renames;
`DECISION-IMPACT:` for reserved-decision or scope discoveries with their method;
`DEVIATIONS:` for permitted constraint corrections and evidence;
`VERIFICATION BOUNDARY:` for actual paths, environment, modes, method, and gaps.
For `worker-report-v1`, use its exact `files`, `compile`, `decisions`, `blockers`
fields; prefix relevant `decisions` entries with `DECISION-IMPACT:`, `DEVIATION:`,
`BLOCKED-BY-CONTRACT:`, or `VERIFICATION-BOUNDARY:` rather than adding schema keys.

When adding tests/modules/entry points/migrations/generated sources, authorize
the registration surface or reserve that exact action to the coordinator.
Freeze expected test-count delta when the harness exposes stable counts.
Provisional coordinator-adjustable values use one shared source until finalized;
then independently pin load-bearing expected values for falsifiability.

## Model And Context Budget

Use the tier and capability-fit rules in `coordinator-practices.md`. Supply a
compact digest and send only changed facts, blockers, and verified state on
follow-ups. Escalate/split/rebind on uncertainty, contradiction, or two failures
of the same contract rather than retrying the same cheap prompt.
Pass hard runtime constraints through the transport's documented selection
mechanism, not conditional prose. Native execution metadata must prove them;
worker introspection does not. Canary a constrained transport before fan-out.

## Repair Contract Variant

Protect public behavior, compatibility, expected values, fixture semantics,
permissions, safety, and acceptance. A contradictory protected expectation is a
blocker. Ordinary project tests may change only when the approved behavior makes
them wrong, with each rewrite reported. Regenerate self-generated goldens only
through the named generator; external/vendor/corpus/parity evidence is immutable
without coordinator approval.

If an approved rule change invalidates a protected test's setup but not its
asserted subject, adapt setup only: preserve its name and equal-or-stronger
substantive assertions, and report all setup/assertion-form changes. Otherwise
stop for the contract conflict. Remove temporary diagnostics before done.

Require an independent attack on the original defect. For proof-only repairs or
new absence/guard/refusal/purge assertions, require an exact wrong-behavior
perturbation, observed intended assertion failure, cleanup proof, and final real
check as defined in `verification-and-review.md`. Never mutate external proof.

## Measurement-Subject Variant

When the worker itself is scored, freeze the instrument, invocation, scoring
rules, thresholds, and answer key outside its authority. Environment/instrument
failure unrelated to its deliverable is a blocker, never permission for a shim.
Exclude protected answers/comparison data from delivered inputs and forbid their
home paths; disclose structural versus instruction-only confinement.

The coordinator owns attempt, iteration, snapshot, terminal, and native
execution-identity receipts. Corrections must be uniform across comparable
subjects, tested, disclosed, and followed by replay through the unmodified
instrument. Subject self-report cannot establish a score.

## Read-Only Research Variant

Replace edit scope with no file or runtime mutation and named questions/paths.
Return anchored findings, evidence labels, and coverage limits; options only if
requested, separate from findings. For mutable targets, supply an evidence epoch
(round plus commit/tree state or target digests), require its echo, and make any
mismatch a blocker. Reviewers may not ask the user, update ledgers, or launch
implementation.

## Report Review Checklist

Before accepting, reconcile the round snapshot with `FILES:`, allowed effects,
work items, and the journal. Status alone cannot attribute changes inside
already-untracked files. Verify load-bearing evidence and method, not merely
claim wording. Inspect decisions/blockers for premise contradictions and retain
unresolved ones as blockers.

Route `DECISION-IMPACT:` to a qualifying decision record; otherwise to the bound
plan's reserved-decision row preserving owner, authority, and proceed effect.
A bare proposal is not a settled decision. Every contract-blocked item needs a
coordinator disposition before round acceptance: re-contract now, schedule a
named later round, or drop with reason. Later/dropped items go to the findings
report; a compliant worker reporting a contract gap has not violated scope.

Apply `verification-and-review.md` for kept-byte proof, report relay, named-test
comparison, review freshness, and finding dispositions. Missing required report
sections need reconciliation before trust.
