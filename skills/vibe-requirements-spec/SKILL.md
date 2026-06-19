---
version: 2.0.0
name: vibe-requirements-spec
description: Use when a user wants to draft, revise, save, approve, or explicitly explore requirements for a rough, ambiguous, contradictory, creative, non-technical, or underspecified coding goal before implementation planning or coding, including explicit chat-only/no-file requirements exploration.
---

# Vibe Requirements Spec

## Overview

Turn rough coding intent into a Markdown requirements specification artifact
without inventing product behavior, scope, data rules, or success criteria.

This skill is a requirements-spec drafting workflow while active. The normal
write is creating or updating the current requirements spec artifact. Do not
create implementation plans, implementation task entries, code changes, tests,
verification command lists, commits, release work, changelog entries, or
unrelated files while using this skill.

The spec is input to a later implementation-planning phase. Requirements
lifecycle state is workflow evidence, not spec content: record requirements-
finished or next-phase handoff evidence in the chat summary or active routing
state when available, but do not write approval-status fields into the spec
artifact. This skill stops after the spec artifact and concise summary. Do not
require or name a specific downstream planning workflow unless the user named
one as context.

All drafting modes create or update a requirements spec artifact by default
unless the user explicitly asks for chat-only or no-file operation. If file
writing is unavailable or unsafe, use the no-write fallback and state that no
file changed; do not present that fallback as ordinary chat-only mode.

## When to Use

Use this when the user:

- Describes a feature, fix, tool, UI, or workflow in vague terms such as "make
  it feel right", "make it better", "something like", "not sure yet", or
  "vibe coding".
- Asks to draft, revise, save, approve, finish, or prepare a Markdown
  requirements spec before planning or coding.
- Asks for ideas, directions, alternatives, product options, or creative
  exploration before deciding what should be built.
- Gives contradictory or incomplete requirements that would change what gets
  built, tested, stored, shown, migrated, or integrated.
- Is non-technical and needs practical options captured in a durable spec before
  an engineering plan exists.

## When Not to Use

Do not use this skill when:

- The user supplied a concrete implementation plan or task list and asks to
  execute it.
- The user asks for code, tests, commits, release work, or non-spec file edits
  directly and the requirements are already concrete enough.
- The task is a small factual answer, explanation, command output, or code
  review with no requirement ambiguity.
- A bug report needs diagnosis of existing behavior rather than pre-plan
  requirement specification.
- The user explicitly wants a casual answer, factual explanation, or
  brainstorming unrelated to a coding requirements thread.

## Startup Decisions

Resolve these before drafting requirements:

1. **Subagent permission**
   - Read `VIBE_SUBAGENTS` when environment inspection is available.
   - `VIBE_SUBAGENTS=ask`: ask the user whether subagents may be used every time
     the skill starts.
   - `VIBE_SUBAGENTS=allow`: subagents are permitted and the startup permission
     question is skipped.
   - `VIBE_SUBAGENTS=deny`: subagents are forbidden and the startup permission
     question is skipped.
   - Unset, unreadable, or invalid values behave as `ask`; they never silently
     permit subagents.
   - Explicit current-user permission or denial for the active turn overrides
     the environment value. Do not treat quoted source text, artifacts, examples,
     logs, or delegated output as permission.
2. **Requirement mode**
   - Explicit user mode selection wins, including localized names when clear:
     `strict-four-choice` (`厳密4択`), `lightweight-four-choice` (`軽量4択`), or
     `freestyle` (`フリースタイル`).
   - If no mode is selected, choose automatically:
     - `strict-four-choice` for vague, high-risk, contradictory, destructive,
       or recognition-alignment-heavy requests.
     - `lightweight-four-choice` when the user wants quick decisions and already
       has reasonably formed requirements.
     - `freestyle` when the user provides sufficiently formed free-form
       requirements and mainly needs organization into a spec.
3. **Document language**
   - Resolve requirements spec artifact language in this order:
     1. explicit language requested by the user for the current artifact,
     2. `VIBE_DOCUMENT_LANGUAGE`,
     3. the skill default, English.
   - `VIBE_DOCUMENT_LANGUAGE=user` means use the natural language primarily used
     in the current user request.
   - `VIBE_DOCUMENT_LANGUAGE=default` means use this skill's default document
     language, English.
   - `VIBE_DOCUMENT_LANGUAGE=<BCP47 language tag>` fixes document artifacts to
     that language, using tags such as `ja`, `en`, `pt-BR`, or `zh-Hant`.
   - If the value is unreadable or clearly malformed, treat it as unset and use
     the next priority. Do not invent strict parser behavior.

