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

After a worker returns or dies:

- Check for unexpected still-running workers.
- Reconcile parallel receipts and shared interface assumptions before merging.
- Check whether files changed after coordinator verification.
- Treat delayed callbacks as suspect until the tree is rechecked.

## Parallel-Writer Accident Cleanup

If two write-capable workers may have touched the same tree:

1. Quarantine: stop new writer launches.
2. Identify expected and unexpected task handles.
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
