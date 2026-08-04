# Artifact-Specific Writing Guidance

Read this reference when the primary deliverable is source comments or docstrings, README/docs/guides/UI copy, a saved audit/report/postmortem, policy or support copy, a changelog/release note, a PR description, a progress/final summary, or a commit message. Read the more specialized changelog and commit-message references where routed below.

## Artifact Notes

### Source-code comments and docstrings

Preserve non-obvious rationale, invariants, compatibility rules, migration
notes, side effects, failure modes, intentional non-goals, performance tradeoffs,
and external constraints. Remove comments that only echo names, signatures,
types, or immediately visible code.

Public APIs may need intent, contracts, invariants, and non-obvious usage.
Internal comments should orient the next maintainer only when the code itself
does not.

### README, docs, guides, and UI copy

Match the artifact's reader. For human-first text, lead with what the reader can
do and keep the prose direct. For LLM-first docs or guides, prefer contract
clarity, stable anchors, and exact commands over editorial polish.

Do not add setup steps, support channels, availability promises, safety
rationales, or business value unless the source provides them.

For a saved audit, report, or postmortem, establish the subject, triggering
task/event, deviation, current status, and purpose using supplied facts and
durable anchors. Run a context-stripped-reader check; do not impose a universal
template or invent organizational context.

When correcting an unsupported claim, first freeze the strongest permitted
replacement claim from authoritative evidence. Include adjacent limitations
needed to prevent inference of the old broader promise. If none exists, state
the permitted boundary for review instead of replacing one overclaim with
another.

For support or policy copy, create warmth by clarifying supplied facts. Do not
add response guarantees, escalation paths, new channels, reassurance claims, or
security reasons.

### CHANGELOG and release notes

Follow the project's style. Each entry should answer what changed for the
reader. Internal refactors without user-visible impact usually belong in commit
history, not a changelog. Do not inflate a narrow implementation change into a
broad reliability, security, performance, or compatibility claim. Do not use
`CHANGELOG.md` as an iteration log; fold superseded run notes into the current
contract delta and latest verification status.

For changelog or release-note work, read `references/changelog.md` when the task
involves entry content quality, the next-agent contract-log reader model,
detecting and conforming to a repository's existing changelog format,
breaking-change presentation, durable references, local generated proof-source
boundaries, or converting commit or PR metadata into a changelog entry. That
reference separates the format layer (the repository owns the format; detect and
conform, never silently restructure it) from the content layer (write each entry
as a contract and evidence log for the next agent resuming with zero context)
and treats git-unmanaged generated reports, local-only run IDs, and private
tool-session records as non-durable changelog evidence.

If the requested changelog slice explicitly names `## [Unreleased]` and a
category such as `### Changed`, include those headings in the artifact. "Return
only the entry" excludes explanatory wrapper prose; it does not reduce a
requested section-shaped artifact to a bare bullet. Preserve the changed
package or skill name exactly, current verification facts that the source
supplies, and any unresolved accepted risk while removing superseded
run-by-run commentary.

When source material says an API, field, schema, command, or behavior was
removed incompatibly, mark the entry explicitly as breaking and preserve the
migration direction. Deprecation history or a `Changed` category does not by
itself communicate that callers must migrate.

### PR descriptions

Honor the requested or project template exactly. Fill unknown sections with the
explicit absence status when appropriate, and preserve supplied statuses such as
`Not run` rather than replacing them with `Not provided`.

### Chat replies, progress updates, and final summaries

Lead with the answer. Keep progress updates to one or two short sentences.
Final summaries should be brief when useful and absent when not needed. Give
depth when the user asks for rationale, verification, limitations, recovery, or
comparison. Avoid ritual closing offers, generic next steps, and template
sections when a short answer resolves the request.

For implementation, debug, review, or verification summaries, do not collapse
`green` into `complete`. Keep these facts separate when they differ:
`suite_status` (what ran and passed or failed), `acceptance_coverage` (which
core criteria or sentinels are proven, missing, stale, failed, or blocked),
`unresolved_scope` (product decisions, deferred findings, accepted residuals, or
out-of-scope items), and `unverified_shared_edits` (changed paths or delegated
edits without final receipt). Do not imply acceptance completion from test
counts, reviewer counts, screenshot counts, or a green suite alone.

Do not send state-change-free waiting updates merely because a poll or timeout
happened. A progress update needs a new result, blocker, policy change, user
decision, or user-requested periodic cadence.

Do not turn every progress update or final summary in an active workflow into a
separate primary writing workflow. Apply the writing rules to the text only
after the active workflow has determined what can be said.
When the active workflow has supplied the facts for an incidental progress
update or final summary and the user asks to send it, write the requested brief
message directly. Do not replace it with a skill-routing explanation or a
checklist about how writing should apply.
Answer how `vibe-writing` applies only when the user asks a meta question about
skill routing. When the user asks to send, draft, or return the progress update
or final summary itself, the deliverable is that message.
Do not treat "not a standalone writing deliverable" as a reason to withhold the
brief message; it only means the active workflow keeps authority over what the
message may say.

