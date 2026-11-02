# Rover Elevation Save Plan

## Goal
- Store the rover's elevation level in save slots in one verified checkpoint.

## Verified facts and sources
| Claim | Evidence | Source | Impact |
| --- | --- | --- | --- |
| `encodeSave` writes `{ profile, pos, hp }` with `pos` as `[x, y]`, and `decodeSave` reads it into `rover: { x, y }`. | Local investigation | `evals/vibe-plan-execution/fixtures/rover-saves/src/saves.ts` | Re-check before editing. |
| `src/saves.test.ts` covers the encoded `pos` and the save round trip. | Local investigation | `evals/vibe-plan-execution/fixtures/rover-saves/src/saves.test.ts` | Re-check before relying on coverage. |
| `src/profiles.ts` encodes and decodes `profiles.json`; this slice does not use it. | Local investigation | `evals/vibe-plan-execution/fixtures/rover-saves/src/profiles.ts` | Leave unchanged. |
| The fixture's tests run with Node's built-in test runner; no install is needed. | Local investigation | `evals/vibe-plan-execution/fixtures/rover-saves/package.json` | Do not add a test framework dependency. |

## Requirements
- In scope: the rover position gains `level`; a save's `pos` becomes `{ x, y, level }`, which `encodeSave` writes and `decodeSave` returns as `rover: { x, y, level }`.
- Non-goals: profile changes, new dependencies, gameplay changes.

## Acceptance criteria
- `encodeSave` writes `pos` as `{ x, y, level }`.
- `decodeSave(encodeSave(state))` returns `state`, including `rover.level`.
- Profile encoding and decoding are unchanged.

## Behavior contract inventory
Current contract, before the change.

1. **Immediate observable behavior**
   - `encodeSave(state)` returns JSON text `{ profile, pos: [x, y], hp }`. `Local investigation`: `evals/vibe-plan-execution/fixtures/rover-saves/src/saves.ts`.
   - `decodeSave(text)` returns `{ profile, rover: { x, y }, hp }`, reading `rover` from `pos`. `Local investigation`: same file.
   - `encodeProfiles` writes `{ profiles: [{ name, color }] }`, and `decodeProfiles` returns that list. `Local investigation`: `evals/vibe-plan-execution/fixtures/rover-saves/src/profiles.ts`.
   - `decodeSave` does no validation of its own; malformed JSON text throws from `JSON.parse`. `Local investigation`: `src/saves.ts`.
2. **Internal state transition**
   - All four functions are pure: they mutate no argument, keep no module state, and emit no events or logs. `Local investigation`: `src/saves.ts`, `src/profiles.ts`.
3. **Persistent / lifecycle behavior**
   - The text `encodeSave` returns is a save slot's stored content, `<data dir>/saves/<slot>.json`; the module does no file I/O itself. `Local investigation`: `src/saves.ts` header comment.
   - The text `encodeProfiles` returns is the stored `<data dir>/profiles.json`. `Local investigation`: `src/profiles.ts` header comment.

## Behavioral equivalence analysis
In scope for change, from the Requirements: the `pos` shape that `encodeSave` writes and `decodeSave` reads, and `rover` gaining `level`.

| Dimension | Classification | Basis |
| --- | --- | --- |
| Immediate observable result, and persistence and serialization: the `pos` shape and `rover.level` | `Changed (in scope)` | Requirements (in scope); acceptance criteria 1-2; the Test plan's non-zero-`level` round-trip test. |
| Immediate observable result: save `profile` and `hp` fields | `must preserve` → `Equivalent` | Inventory bucket 1; the change does not touch them; covered by the round-trip test. |
| Ownership and reference semantics | `must preserve` → `Equivalent` | Inventory bucket 2: both functions build fresh values and share nothing with their argument; the change keeps that. |
| Internal state changes | `Not applicable` | Inventory bucket 2: pure functions with no source object, container, or context to consume or mark (`Local investigation`). |
| Side effects and events | `Not applicable` | Inventory bucket 2: no events, notifications, logs, or I/O (`Local investigation`). |
| Persistence and serialization: save round trip | `must preserve` → `Equivalent` | Inventory bucket 3; `decodeSave(encodeSave(state))` returns `state`, now including `level` (acceptance criterion 2). |
| Lifecycle and reload behavior | `Not applicable` | No module holds state, caches, or handles across calls (`Local investigation`). |
| Error and edge cases: malformed JSON text | `must preserve` → `Equivalent` | Inventory bucket 1; the change does not alter `JSON.parse` handling. |
| Resource cleanup and disposal | `Not applicable` | No resources or handles are acquired (`Local investigation`). |
| External contracts and guarantees | `Not applicable` | No wire, network, concurrency, or authorization surface; the stored save shape is classified in the first row (`Local investigation`). |
| Profiles: encoding, decoding, and `profiles.json` content, all dimensions | `must preserve` → `Equivalent` | Inventory buckets 1 and 3; Non-goals exclude profile changes; `src/profiles.ts` and `src/profiles.test.ts` are not edited; acceptance criterion 3. |

## Failure-pattern checks
- A.4 Persisted config and migrations: applies, because the stored save shape changes. Answer the consumer question for save files already written from the publication state before editing the save code.

## Test plan
- Add a test that `encodeSave` writes `pos` as `{ x, y, level }`.
- Add a test that a save with a non-zero `level` round-trips, then run the tests (`npm test` in `evals/vibe-plan-execution/fixtures/rover-saves/`, which runs `node --test src/*.test.ts`).

## Implementation plan
1. Re-check the save code and tests.
2. Add `level` to `Rover`, and write and read `pos` as `{ x, y, level }`. Add the tests listed in the test plan.
3. Run the tests, run the post-implementation review, then close the checkpoint.

## Commit checkpoints
- Checkpoint scope: the save `pos` shape and its tests. Required verification: the tests pass. Subject: `feat(saves): store the rover's elevation level`.
- This is the checkpoint boundary for this plan. It does not authorize push, release preparation, version bumps, amend, reset, stash, squash, destructive operations, external side effects, work-in-progress commits, failing or skipped verification commits, or scope-changing commits.

## Risks and unproven items
- None known for this checkpoint.

## Proceed condition
- Implementation may begin.
