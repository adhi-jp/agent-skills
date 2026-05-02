# Agent Skills

Codex skill packages maintained in this workspace for public distribution.

## Current Skill Versions

| Skill | Version |
| --- | --- |
| `minecraft-modding-workbench` | `1.1.1` |
| `vibe-planning` | `1.0.0` |
| `vibe-plan-execution` | `1.0.0` |
| `vibe-planning-guard` | `1.3.0` |
| `codex-review-cycle` | `1.8.0` |
| `review-scope-guard` | `1.4.0` |
| `review-fix-cascade-guard` | `1.0.2` |
| `writing-style-guide` | `1.1.0` |

## Included Skills

### `minecraft-modding-workbench`

Version-aware Minecraft modding skill for Fabric, NeoForge, and Architectury
projects. It is designed around the `minecraft-modding` MCP server from
`@adhisang/minecraft-modding-mcp` and focuses on full implementation slices,
version-aware debugging, mapping work, mod JAR inspection, and multi-loader
project structure.

### `vibe-planning`

Standalone planning skill for turning rough vibe-coding requests into
implementation-ready plans. It supports both technical and non-technical users,
and emphasizes primary-source or local-investigation grounding, plain-language
clarification, acceptance criteria before implementation, tests before code,
explicit handling of unproven assumptions, and output-language selection via
user instruction, `VIBE_PLANNING_OUTPUT_LANG`, agent config, or conversation
language. Editable UI plans also cover state transitions such as save,
cancel/reset, pending, validation, success, and error recovery, and prefer
completing verified existing surfaces before expanding into adjacent unproven
channels or modes.

### `vibe-plan-execution`

Execution companion for `vibe-planning` and equivalent implementation plans. It
binds to the authoritative plan before editing, uses the plan's goal,
requirements, acceptance criteria, test plan, risks, and proceed condition, and
checks assumptions against local evidence or primary sources. It stops on
contradictions or missing implementation facts and requires explicit user
agreement for plan deviations.

### `vibe-planning-guard`

Planning-first skill for turning rough change requests into verified,
option-aware implementation plans. It emphasizes workspace inspection,
evidence-labeled claims, recovery-safe replacement planning, and explicit stop
conditions when implementation blockers remain unproven. It includes a
behavior-contract inventory built before behavioral equivalence analysis,
plan-boundary controls (content classification, success-criteria freeze,
plan-body firewall, completion gate, diagnostic-finding restraint) to keep
review feedback and analyzer warnings from bloating the plan, and a selective
10-category failure-pattern checklist for high-risk surfaces (lifecycle,
exception safety, shared state, migrations, ownership, trust boundary,
accounting, packaging, tool capability, plan drift).

### `codex-review-cycle`

Default 2-cycle interactive review-and-fix workflow on a user-chosen git
review target — working-tree diff, current branch vs. its auto-detected
base, or an explicit commit/tag/branch ref — driven by the codex
plugin's `review` or `adversarial-review --json`. Each cycle runs one
codex review, Claude verifies findings against a six-item validity
checklist, `review-scope-guard` triages them against an explicit
Definition of Done, and the user picks which findings to fix before the
next cycle. After the final cycle's fix phase, a final-cycle assessment block
summarizes addressed findings, checks scope health for self-induced findings,
out-of-context hardening, and target growth, and recommends continue,
new-angle, or end; the user decides whether to terminate or extend the run.
Covers both code diffs and markdown planning documents.

### `review-scope-guard`

Companion skill that triages review findings against an explicit Definition
of Done to separate must-fix bugs from scope creep and noise. Collects a
six-item Definition of Done interactively on first invocation, checks the
out-of-scope anchor for strong sibling-framed finding rejections, classifies
every finding into one of four categories (`must-fix`, `minimal-hygiene`,
`reject-out-of-scope`, `reject-noise`), maintains a rejected-findings
ledger, and surfaces five stop signals, though not all are evaluable in
every usage context. Invoked automatically by
`codex-review-cycle` and also usable standalone after any review tool.
Valid findings still pass through this scope triage; a true premise does
not automatically become a selectable fix.

### `review-fix-cascade-guard`

Containment guard that runs before the agent applies any review-cycle
fix and again after the multi-fix batch is assembled. Prevents the
recurring cascade pattern where a valid finding is patched at the named
line and the next cycle raises a new valid finding the fix itself
created. For each selected finding it restates the invariant in
path-neutral terms, classifies the failure into one of 7 cascade
archetypes, builds a sibling-path matrix, picks an explicit fix
envelope, requires targeted validation, and emits a `gate_status` enum
that controls whether `codex-review-cycle` may apply the edit. After
every per-finding envelope, a Phase 5.5 batch reconciliation pass
catches conflicts across the cycle's combined fix set. Invoked
automatically by `codex-review-cycle` at step 13.6 / step 13.7, and
usable standalone before any review-fix edit. Manual fallback is valid
only when it records the same Phase 3 matrix and Phase 5 validation
evidence as the registered skill path.

### `writing-style-guide`

