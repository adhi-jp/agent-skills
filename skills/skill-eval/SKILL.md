---
version: 1.1.0
name: skill-eval
description: Use when running, grading, aggregating, or reporting repository skill evals with skills/skill-eval/scripts/eval_runner.py, when verifying a with_skill/without_skill result before reporting it, or when deciding eval workspace placement, executor/grader separation, model passthrough, or metric capture for an eval run. Do not use for editing the eval suite schema or general skill creation.
---

# Skill Eval

## Overview

This skill owns the repository's skill-eval test operation. It is the
eval-focused alternative to `skill-creator`: it drives `skills/skill-eval/scripts/eval_runner.py`,
keeps the executor and grader as separate agents, surfaces run time and token
usage, and verifies results honestly before they are reported.

Eval execution is always structurally separated. A single agent must never both
produce an answer and grade it. The runner is the authoritative eval mechanism:
do not hand-run prompts or hand-record results, and never estimate or hand-type
metrics. These rules are enforced in the runner's code; this skill is the
always-on instruction to route eval work through that runner so the enforcement
actually applies.

## Critical CLI and Partial-Run Contract

For any command-drafting response, reproduce these shapes before adding
explanation. Treat them as exact; do not move options between subcommands:

| Purpose | Command shape | `--eval-id` |
| --- | --- | --- |
| Static validation | `validate <suite-json>` | Forbidden |
| Partial diagnostic | `run <suite-json> ... --eval-id E17` | Allowed |
| Full closing run | `run <suite-json> ...` | Omitted; do not enumerate all ids |
| Existing-result report | `report <iteration-dir>` | Forbidden |

There is no `--evals` or `--iteration-dir` alias. `validate ... --eval-id` and
filtered full-suite substitutes are invalid. When a response proposes a partial
diagnostic, it must also state all of these proof boundaries:

- unknown or empty ids fail before iteration creation or provider launch;
- `iteration_manifest.json` and `benchmark.json` record selected ids and the
  full-suite size;
- `benchmark.md` says `REVIEW REQUIRED`, diagnostic, and non-closing even when
  all selected cells succeed;
- the skill, prompt, assertions, fixtures, and proof path are frozen before the
  later unfiltered closing run;
- the earlier official aggregate remains unchanged, and an artifact-level
  correction stays separate and non-closing until the repaired assertion is
  measured.

## When to Use

- Running, grading, aggregating, or reporting a skill eval suite under `evals/`.
- Verifying a `with_skill` vs `without_skill` pass-rate result before reporting
  it as a real delta.
- Deciding eval workspace placement, model passthrough, run bounds, or metric
  display for an eval run.
- Reading execution time or token usage from `benchmark.md` or the run summary.

## When Not to Use

- Creating or editing the eval suite JSON schema or the assertion model.
- General skill creation, description/trigger optimization, or eval-viewer work —
  those remain with `skill-creator`.
- Quality decisions about what to change from results — that is `skill-quality`'s
  role. This skill owns the *execution and verification* of a run, not the
  contract-change call.

## Eval Run Authorization

Do not launch eval execution unless the current user explicitly asks to run
evals, run a benchmark, or execute the eval runner. In this skill, eval
execution means `python3 skills/skill-eval/scripts/eval_runner.py run ...` or
any equivalent command that starts executor or grader subprocesses or writes a
new iteration under `evals/<skill-name>/workspace/<agent>/`.

A request to change a skill, inspect results, validate a suite, report an
existing iteration, verify a diff, or prove quality does not by itself authorize
a new eval run. If a claim would require fresh eval execution and that explicit
instruction is absent, do not run evals; report `evals not run` or an equivalent
absence status and label rerun-dependent improvement, regression, token, timing,
or reliability claims as unproven.

## Executor and Grader Stay Separate

This is a hard rule grounded in a real prior incident where execution and
grading collapsed into one agent and the run scored its own output.

- The executor prompt carries the task only and no assertions. The grader prompt
  carries the recorded executor output plus the assertions and must return a
  structured verdict. The runner derives pass/fail from the grader subprocess,
  never from text the executor wrote about its own output, and the grader grades
  the whole recorded output, not a sub-artifact.
- There is no "grade inline" shortcut. Never instruct an agent to execute and
  grade in the same turn, even to save a subprocess, and never substitute a
  single-agent path that produces and scores an answer together. Executor and
  grader run as separate subprocesses with separate, clean invocations.
- The grader runs with a clean environment that strips `CLAUDECODE`, so a nested
  grader does not inherit executor state.
