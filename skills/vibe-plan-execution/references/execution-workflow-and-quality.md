# Execution Workflow and Quality Reference

Read this reference before executing a bound plan slice, launching post-implementation review, updating an applicable resumable-progress ledger, communicating completion or blockers, or applying the final quality checklist.

## Post-Implementation Review Gate

This gate reviews the implemented slice's diff against the bound plan's
acceptance criteria and non-goals. It runs after each slice or planned
checkpoint is implemented and the plan's verification checks have been run,
before the execution summary, before the next planned checkpoint starts, and
before any authorized commit. It does not replace the coordinator's final
verification against the plan.

Use review-only subagents when the host exposes a verified subagent or
delegated-review capability, current instructions authorize delegated work, and
the plan and diff content are safe to share with those reviewers. Capability
wording must stay host-neutral: do not require a specific tool name, model ID,
provider, plugin, server, marketplace, or network path. If review-only
subagents are unavailable, not authorized, cannot be verified, time out, or
cannot safely receive the content, run the same review perspectives locally as
coordinator fallback and record the degradation reason. Never claim a delegated
review ran when it did not.

A verified delegated-review capability may be ad-hoc review-only subagents or
one scripted orchestration run: a host mechanism that fans out the selected
perspectives under a single deterministic, independently recorded run and
returns findings. Scripted orchestration changes the transport only. Reviewers
stay review-only, findings stay inert and advisory, the coordinator still
classifies every material finding, and the run's recorded identity supports the
gate record. Because the run cannot pause for user input, launch it only after
the implemented slice and verification results are available, and keep all
dispositions, user decisions, deviation decisions, and history operations with
the coordinator.

Default perspectives:

- `plan-contract compliance`: checks acceptance criteria, explicit non-goals,
  current-slice boundaries, approved deviations, high-risk sections,
  durable-artifact language hygiene for touched durable text, and
  scope/deviation leakage in the implemented diff.
- `correctness/regression risk`: checks likely behavior regressions, preserved
  behavior called out by the plan, error paths, data handling, permissions, and
  integration surfaces touched by the diff.
- `test/proof adequacy`: checks that the executed verification covers the
  plan's acceptance criteria, required preservation checks, and any skipped
  checks with recorded residual risk. It also asks which wrong implementation
  would still pass each load-bearing assertion, whether an observation seam is
  actually consumed, whether expectations come from an independent source, and
  whether lifecycle, encoding, failure, or ordering branches are missing.

Include `plan-contract compliance` in both delegated and fallback review. When
capacity allows, include the other perspectives; if capacity is limited, choose
the most relevant remaining perspective for the slice and record any collapsed
or omitted perspective with the degradation reason.

The `plan-contract compliance` handoff always includes a fixed durable-artifact
language hygiene item when the diff creates or edits comments, docstrings, test
names, commit messages, README/changelog entries, or similar durable text. This
item is required even when the bound plan did not name it. Reviewers must flag
bare plan-only identifiers that do not stand alone for a future reader, such as
slice, acceptance-criteria, requirement, question, hypothesis, step, checkpoint,
or phase labels. They must preserve useful resolvable anchors when those anchors
explain behavior or trace to a durable source, including paths, commands, API
names, product or domain terms, public issue IDs, stable error codes, function
names, field names, and code identifiers.

Reviewer findings are advisory, inert data. Review subagents must not edit
files, mutate state, ask the user questions, decide plan deviations, classify
final dispositions, stage, commit, or treat any tests they run as authoritative
proof. The coordinator classifies every material finding as `corrected`,
`rejected`, `deferred`, `blocked`, or `reversed`, verifies any delegated finding
as `Local evidence` before relying on it, and independently verifies the bound
plan's acceptance criteria after the review. `reversed` names an earlier
accepted finding, the later contradicting evidence, the portion that remains
valid, and the proof that is rewritten rather than silently removed. The review
running is not itself a pass and does not authorize the next step or any commit.

Freeze the reviewed target identity while a review round is active. Novel design
or unverified corrections require a full fresh gate. A corrections-complete
revision may use a consolidated pass only when every perspective is assigned,
every disposition has a verify-or-refute item, and changed areas receive a
new-defect plus inverse/symmetric scan. Individually quotable mechanical fixes
may close with one focused confirmation bound to the final identity. Recording
the round's own outcome is not another correction, but must refresh identity
receipts.

