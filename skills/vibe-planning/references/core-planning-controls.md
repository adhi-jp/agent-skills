# Core Planning Controls Reference

Read this reference before finalizing any implementation plan or plan revision. It owns detailed plan-only rules, high-risk controls, plan depth, evidence labels, integrity gates, and method selection.

## Core Rules

- This skill is for implementation-plan creation or revision only. Stop after
  the plan artifact and concise summary. Implementation requires a separate
  execution request outside `vibe-planning`. In a trusted orchestration, that
  separate request may be a recordable later coordinator/host phase invocation
  after this skill stops, including within the same outer user turn when the
  current instruction already requested implementation; it is never
  implementation inside the current `vibe-planning` response. Do not convert
  this response stop into a categorical requirement for another user prompt.
- Do not provide patches, edit non-plan files, or claim that code, tests,
  non-plan docs, evals, configs, changelogs, or other implementation work is
  complete. The only commit this phase may make is the reviewed tracked
  planning-artifact checkpoint described by the owning skill. Non-mutating
  investigation is allowed when it grounds the plan.
- Plan-readiness language is later-execution handoff, not current-turn
  authorization. `Implementation plan`, `Commit checkpoints`, `Implementation
  handoff`, `Current slice`, `Proceed condition`, `implementation-ready`, or a
  completed planning phase may indicate that a separate execution request can
  begin; they must not trigger implementation while this skill is active.
- Trusted orchestration continuation after planning is allowed only as a later
  phase when the plan artifact has completed multi-perspective review or
  recorded fallback, completed self-review, and has a ready `Proceed condition`
  or a conditional `Proceed condition` tied to already-recorded explicit
  human-user `Accepted risk`. Blocked, discovery-first, destructive-risk-blocked,
  or current-slice-blocker plans must stop orchestration continuation rather than
  route to execution. Orchestration cannot accept destructive, credential,
  auth/session, permission, billing, security, irreversible, data-migration, or
  other human-risk decisions on the user's behalf unless explicit human-user
  acceptance is already recorded and tied to the current plan.
- During trusted top-level orchestration, do not stop on a sequence of
  delegable planning-quality questions when local evidence, the approved spec,
  existing project conventions, or bounded review perspectives can support a
  safe default. Delegable planning choices include low-risk edit ordering,
  test-shape selection, proof sequencing, wording, scope trimming that preserves
  approved requirements, and implementation-approach defaults that do not change
  product behavior or non-delegable risk. Record them as AI-selected planning
  defaults, assumptions, or `Unproven` items with proof paths, not as explicit
  human-user decisions or accepted risk.
- Trusted orchestration proxy decisions do not authorize requirement changes,
  blocked proceed conditions, destructive or irreversible operations, external
  side effects, credentials, auth/session, permission, billing, security,
  data-migration, legal/compliance, paid or production actions, release work, or
  history mutation. Ask the smallest human-user question or return to the owning
  requirements artifact when those decisions are unresolved.
- `VIBE_SUBAGENTS` controls only plan-review subagent permission. It is not
  phase-continuation authority and must not be used to approve requirements
  handoff, execution handoff, implementation, staging, commits, or release work.
- Ground the plan in primary sources or actual investigation before asking the
  user to decide. Read relevant local code, tests, configs, schemas, docs, logs,
  issue text, or official documentation first. Do not treat the cheapest
  plausible path, first matching file, or inherited summary as enough when the
  slice's behavior depends on adjacent surfaces such as callers, registration,
  stored data, permissions, UI state, layout, rendering, accessibility, or
  external contracts.
- A planning investigation command needs a decision-bearing question and a
  pre-registered result-to-plan mapping. Record why existing evidence is
  insufficient, possible outcomes, affected plan fields, the narrowest safe
  command, and side-effect boundaries. Commands that exist only to obtain a
  passing implementation-style status are not planning evidence; put them in
  the future `Test plan`.
- When implementation changes only an assertion or oracle while product
  behavior is already correct, the test no-escape gate requires a safe,
  reversible perturbation of the exact asserted surface and an observed failure
  before the final real check. If the exact new assertion cannot be observed
  failing, keep proof `Unproven` rather than substituting prose review.
- Use official docs, upstream source, vendor documentation, standards, or
  user-provided source material for claims about external systems. Use local
  reproduction or direct repository inspection for claims about the current
  workspace.
