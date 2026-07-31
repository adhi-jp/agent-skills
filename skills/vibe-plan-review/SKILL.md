---
version: 1.0.0
name: vibe-plan-review
description: Use when the user asks to review, confirm, walk through, or pre-check a saved Markdown implementation plan before implementation; interactively reviews plan items one at a time and manages localized item-level decisions.
---

# Vibe Plan Review

## Overview

Review a saved Markdown implementation plan with the user before implementation
begins. The goal is to surface requirement mismatches, ordering problems,
missing work, ambiguity, risks, and unverifiable items while preserving user
control over every plan item decision.

This skill reviews the plan; it does not execute it. Stop after item review and
the final plan-reflection confirmation workflow. Do not proceed into
implementation, tests, releases, or adjacent coding work.

An explicit invocation permits a scoped local checkpoint commit only when the
user later confirms reflection and that reflection changes the tracked original
plan. The commit may include only the reflected plan-owned tracked paths after
the reflection result is verified. Do not commit item-review chat, temporary
review files, an unreflected plan, an unchanged plan, or an empty file set. The
permission is denied by an explicit no-commit instruction or project policy and
does not include implementation, push, release preparation, version changes,
amend, rebase, reset, stash, squash, or deletion of unrelated state.

If the host requires separate confirmation for local commits, ask once at
review startup when reflection may update a tracked plan. Do not wait until
after reflection. A review that is guaranteed to remain chat-only does not need
the question.

Runtime responses should match the user's language. Before rendering item-review
output, interpreting item decisions, counting review-file thresholds, reflecting
decisions into the plan, or summarizing review results, read
`references/localized-labels.md` and use its exact localized labels, numeric
choice identifiers, and decision semantics. Preserve non-sensitive file paths,
commands, identifiers, and review-state paths exactly. Credential-like literal
values are governed by §Sensitive Content Handling and are never reproduced for
exactness.

## Sensitive Content Handling

Treat plan, requirements-spec, source, and temporary-review content as
potentially sensitive. A requirement to read, quote, preserve, summarize, or
reflect content never authorizes reproducing a suspected credential, token,
password, private key, URL-embedded authentication value, session secret, or
env-style secret assignment.

When a sensitive literal is found:

- Do not emit it in chat, item findings, the temporary review file, reflected
  plan text, commit messages, summaries, quoted snippets, or tool arguments.
- Refer to it by file path and line or item anchor, secret class, and a marker
  such as `[REDACTED:credential]`. Preserve the surrounding non-sensitive
  command shape and identifier when that is needed to review the item.
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

Begin every review response with a compact binding block before item analysis,
decisions, blockers, reflection, or completion behavior:

- `Target plan`: the exact saved plan path.
- `Requirements spec`: the exact spec path, or an explicit limited-confidence
  no-spec status.
- `Temporary review`: the exact derived temporary-review path and its current
  status, including `not created`, `kept`, `blocked`, or `deleted`.

This block is required on first-item, continuation, stop, reflection, and
completion responses. A status without its path is not a resumable identity.

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
7. Determine whether a temporary review file is required before presenting the
   first item.

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
decision but does not override it.

Render each user decision option with the stable numeric identifiers defined in
`references/localized-labels.md`. Accept either the canonical localized decision
label or an unambiguous numeric identifier for the current item decision. Store,
count, summarize, and reflect the decision as its canonical localized label, not
as the numeric identifier. If a user's reply contains conflicting labels or
identifiers, ask which decision they intend before continuing.

## Temporary Review File

Short reviews remain chat-only when all of these are true:

- The plan has fewer than 8 detected items.
- Fewer than 3 item decisions are revise-or-hold decisions as defined in
  `references/localized-labels.md`.
- The user has not asked for a review file.

Create or update a temporary review file when any of these are true:

- The plan has 8 or more detected items.
- 3 or more item decisions are revise-or-hold decisions as defined in
  `references/localized-labels.md`.
- The user asks for a review file.

Store the temporary review file beside the plan as `.<plan-name>.review.md`,
where `<plan-name>` is the target plan filename stem, meaning the filename
without its final suffix. For `plans/payment-plan.md`, use
`plans/.payment-plan.review.md`; for `plans/payment.plan.md`, use
`plans/.payment.plan.review.md`.

During item review, the only allowed file write is creating or updating this
temporary review file. Do not modify the original implementation plan during
item review.

Record enough state to resume review:

- Target plan path.
- Requirements spec path when known, or the limited-confidence no-spec status.
- Detected item list.
- Current review position.
- Per-item AI judgments.
- User decisions as canonical localized labels, even when the user supplied a
  numeric identifier.
- Unresolved blockers.
- Important decision summaries.
- Conversation summary when the user asks for it or when an important decision
  should survive context loss.

Apply §Sensitive Content Handling before every temporary-review-file write.

If the temporary review file already exists, read it before writing. Resume only
when it clearly matches the target plan and is parseable. If ownership, target
identity, parseability, or external edits are unclear, stop and ask whether to
resume, replace, or preserve the file. Do not overwrite or delete a preexisting
review file while that question is unresolved.

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
original-plan write or checkpoint.

After successful reflection, ask whether to delete the temporary review file.
Honor a user instruction to keep it. If the file has unexpected changes or
ownership is unclear, preserve it and report the reason.

After successful reflected-plan verification, create the scoped local
checkpoint when permitted. Run dirty-state and staged-diff checks, stage only
the reflected plan-owned paths, use a standalone Conventional Commit message,
and inspect the stored message and committed file set. If the user denied
commits, project policy forbids them, or unrelated changes cannot be excluded,
leave the reflected plan reviewed but uncommitted and report the blocker.

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
- Whether the reflected plan received its scoped local checkpoint, was unchanged,
  was explicitly left uncommitted, or was blocked by a named safety condition.
- That implementation was not started.
