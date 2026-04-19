# Changelog

All notable changes to this repository will be documented in this file.

## 2026-04-19

### Changed

- `codex-review-cycle` v1.2.0 — finding-block summary format, pre-render translation gate, and DoD proposal from in-conversation plans.
  - §Summary Output Template now uses a per-finding compact block instead of an 8-column table: heading `#### F<n> · <severity> · <scope> · <validity> — <codex title>` plus four body bullets (File:Line, Claude's note, Recommended action, codex recommendation verbatim). Each finding's verbatim recommendation moves inside the block, so the bottom-of-summary `Recommendation (per finding)` list is gone. Findings group by `must-fix` → `minimal-hygiene` → `reject-out-of-scope` → `reject-noise` so selectable items come first. Wide tables and `──────` separator blocks are now explicitly forbidden.
  - Verbatim-recommendation containment: the fourth bullet's quoted body handles multi-line or Markdown-shaped recommendations via an escape-safe fenced block whose fence length is `(maxRun + 1)` backticks, where `maxRun` is the longest backtick run in the recommendation body. A fixed 3-backtick fence is forbidden because nested ` ``` ` inside the recommendation would close the wrapper. Single-line recommendations with no Markdown markers stay inline.
  - Step 11 and §Summary Output Template open with a Language pre-render gate: determine the user's output language before writing any output, then translate headings, bullet labels, action values, and footer prose. English labels in the template are marked as placeholders, not literal output.
  - Step 7 makes mode selection explicit (`free-text` → `quick` → `proposal` → `interview`). Proposal mode gets a plan-evidence path: when the conversation already carries an implementation plan with an intent section and an explicit out-of-scope boundary, Claude drafts DoD from the plan instead of running the 6-question interview. The LOC threshold does not apply on this path. Before drafting, Claude assembles a high-signal target evidence block (scope + base ref, top 5 changed files, top 5 commit subjects newest first) and issues a single confirmation `AskUserQuestion` showing the plan reference and this evidence. Multiple plan candidates are disambiguated via a prior `AskUserQuestion`; binding-ambiguity falls back to the interview.
  - `references/summary-samples.ja.md` rewritten for the finding-block format. Bullet labels (including `codex 推奨（原文）`) are translated, stop-signal table column headers render as `シグナル` / `状態` / `根拠`, and the translation note is mandatory rather than permissive. The middle-dot (`·`) separator is preserved across languages.
  - Phase 2 termination output tightened. Every variant now opens with a single-line **verdict headline** — ✅ `Clean termination` / ⚠️ `Terminated with residuals` / ⚠️ `Cap reached` plus `cycles <M>/3`, applied/residual/unresolved counts, and a `trend:` keyword (`converging` / `stable` / `cascading`). Trend is disposition-aware: `converging` requires `R_final == 0` so decline-driven disappearance routes to `stable`, and `cascading` wins the tie-break when any cycle `i >= 2` has `C[i] > C[i-1]`. A new **§Verification Disclaimer** subsection locks the `⚠️ No automated verification …` paragraph as variant-neutral boilerplate; the old `"resolved" claim` sentence (true only under Clean termination) is removed and run-specific content is prohibited inside the block. A new **§Applied-Fixes List** subsection restricts each entry to `F<n> (<scope_category>) <codex title verbatim>`, with implementation prose, rationale, and code snippets prohibited; Case B renders the same list between the disclaimer and the count lines. The render-order directive splits into a visibility rule (step 20 soft-reset renders for branch/base-ref) and a trailing-prose prohibition that does not silence step 20; step 20 silent-skip is strengthened to zero output when `scope == working-tree` or no cycle commits exist.
  - Routing hardened so Case A and Case B predicates do not overlap. Case A is reached only via step 12's V == 0 path (`cycle_history[M].selectable_count == 0` asserted at the start of step 17); Case B is reached only from step 16's `N == 3` branch where `V[3] > 0` by construction. The old path that rendered `Clean termination` after a cycle 3 with V > 0 all-applied is removed. Case B's `<U>` count carries both sub-states — `<U> > 0` (unapplied remain) and `<U> == 0` (every terminal finding applied, no cycle 4 to re-review); Summary blocks render only when `<U> >= 1`, and `<U> == 0` renders a `No unresolved findings.` one-liner under the same heading. Mid-cycle interruption routes through §Failure Modes' cancellation path instead of Case B, because its state contract is not satisfied on abort.
  - State contract extended so Phase 2 reads from persisted fields. `applied_fixes[]`, `user_declined[]`, and `skipped_for_scope[]` entries gain `display_id` (cycle-local `F<n>` from step 9, used by §Applied-Fixes List and residual-line `F<n>`), and the residual buckets gain `cycle_index` for the residual-line `declined in cycle N` token. `selectable_count` is persisted per cycle (V from step 12) as the single source for trend classification. A shared **No-fix cycle-history persist** step covers both terminal V == 0 paths and the `Run cycle N+1` override — without it the terminal V == 0 cycle was absent from `cycle_history`, undercounting `cycles <M>/3` and skewing trend.
  - §Language and `references/summary-samples.ja.md` updated to match: verdict keywords, three trend keywords, disclaimer boilerplate, Applied-Fixes labels, Case B body labels, residual headings, emoji and numeric headline fragments are added to the translate/verbatim lists. The Japanese sample adds Case A clean, Case A residuals, and Case B headline examples plus a translation table (`クリーン終了 / 残存ありで終了 / 上限到達`, `収束 / 安定 / 連鎖`).
- `review-scope-guard` v1.2.0 — plan-evidence proposal path with plan-to-target binding and per-item evidence gate.
  - New optional input `plan_context` (`{source, reference, content, user_confirmed, target_binding}`) carries an in-conversation implementation plan. When `user_confirmed == true` AND `target_binding` is populated, the plan-evidence path of proposal mode activates and the LOC threshold no longer applies.
  - `references/dod-template.md` adds §Proposal-from-plan detection rules: four detection sources (referenced file, conversation paste, earlier turn, explicit user directive), the high-signal confirmation gate (shows top-5 changed files and top-5 commit subjects so stale or adjacent plans cannot quietly anchor a review), multiple-candidate-plan disambiguation, and a binding-ambiguity fallback. The drafting procedure enforces a per-item evidence gate — items 2, 3, 4, 5 each fall back to the interview when the plan lacks the corresponding section, preventing the scope-guard contract from anchoring on fabricated triage anchors. Item 6 remains safe under silent `(not specified)` because its absence widens scope conservatively.
  - SKILL.md §Inputs and Phase 0 step 2 separate the diff-evidence path (gated on `review_target`) from the plan-evidence path (gated on `plan_context`).

## 2026-04-18

### Changed

- `minecraft-modding-workbench` v1.1.0 — align the skill with the current `minecraft-modding` MCP entry-tool surface.
  - `SKILL.md` scope covers Forge-style access transformers (via `validate-project` task `access-transformer`) and the NBT helper family (`nbt-to-json`, `json-to-nbt`, `nbt-apply-json-patch`).
  - MCP Guardrails lists supporting utilities alongside the entry tools: `get-registry-data` for server-generated vanilla registry bodies, `get-runtime-metrics` for cache/search/index diagnostics, and the NBT helpers for typed-JSON round-trip and RFC6902-style in-place edits. `manage-cache` entry now mentions `action: "verify"`. The MCP-unavailable fallback guidance now also covers version skew: when a named tool/task/argument is rejected as unknown, the skill treats it as an older MCP install and falls back to v1.0-compatible paths instead of guessing alternative payload shapes.
  - Fast Debugging Order gains entries for NeoForge access transformer failures (with `atNamespace` discipline), NBT payload schema drift, and cache/index anomalies that start with `get-runtime-metrics` before any mutating `manage-cache` call. The registry/missing-content entry now states that `get-registry-data` returns the vanilla-version entry list only, so absence from its output is not evidence that a modded, dependency, or datapack entry is missing.
  - `references/mcp-recipes.md` adds sections for `get-registry-data`, `get-runtime-metrics`, NBT helpers (decode / re-encode / patch), and a `manage-cache` section covering summary, preview prune, and the `verify` action. The `get-registry-data` section is explicitly scoped to vanilla-version data (no `projectPath`/loader/datapack awareness). The NBT helpers section leads with a `.mca` Anvil-container stop and a live-save-data backup note before the first decode, and narrows the in-scope list from "chunk region" to "extracted chunk payloads". NBT examples preserve the live `{rootName, root: {type, value}}` envelope and use `/root/...` RFC6902 paths with a leading `test` op, matching what `nbt-to-json` actually emits. `inspect-minecraft` gains recipes for the v3 `subject.kind: "artifact"` form (the nested `artifact: { type: "resolved-id" | "resolve-target", ... }` shape), `analyze-symbol` documents `api-overview` and `exact-map`, and `validate-project` gains a workspace summary with `access-transformers` discovery plus a direct access-transformer recipe.
  - `references/task-checklists.md` renames the Mixin checklist to cover access transformers alongside access wideners, clarifies the mapping/namespace discipline for NeoForge ATs, and adds an "NBT or Save Data" checklist. The NBT checklist covers source identification, compression matching, `DataVersion` preservation, typed-JSON envelope discipline, a pre-edit backup requirement for live save data, and an explicit stop on `.mca` region containers.
  - `references/neoforge.md` adds an Access Transformers section covering file location, mod declaration, mojmap/SRG discipline, and minimal-widening guidance.

### Added

- `writing-style-guide` v1.0.0 — principles-first prose-quality skill for
  durable user-facing artifacts: source-code documentation, README,
  CHANGELOG, commit messages, PR descriptions, and chat replies the reader
  keeps. Covers concision, audience fit, meta-acknowledgment removal,
  language precedence (explicit user request > existing artifact language
  > filename locale marker > project convention > English default), and
  artifact self-containment with a durable-traceability carve-out for issue
  IDs, RFC numbers, commit SHAs, and other rename-stable citations. The
  anti-pattern set names the AI-tell vocabulary (marketing language, hollow
  transitions, groundless future claims, forced symmetry, em-dash
  abundance) and name-echoing doc comments; required safety, security,
  data-loss, compliance, and irreversible-action warnings are exempt from
  the unrequested-additions rule. Scope discipline keeps the guide off
  machine-readable output, verbatim relays, transient status lines, and
  bare acknowledgments, and explicit depth requests (rationale, verification
  results, limitations, recovery plans, comparisons) override the concision
  default. Coexistence section defers to project conventions and active
  workflows for procedure; the guide only shapes the words those workflows
  produce.

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
