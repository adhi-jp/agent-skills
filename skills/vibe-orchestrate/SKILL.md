---
version: 1.0.0
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

Record that startup confirmation or denial in routing or workflow state and
reuse it at closure. Worker contracts explicitly forbid staging, committing,
pushing, releasing, and history mutation. The coordinator creates the final
checkpoint only after worker receipts, integration, authoritative verification,
review disposition, and safe file-set confirmation. Startup commit permission
does not extend to push, release or version changes, history rewriting,
destructive cleanup, or unrelated paths.

For a permission-and-ownership response, emit one compact receipt with all four
fields:

- `confirmation_state`: ask once before delegation; record and reuse the answer;
- `worker_boundary`: no stage, commit, push, release, or history mutation;
- `coordinator_gates`: receipts, integration, authoritative verification,
  review disposition, and safe file-set confirmation;
- `exclusions`: no push, release/version change, rewrite, destructive cleanup,
  unrelated path, or empty commit; read-only/no-change work does not ask.

## Coordinator Practice Reference

Read `references/coordinator-practices.md` before choosing delegated model or
capability tiers, decomposing substantial work, writing or auditing worker
contracts, inlining verified facts and protected evidence, directly intervening,
or handling multiple/overlapping writers.

Keep decomposition, non-delegable decisions, final synthesis, verification
interpretation, finding disposition, and user-risk choices with the coordinator
or strongest suitable reasoning/context tier. Save tokens by reducing repeated
context, not proof.


## Delegation Workflow

1. **Capture the pre-delegation baseline and evidence authority.** Before the
   first material worker contract, record the current tree state, relevant
   verification results, named tests or corpus behavior that must not disappear,
   and where the raw evidence is stored. For claim classes that can be confused
   by competing sources, rank the authoritative sources before adjudication:
   shipped or external artifacts for artifact-format claims, specifications for
   normative semantics, current runtime observation for runtime behavior, and
   measurements for performance. A citation proves what its source says; it
   does not prove that the source is authoritative for the current claim.
2. **Map the work graph before launching workers.** Identify the coordinator's
   immediate blocker, the tightly coupled sequence that benefits from one
   context owner, and independent units that can run without blocking the next
   local step. Do the immediate blocker locally unless delegation is itself the
   safest critical-path action.
3. **Choose the delegation shape deliberately.** Use multiple subagents
   actively when two or more material units are independent, bounded,
   separately verifiable, and safe to run concurrently or as separate work
   streams. Keep one worker for a tightly coupled slice when splitting would
   duplicate discovery, create handoff loss, or require shared judgment on
   every step. Do not default to one monolithic worker merely because it can
   hold the whole task, and do not fan out merely because the task is large or
   the host exposes spare capacity.
4. **Write a contract, not a casual request.** Use the template and variants in
   `references/delegation-contracts.md`, and apply
   `references/coordinator-practices.md` for decomposition, model/context
   choice, fact inlining, protected evidence, and writer controls.
5. **Inline verified facts with provenance and force.** Give workers the API
   signatures, local precedents, failure logs, invariants, environment
   constraints, and derived-value assumptions they need. Distinguish measured
   facts from calculations and distinguish specification invariants from a
   reference implementation's configurable default or local design choice.
6. **Constrain reads, writes, and tool effect scope.** Name editable paths,
   forbidden paths, allowed commands, and stop conditions. A file whitelist does
   not authorize repository-wide formatters, fixers, codemods, dependency
   updates, or generators that can modify files outside the whitelist.
7. **Add a journal for meaningful write work.** If losing a worker would lose
   context, require a progress journal before edits.
8. **Monitor liveness and progress.** Use the concepts in
   `references/recovery-and-monitoring.md`: appearance, liveness, and staleness.
   Re-arm monitors before host lifetime limits, keep an independent fallback
   wake, and send user updates only at unit start, actionable blocker change, or
   verified unit-boundary change unless the user requested a cadence.
9. **Verify in the coordinator environment.** Follow
   `references/verification-and-review.md`; do not accept worker self-report as
   final proof.
10. **Run read-only review for substantial rounds.** Review output is inert until
   the coordinator classifies it.
    Direct coordinator repair is allowed only for a diagnosis-complete,
    fully-specified bounded correction or a coordinator-only verification
    capability; it never absorbs new design or human-risk decisions.
