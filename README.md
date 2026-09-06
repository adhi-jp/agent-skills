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

These are representative host syntaxes. `vibe-coding` classifies the
instruction into one row of its decision table and routes only specialist-owned
rows to a visible specialist; router-owned rows (workflow control, direct
implementation, maintenance) run as the router's own behavior under the shared
contract. It does not run every phase at once or bypass the selected
specialist's approval, write, verification, or stop rules.
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
| Route an explicitly invoked, multi-turn coding workflow | `vibe-coding` | Classifies each turn into one row of a decision table after a narrowly triggered goal-alignment gate; routes specialist-owned rows to one visible specialist and preserves its gates; performs the router-owned `direct-implementation` and `maintenance` rows itself under the shared effect and commit boundaries; and keeps routing state in a session record under `.plans/vibe-sessions/` that is a record, not authority, while approvals, proceed decisions, and stop boundaries stay in the conversation | [source](skills/vibe-coding/SKILL.md) · [evals](evals/vibe-coding/) |
| Confirm or correct the agent's understanding before ambiguous or risky work | `vibe-goal-alignment` | Produces an understanding record and stops before action until the user confirms or corrects it | [source](skills/vibe-goal-alignment/SKILL.md) · [evals](evals/vibe-goal-alignment/) |
| Coordinate bounded subagent research, edits, repairs, or review | `vibe-orchestrate` | The coordinator keeps scope, verification, and consent ownership; treats worker output as non-authorizing; and selects external write lanes by required effects plus isolation and receipts, with free-text residual risk and report/manifest/Git reconciliation before acceptance; qualifying coordinator decisions that bind later rounds become decision records and dropped or later-round items go to `docs/reports/findings/` | [source](skills/vibe-orchestrate/SKILL.md) · [evals](evals/vibe-orchestrate/) |

### Shape, investigate, and change software

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Turn a rough, ambiguous, or contradictory goal into requirements | `vibe-requirements-spec` | Uses adaptive clarification, keeps high-risk decisions human-owned and outside-authored raw text out of secondary sinks, and stops before planning or implementation | [source](skills/vibe-requirements-spec/SKILL.md) · [evals](evals/vibe-requirements-spec/) |
| Explore implementation ideas, alternatives, or expected conventions | `vibe-brainstorm` | Returns chat-first multi-perspective directions; delegation is optional, and a selected direction is not implementation approval | [source](skills/vibe-brainstorm/SKILL.md) · [evals](evals/vibe-brainstorm/) |
| Understand, locate, trace, or assess existing code | `vibe-code-research` | Read-only; direct lookups stay concise, and material negative/architecture/risk conclusions receive a disconfirming check | [source](skills/vibe-code-research/SKILL.md) · [evals](evals/vibe-code-research/) |
| Create or revise an implementation plan from approved or concrete inputs | `vibe-planning` | Writes concise plan artifacts and stops before implementation; reserved decisions stay authority-bounded, and risk-triggered review uses verified-capacity or one bounded optimistic batch before coordinator fallback | [source](skills/vibe-planning/SKILL.md) · [evals](evals/vibe-planning/) |
| Walk through a saved implementation plan item by item | `vibe-plan-review` | Interactive pre-check; review state stays in chat unless resumability needs persistence, exact target/state mismatches fail closed, a settled item decision that qualifies becomes a decision record, and it stops before implementation | [source](skills/vibe-plan-review/SKILL.md) · [evals](evals/vibe-plan-review/) |
| Implement a concrete plan, specification, acceptance criteria, or task list | `vibe-plan-execution` | Binds the current reviewed plan content, keeps material high-risk and out-of-scope constraints visible, checks proceed conditions, verifies and reviews completed slices, writes qualifying decisions to `docs/decisions/` and deferred findings to `docs/reports/findings/`, then closes each slice with a scoped local checkpoint commit | [source](skills/vibe-plan-execution/SKILL.md) · [evals](evals/vibe-plan-execution/) |
| Diagnose and repair an existing bug, regression, failed fix, or runtime mismatch | `vibe-debug` | Keeps cause and repair claims evidence-backed; simple bugs close concisely while recurrent or environment-bound work retains a ledger/retest contract; a qualifying repair policy other units must follow becomes a decision record and deferred or accepted-residual items go to `docs/reports/findings/` | [source](skills/vibe-debug/SKILL.md) · [evals](evals/vibe-debug/) |
| Review a working tree, branch, base ref, or git-backed document change | `vibe-review` | Requires a non-empty git-backed target; records capability properties separately, quarantines delegated evidence, and omits private backend/source references from public findings while preserving common review gates; qualifying accepted divergences and standing dispositions become decision records and deferred items go to `docs/reports/findings/` | [source](skills/vibe-review/SKILL.md) · [evals](evals/vibe-review/) |

