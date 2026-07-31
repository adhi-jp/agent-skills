# Agent Skills

Agent skills and eval prompts for vibe-coding orchestration, goal alignment,
brainstorming, requirements specs, plans, code research, review loops, writing,
skill quality, and Minecraft modding.

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
| Route an explicit multi-turn vibe-coding workflow | `vibe-coding` | Selects one primary visible `vibe-*` specialist for the next phase; does not relax downstream gates; carries default scoped local-checkpoint permission to state-changing phases; backtracks to the artifact-owning phase when a spec or plan is defective; leaves review for debug or artifact backtracking when runtime symptoms, core regressions, repeated findings, or architecture expansion make review the wrong owner | `skills/vibe-coding/` | `evals/vibe-coding/` |
| Coordinate subagents for bounded research, edits, repairs, or review while preserving coordinator-owned scope, verification, and consent boundaries | `vibe-orchestrate` | Produces work-graph and delegation contracts, deliberate multi-subagent fan-out, recovery/monitoring guidance, verification/review discipline, direct-intervention rules, and parallel-writer accident cleanup; reference-only first version with no scripts or runner adapters | `skills/vibe-orchestrate/` | `evals/vibe-orchestrate/` |
| Align the agent's understanding with the user's intent before action, especially after misinterpretation or before risky release/version/commit/destructive work | `vibe-goal-alignment` | Produces an explicit understanding record with goal, success criteria, non-goals, assumptions, blockers, and next step; stops before downstream state changes until the user confirms or corrects the record | `skills/vibe-goal-alignment/` | `evals/vibe-goal-alignment/` |
| Draft, revise, save, finish, or explore requirements before planning | `vibe-requirements-spec` | Creates or updates the requirements spec artifact by default, defaults to strict-four-choice without explicit mode selection, stops before non-spec work, reopens the same spec for downstream requirements defects, and locally checkpoints a verified tracked spec unless commits are denied or blocked | `skills/vibe-requirements-spec/` | `evals/vibe-requirements-spec/` |
| Create or revise an implementation plan from approval-evidenced or concrete inputs | `vibe-planning` | Writes a plan artifact and concise summary; pairs positive and negative proof for material gates; includes an implementation-progress ledger for multi-item plans; ends before implementation and locally checkpoints a reviewed tracked plan unless commits are denied or blocked | `skills/vibe-planning/` | `evals/vibe-planning/` |
| Review, confirm, walk through, or pre-check a saved implementation plan before execution | `vibe-plan-review` | Reviews one plan item at a time, records localized decisions, redacts credential-like literals, stops before implementation, and checkpoints the tracked original plan only after confirmed safe reflection changes it | `skills/vibe-plan-review/` | `evals/vibe-plan-review/` |
| Implement an existing concrete plan, specification, acceptance criteria, or task list | `vibe-plan-execution` | Edits only after binding the plan and checking proceed conditions; runs core acceptance sentinels before hardening; updates progress from evidence; returns plan-changing defects to the owning artifact; locally checkpoints verified reviewed slices even when the plan omitted checkpoint prose | `skills/vibe-plan-execution/` | `evals/vibe-plan-execution/` |
| Brainstorm creative implementation ideas, alternatives, expected behavior, or convention checks | `vibe-brainstorm` | Returns chat-first directions or checklists and stops before implementation until the user confirms the direction or trusted orchestration records a proxy selection for later requirements/planning only | `skills/vibe-brainstorm/` | `evals/vibe-brainstorm/` |
| Debug or repair existing behavior from rough bug reports, regressions, failed fixes, or runtime artifacts | `vibe-debug` | Produces evidence-backed repairs or retest contracts; keeps a concrete runtime regression as the exclusive primary symptom until it is closed, deferred, accepted, or blocked; self-reviews implemented repairs and defaults to scoped local closure commits unless disabled or blocked | `skills/vibe-debug/` | `evals/vibe-debug/` |
| Understand, locate, trace, or assess existing code without changing it | `vibe-code-research` | Read-only; returns anchored evidence-backed findings, redacts suspected secret-like values at output boundaries, and stops before fixes, plans, edits, or commits | `skills/vibe-code-research/` | `evals/vibe-code-research/` |
| Write or revise development text, docs, changelog entries, PR text, UI copy, summaries, or commit messages | `vibe-writing` | Controls wording and can locally checkpoint verified tracked text edits when primary; chat replies and message drafts remain no-commit artifacts, and release or broader history authority stays outside the skill | `skills/vibe-writing/` | `evals/vibe-writing/` |
| Commit or stage changes from a vague request — pick the right files, exclude junk, re-verify staging, or fix message transport, history, or trailers | `vibe-commit` | Executes the commit and git safety with self-contained message-content rules; does not push or rewrite shared history without explicit consent | `skills/vibe-commit/` | `evals/vibe-commit/` |
| Decide what to change in a skill or eval from benchmark results, grader feedback, reviews, or regressions | `skill-quality` | Produces evidence-bound quality decisions; release/version changes still require explicit release instruction | `skills/skill-quality/` | `evals/skill-quality/` |
| Review a git-backed working tree, branch, base ref, PR-style diff, or review/fix loop | `vibe-review` | Reviews only non-empty git-backed targets; maps material acceptance criteria to proof, checkpoint-blocks compound stop signals, and locally commits verified selected fixes while keeping squash/reset/amend/push behind separate consent | `skills/vibe-review/` | `evals/vibe-review/` |

`vibe-planning` is not for rough unapproved requirements drafting. Route those
requests to `vibe-requirements-spec` first. `vibe-plan-execution` needs a
concrete implementation input with a goal, in/out-of-scope behavior, acceptance
criteria or pass/fail checks, a test or proof path, an implementation route or
code area to inspect, and known risks or an explicit absence of known risks.

For `vibe-*` skills that use subagents or delegated review, model selection is
fit-for-purpose when the host exposes model choice and the user has not fixed a
model explicitly. The contract is capability-based, not model-ID-based: newer
high-performing models should be selected by reasoning strength, context window,
tool reliability, and role fit rather than by a hard-coded vendor name. Bounded
low-ambiguity lookup, extraction, and simple checks may use cheaper, faster, or
previous-generation models only when lower capability is quality-neutral or the
user prioritizes cost/latency. Complex judgment, broad context, adversarial
review, security/data-safety, high-risk, synthesis-heavy work, final
recommendations, contract compliance, or contradiction resolution should bias
upward to the strongest suitable reasoning/context tier available. The
coordinator keeps decomposition, final synthesis, verification interpretation,
review dispositions, and non-delegable user-risk choices. Token-saving loops
should reduce repeated context by inlining verified facts, sending compact
per-worker digests, and passing only deltas after each checkpoint; they must not
reduce proof, acceptance coverage, or required user/domain perspectives. The
skills should neither inherit the top model for every small delegate nor
downshift solely to save tokens when stronger reasoning is needed. Delegated
units should also have a bounded task contract: deliverable, question or
hypothesis, elapsed-time and path/change budget, compact context digest,
verification receipt, and stop-and-return conditions. Repeated empty waits,
contradictory delegated findings, or repeated contract misses trigger checkpoint,
split, rebind, or escalation decisions instead of no-change polling updates, and
shared-root edits require explicit changed-path and verification status before
they count as progress.

## Run Skill Evals

Use the shared runner for repo-level eval suites. The `skill-eval` skill
(`skills/skill-eval/SKILL.md`) is the authoritative source for the eval test
operation — workspace placement, the CLI contract, executor and grader
separation, model passthrough, metric capture and display, and result
verification before reporting. Do not launch `eval_runner.py run` unless the
current user explicitly asks to run evals, run a benchmark, or execute the eval
runner; otherwise report `evals not run` and keep rerun-dependent claims
unproven. The commands below are the entry point after that authorization:

