# Delegation Contracts

Use this reference when writing a worker prompt for bounded research, editing,
test creation, repair, or review. A delegation prompt is a contract: it defines
what the worker may do, what it must not do, when it must stop, and how the
coordinator will verify the result.

## Contract Template

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
- Do not run git staging, committing, reset, stash, amend, rebase, tag, push,
  release, destructive, credential, billing, permission, or external-side-effect
  operations.
- Run only these verification commands, if any: [commands]. If blocked by the
  sandbox or host, report `COMPILE: SKIPPED(<reason>)` or equivalent.
- If the task needs a non-whitelisted file, broader command, missing fact,
  user decision, credential, destructive action, or invariant change, stop and
  report it under `BLOCKERS:`.

Verified facts:
- [API signature, version behavior, local convention, current failure log,
  known flake, accepted invariant, unverified limit]

Model and context budget:
- Capability tier: [token-efficient / standard / strongest suitable / user-fixed], because [quality-neutral lookup, broad synthesis, risk, or user priority].
- Context digest: [facts and anchors the worker needs; omit unrelated parent transcript].
- Escalate to coordinator or stronger reasoning/context tier when [contradiction, uncertainty, blocker, risk, or repeated failure].

Design contract:
- [classes, functions, files, data shapes, semantics, public behavior,
  compatibility, invariants, protected tests]

Work items:
1. [bounded item and done criterion]
2. [bounded item and done criterion]

Progress journal:
- Create or update [journal path] before the first meaningful edit.
- Append one line after each completed file edit or work-item transition.
- Include item id, file path, status, and blocker if any.

Report exactly these sections:
FILES:
- [changed files]
COMPILE:
- [PASS / FAIL / SKIPPED(reason), with command if run]
DECISIONS:
- [each discretionary choice made, or `none`]
BLOCKERS:
- [blockers, or `none`]
```

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

## Repair Contract Variant

For repair work, add this block to the contract:

```markdown
Repair invariants:
- Do not change expected values, coordinates, budgets, ticks, fixture semantics,
  public behavior, permission boundaries, or acceptance criteria to make tests
  pass.
- If a protected expectation appears wrong, report it under `BLOCKERS:` with the
  evidence. Do not weaken the test or change the requirement.
- Keep diagnostic instrumentation temporary. Remove it before reporting done,
  unless the coordinator explicitly asked to keep it.
```

## Read-Only Research Variant

For research workers, replace the editable whitelist with:

```markdown
Read-only scope:
- Do not edit files.
- Inspect only [paths/questions].
- Return anchored findings with file paths, line/symbol references where
  available, evidence labels, and coverage limits.
- Do not propose or perform implementation unless asked for options; if options
  are requested, keep them separate from findings.
```

## Report Review Checklist

When the worker returns:

- Compare `FILES:` against the editable whitelist.
- Treat `COMPILE:` as self-report until the coordinator verifies it.
- Check every `DECISIONS:` entry for scope impact.
- Treat any missing `BLOCKERS:` section as a contract failure to inspect before
  trusting the result.
- Reconcile the progress journal with the working tree for long or interrupted
  work.
