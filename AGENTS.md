# AGENTS.md

## Purpose and Scope

- This file defines mandatory operating rules for agents working in this repository.
- When tradeoffs conflict, prioritize skill contract clarity, changelog accuracy, and release safety.

## Core Release Policy

- Do not bump any skill version unless explicitly instructed by the user to prepare or cut a release.
- Until the user gives a release instruction, record notable changes only under `## [Unreleased]` in `CHANGELOG.md`.
- Do not pre-assign future release versions in `## [Unreleased]` entries. Describe the changed skill and behavior without guessing the eventual version.
- Maintain `CHANGELOG.md` with the Keep a Changelog workflow: keep an `Unreleased` section for in-progress changes, move those entries into a release section when cutting a release, and create a fresh empty `Unreleased` section for future changes.

## Release Procedure

- When the user instructs a release, review all accumulated `## [Unreleased]` entries and the corresponding implementation/doc changes before choosing versions.
- Determine the next version for each affected skill from the actual accumulated changes:
  - Major: incompatible workflow or contract changes.
  - Minor: new user-visible capability, workflow branch, or supported use case.
  - Patch: clarifications, narrow fixes, examples, or behavior-preserving corrections.
- Bump the `version` field in each affected skill's `SKILL.md` only during release preparation.
- Move the released changelog entries from `## [Unreleased]` to a section headed `## [<skill-name> <version>] - <YYYY-MM-DD>`, where the date is when that skill's `SKILL.md` version changed.
- Move repository-wide maintenance entries that are not attributable to one skill to `## [Repository] - <YYYY-MM-DD>`. Do not use repository sections for skill behavior changes.

## Change Coupling Rules

- Any skill behavior change must update the relevant `SKILL.md`, supporting references, README text, and `CHANGELOG.md` entry in the same change set when those artifacts describe the changed behavior.
- Do not defer sibling documentation updates when the current change invalidates existing text.

## Local Skill Snapshot Rules

- Local skill snapshot paths under `.agents/skills/` and `.claude/skills/` are managed copies, not source. Do not edit, copy into, remove, recreate, stage, or commit them directly, and do not modify them as a side effect of other work. Reading them for reference (for example, to understand a skill that exists only as a snapshot) is allowed.
- Operate on `.agents/skills/` snapshots and `.claude/skills/` links only through `python3 scripts/sync_dev_agent_skills.py` when the user explicitly requests a local snapshot sync, update, add, or removal.
- Use tracked skill packages under `skills/` as the authoritative source for repository changes and verification. Make repository edits against `skills/`, not against the snapshot copies, and do not treat `.agents/skills/` or `.claude/skills/` as the source of truth for parity or committed runtime state. Editing `skills/*` does not imply updating local snapshots.

## Evaluation Workspace Rules

- Keep eval definitions under `evals/<skill-name>/`.
- Store generated eval run outputs under `evals/<skill-name>/workspace/<agent>/`.
- Do not create generated eval workspaces next to skill packages under `skills/`.
- Do not commit generated eval workspaces unless the user explicitly asks for them; they are local artifacts covered by `.gitignore`.

## Shared Eval CLI Rules

