# Agent Skills

Agent skills and eval prompts for vibe-coding orchestration, brainstorming,
requirements specs, plans, review loops, writing, skill quality, and Minecraft
modding.

## Current Skill Versions

| Skill | Version |
| --- | --- |
| `minecraft-modding-workbench` | `1.2.1` |
| `vibe-coding` | `1.0.0` |
| `vibe-requirements-spec` | `1.0.0` |
| `vibe-planning` | `4.0.0` |
| `vibe-plan-execution` | `2.0.0` |
| `vibe-debug-fix` | `2.0.0` |
| `vibe-writing` | `1.0.0` |
| `skill-quality` | `1.0.0` |
| `vibe-review` | `1.0.0` |

## Included Skills

### `minecraft-modding-workbench`

Version-aware Minecraft modding skill for Fabric, NeoForge, and Architectury
projects. It is designed around the `minecraft-modding` MCP server from
`@adhisang/minecraft-modding-mcp` and focuses on full implementation slices,
version-aware debugging, mapping work, mod JAR inspection, and multi-loader
project structure. It also defines MCP preflight and fallback behavior for
unavailable or unstable tool servers, dependency source lookup, resource/codec
validation, GameTest wiring, HUD/client-rendering verification, and narrow
reference routing for task-relevant playbooks. It records project profile facts
and verification sources when plans or debugging answers will guide later
implementation.

### `vibe-coding`

Top-level orchestration skill for explicitly invoked multi-turn vibe-coding
workflows. It activates only through an explicit host-specific
`vibe-coding` invocation, host-provided invocation signal, or direct instruction
such as "use `vibe-coding`"; merely mentioning "vibe coding" as a style, label,
or quote does not activate it. If activation lacks a concrete coding
instruction, it asks for the instruction before selecting a downstream route.

The skill tracks workflow state through conversation context and existing
artifact paths, then selects exactly one primary visible `vibe-*` specialist for
the immediate next phase. It routes underspecified new goals to
`vibe-requirements-spec`, approval-evidenced specs or insufficient execution
inputs to `vibe-planning`, concrete ready implementation plans to
`vibe-plan-execution`, bug reports and regressions to `vibe-debug-fix`, review
targets to `vibe-review`, and wording-only deliverables to `vibe-writing`.
Specialist boundaries remain authoritative: `vibe-coding` does not relax
approval stops, planning-only behavior, proceed conditions, review gates,
writing-only scope, release policy, or commit authorization. It also
distinguishes matched-but-unavailable specialists from no matching specialist
and treats non-`vibe-*` domain skills as auxiliary only in this first
implementation.
Commit execution is not a primary `vibe-writing` route, but when `vibe-coding`
prepares or inspects a commit message and `vibe-writing` is verified available,
`vibe-writing` is mandatory auxiliary guidance for the message artifact.

### `vibe-requirements-spec`

Markdown requirements-spec drafting skill for rough, ambiguous, contradictory,
creative, or non-technical vibe-coding goals before implementation planning. It
creates or updates one English requirements spec artifact with current
requirements, proposed defaults, ideas or options, decisions, assumptions,
out-of-scope items, acceptance criteria, and open risks. It preserves useful
user-authored wording, domain terms, identifiers, paths, commands, and quoted
text in the original language. The spec artifact does not include approval
status or revision-history sections; approval is workflow evidence from the
current instruction or routing state. While active, its only allowed write is
the requirements spec artifact; it does not write implementation plans,
implementation task entries, code, tests, verification command lists, commits,
release work, changelog entries, or unrelated files.

