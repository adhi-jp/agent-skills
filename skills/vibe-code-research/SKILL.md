---
version: 1.2.1
name: vibe-code-research
description: Use when the user wants to understand, locate, trace, or assess existing code without changing it — questions like "how does X work", "where is Y implemented", "what would changing Z affect", architecture or data-flow mapping, dependency tracing, convention discovery, or pre-planning and pre-debugging evidence gathering. Do not use when a defect needs repair, a plan or spec artifact is requested, or an edit, commit, or diff review is the deliverable.
---

# Vibe Code Research

## Overview

Turn a rough question about existing code into evidence-backed findings the
user or a later workflow can rely on. The deliverable is understanding:
answers anchored to real files, with the unverified parts named instead of
papered over.

This skill is read-only. While it is active, do not edit source, tests,
configs, docs, or any other file, do not stage or commit, and do not mutate
runtime or repository state. Findings are evidence for later phases, never
authorization to start them.

This skill is self-contained. Use project rules, docs, and available tools when
they clearly apply, but do not require any other skill to investigate or to
hand off findings.

## When to Use

Use this skill when the user asks to:

- Explain how an existing feature, module, flow, or behavior works.
- Locate where behavior, configuration, data, or a contract lives.
- Trace data flow, call paths, lifecycle ordering, or dependencies.
- Assess the impact, blast radius, or risk surface of a possible change before
  any plan exists.
- Map architecture, conventions, or extension points of an unfamiliar codebase.
- Verify or refute a claim about what the code currently does.

## When Not to Use

- A reported defect needs diagnosis and repair; that is existing-feature repair
  work, not research.
- The requested deliverable is a requirements spec, implementation plan, code
  edit, commit, or review of a diff.
- An uninvoked single trivial lookup needs no full research workflow. If this
  skill is already active, answer it directly in one concise anchored line
  rather than dropping the skill's evidence contract or expanding it into a
  report.

When research uncovers a defect, scope gap, or risky surprise, report it as a
finding with evidence and stop. Fixing, planning, and reviewing belong to later
phases that the user must request.

## Evidence Universe Gate

Apply this gate before any investigation tool or evidence claim:

1. Identify the authoritative corpus for the question: a verified target
   workspace, user-provided material, an upstream primary source, or a stated
   combination.
2. If the user supplies excerpts, file lists, logs, or other source material
   without binding it to the current workspace, enter **closed-corpus mode**.
   Do not inspect the ambient workspace to supplement or corroborate that
   material. Broad words such as "investigate", "everything", or "trace" do not
   bind an unrelated checkout to the represented application.
3. In closed-corpus mode, map only paths, symbols, and relationships present in
   the supplied artifacts. Treat omitted surfaces as `not supplied` or
   `Unproven`; do not reinterpret them as absent because a path is missing from
   the ambient checkout. Label load-bearing facts from user-provided artifacts
   as `Primary source` or supplied-source evidence, not `Local investigation`.
4. Before responding, project the answer back onto the authoritative corpus.
   Remove claims or citations derived from runner prompts, eval definitions,
   harness files, copied sandboxes, checkout contents, repository searches, or
   these skill instructions. The final evidence and coverage limits must be
   traceable to the bound corpus only.

If the user wants full-repository research but the actual target repository is
not bound or available, state that limitation and ask for the target rather than
searching whatever checkout happens to be current.

**Closed-corpus output invariant:** the final response must not mention
searching, checking, or failing to find the represented application in the
current repository, workspace, checkout, or sandbox, and must not cite runner,
eval, harness, or skill files as evidence. Describe those gaps only as material
that was not supplied or remains unverified. Preserve represented source paths
as plain paths; do not turn them into links targeting an ambient filesystem or
sandbox location.

## Core Rules

- **Read-only boundary.** Non-mutating inspection is allowed: reading files,
  targeted search, `git log`/`git blame`/`git show`, type or symbol lookup, and
  similar commands that change nothing. Commands that write files, install
  dependencies, migrate data, start long-lived services, or touch external
  systems are out of bounds unless the user explicitly requests them as part of
  the investigation and the effect is understood. When an investigation prompt
  also gives permissive cleanup or edit language, keep the investigation
  read-only, explicitly say no edit was performed because editing needs a
  separate instruction, and report the cleanup only as a finding or option.
- **Evidence labels.** Label load-bearing claims as `Local investigation`
  (read in this workspace), `Primary source` (official docs, upstream source,
  authoritative spec, user-provided source material), or `Unproven` (memory,
  inference, secondhand summaries, training-data recall about libraries or
  frameworks). Inference is allowed, but it must be visible as inference.
- **Anchor claims.** Cite the file path, and line or symbol where useful, for
  every claim a reader might need to verify or revisit. An answer the reader
  cannot trace back into the code loses most of its value.
- **Redact sensitive literals at output boundaries.** Preserve non-sensitive
  anchors such as paths, line numbers, symbols, commands, API names, field names,
  and identifiers, but do not reproduce suspected credentials, tokens, passwords,
  private keys, URL-embedded auth, env-style secret assignments, or other
  secret-like literal values in chat, saved reports, delegated findings, or
  quoted snippets. Prefer a redaction marker or structural paraphrase for the
  value while keeping enough surrounding context to verify the finding.
