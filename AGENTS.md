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

- Use `python3 scripts/eval_runner.py` for repo-level skill eval runs in Codex, Claude Code, Gemini, and other agents.
- Keep generated run artifacts under `evals/<skill-name>/workspace/<agent>/`.
- Do not make the shared eval CLI depend on local-only `.agents/` assets.
- `report` writes static `review.html` by default. Do not start a server, open a browser, bind a port, write a PID file, or leave a background process unless the user explicitly asks for an opt-in server workflow.
- `prepare` requires `--agent <agent-name>` and creates `evals/<skill-name>/workspace/<agent-name>/iteration-N/`. Use stable labels such as `codex`, `claude`, or `gemini`; do not write canonical runs directly under `workspace/iteration-N`.
- Standard command sequence:

```sh
python3 scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 scripts/eval_runner.py prepare evals/vibe-planning/evals.json --agent codex --eval E10 --config with_skill,without_skill --runs 1
python3 scripts/eval_runner.py record evals/vibe-planning/workspace/codex/iteration-1/eval-available-commit-message-skill-scheduled-for-checkpoints/with_skill/run-1 --outputs /path/to/outputs --total-tokens 123 --duration-ms 4567 --output-chars 890
python3 scripts/eval_runner.py prepare-grading evals/vibe-planning/workspace/codex/iteration-1/eval-available-commit-message-skill-scheduled-for-checkpoints/with_skill/run-1
python3 scripts/eval_runner.py grading-template evals/vibe-planning/workspace/codex/iteration-1/eval-available-commit-message-skill-scheduled-for-checkpoints/with_skill/run-1
python3 scripts/eval_runner.py record evals/vibe-planning/workspace/codex/iteration-1/eval-available-commit-message-skill-scheduled-for-checkpoints/with_skill/run-1 --grading /path/to/grading.json
python3 scripts/eval_runner.py doctor evals/vibe-planning/workspace/codex/iteration-1
python3 scripts/eval_runner.py aggregate evals/vibe-planning/workspace/codex/iteration-1
python3 scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

- `prepare` creates agent-scoped, provider-neutral `run_index.json`, `next_steps.md`, executor-safe `prompt.md`, `executor_metadata.json`, `outputs/`, and `run_manifest.json` files for each selected eval/config/run. It does not create `grader_prompt.md` or assertion-bearing `eval_metadata.json`.
- Run the current `prompt.md` manually in the agent named by `--agent`; write `outputs/run_receipt.json` from the current run manifest or next-steps payload; attach any host- or parent-captured tool, sub-agent, delegated-review, or other invocation trace that supports output claims as a non-response artifact under `outputs/`; then run `prepare-grading <run-dir|iteration-dir>` to create grader-only `grader_prompt.md` and assertion-bearing `eval_metadata.json` after executor output exists. Executor-authored trace reconstructions, final-response prose, copied invocation IDs, and self-reported call counts do not prove host/tool/delegation execution unless corroborated by recorded host or runner evidence. For custom workspace roots outside `evals/<skill-name>/workspace/<agent>/iteration-N`, pass `--evals-json <path>` to `prepare-grading`.
- `prepare --rerun-of <iteration-dir>` checks eval fingerprints, configs, run counts, agent, model, grader model, and run contract before writing a fresh rerun. Use `--accept-input-changes` only when the changed inputs are intentional.
- `record` attaches produced outputs, parent-captured timing, token, output-size metrics, usage blobs, and grader-produced `grading.json`. Prefer `--total-tokens`, `--duration-ms`, and `--output-chars` for parent-captured metrics, or `--usage-file` / `--usage-text` when the host records the same metrics; accepted timing keys are `duration_ms`, `duration_seconds`, `total_duration_seconds`, `executor_duration_seconds`, and `total_tokens`. Do not use placeholder, guessed, reused, or executor-estimated token/duration values for complete proof.
- When timing or grading metrics do not provide a tool-call count, `aggregate` reads `outputs/tool_trace.json` as the fallback source for `tool_calls`. Timing and grading metrics take precedence. The trace fallback accepts non-negative integer counts from `total_tool_calls`, `tool_call_count`, `invocation_count`, or `delegated_invocation_count`; list lengths from `tool_calls`, `tool_invocations`, `invocations`, `delegated_invocations`, or `delegated_reviews`; and count maps from `tool_calls`.
- Grader passes must grade the whole recorded output set, including `outputs/response.md` when present. Wrapper text, headings, Markdown fences, explanations, and prompt-local meta-notes are part of the output; do not narrow a global assertion to a sub-artifact unless the assertion explicitly scopes it that way.
- `show`, `inspect`, or multi-part response requests do not by themselves authorize Markdown fences or prompt-local references. Do not treat executor self-exoneration such as "the real artifact would be different" as evidence that the recorded output is compliant.
- `record --grading` and `record --finalize` validate prompt receipt, final metrics, metric-integrity findings, and static grading-audit findings for current runner contracts. Use `--allow-missing-prompt-receipt`, `--allow-missing-metrics`, `--allow-suspicious-metrics`, or `--allow-suspicious-grading` only for legacy, partial, or smoke runs; those opt-outs make complete aggregate/report proof incomplete unless `aggregate --allow-incomplete` is used. `--allow-missing-metrics` is for absent metrics, not present-but-invalid zero or placeholder values.
- Use `grading-template <run-dir>` after `prepare-grading` to write `grading-template.json` by default with every assertion text preserved and `passed: null`; fill boolean `passed` values before recording the grader-produced `grading.json`. Use `record-batch <records.json>` only for metrics, usage, grading, and finalization metadata after prevalidation.
- `grading.json` must include every prepared `eval_metadata.json.assertions` text exactly once, in order, with `text`, `passed`, and `evidence` fields.
- The static grading audit catches high-confidence boundary contradictions such as raw commit messages wrapped in Markdown fences, no-fence assertions with fences, prompt-local standalone leaks, JSON-only output with prose or fences, boundary-narrowing grader evidence, and missing artifact evidence for file claims. It does not replace semantic unsupported-claim grading.
- `aggregate` fails incomplete comparative runs by default, including missing current-contract grading materials or grading output, current-contract grading-audit errors, metric-integrity errors, repeated known placeholder metric patterns, or suspicious grading/metric opt-outs; pass `--allow-incomplete` for a single-config smoke run or explicitly incomplete aggregate.
- When a compatible baseline iteration exists for the same agent, use `aggregate --baseline-from <iteration-dir> --baseline-config without_skill` instead of rerunning unchanged baseline configs. Baseline reuse requires matching agent labels and fingerprints; do not force reuse legacy workspaces that lack fingerprint metadata.
- Use `doctor <iteration-dir>` for iteration health checks and `doctor <iteration-dir> --require-complete` before treating a run set as complete proof. Use `doctor --require-clean-grading-audit` when legacy workspaces must also block on audit errors or opt-outs.
- Use `report --previous-iteration <iteration-dir>` or `report --previous-iteration auto` to compare against a previous `benchmark.json`. Feedback controls in `review.html` are static client-side download controls; they must not start a server or write files by themselves. `report` also renders grading-audit findings near affected runs.

## Commit Rules

- Use Conventional Commits.
- Keep commits logically scoped; do not mix unrelated changes.
- Do not force-add ignored files or otherwise commit files outside the agreed commit scope unless the user explicitly instructs you to include those extra files.
