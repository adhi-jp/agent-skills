# Agent Skills

Agent skills and eval prompts for vibe-coding requirements specs, plans, review
loops, writing, skill quality, and Minecraft modding.

## Current Skill Versions

Unreleased skills without a `version` field are documented below but omitted
from this table until release preparation.

| Skill | Version |
| --- | --- |
| `minecraft-modding-workbench` | `1.2.1` |
| `vibe-planning` | `3.0.0` |
| `vibe-plan-execution` | `1.3.0` |
| `vibe-debug-fix` | `1.0.0` |
| `vibe-planning-guard` | `1.3.0` |
| `codex-review-cycle` | `1.9.0` |
| `review-scope-guard` | `1.4.0` |
| `review-fix-cascade-guard` | `1.0.2` |

## Included Skills

### `minecraft-modding-workbench`

Version-aware Minecraft modding skill for Fabric, NeoForge, and Architectury
projects. It is designed around the `minecraft-modding` MCP server from
`@adhisang/minecraft-modding-mcp` and focuses on full implementation slices,
version-aware debugging, mapping work, mod JAR inspection, and multi-loader
project structure. It also defines MCP preflight and fallback behavior for
unavailable or unstable tool servers, dependency source lookup, resource/codec
validation, GameTest wiring, HUD/client-rendering verification, and narrow
reference routing for task-relevant playbooks.

### `vibe-requirements-spec`

Markdown requirements-spec drafting skill for rough, ambiguous, contradictory,
creative, or non-technical vibe-coding goals before implementation planning. It
creates or updates one spec artifact with an approval state, current
requirements, proposed defaults, ideas or options, decisions, assumptions,
out-of-scope items, acceptance criteria, open risks, and revision notes. While
active, its only allowed write is the requirements spec artifact; it does not
write implementation plans, implementation task entries, code, tests,
verification command lists, commits, release work, changelog entries, or
unrelated files.

The skill keeps the same spec active across related turns until the user
explicitly approves it, cancels it, or replaces the effort. Ambiguous readiness
or handoff wording such as "looks good", "ready", "continue", or "go ahead" is
not enough to approve the current spec unless it clearly approves the artifact.
Changes after approval reopen the spec and require renewed approval. Approved
specs can feed a later implementation-planning phase, but this skill still stops
after updating the spec and returning a concise localized summary with the spec
path, approval state, blockers or unknowns, and exact next user action.

Small requests ask no more than three direct questions, mark recommended
defaults for option sets, and move lower-impact unknowns into defaults,
assumptions, out-of-scope items, or open risks. Broader unclear requests use a
grouped confirmation checklist. Creative exploration stays optional: two to five
brainstormed options include fit and tradeoff notes, and do not become
requirements until the user selects a direction. Defaults stay limited to
confirmed scope or cross-cutting choices and do not select or conditionally
pre-stage adjacent surfaces such as admin, reporting, audit views, diagnostic
views, or log storage/retention/search. Bulk data or irreversible-write requests
explicitly surface write-safety choices such as preview or review-before-write,
duplicate handling, permissions, persistence, and recovery. Billing, permission,
security, account-setting, recipient, and routing changes cover auditability as
requirement behavior rather than only excluding audit-log UI work. For
notification or messaging work, unselected delivery-log surfaces stay out of
first-slice defaults and acceptance criteria, including structured per-send
records, timestamp/user/channel/outcome fields, retention, queryability, and
viewer behavior.

### `vibe-planning`

