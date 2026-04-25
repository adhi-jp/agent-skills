---
version: 1.3.0
name: codex-review-cycle
description: Run a bounded 3-cycle interactive review-and-fix workflow against a user-chosen git review target (working-tree diff, current branch vs. auto-detected base, or an explicit commit/tag/branch ref) using the codex plugin. Each cycle invokes codex `review` or `adversarial-review --json`; Claude verifies each finding against a six-item validity checklist, calls `review-scope-guard` for Definition-of-Done triage, and the user picks which findings to fix before the next cycle. Covers both code diffs and markdown planning documents. Hard cap at 3 cycles. Use ONLY when the user explicitly asks to run the codex review cycle on working-tree changes, a committed branch diff, or an explicit base ref. Do NOT trigger for single-shot review requests, auto-hardening, background reviews, plan drafting, or when the chosen target would produce an empty diff.
---

# Codex Review Cycle

## Overview

A simple, user-driven review-and-fix workflow. Every cycle runs one codex review, Claude verifies each finding's validity, presents a verbatim summary, and the user picks which findings to address. Claude then applies only the chosen fixes and loops. Three cycles is a hard cap — the loop never runs a fourth cycle without the user starting a new invocation.

The skill is deliberately simple. It does not auto-fix, does not run parallel reviewers, does not compute stall fingerprints, does not manage autonomy bands, and does not delegate to rescue subagents. Claude is the only fix applier; the user is the only arbiter of which findings matter.

## Language

All user-facing output is rendered in the user's language (the language the user has been using in the conversation, or as configured in the Claude Code system-level language setting). This section is the **authoritative translation contract** — any per-language sample reference (e.g. `references/summary-samples.ja.md`) is illustrative only and MUST NOT contradict these rules.

**Translate into the user's language:**

- Section headings (e.g. `Cycle N review summary`, `Active stop signals`, `Review assessment`)
- Per-finding bullet labels (`File`, `Claude's note`, `Recommended action`, `codex recommendation (verbatim)`) and stop-signal table column headers (`Signal`, `Status`, `Evidence`)
- Free-text fields Claude authors: `Claude's note` body, `Recommended action` values, fleet-rate warnings, stop-signal footer prose, termination messages, post-cycle review assessment
- Verdict headline free-text (see `references/termination.md` §Verdict Headline): the three verdict keyword labels (`Clean termination`, `Terminated with residuals`, `Cap reached`), the segment wordlets (`cycles`, `fix(es) applied`, `applied`, `residual`, `unresolved`, `trend`), and the three trend keyword values (`converging`, `stable`, `cascading`)
- Verification disclaimer heading and body (see `references/termination.md` §Verification Disclaimer) — rendered as fixed boilerplate, but the canonical English text is translated; the parenthetical verification-type enumeration (`test suite, type check, lint, build, manual smoke`) is translated as a fixed generic list, not substituted with run-specific content
- Applied-fixes list labels (see `references/termination.md` §Applied-Fixes List): the `Applied fixes by cycle` heading, the per-cycle `Cycle <N>:` prefix, and the no-fix label (canonical English: `none`). Residual-list headings in the residuals variant (`User-declined valid findings carried to termination`, `Out-of-diff skipped findings carried to termination`) also translate
- Case B cap-reached body labels: `Cycles run`, `Findings applied`, `Findings still valid and unresolved at cap`, `Unresolved valid findings`, `Next steps`, the three `Next steps` option lines, and the `No unresolved findings.` one-liner that replaces the Summary blocks when `<U> == 0`
- `AskUserQuestion` `question`, `header`, and option `label` / `description` fields

**Keep verbatim (do NOT translate), regardless of user language:**

