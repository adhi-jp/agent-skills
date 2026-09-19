# Core Planning Controls Reference

Read this reference before finalizing any implementation plan or plan revision. It owns evidence labels, `Unproven` triage and accepted risk, plan depth, the integrity gates, and routing to the high-risk references.

## Core Rules

- When the requested mechanism is wrong or impossible, keep the intent and
  change the mechanism: restate the likely goal, cite the evidence that blocks
  the literal request, explain the practical risk, and offer the closest viable
  alternative next to the decision it affects. Ask only when the alternatives
  change product behavior, cost, timeline, data handling, security posture, or
  user experience.
- For destructive, auth/session, credential, permission, billing, or
  data-migration plans, acceptance criteria and tests cover enough
  auditability to identify what changed, what was affected, and how rollback or
  recovery is verified; do not invent an audit-log UI or retention feature the
  user did not request.

### Human-Risk Decisions

<!-- shared-contract:begin human-risk-decisions source=shared/vibe-contract.md -->
**Leave every human-risk decision to the human user.**

- Human-risk means destructive, irreversible, credential, auth or session, permission, billing, security, data-migration, legal or compliance, paid, production, external-side-effect, release, or history-mutation decisions.
- Require explicit user acceptance already recorded for the current artifact or request; never let a handoff, proxy, delegated recommendation, or AI-selected default accept one.
- Never proceed, hand off, or route past an unresolved one; ask the smallest question or return to the artifact that owns the decision.
<!-- shared-contract:end human-risk-decisions -->

## High-Risk Planning Controls

Apply a control only when its trigger matches the current slice; these are not a
checklist for every plan.

- `references/behavioral-equivalence-analysis.md` — the slice touches existing
  behavior: refactors, migrations, replacements, internal implementation
  changes, and explicit behavior changes, even when the user expects behavior
  to stay the same. Build its behavior contract inventory first.
- `references/change-recovery-checklist.md` — replacement, restoration,
  rollback, or rewrite of behavior that used to be correct.
- `references/plan-boundary-controls.md` — the plan incorporates review
  comments, diagnostic findings, audit output, analyzer warnings, or additions
  made after success criteria were written.
- `references/failure-pattern-checklist.md` — high-risk surfaces such as
  lifecycle ordering, shared state, persisted config, trust boundaries,
  counters, build or release paths, tool capabilities, and multi-phase drift;
  apply only the matching sections.

## Accepted-Risk Semantics

<!-- shared-contract:begin accepted-risk-semantics source=shared/vibe-contract.md -->
**Only `Accepted risk` lets an `Unproven` item support work that depends on it.**

- Accept only on the human user's explicit choice after the impact was explained, or on the bound plan's recorded acceptance for this request; never on a proxy, delegate, AI-selected default, or a low-risk judgment.
- Record the assumption, who accepted it and why, the impact area, the fastest proof path, and the revisit trigger, tied to the conditional steps it supports; the item stays `Accepted risk`, never verified fact.
- Turn every other `Unproven` item that blocks current work into proof work, a question, or a blocker; defer decisions the current work does not need.
- Never use it for irreversible, destructive, unsafe, illegal, or credential-exposing actions: those need proof, a safer alternative, or the user's explicit human-risk decision.
<!-- shared-contract:end accepted-risk-semantics -->

## Plan Depth and Unproven Triage

Choose depth after initial investigation and escalate when new evidence reveals
a `strict` trigger. Never choose `light` because it is faster when the missing
investigation could change scope, acceptance criteria, UX behavior, proof
strategy, or the proceed condition.

- `light`: small, localized, low-risk slices after local evidence shows no
  existing-behavior change, external contract, destructive operation,
  auth/security/billing boundary, data migration, diagnostic finding,
  replacement/restoration/rollback/rewrite, or current-slice implementation
  blocker. `light` compresses rendering only — short sections, conditional
  sections omitted, gate outcomes in a line or two — never evidence labels, the
  criteria-then-tests-then-steps order, self-review, risk-triggered review, or
  the proceed condition.
