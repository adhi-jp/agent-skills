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

- Local skill snapshot paths under `.agents/skills/` and `.claude/skills/` are managed copies, not source. Do not edit, sync, copy into, remove, recreate, stage, or commit them, and do not modify them as a side effect of other work. Reading them for reference (for example, to understand a skill that exists only as a snapshot) is allowed.
- Use tracked skill packages under `skills/` as the authoritative source for repository changes and verification. Make repository edits against `skills/`, not against the snapshot copies, and do not treat `.agents/skills/` or `.claude/skills/` as the source of truth for parity or committed runtime state.

## Evaluation Workspace Rules

- Keep eval definitions under `evals/<skill-name>/`.
- Store generated eval run outputs under `evals/<skill-name>/workspace/<agent>/`.
- Do not create generated eval workspaces next to skill packages under `skills/`.
- Do not commit generated eval workspaces unless the user explicitly asks for them; they are local artifacts covered by `.gitignore`.

## Shared Eval CLI Rules

- Use `python3 scripts/eval_runner.py` for repo-level skill eval runs. It has three commands: `validate`, `run`, and `report`.
- The runner drives execution itself. `run` executes the bounded matrix end to end: for each eval x config x run it spawns a fresh executor subprocess with the prompt only, then a fresh grader subprocess with a clean environment and only the executor output plus the assertions, then aggregates a `with_skill` vs `without_skill` raw pass-rate comparison. No agent hand-runs prompts or hand-records results.
- The provider selector is a registry. `--agent` selects a registered provider; `claude` and `codex` are built in, and another agent is added as an adapter. The core path (execute, grade, compare, aggregate, report) is provider-neutral and must work on Codex; Claude-only precision such as opt-in metric capture is additive, and other providers skip it.
- An optional `--model` is passed through to the selected provider CLI verbatim (whatever model name that CLI accepts); it is validated before any subprocess launches, applied to both the executor and grader, and recorded in the iteration manifest and benchmark. Absence means the provider's default model, never an injected or guessed model id.
- All input validation runs before any subprocess launches: suite shape, the authoritative `with_skill` skill source, provider availability, and run bounds. Invalid input exits non-zero with zero subprocess launches. An empty suite is not an error: it exits 0 with an explicit empty result and zero subprocess launches.
- Total work is bounded. `--runs` is capped at 1..5 (default 1), `--timeout` bounds each subprocess (default 600s), and `--concurrency` caps concurrent provider subprocesses (1..16, default 4). A timed-out or failed executor is recorded as a failed run, not a pass, and the grader is skipped for it; there are no retries.
- Metrics are never hand-typed or estimated. No flag injects a token or duration value. When a provider exposes machine-readable usage (for example `claude -p --output-format json`), the runner captures it into `metrics.json` with its source; when a provider does not, absence is recorded as absence, never a placeholder number.
- `with_skill` runs must use the authoritative `skills/<skill-name>/SKILL.md` source package. The runner resolves `--skill-path` from the repo root and, for every provider, rejects `.agents/skills` snapshots, `.claude/skills` links, files not named `SKILL.md`, and paths outside `skills/<skill-name>/`. The executor prompt instructs reading that source directly and not substituting a host skill tool, snapshot, link, or cached copy.
- Executor and grader stay separate. The executor prompt carries the task only and no assertions; the grader prompt carries the recorded output plus the assertions and must return a JSON verdict (`{"expectations": [{"text", "passed", "evidence"}]}`). The runner derives pass/fail from the grader subprocess, never from text the executor wrote about its own output. The grader grades the whole recorded output, not a sub-artifact.
- Standard command sequence:

```sh
python3 scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

- `run` writes `iteration_manifest.json` and, for each run, `prompt.md`, `grader_prompt.md`, `outputs/`, `grading.json`, `metrics.json`, and `run.json` under `evals/<skill-name>/workspace/<agent>/iteration-N/`, plus `benchmark.json` and `benchmark.md` at the iteration root. `benchmark.json`/`benchmark.md` carry per-eval and overall raw pass rate and the `with_skill`/`without_skill` comparison.
- `report <iteration-dir>` re-renders `benchmark.md` from `benchmark.json`. It does not start a server, open a browser, bind a port, write a PID file, or leave a background process.
- `grading.json` includes every assertion (`common_assertions` then per-eval `expectations`) exactly once, in order, each with `text`, `passed`, and `evidence`. An assertion the grader omits is recorded as failed.
- Generated eval workspaces are local `.gitignore` artifacts; do not commit them unless the user explicitly asks.

## Commit Rules

- Use Conventional Commits.
- Keep commits logically scoped; do not mix unrelated changes.
- Do not force-add ignored files or otherwise commit files outside the agreed commit scope unless the user explicitly instructs you to include those extra files.
