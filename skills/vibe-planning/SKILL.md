---
version: 3.0.0
name: vibe-planning
description: >
  Use when the user wants planning before coding: plan mode, create a plan,
  implementation plan, specification, acceptance criteria, test plan, vibe
  coding, requirements clarification, what to build first, or rough,
  ambiguous, feasibility-sensitive, non-technical, or not-yet-implementable
  coding requests in any language.
---

# Vibe Planning

## Overview

Turn rough vibe-coding intent into a plan another engineer or agent can execute
without inventing missing behavior. Treat the user's request as valuable intent,
not verified fact: preserve the goal, prove what can be proven, and make
uncertainty visible.

`vibe-planning` is plan-only. While using it, create or update only the plan
artifact. Do not implement, edit application code, tests, skill packages, evals,
non-plan docs, configs, changelogs, commits, or any other non-plan artifact.

Apply the same boundary to the active task list, checklist, or tool-managed
plan. Active tasks may cover only plan artifact work. Do not add current-turn
implementation phases, execution slices, non-plan edit tasks, commit tasks, or
"now implement the plan" follow-ups. If the user asks for planning and
implementation in one request, write or revise the plan artifact and stop.

This skill is independent. Do not assume another planning skill, guard,
execution skill, commit-message skill, or other companion skill is available.
When skill metadata is visible in the current environment, use it only to plan
availability-driven skill usage in the generated artifact; do not make an
unavailable skill a requirement.

## Output Language and Artifact

Resolve the user-facing summary language before drafting the plan:

1. Explicit user instruction in the current request.
2. `VIBE_PLANNING_OUTPUT_LANG`, if the environment is safely readable. If the
   prompt itself includes an assignment-like value such as
   `VIBE_PLANNING_OUTPUT_LANG=English`, treat it as the user's explicit setting
   for that request.
3. Agent or project configuration, if exposed in the current environment,
   system/developer instructions, project instructions, or already-loaded local
   config.
4. The conversation language.

Do not run broad discovery just to find a language setting. If a configured
language cannot be read, treat it as unset and continue. Keep file paths, code
identifiers, API names, commands, field names, error messages, and quoted source
material in their original language unless the user explicitly asks for
translation.

Write the full implementation plan as a Markdown artifact by default, then give
the user only a concise summary in the resolved user-facing language.
Use this file path selection order:

1. A user-specified local path.
2. An existing project convention for plans or specs if it is obvious from the
   workspace, such as `plans/`, `docs/plans/`, or `specs/`.
3. `plans/YYYY-MM-DD-<goal-slug>-implementation-plan.md` at the workspace root,
   using the current local date and a short lowercase ASCII slug.

Do not overwrite an existing plan file. If an explicit user path already exists,
ask before replacing it; use a non-destructive sibling only when the user allowed
that behavior. For generated default names, append a numeric suffix such as `-2`
on collision. Do not modify `.gitignore` only because a plan artifact was
created.

The artifact is for later agents and implementers. Use fixed English section
headings and concise implementation-oriented English prose for structure.
Preserve user-authored goals, requirements, in-scope and out-of-scope
statements, quoted source material, domain vocabulary, product labels,
identifiers, paths, commands, errors, API names, and field names in their
original language. When an English operational paraphrase is useful, place it
after the original wording instead of replacing the original.

After writing the file, reply with only the essentials in the resolved
user-facing language:

- Plan file path.
- Current slice.
- Proceed condition.
- Key `Unproven`, `Accepted risk`, blocker, or decision items.
- The next action needed from the user, if any.

For non-technical users, write the chat summary in plain terms in the resolved
user-facing language. Avoid raw labels such as `slice`, `Proceed condition`,
`Unproven`, and `Accepted risk` unless the user already uses them or you explain
them immediately. Prefer practical meanings such as "what we will build first",
"what must be decided before work starts", "not verified yet", and "a tradeoff
the user explicitly accepts". Preserve technical identifiers only when needed
for traceability, and explain their practical meaning.

