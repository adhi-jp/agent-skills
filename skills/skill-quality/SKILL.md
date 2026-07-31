---
version: 2.2.2
name: skill-quality
description: Use when making evidence-driven quality decisions for a skill package or its evals from benchmark results, grader feedback, review comments, session-history patterns, trigger failures, or quality regressions; especially when deciding what to change, what not to change, how to update assertions, or whether to rerun skill evals.
---

# Skill Quality

## Overview

Improve skills by translating observed failures into small, testable contract
changes. A good skill change explains when the behavior applies, what future
agents must do, how evals will catch regressions, and what evidence proves the
change helped.

This skill governs skill and eval quality decisions. It does not authorize
release preparation, version bumps, commits, generated workspace commits, or
unrelated package rewrites.

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

For any proposal that creates or changes a skill or eval, include a short
evidence map before the contract delta. Label the claims that justify the
current proposal, not only instructions for future subagents or graders. Typical
entries are: user request or supplied eval result as `Primary source`; local
transcript, file, or benchmark inspection as `Local investigation`; inferred
patterns or expected failure modes as `Unproven`; and known but accepted gaps as
`Accepted risk`.

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

## Evaluation Iteration Boundaries

Treat each benchmark as a measurement of one exact skill/eval/fixture state,
not as a floating verdict on the current working tree.

- Before a run, record the affected suite, target failure mechanism, relevant
  skill/eval/fixture paths, and the current change boundary (for example the
  working-tree diff or commit plus iteration manifest).
- A skill, assertion, prompt, fixture, or proof-path edit made after a run
  supersedes that run as closing evidence for the changed behavior. Keep the
  earlier result as historical evidence, but label the latest edit's effect
  `Unproven` until the affected suite runs again.
- Run only suites affected by the latest change unless a broader regression
  claim needs more coverage. Re-running unrelated suites does not repair a
  missing closing run for the changed suite.
- Before reporting or committing a measured improvement, verify that the
  cited closing run occurred after the last relevant tracked edit and that its
  manifest points to the intended model, configs, run count, and skill source.
- When suite assertions or case coverage changed between iterations, raw
  pass-rate movement is not an apples-to-apples trend. Compare retained
  contracts or mapped assertions, and report the coverage change separately.
- After changing a skill rule, prompt, assertion, evidence taxonomy, or output
  contract, run a contract-collision audit before the next closing run. Check
  activation and non-applicability rules, workflow steps, output contracts,
  examples, common and per-eval assertions, README text, and current changelog
  guidance for contradictory or stale obligations. A new rule that says a
  narrow answer may use a symbol anchor does not silently supersede an existing
  path-required assertion; a new supplied-source taxonomy does not leave old
  assertions calling the same material workspace-local evidence.

Maintain a compact iteration ledger during repair loops:

| Iteration | Artifact boundary | Target mechanism | Result/anomalies | Decision |
| --- | --- | --- | --- | --- |
| [run directory] | [diff/commit and affected paths] | [contract or measurement question] | [official result and flagged cells] | [keep, edit, rerun, variance, blocked] |

Stop launching more full-suite runs when the next run has no pre-registered
question or when failures move without a stable shared mechanism. More samples
can measure variance; they are not a substitute for deciding what the next run
is intended to prove.

## Failure To Contract

Before changing skill text or eval behavior, write a one-sentence contract
delta:

```text
When <trigger/context>, the skill should <observable behavior>, because <stable reason>, and it must not <known degeneration>.
```

Use that sentence to decide which files change. If the failure cannot be stated
as an observable contract, keep investigating instead of adding prose.

Good contract deltas name the abstract dimension behind the example:

- `current-slice blocker` instead of one display-name fixture.
- `artifact freshness` instead of one missing image path.
- `benchmark completeness` instead of one fake `Config B` row.
- `local-anchor preservation` from one phrase such as `header handoff`, while
  preserving the concrete anchor as evidence when useful.

After naming the abstract dimension, choose the owning artifact before adding
standing `SKILL.md` guidance.

## Diagnostic And Safety Findings

When the failure signal is a security analyzer, policy scanner, trust review, or
credential-handling warning, derive the warning's prohibited predicate before
choosing prose:

