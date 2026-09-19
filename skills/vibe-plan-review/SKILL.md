---
version: 3.1.1
name: vibe-plan-review
description: Use when the user asks to review, confirm, walk through, or pre-check a saved Markdown implementation plan before implementation; interactively reviews plan items one at a time and manages localized item-level decisions.
---

# Vibe Plan Review

## Overview

Review a saved Markdown implementation plan with the user before implementation
begins. The goal is to surface requirement mismatches, ordering problems,
missing work, ambiguity, risks, and unverifiable items while preserving user
control over every plan item decision. At review start, resume after
interruption, target change, reflection, completion, or a blocker that
prevents further review — even before the first item — include the binding
information that Review Binding Output defines: the target plan, the
requirements source or limited-confidence no-spec status, and the persistence
state. Report binding information not yet established as such, and give a
persistence path only when persistence exists or is being selected.

### Effect And Write Boundaries

<!-- shared-contract:class language=none commit=document-only effect=artifact-only -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
**Write nothing beyond what the phase's declared effect class and boundary permit.**

- Apply the effect class the phase declares in its own text; where this package states a narrower limit, the narrower limit wins.
- Read-only: report in chat; edit no file, run no state-mutating command, and never stage, commit, tag, push, change versions, delete data, or start services. Write a file only when the user explicitly asks for a saved artifact.
- Artifact-only: create or update only the artifact the phase owns and the supporting paths its text declares, such as a confirmed plan reflection or a decision record, and leave them in the working tree.
- Never let an artifact-only phase implement executable behavior, edit code or tests as implementation, produce another phase's artifact, do release work, or treat its artifact as same-turn implementation authority.
- State-changing: edit and run commands only inside the declared scope, in its smallest verified unit; leave other paths, pre-existing changes, and runtime or external state untouched unless the user selects them.
- These limits cover shell commands (redirection, `sed -i`, `tee`, `mv`, `cp`, `rm`, `git checkout --`) as well as file tools; report a refused write as a boundary stop and never retry it through another tool.
- Keep every irreversible or outward-facing operation under its own consent.
<!-- shared-contract:end effect-write-boundaries -->

This phase reviews the saved plan and never executes it; it stops after item
review and the final plan-reflection confirmation workflow. The artifact it owns
is the temporary review-state file that §Review State Persistence names and
places; its declared supporting paths are the target plan file, written only
as the confirmed reflection that §Reflection Into The Plan governs, and the
record directories named under §Durable Records.

### Durable Records

Read `references/durable-records.md` before recording a settled decision,
deferring a finding, or applying or updating an existing record. This phase
writes `docs/decisions/` and `docs/reports/findings/`, or the repository's
existing record directory, as declared supporting paths.

### Commit Selection

<!-- shared-contract:begin commit-selection-document-only source=shared/vibe-contract.md -->
**Never let a document-only phase select a commit.**

- Leave verified artifact changes in the working tree; invocation, path placement, tracked status, a passing review or audit, reflection consent, or artifact completion selects no commit.
- Only an explicit current-user request selects one, scoped to the artifact the phase owns; the commit workflow, or the phase itself when none is visible, commits it under file-set review, message transport, stored-message verification, and the push and history boundaries.
- Never stage, commit, push, release, change versions, or rewrite history while drafting, and never let the artifact authorize implementation, push, release, a version change, or a history rewrite.
<!-- shared-contract:end commit-selection-document-only -->

A commit the current user explicitly requests is routed to a later
commit-execution workflow and is never performed by this phase. Its target is
the reflected plan file; the temporary review-state file is not committed, and
its cleanup remains a separate user decision.

### Runtime Language

Runtime responses should match the user's language. Before rendering item-review
output, interpreting item decisions, selecting review-state persistence,
reflecting decisions into the plan, or summarizing review results, read
`references/localized-labels.md` and use its exact localized labels, numeric
choice identifiers, and decision semantics. Preserve non-sensitive file paths,
commands, identifiers, and review-state paths exactly. Credential-like literal
values are governed by §Sensitive Content Handling and are never reproduced for
exactness.

## Sensitive Content Handling

<!-- shared-contract:begin secret-redaction source=shared/vibe-contract.md -->
**Redact secret-like literals before any text crosses an output boundary.**