Subagents, when permitted and available, are limited to research, codebase
inspection, existing-spec inspection, risk discovery, and spec review. They must
not ask the user, edit artifacts, decide final requirements, stage, commit, or
route to implementation. The main AI remains responsible for final judgment and
requirements updates.

If the user asks to skip the subagent permission question next time, handle that
as a narrow configuration-assistance branch, not as normal spec drafting:

- Inspect the user's environment enough to identify the active shell and the
  most suitable shell configuration target.
- Show the target file, exact proposed change, and practical risks, including
  persistent behavior, conflicting existing settings, shell mismatch, and any
  write outside the current workspace.
- Ask for final confirmation before editing any shell configuration file.
- Obey host filesystem permissions and approval requirements. If the target is
  unknown, conflicting, non-writable, outside permitted access, or host approval
  is missing, stop and report the safest next action.
- Never edit shell configuration silently, and never treat the shell-config edit
  as a requirements spec artifact write.

## Core Rules

- Keep the active artifact to one requirements spec unless the user explicitly
  cancels it or replaces it with a new spec effort.
- Keep the skill active for related requirement-spec work until the user gives
  an explicit requirements-finished phrase, gives a clear next-phase instruction,
  explicitly cancels the drafting effort, or explicitly replaces it.
- Requirements-finished or handoff phrases include wording such as "end
  requirements definition", "finalize these requirements", "create an
  implementation plan", "use this spec for planning", or "implement this".
- Treat ambiguous positive replies such as "OK", "looks good", "ready",
  "continue", and "go ahead" as continued drafting unless the surrounding text
  clearly finishes requirements or asks for the next phase.
- If the user changes requirements after a requirements-finished or handoff
  signal, update the same spec by replacing superseded requirement text and
  related acceptance criteria, decisions, assumptions, defaults, and risks. The
  earlier finish or handoff evidence no longer applies to the revised spec.
- Separate confirmed requirements, proposed defaults, candidate options,
  decisions, assumptions, out-of-scope items, acceptance criteria, evidence, and
  open unknowns.
- Use brainstorming only to produce candidate options. Do not treat an idea as
  a confirmed requirement until the user chooses it or explicitly confirms it.
- Do read-only research when correctness or feasibility affects the
  requirements and the user has provided access or asked for that evidence.
  Relevant sources include local files, existing specs, official documentation,
  primary sources, and user-provided source material.
- Do not run tests, builds, migrations, destructive commands, or other
  implementation verification while this skill is active. If needed facts cannot
  be checked safely, record them as unverified in the spec.
- If the user explicitly requests chat-only or no-file operation, do not write a
  spec artifact. Keep the discussion structured enough to preserve the exact
  next action needed to create or update a spec later.

## Spec Path Rules

Choose and preserve the spec path in this order:

1. Use a user-specified path when one is provided.
2. Reuse the current spec path when it appears in the conversation or existing
   spec artifact, including historical paths under `specs/`.
3. Otherwise create `docs/specs/YYYY-MM-DD-<goal-slug>-spec.md` at the workspace
   root, using the current local date and a short lowercase slug.

This change is forward-looking. Existing files under `specs/` remain in place
as historical artifacts and must not be migrated only because this skill now
defaults new requirements specs to `docs/specs/`.

Before writing, read an existing target path when possible. If the path contains
the current spec, update it in place. If it contains unrelated content, do not
overwrite it; ask for a different path or explicit replacement instruction. If
the user asks for a new spec and the default path would collide, choose a clear
non-conflicting suffix such as `-2` only when the old file is unrelated and the
new path is shown in the summary.

When the user provides new information for an existing spec, update the same
file instead of creating a new unrelated spec. Replace stale requirements,
defaults, decisions, assumptions, acceptance criteria, evidence, and risks with
the new decided content. Do not append dated revision history inside the spec
artifact.

If file writing is unavailable, unsafe, or declined, do not simulate a file
write. If the user requested a spec artifact, return the complete spec in chat,
state the intended path or path-selection blocker, and say no file was changed.
If the user explicitly requested chat-only exploration, return options or
decisions in chat without assigning a new spec path.

