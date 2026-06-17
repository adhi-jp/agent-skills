# Agent Skills

Agent skills and eval prompts for vibe-coding orchestration, brainstorming,
requirements specs, plans, code research, review loops, writing, skill quality,
and Minecraft modding.

## Start Here

This README is a chooser and repository reference for the source skill packages
under `skills/`. For the full workflow contract, read the matching
`skills/<skill-name>/SKILL.md`.

Use the skill chooser before reading the long skill summaries. Use the eval
quickstart when changing a skill or its eval suite.

## Which Skill Should I Use?

| Task | Use | Output or stop boundary | Source package | Eval suite |
| --- | --- | --- | --- | --- |
| Build, debug, port, or inspect Minecraft Java Edition mods for Fabric, NeoForge, or Architectury | `minecraft-modding-workbench` | Produces implementation guidance or code while labeling MCP, workspace, source-jar, runtime, and unverified facts | `skills/minecraft-modding-workbench/` | `evals/minecraft-modding-workbench/` |
| Route an explicit multi-turn vibe-coding workflow | `vibe-coding` | Selects one primary visible `vibe-*` specialist for the next phase; does not relax downstream gates | `skills/vibe-coding/` | `evals/vibe-coding/` |
| Draft, revise, save, approve, or explore requirements before planning | `vibe-requirements-spec` | Writes only the requirements spec artifact, or stays in chat for chat-only exploration; stops before implementation planning | `skills/vibe-requirements-spec/` | `evals/vibe-requirements-spec/` |
| Create or revise an implementation plan from approval-evidenced or concrete inputs | `vibe-planning` | Writes a plan artifact and concise summary; stops before code, tests, changelog edits, commits, and release work | `skills/vibe-planning/` | `evals/vibe-planning/` |
| Review, confirm, walk through, or pre-check a saved implementation plan before execution | `vibe-plan-review` | Reviews one plan item at a time, records localized item decisions from its reference file, and stops before implementation | `skills/vibe-plan-review/` | `evals/vibe-plan-review/` |
| Implement an existing concrete plan, specification, acceptance criteria, or task list | `vibe-plan-execution` | Edits only after binding the plan and checking proceed conditions; stops before commits unless separately authorized | `skills/vibe-plan-execution/` | `evals/vibe-plan-execution/` |
| Brainstorm creative implementation ideas, alternatives, expected behavior, or convention checks | `vibe-brainstorm` | Returns chat-first directions or checklists and stops before implementation until the user confirms the direction | `skills/vibe-brainstorm/` | `evals/vibe-brainstorm/` |
| Debug or repair existing behavior from rough bug reports, regressions, failed fixes, or runtime artifacts | `vibe-debug-fix` | Produces evidence-backed repairs or retest contracts; does not authorize history mutation | `skills/vibe-debug-fix/` | `evals/vibe-debug-fix/` |
| Understand, locate, trace, or assess existing code without changing it | `vibe-code-research` | Read-only; returns anchored evidence-backed findings, redacts suspected secret-like values at output boundaries, and stops before fixes, plans, edits, or commits | `skills/vibe-code-research/` | `evals/vibe-code-research/` |
| Write or revise development text, docs, changelog entries, PR text, UI copy, summaries, or commit messages | `vibe-writing` | Controls wording only; staging, commits, releases, and workflow authority stay with the active workflow | `skills/vibe-writing/` | `evals/vibe-writing/` |
| Commit or stage changes from a vague request — pick the right files, exclude junk, re-verify staging, or fix message transport, history, or trailers | `vibe-commit` | Executes the commit and git safety; defers message wording to `vibe-writing`; does not push or rewrite shared history without explicit consent | `skills/vibe-commit/` | `evals/vibe-commit/` |
| Decide what to change in a skill or eval from benchmark results, grader feedback, reviews, or regressions | `skill-quality` | Produces evidence-bound quality decisions; release/version changes still require explicit release instruction | `skills/skill-quality/` | `evals/skill-quality/` |
| Review a git-backed working tree, branch, base ref, PR-style diff, or review/fix loop | `vibe-review` | Reviews only non-empty git-backed targets; history operations require separate consent and safety checks | `skills/vibe-review/` | `evals/vibe-review/` |

