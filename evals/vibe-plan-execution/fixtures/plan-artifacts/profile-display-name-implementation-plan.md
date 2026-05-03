# Profile Display Name Plan

## Goal
- Original user intent: プロフィール画面で表示名を編集できるようにしたいです。
- Operational goal: let signed-in users update their display name from the existing profile settings screen.

## Verified facts and sources
| Claim | Evidence | Source | Impact |
| --- | --- | --- | --- |
| The app already has a profile settings screen. | Local investigation | `evals/vibe-plan-execution/fixtures/profile-display-name/src/settings/ProfileForm.tsx` | Current UI surface exists. |
| User records have a nullable `display_name` column. | Local investigation | `evals/vibe-plan-execution/fixtures/profile-display-name/db/schema.sql` | No migration is needed for this slice. |

## Requirements
- In scope: edit display name, save, cancel, loading state, validation for empty and over-50-character names.
- Out of scope: avatar upload, username changes, account deletion, and unrelated profile settings cleanup.
- Constraints: follow existing form patterns.

## Ambiguities, questions, and decisions
- Item: exact server action or API helper used by the real project.
- Options or decision: inspect local form submit wiring before editing.
- Evidence: `Local investigation` required in the implementation workspace.
- Recommended path: preserve the existing pattern and change only display-name behavior.

## Acceptance criteria
- A signed-in user can save a 1-50 character display name.
- Empty and overlong names show validation errors and do not submit.
- Cancel restores the previous value.
- Loading and error states remain visible and do not lose the user's last saved value.

## Test plan
- Acceptance tests: save a valid display name and observe the saved value.
- Regression tests: cancel restores the previous value.
- Negative and edge cases: empty name, over-50-character name, submit error.
- Manual or visual checks: confirm validation and pending states are visible.

## Implementation plan
1. Inspect the existing profile form, schema, and test patterns.
2. Add display-name validation and submit wiring using the existing pattern.
3. Add or update component tests for save, validation failure, cancel, and relevant loading or error state.
4. Run the relevant tests and review the diff against the acceptance criteria.

## Risks and unproven items
- Item: exact persistence helper in the target workspace.
- Evidence label: `Unproven`
- Impact: determines which local submit path to edit.
- Fastest proof path: inspect the form submit handler and existing profile tests before editing.
- Revisit trigger: before changing production code.

## Implementation handoff
- When implementing this plan, treat this document as authoritative. Re-check local facts before editing, follow the acceptance criteria and test plan, implement only the current in-scope slice, and stop if the `Proceed condition` is blocked or local evidence contradicts the plan.

## Proceed condition
- Implementation may begin after the existing profile form and tests are inspected.
