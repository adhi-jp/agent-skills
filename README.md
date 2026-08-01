# Agent Skills

Workflow-focused agent skills and evaluation suites for software development,
skill maintenance, and Minecraft modding.

The authoritative skill packages live under [`skills/`](skills/). Each package
defines when the skill applies, what it may change, where it must stop, and what
evidence it needs before claiming completion.

## Start Here

For a multi-turn coding workflow, explicitly invoke `vibe-coding` with a
concrete request:

- Codex: `$vibe-coding <request>`
- Claude Code: `/vibe-coding <request>`

These are representative host syntaxes. `vibe-coding` selects one visible
specialist for the immediate phase; it does not run every phase at once or
bypass the selected specialist's approval, write, verification, or stop rules.
The examples assume the host can already see the skill. Host installation is
environment-specific; `scripts/sync_dev_agent_skills.py` only manages this
checkout's local `.agents/skills/` snapshots and `.claude/skills/` links.

If you already know the task type, invoke the matching specialist directly.
Use the tables below as a chooser, then read that skill's `SKILL.md` for the
complete contract.

For AI agents, this README is navigation rather than executable policy. Read the
selected source `SKILL.md` completely and follow its required references before
acting. Repository contributors must also follow [`AGENTS.md`](AGENTS.md).

## Choose a Skill

### Workflow entry and coordination

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Route an explicitly invoked, multi-turn coding workflow | `vibe-coding` | Selects one primary visible specialist for the current phase and preserves that specialist's gates | [source](skills/vibe-coding/SKILL.md) · [evals](evals/vibe-coding/) |
| Confirm or correct the agent's understanding before ambiguous or risky work | `vibe-goal-alignment` | Produces an understanding record and stops before action until the user confirms or corrects it | [source](skills/vibe-goal-alignment/SKILL.md) · [evals](evals/vibe-goal-alignment/) |
| Coordinate bounded subagent research, edits, repairs, or review | `vibe-orchestrate` | Provides delegation discipline; the coordinator keeps scope, verification, and consent ownership | [source](skills/vibe-orchestrate/SKILL.md) · [evals](evals/vibe-orchestrate/) |

### Shape, investigate, and change software

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Turn a rough, ambiguous, or contradictory goal into requirements | `vibe-requirements-spec` | Writes or revises the requirements spec and stops before planning or implementation | [source](skills/vibe-requirements-spec/SKILL.md) · [evals](evals/vibe-requirements-spec/) |
| Explore implementation ideas, alternatives, or expected conventions | `vibe-brainstorm` | Returns chat-first directions; a selected direction is not implementation approval | [source](skills/vibe-brainstorm/SKILL.md) · [evals](evals/vibe-brainstorm/) |
| Understand, locate, trace, or assess existing code | `vibe-code-research` | Read-only; static evidence is not presented as runtime proof | [source](skills/vibe-code-research/SKILL.md) · [evals](evals/vibe-code-research/) |
| Create or revise an implementation plan from approved or concrete inputs | `vibe-planning` | Writes plan artifacts only and stops before implementation | [source](skills/vibe-planning/SKILL.md) · [evals](evals/vibe-planning/) |
| Walk through a saved implementation plan item by item | `vibe-plan-review` | Interactive pre-check; it stops before implementation and does not grant execution approval | [source](skills/vibe-plan-review/SKILL.md) · [evals](evals/vibe-plan-review/) |
| Implement a concrete plan, specification, acceptance criteria, or task list | `vibe-plan-execution` | Binds the implementation input, checks proceed conditions, and verifies and reviews completed slices | [source](skills/vibe-plan-execution/SKILL.md) · [evals](evals/vibe-plan-execution/) |
| Diagnose and repair an existing bug, regression, failed fix, or runtime mismatch | `vibe-debug` | Keeps cause and repair claims evidence-backed and supplies a retest contract when local proof is unavailable | [source](skills/vibe-debug/SKILL.md) · [evals](evals/vibe-debug/) |
| Review a working tree, branch, base ref, or git-backed document change | `vibe-review` | Requires a non-empty git-backed target; fixes and history actions stay behind the workflow's gates | [source](skills/vibe-review/SKILL.md) · [evals](evals/vibe-review/) |

### Write and commit

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Write or revise README/docs, comments, changelog entries, PR text, UI copy, summaries, or commit messages | `vibe-writing` | Preserves facts, modality, exact formats, and language contracts; it does not authorize releases or broader history work | [source](skills/vibe-writing/SKILL.md) · [evals](evals/vibe-writing/) |
| Select files, stage, commit, split changes, or repair commit history and message transport | `vibe-commit` | Owns commit scope and git safety; it does not push or rewrite shared history without explicit consent | [source](skills/vibe-commit/SKILL.md) · [evals](evals/vibe-commit/) |