- When direct repository inspection is unavailable, concrete user-provided local
  artifacts such as repo-scan excerpts, command output, file excerpts, logs, or
  test results can count as `Local investigation` for the stated facts. Preserve
  the supplied source, do not add unstated facts, and downgrade contradicted or
  bare asserted facts to `Unproven`.
- Do not present memory, inference, forum summaries, or unchecked assumptions as
  fact. Mark them as `Unproven`.
- Do not accept user claims blindly. If a claim is false, stale, unsupported, or
  infeasible, state the evidence and propose the closest viable alternative.
- Do not invent unavailable skills or assume a fixed companion skill set. A plan
  may name a specific skill only after its availability was verified from the
  current environment, user-provided material, project instructions, or local
  metadata.
- Plan-only identifiers are planning state, not durable artifact wording. When a
  slice may create or edit source comments, docstrings, test names, commit
  messages, changelog or README entries, or other durable implementation text,
  require those later artifacts to describe the concrete behavior, domain
  concept, invariant, or user-visible contract instead of copying bare slice,
  acceptance-criteria, requirement, question, hypothesis, step, or phase labels.
  Preserve useful resolvable anchors such as paths, commands, API names,
  product or domain terms, function and field names, public issue IDs, stable
  error codes, and code identifiers when they explain behavior or trace to a
  durable source.
- For plans with multiple implementation items, slices, or eligible commit
  checkpoints, include an `Implementation progress` section that later execution
  can update in place. The section starts every item as `Not started` and gives
  stable item IDs, the planned scope, required proof or review, commit
  expectation when applicable, and a field for the latest evidence-backed
  status. This is a resume ledger for later agents, not current-turn
  implementation authorization or a planning-time completion claim.
- Treat concrete examples, fixtures, project memories, and history-derived
  failure cases as evidence or pressure tests, not skill boundaries. Before an
  example changes scope, acceptance criteria, tests, or implementation order,
  map it to a broader planning dimension it represents, such as external
  contracts, data shape, lifecycle state, destructive risk, local evidence
  grounding, optional tool usage, or user-experience expectation. Name
  dimensions that shape the generated plan.
- Respect the user's requested outcome as far as reality allows. When a request
  cannot be implemented literally, preserve the intent and adjust the mechanism.
- When the user asks for broad UX improvements, make the first slice complete
  or improve an existing verified surface before adding adjacent unverified
  channels, providers, modes, or settings. Include the user's path through the
  changed behavior, state transitions, failure recovery, and accessibility or
  feedback expectations when they are material to the slice; do not choose a
  technically cheap approach that leaves a worse user experience unless the
  plan labels the tradeoff, offers the better alternative, and records user
  preference or accepted risk.
- Ask questions only for intent, tradeoffs, permissions, business rules, or
  missing context that investigation cannot determine. In trusted orchestration,
  use AI-selected planning defaults for delegable choices before asking the
  user, and reserve questions for non-delegable risk, requirement changes, or
  blocked proceed conditions.
- For non-technical users, explain choices in plain language and translate
  technical consequences into product or workflow impact. Do not make the
  low-effort engineering choice the default when a reasonable user would notice
  poorer recovery, clarity, accessibility, performance, data safety, or workflow
  fit; surface the tradeoff as a decision or accepted risk.
- For non-technical "what should we build first" requests, recommend the first
  slice supported by local evidence. Ask only for product wording, business
  rules, or tradeoffs that local investigation cannot settle.
- Define acceptance criteria and tests before implementation steps. For visibility, permission, unlock, feature-flag, and state-transition gates, pair the negative/before proof with the positive/after proof in the current-slice criteria and test plan; do not let hardening or denial tests stand in for the core user success path.
- For absence assertions over a captured channel, add a positive control in the
  same channel that proves capture was live and correctly pathed; explicitly
  assert forbidden fields rather than treating unasserted omission as proof.
- When a distinction could be mistaken for a stronger product guarantee,
  enforce it structurally through schema, namespace, type, validation, or
  capability boundaries. A label may explain the boundary but must not be its
  only enforcement.
- Do not invent numeric limits, thresholds, timing windows, quotas, or product
  constants. Use values only when they come from user requirements, local
  evidence, primary sources, or accepted risk; otherwise label the value
  `Unproven` and make proof or a product decision precede implementation.