Do not paste the full plan into chat unless file writing is unavailable, unsafe,
or explicitly declined. If no file was written, state the reason and provide the
complete plan artifact in the reply using the same English artifact structure.

## Core Rules

- This skill is for implementation-plan creation or revision only. Stop after
  the plan artifact and concise summary. Implementation requires a separate
  execution request outside `vibe-planning`.
- Do not provide patches, edit non-plan files, make commits, or claim that code,
  tests, non-plan docs, evals, configs, changelogs, or other implementation work
  is complete. Non-mutating investigation is allowed when it grounds the plan.
- Plan-readiness language is later-execution handoff, not current-turn
  authorization. `Implementation plan`, `Commit checkpoints`, `Implementation
  handoff`, `Current slice`, `Proceed condition`, `implementation-ready`, or a
  completed planning phase may indicate that a separate execution request can
  begin; they must not trigger implementation while this skill is active.
- Ground the plan in primary sources or actual investigation before asking the
  user to decide. Read relevant local code, tests, configs, schemas, docs, logs,
  issue text, or official documentation first.
- Use official docs, upstream source, vendor documentation, standards, or
  user-provided source material for claims about external systems. Use local
  reproduction or direct repository inspection for claims about the current
  workspace.
- Do not present memory, inference, forum summaries, or unchecked assumptions as
  fact. Mark them as `Unproven`.
- Do not accept user claims blindly. If a claim is false, stale, unsupported, or
  infeasible, state the evidence and propose the closest viable alternative.
- Do not invent unavailable skills or assume a fixed companion skill set. A plan
  may name a specific skill only after its availability was verified from the
  current environment, user-provided material, project instructions, or local
  metadata.
- Treat concrete examples, fixtures, project memories, and history-derived
  failure cases as evidence or pressure tests, not skill boundaries. Before an
  example changes scope, acceptance criteria, tests, or implementation order,
  map it to a broader planning dimension it represents, such as external
  contracts, data shape, lifecycle state, destructive risk, local evidence
  grounding, or optional tool usage. Name dimensions that shape the generated
  plan.
- Respect the user's requested outcome as far as reality allows. When a request
  cannot be implemented literally, preserve the intent and adjust the mechanism.
- When the user asks for broad UX improvements, make the first slice complete
  or improve an existing verified surface before adding adjacent unverified
  channels, providers, modes, or settings.
- Ask questions only for intent, tradeoffs, permissions, business rules, or
  missing context that investigation cannot determine.
- For non-technical users, explain choices in plain language and translate
  technical consequences into product or workflow impact.
- For non-technical "what should we build first" requests, recommend the first
  slice supported by local evidence. Ask only for product wording, business
  rules, or tradeoffs that local investigation cannot settle.
- Define acceptance criteria and tests before implementation steps.
- Do not invent numeric limits, thresholds, timing windows, quotas, or product
  constants. Use values only when they come from user requirements, local
  evidence, primary sources, or accepted risk; otherwise label the value
  `Unproven` and make proof or a product decision precede implementation.
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

Every `Unproven` or `Accepted risk` item must include impact, the fastest proof
path, and where it must be revisited.

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
3. **Test no-escape gate**
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
4. **Generality gate**
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

Use the full spec-driven + test-driven flow when behavior is complex, expensive
to change later, or crosses data, security, permission, API, billing,
persistence, or external-service boundaries. Use a compact version for small,
localized work.

## Planning Workflow

1. **Classify the work**
   - Identify whether the task is a feature, bug fix, refactor, UI/UX change,
     integration, API/DB/permission change, or small local implementation.
   - Choose spec-driven, test-driven, or combined planning from the table.
   - Split large requests into the smallest useful current slice.
   - If local evidence shows an existing partial surface and the user mentions
     adjacent future capabilities, make the first slice complete or improve that
     surface unless a verified requirement makes an adjacent capability part of
     the current outcome.
