---
version: 3.0.0
name: vibe-writing
description: Use when the primary task is writing, revising, reviewing, or critiquing agent-assisted coding development text, source-code comments or docstrings, README/docs, CHANGELOG/release notes, PR descriptions, UI copy, chat replies, progress updates, final summaries, or git commit messages, especially when text must be LLM-readable, meaning-preserving, format-bound, language-aware, or evidence-bound. Treat incidental wording inside another active workflow as auxiliary.
---

# Vibe Writing

## Overview

Write durable development text for the reader who will use it next. In
agent-assisted coding work, the default reader is an LLM that needs precise contracts,
stable anchors, and explicit evidence. Optimize for human readers only when the
artifact's main reader is human.

### Effect And Write Boundaries

<!-- shared-contract:class language=chat commit=document-only effect=artifact-only -->
<!-- shared-contract:begin closing source=shared/vibe-contract.md -->
For every consolidation block this package carries, here and in its references: where this package declares a stricter or narrower rule in its own text, that declaration controls.
For every gate and schema block this package carries, here and in its references: this package may state which of its phases the block applies to; it may not change the block's inputs, outcomes, or fields.
<!-- shared-contract:end closing -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
**Write nothing beyond what the phase's own effect class and its declared boundary permit.**

- Declare exactly one effect class for every workflow phase, in that phase's own text.
- In a read-only phase, read and report; make chat the deliverable — findings, alignment, or direction.
- In a read-only phase, edit no source, test, config, doc, or other file, and run no command that mutates runtime or repository state.
- In a read-only phase, never stage, commit, tag, push, change versions, delete data, or start services.
- In a read-only phase, write a file only when the current user explicitly asks for a saved artifact.
- In an artifact-only phase, create or update the artifact it owns: the requirements spec, the plan, the plan-review state, the instruction files, or the text artifacts the request names.
- In an artifact-only phase, write the supporting paths its own text declares:
  - the text it was asked to revise (comments, docstrings, docs);
  - a confirmed reflection into the bound plan;
  - an ignore file it previewed and the user confirmed;
  - a narrowly confirmed configuration edit its text names;
  - a decision record or findings report its own text declares.
- In an artifact-only phase, leave those verified changes in the working tree.
- In an artifact-only phase, never implement executable behavior, never edit application code or tests as implementation, never produce an artifact another phase owns, and never perform release work.
- Never let an artifact-only phase's artifact authorize same-turn implementation.
- In a state-changing phase, edit files and run commands inside the scope its own text declares — the unit it implements, the repair it proves, the fixes it applies, the round it integrates, or the commit it executes.
- In a state-changing phase, keep its edits to the smallest verified unit of that scope.
- In a state-changing phase, leave paths outside the scope, pre-existing working-tree changes the phase did not make, and runtime or external state beyond the scope unwritten unless the current user selects them.
- Keep every irreversible or outward-facing operation under its own consent.
<!-- shared-contract:end effect-write-boundaries -->

The artifacts this phase owns are the text deliverables the request names —
source comments and docstrings, README, docs, guides, and UI copy, a saved
audit, report, or postmortem, policy or support copy, a changelog or release
note, a PR description, a progress or final summary, and a commit message —
including a rewrite, polish, or localization of any of them; its declared
supporting paths are the decision records and findings reports named under
`Durable Records`.
This skill does not authorize releases, PR submission, template changes, or workflow shortcuts.

### Durable Records

Before recording a settled decision, deferring a finding, closing a unit, or
starting this phase, read `references/durable-records.md`. This phase writes
`docs/decisions/` and `docs/reports/findings/`, or the repository's existing
record directory, as declared supporting paths.

### Read-Only-Phase Write Gate

<!-- shared-contract:begin read-only-phase-write-gate source=shared/vibe-contract.md -->
**Never write a path your phase's effect class and recorded `allowed_paths` do not permit.**

