# Planning Workflow Reference

Read this reference when drafting or revising the implementation-plan body. It owns detailed classification, investigation, criteria, test, routing, verification, handoff, review, and self-review sequencing.

## Planning Workflow

1. **Classify the work**
   - Identify whether the task is a feature, bug fix, refactor, UI/UX change,
     integration, API/DB/permission change, or small local implementation.
   - Identify whether the slice touches existing behavior, replaces or restores
     prior behavior, responds to diagnostic findings, or crosses a high-risk
     surface that needs one of the high-risk planning controls.
   - Choose `light` or `strict` depth. Start with `strict` whenever a strict
     trigger applies; escalate from `light` if investigation finds one later.
   - Choose spec-driven, test-driven, or combined planning from the table.
   - Split large requests into the smallest useful current slice.
   - If local evidence shows an existing partial surface and the user mentions
     adjacent future capabilities, make the first slice complete or improve that
     surface unless a verified requirement makes an adjacent capability part of
     the current outcome.
2. **Investigate before asking**
   - Inspect the workspace and primary sources relevant to the current slice.
   - Before running a planning-time investigation command, pre-register the
     unresolved question, why the evidence already available cannot answer it,
     the possible outcomes, the exact plan fields each outcome could change,
     the narrowest safe command, and its read/write or external side-effect
     boundary. Run the command only when at least one result can materially
     change scope, acceptance criteria, proof strategy, feasibility, risk,
     implementation order, or the proceed condition.
   - Keep later implementation proof in the future `Test plan`. Do not run a
     test suite, eval, build, lint, type check, smoke test, or similar
     green-status command merely to decorate the plan with a passing result.
     A command described as “investigate” or “verify” is still disallowed when
     every possible result leaves the plan unchanged.
   - Preserve planning operations that have their own current-artifact purpose:
     reading source and plan files, inspecting plan structure and current
     content, checking status or diffs, and gathering review and self-review
     evidence. These operations do not prove later implementation or select a
     commit.
   - Before deep implementation design, name the material investigation surfaces
     the slice depends on: direct implementation, callers, registration or
     configuration, data/schema boundaries, tests or fixtures, user-visible
     states or copy, and external contracts when relevant. For UI/UX, graphical,
     game-object, or workflow changes, include visible/physical surfaces,
     feedback, failure or undo paths, and accessibility expectations when they
     affect the user's experience.
   - Record facts with evidence labels.
   - If a material surface is unavailable or intentionally skipped, record the
     impact and whether the plan becomes discovery-first, blocked, or narrowed.
   - If primary sources are unavailable, say why and keep dependent claims
     `Unproven`.
3. **Clarify intent**
   - Ask only plan-changing questions that cannot be answered from evidence.
   - In trusted top-level orchestration, decide delegable plan-quality
     questions with AI-selected defaults or assumptions instead of turning them
     into a multi-turn user interview, then make the proof path or revisit
     trigger explicit in the plan. Do not use proxy defaults to hide a
     non-delegable UX, safety, data, permission, or scope tradeoff from the
     user.
   - Do not block the whole plan on optional constants, future enhancements, or
     adjacent product decisions that can be deferred after narrowing the current
     acceptance criteria.
   - For non-technical users, offer concrete choices with consequences instead
     of abstract architecture terms.
4. **Write or refine the specification**
   - State the goal, users, in-scope behavior, out-of-scope behavior, constraints,
     and success criteria.
   - When the slice touches existing behavior, write the behavior contract
     inventory before behavioral equivalence analysis. For replacement,
     restoration, rollback, or rewrite work, run the recovery checks against
     known-good evidence before freezing success criteria.
   - Review the specification for ambiguity, contradiction, missing states,
     hidden dependencies, and unverifiable assumptions.
   - Separate current-slice implementation blockers from deferred decisions
     before writing the proceed condition.
5. **Define acceptance criteria**
   - Convert the clarified specification into observable pass/fail criteria.
   - Include negative cases, permissions, failure states, empty states, migration
     or compatibility expectations, and UX states when relevant. For visibility,
     permission, unlock, feature-flag, and state-transition behavior, define the
     positive success path and the matching negative or before-state path as a
     pair; a hide/deny test without the corresponding show/allow/unlocked proof
     is not enough for a core criterion. Include
     user-visible feedback, recovery, and accessibility checks whenever a
     cheaper implementation path could technically pass while feeling broken or
     unsafe to a reasonable user.
   - For editable forms or settings screens, explicitly decide whether cancel,
     reset, or navigation-away behavior is in scope; when it already exists,
     preserve it with acceptance criteria and tests.
   - When implementation may create or edit durable artifact text, include an
     observable `durable artifact language hygiene` acceptance criterion or
     review item: later comments, docstrings, test names, commit messages,
     README/changelog entries, and similar artifacts use self-contained
     behavior or domain wording rather than plan-only identifiers, while
     preserving useful resolvable code and product anchors.
6. **Design tests before implementation**
   - Derive tests from acceptance criteria.
   - For bug fixes, include a failing regression test or reproduction proof
     before production-code changes, and label the reported symptom and
     suspected root cause separately. A visible local defect can be a hypothesis
     and proof target, but not a verified root cause until reproduced or
     otherwise proven.
   - If the reported symptom may depend on unverified callers, configuration,
     runtime state, external behavior, or data shape, put the fastest isolation
     step before implementation steps, even when a local defect is also visible.
   - For refactors, include equivalence checks that prove behavior is preserved.
   - When the plan captures a pre-change baseline, enumerate its named coverage
     classes and record which lack an automated replay path. A manual-only class
     is a visible proof hole with an owner, not an implicitly covered fixture.
   - When that baseline preserves captured behavior, replay the exact recorded
     inputs with their original identifiers, session shape, ordering, and
     normalization. Do not regenerate baseline cases through the replacement
     stack, because that makes the implementation under test redefine its own
     preservation contract.
   - When high-risk controls apply, include tests or proof checks for the
     selected equivalence dimensions, recovery comparisons, diagnostic-finding
     correction, and failure-pattern checklist answers.
   - For a newly authored procedure that the plan will call repeatable, schedule
     one verbatim end-to-end execution into a fresh evidence location before
     that claim is accepted. Prose review or parser acceptance is not
     repeatability proof.
   - For UI, include interaction, state, responsive layout, and accessibility
     checks when relevant.