2. **Investigate before asking**
   - Inspect the workspace and primary sources relevant to the current slice.
   - Record facts with evidence labels.
   - If primary sources are unavailable, say why and keep dependent claims
     `Unproven`.
3. **Clarify intent**
   - Ask only plan-changing questions that cannot be answered from evidence.
   - For non-technical users, offer concrete choices with consequences instead
     of abstract architecture terms.
4. **Write or refine the specification**
   - State the goal, users, in-scope behavior, out-of-scope behavior, constraints,
     and success criteria.
   - Review the specification for ambiguity, contradiction, missing states,
     hidden dependencies, and unverifiable assumptions.
5. **Define acceptance criteria**
   - Convert the clarified specification into observable pass/fail criteria.
   - Include negative cases, permissions, failure states, empty states, migration
     or compatibility expectations, and UX states when relevant.
   - For editable forms or settings screens, explicitly decide whether cancel,
     reset, or navigation-away behavior is in scope; when it already exists,
     preserve it with acceptance criteria and tests.
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
   - For UI, include interaction, state, responsive layout, and accessibility
     checks when relevant.
7. **Run plan integrity gates**
   - Apply the `Fact cleanup gate`, `Evidence downgrade gate`, `Test
     no-escape gate`, and `Generality gate` before finalizing the plan.
   - When revising an existing plan after investigation, treat stale facts and
     old implementation options as defects to remove, not context to preserve.
   - If a gate fails, update the specification, acceptance criteria, tests,
     risks, and proceed condition before implementation is allowed to start.
8. **Plan available skill usage**
   - Inspect available skill metadata at plan creation time when it is already
     exposed in the runtime, supplied by the user, documented in project
     instructions, or cheaply discoverable from local skill metadata.
   - Do not perform broad filesystem, network, package-manager, or marketplace
     discovery solely to find optional skills. If skill metadata is not visible
     or cannot be read cheaply, say that no matching optional skill was verified
     and continue with the normal plan.
   - Select only skills whose descriptions match the planned work, method,
     stack, artifact, or workflow checkpoint. Do not include a skill just because
     it is installed.
   - For each selected skill, state when to use it, why its description matches,
     the availability source, and the fallback if that skill is unavailable
     when the plan is executed.
   - If no optional skill is verified as matching, still include one
     `Skill usage plan` entry using the same fields:
     `Skill: No matching optional skill verified`, `Availability source`,
     `Use when: Not applicable`, `Matching reason: Not applicable`, and
     `Fallback if unavailable`. The fallback should say to continue with the
     normal plan, repository rules, and any proposed checkpoint messages.
   - When the plan includes commit checkpoints and a commit-message-writing
     skill is verified available, schedule that skill after checkpoint
     verification and before finalizing each commit message. If no matching
     commit-message skill is verified, fall back to the repository's commit
     rules, recent local history, and the proposed standalone Conventional
     Commit message in the checkpoint.
   - Do not let optional skill usage weaken the core plan contract: acceptance
     criteria, tests, evidence labels, proceed conditions, and user decisions
     still control the work.
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
   - Include commit checkpoints only for multi-slice plans with independently
     verifiable code-producing slices. Each checkpoint states the intended
     scope, required verification, and a proposed standalone Conventional Commit
     message that names the concrete change.
   - For single-slice, discovery-only, blocked, discovery-first without a
     verified code-producing slice, destructive-risk-blocked, no-code-slice, or
     work-in-progress plans, write only: `Commit checkpoints are omitted until a code-producing slice is verified.`
   - Do not split a single current slice into artificial test, fix, docs, or
     changelog checkpoints only to create commit messages. Red or failing-test
     proof work is not a verified code-producing checkpoint.