The skill keeps the same spec active across related turns until the user
explicitly approves it, gives an unambiguous current-spec planning handoff,
cancels it, or replaces the effort. Ambiguous readiness or handoff wording such
as "looks good", "ready", "continue", or "go ahead" is not enough to approve the
current spec unless it clearly approves the artifact. Changes after approval
replace superseded requirements, decisions, assumptions, acceptance criteria,
and risks in the same spec and require renewed approval. Approval-evidenced
specs can feed a later implementation-planning phase, but this skill still
stops after the spec artifact, approval-evidence summary, or chat-only
exploration response. Approval-only handoffs for an existing current spec do not
rewrite the spec solely to store approval evidence; they preserve the spec path
and return a concise localized summary with approval evidence or needed approval
action, blockers or unknowns, and exact next user action. These summaries use
generic later-phase wording and do not tell the user to invoke, run, start, or
route to a named workflow, tool, skill, or planning process.
Chat-only exploration does not write a spec artifact unexpectedly: when the user
only asks to brainstorm, compare, clarify, list decisions, ask questions, or
explicitly declines file edits, it keeps the discussion in chat, states that no
spec file changed, and names the action needed to create or update a spec later.
When an existing spec artifact is used as context, the current spec path remains
unchanged context rather than a new approval or planning handoff. If a legacy
artifact contains an approval state, that state is preserved as legacy context
rather than updated from brainstorming alone. When a legacy spec is updated, old
approval-status and revision-history sections are removed from the saved
artifact and any useful lifecycle context stays in the chat summary. If file
writing is unavailable, unsafe, or declined after a spec artifact was requested,
it returns the spec content in chat with the fallback reason instead of claiming
a file write.

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
duplicate handling, permissions, persistence, and recovery. Mutually exclusive
data migration, storage, compatibility, or destructive-write constraints list
viable resolution options and user-visible or data-safety consequences instead
of hiding the choice behind questions alone. Billing, permission,
security, account-setting, recipient, and routing changes cover auditability as
requirement behavior rather than only excluding audit-log UI work. Invoice or
billing-email recipient changes also cover the delivery-effect window for next
invoices, already-generated unsent invoices, retries or reminders, future
billing-cycle emails, and added or removed recipient notifications; that
delivery-effect coverage remains a high-priority dimension even under the
three-question limit. For
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
Concrete user-provided repo scans, command output, file excerpts, logs, or test
results can count as local evidence when direct inspection is unavailable and
the supplied facts are not contradicted; bare assertions remain unproven.
It starts only when inputs are ready for implementation planning: explicit
planning requests with approval evidence, approval-evidenced requirements specs,
or concrete specs, acceptance criteria, and task lists. Legacy requirements specs
with `Draft`, `Awaiting explicit approval`, or `Reopened after approval` statuses
block implementation-ready planning; current specs without an approval field
require explicit approval evidence from the current request, routing state, or
another concrete source. Plans record the spec path, the absence of the legacy
approval field, and the external approval evidence instead of asking users to
rewrite the spec solely to store approval state. When evidence is missing, the
plan maps confirmed sections only as non-ready input and keeps the proceed
condition blocked or returns to requirements-spec work.
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
split out in the retired planning guard: behavior-contract inventory before
equivalence analysis, known-good recovery checks, diagnostic-scope controls,
selective failure-pattern checks, and blocked proceed conditions while
implementation blockers remain unproven.
Destructive, auth/session, credential, permission, billing, and data-migration
plans also require auditability or traceability criteria sufficient for recovery
proof without inventing unrelated audit-log UI or retention scope.
Editable UI plans also cover state transitions such as save, cancel/reset,
pending, validation, success, and error recovery, and prefer completing verified
existing surfaces before expanding into adjacent unproven channels or modes.
Multi-slice plans include commit checkpoints only after independently verifiable
code-producing phases or slices, with standalone proposed messages. These
checkpoints are proposed later boundaries and do not authorize staging,
committing, release preparation, or history mutation. Single-slice,
blocked, discovery-only, discovery-first, destructive-risk-blocked,
work-in-progress, and no-verified-code-producing-slice plans omit commit
messages and `Subject:`/`Body:` bytes until a code-producing slice is verified,
rather than treating a future implementation step as a verified checkpoint or
moving message text into route fallbacks, review notes, or test/fix/docs
pseudo-checkpoints. At plan creation time, the skill records
matching visible skills in a per-step skill usage plan. Every discovery,
implementation, verification, multi-perspective review, self-review, and
commit-checkpoint step gets a route to a verified matching skill, `No matching
optional skill verified`, or `No skill needed`, with availability source,
timing, matching reason, and fallback. After the draft artifact exists, plans
run a multi-perspective review. Verified review-only subagents are used when
available and authorized; otherwise the planner records a coordinator-run
fallback. That review always includes a `vibe-planning` contract-compliance
perspective and dispositions for material findings before final self-review.
Plans also include an implementation handoff and a final self-review gate that
checks route completeness, unavailable-skill leakage, evidence labels, test
ordering, multi-perspective review completion or fallback, plan-only boundaries,
proceed conditions, and unresolved implementation blockers before returning the
concise summary.

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
prompt or plan-label references. Proposed checkpoint messages are not wrapped in
Markdown fences, and execution summaries name durable plan, file, workspace, or
instruction facts instead of prompt-local harness phrases such as `this eval` or
`current instruction`; inline plans are named by title or goal. Commit
checkpoints inside a plan are proposals unless the user or explicit plan
approval separately authorizes commit execution; "execute this plan" alone is
not commit consent. Missing commit consent does not block an otherwise
authorized implementation slice: execution implements and verifies the slice,
then stops before staging, committing, or other history mutation. When a plan
contains a `Skill usage plan`, execution binds it, re-checks route availability,
and turns planning-time `Local investigation` into current `Local evidence`
before relying on it. If a plan requires inspecting code before writing code or
tests and those files cannot be read, execution stops at the blocker and proof
path instead of drafting unverified code or test templates.

