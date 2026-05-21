---
name: vibe-clarify-requirements
description: Use when a user wants a chat-only requirements discussion or brief for a rough, ambiguous, contradictory, creative, non-technical, or underspecified coding goal before any plan artifact, code, tests, or file edits.
---

# Vibe Clarify Requirements

## Overview

Turn rough coding intent into a chat-only requirements brief without inventing
product behavior, scope, data rules, or success criteria.

This skill is clarification-only while active. The only deliverable is the chat
requirements brief. Active task lists, checklists, and tool-managed plans may
contain only requirement-clarification work. They must not include
implementation planning, implementation task entries, verification commands,
file edits, tests, commits, changelog changes, or release work.

Keep this skill self-contained. It may prepare the user to approve a next phase,
but it must not introduce a downstream skill or workflow. If the user names a
later workflow, treat that as their stated next phase.

## When to Use

Use this when the user:

- Describes a feature, fix, tool, UI, or workflow in vague terms such as "make
  it feel right", "make it better", "something like", "not sure yet", or
  "vibe coding".
- Asks for ideas, directions, alternatives, product options, or creative
  exploration before deciding what should be built.
- Asks for a requirements discussion, requirements brief, scope clarification,
  assumptions, acceptance criteria, product behavior, UX states, data rules,
  constraints, or tradeoffs before any plan artifact exists.
- Gives contradictory or incomplete requirements that would change what gets
  built, tested, stored, shown, migrated, or integrated.
- Is non-technical and needs practical options before a concrete engineering
  plan exists.

## When Not to Use

Do not use this skill when:

- The user supplied a concrete implementation plan or task list and asks to
  execute it.
- The user asks for code, tests, commits, release work, or file edits directly
  and the requirements are already concrete enough.
- The task is a small factual answer, explanation, command output, or code
  review with no requirement ambiguity.
- A bug report needs diagnosis of existing behavior rather than pre-plan
  requirement clarification.

## Core Rule

Clarify before planning or coding. Separate known requirements, safe defaults,
user decisions, and out-of-scope work.

Use brainstorming only to produce candidate options. Do not treat an idea as a
confirmed requirement until the user chooses it or explicitly approves it.

Do not create files, edit code, write tests, produce an implementation plan,
run checks, make commits, bump versions, or modify changelogs while using this
skill. Output the clarification in chat only.

Treat readiness, confirmation, approval, completed checklists, "requirements are
confirmed", "go ahead after this", and similar handoff wording as later-phase
context. They do not authorize this skill's current response to continue into
planning, implementation work, implementation task entries, tests, verification
commands, file edits, commits, or changelog changes.

## Clarification Workflow

1. **Capture the user's intent**
   - Preserve the user's wording for goals, product terms, audience, examples,
     and constraints.
   - Translate vague terms into observable behavior only when the user supplied
     enough context.
   - Mark inferred behavior as an assumption, not a confirmed requirement.

2. **Classify the requirement surface**
   - `Confirmed requirements`: behavior explicitly stated by the user.
   - `Reasonable defaults`: choices that can be safely proposed with low impact.
   - `Ideas or options`: candidate directions that need user selection before
     they become requirements.
   - `User decisions needed`: choices that change behavior, data, permissions,
     cost, user experience, compatibility, or verification.
   - `Out of scope`: adjacent capabilities or polish that would expand the first
     useful slice.
   - `Open unknowns`: facts that need local evidence, primary-source evidence,
     or user input before implementation planning.
   - Classify every build-changing dimension the user names or implies as confirmed scope, a default, a decision, out of scope, or an open unknown.
   - For billing, permissions, security, account settings, or recipient/routing changes, include auditability as a requirement dimension: whether changes are recorded, attributable, retained, or visible. Do not satisfy this by only putting an audit-log UI in `Out of Scope`.

