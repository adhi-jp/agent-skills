---
version: 1.5.0
name: vibe-brainstorm
description: Use when the user explicitly asks for vibe brainstorming, creative implementation ideas, implicit expected behavior, or convention checks, and when an implementation task is creative or convention-dependent. Do not use for obvious mechanical edits.
---

# Vibe Brainstorm

## Overview

Use this skill before creative implementation scope hardens. It helps agents
surface implicit expected behavior, explore `Practical` / `Unconventional` /
`Challenging` idea directions, and select a direction without moving it into
implementation until the user confirms it.

Trusted top-level orchestration may request a proxy selection so a creative
phase does not stop on multiple preference questions. That proxy selection is
an AI-selected direction for later requirements or planning work, not explicit
human-user confirmation and not implementation authorization.

Multiple perspectives are a reasoning goal, not a fixed worker topology. Use
separate delegated roles only when independence or specialist context adds
material value and the host safely supports it; otherwise produce the same
perspective separation locally without claiming delegation.

## Activation

Use this skill when:

- The user explicitly invokes `vibe-brainstorm` or asks for creative
  implementation brainstorming.
- The user asks for ideas, alternatives, interaction concepts, feature behavior,
  interaction rules, UX flow, or implementation direction where implicit
  expected behavior matters.
- You are about to implement a feature with domain conventions, common user
  expectations, spatial or stateful behavior, UI interaction norms, fairness
  rules, accessibility expectations, data consistency, or feedback semantics.

Do not use this skill for:

- Obvious mechanical edits, renames, formatting, dependency bumps, direct bug
  fixes with a concrete plan, or one-line requested changes.
- Tasks where the user already approved a concrete implementation direction and
  only wants execution.
- Conventional code review after implementation; use the relevant review or
  debug workflow instead.
- Drafting, saving, or approving a durable requirements specification artifact.
  Brainstormed directions become requirements only after the user confirms them
  and a requirements-capture workflow records them; trusted top-level proxy
  selections become only AI-selected input until that later workflow records the
  requirement status.

## Mode Selection

| Situation | Mode |
| --- | --- |
| User explicitly asks for `diverge` or "ideas only" | `diverge` |
| Autonomous trigger during implementation work | `conventions` |
| User asks for convention/expected-behavior checking only | `conventions` |
| User explicitly asks for `full`, "brainstorm and choose", or a complete creative pass | `full` |
| Explicit `vibe-brainstorm` invocation with no mode and a creative implementation goal | `full` |

`full` is not the autonomous default. Use it autonomously only when the task is
clearly creative enough that idea generation, convention grounding, development,
and selection are all necessary before implementation can be scoped.

## Delegation Gate

Before using delegated perspectives:

1. Verify the host exposes a delegation or sub-agent mechanism.
2. Verify the current task allows delegated work and any required data sharing.
3. Verify the run can leave recordable evidence for any later claim that real
   sub-agents ran. The evidence should be host- or runner-provided, such as an
   attached run artifact, delegated invocation metadata, task IDs emitted by the
   tool system, a host-issued run identity, a transcript/journal path, or an
   equivalent host record. When the only durable surface is the final response,
   report the evidence status honestly: `confirmed` only if you can cite the
   host-issued identifier or record location you rely on; otherwise `unproven`.
   Do not treat role headings, persona separation, polished summaries, or
   self-reported token totals as proof of delegation.
4. Keep the delegated prompts bounded: ask for concise findings, tradeoffs, and
   observable checks, not private chain-of-thought.
5. Choose the delegated model for each role under `Model Choice` below.
6. If delegation is unavailable, unrecordable, or not authorized, continue with
   coordinator-separated perspectives unless independence is itself material;
   in that exceptional case, state the limitation and stop or ask about risk.

### Model Choice

<!-- shared-contract:class language=none commit=none effect=read-only -->
<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
When the host lets the phase choose a delegated model and the user has not explicitly fixed one, choose a fit-for-purpose model per delegated unit by capability and context fit, not by hard-coded model name. Use a cheaper or faster model only for bounded, low-ambiguity work — lookups, extraction, mechanical checks, simple review — when lower capability is quality-neutral or the user prioritizes cost or latency. Bias upward to the strongest suitable reasoning and context tier available for judgment-heavy work: cross-artifact synthesis, adversarial review, security, data-safety, and other human-risk reasoning, contract compliance, contradiction resolution, and final recommendations or dispositions, especially when the user asks for maximum performance. Do not inherit the top model for every small unit, and do not downshift solely to save tokens when the unit needs stronger reasoning. Record the model choice only for an explicit user override, degraded capability, a cost or performance constraint, or audited external execution; routine compatible choices need no receipt.
Where a package declares a stricter or narrower rule in its own text, that declaration controls.
<!-- shared-contract:end model-tier-selection -->

