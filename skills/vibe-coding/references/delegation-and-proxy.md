# Delegation and Proxy Reference

Read this reference when host delegation or model choice is in play: the user
asks for sub-agents or a scripted orchestration run, a routed phase is about to
delegate or choose a delegated model, or a question-heavy phase could use a
proxy-decision branch.

## Delegation Record

A delegated unit carries work only inside the routed phase, under that
specialist's own delegation rules. When the unit relies on domain, stack, or
toolchain facts a loaded auxiliary skill supplies, its handoff must carry the
skill's name as its metadata states it; how the worker reaches the skill's
content; the instruction to load it before any dependent investigation and keep
it subordinate to the phase; and the facts already verified, with their sources
and the version they apply to, or, where none are verified, the unresolved
facts with the proof they still need. A handoff that only names the skill does
not satisfy this.

## Before choosing a delegated model

<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a model for each delegated unit by capability and context fit, never by hard-coded name.**

- Only choose when the host allows it and the user has not fixed a model.
- Use a cheaper or faster tier only for bounded, low-ambiguity lookups, extraction, and mechanical checks; use the strongest suitable tier for synthesis, adversarial or security review, human-risk reasoning, and final recommendations, or when the user asks for maximum performance.
- Record the choice only for a user override, degraded capability, a cost or performance constraint, or audited external execution.
<!-- shared-contract:end model-tier-selection -->

Do not narrow investigation, skip user or domain perspectives, or take a poorer
UX path only because it is faster when the selected phase's contract says those
surfaces are material. If budget, capability, or time cannot support that
depth, report a degraded route, blocked surface, or accepted-risk decision
instead of silently completing the cheaper path.

## Proxy Decisions

When a routed phase would otherwise ask the user a series of delegable
questions — preference, wording, ordering, low-risk scope trimming, convention,
test shape, or implementation approach — use that specialist's proxy-decision
branch when it has one, with permitted sub-agents as user, domain, or risk
perspectives. A proxy decision is an AI-selected default, assumption, or
direction recorded in the specialist's artifact language; it is never human
approval and never finish, handoff, proceed, accepted-risk, or consent
evidence. Human-risk decisions (the list in `SKILL.md`) still need explicit
human-user acceptance. The plan pre-check walkthrough has no proxy branch.