- Driving eval work through `skills/skill-eval/scripts/eval_runner.py` is what makes this
  separation hold. Eval work performed outside the runner does not get the
  code-enforced separation, so route eval runs through the runner.

## Evaluation Workspace

- Keep eval definitions under `evals/<skill-name>/`.
- Store generated eval run outputs under `evals/<skill-name>/workspace/<agent>/`.
- Do not create generated eval workspaces next to skill packages under `skills/`.
- Do not commit generated eval workspaces unless the user explicitly asks for
  them; they are local artifacts covered by `.gitignore`.

## Shared Eval CLI

- Use `python3 skills/skill-eval/scripts/eval_runner.py` for repo-level skill eval runs. It has
  three commands: `validate`, `run`, and `report`.
- When drafting or executing this command sequence, preserve the runner's
  documented CLI literally: the suite JSON is positional, provider selection
  uses `--agent`, configs use `--config`, repetition uses `--runs`, and
  `--eval-id E01,E03` selects a diagnostic case subset. Do not invent aliases
  such as `--evals`, `--iteration-dir`, `--configuration`, or `--mode`, and do
  not translate one bounded matrix into separate role/config runs unless the
  actual parser exposes that form.
- Run `eval_runner.py run` only after the current user has explicitly authorized
  eval execution. `validate` and `report` may support inspection or existing
  artifact work, but they are not substitutes for a user-authorized run when a
  fresh behavior claim depends on execution.
- The runner drives execution itself. `run` executes the bounded matrix end to
  end: for each eval x config x run it spawns a fresh executor subprocess with
  the prompt only, then a fresh grader subprocess with a clean environment and
  only the executor output (plus any plan artifact the executor wrote to the
  designated path) and the assertions, then aggregates a `with_skill` vs
  `without_skill` raw pass-rate comparison. No agent hand-runs prompts or
  hand-records results.
- The provider selector is a registry. `--agent` selects a registered provider;
  `claude` and `codex` are built in, and another agent is added as an adapter.
  The core path (execute, grade, compare, aggregate, report) is provider-neutral
  and must work on Codex; Claude-only precision such as opt-in metric capture is
  additive, and other providers skip it.
- Optional model flags are passed through to the selected provider CLI verbatim
  (whatever model name that CLI accepts): `--model` is the shared default for
  both roles, and `--executor-model` / `--grader-model` override it per role, so
  the executor and grader can run on different models. All three values are
  validated before any subprocess launches, and the resolved per-role models are
  recorded as `executor_model`/`grader_model` alongside `model` in the iteration
  manifest and benchmark. Absence means the provider's default model for that
  role, never an injected or guessed model id.
- All input validation runs before any subprocess launches: suite shape,
  requested eval ids, the authoritative `with_skill` skill source, provider
  availability, and run bounds. An unknown or empty `--eval-id` selection exits
  non-zero without creating an iteration or launching subprocesses. Other
  invalid input also exits non-zero with zero subprocess launches. An empty
  suite is not an error: it exits 0 with an explicit empty result and zero
  subprocess launches.
- For a non-empty Codex run, the runner performs a Codex-only readiness
  preflight after static validation and before creating an iteration or
  launching suite cells. It probes an executor-shaped invocation in a
  disposable Git repository and a grader-shaped invocation in an empty non-Git
  directory, records bounded evidence at
  `evals/<skill-name>/workspace/codex/preflight.json`, and stops with zero suite
  executor/grader cells if either probe fails. The grader probe compares its
  schema-constrained JSON result semantically rather than requiring one exact
  whitespace serialization, and failed probes retain bounded parsed-output and
  stderr diagnostics. Claude and other providers do not receive these extra
  probe launches.
- Total work is bounded. `--runs` is capped at 1..5 (default 1), `--timeout`
  bounds each subprocess (default 600s), and `--concurrency` caps concurrent
  provider subprocesses (1..16, default 4). A timed-out or failed executor is
  recorded as a failed run, not a pass, and the grader is skipped for it; there
  are no retries.
- `--eval-id` is for authorized, pre-registered diagnostics while a case's
  prompt, assertion, fixture, or proof path is still changing. It preserves the
  requested config matrix but executes only the named eval ids. The runner
  records selected ids and full-suite size in `iteration_manifest.json` and
  `benchmark.json`, marks a partial selection `REVIEW REQUIRED`, and labels it
  diagnostic and non-closing in `benchmark.md`. A partial run must not be
  reported as the suite's overall result or substitute for a later full-suite
  closing run after the contract is frozen. Omit `--eval-id` for that closing
  run. Keep the subcommand boundary literal: only `run` accepts `--eval-id`;
  `validate` takes the positional suite JSON, and `report` takes the iteration
  directory. Never copy the filter onto `validate` or `report`, and never spell
  a closing run as an all-id filtered diagnostic. Freeze the skill, prompt,
  assertions, fixtures, and proof path, then run the same authorized matrix
  without `--eval-id` exactly once for closing evidence.