3. **Choose the clarification mode**
   - Put only confirmed first-slice behavior in `Proposed Scope`.
   - If the user lists adjacent capabilities as "nice to have", "useful", or
     possible future pieces, keep them in `Out of Scope` or
     `Decisions Needed` until the user explicitly selects them for the first
     slice. A "subject to confirmation" qualifier is not enough to include them
     in `Proposed Scope`.
   - Use `Can Default` for confirmed scope or cross-cutting choices that stay valid regardless of which optional surface the user selects.
   - Do not put unselected adjacent capabilities in `Can Default`.
   - After the user selects a surface, a revised brief may propose defaults inside that selected surface.
   - Admin, reporting, audit, diagnostic, delivery-log storage, retention, and search surfaces are adjacent capabilities unless the user explicitly selected that surface.
   - Do not pre-stage adjacent surfaces in `Can Default` with "if chosen", "once selected", "confirm later", or similar gating.
   - If a default starts with "within whichever optional surface you select", move it to that surface's blocking decision or candidate option instead of `Can Default`.
   - In broad requests, do not say the likely first slice includes an adjacent surface unless the user explicitly chose it.
   - For a small, localized request, ask at most three direct questions.
   - Pick the highest-impact user decisions and move the rest into reasonable defaults, assumptions, out-of-scope items, or open unknowns.
   - Do not use `Decisions Needed`, a checklist, or multiple option groups to bypass the three-question limit.
   - Listing many open questions next to defaults still violates the cap.
   - Defaults should be concrete enough that the user can approve the brief with one short reply such as "use these defaults".
   - For a small localized request, if you present multiple choices for an interaction, validation rule, save behavior, or feedback pattern, mark one as the recommended default and give concrete values where values matter.
   - A bare option set, field list, or "choose one" prompt is not a default unless it includes the recommended choice the agent would use if the user says "use defaults".
   - If the brief says a default is proposed below, the later section must actually provide that default.
   - Use a grouped confirmation checklist when more than three answers would materially change a request that spans several surfaces, domains, high-impact rules, or contradictory goals.
   - Do not compress broad uncertainty into overloaded questions.
   - For bulk data creation, imports, migrations, destructive changes, and irreversible writes, classify write-safety decisions before readiness.
   - Write-safety decisions include review-before-write or preview, partial-failure behavior, duplicate or conflict handling, permissions, persistence, and rollback or recovery.
   - For imports and other bulk writes, name review-before-write or preview explicitly as its own default, decision, out-of-scope item, or open unknown.
   - A post-write result summary is not a substitute for pre-write preview behavior.
   - If a reasonable default exists, propose it and ask the user to confirm or
     override it instead of asking an open-ended question.
   - Ask only for decisions that cannot be settled from the user's request or
     later local investigation.

4. **Use brainstorming only when it helps**
   - Brainstorm when the user asks for ideas, creative directions, or multiple
     possible product shapes.
   - For data, permissions, billing, security, migrations, and other high-impact
     areas, classify decisions first. Offer creative alternatives only when the
     user asks for them.
   - Start with the goal and any known hard constraints.
   - Offer two to five options, never more than five.
   - Count merged or hybrid ideas as separate options if they can be chosen independently.
   - For each option, include when it fits, the main tradeoff, and what requirement would be adopted if chosen.
   - Keep high-impact choices conservative. Creative appeal is not evidence that
     risky behavior is acceptable.
   - End by asking which option, combination, or direction the user wants to
     adopt. Unchosen ideas remain options, not requirements.

5. **Write the chat-only requirements brief**
   - Use the user's language for the chat response unless they ask otherwise.
   - Keep identifiers, file paths, commands, field names, API names, and quoted
     product terms in their original form.
   - Be practical for non-technical users: explain consequences in product or
     workflow terms before naming implementation details.

6. **Stop for confirmation**
   - End with the readiness state and the exact decision or confirmation needed
     from the user.
   - Use exactly one readiness label: `Ready for planning`, `Conditional for planning`, or `Not ready for planning`.
   - Do not write `Ready for planning` with a pending-decision, pending-default, pending-confirmation, or approval-to-handoff qualifier.
     If the user still needs to confirm proposed defaults or choose among
     product options, use `Conditional for planning` unless the prompt already
     approved those requirements.
   - If the brief is `Ready for planning`, do not add nearby wording that makes readiness conditional, such as "after approval", "pending confirmation", or "approval to hand off".
   - If the brief is `Ready for planning` and the user already approved the clarified requirements, mark it ready and do not ask for a second approval just because routine planning checks remain.
   - When later work must not start in the same response, say only that this clarification step stops at the brief and later planning or implementation must happen in a later phase.
   - If the brief is `Conditional for planning` or `Not ready for planning`,
     name every blocking category: user decisions, non-user evidence checks, or both.
   - Stop after the requirements brief.
   - This stop still applies when the requirements look ready, the user already approved them, the user said to go ahead afterward, or a next planning or implementation step seems obvious.
   - Do not say user decisions are the only blockers if local evidence or open risks still affect requirement clarity or planning reliability.
   - If a local check is routine planning investigation, label it as a planning check rather than a readiness blocker.