`vibe-planning` is not for rough unapproved requirements drafting. Route those
requests to `vibe-requirements-spec` first. `vibe-plan-execution` needs a
concrete implementation input with a goal, in/out-of-scope behavior, acceptance
criteria or pass/fail checks, a test or proof path, an implementation route or
code area to inspect, and known risks or an explicit absence of known risks.

## Run Skill Evals

Use the shared runner for repo-level eval suites:

```sh
python3 scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

Generated eval workspaces live under `evals/<skill-name>/workspace/<agent>/`
and are local artifacts unless explicitly requested for commit.

## Current Skill Versions

| Skill | Version |
| --- | --- |
| `minecraft-modding-workbench` | `2.0.0` |
| `vibe-coding` | `1.2.0` |
| `vibe-requirements-spec` | `2.0.0` |
| `vibe-planning` | `4.2.0` |
| `vibe-plan-execution` | `2.1.0` |
| `vibe-brainstorm` | `1.1.0` |
| `vibe-debug-fix` | `2.1.0` |
| `vibe-code-research` | `1.0.0` |
| `vibe-writing` | `1.1.0` |
| `vibe-commit` | `1.0.0` |
| `skill-quality` | `2.1.0` |
| `vibe-review` | `1.1.0` |

## Included Skills

### `minecraft-modding-workbench`

Use `minecraft-modding-workbench` when building, debugging, porting, or
inspecting Minecraft Java Edition mods for Fabric, NeoForge, or Architectury. It
is designed around the `minecraft-modding` MCP server from
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
artifact paths, classifies the current instruction into one workflow phase —
requirements specification, creative direction exploration, read-only code
investigation, implementation planning, plan execution, debug and repair,
review, commit execution, or writing — and selects exactly one primary
specialist whose visible metadata matches that phase. Routes are resolved from
visible skill metadata at routing time instead of a hardcoded specialist
roster, so in this repository's family underspecified new goals reach
`vibe-requirements-spec`, idea and convention exploration reaches
`vibe-brainstorm`, read-only code questions reach `vibe-code-research`,
planning inputs reach `vibe-planning`, concrete ready implementation plans
reach `vibe-plan-execution`, bug reports and regressions reach
`vibe-debug-fix`, review targets reach `vibe-review`, commit and staging
requests reach `vibe-commit`, and wording-only deliverables reach
`vibe-writing`. Specialist boundaries remain authoritative: `vibe-coding` does
not relax approval stops, planning-only behavior, read-only investigation
scope, proceed conditions, review gates, writing-only scope, release policy, or
commit authorization. It also distinguishes matched-but-unavailable phases from
no matching specialist, and a skill is primary-route eligible only when its
visible description matches a phase's workflow scope and boundary obligations;
skills describing only a tool, command, or domain capability stay auxiliary.
Commit execution routes to a visible commit-execution specialist as the primary
phase, with a verified visible writing specialist as mandatory auxiliary
wording authority for the message artifact; when no commit-execution specialist
is visible and `vibe-coding` prepares or inspects a commit message, the writing
specialist still provides that auxiliary message guidance. Host delegation and
scripted orchestration runs are execution transport inside a routed phase, not
routes: no orchestrated run may be scheduled to cross a downstream skill's
approval gate, stop condition, or consent boundary in one unattended pass.

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

Use `vibe-planning` for implementation planning from explicit plan requests,
approval-evidenced requirements specs, supplied specs, acceptance criteria, or
task lists. Do not use it for rough unapproved requirements drafting; route that
to `vibe-requirements-spec`. It supports both technical and non-technical users,
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
available and authorized — either ad-hoc subagents or one scripted,
independently recorded orchestration run that fans out the perspectives and
returns inert structured findings; otherwise the planner records a
coordinator-run fallback. That review always includes a `vibe-planning` contract-compliance
perspective and dispositions for material findings before final self-review.
Plans also include an implementation handoff and a final self-review gate that
checks route completeness, unavailable-skill leakage, evidence labels, test
ordering, multi-perspective review completion or fallback, plan-only boundaries,
proceed conditions, and unresolved implementation blockers before returning the
concise summary.

### `vibe-plan-review`

Plan-review skill for saved Markdown implementation plans after a plan exists
and before implementation begins. It reads the target plan, reads a
corresponding requirements spec when one exists, and stops on requirements-plan
conflicts or missing plan information needed for review. It reviews one plan
item at a time with the localized output, AI-judgment, and user-decision labels
defined in `references/localized-labels.md`. The user's item decisions remain
the source of truth.

The skill checks requirement alignment, implementation order, missing work,
ambiguity, risks, and verifiability while keeping source inspection minimal by
default. Short reviews stay chat-only unless the user asks for a file, the plan
has 8 or more detected items, or 3 or more revise-or-hold decisions.
Larger reviews create or update `.<plan-name>.review.md` beside the plan and
record enough state to resume. The original implementation plan is not modified
during item review; reflection into the plan happens only after all items are
reviewed and the user explicitly confirms how decisions should be applied.

### `vibe-plan-execution`

Execution skill for concrete implementation plans, including plans from
planning workflows, specifications, issues, and task lists. It binds to the
authoritative plan before editing, preferring a
referenced local plan artifact over a short user-facing summary. It uses the
plan's goal, requirements, acceptance criteria, test plan, risks, and proceed
condition, and checks assumptions against local evidence or primary sources. It
labels evidence for blockers, deviation notices, commit-checkpoint decisions,
and execution summaries. It stops on contradictions or missing implementation
facts. A concrete plan has a goal, in/out-of-scope behavior, acceptance criteria
or pass/fail checks, a test or proof path, implementation steps or a code area to
inspect, and risks or an explicit absence of known risks. It requires an
evidence-backed gate before plan deviations, including
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
before relying on it. Host delegation or one scripted, independently recorded
orchestration run may carry bounded sub-tasks of an authorized slice when each
delegated unit receives the bound plan contract; deviation decisions, commit
authorization, and final verification stay with the coordinator, and
concurrent slice implementation requires plan-defined independence plus
host-isolated working state. If a plan requires inspecting code before writing code or
tests and those files cannot be read, execution stops at the blocker and proof
path instead of drafting unverified code or test templates.

### `vibe-brainstorm`

Use `vibe-brainstorm` for explicit brainstorming, implementation ideas,
alternatives, interaction concepts, implicit expected behavior, convention
checks, or creative/convention-dependent implementation tasks. Do not use it for
obvious mechanical edits, approved concrete directions, direct bug fixes with a
concrete plan, or conventional review. It supports explicit use and conservative
autonomous reference before coding when implicit expected behavior is easy to miss.
Autonomous use defaults to lightweight `conventions` mode for expected-behavior
checklists; explicit `diverge` mode produces `Practical` / `Unconventional` /
`Challenging` idea directions only; explicit `full` mode combines idea
generation, convention grounding, candidate development, a
mandatory-expected-behavior gate, creativity ranking, and an adoption
recommendation. The skill requires real verified sub-agent capability and
recordable host evidence for delegated generation, critique, development,
grounding, and selection roles. Ad-hoc per-role sub-agents and one scripted,
independently recorded orchestration run that fans out the roles both satisfy
the capability and evidence checks; checklist and direction confirmation stay
in the conversation after the run returns. Evidence must come from an independently
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
debug ledger, keeps a compact current-scope record even for blockers, missing
local evidence, delegated diagnosis, or verified-repair closure decisions,
analyzes existing behavior to preserve or intentionally change, routes
unfamiliar external or tool behavior to authoritative sources, separates
hypotheses from proof, expands examples into domain-general state-space
dimensions before domain-specific cases, verifies artifact freshness, escalates
stalled or over-broad source-only debugging to focused probes after bounded
triage, handles degraded verification as non-proof, gives exact user retest
contracts as soon as local proof is unavailable, and keeps unresolved symptoms
alive across resume or recurrence. Independent hypotheses may be investigated
through delegated read-only units — ad-hoc sub-agents or one scripted,
independently recorded orchestration run — whose findings enter the ledger as
recorded evidence, not proven cause; probes, edits, and ledger ownership stay
with the coordinator.
Repair proof does not authorize repository history mutation. Staging, commits,
stashes, resets, amends, release work, and cleanup require operation-specific
consent after a dirty worktree and index preflight that separates repair-owned
paths from unrelated or ambiguous user changes.

### `vibe-code-research`

Read-only code-research skill for understanding existing code without changing
it: "how does X work", "where is Y implemented", "what would changing Z
affect", architecture and data-flow mapping, dependency tracing, convention
discovery, and pre-planning or pre-debugging evidence gathering. It frames the
request as answerable questions, maps entry points by following real
references, traces evidence along call and data paths, runs at least one
disconfirming check against the main conclusion, and reports findings with the
direct answer first. Claims carry `Local investigation`, `Primary source`, or
`Unproven` labels and file/line anchors; static reading is never presented as
runtime proof, and failed searches are reported as coverage limits, not
nonexistence. Findings preserve non-sensitive paths, line anchors, symbols, API
names, commands, and identifiers, but suspected credentials or secret-like
literal values are redacted or paraphrased before chat output, saved reports, or
delegated-finding summaries. While active it edits nothing, stages nothing, and
commits nothing; findings feed later requirements, planning, repair, review, or
commit phases only after a new user instruction. Findings stay in chat unless
the user explicitly asks for a saved report. Broad questions may fan out to
delegated read-only investigators — ad-hoc sub-agents or one scripted,
independently recorded orchestration run — while the coordinator merges
findings, re-reads load-bearing anchors, sanitizes delegated output, and runs
the disconfirming check itself.

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
Changelog and release-note guidance lives in `references/changelog.md`, which
separates a format layer (the repository owns its changelog format; detect and
conform to it, and never silently restructure it) from a content layer (write
each entry as a contract and evidence log for the next agent resuming with zero
context rather than human-facing release marketing, while collapsing
in-progress run commentary into the current contract delta and latest
verification status). When a requested artifact is the deliverable,
`vibe-writing` returns the artifact itself without process notes, wrappers,
separators, or translation away from the artifact's own language contract.
Commit-message guidance lives in `references/commit-messages.md` and covers
outcome-focused Conventional Commit subjects, commit-body preserve/cut selection,
pre-draft context checks, optional non-trivial body labels,
fresh-clone-readable references, verification provenance, monorepo and
multiple-package cohesion, i18n/localization scope, dependency updates,
performance work, CI/build/publishing changes, security/privacy/data-loss fixes,
release commits, thin-evidence cases, mechanical syncs, stored footer shape,
compact bullets, and multi-line message transport. When `vibe-writing` is active
for a body commit that is actually created or amended, it applies the reference
before execution, uses one message file, editor buffer, or complete payload
instead of repeated `git commit -m` body-line arguments, and inspects
`git show -s --format=%B HEAD` before reporting completion. Commit-execution
skills still own staging, authorization, command safety, signing, history
mutation, and the command transport for added or repaired authorship trailers.

### `vibe-commit`

Commit-execution skill that turns a vague instruction like "commit please",
"commit this", or a localized equivalent into one correctly scoped commit. It is the
execution counterpart to `vibe-writing`: `vibe-writing` owns the message wording,
and `vibe-commit` owns staging, exclusion, the pre-commit re-verification gate,
command safety, history mutation, message transport, and authorship-trailer
command transport. When `vibe-writing` is available it defers message wording to
that skill and its `references/commit-messages.md`; otherwise it applies compact
fallback message rules. The skill's guidance is distilled from real Codex and
Claude Code sessions across multiple repositories where these exact steps either
prevented or, when skipped, caused commit mistakes. Its core workflow discovers
all changes (including ignored and untracked paths), classifies them into one
logical change versus out-of-scope or generated artifacts, stages by explicit
path, runs a mandatory staged-set re-verification gate (`git diff --cached`
name-list, stat, hunks, and `--check`), composes a Conventional Commit message,
transports multi-line messages safely (single-quoted heredoc or `-F`), and
verifies the stored commit with `git show -s --format=%B HEAD` and
`git show --stat HEAD`. References cover file selection and exclusion of
generated/workspace/ignored/secret paths, the staging gate with partial-hunk
staging and a least-destructive recovery ladder, and history edits with
authorship-trailer `--trailer` transport and footer hygiene including the
per-agent `Co-Authored-By` forms.
It stays on the reversible side of git safety: it commits when asked but does not
push, and it does not amend or rebase already-pushed or shared history without
explicit informed consent. Repo release rules and project workflows take
precedence over the skill's defaults.

### `skill-quality`

Evidence-driven skill and eval quality decision workflow for benchmark results,
grader feedback, review findings, session-history patterns, trigger failures,
or quality regressions. It starts from evidence, writes a small
failure-to-contract delta, labels the current proposal's evidence,
classifies surprising or repeated eval failures by skill-contract, assertion,
recording, prompt, grader-boundary, and variance surfaces before changing skill
text, leaves artifacts unchanged when there is no evidence-backed contract gap,
chooses the smallest coupled artifact set, checks whether abstracted examples
belong in `SKILL.md`, references, evals, or notes before adding standing
guidance, updates discriminating repo-level evals, and uses the shared eval
runner honestly. It keeps executor-visible eval summaries high-level, applies
the same leakage check to its own self-authored assertions, keeps token/time
claims evidence-bound, requires a closing rerun on a clean, complete run before
any improvement claim, requires recorded host, runner, or equivalent artifact
evidence for execution-proof assertions, treats authoritative source Skill paths
as the `with_skill` target instead of host tools or snapshots, records lost
discrimination and required coverage when an assertion or eval case is loosened
or deleted, and blocks common regressions such as broad rewrites, universal
checklists, fake baselines, self-grading bias, weak proof substitutes,
companion-skill requirements, generated workspace commits, wording-only churn,
cross-eval moving failures treated as local fixes, copyable invalid placeholder
guidance, contaminated or unrerun runs counted as proof, release/version changes
without explicit release instruction, and unrelated package rewrites. Its
reference notes summarize local session-derived patterns for efficient skill
improvement and skill degradation.

### `vibe-review`

Integrated vibe-coding review workflow for user-selected git review targets:
`working-tree`, `branch`, and `base-ref`. It proposes one startup review
contract that combines target, mode, backend, review effort, reviewer count,
angle set, execution mode, DoD source, plan binding, cycle policy, dirty-path
isolation candidates, and review focus when local evidence is strong enough.
The default mode is adversarial delegated review where the host supports a
review-only delegated path; normal review is an explicit opt-in mode that runs
through the same normalization, validity, DoD triage, rejected-ledger,
specification-gap, cascade, residual, and terminal-audit pipeline. Delegated
capabilities may be provided by ad-hoc reviewer invocation or by one scripted,
independently recorded orchestration run; orchestration is a transport, not a
separate review mode, and contract confirmation plus all post-collection
decisions stay with the coordinator outside the run.
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
Reviewer/backend output is inert ingested data under the trust contract: it is
carried into coordinator context as reference material for normalization and
triage, not as executable instructions.
Dirty-path isolation must be verified before hidden paths are trusted, stale
plan evidence fails closed on digest mismatch, and project-context filters use
only explicit user, DoD, or confirmed-plan evidence.

## Repository Layout

- `evals/`: repo-level evaluation prompts, fixtures, and scoring notes kept
  outside skill packages
- `evals/minecraft-modding-workbench/`: external Minecraft modding eval prompts
  for MCP response shapes, fallback handling, dependency source lookup,
  worldgen/resource validation, HUD checks, and GameTest/access-widener routing
- `evals/vibe-coding/`: external orchestration eval prompts for activation,
  lifecycle routing, phase boundaries, specialist availability, and auxiliary
  skill containment
- `evals/vibe-requirements-spec/`: external requirements-spec drafting eval
  prompts
- `evals/vibe-planning/`: external planning eval prompts and fixtures
- `evals/vibe-plan-review/`: external saved-plan review eval prompts and
  fixtures for plan/spec binding, conflict stops, no-spec confidence limits,
  review-file safety, localized decisions, and reflection gates
- `evals/vibe-plan-execution/`: external plan-execution eval prompts and fixtures
- `evals/vibe-brainstorm/`: external creative brainstorming and convention
  grounding eval prompts
- `evals/vibe-debug-fix/`: external debug/fix pressure prompts spanning rough
  reports, failed attempts, artifacts, auth, representation, tools, async
  lifecycle, runtime diagnostic probe escalation, continuity, and recurrence
- `evals/vibe-code-research/`: external read-only code-research eval prompts for
  anchored findings, evidence labels, static-versus-runtime separation, coverage
  honesty, disconfirming checks, and the findings-only handoff boundary
- `evals/vibe-writing/`: external writing and commit-message eval prompts
- `evals/vibe-commit/`: external commit-execution eval prompts for file
  selection, exclusion, staged-set re-verification, partial-hunk staging, safe
  message transport, authorship-trailer `--trailer` transport, recovery, and the
  reversible-safety boundary
- `evals/skill-quality/`: external skill-improvement and eval-hardening prompts
- `evals/vibe-review/`: external integrated review eval prompts
- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-coding/`: explicit top-level vibe-coding orchestration skill package
- `skills/vibe-requirements-spec/`: Markdown requirements-spec drafting skill package
- `skills/vibe-planning/`: standalone vibe-coding implementation-planning skill package
- `skills/vibe-plan-review/`: saved-plan item review skill package, including
  localized label guidance in `references/localized-labels.md`