- Codex `title` field (appears unquoted in each finding's heading per `references/summary-template.md`, AND inside each applied-fix entry / residual-list entry per `references/termination.md` §Applied-Fixes List)
- Codex `recommendation` field (quoted inside each finding's last bullet per `references/summary-template.md`)
- Severity values (`high` / `medium` / `low`) — codex output
- Validity outcome keywords (`valid` / `partially-valid` / `invalid`)
- Scope category names (`must-fix` / `minimal-hygiene` / `reject-out-of-scope` / `reject-noise`) — applies both inside Summary blocks and inside the Applied-Fixes List's `F<n> (<scope_category>)` prefix
- Stop-signal `Status` keywords (`ACTIVE` / `ADVISORY` / `WARNING` / `silent`)
- Heading middle-dot separator (`·`, U+00B7) between the `F<n> / severity / scope / validity` segments, AND between verdict-headline segments
- Verdict-headline emoji (`✅`, `⚠️`) — rendered literally
- Verdict-headline numeric fragments (`<M>/3`, `<F>`, `<R>`, `<A>`, `<U>`) — digits and the `/3` separator stay literal
- Cycle-local finding IDs (`F<n>`) — the `F` letter and the integer stay literal in every rendering context (Summary blocks, Applied-Fixes List, residual lists)
- Technical identifiers: file paths, git refs (SHAs, branch names), `fingerprint`, `cluster_id`, field names like `applied_fixes`, `not_evaluated_signal_names`
- Cycle indices (`cycle N`, `N/3`)

For a Japanese rendering example that applies these rules, see `references/summary-samples.ja.md`. For German, Korean, or other languages, apply the same rules directly — the Japanese sample is an illustration, not a template to translate.

## When to Use

Use this skill ONLY when:

- The user explicitly asks to run the codex review cycle on one of: the current working-tree diff, the current branch vs. its base branch, or an explicit commit/tag/branch ref, and
- The current working directory is a git repository, and
- The chosen review target produces a non-empty diff (working tree has uncommitted changes, or HEAD is ahead of the chosen base ref).

Do NOT use this skill when:

- The user wants a single codex review pass — use the codex plugin directly.
- The resolved review target produces an empty diff — stop and tell the user.
- The user is drafting a plan from scratch — use `vibe-planning-guard` instead.
- A review is running as a background or automatic check.

## Review Target Modes

The skill supports three review targets, chosen once at Phase 0 and fixed for all three cycles:

- **`working-tree`** — uncommitted changes (tracked-modified + staged + untracked). Codex is invoked with `--scope working-tree`. Claude-side diff commands use `git diff HEAD --name-only` plus `git ls-files --others --exclude-standard` for untracked files.
- **`branch`** — HEAD vs. the auto-detected default branch (tries local `main`/`master`/`trunk` first, then `origin/*`). Codex is invoked with `--base <base_sha>` (frozen SHA resolved from the detected ref at Phase 0). Claude-side diff commands use `git diff --name-only <base_sha>...HEAD` (triple-dot: merge-base semantics).
- **`base-ref`** — HEAD vs. an explicit ref the user supplies (any commit SHA, tag, or branch name). Codex is invoked with `--base <base_sha>` (frozen SHA resolved from the user-supplied ref at Phase 0). Claude-side diff commands use `git diff --name-only <base_sha>...HEAD`.

The three modes share the same workflow — only the Phase 0 target-resolution step, the codex CLI flags, and the diff command Claude uses for validity checks differ.

**Codex internal diff-collection modes** (adversarial-review only, codex plugin ≥ 1.0.4): for diffs exceeding roughly 2 changed files OR ~256KB of patch bytes, codex omits the inline diff, receives only a lightweight target summary, and runs its own read-only `git` commands to inspect the diff before finalizing findings. The summary shape differs by target: `working-tree` self-collect embeds `git status` (`--untracked-files=all`), staged/unstaged `--shortstat`, a changed-files list, and bounded per-file content for untracked files; `branch` / `base-ref` self-collect embeds the commit log, `--stat`, and a changed-files list over `<base_sha>..HEAD`. Neither mode ships the raw patch. Target stability differs by mode: `branch` / `base-ref` are immutable because `--base <base_sha>` (resolved once at Phase 0) pins the self-collected diff to the same commit range the skill targeted; `working-tree` is a live snapshot-at-invocation — `--scope working-tree` has no `base_sha` equivalent, so concurrent worktree mutation during collection changes what self-collect reads. Validity items 1 and 4 re-check every finding's `file` and `line_start` against the skill's own `review_target.diff_command` output regardless of which collection mode codex chose.

## Target Kinds

The skill auto-detects `code` vs `plan` from the diff file extensions. See `references/focus-text.md` for the detection rules. Mixed targets (any code file present) are treated as `code`; item 6 of `references/validity-checklist.md` filters out detailed-design findings on markdown files inside a code cycle.

## Review Variant Selection

At Phase 0, ask the user once which codex review variant to use for all three cycles:

- **`review`** — codex's native review command. Output is free-form text. Claude manually structures each finding section into `title` / `recommendation` / `body` before running the validity check.
- **`adversarial-review`** — codex's adversarial review with `--json`. Output is structured `findings[]`. Each element has `severity`, `file`, `line_start`, `title`, `recommendation`, `body`. Adversarial cycles also carry a `<review_context>` block (see `references/review-context.md`) so codex keeps the same angle across cycles.

The choice is fixed for the whole loop. If the user wants to switch variants, they must restart the skill.

**Recommendation**: use `adversarial-review` unless there is a specific reason not to. The `review` variant is retained for environments where structured JSON output is unavailable or for users who specifically want free-form codex output, but it operates in a **minimum-functionality mode**: no `<review_context>` carry across cycles, no proposal-mode DoD (interview only), no V=0 cycle-N+1 override, no rejected-findings forwarding. Expect to get a single-shot review that Claude structures manually, with no adaptation between cycles. For multi-cycle review-and-fix workflows, adversarial-review is strictly the better path.

## Workflow

### Phase 0 — Preflight (runs once)

1. **Verify git repository.**
   - `Bash`: `git rev-parse --is-inside-work-tree` — stop if not inside a git repo.
2. **Resolve the review target.** Ask the user once, via `AskUserQuestion`, which review scope this cycle should cover. Offer three options:
   - **`working-tree`** — review the uncommitted diff (tracked-modified + staged + untracked).
   - **`branch`** — review HEAD vs. the auto-detected default branch.
   - **`base-ref`** — review HEAD vs. an explicit ref the user provides.

   After the scope choice:
   - `working-tree`: no additional input needed.
   - `branch`: auto-detect the default branch by trying `main`, `master`, `trunk` as local refs via `git show-ref --verify --quiet refs/heads/<name>`, then falling back to `origin/<name>`. If none resolve, stop with `Could not auto-detect a base branch. Re-run with scope = base-ref and supply a ref explicitly.`
   - `base-ref`: ask a follow-up free-form `AskUserQuestion` for the ref string. Validate it with `git rev-parse --verify <ref>` — if the command fails, stop with `Base ref '<ref>' not found in this repository.`

   Store the result as `review_target`. **Fully construct the object in Phase 0 so proposal DoD mode in step 7 has the data it needs**:
   - `scope` — one of `working-tree`, `branch`, `base-ref`.
   - `base_ref` — `null` for `working-tree`; the resolved ref **string** for `branch` and `base-ref` (kept as display metadata only).
   - `base_sha` — `null` for `working-tree`; for `branch` / `base-ref`, the **immutable commit SHA** resolved from `base_ref` at Phase 0 via `git rev-parse <base_ref>`. All subsequent commands across all 3 cycles (codex `--base`, diff commands, commit-range enumeration, validity-check scope diff, Part B ownership audit, soft-reset anchor) use `base_sha`, never `base_ref`, so a mutable ref (e.g. `main`, `origin/main`) advancing mid-run cannot drift the review target. If `base_ref != base_sha` at any later check (user manually updated the ref), print a one-line warning `Base ref '<base_ref>' moved from <base_sha> during the run; continuing against the frozen SHA.` and proceed.
   - `diff_command` — the exact `git diff --name-only …` command Claude will reuse for target-kind detection and validity checks:
     - `working-tree` → `git diff HEAD --name-only` (paired with `git ls-files --others --exclude-standard` for untracked files)
     - `branch` / `base-ref` → `git diff --name-only <base_sha>...HEAD` (triple-dot: merge-base semantics; uses the **frozen SHA**, not the mutable `base_ref`, so target-kind detection and validity checks cannot drift if the named ref advances mid-run)
   - `diff_files` — the executed output of `diff_command`. **For `working-tree` scope, this MUST be the union of `git diff HEAD --name-only` and `git ls-files --others --exclude-standard` (tracked-modified + staged + untracked)**; omitting untracked files would undercount the actual review surface. For `branch` / `base-ref` it is just the `diff_command` output.
   - `diff_numstat` — for `branch` / `base-ref`: `git diff --numstat <base_sha>...HEAD`. For `working-tree`: `git diff --numstat HEAD` **PLUS** a synthesized per-untracked-file line count (e.g. `wc -l` on each untracked file, emitted in the same `<added>\t<deleted>\t<path>` shape as numstat so the total LOC calculation is uniform). Omitting untracked line counts — as an earlier draft did — would let an untracked-only working-tree diff (100% new files) report 0 numstat LOC and silently qualify for proposal-mode DoD with no commit messages or patch to ground intent. Used to size the diff for the proposal-mode threshold (≤ ~100 changed LOC).
   - `commit_range` — `null` for `working-tree`; `<base_sha>..HEAD` (double-dot, using the **frozen SHA** for commit-delta enumeration) for branch / base-ref. NOTE: diff uses triple-dot (merge-base), commit enumeration uses double-dot (exact commits on HEAD that are not on base). Using `base_sha` (not `base_ref`) keeps enumeration stable against mid-run ref movement.
   - `commit_messages[]` — `[]` for `working-tree`; `git log --format='%s%n%b' <commit_range>` splits for branch / base-ref, trimmed per commit. Derives from the frozen-SHA `commit_range` above. Proposal-mode DoD drafting reads these to ground item 1 (intent) and item 4 (out-of-scope) in what the commits actually claim.
   - `diff_patch_excerpts` — bounded content-bearing evidence: a handful of representative files shown mostly in full (small untracked files, key tracked hunks), trimmed with `[truncated — <M> more lines]` when needed. Keep the total roughly on the order of a few KB so the proposal-mode prompt stays manageable. The goal is "enough for Claude to infer intent and out-of-scope boundaries", not byte-exact compliance.
     - **`working-tree`**: always synthesize.
     - **`branch` / `base-ref`**: omit only when the proposal-mode evidence gate is already satisfied by commit messages (≥20-char subject + non-empty body in at least one commit in scope). If the evidence gate fails on messages alone — squashed / templated / vague commits — synthesize excerpts **sourced exclusively from the target commit range** (`git diff <base_sha>...HEAD` output), never from local working-tree state or untracked files, using the same bounded-budget shape as `working-tree`. If the range cannot yield a usable excerpt (binary-only, no textual diff), fall back to `interview` mode. This preserves the existing invariant that DoD drafting for branch/base-ref never anchors on a short squash-commit title AND never leaks out-of-range evidence into the proposal.

   **Proposal-mode evidence gate**: even when `diff_numstat` totals ≤ 100 LOC, proposal mode requires content-bearing evidence.
   - For `working-tree` scope: if `commit_messages[]` is empty AND `diff_patch_excerpts` has no non-blank content (e.g. all untracked files are empty or binary, or all tracked-modified hunks collapsed to no patch), fall back to `interview` mode — filenames and line counts alone cannot draft six DoD items with enough fidelity.
   - For `branch` / `base-ref` scope: commit messages alone are NOT sufficient evidence. Squashed, templated, or vague messages like `"fix review comments"`, `"wip"`, `"update tests"` can pass the LOC threshold while giving proposal mode no usable intent or out-of-scope signal. Require that `commit_messages[]` contain at least one commit with a subject of **≥20 characters AND a non-empty body**, OR fall back to populating `diff_patch_excerpts` for branch/base-ref (same budget-based heuristic as working-tree) and passing it forward. If neither evidence path is available — all commit messages are short/empty and no patch excerpts are synthesized — fall back to `interview` mode. The risk this gate blocks is a DoD drafted from the title of a squash commit, which then anchors `reject-out-of-scope` decisions for the whole run.

   Every cycle reuses the same `review_target` so the diff scope stays stable even after fixes are applied.
3. **Verify the target has a non-empty diff.**
   - `working-tree`: `git status --porcelain` must be non-empty. If empty, stop with `No working-tree diff to review. The codex-review-cycle skill requires uncommitted changes when scope is working-tree.`
   - `branch` / `base-ref`: `git diff --name-only <base_sha>...HEAD` (use the frozen SHA from step 2, not the mutable `base_ref`) must be non-empty. If empty, stop with `No committed changes between <base_ref> (<base_sha>) and HEAD. The codex-review-cycle skill requires a non-empty diff for branch/base-ref scopes.`
4. **Ensure codex is ready.** Invoke `Skill(codex:setup)` once to confirm the codex CLI is configured. Stop if setup reports a blocking failure.
5. **Detect target kind.**
   - Run `review_target.diff_command`. For `working-tree`, also run `git ls-files --others --exclude-standard` and union the untracked list with the diff output.
   - Apply the extension rules in `references/focus-text.md`.
   - Record `target_kind` as either `code` or `plan`.
6. **Ask for review variant** (once, via `AskUserQuestion`). Two options: `review` and `adversarial-review`. Store the choice as `variant`.
7. **Pre-collect DoD (adversarial only) and initialize cycle state.** Set `rejected_ledger = []`, `cycle_history = []`, `dod = null`.
   - If `variant == adversarial-review`, collect the six-item Definition of Done now by invoking the collection flow in `skills/review-scope-guard/references/dod-template.md` §Collection Modes, passing the fully-constructed `review_target` from Phase 0 step 2 (including `diff_files`, `diff_numstat`, `commit_messages[]`, `diff_patch_excerpts`) as the proposal-mode input contract, plus any `plan_context` detected below. Mode selection order (first matching rule wins):
     1. **`free-text`** — the user already pasted a DoD block in the conversation.
     2. **`quick`** — the user explicitly said "quick DoD" / "minimal DoD" / similar AND `review_target.diff_numstat` totals ≤ ~30 LOC.
     3. **`proposal`** — EITHER (a) `review_target.diff_numstat` totals ≤ ~100 LOC AND commit-messages or patch excerpts provide content-bearing evidence (the diff-evidence path), OR (b) an **in-conversation implementation plan** is available (the plan-evidence path; LOC threshold does not apply because the plan anchors scope independently of diff size). For the plan-evidence path: capture the plan as `plan_context` per `dod-template.md` §Proposal-from-plan detection rules, and assemble a **high-signal target evidence block** from the Phase 0 step 2 tuple — scope + base ref, top 5 changed files (`review_target.diff_files`, lexicographic, suffix `+N more` when >5), and top 5 commit subjects newest first (`review_target.commit_messages[]`, omitted for working-tree scope). Issue one confirmation `AskUserQuestion` showing both the plan reference and this evidence block; on `yes`, persist the evidence block verbatim as `plan_context.target_binding`. Disambiguate multiple plan candidates via a prior `AskUserQuestion` before the main gate. Skip the gate and fall through to rule 4 when the plan references a different target, the evidence block cannot be computed, or the user declines.
     4. **`interview`** — default when no rule above fires. Also the mandatory fallback when `review_target` is incomplete (defensive check; Phase 0 step 2 should have populated every field) per the scope-guard input contract.

     Cache the result on `dod` so `<review_context cycle="1">` `<intent>` can be populated from DoD item 1 before step 8 runs. Pass the cached `dod` (not `null`) to `review-scope-guard` at step 10a so the scope-triage skill does not re-ask. This solves the cycle-1 dependency where `<review_context>` would otherwise need intent that had not yet been collected.
   - If `variant == review`, leave `dod = null` here. Native review does not carry `<review_context>`, so there is no early-intent dependency. Step 10a's first `review-scope-guard` invocation will collect DoD interactively at that point.

   Also record `pre_cycle_1_head = git rev-parse HEAD` — this is the anchor for the step 20 soft-reset at termination. For `working-tree` scope this value is unused.

   Subsequent cycles reuse the cached DoD and pass the running `rejected_ledger` / `cycle_history` forward.

### Phase 1 — Review Cycle (repeats up to 3 times; counter `N = 1..3`)

8. **Run the review.** Compute `codex_scope_args` from `review_target.scope`:
   - `working-tree` → `--scope working-tree`
   - `branch` → `--base <review_target.base_sha>` (frozen SHA from Phase 0; NOT `base_ref`, which is mutable)
   - `base-ref` → `--base <review_target.base_sha>`

   **Cycle-N>1 preflight** (`branch` / `base-ref` only): before invoking codex on cycle 2 or 3, verify the state between cycles is as expected. Let `expected_commit = !cycle_history[N-1].no_fix_cycle` (true for normal fix cycles, false for V=0 no-fix retries). Run the following single-pass check:

   - **HEAD movement**: compare `git rev-parse HEAD` against `cycle_history[N-1].pre_pause_head`.
     - If `expected_commit` is true: HEAD MUST have advanced. If equal, the user never committed — re-issue the step 14 manual-commit instruction.
     - If `expected_commit` is false (V=0 retry): HEAD MUST equal the stored head. If HEAD moved, the user pulled or committed unrelated work during the override pause; halt with `⚠️ HEAD changed during the V=0 override pause. Retry cycle would review an expanded target. Restart the skill or revert the changes.`
   - **Working-tree cleanliness**:
     - When `expected_commit` is true: `git status --porcelain -- <cycle N-1's touched_files>` MUST be empty (path-restricted to the fix set; staged/unstaged remnants of applied fixes block the cycle). Untracked files unrelated to the review_target are exempt.
     - When `expected_commit` is false (V=0 retry, no touched_files exists): `git status --porcelain` with **no path restriction** MUST be empty, excepting untracked files unrelated to the review_target. This is strictly wider than the expected_commit=true check because no commit was made — any change to tracked files during the override pause would expand the review target and invalidate the retry. On failure, halt with `⚠️ Working tree changed during the V=0 override pause. Retry cycle would review an expanded target. Restart the skill or revert the changes.`
   - **Commit-delta coverage** (only when `expected_commit` is true): `git diff --name-only <pre_pause_head>..HEAD -- <touched files>` must be non-empty AND must cover every file in cycle N-1's `applied_fixes[*].touched_files[]` list. Any touched file missing from this delta means the user's commit did not include that file. A legitimate fix that reverts a file back to base is still a valid commit delta even though the file disappears from `<base_sha>...HEAD` — this variant catches that case because it queries the commit-delta range, not the branch-total range. Skipped entirely for V=0 retries (no commits to audit).
   - **Cycle-commit ownership (warn-and-confirm)** (only when `expected_commit` is true): compare the full commit-delta path list against cycle N-1's `touched_files`. Run `git diff --name-only <pre_pause_head>..HEAD` (no path restriction) and let `committed_paths` be that output. Paths in `committed_paths` that are NOT in cycle N-1's `touched_files[]` are *unrelated* — typically lint autofixes, typo repairs, or adjacent cleanups the user bundled into the cycle commit. Rather than abort (previous behavior, which was hostile to `git commit -am` usage), surface them via a single `AskUserQuestion`:
     - `question`: "Cycle N-1 commit includes <K> path(s) that Claude did not touch: <full path list>. These will be preserved by the terminal soft-reset and ship in the final squash. Keep them as part of this review's squash, or abort for amend-drop?"
     - options:
       - `Keep (continue to cycle N)` — record the extras in `cycle_history[N-1].unrelated_commit_paths[]` for the step-20 Part B audit to surface again at terminal reset. Proceed to cycle N.
       - `Abort to amend` — print `Amend your cycle N-1 commit to drop the unrelated paths, then reply continue.` and pause the skill like the manual-commit gate in step 14.
     Rationale: the hard-abort form of this check rejected normal developer workflows. Warn-and-confirm preserves the signal (user sees unrelated paths per-cycle) without blocking lint-fix-plus-cycle-fix commits. Skipped entirely for V=0 retries.

   On any mismatch of the bullets above, do NOT proceed. Print a compact explanation naming the specific check that failed and re-issue the step 14 manual-commit instruction (or the V=0 restart message). Wait for the user to correct the state and reply `continue`. Do not silently review stale state.

   Then:
   - `variant == review`:
     ```
     node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" review --wait <codex_scope_args>
     ```
     Capture stdout as free-form text.
   - `variant == adversarial-review`:
     ```
     node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" adversarial-review --wait --json <codex_scope_args> "<focus_text_with_context>"
     ```
     `<focus_text_with_context>` is the target-kind focus text from `references/focus-text.md` followed by the `<review_context>` block (see `references/review-context.md`). Parse stdout as JSON.
   - **Parse-retry policy** (adversarial only): if JSON parsing fails or any required field is missing (`findings[]`, `severity`, `file`, `line_start`, `title`, `recommendation`), retry the exact same call **once**. A second failure aborts the cycle, surfaces codex's raw stdout verbatim to the user, and ends the skill.
9. **Extract findings and assign IDs `F1..Fn`.**
   - `adversarial-review`: use `findings[]` as-is.
   - `review`: Claude manually slices the free-form output into finding blocks. Each block must have a `title` (first line of the block, verbatim), a `recommendation` (the action codex suggests, verbatim), a best-effort `file`, and `line_start` (resolve from context, leave null if codex did not cite a location). Findings without at least a `title` and a `recommendation` are dropped with a note in the summary.
10. **Run the validity check silently.** For every finding, run the six items in `references/validity-checklist.md` **without echoing the per-item trace** to the user. Every item still requires Claude to Read the cited file internally — do not trust codex's body alone — but file reads and item-by-item reasoning are internal only. Assign each finding a three-value outcome: `valid`, `partially-valid`, or `invalid`. Record a short `Claude's note` (≤20 words) for every finding regardless of outcome — for `valid` findings, note the primary reason the finding is grounded (e.g. "confirmed by reading cited lines", "DoD required feature violation"); for `partially-valid`/`invalid`, note the rejection reason. When multiple findings cite the same file, issue a single `Read` call covering the union of cited ranges and reuse the result for every item-2/item-3/item-4 check — do not re-read the same region per finding.

    **External-source rule (warning-only)**: external reads (dependency crate sources, standard library docs, upstream README) are allowed as *background evidence* for Claude's internal reasoning, but they MUST NOT flip the validity verdict. The verdict is always determined from the review diff itself plus what the finding claims. If an external read contradicts or confirms the finding, record it as `Claude's note: background — <source>: <what it showed>` without changing the outcome. The silent-trace rule still holds for validity determined solely from the diff — the `background` note is only emitted when Claude actually consulted an external source. This rule replaces an earlier "External-source exception" that allowed verdict-flipping with version-pinned sources; in practice Claude cannot reliably pin dependency versions, and the safe constraint is to forbid verdict-flipping entirely.

    **No severity-based tiering**: item 3 (premise matches artifact) is mandatory for every finding that could become selectable. Read tiering was considered (skip item 3 on medium/low) but rejected: self-consistency between title and recommendation does not prove the artifact actually has the claimed behavior. Skipping item 3 would let invalid medium/low findings reach the user-selection UI, which is exactly the silent-hallucination failure mode the validity check exists to catch. The Read cost (1 Read per unique cited file, shared across findings in that file via the union rule above) is acceptable; tiering's savings do not justify the safety weakening.
10a. **Run scope triage via `review-scope-guard`.** Invoke `Skill(review-scope-guard)` passing `findings[]` (with the validity outcomes already attached), the cached `dod` (pre-collected in step 7 when variant is adversarial; null on cycle 1 for review variant — the skill will collect it interactively then), the running `rejected_ledger`, `cycle_history` (for stop-signal evaluation), **and `review_target` (already fully constructed in Phase 0 step 2 — pass it verbatim without re-deriving any field)**. Phase 0 step 2 guarantees `review_target` carries the full `{scope, base_ref, base_sha, diff_command, diff_files, diff_numstat, commit_range, commit_messages[], diff_patch_excerpts}` tuple; step 10a simply forwards it. **Do not drop `diff_patch_excerpts`** — scope-guard's proposal-mode evidence gate consumes it for working-tree targets where `commit_messages[]` is empty. The caller MUST pass `review_target` so scope-guard's `proposal` DoD mode has an authoritative source; without it, scope-guard falls back to `interview` mode (see scope-guard §Inputs). The skill returns a triage verdict per finding (`must-fix` / `minimal-hygiene` / `reject-out-of-scope` / `reject-noise`), an updated `rejected_ledger`, a set of active stop signals, and the collected `dod` (on cycle 1). Cache the DoD for later cycles. Store the triage verdicts alongside each finding for step 11. When DoD is missing, the skill still returns classifications inside the 4-category invariant (fall-through lands in `minimal-hygiene`); render the degraded-mode warning as documented in Failure Modes.
11. **Render the summary.** First apply the Language pre-render gate in `references/summary-template.md`: determine the user's output language and translate all non-verbatim elements (heading text, bullet labels, action values, footer prose) before writing any output. Then render using the **per-finding block format** in `references/summary-template.md`. Every finding appears as its own block, including `invalid` and `reject-*` ones. Each finding's `recommendation` field is quoted verbatim inside that finding's last bullet (per `references/summary-template.md` body-bullet rules). The active stop signals footer is rendered when (a) any signal has status `ADVISORY`/`ACTIVE`/`WARNING`, OR (b) any signal is `not evaluated: metrics missing`. Omit the footer only when every signal is truly `silent`. When the footer renders solely due to `not evaluated` rows, print a compact one-line notice — `<Not-evaluated-metrics-missing label translated>: <comma-separated signal names>` — instead of the full signal table.

    **Structurally-unevaluable compaction**: subtract `structurally_unevaluable_signal_names` from the `not_evaluated_signal_names` set before rendering. The structurally-unevaluable names are shown once in cycle 1's footer as `_Stop signals unavailable in codex-review-cycle integration: <names> (standalone invocation required for full 5-signal surface)._` and omitted from cycle 2+ footers entirely. This replaces the previous behavior where `file-bloat` / `reactive-testing` appeared in every cycle's `Not evaluated` list.

    Additionally, starting from cycle 2, compare the **current-cycle `not_evaluated_signal_names`** (taken from `review-scope-guard`'s return value received in step 10a of the current cycle — NOT from `cycle_history[current]`, which is only appended later in step 15) against **`cycle_history[N-1].not_evaluated_signal_names`** (the immediately previous cycle, not cycle 1) using the element-wise-equal semantics in `review-scope-guard/references/stop-signals.md` §Per-cycle suppression. Comparing against N-1 (not cycle 1) prevents flapping from being masked: a set that differs from cycle 1 → matches cycle 2 → differs from cycle 3 would otherwise be silently suppressed if only the cycle-1 baseline were checked. This ordering is required because step 11 runs before step 15 persists the current cycle's entry; reading `cycle_history[current]` at step 11 would read stale or empty state. If the two lists are equal, print `_Not evaluated: unchanged from cycle N-1 — see cycle N-1 summary for signal list._` instead of re-listing the names. If they differ, re-render the full list AND add `_Not evaluated delta vs cycle N-1: added=<names>, removed=<names>._` so the change is visible. The canonical order guarantees ordering-only differences cannot occur; guard for them anyway.

    **Validity fleet-rate check** (plan targets only, ≥5 findings): if the current cycle has ≥5 findings and 100% are classified `valid`, print a single-line calibration warning at the bottom of the summary: `⚠️ 100% valid rate with ≥5 findings is unusual for adversarial-review on plan targets. Re-scan for: (1) vague recommendations that should be 'partially-valid: vague', (2) already-handled premise that should be 'invalid: misread', (3) design-intent reversals that should route through scope triage as 'reject-out-of-scope' instead of being accepted as must-fix.` This is a soft prompt, not a hard gate — the cycle proceeds normally. Raised threshold (was ≥3) and plan-only scope prevent false alarms on small focused diffs, where 3 valid findings is a normal outcome.
12. **Zero-valid check.** Let `V` be the count of findings whose validity outcome is `valid` or `partially-valid` **and** whose scope category is `must-fix` or `minimal-hygiene`. `reject-out-of-scope` and `reject-noise` findings are never counted as selectable, even if their validity outcome was `valid`. If `V == 0`:
    - If `N == 3` (final cycle): run the **No-fix cycle-history persist** step below (terminal path), then jump to Phase 2 Case A — the cap has fired.
    - If `variant == review` (native): run the **No-fix cycle-history persist** step below (terminal path), then jump to Phase 2 Case A. The V=0 override is not available for native review because the `review` command accepts neither a focus-text argument nor a `<review_context>` block — no channel can deliver an `<angle_request>`. Re-running the same command on the same diff would be a hidden no-op that still burns a cycle. The override is scoped to `variant == adversarial-review`.
    - If `N < 3` **and** `variant == adversarial-review`, issue a single `AskUserQuestion` before terminating:
      - `question`: "No selectable findings this cycle. Terminate the review, or run one more cycle with a different angle request?"
      - options (translate to user language per §Language):
        - `Terminate now (Case A)` — run the **No-fix cycle-history persist** step below (terminal path), then proceed to Phase 2 Case A.
        - `Run cycle N+1` — run the **No-fix cycle-history persist** step below (N+1 path), then re-enter step 8 with `N = N + 1`. The next cycle's `<review_context>` carries a one-line `<angle_request>` element: `<angle_request>Prior cycle produced 0 selectable findings. Try a materially different angle — e.g. a deeper root-cause pass, a different subsystem emphasis, or a scope that cuts across files not yet reviewed.</angle_request>` inserted between `<previous_fixes>` and `<rejected_findings>`.

    **No-fix cycle-history persist** (shared by the terminal V=0 paths — `N == 3`, `variant == review`, user-selected `Terminate now (Case A)` — and the `Run cycle N+1` branch): step 15's normal persist never runs in a V=0 cycle, so Phase 2 renderers would otherwise see the terminal cycle missing from `cycle_history`, undercounting `cycles <M>/3` and skewing trend classification. Append a `cycle_history` entry with:

    - `applied_fixes: []`, `user_declined: []`, `skipped_for_scope: []`.
    - `claude_invalid`: populated from the current validity check; carries into the next cycle's `<review_context>` `<rejected_findings>` via the normal ledger union.
    - `not_evaluated_signal_names`: `review-scope-guard` step 11's current return.
    - `pre_pause_head`: `null` for working-tree; `git rev-parse HEAD` otherwise.
    - `no_fix_cycle: true` — the step 8 cycle-N>1 preflight consumes this marker to set `expected_commit = false` (HEAD unchanged, full worktree clean, commit-delta/ownership checks skipped).
    - `selectable_count: 0` — the uniform trend-classification field; normal fix cycles record V at step 15.

    Also persist the current `rejected_ledger` for forwarding. On the terminal path, proceed to Phase 2 Case A after persisting. On the `Run cycle N+1` branch, re-enter step 8 with `N = N + 1`.

    The override path is bounded by the existing 3-cycle cap: requesting cycle N+1 from a V=0 state still consumes one of the 3 cycles. The user cannot escape the cap this way.
13. **Ask the user which findings to fix.** Use `AskUserQuestion(multiSelect: true)` per §User Selection UI. Only findings with scope `must-fix` or `minimal-hygiene` appear as options (further filtered by validity to exclude `invalid`). `reject-out-of-scope` and `reject-noise` findings are never offered for selection — they live in the summary blocks for audit trail only. Always append a final `None — skip all, end cycle` option.
13.5. **Fix-weight precheck (self-discipline gate).** Before applying any selected finding, verify that the planned edit matches the finding's scope classification. This check runs **silently** — it adds no user-visible output unless a mismatch is detected.
    - `must-fix` allows multi-line edits, new sections, flow changes, and cross-file edits within the review diff.
    - `minimal-hygiene` allows **only** 1-line edits, a single short paragraph addition, or a 1-sentence rule insertion. Edits that exceed this envelope indicate the finding should have been classified `must-fix`, not hygiene, and the rest of the workflow would miscount it.
    - On mismatch (a `minimal-hygiene` finding whose planned fix exceeds the hygiene envelope): either (a) simplify the edit to hygiene-scope and apply, or (b) raise an `AskUserQuestion` asking the user whether to re-classify the finding as `must-fix` before proceeding. Do **not** silently apply a must-fix-weight edit to a minimal-hygiene finding.
    - `reject-*` findings must not trigger any edit — skip entirely.
    - Rationale: without this gate, `minimal-hygiene` findings can receive multi-line structural edits, recreating the over-engineering pattern the skill is designed to prevent. This gate forces the classification and the applied weight to match.
14. **Apply fixes.** For each selected finding, Claude reads the cited lines, applies the fix via `Edit` or `Write`, and reports the resulting `git diff` for the touched files. No sync-sweep, no rescue delegation.

    **Write-scope boundary**: Claude edits only files present in `review_target.diff_command` output (plus untracked files for `working-tree` scope). If a finding's fix genuinely needs an out-of-diff file, skip the finding with a note `Skipped: requires out-of-diff write`. Out-of-diff writes are a scope expansion that must go through a separate skill invocation, not through the user-selection UI.

    How the fixes become visible to the next cycle depends on `review_target.scope`:
    - **`working-tree`**: fixes are left in the working tree. Cycle N+1's `--scope working-tree` review sees the staged + unstaged + untracked state directly. No commit is needed.
    - **`branch` / `base-ref`**: codex's branch diff is computed as `<merge-base>..HEAD`, so in-place edits are invisible until they land in a commit on HEAD. **Claude does not commit on the user's behalf**. Before printing the manual-commit instruction, record `pre_pause_head = git rev-parse HEAD` into `cycle_history[current].pre_pause_head` — the next cycle's preflight uses this anchor (plus the per-fix `touched_files[]` list from step 15) to verify the user's actual commit delta, not just worktree cleanliness. Then, after all selected fixes are applied this cycle, print a manual-commit instruction and pause the skill:
      ```
      Cycle N fixes applied to working tree. Branch/base-ref scopes require you to commit these changes before cycle N+1 can see them. Recommended commands:
        git add <touched files>
        git commit -m "review cycle N fixes"
      After committing, reply `continue` to proceed to cycle N+1. Reply `stop` to end the skill here.
      ```
      The user owns pre-commit hook outcomes, clean-index concerns, and rollback. If the user replies `stop`, end the skill in Case B-like state (applied fixes remain uncommitted in the working tree; the user can deal with them however they like). If the user replies `continue`, proceed to step 8's cycle-N>1 preflight which verifies `git rev-parse HEAD` has moved.

    **Sibling-doc cascade check**: when a fix changes a user-facing contract of the skill (adds a new side effect the skill did not previously have, changes a stated invariant, introduces a step that sibling docs describe as absent), Claude must **in the same edit pass** grep sibling docs (`README.md`, other SKILL.md sections, CHANGELOG entries for the current release) for claims describing the OLD behavior, and update every match. Specifically run `rg -n '<characteristic phrase from old behavior>' .` for at least one phrase, and either edit every hit or leave an explicit NOTE comment explaining why a mismatch is acceptable. Rationale: catching contract-breaking fixes in the same edit pass prevents silent contract breaks that would only surface in a later cycle.
15. **Update cycle history and ledger.** Append to `cycle_history` an entry for this cycle recording:
    - `applied_fixes[]` — each entry records `{display_id, fingerprint, title, file, line_start, scope_category, touched_files[]}`. `display_id` is the cycle-local label assigned in step 9 (`F1`, `F2`, …); persisted here as the authoritative source for `references/termination.md` §Applied-Fixes List rendering. `fingerprint` is the stable `{normalized_title, file, line_start, scope_category}` tuple used by step 17's residual matcher. `touched_files[]` is the exact list of files Claude edited while applying the finding — the preflight in step 8 consumes this list to verify those files are visible in cycle N+1's branch diff.
    - `user_declined[]` — each entry records `{display_id, fingerprint, title, file, line_start, scope_category, cycle_index}` for `must-fix`/`minimal-hygiene` findings the user did not select (including the `None — skip all` case). `display_id` is the step 9 label from the declining cycle; `cycle_index` is the declining-cycle integer (1, 2, or 3). Both feed the residual-line `F<n> … — <file>:<line_start>, declined in cycle N` rendering in step 17.
    - `skipped_for_scope[]` — each entry records `{display_id, fingerprint, title, file, line_start, scope_category, cycle_index, reason}` for findings the user selected but Claude skipped because their fix required an out-of-diff write (see step 14 Write-scope boundary). These count as unresolved at termination time — Case A lists them alongside user-declined carry-overs and must not claim clean resolution while the bucket is non-empty. `display_id` and `cycle_index` behave as in `user_declined[]`.
    - `claude_invalid[]` — each entry records `{fingerprint, title, file, line_start, rejection_reason}` for `invalid` findings from the validity check. These findings are not rendered in Phase 2 termination output, so `display_id` and `cycle_index` are not tracked here.
    - `not_evaluated_signal_names[]` — the ordered string array returned by `review-scope-guard` step 11. Stored verbatim, no mutation. Used by step 11's footer rendering in cycle N+1 to decide whether to suppress the `not evaluated` footnote.
    - `unrelated_commit_paths[]` — optional, populated only when the user chose `Keep` at the cycle-N>1 ownership gate. Lists paths from the cycle commit that were NOT in `applied_fixes[*].touched_files[]`. The step-20 Part B terminal audit consumes this list to display the unrelated paths one more time before the final squash, so the user can decide anew whether to include them in the final commit.
    - `selectable_count` — the integer V computed at step 12 for this cycle (count of findings with validity `valid`/`partially-valid` AND scope `must-fix`/`minimal-hygiene`). Persisted uniformly across fix cycles and no-fix cycles so `references/termination.md` §Verdict Headline trend classification reads a single field from every `cycle_history` entry. Normal fix cycles record the current cycle's V; no-fix persists (both terminal and N+1 variants above) record 0.

    All four buckets carry fingerprints so step 17's residual accounting matches on the stable `{normalized_title, file, line_start, scope_category}` tuple, not on title alone.

    The `rejected_ledger` returned by step 10a is already updated with `reject-out-of-scope` and `reject-noise` entries; persist it as-is for the next cycle. The next cycle's `<review_context>` `<rejected_findings>` block is populated from the union of ledger entries and `claude_invalid` only — **not** from `user_declined[]` or `skipped_for_scope[]`. Declines and out-of-diff skips are deferrals, not rejections: leaving them out of `<rejected_findings>` lets codex freely re-raise the same findings next cycle so the user can reconsider them. Termination-time accounting still tracks them as unresolved residuals (see step 17 Case A).
16. **Loop check.**
    - `N < 3`: set `N = N + 1`, return to step 8.
    - `N == 3`: jump to Phase 2 **Case B**. The cap fires after cycle 3's fix phase completed (V[3] > 0; V == 0 already routed to Case A via step 12). Case B's `<U>` count distinguishes two sub-states under the Cap-reached verdict: `<U> > 0` (unapplied findings remain) and `<U> == 0` (every cycle-3 finding applied, no cycle 4 to re-review).
    - **Case A vs Case B**: Case A is reached only via step 12's V == 0 path — `cycle_history[M].selectable_count == 0` in every Case A run. Case B is reached only from this `N == 3` branch — `V[3] > 0` by construction. Routing N == 3 with V > 0 to Case A would render `Clean termination` over a non-zero terminal selectable count, violating `references/termination.md` §Verdict Headline's clean predicate.
    - **Mid-cycle interruption is not Case B**: overflow-paging cancellation, AskUserQuestion cancellation, or abort before step 15 is a run-abort failure. The skill exits with the `User wants to cancel the skill mid-cycle` behavior from §Failure Modes; Phase 2 does not render because neither variant's state contract (`display_id`, `selectable_count`, `applied_fixes`) is satisfied.

### Phase 2 — Termination

17. **Case A — V == 0 termination.** Reached only via step 12's No-fix cycle-history persist (terminal path), so `cycle_history[M].selectable_count == 0` holds. Assert that invariant before rendering; if it fails, print `⚠️ Case A reached with V[M] > 0; routing error. Falling back to Case B render.` and render as Case B instead. Then compute the residual set: scan `cycle_history[*].user_declined[]` and `cycle_history[*].skipped_for_scope[]` across all cycles, fingerprint each as `{normalized_title, file, line_start, scope_category}` (same rule as `review-scope-guard`'s ledger), and mark an entry "carried" when no later cycle's `applied_fixes[]` holds a matching fingerprint. Matching on title alone is forbidden — generic adversarial titles collide across unrelated findings. Render per `references/termination.md`: (1) verdict headline (`Clean termination` when the carried residual set is empty; `Terminated with residuals` otherwise); (2) variant body; (3) `references/termination.md` §Verification Disclaimer; (4) `references/termination.md` §Applied-Fixes List; (5) residual lists when non-empty, one entry per residual in the format `F<n> (<scope_category>) <codex title verbatim> — <file>:<line_start>, <declined-in-cycle label translated> N`, reading `F<n>` from `display_id` and N from `cycle_index`; (6) `references/termination.md` §Step 19 — Review assessment. Do not emit the legacy `All findings resolved after N cycle(s).` / `Review cycle terminated after N cycle(s) with residuals carried forward.` opening — the verdict headline replaces both.
18. **Case B — cap reached (V[3] > 0).** Reached only from step 16's `N == 3` branch, after cycle 3's fix phase. `<A>` is the applied total across all cycles; `<U>` is the count of valid/partially-valid findings unapplied at termination (user-declined + out-of-diff skipped + carry-overs never cleared). `<U> == 0` is a valid sub-state — every finding was applied but the cap fired before another codex pass could re-review the fixes. Render per `references/termination.md` §Case B: verdict headline, `references/termination.md` §Verification Disclaimer, `references/termination.md` §Applied-Fixes List (all three cycles), the three count lines, the `### Unresolved valid findings` section, the `### Next steps` options, then `references/termination.md` §Step 19 — Review assessment. Do not start a fourth cycle. The user re-invokes the skill to run another 3-cycle pass.

## Review Context Format

The `<review_context>` XML block structure, `<previous_fixes>` window rules, and `<rejected_findings>` source rules all live in `references/review-context.md`. Phase 1 step 8 appends it to the focus text for the adversarial-review variant.

## Validity Check Summary

Full details live in `references/validity-checklist.md`. The six items are:

1. **File exists in the diff** — `finding.file` appears in the output of `review_target.diff_command` (plus `git ls-files --others --exclude-standard` when `review_target.scope == working-tree`).
2. **Line range exists** — `finding.line_start` is within the current file length; flag shifted ranges as `partially-valid`.
3. **Premise matches artifact** — Claude reads the cited lines and confirms codex's assertion.
4. **Scope** — `line_start..line_end` overlaps a changed hunk in the scope-appropriate diff (`git diff HEAD -- <file>` for working-tree; `git diff <base_sha>...HEAD -- <file>` for branch / base-ref, using the frozen Phase-0 SHA), not unchanged code in a touched file.
5. **Recommendation concreteness** — a specific failure mode is named, not a vague "consider…".
6. **Target-kind consistency** — plan cycles reject detailed-design nitpicks on `.md`/`.markdown`/`.txt` files.

Outcome: `valid` (all pass), `partially-valid` (items 2 or 5 returned partially-valid, no `invalid`), `invalid` (any of items 1, 3, 4, 6 returned invalid).

## Summary Output Template

The finding-block format, heading-line anatomy, body-bullet rules, verbatim recommendation containment, finding order, and format rules all live in `references/summary-template.md`. Phase 1 step 11's render routine consumes it.

## User Selection UI

**Language reinforcement**: `AskUserQuestion` `question`, `header`, and option `label`/`description` fields must be in the user's language per §Language. Codex verbatim titles embedded in labels stay in their original language.

Use `AskUserQuestion` with `multiSelect: true`. Only findings whose **scope** is `must-fix` or `minimal-hygiene` AND whose **validity** is `valid` or `partially-valid` appear as options. `invalid`, `reject-out-of-scope`, and `reject-noise` findings are never selectable — the user sees them in the summary blocks above for audit trail only.

`minimal-hygiene` options include a `(hygiene)` marker in the label so the user knows the expected fix is 1-line value consume + warn, not a full implementation.

Base layout. **Token rule**: each option's `description` field must carry only the finding's `file:line` — nothing else. The label already encodes the title, severity, and scope; the summary blocks above already carry rationale and Claude's note. Repeating any of that in the description is wasted context.

```text
question: "Which findings should I address in cycle N?"
header: "Cycle N fixes"
multiSelect: true
options:
  - { label: "F1: Missing null check on userId (high, must-fix)",            description: "src/auth/login.ts:42" }
  - { label: "F4: --url-query value leaks to URL (medium, hygiene)",         description: "src/curl.rs:130" }
  - { label: "None — skip all, end cycle",                                   description: "End this cycle" }
```

### Overflow handling (more than 3 selectable findings per severity)

`AskUserQuestion` accepts maximum 4 options per question; reserve one for `None — end cycle`, leaving 3 finding slots per question. When a severity bucket has more than 3 selectable findings, issue multiple sequential `AskUserQuestion` calls (3 findings each) in severity order until every selectable finding has been surfaced. No finding may be silently deferred just because it did not fit on a page — the fix phase does not begin until every selectable finding has been shown to the user and either applied or declined.

## Termination Criteria

The Case A / Case B render templates, verdict headline trend classification, verification disclaimer boilerplate, applied-fixes list, step 19 review assessment, and step 20 soft-reset all live in `references/termination.md`. Rendered from Phase 1 step 16's `N == 3` branch and Phase 2 step 17 / step 18.

### Verdict Headline

See `references/termination.md` §Verdict Headline. Stub kept so the §-anchor stays resolvable from downstream docs.

### Verification Disclaimer

See `references/termination.md` §Verification Disclaimer. Stub kept so the §-anchor stays resolvable from downstream docs.

### Applied-Fixes List

See `references/termination.md` §Applied-Fixes List. Stub kept so the §-anchor stays resolvable from downstream docs.

### Review Assessment

See `references/termination.md` §Step 19 — Review assessment. Stub kept so the legacy `§Review Assessment` anchor — used by `references/summary-samples.ja.md` — still resolves after the split promoted the numbered step to a heading.

## Preconditions Recap

- Git CLI available on `PATH`.
- Current working directory inside a git repository.
- The chosen review target produces a non-empty diff: either uncommitted changes exist (`working-tree`), or HEAD is ahead of the auto-detected default branch (`branch`), or the user-supplied ref exists and `<ref>...HEAD` is non-empty (`base-ref`).
- Codex plugin installed and `Skill(codex:setup)` reports a ready state.
- `review-scope-guard` skill available (invoked at step 10a for scope triage and DoD collection).
- Both `codex-review-cycle` and `review-scope-guard` are registered with the Claude Code harness. If not (e.g. during local development before marketplace publication), follow the SKILL.md steps manually together with the three reference files under `references/` — each step points to the reference content it needs (`references/summary-template.md`, `references/review-context.md`, `references/termination.md`).

## Failure Modes

- **Codex CLI missing or setup incomplete** — stop in Phase 0 step 4. Tell the user to install the codex plugin or run `/codex:setup`.
- **Default branch not detected** (scope = `branch`) — stop in Phase 0 step 2 with guidance to re-run with scope = `base-ref` and an explicit ref.
- **User-supplied ref not found** (scope = `base-ref`) — stop in Phase 0 step 2 with `Base ref '<ref>' not found in this repository.`
- **JSON parse failure (adversarial)** — retry once; a second failure aborts the cycle with codex's raw stdout surfaced verbatim.
- **File cited by codex no longer exists** — item 1 of the validity check returns `invalid: file not in diff`. The finding is listed in the summary but not selectable.
- **User has no working-tree diff after a cycle's fixes are applied** (scope = `working-tree`) — continue to the next cycle anyway (the next review will see the committed state). Do not silently skip cycles. For `branch` / `base-ref` scopes the diff is against a committed base, so in-cycle fixes never empty the diff.
- **User declines every finding across all 3 cycles** — terminate in Case A with the user-declined message, not Case B. The cap did not fire; the user actively closed the loop.
- **User declines the DoD interview in cycle 1 step 7 (adversarial) or step 10a (review)** — `review-scope-guard` stays inside the 4-category invariant: fall-through findings still classify as `minimal-hygiene`, and ledger/vague findings still classify as `reject-noise`. No 5th `unclassified` bucket is created. The summary footer prints `⚠️ DoD not collected — scope triage degraded. Review each selectable finding manually before applying; the minimal-hygiene fall-through is weaker than a DoD-anchored classification.` The user is the last line of defense in this degraded mode.
- **Stop signal `ACTIVE` or `WARNING` during cycles 1-2** — print the recommendation in the summary but do not auto-stop. The cycle cap still governs termination.
- **User chooses `Run cycle N+1` from a V=0 state but codex again returns 0 selectable findings** — the next V=0 offer is still issued per step 12 (adversarial-review variant only); the user can choose to terminate or burn another cycle. The cap still governs. Do not suppress the offer just because it fired before.
- **V=0 fires under `variant == review`** — the override path is unavailable; skip directly to Phase 2 Case A as documented in step 12. The summary block for the cycle still renders (empty-findings summary, with only the stop-signal footer if applicable), and the final `Review assessment` should note "V=0 under native review — override disabled, see step 12" so the user understands why no cycle N+1 offer appeared.
- **`no_fix_cycle: true` entry is internally inconsistent** — corruption is defined by **same-entry contradiction**, not by comparison with earlier cycles. A valid applied-then-V=0-retry sequence (`cycle 1: applied_fixes non-empty` → `cycle 2: no_fix_cycle=true, applied_fixes=[]` → `cycle 3: uses cycle-2 marker to exempt preflight`) must be honored — cycle 2 having a no-fix marker while cycle 1 had fixes is NORMAL. Treat the marker as corrupted ONLY when the **same entry** that carries `no_fix_cycle: true` also has non-empty `applied_fixes[]`, `user_declined[]`, or `skipped_for_scope[]`. In that (truly contradictory) case, print `⚠️ Inconsistent no_fix_cycle marker on cycle N-1 (marker true but the same entry has applied/declined/skipped entries). Running full preflight.` and run the full preflight ignoring the marker. This is defense-in-depth against a corrupted state writer; normal applied-then-V=0 flow is untouched.
- **Conversation context is lost mid-run (e.g. compaction, tab close, long idle)** — the skill's state (cycle_history, rejected_ledger, review_target, dod) lives only in the active conversation. If context is truncated or the session resets, the in-flight run CANNOT be resumed automatically. Recovery steps: (1) if any cycle commits exist on `branch` / `base-ref` scope, the user may squash them manually with `git reset --soft <pre_cycle_1_head>` from `git reflog`; (2) if applied fixes sit uncommitted on `working-tree` scope, they stay in place and the user commits normally; (3) restart the skill from Phase 0 on the current state — the new run does NOT know about prior cycles' rejected_ledger, so codex may re-raise findings that the earlier run rejected as noise. State persistence across session breaks is deferred to a separate plan; this bullet documents the current fallback.
- **User wants to cancel the skill mid-cycle** — at any `AskUserQuestion` prompt, the user can type a message indicating cancellation (e.g. "stop", "cancel", "abort"); Claude treats this as an early termination request. The current cycle's state is preserved as-is (no auto-rollback of applied fixes; no auto-commit). Claude prints a short summary: "Skill cancelled at cycle N step M. Applied fixes in this session: <list>. Remaining state: <working-tree dirty | N cycle commits on <branch>>. Manual cleanup may be needed depending on your preferences (git stash, git reset, amend, etc.)." The skill does NOT attempt any destructive cleanup on behalf of the user. Between-prompts cancellation (user Ctrl-C or tab close without an active prompt) falls under the "Conversation context is lost mid-run" bullet.

## References

- `references/focus-text.md` — target-kind detection and the canonical code/plan focus text.
- `references/validity-checklist.md` — full details of the six validity items.
- `references/summary-template.md` — per-finding block rendering, heading anatomy, body bullets, verbatim recommendation containment, finding order.
- `references/review-context.md` — `<review_context>` XML block structure, `<previous_fixes>` / `<rejected_findings>` rules.
- `references/termination.md` — Phase 2 Case A / Case B render templates, Verdict Headline trend classification, Verification Disclaimer boilerplate, Applied-Fixes List, step 19 Review Assessment, step 20 soft-reset.
- `references/summary-samples.ja.md` — Japanese-rendering examples for finding-block, stop-signal footer, and termination messages.
- `skills/review-scope-guard/SKILL.md` — scope triage skill invoked at step 10a (DoD collection, 4-category triage, rejected ledger, stop signals).