Standalone planning skill for turning rough vibe-coding requests into
implementation-ready plans. It supports both technical and non-technical users,
and emphasizes primary-source or local-investigation grounding, plain-language
clarification, acceptance criteria before implementation, tests before code,
explicit handling of unproven assumptions, and output-language selection via
user instruction, `VIBE_PLANNING_OUTPUT_LANG`, agent config, or conversation
language. It writes full implementation plans as Markdown artifacts with English
LLM-first structure while preserving user-authored goals, requirements, quotes,
and domain terms in their original language. Chat replies are concise localized
summaries with the plan path, current slice, proceed condition, and key blockers
or decisions, using plain wording for non-technical users. Plans avoid invented
product constants; bug-fix plans put reproduction or isolation before
implementation when unresolved callers, configuration, runtime state, or data
shape could affect the symptom, and keep unreproduced symptoms and causal
hypotheses labeled as unproven. It separates current-slice blockers from
deferred decisions so optional product constants or future enhancements do not
block a bounded slice after acceptance criteria are narrowed.
`vibe-planning` is plan-only: it writes or updates implementation-plan artifacts
and must not continue into code, tests, non-plan docs, evals, changelogs,
commits, or other non-plan edits. Its active task lists and checklists must also
stay plan-only; planning completion, current-slice/proceed-condition language,
and implementation handoff sections do not authorize same-turn implementation
phases. Plan artifacts also include integrity gates for fact cleanup, evidence
downgrades, test no-escape checks, and generality checks so revised plans remove
stale hypotheses, keep unmeasured quality claims labeled, block weak substitutes
for important contract tests, name the abstract dimensions that shape the plan,
preserve `data contract` as a dimension for file/data migrations when relevant,
and avoid treating sampled examples, fixtures, or past failures as skill
boundaries.
Plans choose `light` or `strict` depth. `light` keeps small, localized, low-risk
artifacts compact by collapsing not-applicable details while preserving
evidence, acceptance criteria, tests, per-step skill routes, self-review, and
the proceed condition. `strict` is required for existing behavior, high-risk
controls, external contracts, destructive risk, diagnostic findings, recovery or
replacement work, auth/security/billing, data migrations, or current-slice
implementation blockers.
For high-risk planning surfaces, `vibe-planning` owns the safeguards formerly
split out in `vibe-planning-guard`: behavior-contract inventory before
equivalence analysis, known-good recovery checks, diagnostic-scope controls,
selective failure-pattern checks, and blocked proceed conditions while
implementation blockers remain unproven.
Editable UI plans also cover state transitions such as save, cancel/reset,
pending, validation, success, and error recovery, and prefer completing verified
existing surfaces before expanding into adjacent unproven channels or modes.
Multi-slice plans include commit checkpoints only after independently verifiable
code-producing phases or slices, with standalone proposed messages. Single-slice,
blocked, discovery-only, discovery-first, destructive-risk-blocked,
work-in-progress, and no-verified-code-producing-slice plans omit commit
messages until a code-producing slice is verified, rather than splitting one
slice into test/fix/docs checkpoints. At plan creation time, the skill records
matching visible skills in a per-step skill usage plan. Every discovery,
implementation, verification, self-review, and commit-checkpoint step gets a
route to a verified matching skill, `No matching optional skill verified`, or
`No skill needed`, with availability source, timing, matching reason, and
fallback. Plans also include an implementation handoff and a final self-review
gate that checks route completeness, unavailable-skill leakage, evidence labels,
test ordering, plan-only boundaries, proceed conditions, and unresolved
implementation blockers before returning the concise summary.

### `vibe-plan-execution`

Execution skill for concrete implementation plans, including plans from
`vibe-planning`, other planning workflows, specifications, issues, and task
lists. It binds to the authoritative plan before editing, preferring a
referenced local plan artifact over a short user-facing summary. It uses the
plan's goal, requirements, acceptance criteria, test plan, risks, and proceed
condition, and checks assumptions against local evidence or primary sources. It
labels evidence for blockers, deviation notices, commit-checkpoint decisions,
and execution summaries. It stops on contradictions or missing implementation
facts and requires an evidence-backed gate before plan deviations, including
shortcuts justified by perceived redundancy or a preferred smaller
implementation. Agents must prove the affected plan item is contradicted,
impossible, unsafe, stale, or already satisfied, then report the evidence,
impact, and closest plan-preserving alternative before asking for approval. When
commits are authorized, it commits only completed and verified checkpoints and
uses standalone Conventional Commit messages that describe the actual change
without prompt or plan-label references.

### `vibe-debug-fix`

