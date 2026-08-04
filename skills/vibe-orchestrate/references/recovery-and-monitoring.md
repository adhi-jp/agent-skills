# Recovery And Monitoring

Use this reference for long-running or write-capable delegated tasks. It is
reference-only guidance; it does not require a runnable watchdog script.

## Progress Journals

Create a journal when a worker death would lose meaningful context.

Recommended entry shape:

```markdown
- [timestamp or sequence] item=[id] file=[path or none] status=[started|edited|verified|blocked] note=[short note]
```

Rules:

- The first worker action is creating or opening the journal.
- Append after each meaningful file edit or work-item transition.
- Never mark an item complete from memory when the journal and working tree do
  not support it.
- Keep journals untracked unless the user explicitly wants them saved.
- Remove or exclude journals before commit or final handoff.

## Worker Death Recovery

When a worker dies, times out, or returns partial output:

1. Stop launching new write-capable work.
2. Use host task handles or runner status to identify whether the worker is
   dead, still running, duplicated, or unknown.
3. Reconcile the journal with `git status`, diff, and file contents.
4. Classify each work item as completed, partial, untouched, or blocked.
5. Decide resume versus restart:
   - Resume the same thread only when the thread context is valuable and the
     runtime state is healthy enough to trust.
   - Start a self-contained new thread when the old thread is empty, unhealthy,
     duplicated, inherited a bad sandbox, or has ambiguous state.
6. In the next contract, list completed items as `do not repeat` and remaining
   items as the only editable work.
7. Verify any kept bytes through coordinator gates.

An outer launch failure or missing receipt does not prove that no work landed.
Before relaunch, inspect the round baseline-to-tree diff and any report or
journal, salvage coordinator-verified analysis and premise contradictions, and
classify every contract item as completed, partial, untouched, or blocked.

Use this receipt decision:

| Receipt state | Relaunch / writer-slot decision | Evidence treatment |
| --- | --- | --- |
| Available and consistent | Release only after terminal/process absence and final tree audit | May become coordinator-verified evidence |
| Absent but independently observable from named task/process/tree carriers and non-critical | Hold until those carriers prove terminal and allowed-path quiescence | Record degraded evidence and the missing field |
| Absent and not independently observable for a contract-critical fact | Hold the slot and block relaunch/acceptance | `Unproven` blocker; use named cancellation or user recovery |
| Contradictory | Hold and reconcile; never choose the convenient channel | All channels remain untrusted |
| Outer failure with tree/report residue | Audit diff and report before relaunch | Adopt only after ordinary review and verification |

Derive the quiescence budget from the contract's longest legitimate quiet
command and observable descendant/task state; do not hard-code a quiet period.
If descendants or the legitimate quiet phase cannot be observed, quiescence is
not proven.

## Watchdog Concepts

Completion-only notification is not enough. Monitor these conditions using the
host's reliable signals:

- **Appearance timeout**: a launched task does not appear in the runner or host
  task list within the expected window.
- **Liveness**: the task handle, runner record, or process status shows the
  worker is dead or unreachable.
- **Progress staleness**: the journal, output receipt, or task activity has not
  changed for longer than the task's expected quiet period.

Suggested starting thresholds are appearance around 5 minutes, staleness around
10 minutes, and polling around 20 seconds. Adjust for task size, runner behavior,
and known long quiet phases.

`running` is not progress proof. When the journal, output, or activity receipt
exceeds the predeclared staleness budget, treat the unit as stalled regardless
of a live process or task status and start the recovery classification. A fixed
startup log whose size does not change is a staleness signal, not evidence that
the worker is working.

### Handle-Returning Transports

Some delegation transports are forwarders: the visible subagent starts work on
a separate runner and returns only a task handle, status interface, or resume
identifier. That completion proves the handoff returned, not that the delegated
work finished. The receipt shape is the deciding evidence; short elapsed time or
tree quietness alone proves neither completion nor failure.

When the receipt contains a handle instead of the contracted report:

- adopt the runner-native task handle and any session or resume identifier as
  coordinator state immediately;
