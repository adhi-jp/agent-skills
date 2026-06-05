---
version: 1.0.0
name: vibe-requirements-spec
description: Use when a user wants to draft, revise, save, approve, or explicitly explore requirements for a rough, ambiguous, contradictory, creative, non-technical, or underspecified coding goal before implementation planning or coding, including chat-only requirements exploration.
---

# Vibe Requirements Spec

## Overview

Turn rough coding intent into a Markdown requirements specification artifact
without inventing product behavior, scope, data rules, or success criteria.

This skill is a requirements-spec drafting workflow while active. The only
allowed write is creating or updating the current requirements spec artifact.
Do not create implementation plans, implementation task entries, code changes,
tests, verification command lists, commits, release work, changelog entries, or
unrelated files while using this skill.

The spec is input to a later implementation-planning phase. Approval is workflow
evidence, not spec content: record it in the chat summary or active routing
state when available, but do not write approval-status fields into the spec
artifact. This skill stops after the spec artifact and concise summary. Do not
require or name a specific downstream planning workflow unless the user named
one as context.

Using this skill does not by itself authorize file writing. If the requested
deliverable is only a decision list, clarification, questions, tradeoffs,
brainstorming, comparison, or exploration, answer in chat only or ask a narrow
confirmation before writing. Wording such as "what do we need to decide?",
"help me clarify", or "before planning/tooling gets involved" is chat-only
unless the user also asks to draft, save, update, approve, finalize, plan, code,
or implement from the current requirements. If the user declines file writing,
preserve the discussion as options and the exact next action needed to create or
update a spec later.

## When to Use

Use this when the user:

- Describes a feature, fix, tool, UI, or workflow in vague terms such as "make
  it feel right", "make it better", "something like", "not sure yet", or
  "vibe coding".
- Asks to draft, revise, save, approve, or prepare a Markdown requirements
  spec before planning or coding.
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

## Core Rules

- Keep the active artifact to one requirements spec unless the user explicitly
  cancels it or replaces it with a new spec effort.
- Keep the skill active for related requirement-spec work until the user
  explicitly approves the current spec, explicitly cancels the drafting effort,
  explicitly replaces it, or gives an unambiguous instruction to create or use
  an implementation plan from the current spec.
- Treat vague readiness wording, completed checklists, no open questions,
  "looks good", "ready", "continue", "go ahead", and similar handoff phrases
  as continued drafting unless they clearly approve the current spec artifact.
- If the user changes requirements after approval, update the same spec by
  replacing superseded requirement text and related acceptance criteria,
  decisions, assumptions, defaults, and risks. The earlier approval evidence no
  longer applies to the revised spec, and the revised spec needs renewed
  explicit approval before implementation planning.
- Separate confirmed requirements, proposed defaults, candidate options,
  decisions, assumptions, out-of-scope items, acceptance criteria, and open
  unknowns.
- Use brainstorming only to produce candidate options. Do not treat an idea as
  a confirmed requirement until the user chooses it or explicitly approves it.
- Do not run verification commands while this skill is active. Evidence checks
  that affect requirements should be recorded as open unknowns or user decisions
  for a later phase unless the user explicitly asked this skill to inspect
  already-provided source material for the spec.
- Do not write a new spec artifact for chat-only exploration unless the user
  asks to save the result or confirms that a spec file should be created.

## Spec Path Rules

Choose and preserve the spec path in this order:

1. Use a user-specified path when one is provided.
2. Reuse the current spec path when it appears in the conversation or existing
   spec artifact.
3. Follow an obvious repository convention such as `specs/` or `docs/specs/`
   when it already exists.
4. Otherwise create `specs/YYYY-MM-DD-<goal-slug>-spec.md` at the workspace
   root, using the current local date and a short lowercase slug.

Before writing, read an existing target path when possible. If the path contains
the current spec, update it in place. If it contains unrelated content, do not
overwrite it; ask for a different path or explicit replacement instruction. If
the user asks for a new spec and the default path would collide, choose a clear
non-conflicting suffix such as `-2` only when the old file is unrelated and the
new path is shown in the summary.

When the user provides new information for an existing spec, update the same
file instead of creating a new unrelated spec. Replace stale requirements,
defaults, decisions, assumptions, acceptance criteria, and risks with the new
decided content. Do not append dated revision history inside the spec artifact.

