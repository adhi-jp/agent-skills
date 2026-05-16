---
name: vibe-clarify-requirements
description: Use when a user wants a chat-only requirements discussion or brief for a rough, ambiguous, contradictory, creative, non-technical, or underspecified coding goal before any plan artifact, code, tests, or file edits.
---

# Vibe Clarify Requirements

## Overview

Turn rough coding intent into a chat-only requirements brief without inventing
product behavior, scope, data rules, or success criteria.

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

3. **Choose the clarification mode**
   - Put only confirmed first-slice behavior in `Proposed Scope`.
   - If the user lists adjacent capabilities as "nice to have", "useful", or
     possible future pieces, keep them in `Out of Scope` or
     `Decisions Needed` until the user explicitly selects them for the first
     slice. A "subject to confirmation" qualifier is not enough to include them
     in `Proposed Scope`.
   - For a small, localized request, ask at most three direct questions.
   - If more than three answers would materially change the outcome, do not
     compress them into overloaded questions. Render a confirmation checklist
     grouped by decision type.
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
   - Offer two to five options. For each option, include when it fits, the main
     tradeoff, and what requirement would be adopted if chosen.
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
   - If the brief is `Ready for planning`, say that the clarified requirements
     can move to the next phase after user approval.
   - If the brief is `Conditional for planning` or `Not ready for planning`,
     name the blocking decisions or proof needed.

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
- [ ] Proposed defaults the user may accept or override.

### Later Decisions
- [ ] Items that can wait because they do not affect the first useful slice.
```

## Readiness States

- `Ready for planning`: The first useful scope, success criteria, assumptions,
  and known exclusions are clear enough for a later plan after user approval.
- `Conditional for planning`: The first useful scope is mostly clear, but one or
  more named decisions or evidence checks must happen before planning can be
  reliable.
- `Not ready for planning`: The goal, audience, behavior, data handling, or
  constraints are too ambiguous or contradictory to plan without user decisions.

These states never authorize implementation. They describe only whether the
requirements are clear enough for a later planning step.

## Composition Boundaries

- This brief is input to later work, not a plan artifact and not implementation
  authorization.
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
- Putting unconfirmed adjacent capabilities in `Proposed Scope` with a
  "subject to confirmation" qualifier.
- Treating a proposed default as a confirmed user requirement.
- Turning examples into the whole scope instead of naming the dimension they
  represent.
- Treating brainstormed ideas as requirements before the user chooses one.
- Expanding into adjacent features just because they are common in similar
  products.
- Using creative exploration to bypass high-impact decisions.
- Saying work is ready to implement when only planning readiness was established.
- Naming or requiring a specific downstream skill or workflow.

## Self-Check

Before responding, check:

- Is the output chat-only?
- Are confirmed requirements, assumptions, defaults, decisions, and out-of-scope
  items separated?
- If brainstorming was used, are ideas clearly marked as options rather than
  confirmed requirements?
- For a small request, are there no more than three direct questions?
- For a broad request, is there a grouped confirmation checklist instead of an
  interrogation?
- Does the response avoid named downstream-skill requirements unless the user
  supplied the name as context?
- Does `Ready for planning`, `Conditional for planning`, or
  `Not ready for planning` match the unresolved decisions?