- For parser, serializer, money/amount normalization, and public API
  input-grammar plans, treat accepted input forms, output representation,
  precision, rounding, locale separators, and example input/output pairs as
  contract facts. If they are not supplied by user requirements, local evidence,
  primary sources, or accepted risk, label them `Unproven`; do not promote
  invented sample pairs into acceptance criteria or tests. Use placeholder or
  deferred examples only when visibly labeled, and make grammar or
  representation proof or a product decision precede implementation.
- For money or amount parsing, address exact-decimal handling before
  implementation and do not plan IEEE-754 floating-point math unless a primary
  source or accepted risk explicitly permits it.
- For editable UI plans, include observable state transitions in the acceptance
  criteria and tests: save, cancel/reset or explicit no-cancel behavior, pending
  state, success feedback, validation failure, and error recovery when relevant.
- For narrow changes inside profile, account, settings, admin, billing, or other
  broad surfaces, explicitly name adjacent features that are not in the current
  slice when a later implementer could plausibly expand into them. Include
  destructive or high-risk adjacent account actions, such as account deletion,
  only as out of scope unless the user asked for them.
- If implementation proceeds with an `Unproven` assumption, require explicit
  user risk acceptance and keep the item labeled as `Accepted risk`; never
  convert it into verified fact.
- Treat plan updates as replacement work, not additive history. When
  investigation verifies, refutes, or replaces a hypothesis, remove stale
  `Unproven` entries, old API names, and superseded implementation proposals
  instead of leaving them as plan noise.
- When revising a plan reveals that the requirements or spec themselves are
  wrong, contradictory, or infeasible, do not paper over the defect with a
  local plan workaround. Route the requirements defect back to a
  requirements-spec workflow when one is available, or block the plan on the
  requirements decision, then rebuild the affected acceptance criteria, tests,
  and implementation steps from the corrected requirements. Fix the owning
  artifact rather than patching around a broken contract downstream.
- Do not claim visual quality, performance, packet volume, efficiency,
  responsiveness, usability, or UX improvement as fact unless it was measured,
  reproduced, captured, or supported by a primary source or local evidence.
  Otherwise keep the claim `Unproven` or record explicit `Accepted risk`.
- Do not weaken tests to make a plan implementation-ready. If an important
  contract cannot be verified as planned, make it an implementation-start
  blocker or define an alternative proof path that still proves the contract.
- For bug reports, separate the user-reported symptom, local facts, and
  root-cause hypothesis. The symptom and hypothesis stay `Unproven` until a
  fixture-backed failing test, reproduction, log, or local evidence proves the
  causal link. Do not treat a plausible boundary, off-by-one, clock,
  configuration, or data-shape issue as the root cause only because it could
  explain the symptom.

## High-Risk Planning Controls

Use these controls only when their preconditions match the current slice. They
are safeguards, not a universal checklist for every plan.

Read a bundled reference only when its control applies:

- `references/behavior-contract-inventory.md` - required before behavioral
  equivalence analysis when the slice touches existing behavior.
- `references/behavioral-equivalence-analysis.md` - required for refactors,
  migrations, replacements, internal implementation changes, and explicit
  behavior changes that touch an existing contract.
- `references/change-recovery-checklist.md` - required before planning
  replacement, restoration, rollback, or rewrite work against behavior that
  used to be correct.
- `references/plan-boundary-controls.md` - required before finalizing a plan
  that incorporates review comments, diagnostic findings, audit output,
  analyzer warnings, or late additions after success criteria were written.
- `references/failure-pattern-checklist.md` - required selectively for
  high-risk surfaces such as lifecycle ordering, shared state, persisted config,
  trust boundaries, counters, build or release paths, tool capabilities, and
  multi-phase plan drift.

When the current slice touches existing behavior, build the behavior contract
inventory before equivalence analysis. Separate immediate observable behavior,
internal state transition, and persistent or lifecycle behavior. Label each
entry as `Primary source`, `Local investigation`, or `Unproven`. Refactors,
migrations, and internal implementation changes count as existing-behavior work
even when the user expects behavior to stay the same. Omit the inventory only
with an evidence-backed not-applicable rationale.

For replacement, restoration, rollback, or rewrite plans, find and inspect
known-good evidence before planning the change. Use git history, release tags,
historical tests, checked-in fixtures, specs, runbooks, or user-provided source
material. If the known-good contract cannot be proven, reframe the slice as
discovery or net-new behavior design and keep implementation blocked.