- `strict`: any of those triggers, or a `must preserve` equivalence dimension
  that turns out non-equivalent. `strict` adds the controls its triggers
  require, not a larger default test inventory.

Scale effort from the current slice's risk, proof, consent, and recovery
obligations, using confirmed operating context, exposure, failure consequences,
and recovery options. Repository size or a personal or hobby label may compress
rendering but never removes mandatory high-risk controls or consent,
data-safety, or proof obligations; a count of coincident faults is not a safety
policy, and backups must be evidenced before they support a recovery argument.
Bound planned tests, tooling, and review effort to open acceptance criteria and
the proof this workflow requires (this reference's gates and the planning
workflow's test-design step); required proof is never optional hardening, and
optional extensions need scope and cost selection.

Before freezing a universal bound or exhaustive claim, require evidence at and
beyond the boundary; otherwise keep the abstract property and leave the
enumeration `Unproven`.

Check every criterion for coherence and mechanism feasibility against the
requirements, the target toolchain, earlier and later slice interfaces, and the
real actor for every operation. Contradictory proof requirements, vocabulary
borrowed from a neighboring layer, unavailable proof routes, impossible
operations, or insufficient earlier interfaces require correcting the plan, not
weakening a test.

Classify every `Unproven` or `Accepted risk` item by `Phase relevance`:

- `current-slice implementation blocker`: needed to define, implement, or test
  the current acceptance criteria, or affecting current-slice feasibility,
  behavior, data handling, permissions, security, external contracts, or
  destructive risk. Implementation is blocked unless the user explicitly
  accepts a scoped `Accepted risk`.
- `proof before implementation`: resolved by a discovery or proof step before
  code changes begin; the plan may be discovery-first, and implementation stays
  blocked until the proof completes. Inside a discovery-first plan, use
  `current-slice implementation blocker` only for items that need a user or
  product decision or accepted risk before criteria can be frozen.
- `deferred decision`: optional, future-phase, avoidable by narrowing the
  criteria, or not needed for the bounded slice; record impact and revisit
  trigger and do not block the slice on it. Unknown constants, limits, and
  adjacent enhancements outside the slice go here instead of being invented.
- `non-implementation follow-up`: rollout, monitoring, product copy, or future
  hardening outside the current implementation contract.

When an `Accepted risk` could invalidate a named local identifier, mapping,
file-backed fact, or external contract before implementation, put the re-check,
with the concrete sources to re-read, in the first dependent step; a generic
handoff reminder to re-check local facts is not enough.

## Evidence Labels

<!-- shared-contract:begin evidence-classes source=shared/vibe-contract.md -->
**Label every load-bearing claim with one of four evidence classes.**

- A claim is load-bearing when it affects scope, feasibility, behavior, verification, risk, order of work, commit authorization, or whether work may proceed.
- `Primary source`: official or upstream documentation, specification, or source code; user-provided source material; a known-good prior implementation.
- `Local investigation`: what this workspace shows — files, configs, schemas, logs, existing tests, non-mutating command output, reproduced behavior.
- `Unproven`: memory, inference, secondhand or unchecked claims, stale documentation, missing access, hypotheses.
- `Accepted risk`: an `Unproven` item the user explicitly chose to proceed on after its impact was explained, or that the bound plan records as accepted.
- Never rename or redefine these classes; a package may add its own disjoint labels or freshness qualifiers in its own text.
<!-- shared-contract:end evidence-classes -->

Record a value calculated from measured or source-backed inputs as
`Local investigation (derived)` with its formula, assumptions, and at least one
break condition; verified inputs do not verify the arithmetic. Before a derived
value becomes a public limit, frozen constant, acceptance threshold, or test
invariant, confirm it empirically or keep it `Unproven` with proof before
implementation. When an outside draft supplies only a derived result, record the
formula as unavailable instead of reconstructing one from nearby numbers, keep
any supplied occupancy or full-fill assumption, and name a concrete break
condition.

## Plan Integrity Gates

Run these gates before finalizing any plan and after every revision that follows
new evidence. Record outcomes concisely in `Plan integrity gates`: always the
investigation surfaces, and otherwise only gates that changed or blocked the
plan.

1. **Fact cleanup gate** — Plan updates replace rather than append. When a
   hypothesis is verified, refuted, or replaced, search the plan and any copied
   handoff notes for the old `Unproven` wording, API, field, and command names,
   and superseded proposals, and delete or rewrite them; keep a rejected design
   only as an explicit rejected alternative. A plan that holds both the new fact
   and the old hypothesis fails.
2. **Evidence downgrade gate** — Appearance, rendering quality, performance,
   packet volume, memory use, efficiency, responsiveness, usability, and "feels
   better" claims stay `Unproven` unless backed by measurement, screenshots, run
   logs, profiling, user research, primary-source limits, or direct local
   reproduction; wording such as "should be fine" or "visually cleaner" never
   appears as fact. A user who proceeds without measurement makes the item
   `Accepted risk`.
3. **Investigation adequacy gate** — Every material surface named in the
   workflow's investigation step is inspected, unavailable with its impact, or
   outside the narrowed slice; a skipped surface that could change the plan
   keeps it discovery-first or blocked.
4. **Test no-escape gate** — For each important contract the plan depends on
   (API fields, serialization, persistence, network behavior, permissions,
   migrations, visual behavior, cross-loader or external-service behavior):
   - Never replace a test that cannot verify the contract with a weaker one that
     proves only implementation details or serialization shadows. Block
     implementation or add an alternative proof path that proves the same
     contract; record any reduced claim as `Unproven` or `Accepted risk`.
   - Record the known-bad or current baseline of every metric used as an
     acceptance gate. A metric that returns the same verdict before and after
     the planned change is non-discriminating whichever verdict it returns and
     cannot gate implementation completion.
   - Ask what wrong implementation would still pass each load-bearing
     assertion. Reject proof resting only on an unused observation seam,
     expectations imported from the implementation, best-case input for a
     general claim, final-state traces for forbidden-call claims, or missing
     lifecycle or encoding branches.
   - Give every absence assertion over a captured channel a positive control in
     the same channel that proves capture was live and correctly pathed, and
     assert forbidden fields explicitly.
   - For a load-bearing invariant, or an assertion added or strengthened while
     product behavior is already correct, plan a safe reversible mutation of
     the exact asserted surface in a scratch copy or equivalent controlled
     surface. The proof names the controlled change, the assertion that failed
     and its observed status or diagnostic, cleanup evidence, and the final
     unmodified check. A surviving mutation or an assertion that never applied
     is a proof defect; when the exact failure cannot be observed, the proof
     stays `Unproven`.
5. **Representation coverage gate** — When the plan freezes both a public
   contract and an internal protocol, state machine, schema, or result
   representation, map every required public field or outcome on every terminal
   path to the internal observer and carrier that transports it. Give each path
   whose origin, available evidence, cleanup state, precedence, or carrier can
   differ its own row — assertion or script failure, connection failure,
   timeout, cancellation, partial cleanup — and group paths only with evidence
   that observer, carrier, and field availability match. A value only one
   component can observe needs an explicit handoff; an internal representation
   that cannot carry a required public value blocks freezing the design.
6. **Generality gate** — Treat examples, fixtures, project memories, copied
   handoffs, and history-derived failure cases as samples: map each to the
   planning dimension it represents before it changes scope, criteria, tests,
   or order, and remove surfaces, channels, APIs, or UI states that come only
   from examples. Keep the domain requirements, formats, runtimes, and wording
   the user actually supplied.