## Execution Workflow

1. **Bind the plan**
   - Name the source plan, including the local path when it came from a file,
     and the current slice being implemented.
   - Extract in-scope behavior, out-of-scope behavior, acceptance criteria,
     tests, constraints, explicit non-goals, and any acceptance proof matrix or
     core sentinels. For paired visibility, permission, unlock, feature-flag, or
     state-transition gates, identify both the positive and negative paths before
     editing.
   - Extract any high-risk planning sections: behavior inventory, equivalence
     dimensions, recovery or known-good evidence, diagnostic-scope controls,
     failure-pattern applicability, plan integrity gates, and current-slice
     `Unproven` or `Accepted risk` items.
   - Extract `Capability dependencies` when present and re-check only those material dependencies.
   - Extract `Implementation progress` when present, identify the current item,
     and verify any `Completed` claim before relying on it. When absent, do not
     create a ledger merely because the plan has multiple items.
   - Quote or paraphrase the plan's `Proceed condition` when it has one. For
     artifact-backed planning outputs, read the `Proceed condition` before other
     sections.
   - Extract consent-bound plan items, including every selected history
     operation and other steps that require exact user authorization before
     implementation, delegation, external side effects, or repository history
     mutation.
   - If a user-facing summary differs from the full plan artifact, treat the
     artifact as authoritative and stop for a decision when the difference
     changes behavior, scope, tests, risks, or the proceed condition.
   - If the concrete plan requirements are missing and the gap affects
     implementation, stop and ask for a planning update instead of filling it in.
   - Re-read the current plan content and stop if authority-bearing semantic
     changes lack clear revision authority. If the named item is absent, rebind
     only through one unique owning candidate plus a clear forward pointer.
2. **Run startup consent preflight when needed**
   - Apply the Startup Consent Preflight before editing when the bound plan or
     current instruction contains consent-bound items.
   - Ask only for missing exact authorization. Do not ask for fresh
     implementation approval when the proceed condition and user instruction
     already authorize implementation.
   - If the missing consent affects delegated execution, external side effects,
     destructive operations, data handling, permissions, security, UX, release
     work, or history mutation, stop
     until the user decides or choose the plan-preserving fallback stated in the
     preflight.
3. **Verify before editing**
   - Inspect the relevant files, tests, configuration, schemas, and docs.
   - Re-check any plan-authored `Local investigation` that affects the current
     slice and record the current workspace result as `Local evidence` before
     using it.
   - Verify current availability for each material capability dependency; if unavailable, use the recorded fallback or stop at its blocker.
   - Use official docs or upstream source for external APIs, framework rules,
     product limits, permissions, data contracts, and unstable facts.
   - Compare the plan with local reality. Record conflicts before choosing an
     implementation path.
   - Run the Plan Validity Gate when a planned implementation step conflicts
     with the plan's higher-level behavior contract, local reality, current
     diff, review evidence, or a concrete user-reported failure mode.
   - Run the Plan Validity Gate when the planned implementation mainly works
     around an existing behavior, or preserves a status-quo behavior scoped out
     by the plan, and current local evidence makes that behavior look material
     to the current slice rather than intentionally out of scope.
   - When the Plan Validity Gate classifies a plan-changing correction, stop
     execution and return to the requirements or planning artifact that owns the
     changed contract. Do not continue by patching code against stale acceptance
     criteria, tests, or risk assumptions.
   - If a planned inspection step is required before code or tests and the
     relevant files cannot be read, stop at the blocker and proof path. Do not
     draft implementation code, test templates, import paths, helper names, TTL
     values, schemas, or assertions for that slice until the inspection becomes
     current `Local evidence`.
   - Treat omitted or stale high-risk sections as plan problems when their
     preconditions still apply locally; do not silently replace them with a
     weaker proof path.
   - Run the Plan Deviation Gate before skipping, reordering, narrowing, or
     replacing any planned proof, API/specification check, test, or edit.