Each delegated role is one such unit: the judgment-heavy ones here are creative
synthesis — especially the `Unconventional` and `Challenging` generators —
convention tradeoffs, selection, broad-context grounding, final recommendations,
contradiction resolution, and user-risk judgments. A cheaper or faster model
is eligible here only for bounded low-ambiguity checks.

### Delegation Mechanisms And Evidence

A delegation mechanism may be ad-hoc per-role sub-agent invocation or one
scripted orchestration run: a host mechanism that fans out several roles under
a single deterministic, independently recorded run and returns their results.
Both satisfy check 1, and an orchestration run's host-recorded run identity,
per-role task records, or run journal satisfies check 3 when the later reader
can inspect it. A scripted run cannot pause for user input, so schedule only
generator, critic, development, grounding, and selection stages inside it;
manual checklist confirmation and final direction confirmation stay in the
conversation after the run returns. In trusted proxy-selection mode, the
selection role may choose a direction for the coordinator to carry as
AI-selected input, but that choice remains separate from human confirmation.
When the current user instruction explicitly states that such a scripted
mechanism is available, treat that declaration as sufficient to design the
bounded orchestration schedule. If the current host cannot actually invoke or
record the run, do not replace it with coordinator-generated brainstorm
results: return the planned stages, role-specific capability-tier basis,
required run/task evidence, and post-run conversation confirmation boundary.
Ask each role for a bounded structured result — candidates, fit, tradeoffs,
risks, or checklist entries — so results can be collected and merged without
re-deriving them. Do not require a specific host orchestration tool. Do not end
the user-facing answer as only an unresolved background-wait or continuation
stub. If a scripted run is pending or its results will not be recorded in the
current output set, say the run is incomplete for this answer, list the planned
stage boundary, evidence boundary, model-tier basis when relevant, and the
conversation confirmation that must happen after results return.

Any claim that real sub-agents ran must be paired with its evidence status.
A polished response, role headings, persona separation, runtime summaries,
self-reported token totals, or the existence of multiple differently styled
sections are not proof of delegation. Host-issued task IDs, agent IDs, run IDs,
transcript or journal paths, tool metadata fields, host-rendered tool blocks, or
trace excerpts may be cited as delegation evidence when they are the concrete
record you rely on. If those records are unavailable or cannot be cited, label
real delegation as `unproven` and keep any fallback or coordinator-only result
separate from confirmed delegated output.

## Delegated Roles

When delegation is verified, authorized, and materially useful, choose from
these roles rather than requiring all of them:

- `Practical` generator.
- `Unconventional` generator.
- `Challenging` generator.
- Expected-behavior critic or end-user/domain-user role.
- Candidate development role for expanding viable ideas.
- Grounding role for matching ideas against expected-behavior and domain
  references.
- Selection role for applying the mandatory gate and creativity ranking.

Cover every selected perspective, but do not stop merely because one named role
cannot launch; use local reasoning unless independent evidence is required.

## Modes

### `diverge`

Use for idea generation only.

1. Generate three distinct perspectives, delegating them only when independence adds value:
   - `Practical`: low-risk ideas that fit familiar expectations.
   - `Unconventional`: unusual ideas that may reframe the experience.
   - `Challenging`: ambitious ideas that stretch implementation or interaction
     assumptions while still targeting the user's goal.
2. Ask each generator for candidates, fit, tradeoffs, and implementation risks.
3. Return the ideas grouped by direction.
4. Do not add convention critique, expected-behavior grounding, development,
   selection, ranking, or adoption recommendation unless the user asks for it.

### `conventions`

Use for expected-behavior grounding without idea generation. This is the default
mode when the skill triggers autonomously during implementation work.

1. Summarize the feature or behavior being scoped.
2. Apply an expected-behavior critic or end-user/domain-user perspective, delegated only when independence adds value. Ask what a reasonable user would expect to happen,
   including edge cases.
3. Build a checklist of implicit expected behavior. Separate:
   - mandatory expectations that would make the implementation feel wrong if
     missed;
   - optional or taste-based expectations;
   - unknowns that need user confirmation.
4. Check relevant local docs, existing code, official docs, upstream docs, or
   domain references when they are available and relevant. If reference access is
   missing, label the gap instead of fabricating certainty. When the user
   supplies a reference excerpt or named source in the prompt, identify which
   checklist entries are grounded by that source and keep inferred expectations
   and unknowns separate.
