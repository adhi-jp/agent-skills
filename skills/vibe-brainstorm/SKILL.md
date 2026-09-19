---
version: 1.6.1
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
   coordinator-separated perspectives unless independence is itself material.
   Those perspectives are the coordinator's own work within the requested
   mode and need no separate delegation or fallback authorization; label them
   coordinator-derived and claim no independent evidence. If independence is
   material or the user explicitly prohibits coordinator-only work, state the
   limitation and stop or ask about risk.

### Model Choice

<!-- shared-contract:class language=none commit=none effect=read-only -->
<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a model for each delegated unit by capability and context fit, never by hard-coded name.**

- Only choose when the host allows it and the user has not fixed a model.
- Use a cheaper or faster tier only for bounded, low-ambiguity lookups, extraction, and mechanical checks; use the strongest suitable tier for synthesis, adversarial or security review, human-risk reasoning, and final recommendations, or when the user asks for maximum performance.
- Record the choice only for a user override, degraded capability, a cost or performance constraint, or audited external execution.
<!-- shared-contract:end model-tier-selection -->

Each delegated role is one such unit: the judgment-heavy ones here include
creative synthesis — especially the `Unconventional` and `Challenging`
generators — convention tradeoffs, selection, broad-context grounding, final
recommendations, contradiction resolution, and user-risk judgments. A cheaper
or faster model is eligible here only for bounded low-ambiguity checks. In an
orchestration schedule, explain each role's capability and context needs
without enumerating routine role-to-tier assignments; include an explicit
assignment only when one of the four recording conditions above applies, and
name that condition.

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
3. Return the ideas grouped by direction, under the mode and delegation-state
   opening of `Response Shape`; when no delegation ran, that opening labels the
   directions coordinator-derived.
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
   direction, as a carry-forward packet, for later requirements or planning; do not call it user-confirmed
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
**Write nothing beyond what the phase's declared effect class and boundary permit.**

- Apply the effect class the phase declares in its own text; where this package states a narrower limit, the narrower limit wins.
- Read-only: report in chat; edit no file, run no state-mutating command, and never stage, commit, tag, push, change versions, delete data, or start services. Write a file only when the user explicitly asks for a saved artifact.
- Artifact-only: create or update only the artifact the phase owns and the supporting paths its text declares, such as a confirmed plan reflection or a decision record, and leave them in the working tree.
- Never let an artifact-only phase implement executable behavior, edit code or tests as implementation, produce another phase's artifact, do release work, or treat its artifact as same-turn implementation authority.
- State-changing: edit and run commands only inside the declared scope, in its smallest verified unit; leave other paths, pre-existing changes, and runtime or external state untouched unless the user selects them.
- These limits cover shell commands (redirection, `sed -i`, `tee`, `mv`, `cp`, `rm`, `git checkout --`) as well as file tools; report a refused write as a boundary stop and never retry it through another tool.
- Keep every irreversible or outward-facing operation under its own consent.
<!-- shared-contract:end effect-write-boundaries -->

This phase owns no artifact: it writes a file only when the current user's own
instruction asks to save one, and a path a host or runner designates for a
possible artifact is not that request. Without it, keep the brainstorm,
checklist, orchestration schedule, and confirmation request in chat, even when
they use Markdown headings or describe later work.

### Durable Records

Read `references/durable-records.md` before handing a settled decision or
deferred finding forward. This phase ordinarily writes neither `docs/decisions/`
nor `docs/reports/findings/`; it passes them on as the carry-forward packet that
reference defines, and a saved artifact the user explicitly requests stays
within this phase's own boundary.

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
stage files, commit, or claim the direction is approved. Hand the confirmed or
proxy-selected direction and its rejected candidates forward as a carry-forward
packet; this phase writes no decision record itself.
