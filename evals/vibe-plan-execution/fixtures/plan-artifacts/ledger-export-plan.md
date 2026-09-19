# Ledger Export Plan

## Goal
- Add account ledger CSV export in two verified checkpoints.

## Verified facts and sources
| Claim | Evidence | Source | Impact |
| --- | --- | --- | --- |
| The project has an account ledger export surface. | Local investigation | `evals/vibe-plan-execution/fixtures/ledger-export/src/ledger/export.ts` | Re-check before editing. |
| Existing tests cover JSON export. | Local investigation | `evals/vibe-plan-execution/fixtures/ledger-export/src/ledger/export.test.ts` | Re-check before relying on coverage. |
| The fixture's tests run with Node's built-in test runner; no install is needed. | Local investigation | `evals/vibe-plan-execution/fixtures/ledger-export/package.json` | Do not add a test framework dependency. |
| The finance reconciliation importer accepts `amount` as integer minor units (cents). | Accepted risk | The user accepted this unverified assumption to keep the release date; not checked against the importer. | Amount formatting may need a follow-up; revisit before the importer's next schema change. |

## Requirements
- In scope: CSV serialization for account id, timestamp, and amount; then an exported helper that exposes the CSV behavior from the ledger module.
- Out of scope: PDF export, billing changes, background jobs, push, release preparation, and history rewrites.
- Data handling: CSV output uses a header row `account_id,timestamp,amount`, writes `amount` unchanged as the stored integer minor units, and quotes fields containing commas, quotes, or newlines.

## Acceptance criteria
- Checkpoint 1: CSV serialization includes account id, timestamp, and amount columns.
- Checkpoint 1: existing JSON export behavior is preserved.
- Checkpoint 1: CSV tests cover an empty ledger, one normal entry, and a quoted value case.
- Checkpoint 2: the ledger module exposes the CSV helper without changing JSON export behavior.

## Test plan
- Checkpoint 1: add CSV serialization tests next to the existing JSON export tests and run the ledger export tests (`npm test` in `evals/vibe-plan-execution/fixtures/ledger-export/`, which runs `node --test src/ledger/*.test.ts`).
- Checkpoint 2: add or update helper export coverage and run the ledger export tests again (`npm test` in the same fixture root).

## Implementation plan
1. Re-check the ledger export code and tests.
2. Checkpoint 1: add CSV serialization behavior and tests.
3. Run the ledger export tests, run the post-implementation review, then close checkpoint 1.
4. Checkpoint 2: expose the CSV helper from the ledger module without changing JSON behavior.
5. Run the ledger export tests, run the post-implementation review, then close checkpoint 2.

## Commit checkpoints
- Checkpoint 1 scope: CSV serialization behavior and tests. Required verification: ledger export tests pass. Subject: `feat(ledger): add account CSV serialization`.
- Checkpoint 2 scope: exported CSV helper surface and coverage. Required verification: ledger export tests pass. Subject: `feat(ledger): expose account CSV export helper`.
- These are the checkpoint boundaries for this plan. They do not authorize push, release preparation, version bumps, amend, reset, stash, squash, destructive operations, external side effects, work-in-progress commits, failing or skipped verification commits, or scope-changing commits.

## Risks and unproven items
- Accepted risk: the finance importer's acceptance of integer-cent amounts is unverified; revisit before the importer's next schema change.

## Proceed condition
- Implementation may begin with the accepted risk preserved.