For plans driven by review comments, audit output, analyzer warnings, or other
diagnostic findings, freeze current-slice success criteria once written. Later
additions belong in the current success criteria only when they cite a user
requirement, newly verified evidence, or a `must preserve` equivalence dimension
that is non-equivalent. Otherwise defer the addition. Apply the plan-body
firewall so diagnostic findings produce the smallest corrective slice instead
of adjacent hardening, new modes, new detectors, or extra policy surfaces.

For high-risk surfaces, apply only the matching failure-pattern checklist
sections and record why adjacent near-miss sections were not selected. Pasting
the full checklist into every plan is a planning failure; missing an applicable
section is also a failure. Fold selected answers into facts, blockers,
acceptance criteria, or tests before locking the test plan.

If any current-slice implementation blocker remains `Unproven`, the `Proceed
condition` must block implementation or make the affected step conditional on
explicit `Accepted risk` already recorded in the plan. Risk level does not
override this stop condition. Future or optional decisions that are not needed
for the bounded current slice should be deferred instead of blocking
implementation.

## Plan Depth and Unproven Triage

Before freezing universal bounds or exhaustive claims, require extreme-state
and boundary evidence; otherwise preserve the abstract property and keep the
enumeration `Unproven`. Scale effort from current-slice risk, proof, consent,
and recovery obligations. Repository size or “personal project” signals may
compress rendering but never remove mandatory high-risk controls.

Run a criterion-coherence and mechanism-feasibility pass against requirements,
the target toolchain, earlier/later slice interfaces, and the real actor for
every operation. Contradictory proof requirements, neighboring-layer
vocabulary, unavailable proof routes, impossible operations, or insufficient
earlier interfaces require plan correction, not test-only weakening.

When composing existing components and lifecycle facts can change the plan,
investigate acquisition/release lifetime, exclusivity, visibility/freshness,
snapshots, second-holder behavior, and material user cost. For
property-plus-enumeration decisions, derive membership from named authority or
mark it `Unproven`. Operator instructions must name the shipped interface for
each step or explicitly identify an internal harness and product-surface gap.

Choose plan depth after initial investigation. Escalate when new evidence
reveals a `strict` trigger. Do not choose `light` because it is faster when the
missing investigation could change scope, acceptance criteria, UX behavior,
proof strategy, or the proceed condition.

- `light` plans are for small, localized, low-risk slices after local evidence
  shows the slice has no existing-behavior change, external contract,
  destructive operation, auth/security/billing boundary, data migration,
  diagnostic finding, replacement/restoration/rollback/rewrite, or
  current-slice implementation blocker. `light` reduces rendering only: it still
  needs evidence labels, acceptance criteria before tests, tests before
  implementation, per-step skill routing, multi-perspective review or recorded
  fallback, self-review, and a proceed condition.
- `strict` plans are required when the slice touches existing behavior,
  high-risk planning controls, external contracts, destructive risk,
  diagnostic/review/audit/analyzer findings, recovery or replacement work,
  auth/security/billing boundaries, data migrations, or unresolved
  current-slice implementation blockers. When a `must preserve` equivalence
  dimension becomes non-equivalent, escalate to `strict`.

Compact rendering is allowed only for `light` plans:

- Omit high-risk sections when not applicable and record a short
  evidence-backed not-applicable reason in `Plan integrity gates`.
- Collapse not-applicable gate details into concise lines instead of expanding
  every subfield.
- Group repeated skill-route rows only when the row names every covered step ID
  and all route fields are identical. A grouped row is not a global skill list.
- Keep the `Multi-perspective plan review` and `Plan self-review gate` concise,
  but correct material issues before responding.

Classify every `Unproven` item by `Phase relevance`:

- `current-slice implementation blocker`: the item is needed to define,
  implement, or test the current acceptance criteria, or affects current-slice
  feasibility, behavior, data handling, permissions, security, external
  contracts, or destructive risk. Implementation is blocked unless the user
  explicitly accepts a scoped `Accepted risk`.
- `proof before implementation`: the item should be resolved by a discovery or
  proof step before code changes begin; the plan may be discovery-first, but
  implementation remains blocked until proof completes.
- `deferred decision`: the item is optional, future-phase, avoidable by
  narrowing acceptance criteria, or not needed for the current bounded slice.
  Record it as deferred with impact and revisit trigger; do not block the
  current slice on it.
- `non-implementation follow-up`: the item affects rollout, monitoring,
  product copy, or future hardening but not the current implementation contract.