### `vibe-brainstorm`

Unreleased brainstorming skill for creative or convention-dependent
implementation tasks. It supports explicit use and conservative autonomous
reference before coding when implicit expected behavior is easy to miss.
Autonomous use defaults to lightweight `conventions` mode for expected-behavior
checklists; explicit `diverge` mode produces `Practical` / `Unconventional` /
`Challenging` idea directions only; explicit `full` mode combines idea
generation, convention grounding, candidate development, a
mandatory-expected-behavior gate, creativity ranking, and an adoption
recommendation. The skill requires real verified sub-agent capability and
recordable host evidence for delegated generation, critique, development,
grounding, and selection roles. Evidence must come from an independently
recorded host or runner surface visible to the later reader or grader; private
transcript references, assistant-authored references to tool calls, prose-only
agent IDs, and self-reported call counts are treated as unproven. It stops or
asks for a clearly degraded fallback when capability or recordable evidence is
unavailable or unauthorized, stays chat-first, creates files only on request, and
stops before implementation until the user confirms the selected direction or
expected-behavior checklist.

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
Repair proof does not authorize repository history mutation. Staging, commits,
stashes, resets, amends, release work, and cleanup require operation-specific
consent after a dirty worktree and index preflight that separates repair-owned
paths from unrelated or ambiguous user changes.

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
It is primary only when the task is a standalone writing or revision
deliverable. Progress updates, final summaries, checkpoint message polish, and
wording inside planning, execution, review, debug, or release work are auxiliary
and remain subordinate to the active workflow's authority and gates. When the
active workflow has supplied facts for an incidental update or summary,
`vibe-writing` emits the requested brief message instead of a routing
explanation; routing explanations are only for meta questions about how the
skill applies. "Not a standalone writing deliverable" means the active workflow
keeps authority over content, not that the brief message should be withheld.
Commit-message guidance lives in `references/commit-messages.md` and covers
outcome-focused Conventional Commit subjects, commit-body preserve/cut selection,
pre-draft context checks, optional non-trivial body labels,
fresh-clone-readable references, verification provenance, monorepo and
multiple-package cohesion, i18n/localization scope, dependency updates,
performance work, CI/build/publishing changes, security/privacy/data-loss fixes,
release commits, thin-evidence cases, mechanical syncs, trailer separation,
compact bullets, and multi-line message transport. When `vibe-writing` is active
for a body commit that is actually created or amended, it applies the reference
before execution, uses one message file, editor buffer, or complete payload
instead of repeated `git commit -m` body-line arguments, and inspects
`git show -s --format=%B HEAD` before reporting completion. Commit-execution
skills still own staging, authorization, command safety, signing, and history
mutation.

### `skill-quality`

Skill creation and improvement workflow for turning eval failures, benchmark
results, grader feedback, review findings, trigger failures, and session-history
patterns into narrow skill contract changes. It starts from evidence, writes a
small failure-to-contract delta, labels the current proposal's evidence,
leaves artifacts unchanged when there is no evidence-backed contract gap,
chooses the smallest coupled artifact set, updates discriminating repo-level
evals, and uses the shared eval runner honestly. It keeps executor-visible eval
summaries high-level, applies the same leakage check to its own self-authored
assertions, keeps token/time claims evidence-bound, requires a closing rerun on
a clean, complete run before any improvement claim, records the discrimination
lost and the coverage that must remain when an assertion or eval case is
loosened or deleted, and blocks common regressions such as broad rewrites,
universal checklists, fake baselines, self-grading bias, weak proof substitutes,
companion-skill requirements, generated workspace commits, wording-only churn,
contaminated or unrerun runs counted as proof, and release/version changes
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
Plan and document changes are reviewed only when represented by a non-empty
git-backed target; standalone plan or document files are inert context, not a
`vibe-review` target by themselves.

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
- `evals/vibe-coding/`: external orchestration eval prompts for activation,
  lifecycle routing, phase boundaries, specialist availability, and auxiliary
  skill containment
- `evals/vibe-requirements-spec/`: external requirements-spec drafting eval
  prompts
- `evals/vibe-planning/`: external planning eval prompts and fixtures
- `evals/vibe-plan-execution/`: external plan-execution eval prompts and fixtures
- `evals/vibe-brainstorm/`: external creative brainstorming and convention
  grounding eval prompts
