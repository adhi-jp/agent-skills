# Changelog

All notable changes to this repository will be documented in this file.

## 2026-04-17

### Changed

- `codex-review-cycle` v1.1.0 — DoD collection modes, V=0 override, validity external-source exception, soft-reset preview, and Japanese rendering examples.
  - DoD can be collected in `interview` / `proposal` / `free-text` modes instead of the single-question-per-item flow (Task 2).
  - `cycle_history[N].not_evaluated_signal_names` carries the stop-signal not-evaluated set so cycle 2+ can suppress repeated footnotes deterministically (Task 3).
  - validity item 3 gains an external-source verification exception that surfaces reads outside the review diff as `Claude's note` when such reads changed the verdict (Task 4).
  - when V=0 fires before cycle 3, the user can opt into cycle N+1 with an `<angle_request>` element in `<review_context>`; a `no_fix_cycle: true` marker exempts the cycle-N>1 preflight from the HEAD-advance check to avoid deadlocking branch/base-ref scopes (Task 5).
  - optional `cluster_id` in the rejected-findings ledger groups findings by shared root cause; surfaced in the termination assessment (rejected-ledger scope only) (Task 7).
  - soft-reset previews the accumulated cycle commits (`git log --oneline` + `git diff --stat`) and asks the user to confirm before running `git reset --soft`; README public contract updated to match (Task 8).
  - new reference `summary-samples.ja.md` shows Japanese rendering of summary table, stop-signal footer, and termination messages (Task 9).
- `review-scope-guard` v1.1.0 — DoD out-of-scope requirement, DoD collection modes, state carrier for stop-signal suppression, cluster_id, and Japanese rendering examples.
  - `dod-template.md` now requires ≥3 sibling-framed out-of-scope items in DoD item 4 (Task 1).
  - DoD collection modes — see `codex-review-cycle` entry above (Task 2).
  - `not_evaluated_signal_names` return-value field — see `codex-review-cycle` entry above (Task 3).
  - `cluster_id` field — see `codex-review-cycle` entry above (Task 7).
  - new reference `output-samples.ja.md` shows Japanese rendering of triage table, ledger, and stop-signal footer with a verbatim recommendation block (Task 9).

### Deferred

- G1 (straddle adjudication for DoD-endorsed security-adjacent designs) is intentionally NOT included in this release. Three rounds of adversarial-review surfaced state-ordering and classifier-input-surface concerns that need further design work. Will be re-proposed as a separate plan with explicit `rationale` timing and classifier-lexicon tests.

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
