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
planning workflows, specifications, issues, and task lists. It binds to the
authoritative plan before editing, preferring a
referenced local plan artifact over a short user-facing summary. It uses the
plan's goal, requirements, acceptance criteria, test plan, risks, and proceed
condition, and checks assumptions against local evidence or primary sources. It
labels evidence for blockers, deviation notices, commit-checkpoint decisions,
and execution summaries. It stops on contradictions or missing implementation
facts and requires an evidence-backed gate before plan deviations, including
shortcuts justified by perceived redundancy or a preferred smaller
implementation. Agents must prove the affected plan item is contradicted,
impossible, unsafe, stale, or already satisfied, then report the evidence,
impact, and closest plan-preserving alternative before asking for approval.
When a bound plan includes high-risk planning sections, execution treats them as
contract and does not weaken them without the Plan Deviation Gate. When commits
are authorized, it commits only completed and verified checkpoints and uses
standalone Conventional Commit messages that describe the actual change without
prompt or plan-label references.

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

### `vibe-review`

Integrated vibe-coding review workflow for user-selected git review targets:
`working-tree`, `branch`, and `base-ref`. It proposes one startup review
contract that combines target, mode, backend, review effort, reviewer count,
angle set, execution mode, DoD source, plan binding, cycle policy, dirty-path
isolation candidates, and review focus when local evidence is strong enough.
The default mode is adversarial delegated review where the host supports a
review-only delegated path; normal review is an explicit opt-in mode that runs
through the same normalization, validity, DoD triage, rejected-ledger,
specification-gap, cascade, residual, and terminal-audit pipeline.

`vibe-review` preserves the previous review loop, scope-triage, and
cascade-containment responsibilities inside one coordinator-owned workflow.
Delegated reviewers are review-only backends; the coordinator alone asks the
user, merges findings, updates ledgers, applies fixes, runs cascade gates, and
performs consented history operations. Backend output is normalized into a
common finding shape before downstream gates, duplicate findings keep child
provenance, lightweight specification gaps render separately from normal
findings, secret hygiene redacts before render or persistence, and edits remain
forbidden until per-finding and batch cascade gates are `closed` or
`accepted-residual`. Terminal audit runs before End/residual rendering and
before any soft reset, squash, amend, or other history operation.
Dirty-path isolation must be verified before hidden paths are trusted, stale
plan evidence fails closed on digest mismatch, and project-context filters use
only explicit user, DoD, or confirmed-plan evidence.

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
- `evals/vibe-review/`: external integrated review eval prompts
- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-requirements-spec/`: Markdown requirements-spec drafting skill package
- `skills/vibe-planning/`: standalone vibe-coding implementation-planning skill package
- `skills/vibe-plan-execution/`: plan-bound vibe-coding implementation skill package
- `skills/vibe-debug-fix/`: self-contained vibe-coding debug/fix skill package
- `skills/vibe-writing/`: consolidated vibe-coding writing skill package
- `skills/vibe-planning-guard/`: planning and design-review skill package
- `skills/skill-quality/`: skill creation, improvement, and eval-hardening skill package
- `skills/vibe-review/`: integrated vibe-coding review workflow with delegated review, scope triage, cascade containment, and terminal audit
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
  The plan can come from a planning workflow, a specification, an issue, a task
  list, or the current conversation. If a
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
- `vibe-review` runs only when the current directory is a git repository and
  the chosen review target resolves to a non-empty diff. It is platform-neutral:
  Claude Code with the `codex` plugin can be documented as a special backend,
  but the default contract is a host capability model for review-only delegated
  reviewers. If the selected adversarial delegated path is unavailable, the
  workflow pauses for explicit approval of an available backend or mode instead
  of silently downgrading. For `branch` and `base-ref` scopes, commits, squashes,
  resets, amends, and similar history operations require operation-specific user
  consent plus dirty-state, ownership, preview, isolation-restore, and
  conflict-safety preconditions.