- Record the untrusted or sensitive source, the boundary it crosses, every sink
  it can reach, the behavior that makes the flow unsafe, and which layer can
  actually enforce the boundary. Treat the analyzer report as `Primary source`
  for what the analyzer alleges, not as proof that its root-cause account or
  remediation is correct. Verify the reported source-to-sink path in current
  repository artifacts as `Local investigation`; if that path cannot be
  verified, keep the root cause `Unproven` instead of teaching the skill to the
  scanner's preferred wording.
- Distinguish a wording gap from a data-flow, authority, or output-propagation
  gap. Calling content inert, adding an ignore-instructions reminder, or
  redacting only the final display does not close a finding when the same
  outsider-authored bytes still enter the same model context or when a
  preservation rule still requires a sensitive literal to reach another sink.
- Prefer prevention by construction at the earliest owned boundary: omit the
  unsafe payload, accept only a closed structural record, make the capability
  unavailable when isolation cannot be enforced, or block persistence until a
  safe reference replaces sensitive content. Use downstream warnings and
  redaction as defense in depth, not as proof that the original flow is gone.
- Make conflicting obligations explicit. Exactness, verbatim preservation,
  localization, reflection, and meaning-preservation rules apply only within
  their safe domain; they do not outrank credential, privacy, or trust-boundary
  controls. Audit chat output, saved artifacts, temporary state, reflected
  files, logs, commit messages, tool arguments, and delegated context as
  separate sinks when applicable.
- Run a contract-closure audit across the owning `SKILL.md`, references, README,
  changelog, eval prompts, fixtures, and assertions. Remove or revise stale
  current-contract text that still authorizes the flagged path. Historical
  release notes remain historical evidence and are not rewritten as current
  instructions.

If enforcement belongs to a host, adapter, or external service, state that
dependency as a capability requirement and define the fail-closed fallback.
Skill prose can require and report the boundary, but it cannot prove that the
host enforces it. Static validation proves artifact consistency only; it does
not prove scanner closure, runtime isolation, credential revocation, or absence
of undiscovered secret formats. Only a rerun of the reporting analyzer proves
that its warning cleared; another authoritative check may prove the underlying
safety property, but not that analyzer-specific outcome.

## Change Selection

Make the smallest coupled change that closes the contract gap:

- `SKILL.md`: trigger-independent behavior rules, scope boundaries, stop gates,
  and short decision rules.
- `references/`: heavy guidance, detailed checklists, domain variants, or
  reusable research that would bloat `SKILL.md`.
- `scripts/`: deterministic repeated work that agents keep rebuilding during
  eval runs.
- Structured outputs or pre-edit gates: contracts that must be enforced before
  a caller can proceed. Prefer these over doc-only promises when past failures
  show agents skipped the rule.
- `evals/<skill-name>/evals.json`: pressure cases and expectations that prove
  the new contract and guard old behavior.
- `README.md` and `CHANGELOG.md`: only when the changed behavior is described
  there or user-visible for this repository.

A fixture, anecdote, or local case mapped to a reusable dimension still needs
artifact placement. Put broad trigger-independent obligations in `SKILL.md`;
put heavier reusable guidance in `references/` with explicit applicability;
keep narrow pressure cases in evals or local notes; and touch README or
changelog only when they own or describe the behavior.

Treat instruction reachability as part of artifact placement. If a concise,
load-bearing invariant already exists only in a reference but repeated
artifact-level evidence shows agents miss the same mechanism after the
reference route should have applied, consider promoting the invariant—not its
full checklist—to `SKILL.md` while leaving detailed mechanics in the reference.
Require a repeated shared mechanism or other independent evidence before this
promotion; one miss, a moving single-run failure, or grader variance does not
prove that a reference is too hidden. After promotion, audit the body,
reference, README, changelog, and evals for duplicated or contradictory
authority.

When editing skill text, preserve modality, exceptions, exact paths, commands,
field names, local anchors, and absence statuses. Shorten only when the shorter
text keeps the same applicability, obligation, proof path, and failure behavior.

Do not bump `version` fields unless the user explicitly asked for release
preparation. Record unreleased behavior under `CHANGELOG.md` `## [Unreleased]`.
Keep frontmatter descriptions focused on trigger conditions. Do not summarize a
workflow there; agents may follow the metadata instead of loading the skill body.

## Eval Design

Update evals in the same change set as behavior changes. Evals should be
discriminating, observable, and hard to pass with the old failure mode.

- Prefer per-eval expectations for narrow behavior. Add a common assertion only
  when it is valid for every eval, including exact-format and verbatim-output
  cases.