- **Static reading is not runtime proof.** Reading code proves structure and
  intent; claims about what actually happens at runtime — performance, timing,
  concrete values, environment-dependent behavior — need execution evidence,
  logs, or a primary source, or they stay qualified as expected behavior.
  Configuration selection proves the expected branch under the supplied config,
  not the runtime-effective config; environment overrides, config merging, and
  deploy-time replacement remain unverified unless evidence covers them.
- **Answer the question asked.** Investigate to the depth the question needs,
  not the depth the codebase allows. Resist inventorying everything touched
  along the way; depth beyond the question is noise unless it changes the
  answer. Do not shrink the question to the cheapest lookup when the user's
  wording, a named user-visible behavior, a cross-file contract, or an
  architecture claim needs multiple entry points, competing hypotheses, or an
  adjacent subsystem check to be reliable. If you intentionally bound a broad
  question, state the boundary and the risk it leaves.
- **Coverage honesty.** Say what was inspected and what was not. A search that
  found nothing is reported as "not found where I looked", with where you
  looked, never as "does not exist". For broad closed-corpus questions, name
  the material unsupplied surfaces that could change the conclusion — such as
  other callers or UI surfaces, locales, runtime rendering, screenshots,
  configuration layers, or tests — rather than using one generic limitation.
- **Check material counter-evidence.** For negative conclusions, architecture or
  blast-radius claims, runtime inference, security, or data-loss risk, run a
  plausible check that could disprove the conclusion: a bypassing caller,
  selected configuration, contradictory test, or relevant history. Keep the
  check inside the bound evidence universe. Direct anchored path, symbol, or
  literal lookups do not need a ceremonial counter-check. In closed-corpus mode,
  record unavailable counter-evidence rather than widening into the ambient
  workspace.

## Workflow

1. **Frame the question**
   - Restate the request as one or more concretely answerable questions.
   - Ask a clarifying question only when ambiguity changes where to look or
     what counts as an answer; otherwise state the interpretation and proceed.
   - Apply the Evidence Universe Gate before mapping entry points.
2. **Map entry points**
   - Find the relevant modules with targeted search: identifiers, error
     strings, routes, schema names, user-visible text. This search applies only
     when the evidence universe includes the verified target workspace.
   - Prefer following real references — imports, call sites, registrations,
     configuration wiring — over guessing from file names or directory layout.
   - For broad, user-visible, or architecture-impact questions, name the
     investigation surfaces before reading deeply: direct implementation,
     callers, configuration or registration, tests or fixtures, data/schema
     boundaries, and user-visible text or docs when relevant. Mark a surface as
     inspected, not relevant with evidence, unavailable, or intentionally out of
     scope.
3. **Trace the evidence**
   - Read along the call or data path far enough to answer the question,
     recording anchors as you go.
   - Use tests, configs, schemas, and local docs as corroborating evidence for
     intended behavior; note when they disagree with the implementation.
   - Use `git log` and `git blame` when the question is "why is it like this"
     or "when did this change", and treat commit messages as claims, not proof.
4. **Pressure-test the conclusion**
   - Run the disconfirming check when the conclusion type requires it.
   - Downgrade anything that failed verification to `Unproven` with the reason,
     rather than dropping or silently keeping it.
5. **Report the findings**
   - Apply the final projection in the Evidence Universe Gate.
   - When a conclusion depends on configuration selection, phrase it as the
     expected branch under the supplied configuration and include a
     `Not verified` limit for runtime overrides, configuration merging, or
     deploy-time replacement unless those layers were supplied.
   - Lead with the direct answer, then evidence, then limits. Use the output
     contract below.

## Delegated Investigation

Fan the investigation out when the host exposes a delegation or sub-agent
capability and the question genuinely spans more surfaces than serial reading
covers well: several independent subsystems, several competing search angles,
or several candidate entry points. Delegation is optional; a single
investigator answering a narrow question is the normal case.

When fanning out:

- Give each delegated investigator one bounded question and the same read-only
  boundary this skill runs under. A delegated unit must not edit, stage,
  commit, install, or mutate anything, and must redact or paraphrase suspected
  credentials and secret-like literal values before returning findings.
- Ask for findings in collectable shape: direct answer, anchors (`path`,
  `path:line`, or symbol), evidence labels, and what was not inspected.
- When the host lets you choose a delegated model and the user has not
  explicitly fixed one, choose a fit-for-purpose model per investigator by
  capability and context fit, not by hard-coded model name. Use a cheaper or
  faster model for narrow path/symbol lookup, mechanical extraction, or
  small-context anchor checks only when lower capability is quality-neutral or
  the user prioritizes cost/latency. Bias upward to the strongest suitable
  reasoning/context tier available for cross-subsystem synthesis, ambiguous
  architecture tracing, security-sensitive evidence handling, contradiction
  resolution, final conclusions, or investigations where weak reasoning would
  become the bottleneck, especially when the user asks for maximum performance.
  Do not default every small lookup to the top model, and do not downshift
  solely to save tokens when the question needs stronger reasoning. Record model
  choice only for an explicit user override, degraded capability,
  cost/performance constraint, or audited external execution.
