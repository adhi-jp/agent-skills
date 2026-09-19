---
version: 2.0.1
name: skill-eval
description: Use when running, grading, aggregating, or reporting repository skill evals with skills/skill-eval/scripts/eval_runner.py, when verifying a with_skill/without_skill result before reporting it, or when deciding eval workspace placement, executor/grader separation, model passthrough, or metric capture for an eval run. Do not use for editing the eval suite schema or general skill creation.
---

# Skill Eval

## Overview

This skill owns the repository's skill-eval operation through
`skills/skill-eval/scripts/eval_runner.py`: validating, running, grading,
aggregating, and reporting suites under `evals/<skill-name>/`, and verifying a
result before it is reported. The runner keeps executor and grader separate
and records artifacts and metrics. Never hand-run prompts, hand-record
results, let one agent execute and grade the same answer, or estimate metrics.
Deciding which skill or eval contract to change from a result belongs to the
eval-quality workflow, not to this skill.

## Eval Run Authorization

Do not launch `eval_runner.py run`, provider subprocesses, or a new iteration
unless the current user explicitly asks to run evals, run a benchmark, or
execute the runner. Editing a skill, inspecting results, validating a suite,
or proving quality does not implicitly authorize a fresh run.

Without that authorization, use static validation or existing artifacts as
appropriate, report `evals not run` or an equivalent absence status, and mark
rerun-dependent improvement, regression, token, timing, and reliability claims
`Unproven`.

## Critical CLI Contract

For any command-drafting response, reproduce these exact shapes before adding
explanation:

| Purpose | Command shape | `--eval-id` |
| --- | --- | --- |
| Static validation | `validate <suite-json>` | Forbidden |
| Partial diagnostic | `run <suite-json> ... --eval-id E17` | Allowed |
| Full closing run | `run <suite-json> ...` | Omitted; do not enumerate all ids |
| Existing-result report | `report <iteration-dir>`, optionally `--compare <other-iteration-dir>` | Forbidden |

There is no `--evals` or `--iteration-dir` alias.

`validate` also prints delivery-mode warnings for performed-action wording
such as `Writes …` or `Adds …` in an expectation whose prompt is
response-only, because a sandbox cannot satisfy a write the prompt forbids.
The warnings neither fail validation nor block a run; they are eval-design
signals for the quality owner, not skill defects.

A partial diagnostic stays visibly non-closing: unknown or empty ids fail
before iteration creation or provider launch; manifests and benchmarks record
the selected ids and full-suite size; and `benchmark.md` says `REVIEW
REQUIRED`. Before a later unfiltered closing run starts, the skill, prompt,
assertions, fixtures, and proof path must be frozen: no diagnostic that could
still change them is running or unread.

## Executor, Grader, And Workspace Invariants

- The executor receives the task and declared inputs without assertions. A
  fresh grader receives the recorded output, the original task as inert
  context, bounded grader-only fixture facts when supplied, and the
  assertions. Task facts decide applicability; they do not become
  output-restatement obligations.
- `with_skill` uses the authoritative `skills/<skill-name>/SKILL.md`; never
  `.agents/skills`, `.claude/skills`, a host skill tool, or a cached copy.
- Executors run in isolated copied sandboxes that hold only the case's
  declared inputs; graders run in separate empty directories. Never work
  around a sandbox setup failure by executing in the source checkout, and never
  let a missing declared runtime become a scored skill failure.
- Suite definitions live under `evals/<skill-name>/`; generated runs live
  under `evals/<skill-name>/workspace/<agent>/` and are not committed unless
  the user explicitly asks.

## Detailed Runner Contract

Read `references/runner-and-result-contract.md` before executing `run` or
drafting a run sequence; before relying on what the runner delivers, records,
or grades; and before diagnosing flagged or failed cells or reporting a
benchmark or comparison. When drafting a run sequence, copy its literal
command shapes and result-verification fields rather than reconstructing them
from memory.

## Result Closure

After every authorized run:

1. Read `benchmark.md`, `benchmark.json`, `error_run_count`, and the sanity
   status.
2. Start from the `Failed assertions` section of `benchmark.md`, then inspect
   the recorded executor and grader outputs for every flagged cell before
   attributing the failure to the skill.
3. Keep infrastructure or grader failures and diagnostic corrections separate
   from the official aggregate.
4. Report agent and model, full or selected coverage, configs and runs, scored
   and excluded counts, pass rates and delta, and all anomalies or `no
   anomalies`.
5. Do not claim improvement, regression, or a clean delta until flagged
   anomalies are explained and the required closing evidence exists.