- Metrics are never hand-typed or estimated. No flag injects a token or duration
  value. Claude usage comes from its JSON envelope. Codex usage comes from the
  `turn.completed` JSONL event, while Codex executor duration is measured by the
  runner around the subprocess. Missing usage fields remain explicitly absent;
  they are never replaced with placeholder token values.
- `with_skill` runs must use the authoritative `skills/<skill-name>/SKILL.md`
  source package. The runner resolves `--skill-path` from the repo root and, for
  every provider, rejects `.agents/skills` snapshots, `.claude/skills` links,
  files not named `SKILL.md`, and paths outside `skills/<skill-name>/`. The
  executor prompt instructs reading that source directly and not substituting a
  host skill tool, snapshot, link, or cached copy.
- Provider subprocesses run from a per-run sandbox outside the source checkout,
  not from the source checkout or a nested directory inside it. For git-backed
  source checkouts, the sandbox copies git-tracked paths with their current
  working-tree contents and excludes untracked or ignored leftovers, while still
  excluding host-local and generated state such as `.git`, `.agents`, `.claude`,
  `.codex`, `evals/*/workspace/`, `node_modules/`, and `__pycache__/`. A source
  root that is not a git repository falls back to the legacy copytree path but is
  recorded as contamination-unverified; a source root with git metadata that
  cannot be inspected fails instead of silently using the fallback. The runner
  initializes a throwaway git repository when `git` is available, remaps the
  `with_skill` skill path to the sandbox copy, sets provider `cwd`/`PWD` to the
  sandbox, and records sandbox details in `run.json`, including copy strategy,
  contamination status, and a bounded untracked/ignored exclusion sample.
  Codex executors use `workspace-write` inside that isolated repository so an
  independently required file deliverable can reach the designated capture
  path. Codex graders remain `read-only` in their separate empty working
  directory. Executor edits, installs, and commits must stay inside the run
  sandbox; sandbox git initialization failure is recorded, never worked around
  by running in the real repository. Sandbox isolation prevents new writes from
  contaminating the source checkout, but it does not prove the source fixtures
  were clean before copy; the runner records declared fixture-root dirtiness
  before and after execution as a sanity-check anomaly.
- Only the executor runs inside the sandbox repo copy. The grader runs in a
  separate empty per-run working directory, never the sandbox repo, so it cannot
  re-read fixtures, suite files, or the skill source to reconstruct ground truth
  the executor never had. This matters when two evals share a plan title (for
  example an inline plan and a same-titled file-backed fixture plan): a
  filesystem-roaming grader can bind to the wrong file and fail an accurate
  executor for text that only lives in the other file. The grader decides
  pass/fail from its prompt alone: the recorded output, the assertions, and the
  runner-provided `Sandbox File Changes` and `Executor Tool/Delegation Evidence`
  sections.
- Executor fixture delivery and grader ground-truth visibility are separate
  proof surfaces. If a verdict depends on fixture semantics, such as whether the
  executor invented or faithfully used a source fact, the suite must carry the
  minimum relevant facts in per-eval grader-only assertions or another recorded
  grader-only input. Preserve the empty grader working directory and keep those
  facts out of executor-facing material, including any `expected_output` field
  the executor can see. Phrase them as adjudication context: use of the facts is
  supplied, while restating every fact is not required unless an independent
  output contract says otherwise. Without that context, treat the semantic
  assertion as unobservable rather than restoring grader filesystem access or
  attributing the verdict to the target skill.
- Minimize semantic grader context by construction. Do not inject complete
  fixture files merely because the executor received them, and do not treat a
  fixture manifest as semantic ground truth: a manifest proves identity or
  delivery, not what the fixture says. Serialize only the bounded facts the
  assertion needs. Include a whole fixture only when the assertion genuinely
  evaluates its complete contents and the suite records why that scope is
  necessary.
- Executor and grader stay separate. The executor prompt carries the task only
  and no assertions; the grader prompt carries the recorded output plus the
  assertions and must return a structured verdict. The runner derives pass/fail
  from the grader subprocess, never from text the executor wrote about its own
  output. The grader grades the whole recorded output, not a sub-artifact.