- `evals/vibe-debug-fix/`: external debug/fix pressure prompts spanning rough
  reports, failed attempts, artifacts, auth, representation, tools, async
  lifecycle, runtime diagnostic probe escalation, continuity, and recurrence
- `evals/vibe-writing/`: external writing and commit-message eval prompts
- `evals/skill-quality/`: external skill-improvement and eval-hardening prompts
- `evals/vibe-review/`: external integrated review eval prompts
- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-coding/`: explicit top-level vibe-coding orchestration skill package
- `skills/vibe-requirements-spec/`: Markdown requirements-spec drafting skill package
- `skills/vibe-planning/`: standalone vibe-coding implementation-planning skill package
- `skills/vibe-plan-execution/`: plan-bound vibe-coding implementation skill package
- `skills/vibe-brainstorm/`: creative brainstorming and expected-behavior
  grounding skill package
- `skills/vibe-debug-fix/`: self-contained vibe-coding debug/fix skill package
- `skills/vibe-writing/`: consolidated vibe-coding writing skill package
- `skills/skill-quality/`: skill creation, improvement, and eval-hardening skill package
- `skills/vibe-review/`: integrated vibe-coding review workflow with delegated review, scope triage, cascade containment, and terminal audit
- `scripts/eval_runner.py`: shared stdlib CLI that runs the bounded skill-eval
  matrix end to end (executor and grader as separate subprocesses), then
  aggregates a with_skill vs without_skill raw pass-rate comparison
- `CHANGELOG.md`: repository-level change history

## Shared Eval Runner

Use `python3 scripts/eval_runner.py` for repo-level skill eval runs. It has
three commands: `validate`, `run`, and `report`.

`run` drives the whole bounded matrix itself. For each eval, config, and run it
spawns a fresh executor subprocess with the prompt only, then a fresh grader
subprocess with a clean environment and only the executor output plus the
assertions, then aggregates a `with_skill` vs `without_skill` raw pass-rate
comparison. No agent hand-runs prompts or hand-records results.

`--agent` selects a registered provider; `claude` and `codex` are built in. The
core path (execute, grade, compare, aggregate, report) is provider-neutral and
works on Codex; opt-in metric capture is a Claude-only addition that other
providers skip.

All validation runs before any subprocess launches: suite shape, the
authoritative `with_skill` source, provider availability, and run bounds.
Invalid input exits non-zero with zero subprocess launches; an empty suite exits
0 with an empty result. Total work is bounded by `--runs` (1..5, default 1),
`--timeout` per subprocess (default 600s), and `--concurrency` (1..16, default
4). A timed-out or failed executor is recorded as a failed run, not a pass, and
the grader is skipped for it; there are no retries.

For `with_skill`, the runner resolves `--skill-path` from the repo root (default
`skills/<skill-name>/SKILL.md`) and, for every provider, rejects `.agents/skills`
snapshots, `.claude/skills` links, files not named `SKILL.md`, and paths outside
`skills/<skill-name>/`. The executor prompt tells the agent to read that source
directly instead of a host skill tool, snapshot, link, or cached copy.

Metrics are never hand-typed. No flag injects a token or duration value. When a
provider exposes machine-readable usage (for example `claude -p --output-format
json`), the runner captures it into `metrics.json` with its source; otherwise
absence is recorded as absence, never a placeholder number.

The grader subprocess returns a JSON verdict
(`{"expectations": [{"text", "passed", "evidence"}]}`); the runner derives
pass/fail from it, never from the executor's own claims, and grades the whole
recorded output. An assertion the grader omits is recorded as failed.

`run` writes per-run `prompt.md`, `grader_prompt.md`, `outputs/`, `grading.json`,
`metrics.json`, and `run.json` under
`evals/<skill-name>/workspace/<agent>/iteration-N/`, plus `benchmark.json` and
`benchmark.md` (per-eval and overall raw pass rate with the
`with_skill`/`without_skill` comparison) at the iteration root. `report
<iteration-dir>` re-renders `benchmark.md` from `benchmark.json`; it does not
start a server, open a browser, bind a port, or write a PID file.

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
  list, or an inline plan supplied by the user. If a
  summary names a local plan file, read that file as the authoritative
  implementation contract. If no concrete plan exists, return to planning before
  coding.
- `vibe-writing` governs writing quality and commit-message content, not
  staging, commit execution, PR submission, template changes, or release
  actions. Project-specific workflows and the repo's release rules take
  precedence; `vibe-writing` applies to the words inside those constraints.
  Under `vibe-coding`, verified available `vibe-writing` must be used as
  auxiliary guidance whenever a commit message is prepared or inspected, while
  commit authorization and history mutation remain outside `vibe-writing`.
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
