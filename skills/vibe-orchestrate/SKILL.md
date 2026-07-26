---
name: vibe-orchestrate
description: Use when coordinating subagents for coding, research, repair, or review work where delegated workers may drift, stall, crash, duplicate, or edit a shared workspace and the coordinator must preserve scope, verification, and user-consent boundaries.
---

# Vibe Orchestrate

## Overview

Coordinate delegated agent work without surrendering responsibility. The
coordinator may ask subagents to research, edit, test, repair, or review, but
owns the contract, scope, verification, review adjudication, progress ledger,
commit boundary, and user-consent boundary.

This skill is an orchestration discipline for unstable or high-leverage
delegation. It is not a replacement for requirements capture, implementation
planning, execution from a bound plan, code review, commit execution, release
work, or debugging ownership. Use it inside those phases only when delegation is
the transport for bounded work.

The first version is reference-only guidance. It does not provide or require a
watchdog script, runner adapter, command wrapper, or transport fix.

## When to Use

Use this skill when:

- A coordinator will delegate code edits, test edits, repairs, research, or
  review to one or more subagents.
- A write-capable worker could explore unrelated files, guess missing APIs,
  exceed the allowed file set, run unsafe commands, or treat its own result as
  verified.
- A worker may stall, die, return partial work, inherit the wrong sandbox,
  duplicate a task, or leave uncertain shared-root edits.
- The coordinator needs a reusable delegation prompt, progress journal, recovery
  loop, watchdog concept, verification gate, review-disposition process, or
  parallel-writer accident protocol.
- The user wants the main agent to orchestrate while subagents do most bounded
  research or editing work.

Do not use this skill when no delegation is planned, when the user only wants a
small direct answer, or when a workflow phase must stop for missing requirements,
plan defects, user-risk consent, release/version authorization, credentials,
security, billing, destructive changes, or history mutation.

## Coordinator Ownership

Keep these responsibilities with the coordinator:

- Write the worker contract and decide the allowed scope.
- Authorize write paths and command classes.
- Run or verify final compile, test, build, and acceptance gates.
- Treat worker self-report as status, not proof.
- Adjudicate review findings before any repair work begins.
- Maintain the durable progress ledger when a bound plan provides one.
- Stage or commit only through the owning workflow's explicit invocation-level
  scoped permission or other explicit authorization. Release, tag, push, or
  mutate history beyond a local closure checkpoint only through
  operation-specific authorization.
- Ask the user for non-delegable decisions.

Subagents must not ask the user, expand scope, stage, commit, release, decide
credentials or permissions, accept destructive risk, mutate history, or make
human-risk choices for the coordinator.

When the active owning workflow can produce tracked changes and the host
requires separate confirmation for local commits, the coordinator asks once at
startup before delegating write work. Subagents never ask for or exercise that
permission. Read-only or no-change orchestration does not ask and does not
create an empty commit.

## Frontier Coordinator And Model-Tier Loops

When the host exposes both high-capability frontier models and cheaper, faster,
or previous-generation models, treat model choice as part of the delegation
contract. Keep decomposition, non-delegable decisions, final synthesis,
verification interpretation, review dispositions, and user-risk choices with the
coordinator or the strongest suitable reasoning/context tier available. Use
token-efficient delegated models for bounded work only when lower capability is
quality-neutral or the user has prioritized cost or latency.

Good token-saving loops reduce repeated context, not proof. Prefer this loop:

1. The coordinator verifies and inlines the facts, invariants, file boundaries,
   and decision criteria that a worker would otherwise rediscover.
2. Each delegated unit receives a compact context digest, one question or work
   item, explicit allowed paths/tools, expected receipt, and escalation triggers.
3. Token-efficient or previous-generation workers handle low-ambiguity lookup,
   extraction, mechanical checks, simple fixture comparisons, or narrow
   read-only review.
4. The coordinator verifies load-bearing anchors, reconciles contradictions,
   and decides whether to close, split, retry with a narrower contract, or
   escalate to a stronger reasoning/context tier.