```sh
python3 skills/skill-eval/scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 skills/skill-eval/scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
```

The `run` summary and `benchmark.md` also show per-config executor execution
time and token usage (the executor/skill-run subprocess only, grader scoring
cost excluded); uncaptured or partial provider metrics appear as absent with a
reason, never a placeholder number.
Use the documented runner syntax literally when drafting automation: pass the
suite JSON positionally and use `--agent`, `--config`, and `--runs`; do not
invent aliases such as `--eval-id`, `--configuration`, or `--mode`.
Codex runs send prompts through stdin, use absolute provider output/schema
paths, and run a two-role readiness preflight before creating a non-empty
iteration. The preflight uses a disposable Git-backed executor cwd and an empty
non-Git grader cwd, records bounded evidence at
`evals/<skill-name>/workspace/codex/preflight.json`, and launches zero suite
cells when readiness fails. Schema-constrained grader probe output is compared
as JSON rather than by one exact whitespace serialization, and failed probes
record bounded parsed output and stderr. Failed or timed-out suite invocations
persist bounded role-specific stderr artifacts plus a structured `failure` record.
These Codex adapter rules do not change Claude's `claude -p` prompt transport or
its host-transcript evidence path.
For Claude runs, `run.json` can also include redacted `executor_evidence` from
host transcripts: tool names, host-issued tool-use ids, and sub-agent record ids
only. The grader prompt receives that evidence when captured so delegation/tool
claims are checked against runner-recorded host state instead of executor prose.

Generated eval workspaces live under `evals/<skill-name>/workspace/<agent>/`
and are local artifacts unless explicitly requested for commit.

## Current Skill Versions

| Skill | Version |
| --- | --- |
| `minecraft-modding-workbench` | `2.0.0` |
| `skill-eval` | `1.1.0` |
| `vibe-coding` | `1.5.0` |
| `vibe-requirements-spec` | `3.3.0` |
| `vibe-planning` | `4.6.0` |
| `vibe-plan-review` | `1.0.0` |
| `vibe-plan-execution` | `3.3.0` |
| `vibe-brainstorm` | `1.3.0` |
| `vibe-debug` | `3.1.0` |
| `vibe-code-research` | `1.1.0` |
| `vibe-writing` | `1.1.3` |
| `vibe-commit` | `1.0.3` |
| `skill-quality` | `2.2.2` |
| `vibe-review` | `1.3.0` |


## Included Skills

### `minecraft-modding-workbench`

Use `minecraft-modding-workbench` when building, debugging, porting, or
inspecting Minecraft Java Edition mods for Fabric, NeoForge, or Architectury. It
is designed around the `minecraft-modding` MCP server from
`@adhisang/minecraft-modding-mcp` and focuses on full implementation slices,
version-aware debugging, mapping work, mod JAR inspection, and multi-loader
project structure. It tracks the MCP 6.3.0 surface, including structured
workspace focus payloads, direct workspace and dependency targets, `find-class`
workspace/dependency `projectPath` handling, nested Jar-in-Jar class search,
batch lookups, one-call Mixin target probes, Jar-in-Jar shell handling, jar
read-through for exact `assets/**` and `data/**` text files, and validator
timeout handling. It also defines MCP preflight and fallback behavior for
unavailable or unstable tool servers, dependency source lookup,
resource/codec validation, GameTest wiring, HUD/client-rendering verification,
and narrow reference routing for task-relevant playbooks. It records project
profile facts and verification sources when plans or debugging answers will
guide later implementation.

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
review, plan pre-check walkthrough, commit execution, or writing — and selects
exactly one primary specialist whose visible metadata matches that phase.
Routes are resolved from
visible skill metadata at routing time instead of a hardcoded specialist
roster, so in this repository's family underspecified new goals reach
`vibe-requirements-spec`, idea and convention exploration reaches
`vibe-brainstorm`, read-only code questions reach `vibe-code-research`,
planning inputs reach `vibe-planning`, concrete ready implementation plans
reach `vibe-plan-execution`, bug reports and regressions reach
`vibe-debug`, review targets reach `vibe-review`, interactive pre-execution
walkthroughs of a saved implementation plan reach `vibe-plan-review`, commit
and staging requests reach `vibe-commit`, and wording-only deliverables reach
`vibe-writing`. The plan pre-check walkthrough route is inherently
interactive: it stops before implementation, yields no execution
authorization, and has no proxy-decision branch, so unattended orchestration
reports the interactive requirement and stops instead of emulating item
decisions. Git-backed plan or document diffs still route to review, and plan
content revision still routes to implementation planning. Specialist boundaries remain authoritative: `vibe-coding` does
not relax approval stops, planning-only behavior, read-only investigation
scope, proceed conditions, review gates, writing-only scope, release policy, or
commit safety. Explicit activation supplies default permission for scoped local
checkpoint commits produced by state-changing phases unless the user opts out or
project policy forbids commits. If a host requires a separate confirmation, the
workflow asks once before the first likely edit instead of after work is done;
read-only, chat-only, no-file, and message-drafting routes neither ask nor create
empty commits. Push, release/version changes, amend/rebase/reset/stash/squash,
destructive cleanup, and unrelated changes remain outside that permission. It
also distinguishes matched-but-unavailable phases from
no matching specialist, and a skill is primary-route eligible only when its
visible description matches a phase's workflow scope and boundary obligations;
skills describing only a tool, command, or domain capability stay auxiliary.
Commit execution routes to a visible commit-execution specialist as the primary
phase. When `vibe-coding` prepares or inspects a commit message and
`vibe-writing` is verified visible, `vibe-writing` and its
`references/commit-messages.md` are mandatory auxiliary authority for the
message artifact only; this is an orchestration-only exception and does not make
standalone specialists require companion skills. Local checkpoints in a bound
plan stay inside the `vibe-plan-execution` route and do not require a separate
commit-execution route or another explicit commit instruction for each
checkpoint; plan-authored checkpoints are preferred, and natural independently
verified slice boundaries apply when they are absent. Standalone commit requests
outside a bound plan still
route to commit execution when available. Bound-plan implementation-progress
ledgers also stay inside the plan-execution route: routing state can use the
ledger to rebind the active slice after an interruption, but it is not a
separate route or proof of completion until plan execution verifies it. Host
delegation and scripted orchestration runs are execution transport inside a routed phase, not
routes: no orchestrated run may be scheduled to cross a downstream skill's
approval gate, stop condition, or consent boundary in one unattended pass.
For question-heavy quality phases, `vibe-coding` uses a specialist's trusted
orchestration or proxy-decision branch for delegable low-risk judgments instead
of blocking on every preference or plan-quality question. Proxy decisions are
recorded as AI-selected defaults, assumptions, or directions, not explicit
human-user approval, and destructive, credential, auth/session, permission,
billing, security, irreversible, data-migration, legal/compliance, paid,
production, external-side-effect, release, history-mutation, and other
human-risk decisions still require recordable human-user acceptance.
When a downstream phase reports that the bound requirements spec or
implementation plan is contradictory, stale, infeasible, or contract-breaking,
`vibe-coding` treats that as a backtracking signal. The next related turn routes
to the phase that owns the broken artifact — requirements specification for
wrong requirements artifacts, user-visible behavior, scope, or source
acceptance criteria, and implementation planning for the bound plan's acceptance
criteria, proof, schema, tests, edit order, or risk handling — instead of
continuing patch-by-patch execution against a known-bad contract. It also preserves long-session state such as frozen review targets, primary journeys, acceptance sentinels, active stop signals, wait/update policies, delegation budgets, last verified checkpoints, and unverified shared edits so compaction or later continuation does not reset the user's progress/noise preferences.

#### Autonomous operation across the vibe family

