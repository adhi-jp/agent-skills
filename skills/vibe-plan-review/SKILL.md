---
version: 3.1.1
name: vibe-plan-review
description: Use when the user asks to review, confirm, walk through, or pre-check a saved Markdown implementation plan before implementation; interactively reviews plan items one at a time and manages localized item-level decisions.
---

# Vibe Plan Review

## Overview

Review a saved Markdown implementation plan with the user before implementation.
Surface mismatches, ordering problems, missing work, ambiguity, risks, and
unverifiable items while the user decides each item. Use §Review Binding Output
at its listed lifecycle events.

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

The artifact this phase owns is the temporary review-state file §Review State
Persistence names; its supporting paths are the target plan, written only as
the confirmed reflection §Reflection Into The Plan governs, and the record
directories under §Durable Records.

### Durable Records

At phase start, check `docs/decisions/README.md` and
`docs/reports/findings/README.md` (or the repository's existing indexes) for
entries whose paths, tags, or subject match the reviewed plan, and open the
entries that apply. Read `references/durable-records.md` before recording a
settled decision, deferring a finding, or applying or updating an existing
record. This phase writes `docs/decisions/` and `docs/reports/findings/`, or
the repository's existing record directory, as declared supporting paths.

### Commit Selection

<!-- shared-contract:begin commit-selection-document-only source=shared/vibe-contract.md -->
**Never let a document-only phase select a commit.**

- Leave verified artifact changes in the working tree; invocation, path placement, tracked status, a passing review or audit, reflection consent, or artifact completion selects no commit.
- Only an explicit current-user request selects one, scoped to the artifact the phase owns; the commit workflow, or the phase itself when none is visible, commits it under file-set review, message transport, stored-message verification, and the push and history boundaries.
- Never stage, commit, push, release, change versions, or rewrite history while drafting, and never let the artifact authorize implementation, push, release, a version change, or a history rewrite.
<!-- shared-contract:end commit-selection-document-only -->

This phase never performs a requested commit: it routes it to commit execution
for the reflected plan file, never the temporary review-state file, whose
cleanup is a separate user decision.

### Runtime Language

Match the user's language. Read `references/localized-labels.md` before
rendering or interpreting decisions, reflecting them, or summarizing; use its
labels, numeric identifiers, and semantics. Preserve non-sensitive paths,
commands, identifiers, and review-state paths exactly.

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

Also redact a suspected credential that matches no listed type, as
`[REDACTED:credential]`, and keep the plan item anchor with the path and line.
When a sensitive literal is found:

- Treat a live-looking credential in the plan as a blocker: ask the user to
  remove it and rotate or revoke it through a secure process, never to paste it
  into the conversation.
- Record only its redacted location, classification, decision state, and
  required remediation in the temporary review file.
- Reflect nothing into the original plan while a suspected sensitive literal
  remains in the plan or review state, and never let a reflected plan contain
  one from any source. Ask the user to sanitize it or confirm a non-secret
  environment-variable or secret-store reference, then re-read the sanitized
  artifact before reflecting.
- When a value may be a credential or a non-secret identifier, redact it and
  ask about the intended secure reference without showing it.

## Required Inputs

Review one identified saved Markdown implementation plan. Treat other material
as context; if no plan is identified, ask for it.

## Phase Boundary

Use this skill after a plan exists and before implementation. On completion,
report the reviewed state and stop at the user's next decision point.

## Review Binding Output

Show the target plan, requirements source or limited-confidence no-spec status,
and persistence state at review start, resume, target change, reflection,
completion, and any blocker that prevents further review. When a temporary
review file already exists or is being selected, give its exact path as that
persistence state; when review state stays in conversation, say so and give no
path. Do not repeat a binding block on every same-session item response when
nothing changed.

## Start Of Review

Before the first item, read the plan and any explicitly referenced requirements
spec. Otherwise look for an obvious same-goal spec in `docs/specs/`, `specs/`,
or the plan directory; if none exists, continue with limited
requirement-alignment confidence. Identify items and select persistence only
when the user requests it, continuation or context loss is likely, or project
convention requires it.

If a corresponding requirements spec exists, it is requirement evidence for
the review. If the requirements spec and implementation plan conflict, stop the
review, state the conflict, and ask whether the requirements or the plan should
be corrected. Do not continue item review while the conflict controls the item.

If the plan lacks information needed to review it, stop the review, state what
is missing, and ask how to complete the plan. Do not invent missing behavior,
requirements, acceptance criteria, test paths, data handling, or user
experience.

## Source And Code Inspection

Read only what the current item needs unless the user requests more or it affects
data, permissions, security, releases, migrations, external contracts,
destructive writes, or broad user experience. Explain why before expanding
scope.

## Item Extraction

Prefer explicit tasks; otherwise use the smallest executable heading sections
in file order. If boundaries are ambiguous, ask whether to use detected sections
or revise the plan—never choose granularity silently. Keep identities stable;
the user must approve any split, merge, or reorder.

## Per-Item Review

Review one item at a time for requirement alignment, order, missing work,
ambiguity, risk, and verifiability. The user's decision controls; AI judgment
does not override it. Record a qualifying settled held or revise decision under
§Durable Records, without bypassing reflection consent.

Offer the localized choices and stable numeric identifiers from
`references/localized-labels.md`. Accept one unambiguous label or identifier,
normalize it to the canonical label for storage, counts, summaries, and
reflection, and ask when choices conflict.

## Review State Persistence

Keep state in conversation unless the user requests persistence, continuation or
context loss is likely, or project convention requires it; item count never
selects persistence. When selected, store `.<plan-name>.review.md` beside the
plan with the target, requirements source, items, position, canonical decisions,
blockers, and concise continuation context. Before replacing or deleting an
existing mismatched, unparseable, externally edited, or unclear file, stop and
name the current target, derived path, and recorded target; ask to resume,
replace, or preserve it.

## Reflection Into The Plan

After all items, explain the four outcomes from `references/localized-labels.md`,
state that review is complete but unreflected, exclude review history and chat
notes from executable content, and ask for explicit reflection confirmation.
General review consent is not reflection consent; `削除` takes effect only after
confirmation. The reflected plan contains executable content plus held items.

Apply §Sensitive Content Handling before any original-plan write.

After successful reflection, separately ask whether to delete the temporary
file; preserve it if instructed or if it has unexpected changes or unclear
ownership. Verify the reflected plan.

## Stop Conditions

Stop for a missing or unreadable plan/spec, plan-spec conflict, missing review
information, ambiguous items, an unclear review file, an unresolved sensitive
literal at reflection, or work outside reviewing and reflecting the plan. State
the blocker, its evidence and effect, and the nearest user decision.

## Completion Summary

Summarize the target, requirements source or limited-confidence status, items
reviewed, canonical decision counts, blockers or held items, reflection and
temporary-file status, uncommitted plan change or pending commit request, and
that implementation did not start.