Self-contained debug/fix skill for rough vibe-coding bug reports, regressions,
failed prior attempts, repeated "still broken" feedback, environment-specific
failures, runtime artifact mismatches, tool-confidence issues, and
existing-feature repair. It preserves the user's wording, turns symptoms into a
debug ledger, analyzes existing behavior to preserve or intentionally change,
routes unfamiliar external or tool behavior to authoritative sources, separates
hypotheses from proof, expands examples into domain-general state-space
dimensions before domain-specific cases, verifies artifact freshness, escalates
stalled or over-broad source-only debugging to focused probes after bounded
triage, handles degraded verification as non-proof, gives exact user retest
contracts as soon as local proof is unavailable, and keeps unresolved symptoms
alive across resume or recurrence.

### `vibe-writing`

Consolidated writing skill for vibe-coding development text, source-code
comments and docstrings, README/docs, CHANGELOG and release notes, PR
descriptions, UI copy, chat replies, progress updates, final summaries, and git
commit messages. It defaults to LLM-optimized development text that preserves
contracts, evidence, useful local anchors, exact formats, language precedence,
explicit absence, durable references, and modality such as `must`, `should`, and
`may`, while avoiding meaningless hard wraps in compact LLM-facing examples and
list items. Human reader optimization applies only when the artifact's main
reader is human; docs and guides can still be LLM-first for agent-facing workflows.
Verbatim tool or log output and bare acknowledgments stay exact, hollow
transitions are removed when they add no operational value, and support or
policy warmth must not add service promises.
Commit-message guidance lives in `references/commit-messages.md` and covers
outcome-focused Conventional Commit subjects, commit-body preserve/cut selection,
pre-draft context checks, optional non-trivial body labels,
fresh-clone-readable references, verification provenance, monorepo and
multiple-package cohesion, i18n/localization scope, dependency updates,
performance work, CI/build/publishing changes, security/privacy/data-loss fixes,
release commits, thin-evidence cases, mechanical syncs, trailer separation,
compact bullets, and multi-line message transport.

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

### `skill-quality`

Skill creation and improvement workflow for turning eval failures, benchmark
results, grader feedback, review findings, trigger failures, and session-history
patterns into narrow skill contract changes. It starts from evidence, writes a
small failure-to-contract delta, labels the current proposal's evidence,
leaves artifacts unchanged when there is no evidence-backed contract gap,
chooses the smallest coupled artifact set, updates discriminating repo-level
evals, and uses the shared eval runner honestly. It keeps executor-visible eval
summaries high-level, keeps token/time claims evidence-bound, and blocks common
regressions such as broad rewrites, universal checklists, fake baselines,
self-grading bias, weak proof substitutes, companion-skill requirements,
generated workspace commits, wording-only churn, and release/version changes
without explicit release instruction. Its reference notes summarize local
session-derived patterns for efficient skill improvement and skill degradation.

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

## Repository Layout

- `evals/`: repo-level evaluation prompts, fixtures, and scoring notes kept
  outside skill packages
- `evals/vibe-requirements-spec/`: external requirements-spec drafting eval
  prompts
- `evals/vibe-planning/`: external planning eval prompts and fixtures
- `evals/vibe-plan-execution/`: external plan-execution eval prompts and fixtures
- `evals/vibe-debug-fix/`: external debug/fix pressure prompts spanning rough
  reports, failed attempts, artifacts, auth, representation, tools, async
  lifecycle, runtime diagnostic probe escalation, continuity, and recurrence
