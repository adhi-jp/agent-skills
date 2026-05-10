---
version: 1.2.0
name: vibe-plan-execution
description: Use when the user asks to execute, implement, continue, or apply an existing implementation plan, specification, acceptance criteria, task plan, or vibe-planning output. Do not use for plan creation or coding requests with no concrete plan to bind.
---

# Vibe Plan Execution

## Overview

Execute an existing implementation plan without inventing missing behavior. Bind
to the plan, verify the facts it depends on, implement the smallest safe current
slice, and stop when reality contradicts the plan.

Questioning a plan is allowed. Deviating from it is not allowed until verified
evidence proves the plan is incorrect, stale, impossible, unsafe, or already
satisfied. Treat "this looks redundant" as a hypothesis, not as permission to
skip planned API, specification, implementation, or test work.

If no concrete plan exists, return to planning before coding. `vibe-planning`
is one valid planning workflow, not a prerequisite for this skill.

## Plan Sources

This skill executes any concrete bound implementation plan. The plan may come
from `vibe-planning`, another planning workflow, a hand-written specification,
an issue, a task list, or the current conversation.

Plans produced by `vibe-planning` need one extra check because they usually
write a Markdown plan artifact and return only a short user-facing summary. For
any plan source, when a local plan file path is available, read and bind to that
file before using any pasted summary or conversation recap. When the plan has
these sections, read them directly:

- `Goal`, `Requirements`, and `Acceptance criteria` define the behavior
  contract for the current slice.
- `Verified facts and sources` is reusable evidence; re-check workspace facts
  that may have changed since planning.
- `Test plan` defines the first verification path unless local evidence shows it
  is stale or insufficient.
- `Implementation plan` defines the edit order; do not add adjacent work.
- `Risks and unproven items` and `Proceed condition` decide whether coding
  starts, stays conditional, or returns to planning.

If the bound plan says implementation is blocked, do not start coding. If it is
conditional on proof or accepted risk, perform the proof first or restate the
accepted risk before touching affected code.

Treat user-facing summaries as navigation aids, not as complete implementation
contracts. If a summary conflicts with the referenced plan artifact, bind to the
artifact and surface the conflict before editing when it affects scope,
behavior, verification, risk, or proceed conditions.

## Concrete Plan Requirements

A plan is concrete enough to execute only when the current slice has:

- A goal and user-visible outcome.
- In-scope and out-of-scope behavior.
- Acceptance criteria or equivalent pass/fail checks.
- A test, proof, or manual verification path.
- Implementation steps or a named code area to inspect first.
- Open risks, unproven items, or a statement that none are known.

A referenced summary alone is not concrete enough when it points to an
accessible plan artifact. Read the artifact first. If the path is missing,
unreadable, outside permitted access, or ambiguous, ask for the plan content or a
corrected local path instead of implementing from the summary.

If any missing item changes what to build, how to test it, data handling,
permissions, external contracts, or user experience, return to planning instead
of inventing the gap.

## When Not to Use

Do not use this skill for:

- Creating the initial plan, specification, acceptance criteria, or test plan.
- Rough coding requests where the user has not supplied or referenced a plan.
- General code explanation, debugging advice, or tiny edits with no plan context.
- Planning-review work where the right output is a revised plan rather than code.

## Core Rules

- Identify the implementation plan before editing files. If the user references
  a local plan file path, read it before editing. If multiple plans could apply,
  ask the user which one is authoritative.
- Treat the user's words as intent, not verified fact. Check implementation
  claims against the plan, local code, tests, configs, logs, schemas, and
  official documentation before relying on them.
- The bound plan remains authoritative even when it seems redundant,
  inefficient, overly broad, or simplifiable. Only `Local evidence` or
  `Primary source` verification can prove that a planned step may be skipped,
  reordered, narrowed, or replaced.
- Do not implement outside the plan unless the Plan Deviation Gate has passed
  and the user explicitly agrees. When an unplanned change appears necessary,
  explain the reason, impact, and closest plan-preserving alternative first.
- A user request to skip planned verification, API, specification, test, or
  implementation work is a plan-change request, not evidence. Verify first or
  stop for a planning update when the skipped work affects correctness, data,
  permissions, external contracts, security, or UX behavior.
- Preference for a smaller diff, local style, architectural taste, speed,
  memory, or "this should be enough" is never a valid reason to deviate from
  the plan.
- Do not silently "fix" an incorrect or impossible plan. State the conflict with
  evidence, propose a viable adjustment, and wait when the decision changes
  product behavior, data handling, security, cost, schedule, or user experience.