The family's autonomy contract is sequential coordinator continuation: a
downstream phase must first stop and return recordable artifact-bound boundary
evidence — recorded approval, a handoff record, or a ready proceed condition —
before `vibe-coding` starts the already-requested next phase as a separate
route. No orchestrated run may cross an approval, proceed, or consent boundary
in one unattended pass. Question-heavy quality phases may advance delegable
low-risk judgments through proxy decisions, and those are always recorded as
AI-selected defaults, assumptions, or directions — never as human approval.
Destructive, credential, permission, billing, security, irreversible,
data-migration, release, and history-mutation decisions always stop for the
human user. Two surfaces are inherently interactive with no proxy branch: the
plan pre-check walkthrough, where per-item decisions and reflection consent
stay with the user, and review fix selection and history operations, where the
user selects which fixes apply and commits, squashes, and other history
mutation need operation-specific consent. Under unattended orchestration those
phases report the interactive requirement and stop.

### `vibe-orchestrate`

Coordinator-owned subagent orchestration skill for bounded delegated research,
edits, repairs, and review. It is used when workers may drift, stall, crash,
duplicate, or edit a shared workspace and the main agent must keep scope,
verification, review disposition, progress tracking, and user-consent boundaries.

The first version is reference-only. It ships no watchdog script, runner adapter,
or command wrapper. Instead it provides contract templates and guidance for
work-graph mapping, deliberate multi-subagent decomposition, verified-fact
inlining, evidence-authority ranking, derived-value assumptions, protected
external parity evidence, model/context budgets, editable-path and command-effect
whitelists, premise-contradiction stops, progress journals, frontier-coordinator
loops with token-efficient delegates, worker-death recovery,
appearance/liveness/staleness monitoring, pre-fan-out transport canaries,
coordinator-run falsifiability and named-test-set verification gates, read-only
review perspectives, direct-intervention disclosure, and abort-on-detect
parallel-writer cleanup. It
actively fans out material independent units while retaining one context owner
for tightly coupled work; concurrent writers require separate isolated
workspaces, disjoint write surfaces, and an integrated coordinator join gate,
while a shared tree permits only one writer at a time. It does not replace
requirements capture, implementation planning, plan execution, review, commit
execution, release work, or debugging ownership; it is the transport discipline
for delegation inside those workflows.

### `vibe-goal-alignment`

Pre-action alignment skill for user-agent understanding repair. It activates
when the user asks to confirm, align, or correct what the agent understood, when
prior misinterpretation caused rework, or when ambiguous release, version,
commit, migration, deletion, permission, billing, production, or other risky
instructions could lead to different files, commands, or side effects. It
returns a concise understanding record: understood goal, success criteria,
non-goals, assumptions, unresolved blockers, and the next step after agreement.
Goal-affecting facts are separated as user-stated, local evidence, assumption,
or unresolved.

The skill is deliberately pre-action. It does not edit files, run commands,
stage, commit, tag, push, bump versions, prepare releases, deploy, delete data,
or authorize a downstream workflow. It stops until the user confirms or
corrects the record. Correction turns replace the invalid interpretation rather
than carrying it forward as a live option. For release/version/commit cases, it
blocks empty-commit or patch/minor/major conclusions based on partial evidence:
the complete change set, changelog state, package metadata, and project release
policy must be reviewed by the downstream workflow before version or history
action. For an aligned state-changing `vibe-*` next action, it also records the
default scoped local-checkpoint policy or the one host-required startup
confirmation, without executing the commit itself.

### `vibe-requirements-spec`

Markdown requirements-spec drafting skill for rough, ambiguous, contradictory,
creative, or non-technical vibe-coding goals before implementation planning. It
creates or updates one requirements spec artifact by default in all drafting
modes unless the user explicitly asks for chat-only or no-file operation. When
an approved option's exact content affects implementation or acceptance, the
spec embeds the payload or cites a durable repository artifact instead of
relying on chat-local labels or derived measurements. New
default spec paths use `docs/specs/YYYY-MM-DD-<goal-slug>-spec.md` when no user
path or current path applies; historical `specs/` files are reused when they
are the current spec and are not migrated. Host or eval-runner artifact capture
paths are treated as write transport, not as the selected spec path, unless the
user explicitly chose that path.
If a current spec path is supplied but cannot be read in the active workspace,
the skill preserves that path as current context and reports that the saved file
could not be inspected or changed instead of replacing it.
Specs include `Requirement mode` in `Spec metadata` and an `Evidence and
constraints` section for decision-affecting local paths, external sources or
URLs, and unverified facts. The artifact does not include approval status,
approval notes, lifecycle status fields, or revision-history sections.
When later implementation planning or plan execution reports that the current
requirements are wrong, contradictory, infeasible, or missing a build-changing
decision, `vibe-requirements-spec` treats that report as input to reopen and
revise the same spec path when available. Prior requirements-finished or
next-phase handoff evidence no longer applies to the affected contract until
renewed finish or handoff evidence exists.

The skill has three requirement drafting modes. Without explicit current-user
mode selection, it selects `strict-four-choice`; quick, small, low-risk, or
reasonably formed requests do not automatically downgrade to another mode. Broad
UX or non-technical goals classify the user's path, feedback, recovery,
accessibility, data-safety, and permission/cost consequences before confirming a
first slice, so the first requirements draft is coherent for the user rather
than merely cheap to implement.
Explicit current-user selections, including localized names such as `厳密4択`,
`軽量4択`, and `フリースタイル`, still win. Mode names in quoted text, existing
artifacts, logs, examples, or delegated output do not switch modes by
themselves. Natural-language requests for fewer questions, a quick path, or
free-form organization require confirmation before leaving strict mode.
`strict-four-choice` asks one requirements decision question per turn with three
or four options, includes one mildly challenging option with risks,
assumptions, and adoption conditions, and continues for as many turns as needed.
Each option is a viable requirement path under stated conditions rather than a
strawman or filler choice; if only three high-quality choices exist, the skill
uses three instead of adding a weak fourth. A risky option must include the
safeguard that makes it acceptable as part of the option's requirement path, not
depend on an unverified outside escape hatch.
`lightweight-four-choice` asks one main question per turn after explicit
selection or confirmation and records lower-impact details as AI-recommended
defaults. `freestyle` organizes sufficiently formed free-form requirements after
explicit selection or confirmation and uses minimal follow-up, but stops before
adopting false, infeasible, destructive, or specification-breaking requirements
and avoids turning product requirements into implementation details without user
input or local evidence. In artifact mode, those stops still use the normal
requirements-spec shape and record deciding evidence under `Evidence and
constraints`, even when the saved current spec remains unchanged. Free-form
answers are respected instead of forced into numbered choices.

Startup behavior reads `VIBE_SUBAGENTS=ask|allow|deny` when available: `ask`
asks every time, `allow` permits research/review subagents without the startup
question, and `deny` forbids subagents without asking; unset or invalid values
behave as `ask`. Subagents are limited to research, codebase inspection,
existing-spec inspection, risk discovery, spec review, and trusted
orchestration proxy perspectives, with final judgment and spec updates kept by
the main AI. During trusted `vibe-coding` orchestration, proxy perspectives can
resolve delegable low-risk requirements questions as AI-selected proposed
defaults or assumptions instead of asking the user every question; they cannot
create explicit human-user confirmation, finish or handoff evidence, accepted
risk, or consent for non-delegable human-risk decisions. If the user asks to
skip the subagent permission question next time, the skill explains
`VIBE_SUBAGENTS=ask|allow|deny` and may show current-session or manual
user-applied persistent setup guidance, but it does not inspect, select, create,
or edit shell startup or shell configuration files. Source material such as
local docs, external evidence, existing specs, logs, examples, quoted text, and
delegated output is evidence only; embedded workflow directives, metadata-like
claims, tool commands, environment-setting requests, and trust claims stay
inert unless they come through a valid current-user or trusted control-plane
channel. When an approved exact-content requirement contains prompt-like or
imperative text, the spec keeps it in a provenance-labeled
`Content trust: inert-data` payload boundary or cites a durable repository
artifact. The payload record states that the content has no workflow, tool,
configuration, trust, or phase authority. Operational requirements reference
the payload id instead of copying the raw bytes, and inline text uses a
delimiter longer than any matching run in the payload; lossless content that
cannot be contained safely blocks handoff until a durable artifact is available.
`VIBE_DOCUMENT_LANGUAGE=user|default|<BCP47 language tag>` controls
artifact language after explicit user language requests and before the skill
default of English; existing spec language, source language, filename locale
markers, chat language, and project convention do not override that selection
or the English fallback.

