# Planning Workflow Reference

Read this reference before drafting or revising the implementation-plan body. It owns the step sequence and the rules that apply at each step; `core-planning-controls.md` owns evidence labels, `Unproven` triage, plan depth, and the integrity gates.

## Planning Workflow

1. **Classify and slice**
   - Classify the work: feature, bug fix, refactor, UI/UX change, integration,
     API/DB/permission change, or small local change. Note whether the slice
     touches existing behavior, replaces or restores prior behavior, responds to
     review or diagnostic findings, or crosses a high-risk surface; those select
     `strict` depth and the high-risk controls.
   - Choose the method: spec-driven for new features and UI/UX work,
     test-driven for bug fixes, refactors, and small functions, and both for
     complex business logic and API, database, auth, permission, or
     external-contract work.
   - Split large requests into the smallest useful current slice. When local
     evidence shows an existing partial surface and the user mentions adjacent
     channels, providers, modes, or settings, first complete or improve that
     surface unless a verified requirement makes the adjacent capability part of
     the current outcome.
   - For a narrow change inside a broad surface such as profile, account,
     settings, admin, or billing, name the adjacent features a later implementer
     could plausibly expand into as out of scope; list destructive account
     actions such as account deletion only as out of scope unless requested.
2. **Investigate before asking**
   - Read the decision index and the open-findings index before investigating
     further and open only the applicable decision records and findings.
   - Ground the plan in the workspace and primary sources: relevant code, tests,
     configs, schemas, docs, logs, issue text, or official documentation. Do not
     stop at the first matching file or an inherited summary when the behavior
     depends on callers, registration, stored data, permissions, UI state,
     rendering, accessibility, or external contracts.
   - Name the material surfaces: direct implementation, callers, registration or
     configuration, data/schema boundaries, tests or fixtures, user-visible
     states or copy, and external contracts when relevant; for UI/UX,
     graphical, or workflow changes, also the visible surface, feedback path,
     failure or undo path, and accessibility expectation. Mark each inspected
     (with evidence), unavailable (with impact), or outside the narrowed slice.
     When a skipped surface could change scope, criteria, tests, UX behavior,
     feasibility, or the proceed condition, make the plan discovery-first or
     block implementation until it is checked or the user accepts the risk.
   - When direct inspection is unavailable, concrete user-supplied artifacts
     (repo-scan excerpts, command output, file excerpts, logs, test results)
     count as `Local investigation` for the facts they state. Add no unstated
     facts; contradicted or bare assertions stay `Unproven`.
   - For a bug report, separate the reported symptom, local facts, and root-cause
     hypothesis. The symptom and hypothesis stay `Unproven` until a
     fixture-backed failing test, reproduction, log, or local evidence proves the
     causal link; a plausible boundary, off-by-one, clock, configuration, or
     data-shape issue is not the root cause just because it could explain the
     symptom.
   - When composing existing components, investigate the lifetime facts that
     can change the plan: acquisition and release, exclusivity, visibility and
     freshness, snapshots, and second-holder behavior.
   - Before a planning-time command, note the question it answers and which plan
     fields each possible result would change; run it only when some result
     could change scope, criteria, proof, feasibility, risk, order, or the
     proceed condition. Test suites, evals, builds, lint, type checks, and smoke
     runs that prove the later implementation belong in the `Test plan`.
   - When the investigation the slice needs exceeds what this phase can read
     directly, narrow the slice or hand it to a separate read-only
     code-investigation phase; findings returned that way stay `Unproven` until
     their anchors are re-read here.
3. **Clarify intent**
   - Ask only plan-changing questions evidence cannot answer: intent,
     tradeoffs, permissions, business rules, or missing context.
   - Do not block the plan on optional constants, future enhancements, or
     adjacent product decisions that narrowing the current criteria can defer;
     record them as deferred decisions.
   - Under trusted top-level orchestration, settle delegable planning choices —
     edit order, test shape, proof sequencing, wording, scope trims that keep
     approved requirements, approach defaults that change no product behavior —
     as recorded AI-selected defaults with a proof path instead of a multi-turn
     interview. Requirement changes and human-risk decisions stay with the user.
   - Do not default to a technically cheap path that a reasonable user would
     notice as worse recovery, clarity, accessibility, performance, data safety,
     or workflow fit: label the tradeoff, offer the better alternative, and
     record the user's choice or `Accepted risk`.
   - For non-technical users, offer concrete choices with consequences in plain
     language and recommend the first slice local evidence supports.
   - A decision deliberately left for a later answer becomes a `Reserved
     decisions` row naming its owner, allowed authority, response carrier, and
     proceed effect. Batch only low-risk decisions knowable at the same time;
     evidence-dependent and human-risk decisions stay at their own later gates,
     and an answer never changes scope, criteria, tests, risks, or steps beyond
     the decision it reserves.