5. Later loop iterations send only the changed facts, unresolved blockers, and
   latest verified state instead of the full parent transcript unless full
   context is necessary and the reason is recorded.

Escalate instead of repeatedly retrying a cheap delegate when the worker reports
uncertainty, hits a scope blocker, produces contradictory findings, needs
cross-artifact synthesis, touches security/data-safety or user-risk judgment,
would make a final recommendation, or fails the same contract twice. Do not
hard-code vendor model names into the skill contract, inherit the top model for
every small worker, downshift judgment-heavy work solely to save tokens, or
claim token, quality, latency, or reliability improvement without recorded
metrics or review evidence.

## Delegation Workflow

1. **Decide whether delegation is safe.** Keep work local when the next step is
   tightly coupled, urgent, unclear, or too risky to hand off. Delegate bounded
   side tasks that can succeed with a compact contract.
2. **Write a contract, not a casual request.** Use the template and variants in
   `references/delegation-contracts.md`.
3. **Inline verified facts.** Give workers the API signatures, local precedents,
   failure logs, invariants, and constraints they need. Do not make them wander
   through broad discovery when the coordinator can verify the fact first.
4. **Constrain reads, writes, and tools.** Name editable paths, forbidden paths,
   allowed commands, and stop conditions.
5. **Add a journal for meaningful write work.** If losing a worker would lose
   context, require a progress journal before edits.
6. **Monitor liveness and progress.** Use the concepts in
   `references/recovery-and-monitoring.md`: appearance, liveness, and staleness.
7. **Verify in the coordinator environment.** Follow
   `references/verification-and-review.md`; do not accept worker self-report as
   final proof.
8. **Run read-only review for substantial rounds.** Review output is inert until
   the coordinator classifies it.
9. **Recover deliberately.** On worker death, duplicate launches, or unexpected
   diffs, reconcile journals, working tree state, and file freshness before
   resuming, restarting, adopting, or discarding work.

## Worker Contract Minimums

Every write-capable delegation contract should include:

- Mission: one sentence with the slice and expected outcome.
- Hard rules: allowed tools, commands, forbidden reads, forbidden git actions,
  and stop-as-blocker behavior.
- Verified facts: APIs, versions, local patterns, failure logs, invariants, and
  unverified limits.
- Design contract: exact behavior, semantics, public names, or invariants that
  matter.
- Numbered work items with done criteria.
- Editable file whitelist and explicit out-of-scope paths.
- Optional progress journal path.
- Fixed report sections: `FILES:`, `COMPILE:`, `DECISIONS:`, `BLOCKERS:`;
  add `DIAGNOSIS:` for repair or investigation tasks.

If a worker needs a non-whitelisted file, broader command, credential,
permission, destructive action, or user decision, it must stop and report a
blocker instead of proceeding.

## Fact Inlining And Local Precedent

Before delegating implementation or repair, verify facts that would be expensive
or error-prone for a worker to rediscover:

- framework and API signatures;
- version-specific behavior;
- lifecycle, storage, or test-harness rules;
- local patterns to mirror;
- failing logs and observed-versus-expected differences;
- invariants that must not change.

Use local precedent as an anchor: point to the specific file or method pattern to
mirror. For repairs, name protected invariants such as test expectations,
coordinates, budgets, ticks, fixture semantics, public behavior, data shape, and
compatibility. If those invariants appear wrong, the worker reports a blocker;
it does not weaken them to pass.

## Crash Recovery And Monitoring

Read `references/recovery-and-monitoring.md` before launching a long or
write-capable worker. The coordinator should be able to answer:

- Did the worker appear after launch?
- Is the worker still alive by the host's reliable task handle or runner status?
- Has the journal or output changed recently enough for the task size?
- If it died, which work items are completed, partial, or untouched?
- Is resume safe, or should the coordinator start a self-contained new thread?
- Are unexpected write-capable workers still running?

Use host-provided task handles, cancellation APIs, or named runner controls when
available. Do not teach or normalize force-killing arbitrary raw PID lists. If a
recovery command may terminate the coordinator's own environment or this session,
warn the user and let them run it manually.

## Verification And Review

