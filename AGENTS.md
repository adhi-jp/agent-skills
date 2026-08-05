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
- Establish the release scope from the complete accumulated change set since each affected skill's last release, not from the latest commit, one changed package, or the current version field alone. Unless the user explicitly requests a partial release, include every skill with releasable accumulated changes.
- Before editing release artifacts, build an affected-skill inventory that records, for every changed `skills/<skill-name>/` package: its previous version, accumulated reader-visible contract changes, SemVer decision, changelog entries, and any README or supporting-reference updates required by those changes. Include repository-wide maintenance as a separate inventory item. Do not create the release commit until every inventory item is either included or explicitly deferred by the user.
- Determine the next version for each affected skill from the actual accumulated changes:
  - Major: incompatible workflow or contract changes.
  - Minor: new user-visible capability, workflow branch, or supported use case.
  - Patch: clarifications, narrow fixes, examples, or behavior-preserving corrections.
- Bump the `version` field in each affected skill's `SKILL.md` only during release preparation.
- Move the released changelog entries from `## [Unreleased]` to a section headed `## [<skill-name> <version>] - <YYYY-MM-DD>`, where the date is when that skill's `SKILL.md` version changed.
- Move repository-wide maintenance entries that are not attributable to one skill to `## [Repository] - <YYYY-MM-DD>`. Do not use repository sections for skill behavior changes.
- Write release entries as durable reader-visible contract deltas, not as a chronological work log. Consolidate related and superseded entries; do not copy commit subjects, file-edit narration, agent activity, investigation steps, repeated eval iterations, or run-by-run score commentary into a release section. Retain only the final behavior, breaking or migration guidance when applicable, the strongest durable verification status, and unresolved accepted risk.
- Before creating the release commit, inspect the complete staged diff and verify all of the following:
  - Every released skill in the inventory has exactly one intended `SKILL.md` version change and a matching changelog section with the same version and date.
  - Every released `Unreleased` item has moved to the correct skill or repository section, explicitly deferred items remain under `Unreleased`, and no released behavior remains stranded there.
  - README text and supporting references describe the released contracts and do not retain stale versions, names, capabilities, or workflow boundaries.
  - Changelog release sections contain outcome-focused entries rather than duplicated cross-skill text or release-preparation logs.
  - Relevant validation has passed for every affected skill, and one skill's passing checks are not presented as proof for unverified siblings.
  - The staged file set contains all required release artifacts and no unrelated, generated, ignored, or local snapshot paths.
- Do not create a release commit that updates only a convenient subset of affected skills, versions, changelog sections, or README/supporting documentation unless the user explicitly narrowed the release scope and the deferred work remains accurately recorded under `Unreleased`.

## Change Coupling Rules

- Any skill behavior change must update the relevant `SKILL.md`, supporting references, README text, and `CHANGELOG.md` entry in the same change set when those artifacts describe the changed behavior.
- Do not defer sibling documentation updates when the current change invalidates existing text.

## Vibe Skill Cross-Reference Rules

- In `skills/vibe-*` skill instructions outside `skills/vibe-coding/`, do not explicitly name another `vibe-*` skill. Use phase, capability, or workflow-boundary terms such as "top-level orchestration", "requirements capture", "implementation planning", "plan execution", "review workflow", or "commit-execution workflow" instead.
- `skills/vibe-coding/` is the only vibe skill package that may explicitly name other vibe specialists for routing or orchestration. Other vibe skills must remain self-contained and downstream-neutral when referring to neighboring phases.
- Self-identifying frontmatter such as a skill's own `name` field is allowed. Repository catalog text, eval prompts, changelog entries, and release sections may name skills when that naming is the artifact's purpose, but do not copy those names into non-`vibe-coding` skill instructions as cross-skill dependencies.

## Local Skill Snapshot Rules

- Local skill snapshot paths under `.agents/skills/` and `.claude/skills/` are managed copies, not source. Do not edit, copy into, remove, recreate, stage, or commit them directly, and do not modify them as a side effect of other work. Reading them for reference (for example, to understand a skill that exists only as a snapshot) is allowed.
- Operate on `.agents/skills/` snapshots and `.claude/skills/` links only through `python3 scripts/sync_dev_agent_skills.py` when the user explicitly requests a local snapshot sync, update, add, or removal.
- Use tracked skill packages under `skills/` as the authoritative source for repository changes and verification. Make repository edits against `skills/`, not against the snapshot copies, and do not treat `.agents/skills/` or `.claude/skills/` as the source of truth for parity or committed runtime state. Editing `skills/*` does not imply updating local snapshots.

## Skill Eval Operation

- The skill-eval test operation is owned by the `skill-eval` skill (`skills/skill-eval/SKILL.md`): eval workspace placement under `evals/<skill-name>/`, the `skills/skill-eval/scripts/eval_runner.py` CLI contract (`validate`/`run`/`report`), executor and grader separation, `--model` passthrough, metric capture and the executor-only time/token display, and result verification before reporting a `with_skill`/`without_skill` delta. Run skill evals through `skills/skill-eval/scripts/eval_runner.py` and follow that skill as authoritative; do not hand-run prompts or grade in a single agent, and do not hand-type or estimate metrics.

## Commit Rules

- Use Conventional Commits.
- Keep commits logically scoped; do not mix unrelated changes.
- Do not force-add ignored files or otherwise commit files outside the agreed commit scope unless the user explicitly instructs you to include those extra files.
