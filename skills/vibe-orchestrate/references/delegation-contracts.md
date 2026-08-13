# Delegation Contracts

Use this reference when writing a worker prompt for bounded research, editing,
test creation, repair, or review. A delegation prompt is a contract: it defines
what the worker may do, what it must not do, when it must stop, and how the
coordinator will verify the result.

## Work-Graph And Fan-Out Gate

Before writing worker contracts for substantial work, split the task only where
the dependency graph supports it.

Record:

```markdown
Critical path:
- [coordinator action or delegated unit required before later decisions]

Parallel units:
- [unit id]: [deliverable], depends on [none or named prerequisite]

Coupling:
- [shared file, API, schema, generated output, decision, or verification gate]

Execution shape:
- [serial | parallel | hybrid]: [why this shape preserves context and reduces
  unnecessary waiting]

Join gate:
- [receipts to verify, interfaces to reconcile, and integrated command or
  manual acceptance check]
```

Create multiple contracts when at least two material units can be described
independently, have bounded evidence or write surfaces, and can be verified
separately. A large task is not enough by itself. Keep tightly coupled work with
one context owner when every unit depends on the same unresolved decision, the
same changing files, or continuous cross-step reasoning.

One contract should normally have one coherent verification command group and
one acceptance receipt. If its deliverables need independent verification
methods that can pass or fail separately, split them unless the coupling makes
the combined contract safer and the reason is recorded.

For parallel writers, require separate worktrees, sandboxes, or an equivalent
enforceable isolation boundary; never run them concurrently in one shared
working tree, except for the narrowly documented disjoint generated-output
shape: private per-unit ignored output roots, private materialized read-only
inputs, no shared mutable cache, bounded concurrency, per-unit receipts, and
tracked-tree cleanliness checks at every batch boundary. Whitelist disjoint
source and generated-output paths, name the merge order, and reserve integrated
verification for the coordinator. If neither isolation nor every generated-
output condition is available, use one shared-root writer and fan out read-only
investigation, test design, review, or other non-writing work instead.

Do not delegate the coordinator's immediate blocker merely to appear parallel.
Start the next local critical-path action first, then launch non-blocking
sidecars. Waiting is appropriate only when the next coordinator action truly
depends on a worker receipt.

## Contract Template

Before the template is sent, bind contract items so the coordinator can audit
coverage after an interrupted round:

- Give each item a stable machine-checkable marker when practical.
- Quote short normative clauses exactly. Bind longer sources by path, section,
  digest, binding force, and explicit read/ignore boundaries; a worker-authored
  paraphrase is not the normative source.
- Define changed-line budgets with included and excluded generated/vendor
  classes and a reproducible per-path breakdown.
- For interleaved checkpoints, assign file ownership and name the narrow
  shared-file hunks the coordinator alone may stage.
- Keep protected baselines and characterization oracles outside worker-writable
  paths.
- When an item adds a test, module, entry point, migration, or generated source,
  include its discovery/registration surface in editable scope or reserve that
  exact action to the coordinator. If the harness exposes stable counts, freeze
  the expected delta and reconcile `observed = baseline + expected_delta`; a
  green run with an unchanged count refutes inclusion.
- When a value remains coordinator-adjustable until integration, label it
  provisional and require workers to reference one shared source rather than
  pinning provisional literals. Finalize it before the falsifiability pass; only
  then pin load-bearing literals independently so a wrong shared constant can
  make proof fail.