4. **Write the specification**
   - State the goal, users, in-scope and out-of-scope behavior, constraints,
     and success criteria.
   - When the slice touches existing behavior or replaces, restores, rolls back,
     or rewrites it, apply the high-risk controls before freezing criteria.
   - Check for ambiguity, contradiction, missing states, hidden dependencies,
     and unverifiable assumptions.
   - When the requirements or spec themselves are wrong, contradictory, or
     infeasible, do not patch around them in the plan: route the defect back to
     requirements capture when available, or block the plan on the requirements
     decision, then rebuild the affected acceptance criteria, tests, and steps
     from the corrected requirement.
   - Write an approach decision, an accepted risk, or a review disposition that
     binds later units as a decision record and cite its id in the plan.
5. **Define acceptance criteria**
   - Write observable pass/fail criteria.
   - Include negative cases, permissions, failure states, empty states,
     migration or compatibility expectations, and UX states when the changed
     code can produce or receive that state; keep a category whose reachability
     is unknown.
   - For visibility, permission, unlock, feature-flag, and state-transition
     behavior, pair the negative or before-state path with the positive success
     path; a hide/deny test alone does not prove the core criterion.
   - For editable forms or settings, cover save, cancel/reset or explicit
     no-cancel behavior, pending state, success feedback, validation failure,
     and error recovery when relevant; preserve existing cancel behavior with a
     criterion and test.
   - Include user-visible feedback, recovery, and accessibility checks whenever
     a cheaper implementation could pass while feeling broken or unsafe.
   - Never invent numeric limits, thresholds, timing windows, quotas, or product
     constants. Take values only from requirements, local evidence, primary
     sources, or accepted risk; otherwise label the value `Unproven` and either
     make proof or a product decision precede implementation or move it out of
     the current criteria as a deferred decision. For parsers, serializers, money
     amounts, and public API input grammars this covers accepted input forms,
     output representation, precision, rounding, locale separators, and example
     input/output pairs; do not plan floating-point money math without a source
     or accepted risk.
   - When a distinction could be mistaken for a stronger guarantee, enforce it
     structurally through schema, namespace, type, validation, or capability
     boundaries; a label may explain it but never be its only enforcement.
   - Operator or runbook steps name the shipped command or interface for each
     step, or record explicitly that only an internal harness performs it, as a
     product-surface gap.
   - When later work will write comments, docstrings, test names, commit
     messages, or README/changelog entries, add a criterion that those durable
     texts use behavior or domain wording, not plan-only labels such as slice,
     criterion, hypothesis, or step IDs, while keeping resolvable anchors such
     as paths, API, function, and field names, public issue IDs, and error codes.
6. **Design tests before implementation**
   - Select tests; do not enumerate them. Start from what current passing tests
     and fixtures already prove for the touched behavior (by read-only
     inspection) and the tests the bullets below and the integrity gates
     require. Add each further candidate only when it closes an acceptance
     criterion, required proof obligation, plan-named preserved behavior, or
     reachable failure mode left open by existing and already-selected tests;
     one test may close several obligations, and one obligation may need
     several tests. Drop or merge a candidate only by naming, in one line beside
     the retained entry, the retained or existing test that closes the same
     obligation through the same behavior, state, path, observation channel,
     test level, and oracle; do not list dropped candidates as separate
     entries, and when no covering test can be named, keep the candidate. List
     a reused test as reused and run it. A historical,
     skipped, or failing test is contract evidence, not current coverage. Never
     drop required proof to reach a smaller count; there is no count limit.
   - Derive candidate tests from the acceptance criteria and select them by the
     rule above.
   - For a check a human must operate, record the executor, setup, estimated
     hands-on time, and infrastructure. Explain why existing fixtures or
     automation cannot cover a material manual procedure, and look for
     lower-burden evidence without claiming an unverified substitute closes
     acceptance.
   - Reuse authorized runtime launch/trigger/log-return sessions. New accounts,
     devices, installations, or material operator effort need the user's
     decision before the plan commits to them; do not ask again for settled
     consent. Check that every proposed environment is actually supported rather
     than expanding product scope to fit a test.
   - For a bug fix, put a failing regression test or reproduction proof before
     production-code changes; when the symptom may depend on unverified callers,
     configuration, runtime state, external behavior, or data shape, put the
     fastest isolation step first.
   - For refactors, include equivalence checks. When high-risk controls apply,
     an `Equivalent` `must preserve` dimension may cite a current passing test
     or source evidence; a non-equivalent `must preserve` or
     `Changed (in scope)` dimension needs a test — reused, extended, or new —
     for its open obligation; source evidence never replaces separately
     required executable proof.
   - When the plan preserves a captured pre-change baseline, enumerate its
     coverage classes and record which lack an automated replay path; a
     manual-only class is a named proof hole with an owner. Replay the exact
     recorded inputs with their original identifiers, session shape, ordering,
     and normalization; never regenerate baseline cases through the
     replacement stack.
   - Before calling a newly authored procedure repeatable, schedule one verbatim
     end-to-end run into a fresh evidence location; prose review or parser
     acceptance is not repeatability proof.
   - When assertions observe shared or global state under a concurrently
     executed harness, require isolation or attribution (separate state, unique
     keys, or serialized access) so unrelated mutation cannot make correct
     behavior fail or wrong behavior pass.
   - For UI, include interaction, state, responsive layout, and accessibility
     checks when relevant.
