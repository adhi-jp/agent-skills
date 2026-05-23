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

## Evaluation Workspace Rules

- Keep eval definitions under `evals/<skill-name>/`.
- Store generated eval run outputs under `evals/<skill-name>/workspace/<agent>/`.
- Do not create generated eval workspaces next to skill packages under `skills/`.
- Do not commit generated eval workspaces unless the user explicitly asks for them; they are local artifacts covered by `.gitignore`.

## Shared Eval CLI Rules

- Use `python3 scripts/eval_runner.py` for repo-level skill eval runs in Codex, Claude Code, Gemini, and other agents.
- Keep generated run artifacts under `evals/<skill-name>/workspace/<agent>/`.
- Do not make the shared eval CLI depend on local-only `.agents/` assets.
- `report` writes static `review.html` by default. Do not start a server, open a browser, bind a port, write a PID file, or leave a background process unless the user explicitly asks for an opt-in server workflow.
- `prepare` requires `--agent <agent-name>` and creates `evals/<skill-name>/workspace/<agent-name>/iteration-N/`. Use stable labels such as `codex`, `claude`, or `gemini`; do not write canonical runs directly under `workspace/iteration-N`.
- Standard command sequence:

```sh
python3 scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 scripts/eval_runner.py prepare evals/vibe-planning/evals.json --agent codex --eval E10 --config with_skill,without_skill --runs 1
python3 scripts/eval_runner.py record evals/vibe-planning/workspace/codex/iteration-1/eval-available-commit-message-skill-scheduled-for-checkpoints/with_skill/run-1 --outputs /path/to/outputs --total-tokens 123 --duration-ms 4567 --output-chars 890 --grading /path/to/grading.json
python3 scripts/eval_runner.py aggregate evals/vibe-planning/workspace/codex/iteration-1
python3 scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

- `prepare` creates agent-scoped, provider-neutral `prompt.md`, `grader_prompt.md`, and `run_manifest.json` files for each selected eval/config/run. Run `prompt.md` manually in the agent named by `--agent`; run `grader_prompt.md` in a separate grading pass when the host environment supports it.
- `record` attaches produced outputs, parent-captured timing, token, and output-size metrics, and grader-produced `grading.json`. Prefer `--total-tokens`, `--duration-ms`, and `--output-chars` for parent-captured metrics; accepted timing keys are `duration_ms`, `duration_seconds`, `total_duration_seconds`, `executor_duration_seconds`, and `total_tokens`.
- `grading.json` must include every prepared `eval_metadata.json.assertions` text exactly once, in order, with `text`, `passed`, and `evidence` fields.
- `aggregate` fails incomplete comparative runs by default; pass `--allow-incomplete` for a single-config smoke run.
- When a compatible baseline iteration exists for the same agent, use `aggregate --baseline-from <iteration-dir> --baseline-config without_skill` instead of rerunning unchanged baseline configs. Baseline reuse requires matching agent labels and fingerprints; do not force reuse legacy workspaces that lack fingerprint metadata.
- Use `report --previous-iteration <iteration-dir>` to compare against a previous `benchmark.json`. Feedback controls in `review.html` are static client-side download controls; they must not start a server or write files by themselves.

## Commit Rules

- Use Conventional Commits.
- Keep commits logically scoped; do not mix unrelated changes.
- Do not force-add ignored files or otherwise commit files outside the agreed commit scope unless the user explicitly instructs you to include those extra files.
