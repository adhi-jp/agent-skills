# Recovery And Monitoring

Read before long or write-capable delegation, or when a transport stalls or
returns uncertain state. These procedures do not require a watchdog script.

## Progress Journals

Use a journal when worker death would lose meaningful context. Create/open it
before edits and append item ID, path, status, and blocker at meaningful edits
or work-item transitions. Reconcile it with actual bytes before calling an item
complete. Give each unit private, disjoint journal/scratch paths; foreign or
unexplained content blocks use until reconciled. Keep journals untracked unless
the user requests otherwise, and remove/exclude them before commit or handoff.
Use progress channels for ordinary activity, reserving terminal reports for
completion or actionable blockers.

## Watchdog Concepts

Monitor appearance, liveness from native task status, and progress staleness
separately. Set appearance/staleness budgets from task size and the longest
legitimate quiet phase. A live `running` status with stale output still requires
recovery classification; an unchanged startup log is not progress proof.

Prefer delivered completion/failure signals, then bounded status queries, then
incremental journal/output reads. Re-reading growing transcripts spends the
coordinator's adjudication budget; repeated unchanged reads indicate a poor
monitoring mechanism. Do non-overlapping work between checks and avoid fixed
short polling intervals.

Re-arm monitors before host callback lifetime limits and retain an independent
fallback wake. Monitor expiry is not worker death. After obtaining the native
handle, stop polling the old forwarder while retaining runner-task ownership.
Cancel monitors/wakes at acceptance or cancellation; mark uncancellable wakes
as future no-ops. Pollers need an exact captured handle and hard deadline, not
process-name predicates that can match themselves. Shell job-control state
may not persist between tool calls.

Report meaningful starts, changed blockers, and verified progress; suppress
unchanged polling unless the user requested a cadence. A recovery update names
proof/review state, preserved work, and the next recovery action.

## Handle-Returning Transports

A forwarder's completion proves only handoff when its receipt contains a handle
instead of the contracted product. Adopt native task/session identifiers and
keep the writer slot active while status is non-terminal. Do not verify the tree
as final, start another shared-tree writer, or relaunch yet.

Status is the liveness authority; fetch the report through the result interface
after terminal status. A live task with `result: not found` is not lost.
Contradictory status/result receipts must be reconciled, not selectively trusted.
Use named status/attach/resume/cancel controls for missing handles; elapsed time
or a quiet tree does not prove death.

Before fan-out on an untried transport, command form, background mode, or flags,
verify one minimal round-trip canary. Compare observed host metadata
(model/effort/role/sandbox/cwd/task) with the contract after launch; requested
settings are not receipts. Resume only the exact session and matching observed
role/sandbox; otherwise start a fresh self-contained write round after read-only
work. Split repeated over-window units to fit transport lifetime, keeping
coupled splits serial rather than claiming independence.

## Worker Death Recovery

1. Stop new writes. Check native task/process status, possible duplicates, late
   reports, journal freshness, and the baseline-to-current tree diff. A host
   failure notification or outer launch failure does not prove nothing landed.
2. Hold the writer slot until terminal/process absence, report retrieval, and
   allowed-path/descendant quiescence reconcile. For a missing non-critical
   receipt, independent task/process/tree evidence may substitute with a
   disclosed limitation. Missing contract-critical facts or contradictions
   remain `Unproven` blockers.
3. Derive quiescence from the longest legitimate quiet command and observable
   descendants. If either is unobservable, do not substitute a fixed quiet wait;
   use named cancellation or user recovery.
4. Classify each work item as completed, partial, untouched, or blocked from
   journal and bytes. Salvage useful analysis and premise contradictions only
   after coordinator verification.
5. Resume only a healthy context worth preserving. Restart unhealthy, empty,
   duplicated, wrong-sandbox, or ambiguous threads with a compact contract:
   completed work is `do not repeat`; only remaining items are editable.
6. Verify the final kept bytes through ordinary review and coordinator gates.

## Concurrent-Writer Controls

Apply isolation rules from `coordinator-practices.md`. Check active writers
before and immediately after launch, capture an attributable baseline every
round, and retain the expected handle. Timeout/forwarding retries can duplicate
a writer until the original is proven absent. At joins, reconcile shared
assumptions and check for delayed post-verification writes.

For overlapping, stale, or duplicate writers: stop launches; identify the intended
and unintended handles; cancel unintended overlapping tasks through named
controls; inspect diffs, journals, and freshness. Do not blindly discard useful
work. Adopt only contract-fitting changes after normal review/verification;
replace or discard unsuitable changes within authority. Recheck the final tree
for post-gate mutation and repeat affected gates.

## Safe Cancellation And Capability Loss

Prefer host cancellation, then runner cancellation for the exact handle.
Never force-kill arbitrary PID lists. Prove identity for PID-specific actions;
if recovery could terminate the coordinator's environment/session, warn and
leave execution to the user.

On new loader, interop, command-availability, platform, or permission failures,
probe the execution capability before blaming product code. Mark affected gates
blocked-not-failed, name restoration and owner, continue independent work, and
re-probe unexplained recovery. At closure audit workspace-scoped workers,
harnesses, servers, and descendants: parent exit does not prove children exited.
Stop survivors only by named or identity-proven workspace-scoped controls.