- Before adding, changing, or keeping a common assertion, check the eval classes
  it will govern, including activation-only, exact-format, localized, verbatim,
  narrow-boundary, and no-change cases. Move scenario-specific stop gates or
  narrow behavior into per-eval expectations.
- For every conditional common assertion, state both its positive applicability
  predicate and its non-applicable result in grader-readable terms. Do not rely
  on the grader to infer that absent artifact sections, option payloads, source
  handling, language rules, or lifecycle proof should pass when the triggering
  surface is absent. The applicability predicate must be observable from the
  delivered prompt and recorded proof surface; otherwise move the assertion to
  the owning per-eval expectations.
- Classify each eval's delivery mode before writing expectations: executing
  changes, response-only decision or command plan, artifact creation/revision,
  closure-only, or blocked/no-change. Every expectation must be satisfiable and
  observable in that mode. Do not require performed commands from a
  response-only case unless the prompt explicitly requests the exact command
  sequence; do not require a complete plan body from a closure-only decision;
  and do not grade a blocked case as completed implementation.
- In a no-change or blocked case, allow the output to prove scope by naming an
  existing rule, eval, or artifact as sufficient and explicitly declining to
  edit it. Do not treat that no-change explanation as a proposed mutation, and
  do not require a new eval, doc, or skill edit merely to demonstrate that
  existing coverage already owns the failure mode.
- Verify that every declared fixture reaches the executor through the runner's
  copy contract. In this repository's git-backed tracked-only sandbox, a newly
  created but untracked fixture is excluded even when it exists in the source
  checkout. Treat a missing or excluded fixture as a fixture-delivery or
  measurement gap, not a skill failure.
- Before interpreting a missing-file or wrong-artifact response, compare the
  declared fixture set, source fixture dirtiness, sandbox copy strategy,
  excluded-path sample, and change manifest. If the intended target was absent
  and the executor substituted a nearby unrelated fixture, fix the prompt or
  fixture boundary rather than teaching the skill about the substituted
  example.
- Audit runner-provided affordances against the case's authority and delivery
  mode. A designated artifact destination, available tool, optional fallback,
  or conditional transport instruction must not become a request to create a
  file, invoke a capability, broaden scope, or persist state. When the harness
  intends capture or availability only, say so in the executor contract and
  add runner-level regression coverage; do not rely only on the target skill to
  negate the scaffold.
- Write expectations against visible output, files, commands, records, or
  decisions, not against style taste.
- For mechanically inspectable output properties, audit the recorded artifact
  directly and make the grader boundary equally explicit. Examples include
  forbidden absolute sandbox links, runner or eval-file citations, exact
  prefixes, missing required paths, file-change sets, and secret-like literal
  reproduction. A grader pass does not override contradictory output bytes,
  and runner `Sanity checks: OK` proves only the anomaly classes the runner
  computes, not every suite contract. If repeated graders miss a mechanical
  property, add a deterministic check when supported or sharpen the assertion
  with the concrete prohibited predicate without leaking the target answer to
  the executor.
- If the eval runner shows `expected_output` or an expected-output summary to
  the executor, keep that summary high-level: describe the evidence shape and
  output category, not the target decision or named contract. Put
  discriminating answer details only in grader-only assertions, fixtures, or
  hidden grader material so the baseline is not handed the target behavior.
- Apply that leakage discipline to your own contract delta and self-authored
  assertions, not only to delegated eval work: a `SKILL.md` line or
  self-authored assertion must not copy a grader assertion's wording or a
  literal prompt phrase verbatim. Name the abstract dimension (Failure To
  Contract) and keep the concrete phrase only as a labeled example.
- Include negative pressure for the degeneration that motivated the change:
  global skill lists, fake baselines, universal checklists, weak proof
  substitutes, unsupported claims, stale assumptions, or overfit fixture names.
- Keep baselines meaningful. A 100 percent pass rate for both `with_skill` and
  `without_skill` usually means the assertion is not discriminating.
- Do not hide grader ambiguity by loosening expectations. Clarify the assertion
  or add a programmatic check when the property is mechanical. When you relax or
  delete an assertion or a both-config-pass eval to clear a failure, record the
  discrimination lost and add a compensating assertion or an explicit `Accepted
  risk`.
- If an eval expectation encodes an unsupported product fact, correct the eval
  instead of teaching the skill to invent that fact.

### Eval Suite Compaction