- `skills/vibe-plan-execution/`: plan-bound vibe-coding implementation skill package
- `skills/vibe-brainstorm/`: creative brainstorming and expected-behavior
  grounding skill package
- `skills/vibe-debug-fix/`: self-contained vibe-coding debug/fix skill package
- `skills/vibe-code-research/`: read-only code-research skill package for
  evidence-backed findings about existing code
- `skills/vibe-writing/`: consolidated vibe-coding writing skill package
- `skills/vibe-commit/`: commit-execution skill for file selection, exclusion,
  staged-set re-verification, safe message transport, history edits, and trailer
  transport hygiene
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
providers skip. An optional `--model` is passed through to the selected provider
CLI verbatim (whatever model name that CLI accepts, e.g. `claude-sonnet-4-6` or
`gpt-5.3-codex-spark`); it is applied to both the executor and grader and
recorded in the manifest and benchmark. Omit it to use the provider's default
model.

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

The grader subprocess returns a structured, schema-constrained verdict keyed by
the assertion's 1-based `id` (`{"verdicts": [{"id", "passed", "evidence"}]}`),
requested as provider-native structured output where the CLI supports it
(`codex --output-schema`, `claude --json-schema`); the legacy text-keyed
`{"expectations": [...]}` shape is still accepted. The runner derives pass/fail
from it, never from the executor's own claims, and grades the whole recorded
output. An assertion the grader omits is recorded as failed, and a verdict the
runner cannot parse is recorded as `grader_unparseable` and excluded from the
pass rate rather than scored as `0%`.