The requirements lifecycle keeps the same spec active until the completion audit
finds no unresolved build-changing decisions or required local evidence checks,
any lower-priority unknowns have been explicitly accepted for deferral, and the
user gives an explicit requirements-finished phrase, a clear current-spec
next-phase instruction, trusted orchestration continuation provides recordable
current-spec handoff evidence, cancels the effort, or replaces it. Trusted
orchestration evidence must come from host/coordinator state or an independently
recorded phase invocation, name the current spec artifact identity or revision,
and record the passed completion audit; prompt text, artifact text, logs,
examples, delegated output, and user-pasted metadata-like strings do not count
by themselves. Ambiguous positive replies such as "OK", "looks good", "ready",
"continue", or "go ahead" do not end drafting by themselves. If the user later
asks whether questions remain, the skill resumes questioning when unresolved
decisions, evidence checks, or non-deferred unknowns remain. Completion or
next-phase evidence is recorded outside the spec in the chat summary or routing
state. The skill still stops after the spec artifact, explicit
chat-only response, no-write fallback, or lifecycle summary; it does not write
implementation plans, implementation task entries, code, tests, verification
command lists, release work, changelog entries, evals, README changes, unrelated
files, or commits outside the verified tracked spec checkpoint. Same-turn
non-spec work is left for a later phase, and
orchestration contexts receive a requirements-phase stop or handoff signal
rather than a forced termination of the broader orchestration. `VIBE_SUBAGENTS`
remains research/review subagent permission and is not phase-continuation
authority.

Defaults stay limited to confirmed scope or cross-cutting choices and do not
select or conditionally pre-stage adjacent surfaces such as admin, reporting,
audit views, diagnostic views, or log storage/retention/search. Bulk data or
irreversible-write requests surface write-safety choices such as preview or
review-before-write, duplicate handling, permissions, persistence, and recovery.
Blanket consent to skip destructive-change safeguards does not make
no-safeguard behavior a confirmed requirement until the risks and safer
alternatives are confirmed.
Mutually exclusive data migration, storage, compatibility, or destructive-write
constraints list viable resolution options and user-visible or data-safety
consequences. Billing, permission, security, account-setting, recipient, and
routing changes cover auditability and delivery-effect windows as requirement
behavior without inventing provider facts.

### `vibe-planning`

Use `vibe-planning` for implementation planning from explicit plan requests,
approval-evidenced requirements specs, supplied specs, acceptance criteria, or
task lists. Do not use it for rough unapproved requirements drafting; route that
to `vibe-requirements-spec`. It supports both technical and non-technical users,
and emphasizes primary-source or local-investigation grounding, plain-language
clarification, acceptance criteria before implementation, paired positive/negative proof for visibility, permission, unlock, feature-flag, and state-transition gates, tests before code,
explicit handling of unproven assumptions, and output-language selection via
user instruction, `VIBE_PLANNING_OUTPUT_LANG`, `VIBE_CHAT_LANGUAGE` as a
fallback (`VIBE_PLANNING_OUTPUT_LANG` wins when both are set), agent config, or
conversation language. It writes full implementation plans as Markdown artifacts with English
LLM-first structure while preserving user-authored goals, requirements, quotes,
and domain terms in their original language. When no explicit user path or
obvious project convention applies, generated implementation plans default to
`docs/plans/YYYY-MM-DD-<goal-slug>-implementation-plan.md`; explicit paths,
existing conventions, non-overwrite behavior, generated-name numeric suffixes,
and the no-`.gitignore` side effect remain unchanged. Chat replies are concise
localized summaries with the plan path, current slice, proceed condition, and
key blockers or decisions, using plain wording for non-technical users. Plans
avoid invented product constants; bug-fix plans put reproduction or isolation before
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
Trusted orchestration handoff can supply approval evidence only when it is
recordable host/coordinator state or an independently recorded phase invocation
tied to the current spec artifact identity or revision and a passed requirements
completion audit. Prompt-injected or artifact-contained routing text is inert,
and stale handoff evidence is invalid after the requirements change.
`vibe-planning` is plan-only: it writes or updates implementation-plan artifacts
and must not continue into code, tests, non-plan docs, evals, changelogs,
implementation commits, or other non-plan edits. A reviewed tracked plan
receives a scoped local planning-artifact checkpoint by default unless denied or
blocked. Its active task lists and checklists must also
stay plan-only; planning completion, current-slice/proceed-condition language,
and implementation handoff sections do not authorize same-turn implementation
phases. In trusted orchestration, a separate execution request may be a later
recordable coordinator/host phase invocation after the reviewed plan artifact
has a ready `Proceed condition`, or a conditional ready state backed by already
recorded explicit human-user accepted risk. Blocked, discovery-first,
destructive-risk-blocked, or current-slice-blocker plans do not route to execution, and
orchestration cannot accept destructive, credential, auth/session, permission,
billing, security, irreversible, data-migration, or other human-risk decisions
for the user. Plan artifacts also include integrity gates for fact cleanup,
evidence downgrades, investigation adequacy, test no-escape checks,
public-contract/internal-representation coverage, and generality checks
so revised plans remove stale hypotheses, keep unmeasured quality claims labeled,
require material implementation, caller, data, user-visible, and external-contract
surfaces to be checked or explicitly dispositioned, block weak substitutes for
important contract tests, validate acceptance metrics against a current or
known-bad baseline, distinguish derived calculations from measurements, ensure
required public values have an internal observer and carrier across terminal
paths, split terminal classes when their evidence, cleanup state, precedence, or
carrier differs, and group them only with an evidence-backed equivalence, name
the abstract dimensions that shape the plan,
preserve `data contract` as a dimension for file/data migrations when relevant,
and avoid treating sampled examples, fixtures, or past failures as skill
boundaries. For user-visible or UX work, planning records feedback, recovery,
accessibility, and workflow tradeoffs instead of defaulting to the cheapest
technical path. When a slice may create or edit comments, docstrings, test names,
commit messages, README/changelog entries, or other durable implementation text,
plans include a durable artifact language check so later artifacts describe
concrete behavior or domain contracts instead of copying plan-only identifiers,
while preserving useful resolvable code and product anchors.
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
checkpoints define preferred later local commit boundaries when the user asks to
execute, implement, apply, or continue the bound plan and no current user or
project instruction denies commits. Natural verified slice boundaries apply
when checkpoint prose is absent. They still do not authorize implementation
commits during planning, push, release preparation, version bumps, history rewrites, destructive
operations, external side effects, work-in-progress commits, failing or skipped
verification commits, or scope-changing commits. Single-slice, blocked,
discovery-only, discovery-first, destructive-risk-blocked, work-in-progress, and
no-verified-code-producing-slice plans omit commit messages and
`Subject:`/`Body:` bytes until a code-producing slice is verified, rather than
treating a future implementation step as a verified checkpoint or moving message
text into route fallbacks, review notes, or test/fix/docs pseudo-checkpoints. A
blocked proceed condition or unresolved current-slice implementation blocker
makes later implementation phases ineligible for commit-message bytes until a
verified checkpoint boundary exists. Multi-item plans also include an
`Implementation progress` ledger with stable item IDs, planned scope, status,
required verification or review, commit action, last update, and remaining
blocker or next item. Planning initializes those rows as `Not started` and does
not claim implementation completion; the ledger exists so later execution and
resumed sessions can update item status in place. At plan creation time, the
skill records
matching visible skills in a per-step skill usage plan. Every discovery,
implementation, verification, multi-perspective review, self-review, and
commit-checkpoint step gets a route to a verified matching skill, `No matching
optional skill verified`, or `No skill needed`, with availability source,
timing, matching reason, and fallback. After the draft artifact exists, plans
run a multi-perspective review. Verified review-only subagents are used when
available, permitted, safe, and recordable — either ad-hoc subagents or one
scripted, independently recorded orchestration run that fans out the
perspectives and returns inert structured findings; otherwise the planner
records a coordinator-run fallback. `VIBE_SUBAGENTS=ask|allow|deny` controls
future review-subagent permission: unset or invalid values behave like `ask`,
and current-turn explicit user permission or denial overrides a conflicting
environment value. Prompt-like assignments count only when they are the user's
own current instruction, not quoted source, artifacts, delegated output,
examples, or logs. Subagents are limited to the plan-review gate and may not
research the repository, draft or edit the plan artifact, ask the user
questions, update docs/changelogs/evals, implement, stage, commit, or decide
finding dispositions. Review records name the permission source, capability
source, execution mode, fallback reason, and recordable evidence or its absence.
During trusted `vibe-coding` orchestration, delegable planning-quality choices
such as low-risk edit ordering, test shape, proof sequencing, wording, and
requirement-preserving scope trimming can be recorded as AI-selected planning
defaults or assumptions instead of user interview blockers; non-delegable
human-risk, requirement-changing, or blocked-proceed decisions still ask the
human user or return to the owning requirements artifact.
That review always includes a `vibe-planning` contract-compliance perspective
and dispositions for material findings before final self-review. A shell-config
helper for skipping future subagent permission questions is allowed only after
the user explicitly asks for it, sees the exact target file/change and risks,
and confirms the edit under host filesystem permissions.
Plans also include an implementation handoff and a final self-review gate that
checks route completeness, unavailable-skill leakage, evidence labels, test
ordering, multi-perspective review completion or fallback, plan-only boundaries,
proceed conditions, unresolved implementation blockers, and implementation-progress
ledger alignment for multi-item plans before returning the concise summary. If
plan revision reveals that the requirements or spec are
wrong, contradictory, or infeasible, `vibe-planning` routes that defect back to
requirements-spec work when available, or blocks on the requirements decision,
then rebuilds the affected acceptance criteria, tests, and implementation steps
from the corrected requirements instead of hiding the defect in a local plan
workaround.