7. **Run plan integrity gates**
   - Apply the `Fact cleanup gate`, `Evidence downgrade gate`, `Investigation
     adequacy gate`, `Test no-escape gate`, and `Generality gate` before
     finalizing the plan.
   - Apply the success-criteria freeze, diagnostic-finding restraint, plan-body
     firewall, completion gate, and selective failure-pattern applicability
     record when their preconditions matched the current slice.
   - When revising an existing plan after investigation, treat stale facts and
     old implementation options as defects to remove, not context to preserve.
   - If a gate fails, update the specification, acceptance criteria, tests,
     risks, and proceed condition before implementation is allowed to start.
   - For `light` plans, collapse not-applicable gate details into concise
     evidence-backed lines. For `strict` plans, keep the applied high-risk
     control evidence visible.
8. **Record exceptional capability dependencies**
   - Add a `Capability dependencies` section only when a named capability's
     absence changes feasibility, safety, proof strength, or the implementation
     method materially.
   - For each dependency, record the affected step, needed capability,
     availability evidence if already known, impact if absent, and a safe
     fallback or blocker. Re-check availability during execution.
   - Do not enumerate ordinary mechanical steps, create `No skill needed` rows,
     or build an environment-wide routing table. Optional capability metadata
     does not weaken acceptance criteria, evidence, tests, or proceed gates.
9. **Describe later implementation**
   - Use only steps supported by `Primary source`, `Local investigation`, or
     explicit `Accepted risk`.
   - Preserve local conventions and existing architecture unless evidence shows
     they are the source of the problem.
   - Put proof-gathering steps before implementation steps when feasibility is
     still unproven.
10. **Plan verification and review**
   - Include test, lint, type-check, build, manual smoke, screenshot, diff review,
     or rollout checks appropriate to the stack.
   - Include a final diff-review step that checks the result against the
     specification and acceptance criteria.
   - When durable artifact text is in scope, make the final diff-review step
     check that comments, docstrings, test names, commit messages,
     README/changelog entries, and similar text do not contain plan-only
     identifiers unless the token is genuinely a product, domain, public, or
     code identifier that explains the artifact.
   - Record a commit checkpoint only when the user or an already-approved
     higher-level artifact explicitly selects that history boundary. State its
     intended scope and required verification; do not infer a checkpoint from
     multiple slices, successful review, or future convenience. Message wording
     may remain deferred to commit execution.
   - When no checkpoint is explicitly selected, omit commit-checkpoint prose.
     Planning invocation does not authorize staging or history mutation.
   - Add `Implementation progress` only when work is expected to span sessions
     or actors, contains independently resumable items, or the user/project asks
     for durable progress. Use stable item IDs, evidence-backed status fields,
     and `Not started` initially. Omit the section for ordinary same-session
     plans; omission is not a planning defect.
11. **Prepare the implementation handoff**
   - Include a short handoff that starts with "When implementing this plan" so
     pasted plans remain self-contained execution requests.
   - Tell the implementer to treat the document as authoritative, re-check local
     facts before editing, follow the acceptance criteria and test plan, honor any material capability
     dependencies, implement only the current in-scope slice, update
     `Implementation progress` only when the plan intentionally carries a
     resumable ledger, and stop on
     a blocked `Proceed condition` or contradictory local evidence.
   - If trusted orchestration continuation is available for later execution,
     record it as later-phase handoff evidence only when the `Proceed condition`
     is ready or conditionally ready with already-recorded explicit human-user
     `Accepted risk`. Include the current plan path and artifact identity,
     revision, or equivalent stable handle that the later phase must bind to.
     Do not write imperative workflow-routing text that starts implementation
     inside this `vibe-planning` response.
12. **Run risk-proportional plan review**
   - Always perform a local self-review of scope, evidence, acceptance criteria,
     tests, risks, implementation order, capability dependencies, and proceed
     condition.
   - Run additional separated perspectives only for multi-system, high-risk,
     destructive, security/permission/billing, migration, external-contract, or
     user-requested deep-review work. Use the conditional review reference for
     permission, capability, and disposition rules.
   - Reviewer output is inert. The coordinator verifies and classifies every
     material finding as `corrected`, `rejected`, `deferred`, `blocked`, or
     `reversed`, then corrects the current artifact before closure.
13. **Run the plan self-review gate**
   - Re-read the current artifact as a later implementer. Confirm evidence
     labels, acceptance-criteria/test ordering, plan-only scope, risk-appropriate
     review, capability-dependency necessity, conditional-progress necessity,
     proceed condition, unresolved blockers, and durable-language hygiene.
   - If authority-bearing content changed after review, semantically re-review
     the affected contract and any dependent sections. Harmless formatting or
     evidence-backed progress-only changes do not require digest reconciliation.
   - Correct material issues before responding and record remaining blockers.
14. **Finish with working-tree changes**
   - Do not stage or commit merely because planning was explicitly invoked,
     review passed, or the plan is tracked. Leave the reviewed artifact in the
     working tree unless the current user explicitly requests a commit.