### Write and commit

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Write or revise README/docs, comments, changelog entries, PR text, UI copy, summaries, or commit messages | `vibe-writing` | Preserves facts, modality, exact formats, and language contracts; it does not authorize releases or broader history work | [source](skills/vibe-writing/SKILL.md) · [evals](evals/vibe-writing/) |
| Create, refresh, or localize a repository's agent instruction files (AGENTS.md, CLAUDE.md, personal local rules) | `vibe-agent-instructions` | Explicit invocation only; AGENTS.md is the source, CLAUDE.md is a relative link, a documented import stub when links are unavailable, or an import-plus-remainder file when Claude-specific content exists, personal rules live in a Git-ignored AGENTS.override.md with a linked CLAUDE.local.md, detailed procedures live in a pointer-referenced docs folder, existing paths are previewed before any write, known divergences are reported before the policy is applied, and it never stages or commits | [source](skills/vibe-agent-instructions/SKILL.md) · [evals](evals/vibe-agent-instructions/) |
| Select files, stage, commit, split changes, or repair commit history and message transport | `vibe-commit` | Owns artifact eligibility, commit scope, exact-diff message reconciliation, and git safety; detailed receipts are conditional but retain concern coverage and drift invalidation when required, and it does not push or rewrite shared history without explicit consent | [source](skills/vibe-commit/SKILL.md) · [evals](evals/vibe-commit/) |

### Maintain skills and run evals

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Decide what to change in a skill or eval from benchmark, grader, review, or regression evidence | `skill-quality` | Makes evidence-bound quality decisions, including transition-authority and artifact-lifecycle failures; release and version changes still need explicit instruction | [source](skills/skill-quality/SKILL.md) · [evals](evals/skill-quality/) |
| Validate, run, grade, aggregate, or report repository skill evals | `skill-eval` | Owns the shared runner contract, keeps executor and grader roles separate, and bounds long-run workload, retries, and cancellation | [source](skills/skill-eval/SKILL.md) · [evals](evals/skill-eval/) |

### Domain-specific work

| Task | Skill | Important boundary | Package |
| --- | --- | --- | --- |
| Build, debug, port, or inspect Minecraft Java Edition mods | `minecraft-modding-workbench` | Covers Fabric, NeoForge, and Architectury, labels material MCP/workspace/source/runtime provenance, and keeps internal reference routing out of ordinary output | [source](skills/minecraft-modding-workbench/SKILL.md) · [evals](evals/minecraft-modding-workbench/) |

## Shared Workflow Boundaries

The chooser above is intentionally brief. The selected `SKILL.md` is the source
of truth when a summary and a detailed contract differ.

- A skill owns one workflow phase. Requirements work does not silently become
  planning, planning does not become implementation, and read-only
  investigation does not become a fix.
- Approval, proceed, accepted-risk, and consent gates remain explicit. An
  AI-selected default or delegated recommendation is not human approval.
- A state-changing workflow closes each verified, reviewed unit of its own
  changes with a scoped local commit, without needing a per-request commit
  instruction; a no-commit instruction or project policy suspends that. The
  commit covers only that unit — never pre-existing working-tree changes, an
  artifact whose tracked status would itself be new, or paths outside it.
- Artifact creation, tracking, staging, commit, release-note inclusion, and
  publishing are separate lifecycle transitions with their own authority.
- A qualifying decision — one that binds work beyond the current unit and was
  chosen among alternatives, reverses a prior choice, settles an ambiguous
  instruction, or was AI-selected — is written as a decision record under
  `docs/decisions/` when it is settled, and a defect or
  concern a phase deliberately leaves unaddressed is written to
  `docs/reports/findings/` before the unit closes; a phase that may not write
  hands both forward as a carry-forward packet. Each package carries the shared
  obligations in `references/durable-records.md`, together with the record and
  report formats where the phase reads or writes records.
- Commit selection never implies push, release preparation, versions, tags,
  history rewriting, destructive cleanup, or unrelated paths.
- Current versions come from each source `SKILL.md`. Released changes and
  in-progress changes are recorded in [`CHANGELOG.md`](CHANGELOG.md); the README
  does not duplicate the version registry or the full skill contracts.
- Obligations several skills share are written once in
  [`shared/vibe-contract.md`](shared/vibe-contract.md), their single owner. The
  copies inside `skills/` sit between `shared-contract` begin and end markers,
  are generated from that source, are never hand-edited, and are verified by
  `python3 scripts/vibe_shared_contract.py check --strict`.
- The history-mutation, commit-selection, and read-only-phase write gates are
  enforced at the tool call only by hooks you install in your own host
  configuration; this repository ships none. Without them the instruction-only
  wording in [`shared/vibe-contract.md`](shared/vibe-contract.md) is the whole
  gate, and the family behaves as its prose says. Whether Codex honors a hook's
  `ask` or `deny` is `Unproven` until it is observed there. Shell write forms
  such as redirection, `sed -i`, `tee`, a heredoc, `mv`, `cp`, `rm`, or
  `git checkout --` can bypass an edit-tool matcher on either host, so the
  read-only-phase write gate is best-effort even with a hook installed.

## Check Shared Contract Blocks

[`shared/vibe-contract.md`](shared/vibe-contract.md) is the single source of the
contract blocks the `vibe-*` skills share. The rendered copies inside `skills/`
are generated; change the source and re-render instead of editing a copy.