## Spec Template

Use the template below as authoritative. Do not copy older templates that
include `Approval state`, approval-status fields, `Approval note`, `Revision
notes`, or dated change-history entries. Use stable English section headings and
English generated prose unless the user or `VIBE_DOCUMENT_LANGUAGE` selects a
different artifact language. Preserve user-authored requirement wording,
product names, domain terms, paths, API names, commands, identifiers, and quoted
text in the original language where useful, with the artifact language's
operational wording alongside them when needed.

Before writing a spec artifact, scan the artifact body for old-template
approval or revision strings. If any of the following appear, rewrite the
artifact before saving it: `## Approval state`, `Approval state:`,
`Status: Draft`, `Status: Awaiting explicit approval`, `Status: Approved`,
`Status: Reopened after approval`, `Approval note`, `## Revision notes`, and
`Revision notes:`. Use `## Spec metadata` only for current artifact metadata.
Put requirements-finished evidence, missing finish actions, next-phase handoff
evidence, and revision context in the chat summary or workflow state, not in the
spec file.

When updating an existing legacy spec that already contains approval-status or
revision-history sections, migrate it to the current template in the same write:
remove the legacy approval section, approval note, status fields, revision
notes, and dated change-history entries from the saved artifact. Preserve the
current path, last-updated date, and current requirement contract in `## Spec
metadata` and the body; mention prior lifecycle context only in the chat summary
when it is useful.

```markdown
# [Goal or Feature Name] Requirements Spec

## Spec metadata
- Current spec path: [path]
- Last updated: YYYY-MM-DD
- Requirement mode: strict-four-choice|lightweight-four-choice|freestyle

## User goal

## Evidence and constraints

### Local evidence

### External evidence

### Unverified facts

## Current requirements

### Confirmed requirements

### Proposed defaults

### Ideas or options

### Decisions needed

### Assumptions

### Out of scope

## Acceptance criteria

## Open risks and unknowns
```

`Evidence and constraints` records only evidence that affects requirement
decisions. For local evidence, include paths. For external evidence, include
source names or URLs. For unknowns, mark the fact unverified instead of
adopting it as confirmed.

For broad unclear requests, use a grouped confirmation checklist inside
`Decisions needed`:

```markdown
### Decisions needed

#### Blocking decisions
- [ ] Decisions that change the first buildable scope.

#### Can default
- [ ] Defaults for confirmed scope or cross-cutting choices that stay valid
      regardless of optional-surface selection.

#### Later decisions
- [ ] Items that can wait because they do not affect the first useful slice.
```

## Drafting Modes

### `strict-four-choice`

Use `strict-four-choice` for vague, high-risk, contradictory, destructive, or
recognition-alignment-heavy requests. Ask one visible requirements decision
question per turn and continue for as many turns as needed to protect the
requirement contract. Startup permission questions, such as subagent permission,
do not count as the requirements decision question, but keep them separate and
brief.

Each question presents three or four labeled options. Use four options when four
natural, high-quality choices exist; use three when a fourth would be filler.
Each option states the requirement that would be adopted, benefits, drawbacks,
and risks or assumptions. Include one mildly challenging option by default, and
state its risk, assumptions, and adoption conditions.

### `lightweight-four-choice`

Use `lightweight-four-choice` when the user wants quick decisions and already
has reasonably formed requirements. Ask one visible question per turn for the
main requirement dimensions, normally for up to roughly three main questions.
Record lower-impact details as AI-recommended defaults, assumptions, or open
unknowns instead of turning every detail into a question.

Each question presents three or four labeled options when option selection helps
the user decide. Each option states the requirement that would be adopted, the
main benefit, and the main drawback.

### `freestyle`

Use `freestyle` when the user provides sufficiently formed free-form
requirements. Organize the supplied requirements into the spec with minimal
follow-up questions. Stop before adopting a requirement when the user's input
contains a factual error, feasibility risk, destructive-change risk, or a
significant break from an existing specification, API, data contract, workflow,
safety property, or skill integration.

When stopping for risk or false facts, clearly say what is wrong or risky, cite
the evidence or mark it unverified, explain the requirement impact, and propose
alternatives close to the user's goal. If the only requested change depends on a
false or contradicted premise, leave the current spec unchanged unless there is
confirmed unaffected content to update, and state that the saved spec was not
changed while waiting for user confirmation.