### `vibe-plan-review`

Plan-review skill for saved Markdown implementation plans after a plan exists
and before implementation begins. It reads the target plan, reads a
corresponding requirements spec when one exists, and stops on requirements-plan
conflicts or missing plan information needed for review. It reviews one plan
item at a time with the localized output, AI-judgment, and user-decision labels
defined in `references/localized-labels.md`. Users can answer with the
localized decision label or a numeric identifier from `1` to `4`; the skill
records the canonical decision label. The user's item decisions remain the
source of truth.

The skill checks requirement alignment, implementation order, missing work,
ambiguity, risks, and verifiability while keeping source inspection minimal by
default. Short reviews stay chat-only unless the user asks for a file, the plan
has 8 or more detected items, or 3 or more revise-or-hold decisions.
Larger reviews create or update `.<plan-name>.review.md` beside the plan and
record enough state to resume. The original implementation plan is not modified
during item review; reflection into the plan happens only after all items are
reviewed and the user explicitly confirms how decisions should be applied. A
verified changed tracked plan then receives a scoped local checkpoint by default
unless denied or blocked; item-review chat, temporary review files, unreflected
plans, unchanged plans, and empty file sets do not commit. Implementation,
tests, push, release/version changes, and broader history mutation remain
outside this workflow.

### `vibe-plan-execution`

Execution skill for concrete implementation plans, including plans from
planning workflows, specifications, issues, and task lists. It binds to the
authoritative plan before editing, preferring a
referenced local plan artifact over a short user-facing summary. It uses the
plan's goal, requirements, acceptance criteria, test plan, risks, and proceed
condition, and checks assumptions against local evidence or primary sources. It
labels evidence for blockers, deviation notices, commit-checkpoint decisions,
and execution summaries. It stops on contradictions, internal plan defects,
known-defective implementation steps, or missing implementation facts. A
concrete plan has a goal, in/out-of-scope behavior, acceptance criteria or
pass/fail checks, a test or proof path, implementation steps or a code area to
inspect, and risks or an explicit absence of known risks. Implementation steps
are proposed means and do not outrank the plan's higher-level behavior
contract: safety/security/data constraints, acceptance criteria, requirements,
and non-goals. A Plan Validity Gate handles self-contradictory plans, planned
steps that would fail acceptance criteria, local evidence that disproves a
planning assumption, review findings, and concrete user follow-up failure modes.
Plan-preserving corrections can proceed with recorded evidence; plan-changing
corrections stop execution and return to the owning requirements or planning
artifact before affected code changes. Execution names whether the defect belongs
in requirements-spec work or implementation-planning work, and resumes only
after a revised or replacement contract is rebound; a chat-only approval to
"just patch it" does not replace the artifact loop. It also requires an
evidence-backed validity check when implementation would preserve an out-of-scope
or status-quo behavior only by encoding a workaround, because that behavior may
be the material defect the current slice exposed. Plan deviations also require
an evidence-backed gate, including shortcuts justified by perceived redundancy
or a preferred smaller implementation. Agents must prove the affected plan item
is contradicted, impossible, unsafe, stale, or already satisfied, then report
the evidence, impact, and closest plan-preserving alternative before asking for
approval.
When a bound plan includes high-risk planning sections, execution treats them as
contract and does not weaken them without the Plan Deviation Gate. "Execute this
plan", "implement this plan", "apply this plan", or "continue this plan"
authorizes local coordinator-managed commits for verified reviewed slices unless
the current user instruction or project policy denies commits. Plan-authored
checkpoints supply preferred scopes; natural independently verified slice
boundaries apply when they are absent. Execution commits only after the
checkpoint is completed, verified, multi-perspective reviewed, material findings
are dispositioned, and the file set is safely scoped, and it uses standalone
Conventional Commit messages that describe the actual change without prompt or
plan-label references. Proposed checkpoint messages are not wrapped in Markdown
fences, and execution summaries name durable plan, file, workspace, or
instruction facts instead of prompt-local harness phrases such as `this eval` or
`current instruction`; inline plans are named by title or goal. User-facing
progress updates, blocker notices, consent questions, and execution summaries
resolve chat language separately from the source plan language, using explicit
user instruction, `VIBE_CHAT_LANGUAGE` as a language name or BCP47 tag,
conversation language, or English fallback while preserving technical tokens.
Scoped checkpoint commits do not
authorize push, release preparation, version bumps,
amend/reset/stash/squash, destructive operations, external side effects,
work-in-progress commits, failing or skipped verification commits, or
scope-changing commits. When a bound plan includes release work, destructive
operations, delegated execution, external side effects, history operations
outside scoped local checkpoint commits, or other consent-bound items, execution runs
a startup consent preflight before editing the affected slice. When a plan
contains a `Skill usage plan`,
execution binds it, re-checks route availability, and turns planning-time `Local
investigation` into current `Local evidence` before relying on it. When the
bound plan contains `Implementation progress`, execution reads it before
choosing the current item, reconciles it with implementation steps and commit
checkpoints, treats previous completion claims as stale until current evidence
confirms them, initializes a minimal ledger for writable older multi-item plans
that lack one, and updates only that ledger after each completed, blocked,
skipped, or committed item. If the local plan artifact is unavailable or
unwritable, the execution summary includes the same evidence-backed progress row
and says the durable ledger was not changed. Host
delegation or one scripted, independently recorded
orchestration run may carry bounded sub-tasks of an authorized slice when each
delegated unit receives the bound plan contract; deviation decisions, commit
authorization, and final verification stay with the coordinator, and
concurrent slice implementation requires plan-defined independence plus
host-isolated working state. If a plan requires inspecting code before writing code or
tests and those files cannot be read, execution stops at the blocker and proof
path instead of drafting unverified code or test templates. After an implemented
slice or checkpoint is verified, execution runs a mandatory post-implementation
review gate before the execution summary, before the next checkpoint starts, and
before any authorized commit. Acceptance metrics must first distinguish the
current or known-bad state, and lifecycle/control-flow repairs are re-reviewed
for inverse or symmetric regressions. The gate uses
review-only delegated reviewers when a verified, authorized host capability
exists; otherwise it runs a coordinator fallback and records the degradation
reason. Its plan-contract compliance perspective also checks durable artifact
language hygiene when a diff creates or edits comments, docstrings, test names,
commit messages, README/changelog entries, or similar text: reviewers flag
plan-only labels that do not stand alone while preserving resolvable code,
product, issue, path, command, and API anchors. Findings are advisory until the
coordinator classifies them, verifies any delegated finding as local evidence,
and independently confirms the bound plan's acceptance criteria.

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
recommendation. When alternatives differ by user effort, recovery, accessibility,
data safety, or workflow friction, it surfaces the tradeoff instead of selecting
the lowest-effort implementation path by default. The skill requires real
verified sub-agent capability and recordable host evidence for delegated
generation, critique, development, grounding, and selection roles. Ad-hoc
per-role sub-agents and one scripted, independently recorded orchestration run
that fans out the roles both satisfy the capability and evidence checks;
checklist and direction confirmation stay in the conversation after the run
returns. Evidence must come from an independently recorded host or runner surface
visible to the later reader or grader; private
transcript references, assistant-authored references to tool calls, prose-only
agent IDs, and self-reported call counts are treated as unproven. It stops or
asks for a clearly degraded fallback when capability or recordable evidence is
unavailable or unauthorized, stays chat-first, creates files only on request, and
stops before implementation until the user confirms the selected direction or
expected-behavior checklist. During trusted `vibe-coding` orchestration, a
verified proxy selection can carry only an AI-selected checklist or direction to
later requirements or planning; it is not human confirmation or implementation
authorization.