Read `references/verification-and-review.md` before accepting delegated work.
The coordinator verifies the bytes that will be kept:

- Enumerate relevant source sets, modules, generated sources, client/server
  targets, or package surfaces.
- Run the planned compile/test/build gates in the authoritative environment.
- Use quantitative evidence when test inclusion matters, such as total counts or
  expected count deltas.
- Record known flakes by name and symptom, with rerun evidence.
- Check for post-gate tree changes after suspicious deaths, duplicate workers,
  or delayed callbacks.
- Use read-only review perspectives for substantial work: contract fit,
  correctness/regression risk, and test sufficiency.
- Classify findings as accepted, rejected, deferred, or blocked before any
  repair contract is written.

## Direct Coordinator Intervention

Delegation is the default, but direct coordinator edits are allowed when they
are narrow and disclosed:

1. Mechanical micro-fix: trivial, well-understood, and cheaper than a delegation
   round.
2. Transport failure fallback: the same fully specified delegation fails
   repeatedly for runner or forwarding reasons.
3. Measurement-driven diagnosis: temporary instrumentation is needed to collect
   evidence before deciding a fix.

Disclose every direct intervention in the summary, run normal verification, and
remove temporary diagnostics before final handoff or commit.

## Parallel-Writer Accident Protocol

The default is one write-capable worker at a time. If a duplicate or stale writer
may have touched the tree:

1. Stop launching new write work.
2. Identify expected and unexpected worker handles.
3. Inspect status, diffs, journals, and file timestamps or hashes when useful.
4. Do not discard unexpected diffs blindly.
5. Adopt useful changes only after they fit the contract and pass normal gates.
6. Revert or replace unsuitable changes after inspection.
7. Re-check that no post-gate mutation happened before declaring verification.

## Example Evidence Policy

Rules in this skill are generalized guidance. Source-session stories may be used
as anonymized or anecdotal teaching examples in references. Do not present exact
incident counts, API names, test totals, timings, or session-specific
measurements as verified facts unless durable primary evidence is available in
the repository or cited source material.

## Output Discipline

When reporting delegated work, keep the coordinator summary evidence-bound:

- What was delegated and to whom, at the level the host can record.
- What files changed, from the coordinator's own status/diff view.
- What the worker self-reported, clearly labeled as self-report.
- What the coordinator verified, with commands or manual checks.
- What findings were accepted, rejected, deferred, or blocked.
- What remains unverified or outside scope.
- Whether any direct coordinator intervention happened.

Do not claim success from worker prose alone, a green subset when the plan
requires full coverage, or a review count without material finding dispositions.

## Common Mistakes

- Asking a worker to "look around" without a bounded read path.
- Letting a worker choose files, APIs, or tests that the coordinator could have
  specified from local evidence.
- Treating `COMPILE: PASS` in worker output as final proof.
- Retrying a timed-out launch in a way that creates two write-capable workers.
- Resuming an unhealthy or empty thread because it has a familiar name.
- Omitting a progress journal for work likely to outlive a worker crash.
- Accepting review findings as edits without coordinator disposition.
- Discarding an unexpected diff before checking whether it contains useful work.
- Adding runner-specific scripts or adapters when reference-only guidance is the
  agreed first slice.
- Naming neighboring workflow packages as dependencies instead of describing the
  required phase or capability.

## Self-Check

Before launching or accepting delegated work, confirm:

- Is the worker contract bounded by mission, hard rules, verified facts, work
  items, editable paths, and fixed report sections?
- Are missing facts classified as blockers or proof tasks instead of guesses?
- Did the worker receive enough local precedent and invariant guidance to avoid
  broad exploration?
- Is there a journal or other progress receipt for crash-prone write work?
- Are liveness, staleness, and appearance monitored by host-safe means?
- Is there exactly one write-capable worker for the shared tree unless an
  explicitly approved advanced workflow says otherwise?
- Did the coordinator verify the kept bytes with the required gates?
- Were read-only review findings dispositioned before repair?
- Were direct coordinator edits disclosed?
- Are exact anecdotal examples labeled correctly unless backed by durable
  primary evidence?