- keep the unit and its write-capable slot active until the runner's own status
  interface records a terminal state;
- do not treat the tree as final, start authoritative final verification, or
  launch another shared-tree writer while the runner is non-terminal;
- fetch the contracted report through the runner's named result interface after
  terminal status instead of treating the forwarder's receipt as the result;
- use named resume, attach, status, or cancellation controls when a handle is
  lost or stale, and relaunch only after the original task is proven absent or
  dead.

A retry while the runner task remains active is a duplicate-writer risk, even
when the forwarding subagent has already disappeared from the host task list.

Resume or attach binds to a specific session role and sandbox contract, not
merely a thread id. Prefer a fresh self-contained write round after read-only
work unless the exact session and role are named and actual role receipts match.
Read back host-exposed model/effort/write/cwd/task metadata after launch and
compare it with the contract; requested settings are not execution receipts.
Transport lifetime is a unit-sizing constraint: split repeated over-window
units, keep coupled splits serial, and record the transport-driven reason
without claiming work-graph independence.

Before fanning out over a delegation transport, command form, background mode,
or flag combination not yet used in the current session, run one minimal
round-trip canary and verify a known short receipt. Shared transport mistakes
replicate to every worker; capacity is not a reason to skip the canary.

## Loop Engineering For Long Delegations

Use checkpoint loops instead of repeated full-context retries. A useful loop
state includes the current contract id, completed items, partial items, blockers,
changed paths, last coordinator-verified evidence, and the next bounded
question. Send that state as a compact digest to the next worker and keep the
parent transcript out unless a specific ambiguity requires it.

If a token-efficient worker stalls, contradicts another worker, exceeds the
read/write boundary, or fails the same contract twice, do not keep relaunching
the same cheap prompt. Request a checkpoint, split the task, handle the
load-bearing step locally, or escalate to a stronger reasoning/context tier.
Token savings are a budget signal; they do not justify accepting unverified or
low-quality work.

## Safe Cancellation

Prefer, in order:

1. Host-provided task cancellation.
2. Runner-provided named cancellation for the exact task handle.
3. A user-run manual recovery step when the command would terminate the
   coordinator's own environment, shell, container, VM, WSL session, or agent
   runtime.

Do not normalize force-killing arbitrary raw PID lists. If a PID-specific action
is unavoidable, first prove the process identity and ask the user when there is
any chance it belongs to the active agent environment.

## Concurrent-Writer Controls

Before launching a write-capable worker:

- Check the host or runner for active write-capable tasks in the same workspace.
- Permit only one write-capable worker in a shared working tree.
- Confirm its editable whitelist and generated-output paths do not overlap with
  another active writer.
- Require an isolated workspace or equivalent enforceable isolation boundary
  for concurrent write-capable workers.
- Record the merge order and the integrated coordinator verification gate.
- Record the expected worker handle or thread identity.
- Immediately after launch, re-check active writers. Timeout retries and
  forwarding retries are duplicate-launch risks until the original handle is
  proven absent.

After a worker returns or dies:

- Check for unexpected still-running workers.
- Reconcile parallel receipts and shared interface assumptions before merging.
- Check whether files changed after coordinator verification.
- Treat delayed callbacks as suspect until the tree is rechecked.

## Parallel-Writer Accident Cleanup

If two write-capable workers may have touched the same tree:

1. Quarantine: stop new writer launches and cancel every unintended overlapping
   writer through the host's named task control. Do not continue waiting after
   merely logging a duplicate warning.
2. Identify the one intended writer and every unexpected task handle.
3. Capture current `git status`, relevant diffs, journal entries, and file
   modification evidence.
4. Do not discard unexpected diffs blindly.
5. Compare each unexpected change to the intended contract.
6. Keep a useful change only after review, reconciliation, and normal
   verification gates.
7. Revert or replace unsuitable changes after inspection.
8. Re-run necessary gates on the final kept tree.

Unexpected work that is useful may still need recalibration. A test or patch from
a stale worker is not safe until it matches the behavior contract and passes the
coordinator's proof path.