### `vibe-debug`

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
alive across resume or recurrence. Cause claims record the observation regime
and why it represents the user's path; acceptance metrics must fail or differ on
the known-bad baseline, and two unchanged repair attempts stop a third patch
until the cause model or discriminator is revalidated. Independent hypotheses may be investigated
through delegated read-only units — ad-hoc sub-agents or one scripted,
independently recorded orchestration run — whose findings enter the ledger as
recorded evidence, not proven cause; probes, edits, and ledger ownership stay
with the coordinator.
After implementation and verification, it self-reviews the repair slice before
final repair claims. For verified repair-owned file changes, it treats a scoped
local closure commit as the default unless the user disables commits, project
rules forbid them, or a safety gate blocks the operation. It preflights dirty
worktree and index state, uses matching review, commit-execution, and
message-writing capabilities when visible and applicable, stages only
repair-owned paths, and keeps push, amend, rebase, stash, reset, release work,
version changes, destructive cleanup, and unrelated or ambiguous user changes
behind exact consent or blocker reporting.

### `vibe-code-research`

Read-only code-research skill for understanding existing code without changing
it: "how does X work", "where is Y implemented", "what would changing Z
affect", architecture and data-flow mapping, dependency tracing, convention
discovery, and pre-planning or pre-debugging evidence gathering. It frames the
request as answerable questions, maps entry points by following real
references, traces evidence along call and data paths, runs at least one
disconfirming check against the main conclusion, and reports findings with the
direct answer first. Broad, user-visible, or architecture-impact questions name
and cover the material investigation surfaces instead of stopping at the first
cheap file hit, or they state the intentional boundary and residual risk. Claims
carry `Local investigation`, `Primary source`, or `Unproven` labels and
file/line anchors. The investigation first binds its evidence universe:
user-provided or upstream material, a verified target workspace, and
host/runner scaffolding stay distinct, so eval definitions, copied sandboxes,
or missing represented paths in an unrelated checkout are not reused as
application evidence. Inline supplied material that is not explicitly bound to
the current workspace forms a closed corpus: before any investigation tool, the
investigator limits entry-point mapping to the supplied artifacts, and before
responding removes any draft claim derived from ambient checkout, runner, eval,
harness, or skill state. Gaps stay `not supplied` or `Unproven` rather than
becoming absence claims about an unrelated checkout. The mandatory
disconfirming check stays inside that bound corpus; when no contradictory
artifact was supplied, the limitation is reported instead of widening the
search. Closed-corpus output never mentions searching or failing to find the
represented application in the current repository, workspace, checkout, or
sandbox, and represented paths are not converted into links targeting ambient
filesystem or sandbox locations. User-provided artifacts are labeled as `Primary source` or
supplied-source evidence. Static configuration establishes an expected branch,
not runtime-effective configuration when environment or deploy-time overrides
remain unverified; configuration-backed findings carry that distinction into
the final answer and name override, merge, or deploy-time layers under
`Not verified`. Broad closed-corpus limits name the relevant unsupplied
surfaces rather than one generic caveat, and permissive cleanup language inside
an investigation is explicitly declined as requiring a separate edit
instruction. Closed-corpus evidence may carry one section-level supplied-source
label rather than repeating it on every fact. Narrow literal lookups stay
concise but retain the supplied path and avoid unasked runtime-flow narration;
when the skill is already active, triviality scales the response down instead
of dropping the evidence contract.
Static reading is never presented as runtime proof, and
failed searches are reported as coverage limits, not nonexistence. Findings
preserve non-sensitive paths, line anchors, symbols, API
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
in-progress run commentary into the current contract delta and latest durable
verification status). It treats git-unmanaged generated reports, ignored eval
workspace output, local-only run IDs, and private tool-session records as
non-durable changelog evidence unless they are committed, published, or
otherwise available through a stable system, while preserving explicitly
supplied current verification facts that are not tied only to those local
artifacts. When a requested artifact is the deliverable, `vibe-writing` returns
the artifact itself without process notes, wrappers, separators, proof-source
analysis, or translation away from the artifact's own language contract. When
an active workflow has already selected an artifact language, that contract
wins over existing artifact language and filename locale markers for generated
prose. Chat replies, progress updates, final summaries, and confirmation
questions resolve language separately through explicit user instruction,
`VIBE_CHAT_LANGUAGE` as a language name or BCP47 tag, conversation language, or
English fallback, so English source artifacts or path-only invocations do not
change wrapper prose by inertia.
Commit-message guidance lives in `references/commit-messages.md` and covers
outcome-focused Conventional Commit subjects, commit-body preserve/cut selection,
medium-density body shaping, pre-draft context checks, optional non-trivial body labels,
fresh-clone-readable references, verification provenance, verification signal
selection, durable proof-source boundaries for git-unmanaged local generated
artifacts and local-only run records, monorepo and multiple-package cohesion,
i18n/localization scope, dependency updates, performance work,
CI/build/publishing changes, security/privacy/data-loss fixes, release commits,
thin-evidence cases, mechanical syncs, stored footer shape, compact bullets, and
multi-line message transport. When `vibe-writing` is active
for a body commit that is actually created or amended, it applies the reference
before execution, uses one message file, editor buffer, or complete payload
instead of repeated `git commit -m` body-line arguments, and inspects
`git show -s --format=%B HEAD` before reporting completion, including checks
that verification bullets pair durable proof with the changed contract, risk, or
coverage they support rather than becoming command transcripts or local-only
generated proof sources, and that the body is neither an overlong behavior
walkthrough nor an abstract paragraph that hides changed surfaces. Requested commit-message
artifacts are returned as raw message bytes without proof-source analysis,
headings, separators, or other explanatory wrappers. Commit-execution skills
still own staging, authorization, command safety, signing, history mutation, and
the command transport for added or repaired authorship trailers.