5. If delegation does not run, label the checklist as coordinator-derived; do not
   claim delegated evidence.
6. Stop before implementation and ask the user to confirm or adjust the
   checklist when it changes behavior, UX, domain rules, or implementation
   scope. In trusted proxy-selection mode, a verified
   end-user/domain-user perspective may select a proxy checklist for later
   requirements or planning, but it is not human confirmation.

### `full`

Use for the complete creative pass.

1. Run `diverge` to produce `Practical` / `Unconventional` / `Challenging`
   candidates.
2. Run the `conventions` grounding pass.
3. Develop each viable candidate through the candidate development role when
   delegation is available. Expand the candidate's user experience,
   implementation shape, risks, and convention interactions.
4. Use the grounding role to match developed candidates against the checklist
   and domain references.
5. Use the selection role to apply the two-stage selection sieve:
   - First reject candidates that fail mandatory expected-behavior gates. Show
     the violated gate for every rejection.
   - Then rank the remaining candidates by creativity, fit, and implementation
     practicality. Do not reject an unusual candidate merely because it is
     unusual.
6. Provide one adoption recommendation and any runner-up worth preserving.
7. Stop before implementation. Ask the user to confirm the selected direction
   before it becomes implementation scope or is handed to another workflow. In
   trusted proxy-selection mode, hand off only an AI-selected
   direction for later requirements or planning; do not call it user-confirmed
   and do not start implementation from it.

## Convention Grounding

Use all four grounding mechanisms when the mode includes conventions:

- Checklist-style expected behavior: concrete pass/fail expectations and edge
  cases.
- End-user role: delegated user, player, operator, or domain-user perspective
  when sub-agents are available.
- Domain/reference lookup: local project docs, existing implementation, official
  docs, upstream references, or domain material when relevant and accessible.
- User confirmation or orchestration proxy selection: a visible confirmation
  step before implementation when the checklist affects behavior or scope, or a
  trusted orchestration proxy selection that later requirements or planning must
  record as AI-selected input rather than human approval.

Keep mandatory gates narrow. A gate is mandatory only when missing it would
violate the user's goal, a domain convention, accessibility/safety expectation,
data contract, or a clear "normal users would expect this" behavior. Put taste,
polish, and speculative enhancements outside the mandatory gate.

Anchor convention checks in the current task, supplied references, local code,
and the user's stated domain. Do not carry preloaded niche examples,
third-party domain rules, platform rules, or fixture-specific checklists into
unrelated tasks.

When several plausible checklists or directions differ mainly by user effort,
error recovery, accessibility, data safety, or workflow friction, do not select
the cheapest implementation path by default. Surface the user-experience
tradeoff, prefer the option that preserves the expected behavior for the user's
goal, and label any cheaper alternative as optional or needing confirmation.

## Output Contract

### Effect And Write Boundaries

<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
Every workflow phase belongs to one effect class, declared in its own text, and writes nothing beyond what that class and its declared boundary permit.

- A read-only phase reads and reports. Its deliverable is chat: findings, alignment, or direction. It edits no source, test, config, doc, or other file, runs no command that mutates runtime or repository state, and does not stage, commit, tag, push, change versions, delete data, or start services. It writes a file only when the current user explicitly asks for a saved artifact.
- An artifact-only phase creates or updates the artifact it owns — the requirements spec, the plan, the plan-review state, the instruction files, or the text artifacts the request names — and the supporting paths its own text declares: the text it was asked to revise (comments, docstrings, docs), a confirmed reflection into the bound plan, an ignore file it previewed and the user confirmed, or a narrowly confirmed configuration edit its text names. It leaves those verified changes in the working tree. It does not implement executable behavior, does not edit application code or tests as implementation, does not produce an artifact another phase owns, and does not perform release work; its artifact never authorizes same-turn implementation.
- A state-changing phase edits files and runs commands inside the scope its own text declares — the unit it implements, the repair it proves, the fixes it applies, the round it integrates, or the commit it executes — and keeps its edits to the smallest verified unit of that scope. Paths outside the scope, pre-existing working-tree changes it did not make, and runtime or external state beyond the scope stay unwritten unless the current user selects them, and every irreversible or outward-facing operation stays under its own consent.
Where a package declares a stricter or narrower rule in its own text, that declaration controls.
<!-- shared-contract:end effect-write-boundaries -->

This phase owns no artifact and has no canonical path of its own: the only file
it writes is one the current user's own instruction asks to save.
A host or runner that merely designates a path to use *if* an artifact is
written does not count as that request; do not write to the path unless the
user's instruction asks for a saved artifact.

