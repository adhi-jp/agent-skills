---
version: 1.0.0
name: vibe-plan-execution
description: Use when the user asks to execute, implement, continue, or apply an existing vibe-planning output, implementation plan, specification, acceptance criteria, or task plan. Do not use for plan creation or coding requests with no concrete plan to bind.
---

# Vibe Plan Execution

## Overview

Execute an existing implementation plan without inventing missing behavior. Bind
to the plan, verify the facts it depends on, implement the smallest safe current
slice, and stop when reality contradicts the plan.

If no concrete plan exists, use `vibe-planning` or another planning workflow
before coding.

## Relationship to `vibe-planning`

This skill executes bound implementation plans. Prefer a `vibe-planning` output
when one exists, and read these sections directly:

- `Goal`, `Requirements`, and `Acceptance criteria` define the behavior
  contract for the current slice.
- `Verified facts and sources` is reusable evidence; re-check workspace facts
  that may have changed since planning.
- `Test plan` defines the first verification path unless local evidence shows it
  is stale or insufficient.
- `Implementation plan` defines the edit order; do not add adjacent work.
- `Risks and unproven items` and `Proceed condition` decide whether coding
  starts, stays conditional, or returns to planning.

If a `vibe-planning` plan says implementation is blocked, do not start coding.
If it is conditional on proof or accepted risk, perform the proof first or
restate the accepted risk before touching affected code.

## Concrete Plan Requirements

A plan is concrete enough to execute only when the current slice has:

- A goal and user-visible outcome.
- In-scope and out-of-scope behavior.
- Acceptance criteria or equivalent pass/fail checks.
- A test, proof, or manual verification path.
- Implementation steps or a named code area to inspect first.
- Open risks, unproven items, or a statement that none are known.

If any missing item changes what to build, how to test it, data handling,
permissions, external contracts, or user experience, return to `vibe-planning`
instead of inventing the gap.

## When Not to Use

Do not use this skill for:

- Creating the initial plan, specification, acceptance criteria, or test plan.
- Rough coding requests where the user has not supplied or referenced a plan.
- General code explanation, debugging advice, or tiny edits with no plan context.
- Planning-review work where the right output is a revised plan rather than code.

## Core Rules

- Identify the implementation plan before editing files. If multiple plans
  could apply, ask the user which one is authoritative.
- Treat the user's words as intent, not verified fact. Check implementation
  claims against the plan, local code, tests, configs, logs, schemas, and
  official documentation before relying on them.
- Do not implement outside the plan without the user's explicit agreement. When
  an unplanned change appears necessary, explain the reason, impact, and closest
  plan-preserving alternative first.
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

Use these labels internally and in user-facing blockers when they affect the
implementation decision:

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

## Execution Workflow

1. **Bind the plan**
   - Name the source plan and the current slice being implemented.
   - Extract in-scope behavior, out-of-scope behavior, acceptance criteria,
     tests, constraints, and explicit non-goals.
   - Read the `Proceed condition` first when the plan came from `vibe-planning`.
   - If the concrete plan requirements are missing and the gap affects
     implementation, stop and ask for a planning update instead of filling it in.
2. **Verify before editing**
   - Inspect the relevant files, tests, configuration, schemas, and docs.
   - Use official docs or upstream source for external APIs, framework rules,
     product limits, permissions, data contracts, and unstable facts.
   - Compare the plan with local reality. Record conflicts before choosing an
     implementation path.
3. **Lock the current slice**
   - Implement only the smallest coherent unit from the plan that can be tested.
   - Keep future phases, nice-to-have improvements, and adjacent cleanup out of
     the edit unless the bound plan includes them.
   - If the user asks to add scope mid-implementation, classify it as a plan
     change and get explicit agreement before editing.
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

## Stop Conditions

Stop before implementation, or pause an in-progress implementation, when:

- No concrete implementation plan is available.
- The plan cannot be bound to the current workspace or branch.
- A `vibe-planning` `Proceed condition` says implementation is blocked.
- The plan omits behavior, tests, data handling, permissions, or external
  contracts needed for the current slice.
- Local evidence or a primary source contradicts the plan.
- The requested edit requires changing scope, architecture, data model,
  permissions, billing, security posture, UX behavior, or release process beyond
  the plan.
- An external API, library, framework, or product limit is relevant but unverified.
- The only available path is destructive, irreversible, credential-exposing, or
  unsafe without additional proof or permission.

When stopping, explain:

1. What part of the plan is blocked.
2. The evidence behind the blocker.
3. The closest viable path that preserves the user's intent.
4. The decision or proof needed to resume.

## User Communication

- Keep progress updates tied to the plan: "I am implementing step 2" or "This
  conflicts with acceptance criterion 3."
- When no concrete plan exists, say implementation is blocked and name
  `vibe-planning` or the active planning workflow as the next step.
- For non-technical users, describe consequences in workflow terms before naming
  the implementation detail.
- Do not bury plan deviations in the final summary. Call them out before editing.
- In the final response, include the implemented slice, verification performed,
  plan deviations or blockers, and any remaining planned steps.

## Quality Checklist

Before finalizing:

- The implementation plan was explicitly identified.
- The current slice stayed inside the plan or the user approved a deviation.
- Every implementation-affecting claim came from `Plan`, `Local evidence`, or
  `Primary source`.
- False or infeasible plan items were challenged with evidence and alternatives.
- Tests or proof checks matched the plan's acceptance criteria.
- The final diff was reviewed against plan scope and non-goals.