- Output boundaries include chat, saved files, forwarding to another agent or backend, ledgers, quoted snippets, summaries, and tool arguments.
- Never let a request to read, quote, preserve, or summarize content authorize reproducing a secret value.
- Replace each match with `[REDACTED:<type>]`, choosing the most specific type:
  - `private-key`: PEM private-key blocks;
  - `jwt`: three-part JWT-like tokens;
  - `url-auth`: credentials embedded in `http` or `https` URLs;
  - `apikey`: known-prefix API keys and access tokens;
  - `env-secret`: env-style assignments whose names end in key, token, secret, password, or pwd;
  - `secret-context`: other high-entropy text next to key, token, secret, password, bearer, or session-secret wording.
- Keep non-secret wording and the anchors needed to verify a finding: paths, line numbers, symbols, commands, field names, and identifiers.
<!-- shared-contract:end secret-redaction -->

Plan, requirements-spec, source, and temporary-review content are all in scope
for that redaction, as is any commit message this phase drafts or hands to the
commit workflow, and the plan item anchor is one of the anchors preserved for
verification alongside the path and line. A suspected credential that matches
none of the typed classes above is still treated as secret-like here and
redacted under the same rules with a `credential` type.

When a sensitive literal is found:

- Treat a live-looking credential committed to or embedded in the plan as a
  blocker. Ask the user to remove it and rotate or revoke it through an
  appropriate secure process; do not request that the value be pasted into the
  conversation.
- Do not copy a sensitive source line into the temporary review file. Record
  only the redacted location, classification, decision state, and required
  remediation.
- Do not reflect an item containing a sensitive literal by regenerating or
  copying that literal. Do not reflect any decisions into the original plan
  while a suspected sensitive literal remains anywhere in the target plan or
  temporary review state. Ask the user to sanitize it through an appropriate
  secure process or explicitly confirm a non-secret environment-variable or
  secret-store reference, then re-read the sanitized artifact before
  reflection. Never include the old value in patch context or tool arguments.

If distinguishing a credential from a non-secret identifier is uncertain,
redact the value in outputs and ask about the intended secure reference without
showing the candidate value. Redaction does not authorize implementation,
rotation, revocation, or access to an external secret store.

## Required Inputs

The primary target is a saved Markdown implementation plan file. If the user
does not provide a local path or otherwise identify one specific saved plan,
ask for the plan file before starting review.

Treat summaries, chat excerpts, issue descriptions, and pasted snippets as
context only. The saved plan file controls the review.

## Phase Boundary

Use this skill only after an implementation plan exists and before
implementation starts. Do not name or require any neighboring workflow as a
prerequisite or next step. When review is complete, report the reviewed state
and stop at the user's next decision point.

## Review Binding Output

Show the target plan, requirements source or limited-confidence no-spec status,
and persistence state at review start, resume, target change, reflection,
completion, and any blocker that prevents further review. When a temporary
review file already exists or is being selected, give its exact path as that
persistence state; when review state stays in conversation, say so and give no
path. Do not repeat a binding block on every same-session item response when
nothing changed.

## Start Of Review

Before reviewing items:

1. Read the target plan file.
2. Identify whether the plan explicitly references a corresponding requirements
   spec path.
3. If an explicit requirements spec path exists, read that file.
4. If no explicit path exists, look for an obvious same-goal requirements spec
   in `docs/specs/` and `specs/` at the workspace root and in the plan's
   directory.
5. If no corresponding requirements spec can be identified in any of those
   locations, continue only with explicitly limited requirement-alignment
   confidence.
6. Identify plan items using the item extraction rules below.
7. Select persistence before the first item only when the user requests it,
   cross-session continuation is expected, context-loss risk is material, or an
   established project convention requires it.

If a corresponding requirements spec exists, it is requirement evidence for
the review. If the requirements spec and implementation plan conflict, stop the
review, state the conflict, and ask whether the requirements or the plan should
be corrected. Do not continue item review while the conflict controls the item.

If the plan lacks information needed to review it, stop the review, state what
is missing, and ask how to complete the plan. Do not invent missing behavior,
requirements, acceptance criteria, test paths, data handling, or user
experience.

## Source And Code Inspection

Default to minimal source and code inspection. Read only the files needed to
check the current plan item unless the user asks for deeper investigation or
the item has high implementation impact.

High implementation impact includes changes that could affect data handling,
permissions, security posture, releases, migrations, external contracts,
destructive writes, or broad user experience. When deeper inspection is needed,
explain why the item needs it before expanding the read scope.

## Item Extraction

Prefer explicit task or checklist items in the saved plan. If the plan is
organized by headings rather than checkboxes, review the smallest executable
sections in file order.

