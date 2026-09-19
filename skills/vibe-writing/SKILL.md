---
version: 3.1.0
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

The artifacts this phase owns are the text deliverables the request names,
including a rewrite, polish, or localization of one; decision records and
findings reports follow `Durable Records`, which declares their paths.

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

### Auxiliary Wording Mode

When another workflow is active, use this skill only for wording unless the user
asks for a standalone writing deliverable. The active workflow keeps authority
over scope, verification, release, and commit decisions.

## Scope Boundaries

Do not rewrite text whose value is exactness: verbatim tool or log output,
protocol snippets, quoted source, or a bare acknowledgment. Relay it unchanged
or answer around it. For transient progress text, stay brief and do not polish
raw logs into summaries unless asked.

## Reader Priority

Default to LLM-optimized development text: state facts, contracts, constraints,
and proof directly; keep useful stable anchors; remove filler; and state absence
explicitly. Use human-optimized prose when the artifact is mainly for people,
such as end-user docs, UI copy, support copy, or public release notes.

## Evidence And Meaning

Do not invent reasons, goals, outcomes, impact, tests, security/performance,
rollout, or risk-reduction claims. A supplied capability is not evidence of its
cause, purpose, effect, proof, or benefit.

Treat represented workflow state in the current prompt as supplied evidence.
When a response-only task says changes are staged, an edit is complete, a check
passed, or another workflow fact is already established, write from that
represented state. Do not replace it with the eval sandbox's, runner's, or
ambient checkout's current state unless the prompt explicitly binds that
checkout as the target to inspect. If the task asks only for a message, command sequence, or closure record, do not
perform a represented mutation merely because tools are available. Describe
commit mechanics only when the represented current request selects a commit or
an owning workflow's checkpoint closes over the represented changes.

Preserve facts, scope, conditions, exceptions, warnings, required actions,
meaningful order, and modality. Keep useful local terms and identifiers when
they are search anchors, workflow labels, contracts, or domain language. A
cleaner sentence that changes obligation, applicability, permission, or failure
behavior is wrong.

## Language And Format

### Chat Language

<!-- shared-contract:begin language-precedence-chat source=shared/vibe-contract.md -->
**Resolve the language of user-facing chat text separately from any artifact's language, in this order:**

1. An explicit current-user instruction for chat, response, or output language.
2. `VIBE_CHAT_LANGUAGE`, a language name or BCP47 tag such as `ja` or `pt-BR`, when readable or set by the user for this request; an empty or invalid value is unset.
3. The user's active conversational language, else the last clear one in this workflow.
4. English.

- Never infer chat language from artifacts, file contents, paths, commands, code, skill invocations, or host-wrapper text unless the user makes them the language contract.
- Keep paths, commands, identifiers, environment variables, locale tags, message keys, product names, and code verbatim unless the user asks to translate them.
<!-- shared-contract:end language-precedence-chat -->

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

Artifact language does not follow chat language. Keep what `Chat Language`
keeps verbatim, plus canonical strings, unless translation or renaming is
requested.

### Format And Exactness

Return an artifact directly, without prompt-only wrapper prose or provenance,
unless explanation is asked. Preserve required line breaks,
commands, and machine-readable structure; exact formats permit no extra prose or
invented fields. Remove an unsupported claim semantically, while retaining the
required schema with a supported neutral or empty value where permitted.

## Artifact-Specific Guidance

Read `references/artifact-guidance.md` for artifact-specific rules. It routes
changelog and commit-message work to their detailed references. Decision records
and findings reports follow `Durable Records`.

## Durable References

Artifacts should stand outside the prompt. Replace prompt-only references and
machine-local context with durable facts or useful resolvable citations.
