# Changelog

All notable changes to this repository will be documented in this file.

## 2026-04-15

### Added

- `codex-review-cycle` v1.0.0 — bounded 3-cycle interactive review-and-fix
  workflow driven by the codex plugin's `review` or `adversarial-review
  --json`. Three review target modes: `working-tree` (uncommitted diff),
  `branch` (HEAD vs. auto-detected base), `base-ref` (HEAD vs. explicit
  ref). Each cycle runs one codex review, Claude verifies findings against
  a six-item validity checklist, `review-scope-guard` triages scope, and
  the user selects which findings to fix. Adversarial cycles carry a
  `<review_context>` XML block across cycles. Hard cap at 3 cycles. For
  `branch`/`base-ref` scopes, Claude pauses between cycles for the user to
  manually commit applied fixes before the next cycle proceeds.
- `codex-review-cycle` v1.0.0 references: `focus-text.md`,
  `validity-checklist.md`.
- `review-scope-guard` v1.0.0 — companion skill that triages review findings
  against an explicit Definition of Done. Classifies findings into four
  categories (`must-fix`, `minimal-hygiene`, `reject-out-of-scope`,
  `reject-noise`). Collects a six-item DoD interactively, maintains a
  rejected-findings ledger, and surfaces five stop signals (not all
  evaluable in every usage context). Usable
  standalone or as a companion to `codex-review-cycle`.
- `review-scope-guard` v1.0.0 references: `dod-template.md`,
  `triage-categories.md`, `stop-signals.md`.

## 2026-03-28

### Added

- `vibe-planning-guard` v1.1.0 — behavioral equivalence analysis reference for
  changes touching existing behavior, covering comparison dimensions, scope
  separation, classification, and stop conditions

### Changed

- `vibe-planning-guard` v1.1.0: `SKILL.md` now requires behavioral equivalence
  analysis for changes to existing behavior, escalates uncertain cases to
  `strict`, and expands test-plan and report expectations
- `vibe-planning-guard` v1.1.0: recovery checklist, design exploration
  guidance, and evidence rubric now reference the behavioral equivalence
  analysis workflow

## 2026-03-15

Initial public release of this skill repository.

### Added

- `minecraft-modding-workbench` v1.0.0 — Fabric, NeoForge, and Architectury workflows
- `vibe-planning-guard` v1.0.0 — planning-first implementation work
- references and supporting files for both packaged skills
- repository publication files including `README.md` and `LICENSE`