### `vibe-commit`

Commit-execution skill that turns a vague instruction like "commit please",
"commit this", or a localized equivalent into one correctly scoped commit. It
owns staging, exclusion, the pre-commit re-verification gate, command safety,
history mutation, message transport, authorship-trailer command transport, and
self-contained minimum message-content rules aligned with the repository commit
contract: outcome-focused Conventional Commit subjects, body only for durable
context the diff cannot recover, medium-density body wording that groups
durable surfaces without becoming a feature walkthrough, selected verification
proof that explains the changed contract or risk it covers when that is not
already obvious, durable proof-source boundaries for local generated artifacts,
ignored result files, and local-only run records, and no prompt/session/plan-label leakage. The skill's
guidance is distilled from real Codex and Claude Code sessions across multiple
repositories where these exact steps either prevented or, when skipped, caused
commit mistakes. Its core
workflow discovers all changes (including ignored and untracked paths),
classifies them into one logical change versus out-of-scope or generated
artifacts, stages by explicit path, runs a mandatory staged-set re-verification
gate (`git diff --cached` name-list, stat, hunks, and `--check`), composes a
Conventional Commit message, transports multi-line messages safely
(single-quoted heredoc or `-F`), and verifies the stored commit with
`git show -s --format=%B HEAD` and `git show --stat HEAD`, including checks for
low-signal verification dumps and local-only proof leakage. References cover
file selection and exclusion of
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
text, maps security diagnostics to source-boundary-sink predicates and
enforcement ownership, gives credential and trust-boundary safety explicit
precedence over exact-content preservation, leaves artifacts unchanged when
there is no evidence-backed contract gap,
chooses the smallest coupled artifact set, checks whether abstracted examples
belong in `SKILL.md`, references, evals, or notes before adding standing
guidance, updates discriminating repo-level evals, and uses the shared eval
runner honestly. It keeps executor-visible eval summaries high-level, applies
the same leakage check to its own self-authored assertions, keeps token/time
claims evidence-bound, requires a closing rerun on a clean, complete run before
any improvement claim, ties each closing run to the exact post-edit skill,
assertion, prompt, fixture, and proof-surface state it measured, checks that
declared fixtures reach the executor under the runner's copy contract, and
requires assertions to be satisfiable from the case's response-only,
artifact-writing, closure, blocked, or state-changing delivery mode. For
no-change and blocked cases, it distinguishes naming an existing sufficient
artifact from proposing an edit and does not require a new mutation solely as
proof. It binds represented source material, delivered fixtures, and the
executor workspace before treating ambient checkout state as evidence, audits
mechanically inspectable output contracts against recorded bytes even when the
grader and runner sanity summary pass, and checks new rules, evidence
taxonomies, prompts, and assertions for collisions with existing applicability
and output contracts before a closing rerun. It requires recorded host, runner,
or equivalent artifact evidence for execution-proof assertions, requires
turn-level pairing before counting
session-history audit evidence, treats excluded, timed-out, stub, or placeholder eval cells
as partial unmeasured proof until their surface is classified, keeps any
diagnostic adjusted aggregate separate from the official runner result, treats
authoritative source Skill paths as the `with_skill` target instead of host
tools or snapshots, records lost discrimination and required coverage when an
assertion or eval case is loosened or deleted, and treats eval-suite compaction
as a case-to-contract accounting change: suite-specific safe floors, natural
representative prompts, per-case replacement coverage, explicit accepted risk,
and no effectiveness claim from static validation alone. It blocks common
regressions such as broad rewrites, universal checklists, fake baselines,
self-grading bias, weak proof substitutes,
companion-skill requirements, generated workspace commits, wording-only churn,
cross-eval moving failures treated as local fixes, per-cell prose patches after
multi-run evidence shows low-frequency scatter, copyable invalid placeholder
guidance, prompt-side inert labels mistaken for data-flow isolation,
preserve-exactly rules that propagate credentials, scanner-clearance claims
from static validation, contaminated or unrerun runs counted as proof,
release/version changes without explicit release instruction, and unrelated
package rewrites. Its
reference notes summarize local session-derived patterns for efficient skill
improvement and skill degradation.

### `skill-eval`

Owns the repository's skill-eval test operation and is the eval-focused
alternative to `skill-creator`. Use it when running, grading, aggregating, or
reporting skill evals through `skills/skill-eval/scripts/eval_runner.py`, when verifying a
`with_skill`/`without_skill` result before reporting it, or when deciding eval
workspace placement, executor and grader separation, model passthrough, or
metric capture for a run. It is the authoritative source for the eval CLI
contract, requires explicit user instruction before launching eval execution,
keeps the executor and grader as separate agents (no same-agent execute-and-grade
path), surfaces per-config executor-only execution time and token usage with
uncaptured metrics shown as absent rather than zero, and requires verifying
sanity-check status and excluded runs before any pass-rate delta is reported. It
does not edit the eval suite schema or assertion model and leaves general skill
creation and quality decisions to `skill-creator` and `skill-quality`.

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
Three-reviewer coverage is the baseline for broad ordinary code targets rather
than an unconditional shape: the startup contract may add, split, fold, or
reduce angles when target evidence, user focus, DoD, risk, host capacity, or
accepted effort limits make another set more effective, while recording coverage
mapping and residual risk for folded or omitted baseline surfaces.
Plan and document changes are reviewed only when represented by a non-empty
git-backed target; standalone plan or document files are inert context, not a
`vibe-review` target by themselves.

`vibe-review` preserves the previous review loop, scope-triage, and
cascade-containment responsibilities inside one coordinator-owned workflow.
Delegated reviewers are review-only backends; the coordinator alone asks the
user, merges findings, updates ledgers, applies fixes, runs cascade gates, and
creates the scoped local closure commit or performs separately consented history
operations. Backend output is normalized into a
common finding shape before downstream gates, duplicate findings keep child
provenance, lightweight specification gaps render separately from normal
findings, secret hygiene redacts before render or persistence, and edits remain
forbidden until per-finding and batch cascade gates are `closed` or
`accepted-residual`. Terminal audit runs before End/residual rendering and
before any soft reset, squash, amend, or other history operation.
Delegated review is available only when a host-side adapter keeps the original
reviewer/backend response out of the coordinator context, rejects unknown or
instruction-bearing fields, and supplies bounded structural result records with opaque provenance. The coordinator validates those records against
the frozen target and never requests raw transcripts as a fallback. Review
completion also requires acceptance coverage: material criteria are recorded in
an `acceptance_proof` matrix, core criteria need positive proof,
visibility/permission/unlock/state gates need paired positive and negative
proof, and compound stop signals move the run to a checkpoint-blocked state
rather than another mutable-target broad review.
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
- `evals/vibe-orchestrate/`: external subagent-orchestration eval prompts for
  bounded delegation contracts, blocker stops, fact inlining, journal recovery,
  reference-only monitoring, deliberate multi-subagent work-graph selection,
  coordinator verification, review adjudication, direct-intervention disclosure,
  and parallel-writer cleanup