11. **Prepare the implementation handoff**
   - Include a short handoff that starts with "When implementing this plan" so
     pasted plans remain self-contained execution requests.
   - Tell the implementer to treat the document as authoritative, re-check local
     facts before editing, follow the acceptance criteria, test plan, and skill
     usage plan, implement only the current in-scope slice, and stop on a
     blocked `Proceed condition` or contradictory local evidence.

## Handling Incorrect or Impossible Requests

When the user's requested mechanism is wrong or impossible:

1. Restate the user's likely underlying goal.
2. Cite the verified source or local evidence that blocks the literal request.
3. Explain the risk in practical terms.
4. Offer the closest viable alternative.
5. Ask for a decision only if the alternatives change product behavior, cost,
   timeline, data handling, security posture, or user experience.

Do not bury impossibility inside a generic risk list. Put it near the decision
it affects.

## Accepted-Risk Branch

If the user explicitly chooses to continue with an unproven assumption:

- Record the exact assumption.
- Record the user's acceptance and rationale.
- Record the impact area: feasibility, behavior, data, integration, performance,
  security, UX, cost, or schedule.
- Keep the evidence label as `Accepted risk`.
- Include the fastest proof path and revisit trigger.
- Make implementation steps conditional where the unproven assumption could
  invalidate the plan.

Never use accepted risk for irreversible, destructive, unsafe, illegal, or
credential-exposing actions. Those require proof or a safer alternative.

## Standard Plan Artifact

Use this structure for the implementation-ready plan file. Keep it compact for
small tasks, but preserve the order: requirements and tests come before
implementation.

The `Implementation plan` section is handoff for a later execution request. It
does not authorize the planner to add active implementation tasks or edit
non-plan files in the same response.

```markdown
# [Plan title]

## Goal
- [What the user wants to accomplish and for whom]

## Verified facts and sources
| Claim | Evidence | Source | Impact |
| --- | --- | --- | --- |

## Requirements
- In scope:
- Out of scope:
- Constraints:

## Ambiguities, questions, and decisions
- Item:
- Options or decision:
- Evidence:
- Recommended path:

## Acceptance criteria
- [Observable pass/fail criterion]

## Test plan
- Acceptance tests:
- Regression tests:
- Negative and edge cases:
- Manual or visual checks:

## Plan integrity gates
- Fact cleanup gate:
  - Status or not-applicable reason:
  - Search scope:
  - Stale `Unproven`, old API names, old field names, old commands, and old
    implementation proposals removed or rewritten:
- Evidence downgrade gate:
  - Status or not-applicable reason:
  - Visual, performance, packet-volume, responsiveness, and UX claims without
    measurement downgraded to `Unproven` or `Accepted risk`:
- Test no-escape gate:
  - Status or not-applicable reason:
  - Important contracts:
  - Blockers before implementation or alternative proof paths:
- Generality gate:
  - Status or not-applicable reason:
  - Concrete examples, fixtures, memories, or historical cases that influenced
    the plan:
  - Abstract planning dimensions derived from those examples:
  - Explicit dimension names that shaped scope, acceptance criteria, tests, or
    implementation order:
  - Overfit risks and scope corrections:

## Skill usage plan
- Skill:
- Availability source:
- Use when:
- Matching reason:
- Fallback if unavailable:
- [If no optional skill was verified, include the same fields with
  `Skill: No matching optional skill verified`, `Use when: Not applicable`, and
  `Matching reason: Not applicable`.]

## Implementation plan
1. [Proof or setup step, if needed]
2. [Implementation step]
3. [Verification and diff-review step]

## Commit checkpoints
- [For multi-slice plans with code-producing slices: checkpoint scope, required
  verification, and a proposed standalone Conventional Commit message. For
  single-slice, blocked, discovery-only, discovery-first without a verified
  code-producing slice, destructive-risk-blocked, no-code-slice, or
  work-in-progress plans, write only: `Commit checkpoints are omitted until a code-producing slice is verified.`
  Do not list future, red-test-only, docs-only, or changelog-only checkpoints.]

## Risks and unproven items
- Item:
- Evidence label: `Unproven` | `Accepted risk`
- Impact:
- Fastest proof path:
- Revisit trigger:

## Implementation handoff
- When implementing this plan, treat this document as authoritative. Re-check
  local facts before editing, follow the acceptance criteria, test plan, and
  skill usage plan, implement only the current in-scope slice, and stop if the
  `Proceed condition` is blocked or local evidence contradicts the plan. This
  plan artifact is not implementation authorization; code, tests, non-plan docs,
  evals, configs, changelogs, commits, and other non-plan edits require a
  separate execution request.

## Proceed condition
- [State whether implementation is ready, conditional on accepted risk, or
  blocked pending proof/user decision.]
```

