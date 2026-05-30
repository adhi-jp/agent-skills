---
version: 1.0.0
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

- Eval results, `benchmark.json`, `benchmark.md`, `review.html`, grader output,
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
sessions, search-command echoes, quoted skill bodies, session metadata, and
reference-only file reads from historical usage evidence.

Planning or requirements-spec workflows remain primary when they are creating
plans or specs. Use this skill only as an auxiliary lens when that work turns
failures, session-history patterns, review comments, or benchmark evidence into
future skill behavior, acceptance criteria, eval discrimination, or
benchmark-proof requirements. Eval tooling work is relevant only when it affects
prompt delivery, grading fidelity, baseline compatibility, metric provenance,
artifact completeness, or report claims.

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
- Write expectations against visible output, files, commands, records, or
  decisions, not against style taste.
- If the eval runner shows `expected_output` or an expected-output summary to
  the executor, keep that summary high-level: describe the evidence shape and
  output category, not the target decision or named contract. Put
  discriminating answer details only in grader-only assertions, fixtures, or
  hidden grader material so the baseline is not handed the target behavior.
- Include negative pressure for the degeneration that motivated the change:
  global skill lists, fake baselines, universal checklists, weak proof
  substitutes, unsupported claims, stale assumptions, or overfit fixture names.
- Keep baselines meaningful. A 100 percent pass rate for both `with_skill` and
  `without_skill` usually means the assertion is not discriminating.
- Do not hide grader ambiguity by loosening expectations. Clarify the assertion
  or add a programmatic check when the property is mechanical.
- If an eval expectation encodes an unsupported product fact, correct the eval
  instead of teaching the skill to invent that fact.

External eval prompts stay under `evals/<skill-name>/`; generated run output
stays under `evals/<skill-name>/workspace/<agent>/` and is not committed unless
the user explicitly asks.

## Running And Reading Evals

For this repository, use the shared runner:

```sh
python3 scripts/eval_runner.py validate evals/<skill-name>/evals.json
python3 scripts/eval_runner.py prepare evals/<skill-name>/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 scripts/eval_runner.py record <run-dir> --outputs <outputs> --total-tokens <n> --duration-ms <n> --output-chars <n>
python3 scripts/eval_runner.py prepare-grading <run-dir|iteration-dir>
python3 scripts/eval_runner.py grading-template <run-dir>
python3 scripts/eval_runner.py record <run-dir> --grading <grading.json>
python3 scripts/eval_runner.py doctor <iteration-dir> --require-complete
python3 scripts/eval_runner.py aggregate <iteration-dir>
python3 scripts/eval_runner.py report <iteration-dir>
```

Use the generated `prompt.md` for execution. Current-contract `prepare` output
is executor-safe and does not include `grader_prompt.md` or assertion-bearing
`eval_metadata.json`; run `prepare-grading` only after executor outputs and
`outputs/run_receipt.json` exist. For custom workspace roots outside
`evals/<skill-name>/workspace/<agent>/iteration-N`, pass `--evals-json <path>`
to `prepare-grading`. Use the generated `grader_prompt.md` for a separate
grading pass when supported. `grading.json` must preserve every prepared
assertion text exactly once, in order, with `text`, `passed`, and `evidence`.

Reuse baselines only through compatible same-agent fingerprints. Treat missing
timing, missing grades, missing configs, or reused legacy artifacts without
fingerprints as incomplete proof, not as a pass. `report` is static by default;
do not start a server or leave a background process unless the user requested an
opt-in server workflow.

Prepared runner artifacts prove intended runner state, and saved outputs prove
what was recorded. Actual prompt delivery for manual agent runs requires an
invocation log, copied task prompt, subagent transcript, matching prompt
receipt, or equivalent evidence. Without that proof, label prompt mismatch as
`Unproven` or `Accepted risk` and choose a rerun or other proof path before
making root-cause or skill-quality claims.

Pure graders stay bound to the prepared assertions. The change owner treats
surprising, repeated, missing, ambiguous, or both-config-passing grades as
evidence to interpret before editing skill or eval behavior.

Treat eval execution as a data-boundary decision. Do not send private skill
packages, eval prompts, fixtures, outputs, or session excerpts to an external
agent or hosted service unless the user or project explicitly authorizes that
data movement. Prefer local file-contract workflows when privacy is unclear.

## Result Analysis

Compare behavior before declaring improvement:

- Which failures changed from fail to pass, and which old passes stayed intact?
- Did the baseline also pass? If yes, the eval may not prove the skill helped.
- Did a new or targeted eval have a high `without_skill` pass rate, both
  configs pass, or a baseline improve after an eval edit? Inspect prompt
  leakage, expected-output summaries, named capability hints, assertion
  applicability, and whether the eval is regression-only before claiming skill
  value.
- Did token or time cost increase? Treat deltas as cost signals. Call them
  regressions only when transcript evidence, run data, or a predefined budget
  proves the cost is not justified by useful behavior.
- Did a grader failure expose unclear assertions instead of a skill defect?
- Did the skill overfit to a fixture, phrase, project class, or old session?
- Did the change create new obligations, dependencies, or workflow authority
  beyond the user's goal?

Do not claim quality, token, time, reliability, safety, or trigger improvement
unless the run data or review evidence proves that exact claim.

## Degeneration Checks

Before finalizing, reject these common regressions:

- Broad rewrites that erase known-good contracts to fix one eval.
- Copying an old skill wholesale instead of recovering the minimal useful rule.
- Turning examples, fixtures, or session anecdotes into universal requirements.
- Pasting universal checklists into every workflow.
- Requiring a companion skill, model, server, browser, or network path when the
  skill should be self-contained or provider-neutral.
- Moving process details into the description field so agents follow metadata
  instead of reading the body.
- Weakening proof paths because they are expensive.
- Expanding common assertions so exact-format, localized, or verbatim cases
  become impossible to satisfy.
- Counting skipped, flaky, unavailable, self-graded, or incomplete evals as
  proof.

## Self-Check

Before reporting completion:

- Is the failure signal tied to evidence, not guesswork?
- Is there a contract delta before changing skill text or eval behavior?
- Are examples mapped to reusable dimensions?
- Did wording edits preserve modality, exceptions, anchors, and absence
  statuses?
- Did the smallest coupled files change, including evals and changelog when
  required?
- Are baseline, grader, token, timing, and report claims honest?
- Are generated workspaces left uncommitted?
- Did you avoid version bumps unless this is release preparation?

For historical patterns behind these rules, read
`references/session-patterns.md` when the task asks for rationale or when a
change feels like it could make the skill larger but not better.