- With no user-installed hook enforcing this gate, this wording is the whole gate.
- Count as a write any file-edit or file-write tool call, and any shell command that writes a path — redirection, `sed -i`, `tee`, a heredoc, `mv`, `cp`, `rm`, `git checkout --`.
- In a read-only phase, write only an explicitly requested saved artifact whose canonical path is recorded in `allowed_paths`; otherwise write no file.
- In an artifact-only phase, write only the artifact it owns, the supporting paths its own text declares, and the scratch root recorded for the unit.
- Refuse a write outside that boundary in the phase itself and report it as a boundary stop.
- Report a denied write verbatim as a boundary stop; never retry it through another tool.
- Return `deny` only for a fresh, valid, session-bound `read-only` or `artifact-only` record whose canonical target lies outside every `allowed_paths` entry and recorded directory.
- Name the target path in that reason and quote the recorded `phase`, `effect_mode`, and `allowed_paths`.
- Return `allow` in every other case: a target inside `allowed_paths`, an `effect_mode` of `state-changing` or `none`, or a record absent, malformed, stale, foreign, session-unbound, conflicting, or identity-mismatched.
- Never return `ask` from this gate.
- Never let an invalid record state produce `deny`, so the refusal never rests on unverified host behavior.

Example: in an artifact-only phase whose `allowed_paths` holds only the artifact it owns, a write to that artifact is inside the boundary; a write to a source file is outside it, and with a fresh, valid, session-bound record the gate returns `deny`.

Exception: writing the router's own record — `.plans/vibe-sessions/<record_id>.json` or its rename temp file — is `allow` at any `effect_mode`, not a phase write; judge every other path there like any other path, and `allowed_paths` does not widen.
<!-- shared-contract:end read-only-phase-write-gate -->

This gate applies to the writing phase.

### Commit Selection

<!-- shared-contract:begin commit-selection-document-only source=shared/vibe-contract.md -->
**Never let a document-only phase select a commit.**

- Leave the phase's verified artifact changes in the working tree.
- Never let invocation, conventional path placement, tracked status, a successful review, audit, or verification, reflection consent, or artifact completion select history work.
- Never stage, commit, push, prepare releases, change versions, or rewrite history in the phase itself while it drafts.
- Let only an explicit current user request select a commit.
- Scope that commit to the artifact the phase owns.
- Follow the commit-execution workflow's checks for it — file-set review, message transport, stored-message verification, and the push and history boundaries — whether a visible commit-execution specialist performs it or the phase performs it itself under those same checks.
- Never let the artifact itself authorize implementation, push, release preparation, a version change, or a history rewrite.
<!-- shared-contract:end commit-selection-document-only -->

A commit the current user explicitly requests covers the owned text artifact only; a commit-execution workflow performs it, or this phase performs it itself under the minimum commit safety this skill's artifact guidance states.

Wording the user has not yet read is not a closed unit and selects no commit.
When wording is produced inside another active workflow,
that workflow's own checkpoint rules govern its changes.

### Auxiliary Wording Mode

When another workflow is active, use this skill only as auxiliary wording
guidance unless the user asks for a standalone writing deliverable. Incidental
progress updates, final summaries, checkpoint message polish, or README/changelog
phrasing inside planning, execution, review, debug, or release work remain
subordinate to that workflow's authority, stop gates, verification, release
policy, and commit rules.

## Scope Boundaries

Do not rewrite text whose value is exactness: verbatim tool or log output,
protocol snippets, quoted source, or a bare acknowledgment. Relay it unchanged
or answer around it. For transient progress text, stay brief and do not polish
raw logs into summaries unless asked.

## Reader Priority

Default to LLM-optimized writing for agent-assisted coding development text:

- State the operational fact, contract, decision, constraint, or proof directly.
- Prefer stable identifiers, commands, paths, field names, issue IDs, API names,
  and exact error text when they are useful anchors.
- Remove hollow transitions, decorative preambles, and wrap-up phrases when they carry no operational meaning.
- Keep unsupported motivation, benefits, rollout claims, and implied causality
  out of the text.
- Make absence explicit: `tests not run`, `not measured`, `no rollout plan
  supplied`, `not provided`, and similar statuses are real information.

Use human-optimized prose only when the artifact's main reader is human, such as
end-user documentation, user-facing UI copy, support copy, public release notes,
or a README section intended for people learning the project. Docs and guides
can still be LLM-first when their main reader is an LLM agent or developer tool.

## Evidence And Meaning

Do not invent context. Do not add unsupported reasons, goals, outcomes, roadmap
claims, user impact, business value, implementation rationale, tests,
performance/security impact, rollout status, or risk reduction.

Treat supplied capabilities as capabilities. Do not rewrite `supports X` or a
feature name into a cause, purpose, effect, proof, or user benefit unless the
source states that relationship.