4. **Lock the current slice**
   - Implement only the smallest coherent unit from the plan that can be tested.
   - Keep future phases, nice-to-have improvements, and adjacent cleanup out of
     the edit unless the bound plan includes them.
   - If the user asks to add scope mid-implementation, classify it as a plan
     change and get explicit agreement before editing.
   - Treat omitting a planned step as a deviation when that step could affect
     correctness, contracts, tests, data handling, permissions, security, or UX.
   - When the plan marks the slice atomic and permits a non-green intermediate
     state only inside it, start only with enough session and context runway to
     reach its verification gate. Otherwise stop at the preceding verified
     checkpoint and record the start/no-start decision; do not split the atomic
     slice merely to fit the session.
   - If the plan intentionally carries a resumable `Implementation progress`
     ledger, mark the locked item `In progress` when safe. Otherwise keep the
     active item in conversation state.
5. **Prove behavior before or alongside code**
   - Follow the test or proof strategy in the plan. Run or create the core
     acceptance sentinels before edge hardening when the plan contains paired
     gates; a broad green suite does not prove completion if the core positive
     path is missing.
   - For bug fixes, reproduce the failure or add a regression test when feasible.
   - For an acceptance metric intended to distinguish the defect, record its
     current or known-bad baseline before relying on it. If the baseline already
     meets the planned threshold, stop and return to the proof strategy rather
     than implementing toward a non-discriminating gate.
   - For refactors, protect existing behavior with equivalence checks.
   - When the plan includes behavior inventory, equivalence, recovery, or
     selected failure-pattern checks, verify every current-slice contract those
     sections marked as `must preserve`, `Changed (in scope)`, or selected for
     high-risk proof.
   - For UI work, verify states and responsive behavior the plan calls out.
   - For a slice that changes a user-facing artifact or command surface, exercise
     the composed product as its user would: build/open the artifact or run/read
     the command output. Layer-level green tests do not replace this observation.
6. **Implement conservatively**
   - Reuse local helpers, conventions, naming, and architecture.
   - Keep changes close to the planned files and behavior surface.
   - Add comments only when they clarify non-obvious reasoning.
7. **Verify and review**
   - Run the plan's checks plus the repository's relevant lint, type, test, build,
     or manual smoke checks.
   - Preserve every gate's exit status independently. Use separate invocations
     or explicit per-gate variables plus a structured final status line; never
     let a truncating filter carry the gate status.
   - If a gate has never run on this tree or environment, run it on the
     pre-change baseline first so existing debt is not misattributed to the
     slice. The gate still gates; disclosed debt is separate scoped work.
   - Reconcile every named frozen baseline class as verified now, deferred to a
     named later gate, or a manual-only hole with an owner and residual risk.
   - For contract-bearing rules, show a production path that reaches each rule
     and observe it firing; direct unit tests alone do not prove reachability.
   - Pair absence assertions with same-channel positive controls so an empty or
     mis-pathed observation cannot pass. For module-load environment state,
     establish the complete intended state and test hostile inheritance when
     material.
   - For load-bearing invariants on high-risk slices, perform a reversible
     scratch-isolated mutation of the exact protected surface, observe the
     intended proof fail, revert it, and prove no mutation bytes remain. A
     surviving mutation is a proof finding, not permission to change product
     behavior.
   - Run the Post-Implementation Review Gate on the implemented slice's diff
     after verification and before the execution summary or any authorized
     commit.
   - Classify material review findings as `corrected`, `rejected`, `deferred`,
     `blocked`, or `reversed`; verify delegated findings as `Local evidence`
     before relying on them, and do not treat the review itself as a pass.
   - Treat a correction that changes control flow, ordering, lifecycle,
     concurrency, priority, timeout, fallback, or first-winner behavior as a new
     reviewable change. Re-run at least the perspective that found the original
     issue and check the inverse or symmetric failure mode before closure.
   - If the diff creates or edits durable text, inspect durable-artifact
     language hygiene and record the result before the execution summary or any
     authorized commit; classify any material wording finding with the other
     review findings.
   - Review the final diff against the plan's acceptance criteria and non-goals.
   - If intentional edits landed after an empirical run, rerun the affected
     empirical gate on final bytes or record the exact delta and bounded
     behavior-neutrality argument. Static reruns do not extend empirical proof.
   - Report suite status, acceptance-coverage status, unresolved scope, and any
     unverified shared edits as separate facts. Report any skipped check with the
     reason and residual risk.
   - Update an existing intentional `Implementation progress` ledger after the
     item is verified and reviewed. Otherwise put the evidence-backed status,
     residual risk, and next item in the execution summary. Never create or
     mutate a progress artifact solely because execution occurred.