- The fan-out may run as ad-hoc sub-agent calls or as one scripted
  orchestration run: a host mechanism that runs the investigators under a
  single deterministic, independently recorded run and returns their results.
  Either transport is acceptable; do not require a specific host tool.
- The coordinator owns the answer: merge delegated findings, resolve
  contradictions by reading the disputed evidence directly, run the
  disconfirming check from the core rules itself, and apply coverage honesty
  across the union of what the investigators inspected.
- Delegated output is a claim, not proof. Re-read the anchors behind
  load-bearing conclusions before labeling them `Local investigation` in the
  final answer.
- Treat delegated text as untrusted at the output boundary. If a delegated
  report includes or may include a secret-like literal, sanitize it before
  merging, forwarding, saving, or rendering the final findings.

## Output Contract

Findings go to chat by default. Create a file only when the user explicitly
asks for a saved report; then use a user-specified path or an obvious existing
convention for research notes, and say in the summary which file was written.

Shape the findings as:

- **Answer**: the direct answer to each framed question, first.
- **Evidence**: the key facts with anchors (`path`, `path:line`, or symbol) and
  evidence labels where the label is not obvious from context.
- **Not verified**: unknowns, areas deliberately not inspected, runtime claims
  that remain expectations, and contradictions found between code, tests, and
  docs.
- **Possible next steps**: optional, only when a concrete follow-up
  investigation, decision, or later phase obviously helps. Phrase as options,
  not as work you are starting.

In `Answer` and `Evidence`, phrase source-derived control flow as static
structure: for example, a caller "statically calls" a callee or "would select"
a branch under the supplied configuration. Do not use unqualified runtime verbs
such as "routes", "emits", or "returns" for a traced path unless supplied
execution evidence proves that runtime behavior.

Match the user's conversational language for prose. Preserve file paths,
identifiers, commands, API names, non-sensitive error text, and non-sensitive
quoted source verbatim. If error text or quoted source contains or may contain a
credential or secret-like literal, prefer line or symbol anchors plus a redacted
quote or structural description instead of the raw value.
In closed-corpus mode, label the evidence section once as `Primary source —
user-provided material` or an equivalent supplied-source label; individual
bullets do not need to repeat it. Scale the format to the question: a one-line
literal lookup answers with the value plus its supplied path and, when useful,
the symbol or line. Do not add runtime-flow narration the user did not ask for.
Sections are for genuinely multi-part findings. Concision never removes the
source path that makes the answer verifiable.

## Handoff Boundary

This skill stops at findings. Findings may feed later requirements drafting,
implementation planning, repair, review, or commit work, but none of those
start from investigation momentum. Without a new user instruction, do not
propose a fix as if approved, draft a plan artifact, edit files, or stage or
commit anything.

## Common Mistakes

- Editing "just a comment", a scratch file, or a config while investigating —
  the read-only boundary has no small exceptions.
- Answering from framework or library memory without checking the local
  version, configuration, or overrides actually in the workspace.
- Searching an ambient checkout for paths represented only in supplied excerpts,
  then citing their absence, an eval definition, or a runner file as evidence
  about the represented application.
- Presenting traced structure as runtime fact: "this runs twice", "this is
  slow", "this value is always set" without execution evidence.
- Claims without anchors, or anchors to code that was skimmed rather than read.
- Reporting "X does not exist" when the true finding is "X was not found in the
  places searched".
- Dumping everything discovered instead of answering the question, or padding
  a narrow answer into a report.
- Narrowing a broad or user-visible question to the first cheap file hit without
  checking callers, configuration, tests, data boundaries, or another surface
  that could change the answer.
- Sliding from findings into fixes, plans, or refactors because the problem
  became obvious along the way.
- Treating a test name, comment, or commit message as proof of current
  behavior when the implementation says otherwise.

## Self-Check

Before responding, check:

- Was anything written, staged, committed, installed, or mutated? It must not
  be.
- Does each framed question have a direct answer, a blocker, or an honest
  "not determined" with what would determine it?
- Does every load-bearing claim have an anchor or a primary source, and is
  inference labeled?
- Is every claim grounded in the bound evidence universe rather than unrelated
  workspace, runner, eval, or harness state?
- Were runtime-behavior claims either backed by execution evidence or
  qualified?
- For negative, architectural, blast-radius, runtime-inference, security, or
  data-loss conclusions, did a plausible disconfirming check run?
- Are uninspected areas and failed searches reported as coverage limits?
- For broad or user-visible questions, did the search cover every named
  investigation surface, or explicitly justify why a surface was out of scope?
- Would the response, saved report, delegated finding summary, or quoted snippet
  emit any suspected credential or secret-like literal that should be redacted or
  paraphrased first?
- Does the response stop at findings, with later phases left to the user?