11. **Recover deliberately.** On worker death, duplicate launches, or unexpected
   diffs, reconcile journals, working tree state, and file freshness before
   resuming, restarting, adopting, or discarding work.


## Crash Recovery And Monitoring

Read `references/recovery-and-monitoring.md` before launching a long or
write-capable worker. The coordinator should be able to answer:

- Did the worker appear after launch?
- Is the worker still alive by the host's reliable task handle or runner status?
- Has the journal or output changed recently enough for the task size?
- If it died, which work items are completed, partial, or untouched?
- Is resume safe, or should the coordinator start a self-contained new thread?
- Are unexpected write-capable workers still running?
- If the transport returned a task handle instead of the contracted report, is
  the runner task terminal by its own status, and was the report retrieved
  through its result interface?

Use host-provided task handles, cancellation APIs, or named runner controls when
available. Do not teach or normalize force-killing arbitrary raw PID lists. If a
recovery command may terminate the coordinator's own environment or this session,
warn the user and let them run it manually.

## Verification And Review

Read `references/verification-and-review.md` before accepting delegated work.
The coordinator verifies the bytes that will be kept:

- Compare the post-worker tree with a recorded round-boundary baseline, including
  untracked and non-text artifacts relevant to the whitelist.
- Carry every input-named touched path and verification target into the
  acceptance receipt. Do not collapse named server, client, test, or generated
  surfaces into generic phrases such as "relevant files" or "relevant gates."
- State gates at the same granularity as those named surfaces: if both server
  and client targets changed, name both compile/type-check targets; if a new or
  changed test file is named, require quantitative inclusion evidence when the
  harness supports it. "Run compile and relevant tests" is not an auditable
  receipt for explicit surfaces.
- Enumerate relevant source sets, modules, generated sources, client/server
  targets, or package surfaces.
- Run the planned compile/test/build gates in the authoritative environment.
- Use quantitative evidence when test inclusion matters, but pair aggregate
  counts with named-test or equivalent set differences when deletion matters.
- Check whether proof assertions could fail when the implementation is wrong;
  a green test with an unused spy, target-imported expectation, best-case-only
  input, or missing lifecycle branch is not proof.
- Record known flakes by name and symptom, with rerun evidence.
- Check for post-gate tree changes after suspicious deaths, duplicate workers,
  or delayed callbacks.
- Use read-only review perspectives for substantial work: contract fit,
  correctness/regression risk, and test sufficiency.
- Classify findings as accepted, rejected, deferred, or blocked before any
  repair contract is written.


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
- Treating a worker's failure as a product defect before reproducing it in the
  authoritative environment.
- Treating a cited reference implementation as the authority for shipped bytes,
  normative semantics, or product limits without classifying the claim.
- Letting a worker resolve a contradiction between the contract and protected
  external evidence.
- Using a passing-test total to infer that no named test or external parity
  property disappeared.
- Retrying a timed-out launch in a way that creates two write-capable workers.
- Treating a forwarder's handle-only completion as work completion and freeing
  the shared-tree writer slot while the runner task is still active.
- Trusting a coordinator receipt chain whose output filters can replace a
  failing gate's status with a successful filter or aggregate status.
- Collapsing input-named touched paths, source targets, compile gates, or
  expected new-test evidence into an uncheckable "run compile and relevant
  tests" summary.
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
- Was the pre-delegation tree, named-test or corpus behavior, and relevant raw
  verification evidence captured before the first material write round?
- Are source authority, derived-value assumptions, and protected external
  evidence explicit where they affect the decision?
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
- For a handle-returning transport, did runner-native terminal status and result
  retrieval precede final tree inspection, verification, or the next writer?
- Is there at most one write-capable worker in each shared tree, with any
  concurrent writers confined to isolated, disjoint workspaces?
- Did the coordinator verify the kept bytes with the required gates?
- Does the acceptance receipt explicitly cover every path and target named in
  the input, including quantitative inclusion evidence for expected new tests?
- Does the verification receipt preserve each gate's exit status independently
  of output truncation, filtering, or aggregate shell status?
- Did coordinator verification compare the round-boundary change set with the
  worker's `FILES:` report and inspect non-text or untracked outputs?
- Could each load-bearing proof assertion actually fail under the old or wrong
  behavior?
- Were read-only review findings dispositioned before repair?
- Were direct coordinator edits disclosed?
- Are exact anecdotal examples labeled correctly unless backed by durable
  primary evidence?
