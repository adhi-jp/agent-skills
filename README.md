# Agent Skills

Codex skill packages maintained in this workspace for public distribution.

## Included Skills

### `minecraft-modding-workbench`

Version-aware Minecraft modding skill for Fabric, NeoForge, and Architectury
projects. It is designed around the `minecraft-modding` MCP server from
`@adhisang/minecraft-modding-mcp` and focuses on full implementation slices,
version-aware debugging, mapping work, mod JAR inspection, and multi-loader
project structure.

### `vibe-planning-guard`

Planning-first skill for turning rough change requests into verified,
option-aware implementation plans. It emphasizes workspace inspection,
evidence-labeled claims, recovery-safe replacement planning, and explicit stop
conditions when implementation blockers remain unproven.

### `codex-review-cycle`

Simple, user-driven 3-cycle review-and-fix workflow on a user-chosen git
review target (working-tree diff, current branch vs. its auto-detected
base branch, or an explicit commit/tag/branch ref), driven by the codex
plugin's `review` or `adversarial-review --json`. The review variant is
chosen once at cycle entry and stays fixed for all three cycles. Each
cycle runs one codex review, Claude verifies findings against a six-item
validity checklist, calls `review-scope-guard` to triage the findings
against an explicit Definition of Done, and the user picks which findings
to address. Claude then applies only the selected fixes before the next
cycle. Hard cap at 3 cycles. Covers both code diffs and markdown planning
documents.

### `review-scope-guard`

Companion skill that triages review findings against an explicit Definition
of Done to separate must-fix bugs from scope creep and noise. Collects a
six-item Definition of Done interactively on first invocation, classifies
every finding into one of four categories (`must-fix`, `minimal-hygiene`,
`reject-out-of-scope`, `reject-noise`), maintains a rejected-findings
ledger, and surfaces five stop signals, though not all are evaluable in
every usage context. Invoked automatically by
`codex-review-cycle` and also usable standalone after any review tool.

## Repository Layout

- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-planning-guard/`: planning and design-review skill package
- `skills/codex-review-cycle/`: codex-driven interactive 3-cycle review-and-fix workflow
- `skills/review-scope-guard/`: Definition-of-Done-aware review finding triage, invoked by codex-review-cycle
- `CHANGELOG.md`: repository-level change history

## Package Contents

Each skill package ships with:

- `SKILL.md`: the main workflow and decision rules

Some packages also include `references/` or other helper assets that are
specific to the skill.

## Notes

- `minecraft-modding-workbench` is scoped to Fabric, NeoForge, and
  Architectury. Legacy Forge-only projects should be treated as a separate
  toolchain check, not as NeoForge by default.
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
  squash them manually later.
- `review-scope-guard` needs a Definition of Done to triage against. On
  first invocation it collects the six DoD items via an interview, a
  Claude-drafted proposal the user confirms, or a pasted block the user
  confirms (three modes). The skill never applies fixes itself — it only
  classifies findings and updates the ledger.