If file writing is unavailable, unsafe, or declined, do not simulate a file
write. If the user requested a spec artifact, return the complete spec in chat,
state the intended path or path-selection blocker, and say no file was changed.
If the user requested chat-only exploration, return options or decisions in
chat without assigning a spec path.

## Spec Template

Use the template below as authoritative. Do not copy older templates that
include `Approval state`, approval-status fields, `Approval note`, `Revision
notes`, or dated change-history entries. Use stable English section headings and
English generated prose unless the user explicitly requested a different
artifact language. Preserve user-authored requirement wording, product names,
domain terms, paths, API names, commands, identifiers, and quoted text in the
original language where useful, with English operational wording alongside them
when needed.

Before writing a spec artifact, scan the artifact body for old-template
approval or revision strings. If any of the following appear, rewrite the
artifact before saving it: `## Approval state`, `Approval state:`,
`Status: Draft`, `Status: Awaiting explicit approval`, `Status: Approved`,
`Status: Reopened after approval`, `Approval note`, `## Revision notes`, and
`Revision notes:`. Use `## Spec metadata` only for the current path and
last-updated date. Put approval evidence, missing approval actions, and revision
context in the chat summary or workflow state, not in the spec file.

When updating an existing legacy spec that already contains approval-status or
revision-history sections, migrate it to the current template in the same write:
remove the legacy approval section, approval note, status fields, revision notes,
and dated change-history entries from the saved artifact. Preserve the current
path and last-updated date in `## Spec metadata`; mention prior approval or
revision context only in the chat summary when it is useful.