If the plan is discovery-first, label unknowns cleared by the discovery step as
`proof before implementation`. Use `current-slice implementation blocker` inside
a discovery-first plan only when the item requires a user/product decision or
accepted-risk choice before acceptance criteria can be frozen.

When unknown product constants, numeric limits, or adjacent enhancements are
outside the current slice, do not invent them or block planning on them.
Recommend the evidence-backed bounded slice, remove the unsupported constant
from current acceptance criteria, and record the unknown as a deferred decision.

## Evidence Labels

Use these labels in the plan when a claim affects scope, feasibility, behavior,
tests, or implementation order:

- `Primary source`: official documentation, authoritative specification,
  upstream source, vendor docs, user-provided source material, or a known-good
  historical implementation.
- `Local investigation`: repository inspection, non-mutating command output,
  reproduced behavior, existing tests, configs, schemas, or logs from the
  current workspace.
- `Unproven`: memory, inference, secondhand claims, stale docs, unchecked user
  claims, missing access, or hypotheses.
- `Accepted risk`: an `Unproven` item the user explicitly chose to proceed with
  after the impact was explained.

Every `Unproven` or `Accepted risk` item must include impact, `Phase
relevance`, the fastest proof path, and where it must be revisited.

A value calculated from measured or source-backed inputs is a derivation, not a
measurement. Record it as `Local investigation (derived)` with the formula,
assumptions, and at least one condition that would break the derivation. When a
derived value becomes a public limit, frozen constant, acceptance threshold, or
test invariant, confirm it empirically before implementation or keep it
`Unproven` with proof before implementation. Do not let verified inputs
silently upgrade unchecked arithmetic assumptions.
When an outside draft supplies only a derived result but not a reproducible
formula, record the formula as unavailable instead of reconstructing one from
nearby numbers. Preserve any supplied occupancy or full-fill assumption,
identify a concrete break condition, and require the missing derivation plus
empirical proof before freezing the value.

## Plan Integrity Gates

Run these gates before finalizing any plan and every time a plan is revised
after new evidence appears.

For a first-draft plan with no prior artifact or copied handoff text, record the
relevant gate as not applicable with the reason. Do not run broad discovery only
to prove that no prior plan exists.

1. **Fact cleanup gate**
   - When a hypothesis becomes verified, refuted, or replaced, run full-text
     search over the plan artifact and any copied handoff notes for the old
     `Unproven` wording, old API names, old field names, old commands, and
     superseded implementation proposals.
   - Delete or rewrite stale text. Do not keep old labels or rejected designs as
     historical commentary unless the plan still needs them as an explicit
     rejected alternative.
   - If the plan still contains both the new fact and the old hypothesis, the
     gate fails.
2. **Evidence downgrade gate**
   - Downgrade appearance, rendering quality, performance, packet volume,
     memory use, responsiveness, "feels better", and UX claims to `Unproven`
     unless they are backed by measurement, screenshots, run logs, profiling,
     packet counts, user research, primary-source limits, or direct local
     reproduction.
   - If the user chooses to proceed without measurement, keep the item as
     `Accepted risk` with impact, fastest proof path, and revisit trigger.
   - Do not let optimistic wording such as "should be fine", "small enough", or
     "visually cleaner" appear as verified fact.
3. **Investigation adequacy gate**
   - List the current slice's material surfaces before finalizing scope: direct
     implementation, callers, registration or configuration, data/schema
     boundaries, tests/fixtures, user-visible states or copy, and external
     contracts when relevant. For UI/UX, graphical, game-object, or workflow
     changes, include the visible/physical surface, feedback path, failure or
     undo path, and accessibility expectation when they affect the user's
     experience.
   - Mark each surface as inspected with evidence, not applicable with a reason,
     unavailable with impact, or deferred because it is outside the narrowed
     slice.
   - If a skipped or unavailable surface could change scope, acceptance
     criteria, tests, UX behavior, feasibility, or the proceed condition, keep
     the plan discovery-first or block implementation until the surface is
     checked or the user accepts the scoped risk.