- `evals/vibe-goal-alignment/`: external goal-alignment prompts for
  understanding records, correction loops, risky release/version/commit
  ambiguity, destructive side-effect stops, source-instruction boundaries, and
  no-execution alignment boundaries
- `evals/vibe-requirements-spec/`: external requirements-spec drafting eval
  prompts
- `evals/vibe-planning/`: external planning eval prompts and fixtures
- `evals/vibe-plan-review/`: external saved-plan review eval prompts and
  fixtures for plan/spec binding, conflict stops, no-spec confidence limits,
  review-file safety, localized decisions, numeric shortcuts, and reflection
  gates
- `evals/vibe-plan-execution/`: external plan-execution eval prompts and fixtures
- `evals/vibe-brainstorm/`: external creative brainstorming and convention
  grounding eval prompts
- `evals/vibe-debug/`: external debug/fix pressure prompts spanning rough
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
- `evals/skill-eval/`: external eval-runner operation prompts for run
  authorization, runner routing, and reporting boundaries
- `evals/vibe-review/`: external integrated review eval prompts
- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-coding/`: explicit top-level vibe-coding orchestration skill package
- `skills/vibe-orchestrate/`: coordinator-owned subagent orchestration skill
  package with reference-only delegation, recovery, monitoring, verification,
  review, and accident-cleanup guidance
- `skills/vibe-goal-alignment/`: pre-action user-agent understanding alignment
  skill package
- `skills/vibe-requirements-spec/`: Markdown requirements-spec drafting skill package
- `skills/vibe-planning/`: standalone vibe-coding implementation-planning skill package
- `skills/vibe-plan-review/`: saved-plan item review skill package, including
  localized label, numeric identifier, and credential-safe reflection guidance in
  `references/localized-labels.md`
- `skills/vibe-plan-execution/`: plan-bound vibe-coding implementation skill package
- `skills/vibe-brainstorm/`: creative brainstorming and expected-behavior
  grounding skill package
- `skills/vibe-debug/`: self-contained vibe-coding debug/fix skill package
- `skills/vibe-code-research/`: read-only code-research skill package for
  evidence-backed findings about existing code
- `skills/vibe-writing/`: consolidated vibe-coding writing skill package
- `skills/vibe-commit/`: commit-execution skill for file selection, exclusion,
  staged-set re-verification, safe message transport, history edits, and trailer
  transport hygiene
- `skills/skill-quality/`: skill creation, improvement, and eval-hardening skill package
- `skills/vibe-review/`: integrated vibe-coding review workflow with delegated review, scope triage, cascade containment, and terminal audit
- `skills/skill-eval/scripts/eval_runner.py`: shared stdlib CLI that runs the bounded skill-eval
  matrix end to end (executor and grader as separate subprocesses), then
  aggregates a with_skill vs without_skill raw pass-rate comparison
- `CHANGELOG.md`: repository-level change history

## Shared Eval Runner

`skills/skill-eval/scripts/eval_runner.py` runs repo-level skill evals with three commands:
`validate`, `run`, and `report`. The runner drives the bounded matrix itself and
keeps the executor and grader as separate subprocesses; see
[Run Skill Evals](#run-skill-evals) for the command sequence.

The `skill-eval` skill (`skills/skill-eval/SKILL.md`) is the authoritative source
for the eval test operation: eval workspace placement, the CLI contract,
executor and grader separation, model passthrough, metric capture and the
executor-only time/token display, and result verification before reporting a
`with_skill`/`without_skill` delta. Follow that skill for any eval run rather
than restating its rules here.

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
  creates or updates the requirements spec artifact by default while active,
  persists selected exact-content payloads or durable repository references
  before dependent handoff, uses explicit chat-only/no-file only when requested,
  keeps the same spec open until explicit requirements-finished evidence,
  next-phase handoff, cancellation, or replacement, and does not create an
  implementation plan in the same skill response.
- `vibe-goal-alignment` is a pre-action alignment workflow for repairing or
  confirming the agent's understanding before work starts. It produces a
  concise goal/success/non-goal/assumption/blocker record and stops before
  edits, commands, commits, releases, destructive actions, or downstream
  workflow authorization until the user confirms or corrects the record.
- `vibe-orchestrate` is a coordinator-owned delegation discipline for using
  subagents safely inside bounded research, editing, repair, or review work. It
  is reference-only in its first version: no watchdog script, runner adapter, or
  command wrapper is included. The coordinator remains responsible for scope,
  work-graph and fan-out decisions, verified facts, progress journals,
  monitoring decisions, verification gates, review dispositions,
  direct-intervention disclosure, and parallel-writer accident cleanup.
- `vibe-planning` is the primary user-facing implementation-planning workflow
  when the user asks for a plan, acceptance criteria, test plan, or rough
  vibe-coding implementation plan. Its normal output is a full plan file plus a
  short localized summary, not a full plan pasted into chat. It names concrete
  companion skills only after verifying them from the current environment,
  user-provided material, project instructions, or local metadata; unavailable
  skills remain optional and get an explicit fallback.
- `vibe-plan-review` reviews a saved Markdown implementation plan before
  execution, one item at a time. It keeps the original plan unchanged during
  review, keeps localized labels and numeric input shortcuts in
  `references/localized-labels.md`, may maintain `.<plan-name>.review.md`
  beside larger reviewed plans, and requires explicit confirmation before
  reflecting item decisions back into the executable plan. Non-sensitive paths,
  commands, and identifiers remain stable anchors, but suspected credential
  literals are redacted from chat, review-state files, reflected plans,
  summaries, commit messages, and tool arguments; affected items remain blocked
  or held until the user confirms a safe secret reference.
- `vibe-plan-execution` is for implementing from an already-bound concrete plan.
  The plan can come from a planning workflow, a specification, an issue, a task
  list, or an inline plan supplied by the user. If a
  summary names a local plan file, read that file as the authoritative
  implementation contract. If no concrete plan exists, return to planning before
  coding.
- `vibe-writing` governs writing quality and commit-message content. When
  explicitly invoked as the primary workflow for tracked text edits, it may
  stage and create a scoped verified local checkpoint; chat replies, summaries,
  and commit-message drafts do not. PR submission, release actions, broader
  history mutation, and unrelated paths stay outside its authority.
  Project-specific workflows and the repo's release rules take precedence.
  Under `vibe-coding`, verified available `vibe-writing` must be used as
  auxiliary guidance whenever a commit message is prepared or inspected, while
  commit permission and history mutation remain with the active workflow.
- `vibe-commit` owns file selection, exclusion, the staged-set re-verification
  gate, message content minimums, message transport, history mutation, and
  authorship-trailer `--trailer` transport. It commits when asked but does not
  push, and it does not amend or rebase already-pushed or shared history without
  explicit informed consent. Project-specific workflows and the repo's release
  and commit rules take precedence over its defaults.
- `vibe-review` runs only when the current directory is a git repository and
  the chosen review target resolves to a non-empty diff. It is platform-neutral:
  Claude Code with the `codex` plugin can be documented as a special backend,
  but the default contract is a host capability model for review-only delegated
  reviewers. If the selected adversarial delegated path is unavailable, the
  workflow pauses for explicit approval of an available backend or mode instead
  of silently downgrading. For `branch` and `base-ref` scopes, commits, squashes,
  resets, amends, and similar history operations require operation-specific user
  consent plus dirty-state, ownership, preview, isolation-restore, and
  conflict-safety preconditions. A scoped local closure commit for verified
  selected fixes is the default under explicit invocation unless denied or
  blocked; squash, reset, amend, rebase, push, and release/version work still
  require operation-specific consent.