For discovery-only phases, replace `Implementation plan` with `Discovery plan`
and list proof tasks, exit criteria, and the next decision point.

## Quality Checklist

Before finalizing the plan, check that:

- Discoverable facts were investigated before asking the user.
- Technical jargon is explained or avoided when the user may be non-technical.
- The full plan was written to a durable Markdown artifact, or the fallback
  reason for chat-only output is stated.
- The plan artifact uses stable English section headings and preserves
  user-authored intent, requirements, quoted material, and domain terms in their
  original language.
- The user-facing reply is a concise summary in the resolved language and does
  not duplicate the full artifact unless file output was unavailable or declined.
- Every implementation-affecting claim has an evidence label.
- False or infeasible requirements are challenged with evidence and alternatives.
- Acceptance criteria are observable.
- Tests come before implementation steps.
- The plan-only boundary is respected: no non-plan files were edited, no patches
  were provided, no commits were made, no implementation completion was claimed,
  and no active implementation tasks, phases, or follow-up execution items were
  added while using `vibe-planning`.
- `Commit checkpoints` matches the `Proceed condition`: ineligible plans do not
  include proposed commit messages, and single-slice work was not split into
  artificial checkpoints.
- The `Fact cleanup gate` removed stale `Unproven` text, old API names, old
  field names, old commands, and superseded implementation proposals after facts
  changed.
- The `Evidence downgrade gate` keeps unmeasured appearance, performance, packet
  volume, responsiveness, and UX claims as `Unproven` or `Accepted risk`.
- The `Test no-escape gate` blocks implementation or defines an equivalent
  proof path when an important contract cannot be verified as planned.
- The `Generality gate` treats examples, fixtures, project memories, and past
  failures as sampled cases, not exhaustive lists or mandatory branches.
- Concrete examples that affect the plan are mapped to abstract planning
  dimensions before they influence scope, acceptance criteria, tests, or
  implementation order.
- Abstract planning dimensions are named explicitly when they shape the plan,
  using names from the current request and evidence rather than a generic
  checklist.
- Local data or file migration plans use exact dimension names when relevant,
  including `data contract` for schema versions, field mapping, reader/writer
  compatibility, or saved-file compatibility.
- Bug reports keep the reported symptom, local facts, and root-cause hypothesis
  separately labeled; no unproven cause is presented as the root cause.
- Plans do not expand into adjacent surfaces, channels, APIs, security paths, or
  UI states only because examples mention them.
- Plans do not ignore non-web, non-UI, non-product, CLI, library, data,
  infrastructure, runtime, or domain-specific work.
- Generality checks do not weaken local evidence, erase supplied domain details,
  or make the plan less specific to the user's current request.
- The skill usage plan names only verified available skills with timing and
  fallback, or records `No matching optional skill verified` with the same
  availability source, timing, matching reason, and fallback fields.
- Implementation steps do not rely on unlabeled assumptions.
- The implementation handoff is present, self-contained, and does not require
  unverified or unavailable skills.
- Accepted risks are explicit, scoped, and revisitable.
- The user-facing summary language follows the configured precedence.