Do not convert supplied product requirements into implementation details such as
schema fields, API endpoints, UI component names, storage representation,
client/server validation placement, test cases, or framework choices unless the
user supplied them or local evidence proves they are existing constraints.
Record such details as open implementation evidence needs, assumptions, or leave
them out of the requirements spec.

### Free-Form Answers

If the user answers freely instead of selecting a numbered option, respect the
free-form answer. Map it to the nearest option only when useful, preserve the
user's difference from that option, and ask one follow-up question only when
needed.

## Drafting Workflow

0. **Resolve startup decisions**
   - Apply `Startup Decisions` before selecting a drafting path.
   - Record the selected `Requirement mode` in `Spec metadata`.
   - If subagents are not permitted, continue without them.
   - If environment values cannot be inspected, treat `VIBE_SUBAGENTS` and
     `VIBE_DOCUMENT_LANGUAGE` as unset.

1. **Choose artifact, no-write fallback, or explicit chat-only**
   - If the user asked only to record a requirements-finished or next-phase
     handoff for an existing current spec, use lifecycle-summary mode: preserve
     the current spec path, record the evidence in the response or active
     routing state, and do not rewrite the spec solely to store lifecycle
     evidence.
   - If the user explicitly says chat only, no file, do not write, or equivalent,
     use explicit chat-only mode.
   - Otherwise proceed with artifact mode, including for ideas, directions,
     exploration, clarification, questions, tradeoffs, decision lists,
     underspecified coding requests, and requests to plan or implement from an
     underspecified goal.
   - If file writing is unavailable or unsafe, use the no-write fallback in
     `Spec Path Rules` and state that no file changed.

2. **Capture the user's intent**
   - Preserve the user's wording for goals, product terms, audience, examples,
     and constraints.
   - Translate vague terms into observable behavior only when the user supplied
     enough context or confirmed an option.
   - Mark inferred behavior as an assumption or proposed default, not as a
     confirmed requirement.

3. **Select or reuse the spec path**
   - Apply the path rules before writing.
   - If a current spec exists, read it and revise that artifact.
   - Do not silently fork a second spec for the same requirement thread.

4. **Classify the requirement surface**
   - `Confirmed requirements`: behavior explicitly stated by the user.
   - `Proposed defaults`: choices that can be safely proposed with low impact or
     lower-impact details the active mode intentionally defaults.
   - `Ideas or options`: candidate directions needing user selection.
   - `Decisions needed`: choices that change behavior, data, permissions, cost,
     user experience, compatibility, verification, safety, or integration.
   - `Assumptions`: inferred behavior that needs user confirmation or later
     proof.
   - `Out of scope`: adjacent capabilities or polish outside the first useful
     slice.
   - `Evidence and constraints`: decision-affecting local evidence, external
     evidence, and unverified facts.
   - `Open risks and unknowns`: facts needing local evidence, primary-source
     evidence, or user input before implementation planning.
   - Classify every build-changing dimension the user names or implies.
   - When the skill relies on evidence for requirement correctness or
     feasibility, record the source in `Evidence and constraints`; if required
     research cannot be done, mark the fact unverified.