### Commit messages

For commit-message work, read `references/commit-messages.md` when the task
involves a body, Conventional Commit shaping, durable references, verification
provenance, release commits, dependency updates, monorepo/package changes,
i18n/localization, performance, CI/build/publishing, security/privacy/data-loss,
thin evidence, mechanical syncs, required trailers, compact bullets, or
multi-line commit-message transport.

For a multi-line commit message, use one message file, one editor buffer, or one
complete message payload. Do not use repeated `git commit -m` arguments for body
lines, bullets, verification lines, or trailers.

Before a `git commit` or an amendment for a message with a body runs while this
skill is active, apply `references/commit-messages.md` to the subject shape, body
value, message density, verification provenance, durable references, compact
bullets, trailers, and transport.

After creating or amending a commit with a body, inspect the stored message with
`git show -s --format=%B HEAD`. This post-commit inspection duty and any amend
belong to the workflow holding history authority under its consent rules;
`vibe-writing` supplies the corrected message artifact. If the stored message
violates this skill, the corrected message must be applied through that
workflow before completion is reported. That inspection includes checking that
`Verification:` is a compact proof section for the next reviewer, not a session
command transcript: each kept bullet should normally pair a stable evidence
anchor with the outcome and the changed contract, risk, or coverage it supports.
Omit that coverage phrase only when the command or suite name already carries
the useful scope, the commit is small enough that the proof meaning is obvious,
or the available evidence is too thin; in thin cases preserve the explicit
absence status instead of forcing a template. The body must not leak
git-unmanaged local generated artifacts, ignored result files, local-only run
IDs, or private tool-session records as proof sources. Pure message-drafting
tasks do not need this Git inspection because no stored commit artifact was
created.

When asked to diagnose a stored-message violation and show the correction,
state the defects and required history-authority follow-up, then present the
corrected commit-message payload without Markdown fences. The explanatory
diagnosis is not part of that payload. Remove fence bytes and replace any
git-unmanaged report, local run label, or private tool-session proof with a
durable reference or an explicit absence status such as `verification not
durably recorded`. The workflow holding history authority must apply the
corrected payload under its consent rules and rerun
`git show -s --format=%B HEAD` before reporting completion.

For commit-message bodies, default to a medium-density shape: enough durable
context for a future AI to recover the commit's intent, changed contract
surfaces, constraints, non-goals, and proof, but not a feature walkthrough or
file-by-file transcript. Use one to three short paragraphs or a few labeled
bullets before `Verification:` for ordinary commits. If a draft needs many
bullets or multiple long behavior sections, summarize by durable surfaces or
split the commit instead of stuffing implementation details into the message.

When the requested response combines a commit message, its transport, and
post-commit checks, keep those three surfaces distinct. Emit the commit-message
payload itself unfenced; a separate shell-command block may be fenced without
making those fence bytes part of the message. Use one complete message payload,
then include `git show -s --format=%B HEAD` and a committed-file-set inspection.
State that malformed stored bytes must be corrected by the workflow holding
history authority before completion is reported. The transport must be
executable rather than contain an unresolved placeholder path. In the message,
group changes by durable contract surface instead of file inventory, and make
each retained verification bullet state what the command proves when the scope
is not already obvious.

Before returning a combined commit record, audit each `Verification:` bullet:
if the command or suite name does not make the changed coverage self-evident,
append a compact outcome-and-scope phrase. Also state the stored-message failure
behavior explicitly: if `git show -s --format=%B HEAD` reveals malformed bytes,
the history-authority workflow must correct them before completion is reported.

When the requested deliverable is the commit message itself, return raw commit
message text: no Markdown fence, example label, or explanatory prose unless the
user explicitly asks for that wrapper. Do not include proof-source analysis,
local-artifact classification, separators, headings, or any other wrapper before
the subject or after the final body/trailer line.

Markdown fences become commit-message bytes when pasted into `git commit`, so
they contaminate subjects, bodies, and trailers.

When used with a commit-execution skill, that skill controls staging,
authorization, command safety, signing, release processes, and history mutation.
`vibe-writing` controls the commit message artifact: subject wording, body value,
verification wording, durable references, trailers, compact bullets, and
multi-line transport.

For a standalone tracked-text edit under this skill's scoped permission, apply
the same minimum commit safety: refresh dirty state, stage only owned paths,
inspect the staged diff, use a Conventional Commit message, and inspect the
stored message and committed file set. If any gate fails, report the reviewed
uncommitted state rather than silently saying commit instructions were absent.