If item boundaries are ambiguous, stop and ask the user whether to use the
detected sections or revise the plan structure first. Do not silently choose a
more convenient item granularity.

Keep item identity stable during review. If you propose splitting, merging, or
reordering items, present the proposal as a recommendation and wait for the
user's decision before treating it as part of the executable plan.

## Per-Item Review

Read `references/localized-labels.md` before the first per-item review in a
session.

Review one item at a time. For each item, check:

- Requirement alignment.
- Implementation order and dependency sequencing.
- Missing work.
- Ambiguity.
- Risks.
- Verifiability.

The user's item decision is the source of truth. AI judgment guides the
decision but does not override it. Write a held or revise decision that
qualifies under the durable-records contract as a decision record once
settled; plan reflection keeps its consent.

Render each user decision option with the stable numeric identifiers defined in
`references/localized-labels.md`. Accept either the canonical localized decision
label or an unambiguous numeric identifier for the current item decision. Store,
count, summarize, and reflect the decision as its canonical localized label, not
as the numeric identifier. If a user's reply contains conflicting labels or
identifiers, ask which decision they intend before continuing.

## Review State Persistence

Keep review state in conversation by default. Persist a temporary review file
only when the user asks, cross-session continuation is expected, context loss is
a material risk, or an established project convention already owns such state.
Do not use item-count or decision-count thresholds.

When persistence is selected, store the file beside the plan as
`.<plan-name>.review.md` and record the target, requirements source, item list,
position, canonical decisions, blockers, and concise continuation context. Apply
sensitive-content rules before every write. If an existing file is mismatched,
unparseable, externally edited, or ownership is unclear, stop and ask before
overwriting or deleting it. At that mismatch blocker, state the exact current
target, the exact derived review-state path, and the recorded conflicting target,
then ask whether to resume the old review, replace the state for the current
plan, or preserve it and continue without using it.

## Reflection Into The Plan

After all detected items have been reviewed, ask for explicit confirmation
before modifying the original implementation plan. The confirmation must state
how decisions will be reflected according to `references/localized-labels.md`.

Before asking for that confirmation, make the reflection record explicit:

- State that item review is complete and reflection has not happened yet.
- Explain all four localized decision outcomes, including that a `削除` item is
  removed only after this reflection confirmation.
- State that review-history annotations, per-item judgment logs, and chat
  discussion notes stay out of executable plan content.
- State that deleting the temporary review file is a separate decision asked
  only after successful reflection.

Do not reflect review results into the original plan without this explicit
confirmation. A general request to review the plan is not reflection consent.

Reflected plans should contain executable plan content plus unresolved held
items. Remove review-history annotations, per-item judgment logs, and chat
discussion notes from the executable plan.

Apply §Sensitive Content Handling before reflection and verification. A
reflected plan must not newly contain or reproduce a sensitive literal from the
source plan, requirements spec, temporary review file, source inspection, or
conversation. If the pre-reflection scan still finds one, stop before any
original-plan write.

After successful reflection, ask whether to delete the temporary review file.
Honor a user instruction to keep it. If the file has unexpected changes or
ownership is unclear, preserve it and report the reason.

After successful reflected-plan verification, leave the plan changes
uncommitted unless the current user explicitly asks for a commit. Temporary
review-file cleanup remains a separate user decision.

## Stop Conditions

Stop and ask for user direction when:

- No saved Markdown implementation plan file is identified.
- The target plan file cannot be read.
- A corresponding requirements spec exists but cannot be read.
- The requirements spec and implementation plan conflict.
- Plan information needed for review is missing.
- Item boundaries are ambiguous.
- A preexisting temporary review file is mismatched, unparseable, externally
  edited, or has unclear ownership.
- A suspected sensitive literal remains in the target plan or temporary review
  state when reflection is requested.
- The user asks to change scope beyond reviewing and reflecting the saved plan.
- The user asks to start implementation, tests, release preparation, or
  other work outside plan review.

When stopping, state the blocker, the evidence that triggered it, the effect on
review, and the closest next user decision.

## Completion Summary

When the review workflow completes, summarize:

- Target plan path.
- Requirements spec path or limited-confidence no-spec status.
- Number of items reviewed.
- Decisions by count for the four canonical user decision labels, not their
  numeric identifiers.
- Unresolved blockers or held items.
- Whether the original plan was reflected after explicit confirmation.
- Whether the temporary review file was created, kept, or deleted.
- Whether the reflected plan changed and whether an explicit commit request remains pending.
- That implementation was not started.