5. **Protect high-impact requirement surfaces**
   - For billing, permissions, security, account settings, recipient, or routing
     changes, include auditability as a requirement dimension: whether changes
     are recorded, attributable, retained, or visible.
   - For billing, permissions, security, account settings, recipient, or routing
     changes, mark permission, recipient, and auditability choices as blocking
     or high-impact when they can change access, recipients, compliance, account
     safety, or billing outcomes.
   - For billing, account-setting, recipient, or routing changes, clarify who can
     make the change, who or what can be targeted, validation or verification
     rules, whether future sends or prior records are affected, and
     auditability. In explicit chat-only mode, cover lower-priority dimensions as
     proposed defaults, open assumptions, or unknowns instead of turning them all
     into direct questions.
   - For invoice or billing-email recipient changes, explicitly cover the
     delivery-effect window: whether saved recipient changes affect the next
     invoice only, already-generated but unsent invoices, retries or reminders,
     future billing-cycle emails, and whether added or removed recipients are
     notified. Treat this as a requirement dimension, proposed default, or
     blocking/high-impact unknown.
   - In invoice or billing-email recipient clarification, the delivery-effect
     window is one of the highest-impact dimensions. In `lightweight-four-choice`
     combine edit permissions, target eligibility, and validation into one main
     question if needed; do not let recipient count, minimum-list behavior, or
     auditability consume every direct question while delivery consequences
     disappear. Cover lower-priority dimensions as proposed defaults,
     assumptions, or open unknowns.
   - For notification or messaging channels such as email, SMS, and push,
     surface channel-specific product uncertainties such as consent or
     permission, opt-in or opt-out behavior, provider setup, cost, and
     compliance before treating channels as interchangeable. Do not invent
     provider facts.
   - For bulk data creation, imports, migrations, destructive changes, and
     irreversible writes, classify write-safety decisions before requirements
     finish: review-before-write or preview, partial-failure behavior, duplicate
     or conflict handling, permissions, persistence, and rollback or recovery.
     Do not bury review-before-write or preview inside duplicate handling,
     partial-failure handling, or a post-write result summary; record it as its
     own write-safety decision, proposed default, out-of-scope item, or open
     unknown.
   - For mutually exclusive data migration, storage, compatibility, or
     destructive-write constraints, list viable interpretation or resolution
     choices as options or blocking decisions, and state the user-visible or
     data-safety consequence of each. Examples include copy-on-read, one-time
     migration, dual reader, or no migration. Do not choose one without user
     confirmation, and do not hide the choice behind clarifying questions alone.
   - A post-write result summary is not a substitute for pre-write preview
     behavior.
   - When the user names admin screens, delivery logs, reporting, audit views,
     diagnostics, frequency controls, or similar adjacent surfaces as merely
     useful or possible, keep their storage, retention, search, viewer,
     per-event record shape, and staff-facing behavior out of `Can default`,
     `Proposed defaults`, and `Acceptance criteria` until selected.
   - Do not turn an unselected delivery-log surface into a "safe default" by
     requiring structured per-send records, timestamp/user/channel/outcome log
     entries, retention policy, queryability, or standard logging emission for
     the first slice. Put that behavior in `Decisions needed`, `Open risks and
     unknowns`, or `Later decisions`.

6. **Use brainstorming only when it helps**
   - Brainstorm when the user asks for ideas, creative directions, or multiple
     possible product shapes.
   - Offer two to five options, never more than five.
   - Count merged or hybrid ideas as separate options if they can be chosen
     independently.
   - For each option, include when it fits, the main tradeoff, and what
     requirement would be adopted if chosen.
   - Keep high-impact choices conservative. Creative appeal is not evidence that
     risky behavior is acceptable.
   - Keep unchosen ideas in `Ideas or options`.

7. **Write or update the spec artifact**
   - Update artifacts at meaningful points, not mechanically after every answer:
     after important decisions, when context compaction appears near and the
     agent can tell, or after a reasonable batch of lower-impact decisions
     accumulates.
   - Put only confirmed first-slice behavior in `Confirmed requirements`.
   - Keep adjacent capabilities in `Out of scope`, `Decisions needed`, or
     `Ideas or options` until the user selects them.
   - Use `Can default` only for confirmed scope or cross-cutting choices that
     stay valid regardless of optional-surface selection.
   - Do not pre-stage admin, reporting, audit views, diagnostic views,
     delivery-log storage, retention, search, or other adjacent surfaces in
     `Can default` with "if chosen", "once selected", or similar gating.
   - For notification, messaging, import, billing, account, or permission
     surfaces, do not include structured delivery, attempt, audit-log, or
     operational record storage in first-slice defaults only because it seems
     prudent. It becomes a requirement only when the user selected that surface
     or the spec records it as a blocking decision to finish.
   - This does not remove auditability as a requirement dimension. For billing,
     permission, security, account-setting, recipient, or routing changes,
     record whether auditability is required, deferred, or a user decision.
   - If a default starts with "within whichever optional surface you select",
     move it to that surface's blocking decision or candidate option.
   - When revising an existing spec, remove or rewrite superseded requirements,
     defaults, decisions, assumptions, acceptance criteria, evidence, and risks
     instead of preserving stale content as dated change history.
   - Do not add `Approval state`, approval-status fields or values such as
     `Status: Draft`, `Status: Awaiting explicit approval`, `Status: Approved`,
     `Status: Reopened after approval`, `Approval note`, `Revision notes`, or
     equivalent approval or revision-history sections to new or rewritten spec
     artifacts.