## Requirements Brief Format

Use this structure unless the user asks for a different shape. Omit empty
sections.

```markdown
## Clarified Goal

## Proposed Scope

## Out of Scope

## Assumptions

## Ideas or Options

## Decisions Needed

## Success Criteria

## Open Risks or Unknowns

## Readiness
Ready for planning | Conditional for planning | Not ready for planning
```

For broad unclear requests, replace `Decisions Needed` with a checklist:

```markdown
## Confirmation Checklist

### Blocking Decisions
- [ ] Decisions that change the first buildable scope.

### Can Default
- [ ] Defaults for confirmed scope or cross-cutting choices that stay valid regardless of optional-surface selection.

### Later Decisions
- [ ] Items that can wait because they do not affect the first useful slice.
```

## Readiness States

- `Ready for planning`: The first useful scope, success criteria, assumptions,
  and known exclusions are clear enough for a later plan, and no requirement
  decision or default selection remains before that plan. This includes prompts
  where approval was already supplied.
- `Conditional for planning`: The first useful scope is mostly clear, but one or
  more named requirement decisions or pre-planning evidence checks must happen
  before planning can be reliable.
- `Not ready for planning`: The goal, audience, behavior, data handling, or
  constraints are too ambiguous or contradictory to plan without user decisions.

Select readiness by the blocker:

- Use `Conditional for planning` when the goal is coherent and the remaining blocker is bounded option selection, default confirmation, or pre-planning evidence that can change the requirement contract.
- Keep `Ready for planning` when remaining unknowns are routine planning checks that do not change the approved requirement contract, such as finding the exact existing UI surface, validation copy location, route name, schema field name, or update path.
- Do not downgrade an approved brief to `Conditional for planning` for bounded UI, copy, code-path, or implementation details that can be settled during planning.
- Treat local evidence as a pre-planning blocker when it can change the first-slice scope, data contract, user decisions, success criteria, compatibility, safety, or rollback/recovery expectations.
- Treat local evidence as a routine planning check only when it selects an implementation path for an already-clear requirement contract.
- For data creation or imports, existing entity schema, required fields, validation/create path, permission model, upload plumbing, and file limits are pre-planning evidence when they can change columns, mapping, limits, persistence, success criteria, or safety.
- If `Open Risks or Unknowns` says local evidence is needed before planning, include that evidence check in the `Readiness` blockers instead of saying only the user must confirm decisions.
- Use `Not ready for planning` when the user's stated requirements are mutually exclusive or the first slice cannot yet form a coherent contract.
- Also use `Not ready for planning` when a migration or destructive change has unresolved data, safety, compatibility, rollback, or recovery contracts.
- For creative exploration, choosing among concrete candidate directions is usually `Conditional for planning`, not `Not ready for planning`.

These states never authorize implementation. They describe only whether the
requirements are clear enough for a later planning step. Approval or readiness
can inform a later phase, but the current response still stops before any
same-turn planning, implementation work, implementation task entries, tests,
verification commands, file edits, commits, or changelog changes.

## Composition Boundaries

- This brief is input to later work, not a plan artifact and not implementation authorization.
- Completed checklists, confirmations, approvals, readiness states, and handoff phrases do not authorize same-turn planning, implementation work, implementation task entries, tests, verification commands, file edits, commits, or changelog changes.
- While this skill is active, active task lists and checklists may track only requirement clarification, confirmation, and unanswered decisions.
- If the user asks for a plan artifact, use this skill only when a requirements
  brief is still needed first.
- If the user asks to execute an existing plan, do not use this skill unless the
  plan is missing behavior-changing requirements and the execution workflow has
  stopped for clarification.
- If another active workflow already supplies the needed artifact, keep this
  skill to requirement questions and do not duplicate that output.
- Do not recommend or require a named downstream skill. Respect a user-named
  later workflow as context, but keep this skill's output to the chat brief.

## Common Mistakes

- Asking a long list of questions before classifying what is already known.
- Treating `Decisions Needed`, checklists, or option groups as a loophole around the three-question limit for small, localized requests.
- Listing options for a small localized request without marking one recommended default.
- Saying a reasonable default is proposed below, then asking the user to supply the values.
- Putting unconfirmed adjacent capabilities in `Proposed Scope` with a
  "subject to confirmation" qualifier.