Treat case-count reduction as an eval-quality change, not mechanical cleanup.
Before deleting, merging, or folding a case, inventory the current suite and
write a compaction ledger with:

- old case IDs and the abstract contract dimensions each guards
- the retained case, per-eval expectation, common assertion, or fixture that
  will carry each dimension
- discrimination lost, including distinct state, language, exact-format,
  no-change, failure, or proof-boundary pressure
- the decision: keep, merge, delete, or `Accepted risk`

Compress by contract overlap, not by a uniform case-count target. A narrow,
expensive, passing, or both-config-passing case may still be the only regression
guard for a known failure. Keep it when no stronger case naturally covers the
same behavior. Stop when the next cut would lose a distinct contract, require an
artificial multi-scenario prompt, or broaden a common assertion beyond every eval
class it would govern.

Prefer these compaction moves:

- remove a common assertion that is scenario-specific or vacuous on unrelated
  cases, after moving its pressure to the owning per-eval expectations
- merge cases only when one realistic prompt can exercise the combined behavior
  without becoming a harness-only matrix
- fold repeated expectations into their owning case while preserving the
  strongest observable positive and negative pressure
- remove a case when a stronger retained case covers the same contract and the
  lost input variation is explicitly recorded

After compaction, reconcile every old case to retained coverage or accepted
risk; update suite `purpose`, `coverage_notes`, and scoring notes if their
coverage description changed. Static validation proves schema and fixture
integrity only. Do not claim preserved discrimination, effectiveness, or cost
improvement without an authorized clean comparative rerun; if that rerun is not
performed, report it as not measured.

External eval prompts stay under `evals/<skill-name>/`; generated run output
stays under `evals/<skill-name>/workspace/<agent>/` and is not committed unless
the user explicitly asks.

## Running And Reading Evals

For this repository, use the shared runner:

```sh
python3 skills/skill-eval/scripts/eval_runner.py validate evals/<skill-name>/evals.json
python3 skills/skill-eval/scripts/eval_runner.py run evals/<skill-name>/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py report evals/<skill-name>/workspace/codex/iteration-N
```

Keep eval workflows provider-neutral and file-contract based. Do not make the
shared runner depend on local-only skill snapshots, one host's UI, or
Claude-Code-only paths.
For this repository's `with_skill` runs, use the authoritative source skill
package directly; do not substitute an installed host skill tool,
`.agents/skills` snapshot, `.claude/skills` link, or cached skill copy.

`run` drives execution, grading, aggregation, and reporting end to end. It
spawns fresh executor subprocesses with the prompt only, then fresh grader
subprocesses with the recorded output plus assertions. No agent hand-runs
prompts, hand-records outputs, injects token counts, or grades its own output.
`run` writes `iteration_manifest.json` and, per run, `prompt.md`,
`grader_prompt.md`, `outputs/`, `grading.json`, `metrics.json`, and `run.json`,
plus `benchmark.json` and `benchmark.md` at the iteration root.

`report <iteration-dir>` only re-renders `benchmark.md` from `benchmark.json`;
it must not start a server, open a browser, bind a port, write a PID file, or
leave a background process.

Treat missing metrics, missing grades, missing configs, failed or timed-out
executors, grader failures, omitted assertions, or reused legacy artifacts as
incomplete proof, not as a pass. Also treat an abnormal aggregate-metric shift
between runs — for example `mean_tokens` collapsing — or executor batching that
loses per-eval isolation as a stop-and-verify condition, not a pass.

When cells are excluded or unscored because an executor timed out, classify
whether the surface is runner/grader infrastructure, prompt or invocation,
runtime-cost/complexity, run variance, or a real skill behavior failure before
using the aggregate delta or editing skill prose. If excluded or timeout cells
hide targeted behavior, especially asymmetrically in `with_skill`, report those
evals as unmeasured or cost-risk evidence until a complete rerun or separate
scored artifact clears them; do not call the run clean or harmless merely
because the pass-rate aggregate omits the cells.

Runner artifacts prove what the runner invoked, recorded, graded, and
aggregated. When a claim or assertion depends on prompt delivery, host, tool,
delegation, file, artifact, metric, timing, or other execution proof, audit the
evidence surface and compare the proof requirement with the recorded output set
before reading the grade as a skill signal or making root-cause or skill-quality
claims. Inspect the recorded invocation, output artifact, metric source, or
equivalent non-response evidence. Final-response prose, copied invocation IDs,
role labels, and self-reported call counts are not execution proof unless
corroborated by recorded host or runner evidence or an equivalent non-response
artifact.