8. **Track requirements lifecycle evidence outside the spec**
   - Treat requirements-finished and next-phase handoff evidence as workflow
     lifecycle evidence, not artifact content.
   - Explicit finish or handoff evidence includes wording tied to the current
     requirements, such as "finalize these requirements", "end requirements
     definition", "仕様を確定", "use this spec for planning", "create an
     implementation plan from this spec", or "implement this".
   - When a requirement changes after finish or handoff evidence, the prior
     evidence no longer applies to the revised requirement contract. Keep
     drafting active until renewed explicit finish evidence or another
     unambiguous current-spec next-phase handoff.
   - Ambiguous "OK", "looks good", "ready", "continue", or "go ahead" wording
     does not finish requirements unless the surrounding text clearly says the
     current requirements are finished or asks for the next phase.

9. **Return a concise localized summary**
   - Use the user's language for the chat response unless they ask otherwise.
   - In artifact mode, include the spec path, current requirements-finished or
     handoff evidence when available, the exact finish or next action still
     needed, blocking decisions or unknowns, and the exact user action needed
     next.
   - If build-changing local evidence checks remain open, name them in the
     summary alongside user decisions under an explicit label such as `Local
     evidence still needed`; do not imply user answers alone make the spec final
     when existing schemas, validation rules, limits, permissions, or persistence
     still need evidence.
   - In explicit chat-only mode, state that no spec file was written and name the
     exact user action that would create or update one.
   - In lifecycle-summary mode, include the current spec path, the
     requirements-finished or next-phase handoff evidence, whether the saved spec
     was left unchanged, and the exact later-phase action. Do not create an
     implementation plan in the same response.
   - In lifecycle-summary mode, phrase the later action generically, such as "a
     later implementation-planning phase can use this spec." Do not tell the
     user to invoke, run, start, or route to a workflow, tool, skill, or named
     planning process.
   - In explicit chat-only clarification for high-impact surfaces, keep the
     response structured enough to separate confirmed intent, blocking or
     high-impact decisions, proposed defaults or assumptions, open risks or
     unknowns, and the exact action that would save a spec.
   - If explicit chat-only mode used an existing spec artifact as context,
     preserve the current spec path as unchanged context. If a legacy artifact
     contains approval state, mention it only as legacy context and do not update
     it from brainstorming alone.
   - Stop after the spec summary.
   - If the user explicitly finished requirements or gave an unambiguous
     current-spec next-phase handoff and also asked to plan or implement, state
     that lifecycle evidence is available for a later implementation-planning
     phase. Do not create that plan or implement in the same skill response.

## Requirements Lifecycle

This skill remains active across related turns until one of these happens:

- The user gives an explicit requirements-finished phrase for the current spec.
- The user gives an unambiguous instruction to create or use an implementation
  plan from the current spec.
- The user gives an unambiguous instruction to implement from the current spec.
- The user explicitly cancels the spec drafting effort.
- The user explicitly replaces it with a different spec effort.

No amount of internal confidence, absence of open questions, completed
checklists, or ambiguous positive wording ends requirements drafting by itself.
If the next user turn adds requirements, edits decisions, changes scope, or
responds ambiguously, keep updating the same spec and require explicit
requirements-finished or next-phase handoff evidence before later implementation
planning.

Requirements with finish or next-phase handoff evidence are stable input to a
later implementation-planning phase. They do not authorize same-turn
implementation planning, code edits, tests, verification commands, commits,
release work, changelog edits, or unrelated file edits while this skill is
active.

## Common Mistakes

- Creating a new spec when the current conversation already has a spec path.
- Treating clarification, ideation, tradeoff, or decision-list requests as
  no-file work when the user did not explicitly request chat-only or no-file
  operation.
- Writing a spec file after the user explicitly requested chat-only or no-file
  operation.
- Treating a file-unavailable or unsafe-write fallback as ordinary chat-only
  mode instead of saying no file changed.
- Treating "what do we need to decide?", "help me clarify", or similar
  clarification wording as a reason to avoid the default spec artifact.
- Applying the old global small-request question limit instead of selecting
  `strict-four-choice`, `lightweight-four-choice`, or `freestyle`.
