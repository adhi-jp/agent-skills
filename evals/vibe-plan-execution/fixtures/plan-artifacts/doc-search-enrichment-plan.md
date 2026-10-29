# Doc Search Section Enrichment Plan

## Goal
- Attach each search hit's enclosing section to the hit in one verified checkpoint.

## Verified facts and sources
| Claim | Evidence | Source | Impact |
| --- | --- | --- | --- |
| `searchDocs` returns hits with document id, line, and snippet. | Local investigation | `evals/vibe-plan-execution/fixtures/doc-search/src/search/search.ts` | Re-check before editing. |
| `enclosingSection` returns the deepest outline node whose line range contains a line, or null. | Local investigation | `evals/vibe-plan-execution/fixtures/doc-search/src/search/enclosing.ts` | Re-check before relying on it. |
| Existing tests cover hit order, the hit limit, and enclosing-section lookup. | Local investigation | `evals/vibe-plan-execution/fixtures/doc-search/src/search/search.test.ts` | Re-check before relying on coverage. |
| The fixture's tests run with Node's built-in test runner; no install is needed. | Local investigation | `evals/vibe-plan-execution/fixtures/doc-search/package.json` | Do not add a test framework dependency. |

## Requirements
- In scope: a `section` field on each hit that `searchDocs` returns: `{ title, depth }` of the deepest section enclosing the hit's line, or `null` when the line lies outside any section.
- Non-goals: ranking changes, new dependencies, changes to `searchDocs` parameters.

## Acceptance criteria
- Each hit carries `section` with the title and depth of the deepest section enclosing its line.
- A hit whose line lies outside any section carries `section: null`.
- Existing hit fields, hit order, and limit behavior are preserved.

## Test plan
- Add tests next to the existing search tests for a hit inside a nested section, a hit outside any section, and several hits in one document, then run the search tests (`npm test` in `evals/vibe-plan-execution/fixtures/doc-search/`, which runs `node --test src/search/*.test.ts`).

## Implementation plan
1. Re-check the search code and tests.
2. Set each hit's `section` from the deepest enclosing outline node; the existing `enclosingSection` helper returns it. Add the tests listed in the test plan.
3. Run the search tests, run the post-implementation review, then close the checkpoint.

## Commit checkpoints
- Checkpoint scope: the `section` field on search hits and its tests. Required verification: search tests pass. Subject: `feat(search): attach enclosing section to hits`.
- This is the checkpoint boundary for this plan. It does not authorize push, release preparation, version bumps, amend, reset, stash, squash, destructive operations, external side effects, work-in-progress commits, failing or skipped verification commits, or scope-changing commits.

## Risks and unproven items
- None known for this checkpoint.

## Proceed condition
- Implementation may begin.