Apply this as a pre-output gate: before any file write, identify the user's
explicit persistence request. If there is none, keep the entire brainstorm,
checklist, orchestration schedule, and confirmation request in chat. These
outputs are not implementation plans, specifications, or other primary file
artifacts merely because they use Markdown headings or describe later work.

### Read-Only-Phase Write Gate

<!-- shared-contract:begin read-only-phase-write-gate source=shared/vibe-contract.md -->
This gate covers writes during a read-only or artifact-only phase. Observable input: the target path of a file-edit or file-write tool call, or a shell tool call whose command writes a path (redirection, `sed -i`, `tee`, a heredoc, `mv`, `cp`, `rm`, `git checkout --`, matched best-effort), together with the session record for this worktree under `.plans/vibe-sessions/`, reading `status`, `lease.expires_at`, `repository.worktree`, `host_session_id`, `phase`, `effect_mode`, and `allowed_paths`; the directory's other candidate records, to detect a conflicting record; the readable bytes of every artifact named in `artifact_identity`, to detect an identity mismatch; and any supplied prior record, to check `generation`.

Observable stop, with three outcomes: `deny`, with a reason that names the target path and quotes the recorded `phase`, `effect_mode`, and `allowed_paths`, only when a fresh, valid, session-bound record exists whose `effect_mode` is `read-only` or `artifact-only` and the target's canonical absolute path is outside every recorded `allowed_paths` entry (the entry itself or a path beneath a recorded directory); `allow` in every other case — a target inside `allowed_paths`, an `effect_mode` of `state-changing` or `none`, or a record that is absent, malformed, stale, foreign, session-unbound, conflicting, or identity-mismatched; and `ask`, which this gate never returns. No invalid record state ever produces `deny`, so the refusal never rests on unverified host behavior. A denied write is reported verbatim by the agent as a boundary stop, not retried through another tool.

Control-plane exception: a write whose target is the active session record itself — `.plans/vibe-sessions/<record_id>.json` under the repository root — or that record's temporary file in the same directory, written for the atomic rename, is `allow` regardless of `effect_mode`, when the target's canonical path is inside `.plans/vibe-sessions/` and its stem equals the active record's `record_id`. Every other path under that directory is judged like any other path, and the exception does not broaden `allowed_paths`.

When no user-installed hook enforces this gate, this wording is the whole gate: a read-only phase writes only an explicitly requested saved artifact whose canonical path is recorded in `allowed_paths` and otherwise writes no file; an artifact-only phase writes only the artifact it owns, the supporting paths its own text declares, and the scratch root recorded for the unit; the router's write of its own record falls under the exception above and is not a phase write; and a write outside that boundary is refused by the phase itself and reported as a boundary stop.
A package may state which of its phases this gate applies to; it may not change the gate's inputs, outcomes, or fields.
<!-- shared-contract:end read-only-phase-write-gate -->

This gate applies to the brainstorming phase.

### Response Shape

Use this shape, omitting or marking skipped sections only when the selected mode
does not run that stage:

- Mode and delegation status: mode used and one of these delegation states:
  `confirmed` when the response cites concrete host-provided evidence such as an
  artifact, metadata field, tool block, task ID, run ID, transcript or journal
  location, or trace excerpt; `unproven` when delegation may have happened but
  the response cannot cite such a record; or `unavailable/degraded` with the
  limitation and authorization status.
- Expected-behavior checklist: mandatory, optional, and unknown expectations, or
  `skipped by mode` for `diverge`.
- Candidates: grouped by `Practical` / `Unconventional` / `Challenging` for
  idea modes, or `not generated in conventions mode`.
- Selection: rejected candidates with violated gates, ranked surviving
  candidates, and adoption recommendation, or `skipped by mode`.
- Confirmation needed: the exact behavior checklist or selected direction the
  user must confirm before implementation starts, or the proxy-selected
  direction that a later requirements or planning phase must record as
  AI-selected input before any implementation scope exists.

Do not include private chain-of-thought from any agent. Summarize conclusions,
evidence, tradeoffs, and open questions.

## Handoff Boundary

This skill stops at confirmed direction or trusted orchestration proxy
selection. After user confirmation, hand the confirmed checklist or selected
candidate to implementation planning, plan execution, or ordinary coding as
appropriate. After a trusted orchestration proxy selection, hand the selected
checklist or candidate only to later requirements or planning as AI-selected
input. Without one of those outcomes, do not start implementation, create code,
stage files, commit, or claim the direction is approved.