- In `strict-four-choice`, asking multiple requirements decision questions in
  one turn or omitting the mildly challenging option with risk, assumptions, and
  adoption conditions.
- In `lightweight-four-choice`, asking every lower-impact detail instead of
  recording AI-recommended defaults.
- In `freestyle`, adopting a false, infeasible, destructive, or
  specification-breaking requirement without confirmation.
- In `freestyle`, turning supplied product requirements into schema fields,
  endpoint names, UI component names, client/server validation placement, tests,
  or other implementation details without user input or local evidence.
- Treating "OK", "looks good", or "go ahead" as requirements-finished evidence
  without clear finish or next-phase wording.
- Copying an old requirements-spec template with `Approval state`, `Approval
  note`, or `Revision notes` sections.
- Writing approval-status fields, approval notes, lifecycle status fields, or
  revision-history sections into the requirements spec artifact.
- Preserving legacy `Approval state`, `Approval note`, or `Revision notes`
  sections when updating an existing spec artifact.
- Appending dated change notes instead of replacing superseded requirement
  content.
- Writing an implementation plan, task breakdown, verification command
  sequence, patch outline, commit checklist, or release note inside the spec.
- Editing README, changelog, tests, source code, or other repository files as
  part of normal spec drafting.
- Editing shell configuration to persist `VIBE_SUBAGENTS` before showing the
  target file, exact change, risks, and receiving final confirmation.
- Treating subagent output as final requirements instead of research or review
  input owned by the main AI.
- Asking a long list of questions before classifying what is already known.
- Listing options for a mode question without explaining the adopted
  requirement and required tradeoffs for that mode.
- Saying a default is proposed below, then asking the user to supply all values.
- Putting unconfirmed adjacent capabilities in confirmed requirements with a
  "subject to confirmation" qualifier.
- Putting unconfirmed adjacent capabilities in `Can default` so they become
  staged or automatic first-slice scope.
- Adding structured per-send delivery logs, timestamp/user/channel/outcome
  records, audit-log storage, retention, search, or staff visibility as a
  first-slice default when delivery logs or audit views were only named as
  possible adjacent surfaces.
- Treating an audit-log UI exclusion as enough auditability coverage for
  billing, permission, account-setting, recipient, or routing changes.
- Treating a proposed default as a confirmed user requirement.
- Treating brainstormed ideas as requirements before the user chooses one.
- Offering more than five brainstorming options because the ideas are distinct.
- Treating a post-write import summary, duplicate-handling branch, or
  partial-failure branch as equivalent to review-before-write or preview.
- Expanding into adjacent features just because they are common in similar
  products.
- Treating mutually exclusive requirements as merely waiting for finish wording.
- Turning mutually exclusive migration or compatibility constraints into
  clarifying questions without listing viable interpretations and consequences.
- Leaving rollback or recovery expectations as ordinary risks when the work
  depends on safety, invisibility, compatibility, or destructive-change
  recovery.
- Naming or requiring a specific downstream planning skill or workflow.
- Using imperative workflow routing such as "invoke an implementation-planning
  workflow" instead of a generic later implementation-planning phase handoff.

## Self-Check

Before responding, check:

- Did startup resolve `VIBE_SUBAGENTS`, requirement mode, and document language,
  or explicitly treat them as unset because they could not be inspected?
- Is `Requirement mode` recorded in `Spec metadata` when artifact mode applies?
- In artifact mode, did you create or update only the requirements spec
  artifact?
- In artifact mode, does the spec use the selected document language while
  preserving useful user-authored original wording, identifiers, paths,
  commands, and quoted text?
- In artifact mode, does the spec include `Evidence and constraints` with only
  decision-affecting evidence, paths, source names or URLs, and unverified facts?
- In artifact mode, does the spec omit `Approval state`, approval-status fields
  or values such as `Status: Draft`, `Status: Awaiting explicit approval`,
  `Status: Approved`, `Status: Reopened after approval`, `Approval note`,
  `Revision notes`, and equivalent approval or revision-history sections?
- When updating a legacy spec artifact, did you remove old approval-status and
  revision-history sections from the saved artifact instead of preserving or
  updating them?
- Did you use `docs/specs/YYYY-MM-DD-<goal-slug>-spec.md` for a new default spec
  path when no user path or current path applied?
