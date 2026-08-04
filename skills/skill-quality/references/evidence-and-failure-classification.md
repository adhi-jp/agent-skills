# Evidence and Failure Classification

Read this reference when the quality decision depends on relayed run summaries, session history, delegation, represented workflow state, executor evidence, structured public projections, runner affordances, or artifact proof transport.

## Evidence Intake

Start from the failure signal, not from a preferred rewrite. Collect only the
evidence needed for the current decision:

- Eval results, `benchmark.json`, `benchmark.md`, grader output,
  and human feedback.
- Relevant `SKILL.md`, references, scripts, README text, `CHANGELOG.md`, and
  eval definitions.
- Session-history excerpts when the user asks for history research or repeated
  failures are only visible in transcripts.
- Local plans or changelog entries that explain why current behavior exists.

Label implementation-affecting claims as `Primary source`, `Local
investigation`, `Unproven`, or `Accepted risk`. Do not treat old session
memory, a plausible fix, a single passing run, or a reviewer preference as proof.
If the evidence shows no contract gap, do not polish by default. Report that no
tracked change is needed and name the evidence that supports that decision.

For any proposal that creates or changes a skill or eval, make the decision
record explicit before recommending prose edits:

- A short evidence map labels the claims that justify the current proposal as
  `Primary source`, `Local investigation`, `Unproven`, or `Accepted risk`.
- A one-sentence reusable contract delta names the behavior and degeneration.
- Owning surfaces name both the smallest coupled edits and important surfaces
  that must remain unchanged.
- Proof status states what current evidence establishes and what requires a
  later authorized run or external check.
- For grader-only ground-truth repairs, distinguish adjudication context from
  output obligation: state which supplied facts the grader may recognize and
  which facts, if any, an independent output contract requires the executor to
  restate.
- When correcting a grader or artifact-level interpretation, keep the recorded
  official aggregate unchanged and label the corrected reading diagnostic until
  the grader, deterministic check, or proof boundary is fixed and rerun.

A no-change decision may stay concise, but identify the existing rule, eval, or
artifact that already owns the reported mechanism and keep unsupported proof
claims explicit. Do not require a formal evidence table or a new mutation merely
to make a no-change decision look complete.

When an eval result arrives as a relayed Claude Code, Codex, or other host-agent
summary, treat that prose as a pointer to verify, not as execution proof. Locate
the corresponding `benchmark.json`, `benchmark.md`, `iteration_manifest.json`,
`run.json`, `grading.json`, recorded outputs, or transcript evidence before
making root-cause, improvement, or changelog claims. If those artifacts are
unavailable, label the host summary as user-supplied evidence for the report
only and keep artifact-dependent claims `Unproven` or `Accepted risk`.

When session history is part of the task, split extraction work across
subagents when available. Give each agent a bounded session range or question,
have it write temporary per-session notes under `/tmp`, and synthesize the
patterns yourself before editing tracked files.

When delegated review, extraction, or benchmark analysis may affect a tracked
skill/eval decision, pass a compact quality lens to the delegate instead of
assuming this skill context transfers. Name the delegated mode, such as
contract review, eval hardening, benchmark triage, or history extraction; ask
for evidence, inferred risks, unsupported claims, what should not change, and,
for eval work, expected-output leakage, common assertion applicability, and
baseline plausibility. Do not require the full skill for narrow lookups.

For session-history audits, count actual skill use only when the record shows a
user trigger, assistant declaration, skill-body read tied to a substantive
decision, or decision behavior in a substantive task. Separate current audit
sessions, eval-runner sandbox sessions, search-command echoes, quoted skill
bodies, session metadata, and reference-only file reads from historical usage
evidence.

Before counting a session-history candidate as evidence, build a turn-level
inclusion ledger. For each candidate, record the session path, turn identifier
or boundary evidence, skill trigger/read/decision evidence, tracked patch
evidence, verification evidence or explicit verification absence,
classification, and any exclusion or low-confidence reason. Treat one user
request plus its directly associated assistant/tool/edit/verification sequence
before the next unrelated user request as the same turn. If the log cannot
support that boundary, or if skill-quality use, patches, and verification only
co-occur in different turns of the same JSONL file, mark the candidate
low-confidence or excluded instead of counting it.