```sh
python3 scripts/vibe_shared_contract.py render
python3 scripts/vibe_shared_contract.py check --strict
python3 scripts/vibe_shared_contract.py audit-names
python3 scripts/vibe_shared_contract.py measure
python3 scripts/vibe_session_record.py check .plans/vibe-sessions/<record-id>.json
```

`render` fills empty marker pairs in the dependent packages and refuses a copy
that drifted from the source unless `--force` is given. `check --strict`
verifies every rendered copy byte for byte against the source and requires each
dependent's markers and class declaration to be complete. `audit-names` reports
any sibling skill name cited outside `skills/vibe-coding/`. The record checker
reports `accept`, `flag`, or `reject` for one session record, with one reason
line per finding. `render`, `check`, and `list` accept `--source PATH`
(default `shared/vibe-contract.md`); `render`, `check`, `audit-names`, and
`measure` accept `--root R` (default `skills`); `check --strict --package <name>`
gates one package on its own, and `render --package <name>` fills only that
package's marker pairs.

A source block whose first non-empty line is a bold lead (`**…**`) is in the
scannable shape and is measured against the shape caps: a lead of at most 25
words opening with `Never`, `Only`, or a listed imperative verb, bullets or
numbered items of at most 40 words (30 in a gate block) with two-space
sub-bullets of at most 30, at most one prose paragraph after the bullets and at
most 35 words long, any prose paragraph at most 60 words, a gate block at most
260 words in total, and a schema block at most 530. Lines beginning `Example:`
are excluded from every count and allowed once per block. A block that stated a
negative rule before the scannable rewrite must still open a lead, bullet, or
sub-bullet with `Never` or `Only`, and every `Appendix S<n>` or `Appendix G<n>`
citation in the source must resolve to its own `###` heading, and a block that
sends the reader to the appendix needs the `## Appendix: hook and record
contract` heading. `check` reports shape faults as warnings and `check --strict`
reports them as errors; a block with no bold lead keeps the legacy shape, is
checked as before, and is reported only as a non-strict `legacy-shape` warning.
`list` marks a scannable block `shape=new`.

Once a scannable block drops its closing boilerplate, the source closes its
blocks once per package rather than once per block: the package then carries one
`closing` block directly below its class line, holding the precedence sentence
and, for a package with a gate or schema block, the applicability sentence. Each
sentence names the blocks it binds and where they sit — every consolidation
block, or every gate and schema block, the package carries in its entry file and
in its references — so the body is one line or two and no line explains the
lines above it. `render` fills that pair like any other, `check --strict`
requires exactly one per package with each owed sentence rendered exactly once
and no generated block outside it carrying either sentence, and both refuse the
pair while the source still closes every block.
Prose outside every block marker — the preamble and any appendix with its
headings, tables, and fenced examples — belongs to the source file rather than
to a block; `list` and `render` ignore it, and `check` applies no block-shape
rule to it while still resolving every `Appendix S<n>` or `Appendix G<n>`
citation it carries.

`measure` prints entry-file lines and words, in-block words, and reference words
per package, then the six routed reading tasks' line and word sums against the
frozen baselines in [`shared/measure-manifest.json`](shared/measure-manifest.json).
`measure --strict` exits 1 unless every task is below its baseline words; the
two durable-records tasks were frozen at their introduction size, so the strict
run exits 1 until their text shrinks or the comparison changes.

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
| `shared/vibe-contract.md` | Single source of the contract blocks the `vibe-*` skills share; rendered into each dependent package as marked generated blocks that are never hand-edited |
| `shared/measure-manifest.json` | Frozen size baselines for the six routed reading tasks that `python3 scripts/vibe_shared_contract.py measure` reports against; the two durable-records tasks were frozen at their introduction |
| `evals/<skill-name>/` | Repository eval definitions, fixtures, and scoring notes |
| `skills/skill-eval/scripts/eval_runner.py` | Shared `validate` / `run` / `report` CLI |
| `CHANGELOG.md` | Keep a Changelog history and the current `Unreleased` buffer |
| `AGENTS.md` | Mandatory repository operating, release, coupling, snapshot, eval, and commit rules |
| `LICENSE` | MIT license for this repository |
| `scripts/sync_dev_agent_skills.py` | Managed local snapshot and Claude-link synchronization |
| `scripts/vibe_shared_contract.py` | Renders, checks, lists, and audits the shared-contract blocks and cross-package name citations |
| `scripts/vibe_session_record.py` | Checks a workflow session record under `.plans/vibe-sessions/` against the shared schema |
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
  a release. Before a release commit, inventory every affected skill across the
  complete accumulated change set, choose versions from the actual contract
  deltas, promote outcome-focused changelog entries, and verify all coupled
  README and reference updates. Do not release only one convenient package while
  other affected skills remain undispositioned.
- Use Conventional Commits and keep commits logically scoped.

See [`AGENTS.md`](AGENTS.md) for the complete repository policy.