Treat represented workflow state in the current prompt as supplied evidence.
When a response-only task says changes are staged, an edit is complete, a check
passed, or another workflow fact is already established, write from that
represented state. Do not replace it with the eval sandbox's, runner's, or
ambient checkout's current state unless the prompt explicitly binds that
checkout as the target to inspect. If the task asks only for a message, command sequence, or closure record, do not
perform a represented mutation merely because tools are available. Describe
commit mechanics only when the represented current request selects a commit or
an owning workflow's checkpoint closes over the represented changes.

Preserve meaning when editing or summarizing. Keep:

- Facts, scope, audience, terminology, and order that matters.
- Conditions, exceptions, warnings, limitations, and required actions.
- Modality. `must`, `should`, `may`, `can`, `required`, `optional`, and
  `recommended` encode different obligations.

Do not over-normalize. Preserve useful local terms, order, tone, and examples when they are search anchors, workflow labels, public contracts, or supplied domain language.
Do not turn `header handoff`, `sample refresh`, or a useful prop or API name into a generic label such as `request metadata flow`.

If a cleaner sentence changes who must do what, when a rule applies, what is
allowed, what is optional, or what happens on failure, it is wrong.

## Language And Format

### Chat Language

<!-- shared-contract:begin language-precedence-chat source=shared/vibe-contract.md -->
**Resolve the language of user-facing chat text separately from any artifact's language, in this order:**

1. An explicit current-user instruction for chat, response, or output language.
2. `VIBE_CHAT_LANGUAGE`, when the environment is safely readable or the current user explicitly sets it for the request.
3. The user's active conversational language.
4. The last clear user conversational language available in the current workflow context.
5. English.

- Apply this precedence to replies, progress updates, blocker and consent questions, summaries, and final responses.
- Read `VIBE_CHAT_LANGUAGE` as a natural language name or a BCP47 language tag such as `Japanese`, `ja`, `en`, or `pt-BR`; treat an unreadable, empty, or invalid value as unset.
- Never infer chat language from source artifacts, referenced plan or implementation files, filenames without locale markers, commands, skill invocations, code, identifiers, or host-wrapper text.
- Treat those inputs as language-neutral for chat unless the current user explicitly makes them the response-language contract.
- Preserve file paths, commands, identifiers, environment variables, locale tags, message keys, product names, canonical strings, and code verbatim unless the user explicitly asks to translate or rename them.
<!-- shared-contract:end language-precedence-chat -->

Chat-language selection controls only wrapper prose, progress updates, summaries, and confirmation questions; it does not translate the requested artifact or override exact-format output.

### Artifact Language

Choose artifact language by this precedence:

1. Explicit user instruction, including translation or localization requests.
2. Active workflow or artifact-specific language contract already selected for
   the requested artifact, including configuration-driven document-language
   settings.
3. Existing artifact language.
4. Filename locale markers such as `README.ja.md` or `docs/de_de/guide.md`.
5. Project convention.
6. English.

Do not reselect language from an existing artifact when an active workflow has
already resolved the artifact language. In that case, use the selected artifact
language for generated prose and preserve original-language source wording only
where it is a useful quote, term, identifier, or evidence anchor.

When the requested deliverable is the artifact itself, return the artifact
directly. Do not add process notes, source-read confirmations, "here is"
preambles, separators, change summaries, or placement instructions unless the
user asks for an explanation. The artifact's explicit language, existing
language, filename locale marker, or repository convention wins over chat
language. Internal evidence checks, source classification, and proof-source
decisions stay out of the delivered artifact unless the user explicitly asks for
that explanation.

The path, command, identifier, environment-variable, locale-tag, message-key, product-name, canonical-string, and code preservation rule above binds artifact and localized output as well as chat.

### Format And Exactness

For rewrite, polish, localization, comment, docstring, policy, template, and
other artifact-editing tasks, wrapper text is part of the output and can be
wrong even when the artifact body is right. Do not introduce task-frame phrases
such as `provided text`, `given context`, `as requested`, `rewritten below`, or
`made friendlier` around the artifact unless the requested artifact itself
requires that wording. Emit the revised artifact, or a requested change list,
without prompt-only provenance.

For LLM-first text, use line breaks as structure, not as an 80-column habit.
Keep short examples, commands, commit-message snippets, and compact list items on one physical line when the break would add no meaning.
Preserve required line breaks in verbatim output, quoted source, templates, logs, protocol payloads, JSON, and commit-message transport.