- The executor prompt names one designated artifact path inside the sandbox,
  config-symmetrically for both `with_skill` and `without_skill`, so a skill
  whose deliverable is a written file (an implementation plan, spec, or other
  primary Markdown artifact) is not scored only on its concise chat summary.
  After execution the runner copies any file written to that path into
  `outputs/plan.md` under the run dir and folds its contents into the grader's
  recorded output under a delimited `Written Plan Artifact` section, capped and
  with truncation recorded, never silently dropped. Runs whose executor writes no
  such file (the deliverable is the chat reply) keep the grader prompt unchanged
  and record `written_artifact.captured = false`. The prompt labels the path as a
  capture destination rather than an artifact request: executors write it only
  when the user prompt or the workflow's normal deliverable contract independently
  requires a file, and otherwise answer in chat. The designated path does not
  instruct the executor how to structure the artifact, so it adds no
  target-behavior leakage.
- The runner also records the executor's real file changes in the sandbox as a
  `change_manifest`: the created, modified, and deleted paths (with content
  hashes for existing files) diffed against the sandbox baseline commit,
  excluding the runtime `.eval-runner/` scaffold, computed identically for
  `with_skill` and `without_skill`. It folds that record into the grader prompt
  under a `Sandbox File Changes` section so the grader can verify claims about
  writing, reusing, or updating files instead of trusting the executor's
  narration; when the sandbox git baseline is unavailable the manifest records
  `captured = false` with a reason and the grader prompt omits the section.
- For Claude runs, the runner also records a redacted host tool/delegation trace
  as `executor_evidence`. It captures the CLI `session_id`, reads the host
  transcript under `<CLAUDE_CONFIG_DIR or ~/.claude>/projects/<encoded-cwd>/`,
  and folds only tool names, host-issued tool-use ids, and host-created
  sub-agent record ids into the grader prompt under `Executor Tool/Delegation
  Evidence`. Prompt text, reasoning, and tool results stay redacted. This record
  is marked `source = host` because it reads host state outside the sandbox. For
  providers without an equivalent host transcript the field records
  `captured = false` with a reason, and the grader prompt omits the section.
- The grader returns a structured, schema-constrained verdict. Verdicts are keyed
  by the assertion's 1-based `id` (`{"verdicts": [{"id", "passed", "evidence"}]}`),
  not by an echoed assertion string, so a grader cannot break grading by
  re-numbering or paraphrasing the assertion text. The runner requests
  provider-native structured output where the CLI supports it
  (`codex --output-schema <file>`, `claude --json-schema <schema>`) and carries
  the same contract in the grader prompt for providers that do not; the legacy
  text-keyed `{"expectations": [{"text", ...}]}` shape is still accepted. A
  grader output the runner cannot parse into a verdict list is recorded as
  `grader_unparseable` with `pass_rate` absent and excluded from the comparison,
  never scored as a real `0%`.
- Codex prompts are sent through stdin with a terminal `-`, never as a
  positional command-line prompt. Codex-owned `--output-last-message` and
  `--output-schema` paths are absolute, and the adapter explicitly permits the
  isolated non-Git grader cwd with `--skip-git-repo-check`. The adapter gives
  only the executor `workspace-write` in its throwaway repository and keeps the
  grader `read-only`. Claude retains its existing
  `claude -p <prompt> --output-format json` invocation contract.
- Failed or timed-out executor/grader invocations persist bounded
  `outputs/executor_stderr.txt` or `outputs/grader_stderr.txt` diagnostics and a
  structured `failure` object in `run.json`. Truncation is explicit, and raw
  unbounded stderr is not embedded in the run record.
- Standard command sequence after explicit run authorization:

```sh
python3 skills/skill-eval/scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 skills/skill-eval/scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --eval-id E03 --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

The first `run` form is a case diagnostic; the second is the full-suite form.
The diagnostic filter belongs only to `run`; `validate` and `report` do not
accept it. Do not turn the full-suite form into a filtered enumeration of every
case.

- `run` writes `iteration_manifest.json` and, for each run, `prompt.md`,
  `grader_prompt.md`, `outputs/`, `grading.json`, `metrics.json`, and `run.json`
  under `evals/<skill-name>/workspace/<agent>/iteration-N/`, plus `benchmark.json`
  and `benchmark.md` at the iteration root. `run.json` records the external
  sandbox repo path for audit. `benchmark.json`/`benchmark.md` carry per-eval and
  overall raw pass rate, the `with_skill`/`without_skill` comparison, the
  execution-metrics summary, and a `sanity_checks` section flagging
  infrastructure failures, scored-`0%` cells, candidate-below-baseline cells, and
  dirty declared fixture roots for review. The manifest and benchmark also
  record suite coverage, and a partial `--eval-id` selection is a sanity signal
  even when every selected cell scored successfully.
- `report <iteration-dir>` re-renders `benchmark.md` from `benchmark.json`. It
  does not start a server, open a browser, bind a port, write a PID file, or
  leave a background process.
- `grading.json` includes every assertion (`common_assertions` then per-eval
  `expectations`) exactly once, in order, each with `text`, `passed`, and
  `evidence`. An assertion the grader omits is recorded as failed.
- Generated eval workspaces are local `.gitignore` artifacts; do not commit them
  unless the user explicitly asks.

## Execution Metrics (executor-only)

The `run` stdout summary and `benchmark.md` show per-config execution time and
token usage for at least the claude provider.

- The displayed values are the **executor** subprocess metrics, labeled
  executor-only so grader scoring cost is excluded and the values are not read as
  total run cost. The executor is the subprocess that runs the skill
  (`with_skill` vs `without_skill`), so the executor-only metrics are the skill's
  own performance signal; the `with_skill` vs `without_skill` delta is the
  meaningful reading.
- Aggregation is computed from the existing per-run `metrics`, so `report`
  re-renders older `benchmark.json` files that predate the metric rows. A
  per-config mean is shown with `± stddev` only when more than one run captured a
  numeric value for that metric, so a single captured value or the `--runs 1`
  default never produces a misleading spread.
- Uncaptured or partial provider metrics are shown as absent with a reason, never
  a placeholder. This includes a Claude run whose output was not a JSON envelope,
  individual missing sub-fields on an otherwise captured run, and a Codex run
  whose JSONL omitted usage even though runner-measured duration is available.
  Never read an absent metric as `0`.

## Result Verification and Reporting

- An agent that supervises an eval run must verify the result before reporting
  it. A run that finished without a crash is not the same as a clean result; do
  not present a `with_skill`/`without_skill` delta as normal completion until the
  verification below passes.
- After every user-authorized `run`, read the `Sanity checks` status (printed to
  stdout and written to `benchmark.md`) and the `error_run_count`. Treat these
  as stop-and-verify conditions, not passes: a `REVIEW REQUIRED` sanity status,
  `error_run_count > 0`, any
  `grader_unparseable`/`grader_failed`/`executor_failed`/timeout status, any
  scored-`0%` cell, any candidate-below-baseline cell, or any dirty
  source-fixture signal before or after execution. A partial suite selection is
  also `REVIEW REQUIRED` by construction because it is diagnostic rather than
  full-suite closing evidence.
- For each flagged cell, open the recorded `outputs/output.txt` and
  `outputs/grader_output.txt` and determine whether the cause is the executor
  output, the grader verdict, or the runner before attributing it to the skill.
  A grader-side or runner-side failure must not be reported as a skill score. Fix
  the cause and re-run, or report the cell as an excluded infrastructure failure
  with the reason; never silently fold it into the headline number.
- For a non-exact natural-language assertion, compare the output with the
  assertion's semantic predicate rather than one preferred phrase. If the
  response satisfies the behavior through equivalent wording but the grader
  fails it for omitting an unstated literal, record a lexical grader false
  negative. Keep the official aggregate unchanged and route any assertion edit
  to the quality owner; do not add the phrase to the target skill merely to make
  the grader recognize it.
- Always report a summary, not just the headline delta. The summary states: agent
  and model, full or selected suite coverage, configs and runs, scored versus
  excluded run counts, overall `with_skill`/`without_skill` pass rate and delta,
  and the sanity-check status with any flagged cells (or an explicit "no
  anomalies"). If any cell was excluded or re-graded, say so and give the
  corrected reading.
- Do not claim an improvement, regression, or delta as proven from a run that has
  flagged anomalies or excluded cells until they are explained or the run is
  repeated cleanly. Explaining a partial-selection signal does not promote that
  subset to full-suite proof; it remains non-closing even when every selected
  result is valid.

## Local Snapshots and Release

- `skill-creator` exists only as a managed snapshot under `.agents/skills/`.
  Read it for reference, but do not edit, copy, or commit it. Make eval and skill
  edits against tracked `skills/<skill-name>/` packages.
- Do not bump any skill version or assign a release version while running evals.
  Record notable changes under `## [Unreleased]` in `CHANGELOG.md` until the user
  instructs a release.