- Putting unconfirmed adjacent capabilities in `Can Default` so they become staged or automatic first-slice scope.
- Pre-staging admin, reporting, audit, diagnostic, or log surfaces in `Can Default` with "if selected later" wording.
- Writing "within whichever admin/log surface you select" defaults in `Can Default` instead of keeping those details with the blocking decision or candidate option.
- Treating an audit-log UI exclusion as enough auditability coverage for billing, permission, account-setting, recipient, or routing changes.
- Treating a proposed default as a confirmed user requirement.
- Turning examples into the whole scope instead of naming the dimension they
  represent.
- Treating brainstormed ideas as requirements before the user chooses one.
- Offering more than five brainstorming options because the ideas are distinct.
- Covering only some build-changing dimensions and omitting another from the brief.
- Treating a post-write import summary as equivalent to review-before-write or preview.
- Expanding into adjacent features just because they are common in similar
  products.
- Using creative exploration to bypass high-impact decisions.
- Treating mutually exclusive requirements as merely conditional because options were listed.
- Treating bounded creative option selection as not-ready.
- Leaving rollback or recovery expectations as ordinary risks when the work depends on safety, invisibility, compatibility, or destructive-change recovery.
- Saying work is ready to implement when only planning readiness was established.
- Writing `Ready for planning` with pending default confirmation instead of using `Conditional for planning`.
- Writing `Ready for planning` and then saying the brief is ready only after another approval or handoff confirmation.
- Downgrading an approved, coherent brief to conditional because routine planning checks remain.
- Saying only user confirmation is needed when local evidence is also named as a pre-planning blocker.
- Calling a local evidence check routine when it can change scope, data contracts, success criteria, safety, or recovery.
- Calling existing schema, validation, create path, upload plumbing, or file-limit checks routine while saying they may change columns, mapping, limits, or data contracts.
- Continuing into planning or implementation because the user said the requirements are approved, ready, or should be followed by "go ahead".
- Adding implementation or verification work to an active task list while this skill is still producing the requirements brief.
- Naming or requiring a specific downstream skill or workflow.

## Self-Check

Before responding, check:

- Is the output chat-only?
- Are confirmed requirements, assumptions, defaults, decisions, and out-of-scope
  items separated?
- If brainstorming was used, are ideas clearly marked as options rather than confirmed requirements, and are there two to five options?
- Did every build-changing dimension named or implied by the user appear in one brief section?
- For billing, permission, security, account-setting, recipient, or routing changes, did you address auditability as requirement behavior instead of only excluding an audit-log UI?
- For bulk data writes or imports, did you account for review-before-write or preview, partial failure, duplicate or conflict handling, permissions, persistence, and rollback or recovery?
- For bulk data writes or imports, is review-before-write or preview explicit rather than implied by a post-write result summary?
- For a small request, are there no more than three direct questions, and can the proposed defaults be accepted with one short reply?
- If a small request has options, is one option marked as the recommended default with concrete values where needed?
- For a broad request, is there a grouped confirmation checklist instead of an
  interrogation?
- Are `Can Default` items limited to confirmed scope or cross-cutting choices that stay valid regardless of optional-surface selection?
- Are admin, reporting, audit, diagnostic, and log-related surfaces absent from `Can Default` unless the user selected that surface?
- Did you move "within whichever optional surface you select" defaults out of `Can Default`?
- Does readiness wording avoid understating open risks or local evidence still needed for planning?
- Did you classify local evidence that can change scope, data contracts, success criteria, safety, or recovery as a pre-planning blocker rather than routine planning work?
- If schema, validation, create path, upload plumbing, or file limits may change columns, mapping, limits, persistence, success criteria, or safety, did readiness name that evidence blocker?
- If the brief is approved and coherent, does readiness avoid blocking on routine planning checks?
- If readiness is `Ready for planning`, does the surrounding text avoid "after approval", "pending confirmation", or "approval to hand off" wording?
- If readiness is conditional, does it name both user decisions and non-user evidence checks when both remain?
- Does the response stop after the requirements brief even if the user approved the requirements, said to go ahead, or the next phase seems obvious?
- Do any active task lists or checklists contain only requirement-clarification work while this skill is active?
- Does the response avoid named downstream-skill requirements unless the user
  supplied the name as context?
- Is the readiness label exactly one of the three states, and does it match the unresolved decisions without a contradictory parenthetical?
- Did you distinguish bounded option selection from contradictory or unresolved data, safety, compatibility, rollback, or recovery contracts?