- Did you avoid migrating existing historical files under `specs/`?
- Are confirmed requirements, proposed defaults, options, decisions,
  assumptions, out-of-scope items, acceptance criteria, evidence, and unknowns
  separated?
- If requirements-finished or next-phase handoff evidence is available, is it
  tied to the current spec rather than an artifact status field?
- In artifact mode, if requirements changed after finish or handoff evidence,
  did you replace superseded spec content and require renewed finish or handoff
  evidence?
- If brainstorming was used, are ideas clearly marked as options rather than
  confirmed requirements, and are there two to five options?
- Did every build-changing dimension named or implied by the user appear in one
  spec section?
- If a user claim was false, did you say it was wrong, cite evidence and impact,
  and propose close alternatives instead of adopting it?
- If a requested requirement could significantly break an existing spec, API,
  data contract, workflow, safety property, or skill integration, did you show
  concrete risks and ask whether it should really be included?
- For billing, permission, security, account-setting, recipient, or routing
  changes, did you address auditability as requirement behavior?
- For bulk data writes or imports, did you account for review-before-write or
  preview as its own write-safety dimension, plus partial failure, duplicate or
  conflict handling, permissions, persistence, and rollback or recovery?
- For mutually exclusive data migration, storage, compatibility, or
  destructive-write constraints, did you list viable interpretations or
  resolution choices and state the user-visible or data-safety consequence of
  each without selecting one?
- For `strict-four-choice`, is there one visible requirements decision question,
  three or four labeled options, and one mildly challenging option with risk,
  assumptions, and adoption conditions?
- For `lightweight-four-choice`, is there one visible main question and are
  lower-impact details recorded as AI-recommended defaults, assumptions, or
  unknowns?
- For `freestyle`, are follow-up questions minimal, with false facts,
  feasibility risks, destructive risks, and specification breaks confirmed
  before adoption?
- If the user answered freely, did you preserve the free-form answer and ask
  only one follow-up question when needed?
- For a broad request, is there a grouped confirmation checklist instead of an
  interrogation?
- Are `Can default` items limited to confirmed scope or cross-cutting choices
  that stay valid regardless of optional-surface selection?
- If delivery logs, admin views, reporting, audit views, diagnostics, or
  frequency controls were only named as useful, did you keep their record shape,
  storage, retention, queryability, and viewer behavior out of defaults and
  acceptance criteria?
- For billing, permission, security, account-setting, recipient, or routing
  changes, did you still classify auditability as required, deferred, or a user
  decision?
- For billing, permission, security, account-setting, recipient, or routing
  changes, did you mark permission, recipient, and auditability choices as
  blocking or high-impact when they affect access, compliance, account safety,
  or billing outcomes?
- For billing, account-setting, recipient, or routing changes, did you cover edit
  permissions, target eligibility, validation or verification, future-send
  consequences, and auditability as requirements, decisions, defaults, or
  unknowns?
- For invoice or billing-email recipient changes, did you explicitly cover the
  delivery-effect window for the next invoice, already-generated unsent invoices,
  retries or reminders, future billing-cycle emails, and added or removed
  recipient notifications as a requirement, proposed default, or unknown?
- For invoice or billing-email recipient clarification, did delivery-effect
  coverage survive the active mode's question cadence rather than being displaced
  by recipient count, minimum-list behavior, or auditability questions?
- For notification or messaging channels such as email, SMS, and push, did you
  surface channel-specific product uncertainties without inventing provider
  facts?
- In artifact mode, does the chat summary include the spec path, finish or
  handoff evidence when present, blockers or unknowns, and exact next user
  action?
- If build-changing local evidence checks remain open, does the summary name
  them under a clear `Local evidence still needed`-style label alongside user
  decisions instead of presenting user replies as the only remaining gate?
- In explicit chat-only mode, does the response state that no spec file was
  written and name the exact next user action for artifact drafting or lifecycle
  handoff?
- In explicit chat-only mode with an existing spec artifact, did you preserve the
  current spec path as unchanged context and avoid changing any legacy approval
  state from brainstorming alone?
- Does the response stop after the spec artifact and summary, after the
  explicit chat-only exploration response, or after lifecycle-summary mode, even
  if the user said to go ahead or the next phase seems obvious?
- In lifecycle-summary mode, is the next action a generic later planning-phase
  handoff rather than an instruction to invoke, run, start, or route to a
  workflow, tool, skill, or named planning process?