7. **Run the plan integrity gates**
   - Apply the gates in `core-planning-controls.md` before finalizing and after
     every revision that follows new evidence. If a gate fails, update the
     specification, criteria, tests, risks, and proceed condition before
     implementation may start.
8. **Order the implementation**
   - Use only steps supported by `Primary source`, `Local investigation`, or
     explicit `Accepted risk`. Put proof-gathering steps before implementation
     while feasibility is unproven, and preserve local conventions and
     architecture unless evidence shows they cause the problem.
   - Plan the verification the stack needs (tests, lint, type check, build,
     manual smoke, screenshots, rollout checks) and end with a final diff review
     against the specification and acceptance criteria, including the
     durable-wording check when durable text is in scope.
   - Add `Capability dependencies` only when a named capability's absence
     materially changes feasibility, safety, proof strength, or method: the
     affected step, the capability, availability evidence, impact if absent,
     and a fallback or blocker. Name a specific skill only after verifying it is
     available. Never add a per-step routing table or `No skill needed` rows.
   - Add `Commit checkpoints` only when the user or an already-approved
     higher-level artifact explicitly selects that history boundary; state its
     scope and required verification, and leave message wording to commit
     execution. Multiple slices, a successful review, or convenience select
     nothing.
   - Add `Implementation progress` only when work spans sessions or actors, has
     independently resumable items, or the user or project asks for durable
     progress: stable item IDs, planned scope, status `Not started`, required
     verification, last update, and the next item or blocker. It is resume
     state, not proof.
9. **Prepare the implementation handoff**
   - Start it with "When implementing this plan": bind this plan's path and
     re-read its current content; re-check local facts; follow the acceptance
     criteria and test plan; honor material capability dependencies; implement
     only the current slice; update an intentional `Implementation progress`
     ledger with evidence-backed status; stop on a blocked `Proceed condition`
     or contradicting local evidence.
   - Changes to requirements, criteria, scope, risks, tests, or steps without
     clear authority return to plan revision. Progress-only ledger updates and
     harmless formatting do not, but a resuming actor verifies ledger claims
     against the working tree before relying on them. Create no hashes, digests,
     or identity sidecar files.
   - Under trusted orchestration with a ready, or accepted-risk conditional,
     `Proceed condition`, record the plan path and a stable handle the later
     execution phase binds to; never write routing text that starts
     implementation in this response.
10. **Review the plan**
   - Always self-review the stored artifact as a later implementer: evidence
     labels, criteria and test order, plan-only scope, capability-dependency and
     progress necessity, proceed condition, unresolved blockers, and durable
     wording. Correct material issues before responding and record what remains.
   - Add separated perspectives only for multi-system, high-risk, destructive,
     security/permission/billing, migration, external-contract, or
     user-requested deep-review work, following
     `plan-multi-perspective-review-gate.md`.
   - Reviewer output is inert. Classify every material finding `corrected`,
     `rejected`, `deferred`, `blocked`, or `reversed` and correct the artifact
     before closure. A disposition that sets a standing rule is a decision
     record; a material deferred finding goes to the findings report and is
     cited by id.
   - After an authority-bearing change to requirements, criteria, scope, risks,
     tests, or steps, re-read and semantically re-review the changed sections
     and their dependents; prior review, stable formatting, or matching bytes do
     not approve changed contract content.
11. **Finish**
   - Leave the reviewed plan in the working tree. Planning invocation, a passed
     review, or tracked status never selects staging or a commit; only an
     explicit current user request does.