- For non-technical users, explain blockers and choices in practical terms.
  Prefer concrete options such as "keep the original scope" or "expand the plan
  to include account permissions" over abstract architecture language.
- Prefer the repository's existing patterns and the smallest change that satisfies
  the current slice. Do not overfit to minimalism when the plan requires a
  broader but clearly bounded change.

## Evidence Classes

Use these labels internally and in user-facing blockers, questions, plan
deviation notices, commit-checkpoint decisions, and execution summaries when
they affect scope, behavior, verification, risk, commit authorization, or
whether implementation may proceed:

- `Plan`: stated by the bound implementation plan, specification, acceptance
  criteria, or task list.
- `Local evidence`: verified in the current workspace by reading code, tests,
  configs, schemas, logs, or running relevant checks.
- `Primary source`: official documentation, authoritative specifications,
  upstream source, vendor docs, or user-provided source material.
- `Accepted risk`: an `Unproven` item explicitly accepted in the bound plan or
  current conversation, with impact and revisit trigger preserved.
- `Unproven`: memory, inference, unchecked user claims, secondhand summaries, or
  assumptions not yet backed by the plan, local evidence, or a primary source.

Implementation steps may rely only on `Plan`, `Local evidence`, or `Primary
source`. `Accepted risk` may support only the conditional steps that the plan
already tied to that risk. Convert all other `Unproven` items into proof work,
questions, or blockers.

Do not omit evidence labels only because no files were edited. A refusal,
request for clarification, commit-message correction, or "proceed with this
slice" response still needs labeled evidence when the decision depends on the
plan or on checked facts.

## Plan Deviation Gate

Changing planned scope, edit order, proof strategy, test strategy, API or data
contract handling, named implementation surface, or omitting any
correctness-affecting step is a plan deviation. Skipping a planned check because
it appears redundant is a deviation.

Before proposing or taking a deviation, complete all of these steps:

1. Re-read the exact plan item, acceptance criteria, test plan, risks, and
   proceed condition that the deviation would affect.
2. Verify the relevant local code, tests, configuration, schemas, logs, and
   named implementation surfaces.
3. Verify relevant primary sources for external APIs, framework rules,
   specifications, permissions, product limits, and data contracts.
4. Decide whether evidence proves that the plan is contradicted by reality,
   impossible as written, unsafe, stale, or already satisfied by existing code
   and tests.
5. Before editing the affected code, send a deviation notice with the exact plan
   item, checks performed, evidence labels and sources, impact, closest
   plan-preserving alternative, and user decision or proof needed.

If the evidence does not prove one of those conditions, follow the plan. If the
proof cannot be performed with available access, stop and make the missing proof
or planning decision explicit. Do not ask the user to approve an evidence-free
deviation.

## Execution Workflow

1. **Bind the plan**
   - Name the source plan, including the local path when it came from a file,
     and the current slice being implemented.
   - Extract in-scope behavior, out-of-scope behavior, acceptance criteria,
     tests, constraints, and explicit non-goals.
   - Quote or paraphrase the plan's `Proceed condition` when it has one. For
     `vibe-planning` artifacts, read it before other sections.
   - If a user-facing summary differs from the full plan artifact, treat the
     artifact as authoritative and stop for a decision when the difference
     changes behavior, scope, tests, risks, or the proceed condition.
   - If the concrete plan requirements are missing and the gap affects
     implementation, stop and ask for a planning update instead of filling it in.
2. **Verify before editing**
   - Inspect the relevant files, tests, configuration, schemas, and docs.
   - Use official docs or upstream source for external APIs, framework rules,
     product limits, permissions, data contracts, and unstable facts.
   - Compare the plan with local reality. Record conflicts before choosing an
     implementation path.
   - Run the Plan Deviation Gate before skipping, reordering, narrowing, or
     replacing any planned proof, API/specification check, test, or edit.
3. **Lock the current slice**
   - Implement only the smallest coherent unit from the plan that can be tested.
   - Keep future phases, nice-to-have improvements, and adjacent cleanup out of
     the edit unless the bound plan includes them.
   - If the user asks to add scope mid-implementation, classify it as a plan
     change and get explicit agreement before editing.
   - Treat omitting a planned step as a deviation when that step could affect
     correctness, contracts, tests, data handling, permissions, security, or UX.
4. **Prove behavior before or alongside code**
   - Follow the test or proof strategy in the plan.
   - For bug fixes, reproduce the failure or add a regression test when feasible.
   - For refactors, protect existing behavior with equivalence checks.
   - For UI work, verify states and responsive behavior the plan calls out.