```markdown
# [Goal or Feature Name] Requirements Spec

## Spec metadata
- Current spec path: [path]
- Last updated: YYYY-MM-DD

## User goal

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

## Drafting Workflow

0. **Choose artifact or chat-only mode**
   - If the user asked only to approve an existing current spec, or gave an
     unambiguous instruction to create or use an implementation plan from the
     current spec, use approval-evidence summary mode: preserve the current spec
     path, record approval evidence in the response or active routing state, and
     do not rewrite the spec solely to store approval evidence.
   - If the user asked to draft, save, update, or finalize a requirements spec,
     proceed with artifact mode.
   - If the user asked for code, implementation, planning, or execution from an
     underspecified goal, proceed with artifact mode instead of coding or
     planning.
   - If the user asked only for ideas, directions, exploration, clarification,
     questions, tradeoffs, or a decision list and did not ask for a saved spec,
     use chat-only mode or ask before creating a file.
   - Treat phrases such as "what do we need to decide?" and "help me clarify"
     as chat-only deliverables unless the same request explicitly asks to save,
     draft, update, approve, finalize, plan, code, or implement.
   - If file writing is unavailable, unsafe, or declined, use the fallback in
     `Spec Path Rules` and state that no file was changed.

1. **Capture the user's intent**
   - Preserve the user's wording for goals, product terms, audience, examples,
     and constraints.
   - Translate vague terms into observable behavior only when the user supplied
     enough context.
   - Mark inferred behavior as an assumption or proposed default, not as a
     confirmed requirement.

2. **Select or reuse the spec path**
   - Apply the path rules before writing.
   - If a current spec exists, read it and revise that artifact.
   - Do not silently fork a second spec for the same requirement thread.

3. **Classify the requirement surface**
   - `Confirmed requirements`: behavior explicitly stated by the user.
   - `Proposed defaults`: choices that can be safely proposed with low impact.
   - `Ideas or options`: candidate directions needing user selection.
   - `Decisions needed`: choices that change behavior, data, permissions, cost,
     user experience, compatibility, or verification.
   - `Assumptions`: inferred behavior that needs approval or later proof.
   - `Out of scope`: adjacent capabilities or polish outside the first useful
     slice.
   - `Open risks and unknowns`: facts needing local evidence, primary-source
     evidence, or user input before implementation planning.
   - Classify every build-changing dimension the user names or implies.
   - For billing, permissions, security, account settings, recipient, or routing
     changes, include auditability as a requirement dimension: whether changes
     are recorded, attributable, retained, or visible.
   - For billing, permissions, security, account settings, recipient, or routing
     changes, mark permission, recipient, and auditability choices as blocking
     or high-impact when they can change access, recipients, compliance,
     account safety, or billing outcomes.
   - For billing, account-setting, recipient, or routing changes, clarify who can
     make the change, who or what can be targeted, validation or verification
     rules, whether future sends or prior records are affected, and auditability.
     In chat-only mode, cover lower-priority dimensions as proposed defaults,
     open assumptions, or unknowns instead of turning them all into direct
     questions.
   - For invoice or billing-email recipient changes, explicitly cover the
     delivery-effect window: whether saved recipient changes affect the next
     invoice only, already-generated but unsent invoices, retries or reminders,
     future billing-cycle emails, and whether added or removed recipients are
     notified. Treat this as a requirement dimension, proposed default, or
     blocking/high-impact unknown in chat-only mode.
   - In invoice or billing-email recipient clarification, the delivery-effect
     window is one of the highest-impact dimensions. Under the three-question
     limit, combine edit permissions, target eligibility, and validation into
     one question if needed; do not let recipient count, minimum-list behavior,
     or auditability consume every direct question while delivery consequences
     disappear. Cover any lower-priority dimension as a proposed default,
     assumption, or open unknown.

4. **Choose the question mode**
   - For a small localized request, ask at most three direct questions in the
     chat summary.
   - Pick the highest-impact user decisions and move the rest into proposed
     defaults, assumptions, out-of-scope items, or open unknowns.
   - Do not use long checklists, option groups, or `Decisions needed` to bypass
     the three-question limit for small requests.
   - Defaults should be concrete enough that the user can approve the spec with
     one short reply.
   - If a small request presents interaction, validation, save behavior, or
     feedback options, mark one as the recommended default and give concrete
     values where values matter.
   - The three-question limit constrains direct questions, not requirement
     coverage. For high-impact surfaces such as billing, permissions, account
     settings, recipients, routing, imports, or destructive writes, still cover
     auditability, notification consequences, validation, local-evidence needs,
     and safety dimensions as proposed defaults, blocking/high-impact decisions,
     open assumptions, or unknowns.
   - Use the grouped checklist for broad requests spanning several surfaces,
     domains, high-impact rules, or contradictory goals.
   - For notification or messaging channels such as email, SMS, and push,
     surface channel-specific product uncertainties such as consent or
     permission, opt-in or opt-out behavior, provider setup, cost, and
     compliance before treating channels as interchangeable. Do not invent
     provider facts.
   - For bulk data creation, imports, migrations, destructive changes, and
     irreversible writes, classify write-safety decisions before approval:
     review-before-write or preview, partial-failure behavior, duplicate or
     conflict handling, permissions, persistence, and rollback or recovery.
   - For mutually exclusive data migration, storage, compatibility, or
     destructive-write constraints, list viable interpretation or resolution
     choices as options or blocking decisions, and state the user-visible or
     data-safety consequence of each. Examples include copy-on-read, one-time
     migration, dual reader, or no migration. Do not choose one, and do not hide
     the choice behind clarifying questions alone.
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
     the first slice. Put that behavior in `Decisions needed`,
     `Open risks and unknowns`, or `Later decisions`.

5. **Use brainstorming only when it helps**
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

6. **Write or update the spec artifact**
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
     or the spec records it as a blocking decision to approve.
   - This does not remove auditability as a requirement dimension. For billing,
     permission, security, account-setting, recipient, or routing changes,
     record whether auditability is required, deferred, or a user decision.
   - If a default starts with "within whichever optional surface you select",
     move it to that surface's blocking decision or candidate option.
   - When revising an existing spec, remove or rewrite superseded requirements,
     defaults, decisions, assumptions, acceptance criteria, and risks instead
     of preserving stale content as dated change history.
   - Do not add `Approval state`, approval-status fields or values such as
     `Status: Draft`, `Status: Awaiting explicit approval`, `Status: Approved`,
     `Status: Reopened after approval`, `Approval note`, `Revision notes`, or
     equivalent approval or revision-history sections to new or rewritten spec
     artifacts.

7. **Track approval evidence outside the spec**
   - Treat approval as workflow lifecycle evidence, not artifact content.
   - Explicit approval includes wording tied to the current spec, such as
     "approve this spec", "仕様を承認", "use this spec for planning", "create an
     implementation plan from this spec", or an equivalent current-spec
     planning handoff.
   - When a requirement changes after approval, the prior approval evidence no
     longer applies to the revised requirement contract. Keep drafting active
     until renewed explicit approval or another unambiguous current-spec
     planning handoff.
   - Ambiguous "looks good", "ready", "continue", or "go ahead" wording does
     not approve the current spec unless the surrounding text clearly says the
     spec itself is approved.

8. **Return a concise localized summary**
   - Use the user's language for the chat response unless they ask otherwise.
   - In artifact mode, include the spec path, any current approval evidence or
     the exact approval action still needed, blocking decisions or unknowns, and
     the exact user action needed next.
   - If build-changing local evidence checks remain open, name them in the
     summary alongside user decisions under an explicit label such as `Local
     evidence still needed`; do not imply user answers alone make the spec final
     when existing schemas, validation rules, limits, permissions, or persistence
     still need evidence.
   - In chat-only mode, state that no spec file was written and name the exact
     user action that would create or update one.
   - In approval-evidence summary mode, include the current spec path, the
     approval or current-spec planning-handoff evidence, whether the saved spec
     was left unchanged, and the exact later-phase action. Do not create an
     implementation plan in the same response.
   - In approval-evidence summary mode, phrase the later action generically,
     such as "a later implementation-planning phase can use this spec." Do not
     tell the user to invoke, run, start, or route to a workflow, tool, skill, or
     named planning process.
   - In chat-only clarification for high-impact surfaces, keep the response
     structured enough to separate confirmed intent, blocking or high-impact
     decisions, proposed defaults or assumptions, open risks or unknowns, and the
     exact action that would save a spec. Use no more than three direct
     questions for small requests, but do not omit required dimensions solely to
     stay under that limit.
   - If chat-only mode used an existing spec artifact as context, preserve the
     current spec path as unchanged context. If a legacy artifact contains an
     approval state, mention it only as legacy context and do not update it from
     brainstorming alone.
   - Stop after the spec summary.
   - If the user explicitly approved the spec or gave an unambiguous
     current-spec planning handoff and also asked to plan or implement, state
     that approval evidence is available for a later implementation-planning
     phase. Do not create that plan in the same skill response.

## Approval Lifecycle

This skill remains active across related turns until one of these happens:

- The user explicitly approves the current spec artifact.
- The user gives an unambiguous instruction to create or use an implementation
  plan from the current spec.
- The user explicitly cancels the spec drafting effort.
- The user explicitly replaces it with a different spec effort.

No amount of internal confidence, absence of open questions, completed
checklists, or readiness wording ends the skill by itself. If the next user turn
adds requirements, edits decisions, changes scope, or responds ambiguously, keep
updating the same spec and require explicit approval evidence before later
implementation planning.

Specs with explicit approval evidence are stable input to later implementation
planning. They do not authorize same-turn implementation planning, code edits,
tests, verification commands, commits, release work, changelog edits, or
unrelated file edits while this skill is active.

## Common Mistakes

- Creating a new spec when the current conversation already has a spec path.
- Writing a spec file for chat-only brainstorming when the user did not ask to
  save or approve an artifact.
- Treating "what do we need to decide?", "help me clarify", or similar
  clarification wording as permission to create a saved spec artifact.
- In chat-only clarification, asking three questions and dropping other
  requirement dimensions that should have been captured as defaults, assumptions,
  blocking/high-impact decisions, or unknowns.
- Treating "looks good" or "go ahead" as spec approval without clear approval of
  the current artifact.
- Copying an old requirements-spec template with `Approval state`, `Approval
  note`, or `Revision notes` sections.
- Writing approval-status fields, approval notes, or revision-history sections
  into the requirements spec artifact.
- Preserving legacy `Approval state`, `Approval note`, or `Revision notes`
  sections when updating an existing spec artifact.
- Appending dated change notes instead of replacing superseded requirement
  content.
- Writing an implementation plan, task breakdown, verification command
  sequence, patch outline, commit checklist, or release note inside the spec.
- Editing README, changelog, tests, source code, or other repository files as
  part of normal spec drafting.
- Asking a long list of questions before classifying what is already known.
- Treating `Decisions needed`, checklists, or option groups as a loophole around
  the three-question limit for small localized requests.
- Listing options for a small localized request without marking one recommended
  default.
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
- Treating a post-write import summary as equivalent to review-before-write or
  preview.
- Expanding into adjacent features just because they are common in similar
  products.
- Treating mutually exclusive requirements as merely waiting for approval.
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

- In artifact mode, did you create or update only the requirements spec
  artifact?
- Before artifact mode, did the user ask for a saved spec or for
  code/planning/implementation from underspecified requirements, rather than
  only asking for clarification, questions, tradeoffs, or a decision list?
- In chat-only mode, did you avoid writing a spec artifact and state the next
  action needed to create one?
- In approval-only or current-spec planning-handoff mode, did you avoid
  rewriting the spec solely to record approval evidence?
- In artifact mode, did you reuse the current spec path when one was available?
- In artifact mode, does the spec use stable English headings and English
  generated prose while preserving useful user-authored original wording,
  identifiers, paths, commands, and quoted text?
- In artifact mode, does the spec omit `Approval state`, approval-status fields
  or values such as `Status: Draft`, `Status: Awaiting explicit approval`,
  `Status: Approved`, `Status: Reopened after approval`, `Approval note`,
  `Revision notes`, and equivalent approval or revision-history sections?
- When updating a legacy spec artifact, did you remove old approval-status and
  revision-history sections from the saved artifact instead of preserving or
  updating them?
- Are confirmed requirements, proposed defaults, options, decisions,
  assumptions, out-of-scope items, acceptance criteria, and unknowns separated?
- If approval evidence is available, is it tied to the current spec or an
  unambiguous current-spec planning handoff rather than an artifact status
  field?
- In artifact mode, if requirements changed after approval, did you replace
  superseded spec content and require renewed explicit approval?
- If brainstorming was used, are ideas clearly marked as options rather than
  confirmed requirements, and are there two to five options?
- Did every build-changing dimension named or implied by the user appear in one
  spec section?
- For billing, permission, security, account-setting, recipient, or routing
  changes, did you address auditability as requirement behavior?
- For bulk data writes or imports, did you account for review-before-write or
  preview, partial failure, duplicate or conflict handling, permissions,
  persistence, and rollback or recovery?
- For mutually exclusive data migration, storage, compatibility, or
  destructive-write constraints, did you list viable interpretations or
  resolution choices and state the user-visible or data-safety consequence of
  each without selecting one?
- For a small request, are there no more than three direct questions, and can
  the proposed defaults be accepted with one short reply?
- For a broad request, is there a grouped confirmation checklist instead of an
  interrogation?
- Are `Can default` items limited to confirmed scope or cross-cutting choices
  that stay valid regardless of optional-surface selection?
- If delivery logs, admin views, reporting, audit views, diagnostics, or frequency
  controls were only named as useful, did you keep their record shape, storage,
  retention, queryability, and viewer behavior out of defaults and acceptance
  criteria?
- For billing, permission, security, account-setting, recipient, or routing
  changes, did you still classify auditability as required, deferred, or a user
  decision?
- For billing, permission, security, account-setting, recipient, or routing
  changes, did you mark permission, recipient, and auditability choices as
  blocking or high-impact when they affect access, compliance, account safety,
  or billing outcomes?
- For billing, account-setting, recipient, or routing changes, did you cover
  edit permissions, target eligibility, validation or verification, future-send
  consequences, and auditability as requirements, decisions, defaults, or
  unknowns?
- For invoice or billing-email recipient changes, did you explicitly cover the
  delivery-effect window for the next invoice, already-generated unsent invoices,
  retries or reminders, future billing-cycle emails, and added or removed
  recipient notifications as a requirement, proposed default, or unknown?
- For invoice or billing-email recipient clarification, did delivery-effect
  coverage survive the three-question limit rather than being displaced by
  recipient count, minimum-list behavior, or auditability questions?
- For notification or messaging channels such as email, SMS, and push, did you
  surface channel-specific product uncertainties without inventing provider
  facts?
- In artifact mode, does the chat summary include the spec path, approval
  evidence or the exact approval action still needed, blockers or unknowns, and
  exact next user action?
- If build-changing local evidence checks remain open, does the summary name
  them under a clear `Local evidence still needed`-style label alongside user
  decisions instead of presenting user replies as the only remaining gate?
- In chat-only mode, does the response state that no spec file was written and
  name the exact next user action for artifact drafting or approval?
- In chat-only mode with an existing spec artifact, did you preserve the current
  spec path as unchanged context and avoid changing any legacy approval state
  from brainstorming alone?
- Does the response stop after the spec artifact and summary, or after the
  chat-only exploration response, even if the user approved the spec, said to go
  ahead, or the next phase seems obvious?
- In approval-evidence summary mode, is the next action a generic later
  planning-phase handoff rather than an instruction to invoke, run, start, or
  route to a workflow, tool, skill, or named planning process?