Principles-first prose-quality skill for durable user-facing artifacts:
source-code documentation, README, CHANGELOG, commit messages, PR
descriptions, release notes, and chat replies. Covers concision,
meaning preservation, no-invented-context discipline, language
precedence, artifact self-containment with a durable-citation carve-out,
exact-format obedience, and concrete handling of supplied statuses such
as tests not run, not measured, or no rollout plan. Required safety,
security, compliance, data-loss, and irreversible-action warnings stay
when they change what the reader should do; generic safety theater and
unsupported rationale are removed. Defers to project conventions and
active workflows for procedure; only the prose quality is this skill's
territory.

## Repository Layout

- `evals/`: repo-level evaluation prompts, fixtures, and scoring notes kept
  outside skill packages
- `evals/vibe-planning/`: external planning eval prompts and fixtures
- `evals/vibe-plan-execution/`: external plan-execution eval prompts and fixtures
- `evals/review-fix-cascade-guard/`: external cascade-guard eval prompts
- `evals/review-scope-guard/`: external scope-guard eval prompts
- `evals/writing-style-guide/`: external prose-quality eval prompts
- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-planning/`: standalone vibe-coding implementation-planning skill package
- `skills/vibe-plan-execution/`: plan-bound vibe-coding implementation skill package
- `skills/vibe-planning-guard/`: planning and design-review skill package
- `skills/codex-review-cycle/`: codex-driven interactive 2-cycle review-and-fix workflow with user-elected extensions
- `skills/review-scope-guard/`: Definition-of-Done-aware review finding triage, invoked by codex-review-cycle
- `skills/review-fix-cascade-guard/`: cascade-containment guard invoked by codex-review-cycle before any fix-application edit
- `skills/writing-style-guide/`: principles-first prose-quality skill for durable artifacts
- `CHANGELOG.md`: repository-level change history

## Package Contents

Each skill package ships with:

- `SKILL.md`: front matter with `version`, `name`, and `description`, followed
  by the main workflow and decision rules

Some packages also include `references/` or other helper assets that are
specific to the skill.

## Notes

- `minecraft-modding-workbench` is scoped to Fabric, NeoForge, and
  Architectury. Legacy Forge-only projects should be treated as a separate
  toolchain check, not as NeoForge by default.
- `vibe-planning` is independent from `vibe-planning-guard`. Use it as the
  primary user-facing planning workflow when the user asks for a plan, spec,
  acceptance criteria, test plan, or rough vibe-coding implementation plan.
- `vibe-plan-execution` is for implementing from an already-bound plan,
  preferably one produced by `vibe-planning`. If no concrete plan exists, use
  `vibe-planning` or another planning workflow before coding.
- `vibe-planning-guard` is for planning, not implementation. It should stay
  light on tiny, already-clear edits unless the user explicitly asks for
  planning or risk review.
- `codex-review-cycle` requires the `codex` Claude Code plugin to be
  installed and `/codex:setup` to be complete. The skill only runs when the
  current directory is a git repository and the chosen review target
  resolves to a non-empty diff. It does not commit files on behalf of the
  user; for `branch` / `base-ref` scopes the skill pauses between cycles
  for the user to manually commit applied fixes. At termination, the skill
  previews the accumulated cycle commits (via `git log --oneline` and
  `git diff --stat`) and asks the user to confirm. On approval it
  collapses the per-cycle commits via soft-reset and leaves all applied
  changes staged for the user to create a single final commit. If the
  user declines, the cycle commits remain in place and the user can
  squash them manually later. For plan targets, the final-cycle
  scope-health judgment uses caller-local baseline and current metrics for
  plan growth; those metrics are separate from `review-scope-guard`'s
  standalone stop-signal inputs.
  Both `codex-review-cycle` and `review-scope-guard` must be registered
  with the Claude Code harness (as marketplace plugins or in the user's
  skill set) for `Skill()` invocation to work. If either skill is not
  registered, open the SKILL.md file and follow the workflow manually —
  the spec is self-contained enough for direct execution.
- `review-scope-guard` needs a Definition of Done to triage against. On
  first invocation it collects the six DoD items via an interview, a
  Claude-drafted proposal the user confirms, or a pasted block the user
  confirms (three modes). The skill never applies fixes itself — it only
  classifies findings and updates the ledger.
- `review-fix-cascade-guard` runs after `review-scope-guard` triage and
  before the agent applies any selected `must-fix` / `minimal-hygiene`
  finding. It does not auto-fix; it returns a per-finding envelope with
  a `gate_status` enum that gates the agent's `Edit` / `Write`. Edits
  are permitted only when both the per-finding gate and the Phase 5.5
  batch gate are `closed` or `accepted-residual`. The override transition
  for `high-cascade-risk` / `invariant-unknown` requires the user to
  explicitly record residuals, surfaces, validation limits, and the
  next-cycle attack via `AskUserQuestion` before the gate flips. Phase 6
  completion notes are mandatory for every applied finding and are
  carried into the next cycle's `<previous_fixes>` `<fix>` named child
  elements; missing notes abort the next cycle's preflight. When the guard
  runs through manual fallback, receipt evidence must show the matrix and
  validation steps actually ran; otherwise `codex-review-cycle` blocks the
  edit as `manual_fallback_evidence_missing`.