4. **Test no-escape gate**
   - Identify important contracts that the plan depends on, especially API
     fields, serialization, persistence, network behavior, permissions,
     migrations, visual behavior, cross-loader behavior, and external-service
     behavior.
   - If a planned test cannot verify a contract, do not replace it with a weaker
     test that proves only implementation details or serialization shadows. Mark
     implementation start as blocked, or add an alternative proof path that
     still proves the same contract.
   - If the alternative proof path reduces coverage, record the reduced claim as
     `Unproven` or `Accepted risk` and keep implementation blocked unless the
     user explicitly accepts that risk.
   - For each metric used as an acceptance gate, record the known-bad or current
     baseline. The gate must fail, differ, or otherwise expose the defect before
     the planned fix. If the baseline already satisfies the threshold, the
     metric is non-discriminating and cannot gate implementation completion.
   - Ask what wrong implementation would still pass each load-bearing
     assertion. Reject proof based only on an unused observation seam,
     expectations imported from the implementation, best-case input for a
     general claim, final-state traces for forbidden-call claims, or missing
     lifecycle/encoding branches.
   - For load-bearing invariants, plan a reversible performed mutation in a
     scratch copy or equivalent controlled surface. A surviving mutation and an
     assertion that never applied are both proof defects; require observed
     failure plus cleanup before treating the assertion as protective. The
     proof record names the controlled change, the assertion or predicate that
     failed and its observed status or diagnostic, cleanup evidence, and the
     final unmodified check.
5. **Representation coverage gate**
   - When the plan freezes both a public contract and an internal protocol,
     state machine, schema, or result representation, map every required public
     field or outcome across terminal paths or states to the internal carrier
     that can observe and transport it.
   - Split paths when their origin, available evidence, cleanup state,
     precedence, or carrier can differ. Do not use one broad `error`, `fatal`,
     or `failure` row when assertion/script failure, connection failure,
     timeout, cancellation, partial cleanup, or another terminal class can
     observe or transport different values. Group paths only when current
     evidence proves the same observer, carrier, and field availability apply,
     and record that grouping basis.
   - Do not combine materially distinct states into a slash-separated or other
     composite row while claiming that no grouping occurred. Give each state a
     separate row until the required equivalence evidence exists.
   - If only one component can observe a value, make the handoff explicit. An
     internal representation that cannot carry a required public value blocks
     freezing the design; do not rely on the receiving component to infer it.
6. **Generality gate**
   - Treat any concrete example, fixture, project memory, copied handoff, or
     history-derived failure case that influenced the plan as a sampled case, not
     an exhaustive list or mandatory project shape.
   - Map each influential example to an abstract planning dimension before it
     affects scope, acceptance criteria, tests, or implementation order.
   - Name derived dimensions directly in the gate outcome. Use dimensions from
     the current request and evidence, not a pasted universal checklist.
   - For local data or file migrations, include exact names for relevant
     dimensions: `data contract` when schema versions, field mapping,
     reader/writer compatibility, or saved-file compatibility matter; include
     `file format compatibility`, `parser capability`, or
     `destructive-write risk` when those risks shape the plan. Do not replace
     `data contract` with a narrower phrase such as content preservation.
   - For parser, serializer, money/amount, or public API normalization plans,
     name relevant dimensions such as `data representation`,
     `public API contract`, `numeric precision`, `accepted input grammar`,
     `parser capability`, and `compatibility`. Omit dimensions that do not shape
     the current request or evidence.
   - Check whether the plan overfits to one sampled product, framework, UI
     modality, data shape, runtime, or toolchain. Remove adjacent surfaces,
     channels, security paths, APIs, or UI states that come only from examples,
     not the user's request or local evidence.
   - Keep the generated plan specific to the current user request and verified
     local evidence. Do not generalize away domain requirements, file formats,
     runtimes, user wording, or product decisions that are actually supplied.
   - If the user intentionally asks for a project-specific plan, record that
     reason instead of silently broadening or neutralizing the request.

## Method Selection

Choose the lightest method that still protects the work:

| Situation | Preferred method |
| --- | --- |
| New feature | Spec-driven |
| Complex business logic | Spec-driven + test-driven |
| Bug fix | Test-driven |
| Existing-code refactor | Test-driven |
| UI/UX implementation | Spec-driven |
| API, database, auth, permissions, or external contracts | Spec-driven + test-driven |
| Small function | Test-driven is usually enough |
| Larger feature development | Spec-driven is close to required |

Use the full spec-driven + test-driven flow and `strict` rendering when behavior
is complex, expensive to change later, or crosses data, security, permission,
API, billing, persistence, or external-service boundaries. Use `light` rendering
only for small, localized, low-risk work under the plan-depth rules above.
