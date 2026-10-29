# Execution Workflow and Quality Reference

Read this when proving, reviewing, or closing a slice.

## Proving The Slice

- Verify every current-slice behavior the plan's high-risk sections mark as
  preserved, changed, or selected.
- For paired gates (visibility, permission, unlock, feature flag, state
  transition), prove both the positive and the negative path before edge
  hardening.
- Add a test beyond the plan only for an open obligation: a plan criterion no
  planned or existing test covers, a required proof obligation, plan-named
  preserved behavior, or a reachable failure mode of the changed code,
  including the inverse order after an ordering or lifecycle change. A test
  added for an uncovered plan criterion is a visible plan-preserving
  correction, never a silent one. Add no tests for extra assurance, and never
  drop, narrow, or skip a planned test outside the Plan Deviation Gate.
- When the slice changes a user-facing artifact or command, exercise it as its
  user would (build or open it, run the command); layer-level tests do not
  replace that observation.

## Post-Implementation Review Gate

Review the verified slice against the plan's acceptance criteria and
non-goals; the review running is not a pass.

- Use review-only subagents when the host offers a verified delegated-review
  capability, delegation is authorized, and the plan and diff are safe to
  share; otherwise run the same perspectives yourself and say so. Never claim
  a delegated review that did not run.
- Always include `plan-contract compliance` (acceptance criteria, non-goals,
  slice boundaries, approved deviations, scope leakage). Add
  `correctness/regression risk` and `test/proof adequacy` when capacity allows;
  otherwise pick the more relevant one.
- When the slice adds or changes hot-path code — code that runs per frame,
  tick, request, or chunk, or per item of a loop whose length depends on user
  input — also check it for unnecessary repeated work: a copy, parse, read, or
  rebuild of data the same operation already holds, where no ownership,
  freshness, validation, or snapshot reason calls for a fresh one. Remove such
  repetition the slice introduces. An optional performance mechanism — a cache
  that outlives the operation, a new index, or a new API that code outside the
  slice must adopt — needs a measured benefit and must fit the plan's
  non-goals; name any you leave out in the report.
- Reviewers only report: they do not edit, ask the user, decide deviations,
  classify findings, or commit, and tests they run are not proof. Verify each
  delegated finding before relying on it, then classify every material finding
  as `corrected`, `rejected`, `deferred`, `blocked`, or `reversed`; record
  `deferred` and `blocked` findings in the findings report.
- A finding `rejected` or `deferred` because its case is rare first records
  what happens when the case occurs, traced from source or a runtime check;
  evidence that the case cannot occur is enough instead. Rarity alone never
  dismisses a data-loss, security, permission, or core-path consequence the
  slice's own code causes: correct it in the slice when the fix is
  plan-preserving. Record any other such finding in the findings report with
  its traced consequence, or `Unproven` and its fastest proof path.
- A correction that changes control flow, ordering, lifecycle, concurrency,
  priority, timeout, fallback, or first-winner behavior is a new change: re-run
  at least the perspective that found the issue and check the inverse or
  symmetric failure mode before closing.
- Review the final diff after corrections, then verify the acceptance criteria
  yourself.

## Progress Ledger

When the plan has an `Implementation progress` section, verify any `Completed`
claim before relying on it, and after verification and review update only the
current item's status and evidence. Mark an item `Completed` only when all its
planned work is delivered and its verification and review are recorded;
otherwise record `In progress` or `Blocked` with the missing proof or
undelivered work and its next step. Never change contract sections through
the ledger, and never create a ledger the plan lacks; carry progress in the
summary instead.