If a scored executor output is only a host-continuation stub, waiting message,
tool-use placeholder, or other unresolved async artifact, do not silently
remove the cell from the official aggregate or call it an infrastructure
exclusion. Classify it as a prompt, invocation, recording, or output-set
completeness surface, report the official aggregate with that caveat, and fix
the eval prompt, runner recording, or proof path before treating the adjusted
reading as measured improvement.

When you compute an adjusted aggregate that excludes a scored stub,
placeholder, timeout, or other anomalous cell for diagnosis, label it as
diagnostic only. Report the official runner aggregate first, list the excluded
cell ids/configs and exclusion criterion, and use the adjusted number only to
localize unmeasured or contaminated behavior. Do not replace the benchmark's
official result, mark the run clean, or use the adjusted reading as proof of
improvement until a clean rerun or separately scored artifact measures the same
behavior.

Pure graders stay bound to the suite assertions recorded for the run. The
change owner treats surprising, repeated, missing, ambiguous, or
both-config-passing grades as evidence to interpret before editing skill or
eval behavior.

Read the recorded executor output as well as the grade for the targeted
mechanism. When the bytes violate a mechanical assertion that the grader marked
passed, record a grader false positive and keep the run non-closing for that
mechanism even if the official aggregate and sanity summary are clean. Keep the
official aggregate unchanged; artifact-level contract audit determines whether
the run can support the narrower closure claim.

Before comparing two iterations, confirm whether their skill source, prompts,
fixtures, assertion set, and recorded proof surface are equivalent. If not,
state which contract changed and avoid presenting the aggregate delta as a
direct model or skill improvement. A newer run can validate the new contract,
but it does not retroactively isolate which prior edit caused the difference.

Treat eval execution as a data-boundary decision. Do not send private skill
packages, eval prompts, fixtures, outputs, or session excerpts to an external
agent or hosted service unless the user or project explicitly authorizes that
data movement. Prefer local file-contract workflows when privacy is unclear.

## Result Analysis

Compare behavior before declaring improvement:

- Which failures changed from fail to pass, and which old passes stayed intact?
- Did the baseline also pass? If yes, the eval may not prove the skill helped.
- Did a new or targeted eval show any of these? If so, inspect prompt leakage,
  expected-output summaries, named capability hints, assertion applicability,
  and whether the eval is regression-only before claiming skill value.
  - a high `without_skill` pass rate
  - both configs pass
  - a high `with_skill` rate whose magnitude of help is unreadable because the
    baseline delta was not measured or read
  - a baseline that improved after an eval edit
- Did token or time cost increase? Treat deltas as cost signals. Call them
  regressions only when transcript evidence, run data, or a predefined budget
  proves the cost is not justified by useful behavior.
- Were any targeted evals excluded, unscored, or timed out? If yes, read the
  aggregate as partial and identify which behavior is unmeasured before
  accepting a headline delta.
- Did a grader failure expose unclear assertions instead of a skill defect?
- Did a conditional common assertion explicitly tell the grader what happens
  when its triggering surface is absent, or did absence get misgraded as
  failure?
- Did the recorded output set contain the proof the assertion requires, or did
  the proof live only in host UI, private transcript, or unrecorded tool state?
- Did the skill overfit to a fixture, phrase, project class, or old session?
- Did the change create new obligations, dependencies, or workflow authority
  beyond the user's goal?
- For any compacted suite, does every old case map to retained coverage or an
  explicit accepted risk, and did the merge remain a natural skill prompt?
  Lost coverage is a regression even when every remaining eval passes.

If repeated wording-only contract changes do not move the targeted failure,
stop tightening prose. Inspect runner recording, prompt delivery, grader inputs,
assertion scope, output-set completeness, and run variance before another skill
text edit. When that stop condition becomes tracked behavior, add or propose
generic eval coverage for the retry-stop and proof-boundary rule instead of a
local-case checklist.

If a similar failure moves to a different eval after each targeted wording fix,
treat that as a moving-failure pattern rather than proof that every new cell
needs another local sentence. Compare the per-run and cross-run evidence first:
which assertions fail, whether the failed dimension changes direction, whether
with-skill remains near ceiling, and whether multi-run results show a stable
cell or only scattered single-run misses. If repeated runs show low-frequency
scatter, classify the surface as run variance, prompt or runner leakage, or
measurement boundary and stop editing skill prose. If repeated runs show a
stable shared mechanism, choose the broad owner and update that rule or eval
pressure once instead of adding per-cell patches.