When the audit is counting skill/eval edit sessions, a same-turn no-change
decision may be recorded separately as actual skill use, but it is not edit
evidence unless the same turn also has a tracked patch or an explicit
post-edit verification absence.

Planning or requirements-spec workflows remain primary when they are creating
plans or specs. Use this skill only as an auxiliary lens when that work turns
failures, session-history patterns, review comments, or benchmark evidence into
future skill behavior, acceptance criteria, eval discrimination, or
benchmark-proof requirements. Eval tooling work is relevant only when it affects
prompt delivery, grading fidelity, baseline compatibility, metric provenance,
artifact completeness, or report claims.

Before treating a surprising, repeated, tool-related, artifact-related, or
transcript-contradicted eval failure as a skill defect, classify the failure
surface: skill contract gap, eval assertion gap, measurement or recording gap,
prompt or invocation mismatch, grader-boundary issue, or run variance/noise. If
the classification points outside the skill contract, fix or record that
boundary instead of tightening skill prose.

Before interpreting executor behavior, bind the eval's evidence universe.
Distinguish a verified target workspace, runner-delivered fixtures,
user-provided or represented source material, and runner or harness
scaffolding. If the suite expects a closed supplied corpus but the prompt
ambiguously says `this project`, invites work "while you're in there", or
otherwise suggests that the ambient checkout is the represented application,
classify that as a prompt or invocation mismatch. Make the prompt or fixture
binding explicit instead of teaching the skill to ignore a legitimately bound
workspace. Conversely, do not accept ambient repository, sandbox, eval, or
runner state as evidence about represented code unless the prompt or artifact
provenance establishes that relationship.

Bind represented workflow state separately from executor action mode. A
response-only decision, command record, or closure description may legitimately
receive facts such as `edit complete`, `changes staged`, `verification passed`,
or `commit authorized` while also forbidding the executor from inspecting or
mutating the ambient sandbox. The prompt must make both axes explicit:

1. Which represented facts the answer should treat as established.
2. Which actions the executor may perform in this delivery mode.

Do not replace supplied workflow state with an empty or contradictory ambient
checkout merely because tools are available. Conversely, do not treat a
represented completed action as proof that the executor performed it. A
response-only restriction changes execution authority and proof, not the
represented workflow's required closure outcome; it does not silently turn an
authorized commit into an optional future suggestion or an uncommitted
checkpoint.

When an eval consumes structured internal inputs but asks for a public record,
bind three schemas separately:

1. The delivered input schema: what the executor may inspect.
2. The internal retained-state schema: what may exist for correlation or audit
   without becoming public.
3. The public output schema: what keys and values may be serialized.

Input availability does not authorize output reproduction. A prompt that asks
for a public projection must say whether accepted or rejected input arrays are
summary-only, whether internal provenance is retained, and which fields are
forbidden from public output. If repeated projection leakage survives skill
wording changes, fix the owning prompt, fixture, adapter, or structured-output
contract instead of adding another downstream reminder. Prefer deterministic
key and value checks for forbidden public fields when supported.

Also bind the eval's authority universe. Runner or host scaffolding can expose
an output path, tool, capability, fallback, or optional transport without
authorizing the executor to use it. Inspect the exact delivered prompt before
attributing a file write, tool call, scope expansion, or persistence choice to
the skill. If conditional scaffolding repeatedly induces behavior that the
represented user did not request, classify it as prompt or invocation authority
leakage and fix the owning transport contract. Make the affordance explicitly
non-authorizing and test that boundary symmetrically across configs instead of
adding stronger downstream skill prose to counter the runner-delivered
instruction.

After authority, bind the proof-transport universe separately. A capture
destination can be non-authorizing when the represented user or workflow does
not require an artifact, yet become required recording transport after an
artifact deliverable is independently authorized. Ask three separate questions:

1. May the artifact exist in this delivery mode?
2. What repository-relative path or stable handle is the artifact's logical
   identity?
3. Where must the complete artifact bytes be recorded so the grader can inspect
   them?

Do not collapse those answers. Writing in a chat-only or response-only case is
an authority or delivery-mode failure even when a capture path exists. In an
artifact-writing case, leaving the capture destination empty while writing only
to an unrecorded sandbox path is a measurement or recording gap, even when the
change manifest proves a file existed. Keep the logical artifact identity out of
temporary capture or sandbox paths, and test both the negative authority
boundary and the positive recording obligation.