8. **Hand off explicitly selected commits**
   - Leave verified changes in the working tree unless the current user
     explicitly asks for a commit or a bound approved plan item explicitly
     selects that checkpoint.
   - For a selected checkpoint, preserve the verified scope, test/review receipt,
     unrelated-path exclusions, and any proposed message, then use the normal
     commit-execution workflow. Do not stage or commit inside plan execution by
     implication.
   - A failed, blocked, unchanged, unverified, or ambiguous slice is never an
     eligible commit handoff. Push, release, version changes, history rewrites,
     destructive actions, and external side effects remain separately consented.

## User Communication

- Resolve user-facing chat language before progress updates, blocker notices,
  consent questions, execution summaries, or final responses. Use: explicit
  current-user instruction for chat/output language; `VIBE_CHAT_LANGUAGE` when
  the environment is safely readable or the current user explicitly sets it for
  the request, using a natural language name or BCP47 language tag such as
  `Japanese`, `ja`, `en`, or `pt-BR`; the user's active conversational language;
  the last clear user conversational language available in the current workflow
  context; then English. Treat unreadable, empty, or invalid
  `VIBE_CHAT_LANGUAGE` values as unset. Do not infer chat language from a source
  plan, implementation file, filename without a locale marker, command, skill
  invocation, code identifier, or host-wrapper text. Preserve file paths,
  commands, identifiers, evidence labels, plan headings, and quoted source text
  verbatim unless the user asks to translate or rename them.
- Keep progress updates tied to the plan: "I am implementing step 2" or "This
  conflicts with acceptance criterion 3."
- When bound to a plan file, include the path in the initial binding note so the
  user can see which artifact controls the work.
- When bound to an inline plan, name the plan title or goal, such as `inline
  Payment Webhook Plan` or `inline password-reset regression plan`. Do not
  describe the source as the current conversation, current prompt, current
  instruction, or eval workspace in user-facing output.
- When startup consent is missing for a selected history operation, ask for the
  exact operation-specific decision before that operation and explain the data, permission, delegation, external side
  effect, release, or history risk that makes the decision current rather than
  optional cleanup.
- Include the plan's `Proceed condition` in the initial binding note or the
  first blocker notice, even when later local evidence overrides it.
  If the final response is the first durable handoff, or if the run included
  authorized commits, repeat the plan source and `Proceed condition` status
  there too; do not rely on a transient progress note to carry that evidence.
- When a plan artifact contains an `Implementation progress` ledger, include the
  current item status in blocker notices and final summaries. Name whether the
  ledger was updated in the plan artifact; if not, include the evidence-backed
  progress row in the summary so a later session can resume without inferring
  status from chat-only prose.
- When no concrete plan exists, say implementation is blocked and planning is
  the next step. Refer to a specific planning workflow only when it is
  appropriate or already active in the context.
- For non-technical users, describe consequences in workflow terms before naming
  the implementation detail. Keep evidence labels explicit but light, such as
  "根拠: `Plan` ..." or "Evidence: `Plan` ...".
- Do not bury plan deviations in the final summary. Call them out before editing
  with the exact plan item, checks performed, evidence, impact, closest
  plan-preserving alternative, and decision needed.
- When rejecting or correcting a flawed plan step, avoid framing the user or
  local evidence as "violating the plan". Explain which higher-level plan
  contract or verified fact the step would break, whether the correction is
  plan-preserving or plan-changing, and what decision is needed if any.
- When a plan-changing defect stops execution, name the revision target
  explicitly, such as the current requirements spec path, implementation plan
  path, or missing replacement-plan artifact. State that implementation resumes
  only after that artifact or contract is updated and rebound.
- Keep execution summaries durable. Replace prompt-local or harness-local
  phrases such as `this eval`, `as requested`, `above`, `current prompt`, or
  `current conversation`, `current instruction`, and `this eval workspace` with
  the concrete plan title, file path, provided fixture workspace, workspace
  access state, or explicit user instruction they refer to.