If a targeted fix makes one eval pass while the same failure mechanism appears
in another eval, stop treating the remaining failure as a local wording problem.
Classify the shared mechanism, choose its owning artifact, and update the broad
rule or eval pressure that owns it before adding another per-eval wording patch.
Keep invalid placeholder text out of executable commands, final-answer
templates, and other user-copyable guidance; if a placeholder must be discussed
as evidence, label it as non-copyable evidence instead of a template.

If adding a missing recorded evidence artifact changes the outcome, describe
the prior result as a measurement-boundary correction or proof-path
reclassification unless a separate run isolates a skill-contract change as the
cause.

If a proof-path or runner-recording change and a skill-contract change land in
the same rerun, separate what the artifacts prove from what they cannot isolate.
A grader prompt or verdict that directly cites the new recorded evidence can
prove the proof path is functioning, but it does not by itself prove how much of
the pass-rate change came from the skill text, the runner evidence, grader
behavior, or run variance.

When the proof path, recording contract, assertion boundary, or skill text
changes, rerun before claiming improvement. Treat single-run headline deltas and
unstable baselines as caveats. If single-run results repeatedly show a moving
failure or a volatile baseline, use repeated runs or an equivalent separately
scored artifact before deciding whether to edit again; report per-run spread and
whether the same cell fails consistently. If an action happened but the proof
was not recorded, fix or downgrade the proof claim instead of making the agent
deny or hide the real action.

Do not claim quality, token, time, reliability, safety, or trigger improvement
unless the run data or review evidence proves that exact claim. Writing
`improved` or `optimized` specifically requires a closing rerun on a clean,
complete run — same eval set, per-eval isolation, complete metrics, both
configs; without it, label the effect `Unproven` or `Accepted risk` rather than
a pass.

## Degeneration Checks

Before finalizing, reject these common regressions:

- Broad rewrites that erase known-good contracts to fix one eval.
- Copying an old skill wholesale instead of recovering the minimal useful rule.
- Turning examples, fixtures, or session anecdotes into universal requirements.
- Promoting named pattern sections, domain-specific branches, fixture-derived
  checklists, or single-example taxonomies into `SKILL.md` unless multiple
  independent evidence sources or a user-approved scope make them part of the
  skill contract.
- Echoing grader-assertion wording or a literal prompt phrase verbatim into
  `SKILL.md` or a self-authored assertion instead of naming the abstract
  dimension.
- Pasting universal checklists into every workflow.
- Requiring a companion skill, model, server, browser, or network path when the
  skill should be self-contained or provider-neutral.
- Moving process details into the description field so agents follow metadata
  instead of reading the body.
- Weakening proof paths because they are expensive.
- Continuing wording-only contract tightening after clean reruns leave the
  targeted failure unchanged.
- Continuing per-cell wording patches when a failure moves across evals and
  repeated runs have not shown a stable skill-contract gap.
- Treating a failure that moves across evals after a targeted fix as a new local
  wording problem instead of a shared mechanism.
- Treating a data-flow or credential-propagation warning as a wording-only
  problem while the flagged source-to-sink path remains authorized elsewhere.
- Preserving exact or verbatim content across a sensitive sink without an
  explicit safety-precedence rule and a fail-closed path.
- Claiming that skill prose, static validation, or a synthetic fixture proves
  host isolation, credential revocation, or external analyzer clearance.
- Leaving invalid placeholder text in executable or user-copyable examples
  because nearby prose says to replace it later.
- Expanding common assertions so exact-format, localized, or verbatim cases
  become impossible to satisfy.
- Forcing every suite toward one numeric target, deleting narrow cases without a
  contract ledger, or replacing natural prompts with artificial multi-scenario
  matrices.
- Counting skipped, flaky, unavailable, self-graded, or incomplete evals as
  proof.
- Replacing the official runner aggregate with a diagnostic adjusted aggregate
  that excludes scored anomalous cells.
- Counting an unrerun or contaminated run — no closing rerun, collapsed
  aggregate metrics, or lost per-eval isolation — as proof of improvement.
- Calling a run "closing" when a relevant skill, assertion, prompt, fixture, or
  proof-path edit happened afterward.
- Comparing headline pass rates across changed assertion sets as though they
  measured the same denominator and contract.