- `evals/vibe-writing/`: external writing and commit-message eval prompts
- `evals/skill-quality/`: external skill-improvement and eval-hardening prompts
- `evals/review-fix-cascade-guard/`: external cascade-guard eval prompts
- `evals/review-scope-guard/`: external scope-guard eval prompts
- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-requirements-spec/`: Markdown requirements-spec drafting skill package
- `skills/vibe-planning/`: standalone vibe-coding implementation-planning skill package
- `skills/vibe-plan-execution/`: plan-bound vibe-coding implementation skill package
- `skills/vibe-debug-fix/`: self-contained vibe-coding debug/fix skill package
- `skills/vibe-writing/`: consolidated vibe-coding writing skill package
- `skills/vibe-planning-guard/`: planning and design-review skill package
- `skills/skill-quality/`: skill creation, improvement, and eval-hardening skill package
- `skills/codex-review-cycle/`: codex-driven interactive 2-cycle review-and-fix workflow with user-elected extensions
- `skills/review-scope-guard/`: Definition-of-Done-aware review finding triage, invoked by codex-review-cycle
- `skills/review-fix-cascade-guard/`: cascade-containment guard invoked by codex-review-cycle before any fix-application edit
- `scripts/eval_runner.py`: shared stdlib CLI for preparing agent-scoped repo
  eval runs, recording outputs and parent-captured metrics, aggregating, and
  statically reviewing results with grader prompts and client-side feedback
- `CHANGELOG.md`: repository-level change history

## Shared Eval Runner

Use `python3 scripts/eval_runner.py` for repo-level skill eval runs. `prepare`
creates `prompt.md`, `grader_prompt.md`, `run_manifest.json`, and
`eval_metadata.json` under `evals/<skill-name>/workspace/<agent>/iteration-N/`.
Run `prompt.md` with the named agent, then run `grader_prompt.md` as a separate
grading pass when supported. Use `record` to attach outputs, parent-captured
metrics such as `--total-tokens`, `--duration-ms`, and `--output-chars`, and
the grader-produced `grading.json`.

`grading.json` must preserve every `eval_metadata.json.assertions` text exactly
once, in order. `aggregate` writes `benchmark.json` and `benchmark.md` with
analysis notes, and `report` writes static `review.html` without starting a
server. `report --previous-iteration <iteration-dir>` compares against a prior
benchmark; feedback controls download a local `feedback.json` from the browser.

## Package Contents

Each skill package ships with:

- `SKILL.md`: front matter with `name` and `description`, plus `version` after
  the skill has been released, followed by the main workflow and decision rules

Some packages also include `references/` or other helper assets that are
specific to the skill.

## Notes

- `minecraft-modding-workbench` is scoped to Fabric, NeoForge, and
  Architectury. Legacy Forge-only projects should be treated as a separate
  toolchain check, not as NeoForge by default.
- `vibe-requirements-spec` is the pre-planning requirements-spec workflow. It
  writes or updates only the requirements spec artifact while active, keeps the
  same spec open until explicit approval, cancellation, or replacement, and does
  not create an implementation plan in the same skill response.
- `vibe-planning` is the primary user-facing implementation-planning workflow
  when the user asks for a plan, acceptance criteria, test plan, or rough
  vibe-coding implementation plan. Its normal output is a full plan file plus a
  short localized summary, not a full plan pasted into chat. It names concrete
  companion skills only after verifying them from the current environment,
  user-provided material, project instructions, or local metadata; unavailable
  skills remain optional and get an explicit fallback.
- `vibe-plan-execution` is for implementing from an already-bound concrete plan.
  The plan can come from `vibe-planning`, another planning workflow, a
  specification, an issue, a task list, or the current conversation. If a
  summary names a local plan file, read that file as the authoritative
  implementation contract. If no concrete plan exists, return to planning before
  coding.
- `vibe-writing` governs writing quality and commit-message content, not
  staging, commit execution, PR submission, template changes, or release
  actions. Project-specific workflows and the repo's release rules take
  precedence; `vibe-writing` applies to the words inside those constraints.
- `vibe-planning-guard` is for planning, not implementation. It should stay
  light on tiny, already-clear edits unless the user explicitly asks for
  planning or risk review.
- `codex-review-cycle` requires the `codex` Claude Code plugin to be
  installed and `/codex:setup` to be complete. The skill only runs when the
  current directory is a git repository and the chosen review target
  resolves to a non-empty diff. Before review, it may ask once to
  temporarily isolate out-of-scope dirty paths with a pathspec-limited stash
  and git-common-dir recovery metadata, then restore those paths unstaged
  after termination or hand off retained stash recovery details on failure.
  It does not commit files without explicit run-level consent; for
  `branch` / `base-ref` scopes the skill otherwise pauses between cycles
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