- Use `python3 scripts/eval_runner.py` for repo-level skill eval runs. It has three commands: `validate`, `run`, and `report`.
- The runner drives execution itself. `run` executes the bounded matrix end to end: for each eval x config x run it spawns a fresh executor subprocess with the prompt only, then a fresh grader subprocess with a clean environment and only the executor output (plus any plan artifact the executor wrote to the designated path) and the assertions, then aggregates a `with_skill` vs `without_skill` raw pass-rate comparison. No agent hand-runs prompts or hand-records results.
- The provider selector is a registry. `--agent` selects a registered provider; `claude` and `codex` are built in, and another agent is added as an adapter. The core path (execute, grade, compare, aggregate, report) is provider-neutral and must work on Codex; Claude-only precision such as opt-in metric capture is additive, and other providers skip it.
- An optional `--model` is passed through to the selected provider CLI verbatim (whatever model name that CLI accepts); it is validated before any subprocess launches, applied to both the executor and grader, and recorded in the iteration manifest and benchmark. Absence means the provider's default model, never an injected or guessed model id.
- All input validation runs before any subprocess launches: suite shape, the authoritative `with_skill` skill source, provider availability, and run bounds. Invalid input exits non-zero with zero subprocess launches. An empty suite is not an error: it exits 0 with an explicit empty result and zero subprocess launches.
- Total work is bounded. `--runs` is capped at 1..5 (default 1), `--timeout` bounds each subprocess (default 600s), and `--concurrency` caps concurrent provider subprocesses (1..16, default 4). A timed-out or failed executor is recorded as a failed run, not a pass, and the grader is skipped for it; there are no retries.
- Metrics are never hand-typed or estimated. No flag injects a token or duration value. When a provider exposes machine-readable usage (for example `claude -p --output-format json`), the runner captures it into `metrics.json` with its source; when a provider does not, absence is recorded as absence, never a placeholder number.
- `with_skill` runs must use the authoritative `skills/<skill-name>/SKILL.md` source package. The runner resolves `--skill-path` from the repo root and, for every provider, rejects `.agents/skills` snapshots, `.claude/skills` links, files not named `SKILL.md`, and paths outside `skills/<skill-name>/`. The executor prompt instructs reading that source directly and not substituting a host skill tool, snapshot, link, or cached copy.
- Provider subprocesses run from a per-run sandbox copy of the current repository tree outside the source checkout, not from the source checkout or a nested directory inside it. The runner excludes host-local and generated state such as `.git`, `.agents`, `.claude`, `.codex`, `evals/*/workspace/`, `node_modules/`, and `__pycache__/`, initializes a throwaway git repository when `git` is available, remaps the `with_skill` skill path to the sandbox copy, sets provider `cwd`/`PWD` to the sandbox, and records sandbox details in `run.json`. Executor or grader edits, installs, and commits must stay inside that sandbox; sandbox git initialization failure is recorded, never worked around by running in the real repository. Sandbox isolation prevents new writes from contaminating the source checkout, but it does not prove the source fixtures were clean before copy; the runner records declared fixture-root dirtiness before and after execution as a sanity-check anomaly.
- Executor and grader stay separate. The executor prompt carries the task only and no assertions; the grader prompt carries the recorded output plus the assertions and must return a structured verdict. The runner derives pass/fail from the grader subprocess, never from text the executor wrote about its own output. The grader grades the whole recorded output, not a sub-artifact.
- The executor prompt names one designated artifact path inside the sandbox, config-symmetrically for both `with_skill` and `without_skill`, so a skill whose deliverable is a written file (an implementation plan, spec, or other primary Markdown artifact) is not scored only on its concise chat summary. After execution the runner copies any file written to that path into `outputs/plan.md` under the run dir and folds its contents into the grader's recorded output under a delimited `Written Plan Artifact` section, capped and with truncation recorded, never silently dropped. Runs whose executor writes no such file (the deliverable is the chat reply) keep the grader prompt unchanged and record `written_artifact.captured = false`. The designated path does not instruct the executor how to structure the artifact, so it adds no target-behavior leakage.
- The grader returns a structured, schema-constrained verdict. Verdicts are keyed by the assertion's 1-based `id` (`{"verdicts": [{"id", "passed", "evidence"}]}`), not by an echoed assertion string, so a grader cannot break grading by re-numbering or paraphrasing the assertion text. The runner requests provider-native structured output where the CLI supports it (`codex --output-schema <file>`, `claude --json-schema <schema>`) and carries the same contract in the grader prompt for providers that do not; the legacy text-keyed `{"expectations": [{"text", ...}]}` shape is still accepted. A grader output the runner cannot parse into a verdict list is recorded as `grader_unparseable` with `pass_rate` absent and excluded from the comparison, never scored as a real `0%`.
- Standard command sequence:

```sh
python3 scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

- `run` writes `iteration_manifest.json` and, for each run, `prompt.md`, `grader_prompt.md`, `outputs/`, `grading.json`, `metrics.json`, and `run.json` under `evals/<skill-name>/workspace/<agent>/iteration-N/`, plus `benchmark.json` and `benchmark.md` at the iteration root. `run.json` records the external sandbox repo path for audit. `benchmark.json`/`benchmark.md` carry per-eval and overall raw pass rate, the `with_skill`/`without_skill` comparison, and a `sanity_checks` section flagging infrastructure failures, scored-`0%` cells, candidate-below-baseline cells, and dirty declared fixture roots for review.
- `report <iteration-dir>` re-renders `benchmark.md` from `benchmark.json`. It does not start a server, open a browser, bind a port, write a PID file, or leave a background process.
- `grading.json` includes every assertion (`common_assertions` then per-eval `expectations`) exactly once, in order, each with `text`, `passed`, and `evidence`. An assertion the grader omits is recorded as failed.
- Generated eval workspaces are local `.gitignore` artifacts; do not commit them unless the user explicitly asks.

## Result Verification and Reporting

- An agent that supervises an eval run must verify the result before reporting it. A run that finished without a crash is not the same as a clean result; do not present a `with_skill`/`without_skill` delta as normal completion until the verification below passes.
- After every `run`, read the `Sanity checks` status (printed to stdout and written to `benchmark.md`) and the `error_run_count`. Treat any of the following as a stop-and-verify condition, not a pass: a `REVIEW REQUIRED` sanity status, `error_run_count > 0`, any `grader_unparseable`/`grader_failed`/`executor_failed`/timeout status, any scored-`0%` cell, any candidate-below-baseline cell, or any dirty source-fixture signal before or after execution.
- For each flagged cell, open the recorded `outputs/output.txt` and `outputs/grader_output.txt` and determine whether the cause is the executor output, the grader verdict, or the runner before attributing it to the skill. A grader-side or runner-side failure must not be reported as a skill score. Fix the cause and re-run, or report the cell as an excluded infrastructure failure with the reason; never silently fold it into the headline number.
- Always report a summary, not just the headline delta. The summary states: agent and model, configs and runs, scored versus excluded run counts, overall `with_skill`/`without_skill` pass rate and delta, and the sanity-check status with any flagged cells (or an explicit "no anomalies"). If any cell was excluded or re-graded, say so and give the corrected reading.
- Do not claim an improvement, regression, or delta as proven from a run that has flagged anomalies or excluded cells until they are explained or the run is repeated cleanly.

## Commit Rules

- Use Conventional Commits.
- Keep commits logically scoped; do not mix unrelated changes.
- Do not force-add ignored files or otherwise commit files outside the agreed commit scope unless the user explicitly instructs you to include those extra files.