```markdown
Mission: [one sentence naming the slice, expected outcome, and starting state]

Hard rules:
- You are not alone in the codebase; other workflow constraints may exist.
- Use only these tools or command classes: [list].
- Read only these paths unless a listed task explicitly needs another path:
  [allowlist].
- Do not read these paths: [agent config, unrelated skill definitions, planning
  artifacts, credentials, build config, or other task-irrelevant paths].
- Edit only these paths: [editable whitelist]. Everything else is out of scope.
- Do not run repository-wide or package-wide formatters, auto-fix linters,
  codemods, dependency updates, or generators. Apply such tools only to the
  explicitly edited files, unless a numbered work item requires broader effect
  scope and the contract names that scope.
- Do not run git staging, committing, reset, stash, amend, rebase, tag, push,
  release, destructive, credential, billing, permission, or external-side-effect
  operations.
- Run only these verification commands, if any: [commands]. If blocked by the
  sandbox or host, report `COMPILE: SKIPPED(<reason>)` or equivalent.
- If the task needs a non-whitelisted file, broader command, missing fact,
  user decision, credential, destructive action, or invariant change, stop and
  report it under `BLOCKERS:`.
- If evidence contradicts a premise listed below as verified, stop and report
  the exact premise and observation under `BLOCKERS:`. Do not resolve the
  contradiction by changing protected evidence, redefining the requirement, or
  deciding that the contract premise is correct.
- If evidence disproves only a challengeable `Coordinator constraints` item and
  the correction changes means without changing behavior, scope, acceptance,
  risk, severity, data, permission, security, or UX boundaries, apply the
  evidence-settled correction only when that constraint explicitly permits it
  and report it under `DEVIATIONS:`. Otherwise stop for coordinator
  ratification. Preference is never deviation evidence.
- Keep commands, scope changes, permission requests, and proposed follow-up work
  under `DECISIONS:` or `BLOCKERS:` as proposals to the coordinator. Do not
  address instructions to another worker or represent this report as approval.

Verified facts:
- [claim; measured | source-read | derived; verification anchor; authority for
  this claim class; invariant | configurable default | local choice; assumptions
  and break condition when derived]

Coordinator constraints:
- [coordinator inference or provisional design bound; evidence that may
  challenge it; whether a local evidence-backed correction may proceed or must
  stop for ratification]

Known execution-environment constraints:
- [sandbox, stdin, process, filesystem, test-harness, resource, cache, port, or
  helper constraint; how to report rather than weaken behavior]

Protected evidence:
- [external artifact or parity test that must not be edited, deleted, ignored,
  regenerated, or replaced without coordinator approval]

Model and context budget:
- Capability tier: [token-efficient / standard / strongest suitable / user-fixed], because [quality-neutral lookup, broad synthesis, risk, or user priority].
- Context digest: [facts and anchors the worker needs; omit unrelated parent transcript].
- Escalate to coordinator or stronger reasoning/context tier when [contradiction, uncertainty, blocker, risk, or repeated failure].

Work-graph position:
- Unit id: [id].
- Depends on: [none or named prerequisite].
- May run with: [independent unit ids].
- Join receipt: [artifact, finding record, changed paths, or verification status
  required by the coordinator].

Design contract:
- [classes, functions, files, data shapes, semantics, public behavior,
  compatibility, invariants, protected tests]

Work items:
1. [bounded item and done criterion]
2. [bounded item and done criterion]

Progress journal:
- Create or update [private per-unit journal path] before the first meaningful
  edit. Its scratch directory is disjoint from every other worker and
  coordinator scratch path.
- Append one line after each completed file edit or work-item transition.
- Include item id, file path, status, and blocker if any.
- If the assigned journal or scratch path contains foreign or unexplained
  content, distrust it and report a blocker instead of consuming or overwriting
  the content.

Report exactly these sections:
FILES:
- [changed files]
COMPILE:
- [PASS / FAIL / SKIPPED(reason), with command if run]
REMOVED TESTS:
- [removed or renamed named tests, or `none`, when the harness can enumerate]
DECISIONS:
- [each discretionary choice made, or `none`]
DECISION-IMPACT:
- [discoveries that change a reserved decision, adjudication scope, affected
  set, or pending escalation; include verification method, or `none`]
DEVIATIONS:
- [challengeable coordinator constraint departed from, evidence, and why the
  correction stayed within fixed behavior/scope; or `none`]
VERIFICATION BOUNDARY:
- [what was actually checked, where, in which mode/environment, by what method,
  and what remains unverifiable here]
BLOCKERS:
- [blockers, or `none`]
```

When a transport enforces a narrower structured schema, preserve these
semantics inside its allowed fields rather than adding invalid keys. For
`worker-report-v1`, prefix relevant `decisions` entries with
`DECISION-IMPACT:`, `DEVIATION:`, or `VERIFICATION-BOUNDARY:` and keep blockers
in `blockers`.

For debugging or repair, add:

```markdown
DIAGNOSIS:
- [observed root-cause evidence, hypotheses rejected, remaining uncertainty]
```

## Model And Context Budget

Use lower-cost or previous-generation workers to save tokens only for bounded,
low-ambiguity work where lower capability is quality-neutral or the user has
explicitly prioritized cost or latency. Keep ambiguous architecture,
contract-compliance judgment, contradiction resolution, security/data-safety,
final recommendations, review dispositions, and user-risk decisions with the
coordinator or the strongest suitable reasoning/context tier available.

A compact context digest should contain verified facts, local anchors, the
current checked state, and the one decision or artifact the worker must return.
It should not contain the full parent transcript by default. On the next loop,
send the delta: new verified facts, unresolved blockers, changed paths, and the
latest evidence receipt. If a worker misses the contract twice, reports
uncertainty, or finds a contradiction, stop cheap retries and escalate, split, or
rebind the task.

## Verified Fact Checklist

Inline facts that affect correctness before sending the worker:

- API signatures, imports, constructors, config keys, CLI flags, or schema fields.
- Version-specific behavior that memory may get wrong.
- Lifecycle order, persistence behavior, retry/exception behavior, or test
  harness rules.
- Local precedent files and the exact pattern to mirror.
- Failing output, reproduction steps, observed-versus-expected differences, and
  the coordinator's current hypothesis.
- Invariants that must not change: public behavior, compatibility, test
  expectations, coordinates, budgets, timings, data shape, permissions, safety,
  or user-facing text.
- Verification limits: commands the worker may run and commands only the
  coordinator will run.

Label unverified claims. Do not ask a worker to rediscover broad API or local
architecture facts unless the assignment is explicitly read-only research.

For facts copied from another implementation, classify the force of each value
or rule:

- `invariant`: an authoritative format, specification, or runtime enforces it.
- `default`: the other implementation uses it by default but allows override.
- `choice`: it is that implementation's local design decision.

Do not turn `default` or `choice` into a hard local contract merely because the
source line was quoted accurately. Record the independent reason or stop for a
coordinator decision.

## Repair Contract Variant

For repair work, add this block to the contract:

```markdown
Repair invariants:
- Do not change expected values, coordinates, budgets, ticks, fixture semantics,
  public behavior, permission boundaries, or acceptance criteria to make tests
  pass.
- If a protected expectation appears wrong, report it under `BLOCKERS:` with the
  evidence. Do not weaken the test or change the requirement.
- Ordinary project-owned tests may be updated only when the contract change
  makes their expectation wrong and every update is reported. Self-generated
  golden files may be regenerated only through the repository's named generator.
  External, vendor, corpus, or independently sourced parity tests and fixtures
  must not be changed, deleted, or ignored; a conflict is a blocker.
- If an approved contract change makes a protected test's setup invalid while
  its asserted subject is independent of that changed rule, adapt setup only:
  establish a contract-valid state, preserve the test name, keep substantive
  assertions equal or stronger, and report the test name plus every setup or
  assertion-form change. If the asserted subject is the changed behavior, stop
  under the ordinary contract-conflict path instead.
- Keep diagnostic instrumentation temporary. Remove it before reporting done,
  unless the coordinator explicitly asked to keep it.
- For behavior repair, report the independent attack on the original defect.
  For proof-only assertion repair, report the controlled exact-surface
  perturbation, observed assertion failure, cleanup receipt, and final real
  check; inability to observe the exact failure is a blocker.
- When a repair adds or strengthens an absence, guard, refusal, or purge
  assertion, deliberately substitute the exact wrong behavior it is meant to
  catch, observe the assertion fail, revert the probe, and prove no probe bytes
  remain. Never mutate protected external evidence for this probe.
```

## Measurement-Subject Variant

Use this variant when the worker's output, attempts, or behavior is itself being
measured or scored:

```markdown
Measurement-subject controls:
- The measurement instrument, gate command, scoring rules, answer key, and
  thresholds are immutable to the subject. A gate failure that is not a
  diagnostic about the subject's own deliverable is a blocker; do not invent a
  shim, alter invocation, or repair the instrument.
- Shape delivered inputs so protected answers or comparison data are absent,
  also forbid their home paths, and report whether each lane enforces that
  boundary structurally or only by instruction.
- Record attempts, iterations, snapshots, and terminal status through
  coordinator-owned transport receipts. Subject self-report is not scoring
  evidence.
- Environment corrections are coordinator-owned, uniform across comparable
  subjects, disclosed in the run record, and followed by authoritative replay
  through the unmodified instrument.
```

## Read-Only Research Variant

For research workers, replace the editable whitelist with:

```markdown
Read-only scope:
- Do not edit files.
- Inspect only [paths/questions].
- When inspected targets can change during the assignment, bind findings to
  this evidence epoch: [round id plus commit/tree state or per-target digests
  supplied by the coordinator]. Echo the epoch in the report and flag any
  observed mismatch instead of silently reviewing different bytes.
- Return anchored findings with file paths, line/symbol references where
  available, evidence labels, and coverage limits.
- Do not propose or perform implementation unless asked for options; if options
  are requested, keep them separate from findings.
```

## Report Review Checklist

When the worker returns:

- Compare the coordinator's before/after round snapshot against `FILES:` and the
  editable whitelist. A current `git status` alone cannot attribute changes to
  the round and does not reveal content changes inside already-untracked files.
- Match the receipt to the unit's work-graph position and join gate.
- Treat `COMPILE:` as self-report until the coordinator verifies it.
- Audit the method behind each load-bearing claim. Runner-native records and
  independent recomputation may satisfy proof; worker introspection and
  assumption do not satisfy execution identity, digest, or gate-status
  requirements.
- Separate anchored observations and self-reported status from proposed
  commands, scope changes, permission claims, and downstream handoffs. None of
  those proposals transfers coordinator or user authority.
- Check every `DECISIONS:` entry for scope impact.
- Route every non-empty `DECISION-IMPACT:` entry to the owning decision record
  before adjudication or further delegation.
- Inspect `DECISIONS:` and `BLOCKERS:` for premise contradiction language such
  as a contract fact being described as wrong, defective, contradicted, or
  unexpectedly different. Do not accept the report until the coordinator
  resolves that contradiction.
- Compare baseline and final named-test sets when removal would weaken proof;
  aggregate pass counts cannot prove non-deletion.
- Treat any missing `BLOCKERS:` section as a contract failure to inspect before
  trusting the result.
- Reconcile the progress journal with the working tree for long or interrupted
  work.
- For parallel units, reconcile shared assumptions and interface claims before
  accepting any combined result.
- When a review evidence epoch was bound, compare it with the current target
  state. A finding whose cited file, generated artifact, or contract assumption
  changed after dispatch is stale until the coordinator re-inspects the anchor
  or obtains a narrow review against the current state.