### Maintain skills and run evals

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Decide what to change in a skill or eval from benchmark, grader, review, or regression evidence | `skill-quality` | Makes evidence-bound quality decisions; release and version changes still need explicit instruction | [source](skills/skill-quality/SKILL.md) · [evals](evals/skill-quality/) |
| Validate, run, grade, aggregate, or report repository skill evals | `skill-eval` | Owns the shared runner contract and keeps executor and grader roles separate | [source](skills/skill-eval/SKILL.md) · [evals](evals/skill-eval/) |

### Domain-specific work

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Build, debug, port, or inspect Minecraft Java Edition mods | `minecraft-modding-workbench` | Covers Fabric, NeoForge, and Architectury and labels MCP, workspace, source, runtime, and unverified facts | [source](skills/minecraft-modding-workbench/SKILL.md) · [evals](evals/minecraft-modding-workbench/) |

## Shared Workflow Boundaries

The chooser above is intentionally brief. The selected `SKILL.md` is the source
of truth when a summary and a detailed contract differ.

- A skill owns one workflow phase. Requirements work does not silently become
  planning, planning does not become implementation, and read-only
  investigation does not become a fix.
- Approval, proceed, accepted-risk, and consent gates remain explicit. An
  AI-selected default or delegated recommendation is not human approval.
- Explicit state-changing `vibe-*` workflows may create scoped local checkpoint
  commits after their own verification and file-ownership gates pass, unless
  the user opts out or project policy forbids them.
- Scoped checkpoint permission does not include push, release preparation,
  version changes, tags, amend, rebase, reset, stash, squash, destructive
  cleanup, or unrelated and ambiguous paths.
- Current versions come from each source `SKILL.md`. Released changes and
  in-progress changes are recorded in [`CHANGELOG.md`](CHANGELOG.md); the README
  does not duplicate the version registry or the full skill contracts.

## Run Skill Evals

[`skill-eval`](skills/skill-eval/SKILL.md) is authoritative for eval workspace
placement, the runner CLI, executor/grader separation, model passthrough,
metrics, and result verification.

Do not launch an eval run unless the current user explicitly asks to run evals,
run a benchmark, or execute the eval runner. Static validation is safe for
checking an edited suite, but it is not benchmark evidence.

```sh
python3 skills/skill-eval/scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 skills/skill-eval/scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

Use `--eval-id E01,E03` only for an authorized diagnostic subset. A filtered run
is partial and non-closing; omit the filter for a full-suite closing run.
Generated workspaces under `evals/<skill-name>/workspace/<agent>/` are local
artifacts unless the user explicitly requests otherwise.

## Repository Map and Sources of Truth

| Path | Role |
| --- | --- |
| `skills/<skill-name>/SKILL.md` | Authoritative metadata and workflow contract; released skills also carry their current `version` |
| `skills/<skill-name>/references/` | Detailed guidance read when the skill routes to it |
| `evals/<skill-name>/` | Repository eval definitions, fixtures, and scoring notes |
| `skills/skill-eval/scripts/eval_runner.py` | Shared `validate` / `run` / `report` CLI |
| `CHANGELOG.md` | Keep a Changelog history and the current `Unreleased` buffer |
| `AGENTS.md` | Mandatory repository operating, release, coupling, snapshot, eval, and commit rules |
| `LICENSE` | MIT license for this repository |
| `scripts/sync_dev_agent_skills.py` | Managed local snapshot and Claude-link synchronization |
| `.agents/skills/`, `.claude/skills/` | Managed local copies and links; never the repository source of truth |

Some skill packages also include helper assets or scripts. Follow the routing in
that package's `SKILL.md` instead of loading every supporting file by default.

## Contributing

- Edit authoritative packages under `skills/`, not `.agents/skills/` snapshots
  or `.claude/skills/` links.
- Synchronize managed local copies only when explicitly requested, through
  `python3 scripts/sync_dev_agent_skills.py`. Use `--help` to inspect its
  `add`, `update`, and `remove` commands before changing local snapshots.
- Couple skill behavior changes with affected references, README guidance, and
  an entry under `CHANGELOG.md` → `Unreleased` when those artifacts describe the
  changed behavior.
- Do not bump a skill version until the user explicitly asks to prepare or cut
  a release. Release preparation moves accumulated entries out of `Unreleased`.
- Use Conventional Commits and keep commits logically scoped.

See [`AGENTS.md`](AGENTS.md) for the complete repository policy.