Treat commands as commands. Preserve `npm install`, `cargo test`, `pnpm build`,
and similar invocations without adding what they do, prove, fetch, generate, or
validate unless the source states it.

This applies in localized docs too: if the source only says `Run npm install`,
do not expand it to `Run npm install to fetch dependencies`.

Exact formats win. JSON, protocol payloads, parser-sensitive templates, PR
templates, release formats, and other machine-readable shapes must keep their
required structure with no extra prose, headings, Markdown fences, or invented
fields.

Removing an unsupported proposition means removing its semantic claim, not
only shortening its adjectives. In a fixed JSON or template shape, preserve the
required key, value type, and array/object shape while using a supported neutral
value or an empty value that the requested schema permits. Deleting only
promotional adjectives while retaining the underlying promise, or shortening a
future-benefit sentence into a future-benefit fragment, does not remove the
unsupported proposition. When a required string consists entirely of an
unsupported benefit, reduce it to a neutral topic label grounded in the
described object or action. When an optional array item consists entirely of an
unsupported claim, remove the item and preserve the array as empty rather than
keeping a shortened claim.

## Artifact-Specific Guidance

Read `references/artifact-guidance.md` when the deliverable is source comments or
docstrings, README/docs/guides/UI copy, a saved audit/report/postmortem, policy
or support copy, a changelog/release note, a PR description, a progress/final
summary, or a commit message. Its applicability routes to
`references/changelog.md` and `references/commit-messages.md` where detailed
format, proof-source, or transport rules are required.

Keep these invariants visible even before loading the reference:

- comments preserve non-obvious rationale and remove code narration;
- changelog entries follow repository format and record durable changed
  contracts, not iteration diaries or unsupported impact;
- progress/final summaries separate green checks from acceptance coverage,
  unresolved scope, and unverified shared edits;
- commit-message payloads are raw and unfenced, use durable proof, and leave
  staging/history authority with the owning workflow.

## Durable References

Artifacts should stand alone outside the prompt. Remove prompt-only references
or translate them into durable facts: `above`, `the provided text`,
`per plan1.md`, `as discussed`, local run labels, temporary files, unpublished
branches, and private checkout paths.

Keep durable citations when requested or useful for audit, rollback, or search:
issue IDs, incident IDs, public API names, ADR slugs, release versions, commit
SHAs, committed paths, stable design docs, primary-source URLs, and exact error
codes.

## Common Mistakes

- Optimizing for human polish when the next reader is an LLM that needs precise
  constraints.
- Replacing a supplied absence status with a vague placeholder.
- Upgrading `should` to `must`, weakening `must not`, or dropping exceptions.
- Translating commands, env vars, file paths, locale tags, or identifiers during
  documentation polish.
- Turning a supplied capability or command into an inferred purpose, cause,
  outcome, proof, or benefit.
- Summarizing or normalizing raw logs, exact tool output, or bare
  acknowledgments that should stay unchanged.
- Keeping filler such as `It's worth noting that`, `In conclusion`, or `Ultimately` when the transition adds no contract, evidence, or action.
- Replacing useful local anchors, order, tone, or examples with generic textbook wording.
- Wrapping a requested commit message in a Markdown code fence.
- Adding safety, security, performance, rollout, or support promises because
  they sound helpful.
- Treating a writing request as commit selection, or allowing an explicit commit to ignore exact
  templates, release rules, PR formats, staging procedures, or unrelated dirty
  paths.

## Self-Check

Before returning text, check:

- Did the artifact use the correct reader priority?
- Did all facts, scope, conditions, exceptions, warnings, required actions, and
  modality survive?
- Did unsupported reasons, benefits, impact, tests, security/performance claims,
  or rollout status sneak in?
- Did useful local anchors survive, and did hollow transitions disappear unless exact source text required them?
- Did exact-format output stay exact?
- Did locale and technical-token preservation rules hold?
- Did durable references replace prompt-only or machine-local context?
- For commit-message bodies, did the body use medium density and did
  verification lines preserve durable, review-useful proof instead of a session
  command transcript or local-only generated proof source?
- If text was written through a tool, did the stored artifact match the intended
  artifact? For created or amended commits with a body, inspect the stored
  message, not only the command used to create it.
