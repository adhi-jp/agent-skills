# Delegation and Proxy Reference

Read this reference when host delegation or model choice is in play: the user
asks a sub-agent or a scripted orchestration run to carry work, a routed phase
is about to delegate, the host offers a choice of delegated models, a delegated
unit returns a result to accept, or a question-heavy specialist phase could use
a proxy-decision branch. It owns host delegation as transport, the delegation
record, the model-tier contract and model choice inside a routed phase, and
proxy decisions.

## Delegation Is Transport

Host delegation and orchestration mechanisms — single sub-agents or scripted
multi-agent orchestration runs — are execution transport inside a routed
phase, not routes or specialists. Phase selection, approvals, and stop
boundaries live in the conversation. A routed specialist may use host
delegation internally under its own delegation rules, but no orchestrated run
may be scheduled to cross a downstream skill's approval gate, stop condition,
or consent boundary in one unattended pass. When the user asks for one
unattended run across several phases, reject the schedule, route the immediate
phase only, and state that transport is limited to that phase under the
specialist's own rules; a blanket instruction to skip approvals is not approval
evidence for any phase.

## Delegation Record

Before a routed phase delegates work, its delegation record should bound the
unit: deliverable, hypothesis or question, maximum elapsed time, file/path or
surface boundary, changed-line budget when edits are allowed, verification
receipt, stop-and-return conditions, and compact context digest. Full parent
context inheritance in long sessions requires a phase-recorded reason. Three
consecutive empty waits for the same unit are a task-design signal: request a
checkpoint, split the task, or stop rather than continuing short polling.
User-facing updates require a new result, blocker, policy change, requested
decision, or user-requested reporting cadence; no-change polling is not
progress. Delegated shared-root edits must be avoided unless the phase permits
them and records changed paths plus verification status; otherwise use isolated
work or patch/diff handoff.

## Before choosing a delegated model

<!-- shared-contract:begin model-tier-selection source=shared/vibe-contract.md -->
**Choose a fit-for-purpose model per delegated unit by capability and context fit, not by hard-coded model name.**

- Choose only when the host lets the phase choose a delegated model and the user has not explicitly fixed one.
- Use a cheaper or faster model only for bounded, low-ambiguity work — lookups, extraction, mechanical checks, simple review — when lower capability is quality-neutral or the user prioritizes cost or latency.
- Bias upward to the strongest suitable reasoning and context tier available for judgment-heavy work: cross-artifact synthesis, adversarial review, security, data-safety, and other human-risk reasoning, contract compliance, contradiction resolution, and final recommendations or dispositions.
- Bias upward especially when the user asks for maximum performance.
- Never inherit the top model for every small unit.
- Never downshift solely to save tokens when the unit needs stronger reasoning.
- Record the model choice only for an explicit user override, degraded capability, a cost or performance constraint, or audited external execution.
- Give routine compatible choices no receipt.
<!-- shared-contract:end model-tier-selection -->

Inside a routed phase the choice stays within that phase's delegation contract:
model selection never leaves the selected phase's contract, never uses a
hard-coded model name, and never assigns one blanket model to an unattended
cross-phase run.

Orchestration quality is not a token-minimization objective. Do not narrow
investigation scope, skip user/domain perspectives, or choose a poorer UX path
only because it is faster when the selected phase's contract says those
surfaces are material. If the current budget, capability, or time cannot
support the needed depth, report a degraded route, blocked surface, or
accepted-risk decision instead of silently completing the cheaper path.

## Proxy Decisions

When a routed quality phase would normally ask a series of user questions to
improve requirements, creative direction, planning, or similar judgment quality,
use the specialist's trusted-orchestration or proxy-decision branch when it has
one instead of blocking on every delegable question. Delegable questions are
preference, wording, ordering, low-risk scope-trimming, convention, test-shape,
and implementation-approach judgments that can be decided from the user's goal,
local evidence, existing artifacts, or bounded sub-agent perspectives without
changing non-delegable risk. Use permitted and recordable sub-agents as proxy
user/domain/risk perspectives when the specialist allows them; otherwise use the
specialist's coordinator fallback if it allows one.

The plan pre-check walkthrough phase is inherently interactive and has no
proxy-decision branch: per-item plan decisions and reflection consent are not
delegable judgments. When unattended orchestration reaches that phase, report
the interactive requirement and stop instead of emulating item decisions.

Proxy decisions never become explicit human-user approval. Record them as
AI-selected defaults, assumptions, or proxy-selected directions using the
downstream specialist's artifact language, and keep any finish, handoff,
proceed, accepted-risk, and consent evidence separate. A proxy decision is
recorded in the session record, when it is recorded at all, as an event with
`source: agent-proposed`, which selects and approves nothing. Human-risk
decisions — the list in `SKILL.md` — still require explicit human-user
acceptance unless that acceptance is already recordably tied to the current
artifact.