- Treating a source-checkout fixture as delivered evidence without checking
  that the runner copied it into the executor sandbox.
- Requiring execution proof, full artifact content, or implementation completion
  from an eval mode that can only record a response-only decision, closure, or
  blocker.
- Treating an ambiguous represented project as the ambient runner checkout, or
  repairing that prompt-boundary defect with more skill prose.
- Treating a runner path, tool, fallback, or transport affordance as user
  authority, or trying to cancel that authority leakage only with downstream
  skill wording.
- Treating non-authorizing capture transport as optional after the represented
  workflow independently requires an artifact, leaving the grader without the
  complete deliverable while a sandbox-only copy exists.
- Encoding conditional common assertions without an explicit observable
  applicability predicate and non-applicable result, so graders fail cases
  solely because an irrelevant surface is absent.
- Promoting an entire reference checklist into `SKILL.md` after one miss, or
  keeping a repeatedly missed load-bearing invariant reference-only without
  evaluating instruction reachability.
- Calling a run contract-clean because the grader and sanity summary passed
  while recorded output bytes violate a mechanically inspectable assertion.
- Adding a new rule or evidence taxonomy without checking for collisions with
  existing applicability rules, output contracts, examples, and eval
  assertions.

## Self-Check

Before reporting completion:

- Is the failure signal tied to evidence, not guesswork?
- Did surprising, repeated, tool-related, or artifact-related eval failures get
  classified by failure surface before skill text changed?
- For analyzer or safety findings, does the owned skill/eval contract stop
  authorizing the prohibited source-boundary-sink path, or was it only
  relabeled? If runtime enforcement is host-owned, is the actual runtime
  property still reported as unproven?
- Did exactness, preservation, and reflection obligations get checked for
  conflict with credential, privacy, or trust-boundary controls at every
  applicable sink?
- If enforcement is host-owned, is the capability requirement and fail-closed
  fallback explicit, with scanner/runtime closure still labeled unproven?
- Does each execution-proof assertion have recorded host, runner, or equivalent
  artifact evidence rather than prose-only IDs or counts?
- Is there a contract delta before changing skill text or eval behavior?
- Are examples mapped to reusable dimensions?
- Did each mapped dimension pass the artifact-placement gate before becoming
  always-visible `SKILL.md` guidance?
- Did wording edits preserve modality, exceptions, anchors, and absence
  statuses?
- For eval compaction, did the ledger reconcile old cases, replacement coverage,
  lost discrimination, and accepted risks before deletion or merge?
- Did the smallest coupled files change, including evals and changelog when
  required?
- Are baseline, grader, token, timing, and report claims honest?
- Did the cited closing run occur after the last relevant edit, and does the
  iteration ledger identify what that run was intended to prove?
- If iterations changed prompts, assertions, fixtures, or proof surfaces, were
  coverage changes separated from raw score movement?
- Are declared fixtures present in the executor sandbox under the runner's copy
  contract, not merely present or untracked in the source checkout?
- Can every assertion be satisfied from the eval's delivery mode and recorded
  proof surface?
- Is the represented evidence universe explicitly aligned with the executor's
  actual workspace and delivered fixtures, without accidental ambient-checkout
  substitution?
- Are runner and host affordances explicitly non-authorizing unless the
  represented user or owning workflow independently permits their use?
- After artifact authority was established, did the proof path separately bind
  the logical artifact identity and the destination that must contain complete
  grader-visible bytes?
- Do conditional common assertions state an observable applicability predicate
  and what passes by non-applicability instead of requiring the grader to infer
  it?
- If a reference-owned invariant was promoted or kept reference-only, is that
  placement supported by repeated reachability evidence rather than one noisy
  cell?
- Did targeted mechanical assertions get checked against recorded output bytes,
  not only grader verdicts or the runner sanity summary?
- After the latest edit, did a contract-collision audit remove stale or
  contradictory rules, examples, evidence labels, prompts, and assertions?
- For a no-change or blocked case, did the grader distinguish naming an existing
  sufficient artifact from proposing an edit, and avoid requiring a new
  mutation solely as proof?
- If any adjusted aggregate excludes anomalous cells, is it labeled diagnostic
  and kept separate from the official runner result?
- Are generated workspaces left uncommitted?
- Did you avoid version bumps unless this is release preparation?

For historical patterns behind these rules, read
`references/session-patterns.md` when the task asks for rationale or when a
change feels like it could make the skill larger but not better.