- In the final response, include the bound plan source, implemented slice,
  verification performed, Post-Implementation Review Gate execution mode and
  material finding dispositions, the durable-artifact language hygiene result
  when applicable, applicable progress-ledger update status, plan deviations or
  blockers, and any remaining planned steps. For committed checkpoints, show the
  verification that cleared each checkpoint before the commit.

## Quality Checklist

Before finalizing:

- The implementation plan was explicitly identified.
- Any referenced local plan file was read before using a summary.
- The plan's `Proceed condition`, when present, was quoted or paraphrased before
  editing or in the first blocker notice.
- An intentional `Implementation progress` ledger, when present, was read and
  verified before use. Its absence did not cause execution to create one.
- The current slice stayed inside the plan or the user approved an
  evidence-backed deviation after the Plan Deviation Gate was satisfied.
- No planned step was skipped, reordered, narrowed, or replaced for perceived
  redundancy without passing the Plan Deviation Gate first.
- Any internally inconsistent or known-defective plan step passed the Plan
  Validity Gate before implementation continued; plan-preserving corrections
  were evidenced and plan-changing corrections stopped for artifact revision
  before implementation resumed.
- Any implementation-time workaround or status-quo preservation that appeared
  material to the current slice passed the Plan Validity Gate; the run did not
  finish by encoding the workaround only because the plan scoped the underlying
  behavior out.
- Plan-changing defects returned to the owning requirements or planning
  artifact before affected code changed; execution did not proceed through
  one-off patches against stale plan text.
- Runtime defects in existing behavior the bound plan does not own stopped the
  affected slice as blocked and were reported as existing-feature repair work,
  rather than being patched, worked around, or debugged open-endedly inside
  execution.
- Every approved deviation identified the exact affected plan item, verification
  performed, evidence labels and sources, impact, closest plan-preserving
  alternative, and user decision.
- Every implementation-affecting or decision-affecting claim came from `Plan`,
  `Local evidence`, `Primary source`, or scoped `Accepted risk`, and user-facing
  decisions used those labels even when no code was edited.
- Planned inspection blockers stopped before code or test templates for the
  affected slice.
- False or infeasible plan items were challenged with evidence and alternatives.
- Tests or proof checks matched the plan's acceptance criteria.
- Each acceptance metric used as a completion gate was shown to distinguish the
  current or known-bad baseline from the required after state.
- The Post-Implementation Review Gate ran after implementation and verification,
  before the execution summary or any authorized commit; the review mode,
  degradation reason when applicable, perspectives, material findings, and
  dispositions were recorded, and delegated output was treated as `Unproven`
  until coordinator-verified as `Local evidence`.
- Corrections to control flow, ordering, lifecycle, concurrency, priority,
  timeout, fallback, or first-winner behavior were treated as new reviewable
  changes and checked for inverse or symmetric regressions before closure.
- When the diff created or edited durable text, the review handoff included the
  durable-artifact language hygiene item, the coordinator recorded its result,
  and any material wording finding was classified before the execution summary or
  any authorized commit.
- The final diff was reviewed against plan scope and non-goals.
- Material `Capability dependencies`, when present, were re-checked and their
  fallback or blocker behavior was honored.
- Consent-bound plan items were extracted during plan binding, and unresolved
  exact authorization for history operations and other consent-bound actions
  was handled by Startup Consent Preflight before the affected slice.
- Commit selection came only from an explicit current request or an explicitly
  selected bound checkpoint; invocation and natural slice boundaries were not
  treated as history authority.
- Any selected checkpoint was handed to the commit-execution workflow only after
  verification, review, finding disposition, and safe file-set identification.
- Proposed commit messages were not wrapped in Markdown fences, and execution
  summaries did not rely on prompt-local or harness-local references.
- User-facing progress updates, blocker notices, consent questions, execution
  summaries, and final responses used the resolved chat language instead of the
  source plan language, while preserving technical tokens verbatim.
- Final checkpoint summaries preserved the bound plan source, `Proceed
  condition` status, per-checkpoint verification result, commit action, and any
  skipped or failing verification status.
- An existing intentional progress ledger was updated without changing contract
  sections, or the execution summary carried the status because no durable ledger
  was applicable.
