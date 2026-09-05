---
version: 3.0.0
name: vibe-plan-review
description: Use when the user asks to review, confirm, walk through, or pre-check a saved Markdown implementation plan before implementation; interactively reviews plan items one at a time and manages localized item-level decisions.
---

# Vibe Plan Review

## Overview

Review a saved Markdown implementation plan with the user before implementation
begins. The goal is to surface requirement mismatches, ordering problems,
missing work, ambiguity, risks, and unverifiable items while preserving user
control over every plan item decision.

### Effect And Write Boundaries

<!-- shared-contract:class language=none commit=document-only effect=artifact-only -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
Every workflow phase belongs to one effect class, declared in its own text, and writes nothing beyond what that class and its declared boundary permit.

- A read-only phase reads and reports. Its deliverable is chat: findings, alignment, or direction. It edits no source, test, config, doc, or other file, runs no command that mutates runtime or repository state, and does not stage, commit, tag, push, change versions, delete data, or start services. It writes a file only when the current user explicitly asks for a saved artifact.
- An artifact-only phase creates or updates the artifact it owns — the requirements spec, the plan, the plan-review state, the instruction files, or the text artifacts the request names — and the supporting paths its own text declares: the text it was asked to revise (comments, docstrings, docs), a confirmed reflection into the bound plan, an ignore file it previewed and the user confirmed, or a narrowly confirmed configuration edit its text names. It leaves those verified changes in the working tree. It does not implement executable behavior, does not edit application code or tests as implementation, does not produce an artifact another phase owns, and does not perform release work; its artifact never authorizes same-turn implementation.
- A state-changing phase edits files and runs commands inside the scope its own text declares — the unit it implements, the repair it proves, the fixes it applies, the round it integrates, or the commit it executes — and keeps its edits to the smallest verified unit of that scope. Paths outside the scope, pre-existing working-tree changes it did not make, and runtime or external state beyond the scope stay unwritten unless the current user selects them, and every irreversible or outward-facing operation stays under its own consent.
Where a package declares a stricter or narrower rule in its own text, that declaration controls.
<!-- shared-contract:end effect-write-boundaries -->

This phase reviews the saved plan and never executes it; it stops after item
review and the final plan-reflection confirmation workflow. The artifact it owns
is the temporary review-state file that §Review State Persistence names and
places; its one declared supporting path is the target plan file, written only
as the confirmed reflection that §Reflection Into The Plan governs.

### Read-Only-Phase Write Gate

<!-- shared-contract:begin read-only-phase-write-gate source=shared/vibe-contract.md -->
This gate covers writes during a read-only or artifact-only phase. Observable input: the target path of a file-edit or file-write tool call, or a shell tool call whose command writes a path (redirection, `sed -i`, `tee`, a heredoc, `mv`, `cp`, `rm`, `git checkout --`, matched best-effort), together with the session record for this worktree under `.plans/vibe-sessions/`, reading `status`, `lease.expires_at`, `repository.worktree`, `host_session_id`, `phase`, `effect_mode`, and `allowed_paths`; the directory's other candidate records, to detect a conflicting record; the readable bytes of every artifact named in `artifact_identity`, to detect an identity mismatch; and any supplied prior record, to check `generation`.

Observable stop, with three outcomes: `deny`, with a reason that names the target path and quotes the recorded `phase`, `effect_mode`, and `allowed_paths`, only when a fresh, valid, session-bound record exists whose `effect_mode` is `read-only` or `artifact-only` and the target's canonical absolute path is outside every recorded `allowed_paths` entry (the entry itself or a path beneath a recorded directory); `allow` in every other case — a target inside `allowed_paths`, an `effect_mode` of `state-changing` or `none`, or a record that is absent, malformed, stale, foreign, session-unbound, conflicting, or identity-mismatched; and `ask`, which this gate never returns. No invalid record state ever produces `deny`, so the refusal never rests on unverified host behavior. A denied write is reported verbatim by the agent as a boundary stop, not retried through another tool.

Control-plane exception: a write whose target is the active session record itself — `.plans/vibe-sessions/<record_id>.json` under the repository root — or that record's temporary file in the same directory, written for the atomic rename, is `allow` regardless of `effect_mode`, when the target's canonical path is inside `.plans/vibe-sessions/` and its stem equals the active record's `record_id`. Every other path under that directory is judged like any other path, and the exception does not broaden `allowed_paths`.

When no user-installed hook enforces this gate, this wording is the whole gate: a read-only phase writes only an explicitly requested saved artifact whose canonical path is recorded in `allowed_paths` and otherwise writes no file; an artifact-only phase writes only the artifact it owns, the supporting paths its own text declares, and the scratch root recorded for the unit; the router's write of its own record falls under the exception above and is not a phase write; and a write outside that boundary is refused by the phase itself and reported as a boundary stop.
A package may state which of its phases this gate applies to; it may not change the gate's inputs, outcomes, or fields.
<!-- shared-contract:end read-only-phase-write-gate -->

This gate applies to the plan-review phase.

### Commit Selection

<!-- shared-contract:begin commit-selection-document-only source=shared/vibe-contract.md -->
A document-only phase never selects a commit. Its verified artifact changes remain in the working tree: invocation, conventional path placement, tracked status, a successful review, audit, or verification, reflection consent, and artifact completion do not select history work, and the phase itself never stages, commits, pushes, prepares releases, changes versions, or rewrites history while it drafts. Only an explicit current user request selects a commit; that commit is scoped to the artifact the phase owns and follows the commit-execution workflow's checks — file-set review, message transport, stored-message verification, and the push and history boundaries — whether a visible commit-execution specialist performs it or the phase performs it itself under those same checks. The artifact itself authorizes no implementation, push, release preparation, version change, or history rewrite.
Where a package declares a stricter or narrower rule in its own text, that declaration controls.
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
Redact secret-like literals before any text crosses an output boundary: rendering, persistence, forwarding to another agent or backend, ledger projection, quoted snippets, summaries, and tool arguments. A requirement to read, quote, preserve, summarize, or reflect content never authorizes reproducing the value. Detection classes:

- `apikey`: known-prefix API keys and access tokens.
- `jwt`: three-part JWT-like tokens.
- `private-key`: PEM private-key headers and matching footers.
- `url-auth`: credentials embedded in `http` or `https` URLs.
- `secret-context`: high-entropy text co-occurring with key, token, secret, password, api key, bearer, or session-secret context.
- `env-secret`: env-style assignment names ending in key, token, secret, password, or pwd.

Replace each match with `[REDACTED:<type>]`. When one span matches several classes, the most specific structural class wins: `env-secret` for a secret-named environment assignment and `apikey` for a recognized API-key prefix take precedence over generic `secret-context`. Preserve non-secret wording and the anchors needed to verify the finding — paths, line numbers, symbols, commands, API names, field names, and identifiers. Count the redactions and render a compact footer when any occurred.
Where a package declares a stricter or narrower rule in its own text, that declaration controls.
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
and persistence state at review start, resume, target change, reflection, and
completion. Do not repeat a binding block on every same-session item response
when nothing changed.

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
decision but does not override it.

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
