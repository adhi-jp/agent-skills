---
version: 1.6.2
name: vibe-brainstorm
description: Use when the user explicitly asks for vibe brainstorming, creative implementation ideas, implicit expected behavior, or convention checks, and when an implementation task is creative or convention-dependent. Do not use for obvious mechanical edits.
---

# Vibe Brainstorm

Turn an underspecified creative request into ideas, expected behavior, and a
direction to confirm. This is a read-only, pre-implementation phase: a
trusted proxy may select input for later requirements or planning, but it is
not user confirmation or implementation authorization.

## Use and mode

Use this skill for requested ideas, alternatives, interaction behavior, or
convention-dependent implementation. Skip it for mechanical edits, a direct
bug fix with a concrete plan, approved execution, review, or a saved
requirements artifact.

| Situation | Mode |
| --- | --- |
| Explicit `diverge` or ideas only | `diverge` |
| Autonomous or convention-check request | `conventions` |
| Explicit `full`, or explicit invocation with a creative goal | `full` |

Do not autonomously choose `full` unless ideation, convention grounding, and
selection are all needed to scope the work.

## Perspectives and delegation

Use separate perspectives locally by default; delegate only when independent
work or specialist context materially helps and the host permits it. Never
claim delegation from headings or polished prose. Call it `confirmed` only
with a citable host record; otherwise say `unproven` or unavailable.

Delegated prompts request concise candidates, tradeoffs, risks, or checks, not
private reasoning. A user-stated scripted orchestration mechanism is sufficient
to plan its bounded schedule. If a scripted run is available, it may cover
generation, critique, development, grounding, and selection, but final
confirmation stays in chat. If the current host cannot actually invoke or record
that run, do not replace it with coordinator-generated brainstorm results.
Return the planned stages, role-specific capability-tier basis, required
run/task evidence, and the post-run conversation confirmation boundary instead.
For ordinary perspective gathering, give local coordinator-derived perspectives
unless independence itself is required; then state the limitation.

### Model Choice

<!-- shared-contract:class language=none commit=none effect=read-only -->
<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a model for each delegated unit by capability and context fit, never by hard-coded name.**

- Only choose when the host allows it and the user has not fixed a model.
- Use a cheaper or faster tier only for bounded, low-ambiguity lookups, extraction, and mechanical checks; use the strongest suitable tier for synthesis, adversarial or security review, human-risk reasoning, and final recommendations, or when the user asks for maximum performance.
- Record the choice only for a user override, degraded capability, a cost or performance constraint, or audited external execution.
<!-- shared-contract:end model-tier-selection -->

Creative synthesis, convention tradeoffs, selection, and final recommendations
need the stronger suitable capability; cheap tiers fit only bounded checks. In
an orchestration schedule, explain each role's capability and context needs;
name a tier or model only under one of the block's recording conditions, and
name that condition.

## Modes

### `diverge`

Generate `Practical`, `Unconventional`, and `Challenging` directions. For each,
give fit, tradeoffs, and implementation risks. Do not ground conventions,
rank, choose, recommend, or begin implementation.

### `conventions`

Summarize the behavior, then produce a checklist separating mandatory expected
behavior, optional taste, and unknowns. Ground it in relevant local, supplied,
official, or domain sources when available; label missing access and inference.
Mandatory means missing it would violate the goal, a real convention,
accessibility/safety expectation, data contract, or normal user expectation.
Surface meaningful UX tradeoffs rather than selecting the cheapest build path.
Stop for user confirmation when the checklist changes behavior or scope.

### `full`

Generate the three directions, run the convention checklist, develop viable
candidates, and apply this sieve: reject failures of mandatory gates (name the
gate), then rank survivors for creativity, fit, and practicality. Recommend a
direction and any worthwhile runner-up. Do not reject unusual ideas merely for
being unusual. Stop for user confirmation; a proxy-selected direction is only
AI-selected input for later requirements or planning.

## Output and boundary

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

Keep the result in chat unless the user explicitly requests a saved artifact.

### Response Shape

Report the mode and delegation state; the checklist; candidates where generated;
selection or skipped stages; and the exact checklist or direction requiring
confirmation. Summarize conclusions, evidence, tradeoffs, and open questions,
never private reasoning.

### Durable Records

Read `references/durable-records.md` only before handing a settled decision or
deferred finding forward. This phase writes neither decision nor finding
records; its packet remains unpersisted until a later writing phase records it.

## Handoff

Stop at user-confirmed direction or proxy selection. Hand the outcome forward
as a carry-forward packet; without confirmation, do not implement, edit,
stage, commit, or call it approved.
