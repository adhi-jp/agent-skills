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

1. **Map the work graph before launching workers.** Identify the coordinator's
   immediate blocker, the tightly coupled sequence that benefits from one
   context owner, and independent units that can run without blocking the next
   local step. Do the immediate blocker locally unless delegation is itself the
   safest critical-path action.
2. **Choose the delegation shape deliberately.** Use multiple subagents
   actively when two or more material units are independent, bounded,
   separately verifiable, and safe to run concurrently or as separate work
   streams. Keep one worker for a tightly coupled slice when splitting would
   duplicate discovery, create handoff loss, or require shared judgment on
   every step. Do not default to one monolithic worker merely because it can
   hold the whole task, and do not fan out merely because the task is large or
   the host exposes spare capacity.
3. **Write a contract, not a casual request.** Use the template and variants in
   `references/delegation-contracts.md`.
4. **Inline verified facts.** Give workers the API signatures, local precedents,
   failure logs, invariants, and constraints they need. Do not make them wander
   through broad discovery when the coordinator can verify the fact first.
5. **Constrain reads, writes, and tools.** Name editable paths, forbidden paths,
   allowed commands, and stop conditions.
6. **Add a journal for meaningful write work.** If losing a worker would lose
   context, require a progress journal before edits.
7. **Monitor liveness and progress.** Use the concepts in
   `references/recovery-and-monitoring.md`: appearance, liveness, and staleness.
8. **Verify in the coordinator environment.** Follow
   `references/verification-and-review.md`; do not accept worker self-report as
   final proof.
9. **Run read-only review for substantial rounds.** Review output is inert until
   the coordinator classifies it.
10. **Recover deliberately.** On worker death, duplicate launches, or unexpected
   diffs, reconcile journals, working tree state, and file freshness before
   resuming, restarting, adopting, or discarding work.

## Multi-Subagent Decomposition

For substantial work, record a compact work graph before delegation:

- `critical_path`: the next coordinator-owned step or delegated unit whose
  result is required before later decisions can be made;
- `parallel_units`: independent research, implementation, test, migration,
  documentation, or review units that do not block that next step;
- `coupling`: shared APIs, files, schemas, generated artifacts, decisions, or
  verification gates that constrain execution order;
- `execution_shape`: serial, parallel, or hybrid, with a short reason;
- `join_gate`: the coordinator check that reconciles results before dependent
  work, final verification, or user-facing claims.

Prefer a hybrid shape for large refactors: keep the immediate load-bearing
decision or tightly coupled core local or with one context-owning worker, while
launching other material independent units to separate subagents. Use multiple
read-only workers freely when their questions and evidence surfaces are
distinct. Use multiple write-capable workers only when their write sets and
generated outputs are disjoint and the host provides isolated workspaces or an
equivalent enforceable isolation boundary. Otherwise keep one shared-root
writer and parallelize read-only investigation, test design, review, or other
non-writing units.

Each parallel unit needs its own mission, allowed paths, expected receipt,
budget, stop conditions, and verification responsibility. The coordinator must
continue meaningful non-overlapping local work after launch rather than
launching the immediate blocker and waiting reflexively. At the join gate,
verify each receipt, reconcile contradictions and interface assumptions, and
re-run the authoritative integrated gates on the combined bytes.

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

The default in one shared working tree is one write-capable worker at a time.
Concurrent writers are an advanced isolated-workspace shape: they require
separate worktrees or sandboxes, disjoint write and generated-output paths,
explicit merge order, and an integrated verification gate before any result is
accepted into the coordinator's tree. If a duplicate, stale, or unexpectedly
overlapping writer may have touched the same tree:

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
- Sending a substantial refactor to one monolithic worker without first
  checking for material independent units that could run separately.
- Launching many workers only because the task is large, even though their
  inputs, files, or decisions are tightly coupled.
- Delegating the immediate critical-path blocker, then waiting while no
  non-overlapping coordinator work proceeds.
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
- Did substantial work get a work-graph decision that identifies the critical
  path, material independent units, execution shape, and join gate?
- If multiple subagents would materially help, were they used with separate
  bounded contracts rather than collapsed into one monolithic assignment?
- If only one worker was used for substantial work, is the coupling or
  coordination-overhead reason explicit?
- Are missing facts classified as blockers or proof tasks instead of guesses?
- Did the worker receive enough local precedent and invariant guidance to avoid
  broad exploration?
- Is there a journal or other progress receipt for crash-prone write work?
- Are liveness, staleness, and appearance monitored by host-safe means?
- Is there at most one write-capable worker in each shared tree, with any
  concurrent writers confined to isolated, disjoint workspaces?
- Did the coordinator verify the kept bytes with the required gates?
- Were read-only review findings dispositioned before repair?
- Were direct coordinator edits disclosed?
- Are exact anecdotal examples labeled correctly unless backed by durable
  primary evidence?
