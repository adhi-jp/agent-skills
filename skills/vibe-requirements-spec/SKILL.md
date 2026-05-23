---
name: vibe-requirements-spec
description: Use when a user wants to draft, revise, or approve a Markdown requirements spec for a rough, ambiguous, contradictory, creative, non-technical, or underspecified coding goal before implementation planning or coding.
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

The spec is input to a later implementation-planning phase. This skill may mark
the spec approved, but it stops after the spec artifact and concise summary. Do
not require or name a specific downstream planning workflow unless the user
named one as context.

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

## Core Rules

- Keep the active artifact to one requirements spec unless the user explicitly
  cancels it or replaces it with a new spec effort.
- Keep the skill active for related requirement-spec work until the user
  explicitly approves the current spec, explicitly cancels the drafting effort,
  or explicitly replaces it.
- Treat vague readiness wording, completed checklists, no open questions,
  "looks good", "ready", "continue", "go ahead", and similar handoff phrases
  as continued drafting unless they clearly approve the current spec artifact.
- If the user changes requirements after approval, update the same spec, set the
  approval state to `Reopened after approval`, record the change in
  `Revision notes`, and require renewed explicit approval before the revised
  spec is used for implementation planning.
- Separate confirmed requirements, proposed defaults, candidate options,
  decisions, assumptions, out-of-scope items, acceptance criteria, and open
  unknowns.
- Use brainstorming only to produce candidate options. Do not treat an idea as
  a confirmed requirement until the user chooses it or explicitly approves it.
- Do not run verification commands while this skill is active. Evidence checks
  that affect requirements should be recorded as open unknowns or user decisions
  for a later phase unless the user explicitly asked this skill to inspect
  already-provided source material for the spec.

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
file instead of creating a new unrelated spec. Revision history belongs in the
spec's `Revision notes` section, not in separate files.

## Spec Template

Use stable English section headings unless the user explicitly requested a
different language for headings. Preserve user-authored requirement wording,
domain terms, paths, API names, commands, and quoted text exactly where useful.

```markdown
# [Goal or Feature Name] Requirements Spec

## Approval state
- Status: Draft | Awaiting explicit approval | Approved | Reopened after approval
- Current spec path: [path]
- Last updated: YYYY-MM-DD
- Approval note: [who approved, what was approved, or what is still needed]

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

## Revision notes
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
   - Use the grouped checklist for broad requests spanning several surfaces,
     domains, high-impact rules, or contradictory goals.
   - For bulk data creation, imports, migrations, destructive changes, and
     irreversible writes, classify write-safety decisions before approval:
     review-before-write or preview, partial-failure behavior, duplicate or
     conflict handling, permissions, persistence, and rollback or recovery.
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

7. **Set approval state**
   - Use `Draft` while the spec is incomplete or contradictory.
   - Use `Awaiting explicit approval` when the spec is coherent and waiting for
     the user to approve or change it.
   - Use `Approved` only when the user explicitly approves the current spec,
     such as "approve this spec", "仕様を承認", "use this spec for planning", or
     an equivalent statement tied to the current spec.
   - Use `Reopened after approval` when any requirement changes after approval.
   - Ambiguous "looks good", "ready", "continue", or "go ahead" wording does
     not approve the current spec unless the surrounding text clearly says the
     spec itself is approved.

8. **Return a concise localized summary**
   - Use the user's language for the chat response unless they ask otherwise.
   - Include the spec path, approval state, blocking decisions or unknowns, and
     the exact user action needed next.
   - Stop after the spec summary.
   - If the user explicitly approved the spec and also asked to plan or
     implement, mark the spec approved and say the approved file can be used by
     a later implementation-planning phase. Do not create that plan in the same
     skill response.

## Approval Lifecycle

This skill remains active across related turns until one of these happens:

- The user explicitly approves the current spec artifact.
- The user explicitly cancels the spec drafting effort.
- The user explicitly replaces it with a different spec effort.

No amount of internal confidence, absence of open questions, completed
checklists, or readiness wording ends the skill by itself. If the next user turn
adds requirements, edits decisions, changes scope, or responds ambiguously, keep
updating the same spec and keep approval state unapproved or reopened.

Approved specs are stable input to later implementation planning. They do not
authorize same-turn implementation planning, code edits, tests, verification
commands, commits, release work, changelog edits, or unrelated file edits while
this skill is active.

## Common Mistakes

- Creating a new spec when the current conversation already has a spec path.
- Treating "looks good" or "go ahead" as spec approval without clear approval of
  the current artifact.
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
- Leaving rollback or recovery expectations as ordinary risks when the work
  depends on safety, invisibility, compatibility, or destructive-change
  recovery.
- Naming or requiring a specific downstream planning skill or workflow.

## Self-Check

Before responding, check:

- Did you create or update only the requirements spec artifact?
- Did you reuse the current spec path when one was available?
- Does the spec use the stable headings, including `Approval state`?
- Are confirmed requirements, proposed defaults, options, decisions,
  assumptions, out-of-scope items, acceptance criteria, and unknowns separated?
- Is approval state one of `Draft`, `Awaiting explicit approval`, `Approved`, or
  `Reopened after approval`?
- If approval is marked `Approved`, did the user explicitly approve the current
  spec artifact?
- If requirements changed after approval, did you reopen the spec and require
  renewed explicit approval?
- If brainstorming was used, are ideas clearly marked as options rather than
  confirmed requirements, and are there two to five options?
- Did every build-changing dimension named or implied by the user appear in one
  spec section?
- For billing, permission, security, account-setting, recipient, or routing
  changes, did you address auditability as requirement behavior?
- For bulk data writes or imports, did you account for review-before-write or
  preview, partial failure, duplicate or conflict handling, permissions,
  persistence, and rollback or recovery?
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
- Does the chat summary include the spec path, approval state, blockers or
  unknowns, and exact next user action?
- Does the response stop after the spec artifact and summary even if the user
  approved the spec, said to go ahead, or the next phase seems obvious?