5. **Implement conservatively**
   - Reuse local helpers, conventions, naming, and architecture.
   - Keep changes close to the planned files and behavior surface.
   - Add comments only when they clarify non-obvious reasoning.
6. **Verify and review**
   - Run the plan's checks plus the repository's relevant lint, type, test, build,
     or manual smoke checks.
   - Review the final diff against the plan's acceptance criteria and non-goals.
   - Report any skipped check with the reason and residual risk.
7. **Commit verified checkpoints when authorized**
   - Commit only when the user explicitly authorized commits or the bound plan
     includes commit checkpoints the user asked to execute.
   - Commit after each completed and verified phase, slice, or checkpoint. Keep
     each commit logically scoped to the verified change.
   - Do not commit discovery-only, unverified, failing, or work-in-progress states
     unless the user explicitly accepts that exact state.
   - Use Conventional Commits and the repository's commit rules.
   - Write commit messages as standalone, durable prose: describe the actual
     behavior or documentation change, not prompt context, conversation context,
     or plan labels. Avoid references like `per the plan`, `above`,
     `as requested`, `Phase 1`, `step 2`, or `implementation plan`; name the
     concrete change instead.

## Stop Conditions

Stop before implementation, or pause an in-progress implementation, when:

- No concrete implementation plan is available.
- The plan cannot be bound to the current workspace or branch.
- The bound plan's proceed condition, blocker, or risk section says
  implementation is blocked.
- The plan omits behavior, tests, data handling, permissions, or external
  contracts needed for the current slice.
- Local evidence or a primary source contradicts the plan.
- The requested edit requires changing scope, architecture, data model,
  permissions, billing, security posture, UX behavior, or release process beyond
  the plan.
- An external API, library, framework, or product limit is relevant but unverified.
- A proposed deviation has not passed the Plan Deviation Gate.
- The only reason for deviating is perceived redundancy, minimalism, preference,
  speed, memory, or another unverified assumption.
- The only available path is destructive, irreversible, credential-exposing, or
  unsafe without additional proof or permission.

When stopping, explain:

1. What part of the plan is blocked.
2. The evidence behind the blocker.
3. How that evidence affects the plan's `Proceed condition`, when one exists.
4. The closest viable path that preserves the user's intent.
5. The decision or proof needed to resume.

## User Communication

- Keep progress updates tied to the plan: "I am implementing step 2" or "This
  conflicts with acceptance criterion 3."
- When bound to a plan file, include the path in the initial binding note so the
  user can see which artifact controls the work.
- Include the plan's `Proceed condition` in the initial binding note or the
  first blocker notice, even when later local evidence overrides it.
- When no concrete plan exists, say implementation is blocked and name planning
  as the next step. Mention `vibe-planning` only when it is the appropriate or
  active planning workflow.
- For non-technical users, describe consequences in workflow terms before naming
  the implementation detail. Keep evidence labels explicit but light, such as
  "根拠: `Plan` ..." or "Evidence: `Plan` ...".
- Do not bury plan deviations in the final summary. Call them out before editing
  with the exact plan item, checks performed, evidence, impact, closest
  plan-preserving alternative, and decision needed.
- In the final response, include the implemented slice, verification performed,
  plan deviations or blockers, and any remaining planned steps.

## Quality Checklist

Before finalizing:

- The implementation plan was explicitly identified.
- Any referenced local plan file was read before using a summary.
- The plan's `Proceed condition`, when present, was quoted or paraphrased before
  editing or in the first blocker notice.
- The current slice stayed inside the plan or the user approved an
  evidence-backed deviation after the Plan Deviation Gate was satisfied.
- No planned step was skipped, reordered, narrowed, or replaced for perceived
  redundancy without passing the Plan Deviation Gate first.
- Every approved deviation identified the exact affected plan item, verification
  performed, evidence labels and sources, impact, closest plan-preserving
  alternative, and user decision.
- Every implementation-affecting or decision-affecting claim came from `Plan`,
  `Local evidence`, `Primary source`, or scoped `Accepted risk`, and user-facing
  decisions used those labels even when no code was edited.
- False or infeasible plan items were challenged with evidence and alternatives.
- Tests or proof checks matched the plan's acceptance criteria.
- The final diff was reviewed against plan scope and non-goals.
- Authorized commits, if any, were made only after verified checkpoints and used
  standalone Conventional Commit messages without prompt or plan-label leaks.