`run` writes per-run `prompt.md`, `grader_prompt.md`, `outputs/`, `grading.json`,
`metrics.json`, and `run.json` under
`evals/<skill-name>/workspace/<agent>/iteration-N/`, plus `benchmark.json` and
`benchmark.md` (per-eval and overall raw pass rate with the
`with_skill`/`without_skill` comparison, plus a `sanity_checks` section flagging
infrastructure failures, scored-`0%` cells, and candidate-below-baseline cells)
at the iteration root. `report <iteration-dir>` re-renders `benchmark.md` from
`benchmark.json`; it does not start a server, open a browser, bind a port, or
write a PID file.

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
- `vibe-plan-review` reviews a saved Markdown implementation plan before
  execution, one item at a time. It keeps the original plan unchanged during
  review, keeps localized labels in `references/localized-labels.md`, may
  maintain `.<plan-name>.review.md` beside larger reviewed plans, and requires
  explicit confirmation before reflecting item decisions back into the
  executable plan.
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
- `vibe-commit` is the commit-execution counterpart to `vibe-writing`: it owns
  file selection, exclusion, the staged-set re-verification gate, message
  transport, history mutation, and authorship-trailer `--trailer` transport, and
  defers message wording to `vibe-writing` when available. It commits when asked
  but does not push, and it does not amend or rebase already-pushed or shared
  history without explicit informed consent. Project-specific workflows and the
  repo's release and commit rules take precedence over its defaults.
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
