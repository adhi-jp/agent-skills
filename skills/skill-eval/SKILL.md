---
version: 1.2.2
name: skill-eval
description: Use when running, grading, aggregating, or reporting repository skill evals with skills/skill-eval/scripts/eval_runner.py, when verifying a with_skill/without_skill result before reporting it, or when deciding eval workspace placement, executor/grader separation, model passthrough, or metric capture for an eval run. Do not use for editing the eval suite schema or general skill creation.
---

# Skill Eval

## Overview

This skill owns the repository's skill-eval test operation through
`skills/skill-eval/scripts/eval_runner.py`. The runner keeps executor and grader
separate, records artifacts and metrics, and aggregates `with_skill` versus
`without_skill` results. Never hand-run prompts, hand-record results, let one
agent execute and grade the same answer, or estimate metrics.

## Critical CLI Contract

For any command-drafting response, reproduce these exact shapes before adding
explanation:

| Purpose | Command shape | `--eval-id` |
| --- | --- | --- |
| Static validation | `validate <suite-json>` | Forbidden |
| Partial diagnostic | `run <suite-json> ... --eval-id E17` | Allowed |
| Full closing run | `run <suite-json> ...` | Omitted; do not enumerate all ids |
| Existing-result report | `report <iteration-dir>` | Forbidden |

There is no `--evals` or `--iteration-dir` alias. `validate ... --eval-id` and
filtered full-suite substitutes are invalid.

A partial diagnostic must remain visibly non-closing: unknown or empty ids fail
before iteration creation or provider launch; manifests and benchmarks record
selected ids and full-suite size; `benchmark.md` says `REVIEW REQUIRED`; and the
skill, prompt, assertions, fixtures, and proof path must be frozen before a later
unfiltered closing run. Keep the earlier official aggregate unchanged when an
artifact-level correction is only diagnostic.

## When To Use

Use this skill for:

- validating, running, grading, aggregating, or reporting a suite under
  `evals/<skill-name>/`;
- verifying a comparative result before reporting a delta;
- deciding runner workspace, provider/model passthrough, run bounds, artifact
  capture, metric provenance, or executor/grader proof boundaries.

Do not use it for general skill creation or for deciding what skill/eval contract
to change from a result. This skill owns execution and result verification, not
the quality-change decision.

## Eval Run Authorization

Do not launch `eval_runner.py run`, provider subprocesses, or a new iteration
unless the current user explicitly asks to run evals, run a benchmark, or
execute the runner. Editing a skill, inspecting results, validating a suite, or
proving quality does not implicitly authorize a fresh run.

When fresh execution is not authorized, use static validation or existing
artifacts as appropriate and report `evals not run` or an equivalent absence
status. Mark rerun-dependent improvement, regression, token, timing, and
reliability claims `Unproven`.

## Executor, Grader, And Workspace Invariants

- The executor receives the task without assertions. A fresh grader receives the
  recorded output and assertions and returns a structured verdict.
- Use the shared runner so this separation is code-enforced; there is no inline
  grading shortcut.
- Keep definitions under `evals/<skill-name>/` and generated runs under
  `evals/<skill-name>/workspace/<agent>/`.
- `with_skill` uses the authoritative `skills/<skill-name>/SKILL.md`; never use
  `.agents/skills`, `.claude/skills`, a host skill tool, or a cached copy.
- Provider executors run in isolated copied repositories; graders run in
  separate empty working directories. Do not work around sandbox setup failure
  by executing in the source checkout.
- Generated workspaces are local artifacts and are not committed unless the user
  explicitly asks.

## Detailed Runner Contract

Read `references/runner-and-result-contract.md` before:

- executing `run` or drafting a detailed run command sequence;
- changing or interpreting provider/model, preflight, sandbox, fixture,
  artifact-capture, change-manifest, grader-output, stderr, or metric behavior;
- diagnosing `REVIEW REQUIRED`, failed/unparseable/timeout cells, dirty fixtures,
  scored `0%`, candidate-below-baseline, or missing metrics;
- reporting a benchmark, corrected reading, exclusion, or comparative claim.

That reference is mandatory when its conditions apply and retains the complete
runner, artifact, provider, metric, and result-verification contract.

When drafting a full-suite run sequence, the response must preserve the
reference's literal positional suite path and flags, keep the requested configs
in one runner invocation, and include the result-verification and reporting
fields from that reference. Do not reconstruct the CLI or closure checklist from
memory.

## Result Closure

After every authorized run:

1. Read `benchmark.md`, `benchmark.json`, `error_run_count`, and sanity status.
2. Inspect recorded executor and grader outputs for every flagged cell before
   attributing the failure to the skill.
3. Keep infrastructure/grader failures and diagnostic corrections separate from
   the official aggregate.
4. Report agent and model, full or selected coverage, configs/runs, scored and
   excluded counts, pass rates/delta, and all anomalies or `no anomalies`.
5. Do not claim improvement, regression, or a clean delta until flagged
   anomalies are explained and the required closing evidence exists.

## Local Snapshots And Release

Operate on tracked `skills/<skill-name>/` packages. Managed `.agents/skills/`
and `.claude/skills/` copies are read-only unless the user explicitly requests
the repository sync workflow. Do not bump skill versions or assign a release
version during eval work; record notable changes under `## [Unreleased]` until a
release is explicitly requested.
