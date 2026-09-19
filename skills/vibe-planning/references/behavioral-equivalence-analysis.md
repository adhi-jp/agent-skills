# Behavioral Equivalence Analysis

Use this file when a change touches existing behavior, whether it is meant to
preserve, modify, or replace that behavior: refactors, migrations, replacements,
internal implementation changes, and explicit behavior changes. A user-requested
change can still affect other dimensions, and "the new code uses the same API",
"the user asked for this change", or "the immediate output looks the same" are
not reasons to skip it.

## Behavior Contract Inventory

Write the current contract down before classifying any dimension; otherwise
equivalence reasoning anchors on memory. Populate three separately labeled
buckets, compactly in a `light` plan but never merged into one paragraph:

1. **Immediate observable behavior** — inputs, outputs, return values, visible
   state changes, user-facing effects, and documented contracts such as API
   response shape, command output, UI rendering, and error messages.
2. **Internal state transition** — what the operation does to the source object,
   container, cache, or context: mutation, ownership transfer, observer
   notifications, intermediate flags, reentrancy, and ordering against
   neighboring state changes that downstream consumers see.
3. **Persistent / lifecycle behavior** — what survives persistence round-trips,
   restart, reload, cache invalidation, garbage collection, or migration:
   on-disk schema, serialized envelope, identity keys, version markers, cleanup
   obligations, reload reconstruction, and packaging behavior when the change
   crosses a build artifact boundary.

Label every entry `Primary source`, `Local investigation`, or `Unproven`; an
`Unproven` entry is triaged like any other `Unproven` item. For replacement,
restoration, rollback, or rewrite, give each bucket two columns — historical or
known-good, and current — and treat a historical column that cannot be sourced
as a recovery blocker (`change-recovery-checklist.md`).

The inventory appears in the plan before the equivalence analysis, and the
analysis cites its rows. Omit it only when source evidence shows the slice adds
a new code path with no existing-behavior intersection, and say so.

## Scope Separation

Every dimension is `must preserve` by default. Mark a dimension `in scope for
change` only with a clear, traceable basis in the user's stated requirements;
"it seems reasonable to change this" is not one.

## Dimension Classification

Classify every dimension with exactly one of:

- **`Equivalent`** — verified by `Primary source` or `Local investigation`
  against the inventory. A dimension resting on an `Unproven` inventory entry is
  `Unknown`, not `Equivalent`.
- **`Changed (in scope)`** — only for an `in scope for change` dimension with
  the user's explicit basis, documented changed success criteria, and a test for
  the new behavior; missing any of these makes it `Unknown`.
- **`Not applicable`** — the dimension does not apply to the operation; give a
  short rationale with an evidence class.
- **`Unknown`** — not yet verified; treat it as `Unproven` and resolve it before
  implementation.

A dimension the change clearly affects needs an inventory entry; a missing entry
is not a free pass.

When a `must preserve` dimension is not equivalent, stop and report it to the
user; do not self-classify the difference as intentional or acceptable. If the
user approves making it `in scope for change`, classify it `Changed (in scope)`
with its success criteria and test, and escalate the plan to `strict`.

## Comparison Dimensions

For each changed operation, compare old and new implementations across:

1. **Immediate observable result** — output, return value, or visible state
   change.
2. **Ownership and reference semantics** — move, copy, alias, or create; whether
   ownership transfers.
3. **Internal state changes** — whether the source object, container, or context
   is consumed, marked, hidden, or left unchanged.
4. **Side effects and events** — events, notifications, logs, counters, and
   observers.
5. **Persistence and serialization** — whether a save/reload round-trip
   preserves the result without dangling references, orphans, or duplicates.
6. **Lifecycle and reload behavior** — restart, reconnect, context reload, cache
   invalidation, view reconstruction, and garbage collection.
7. **Error and edge cases** — invalid input, missing prerequisites, concurrent
   access, partial failure, and resource exhaustion.
8. **Resource cleanup and disposal** — cleanup obligations, leaked handles, and
   orphaned state.
9. **External contracts and guarantees** — wire contracts and event schemas,
   ordering, input validation, authorization, idempotency, atomicity,
   consistency, rate limiting, and retry semantics.

Classify every dimension, using `Not applicable` with a rationale rather than
skipping one.

## Surface Equivalence Warning

A similar API name, parameter shape, or immediate output is a risk signal, not
evidence of equivalence. Before classifying a dimension `Equivalent`, read the
implementation or documentation of both old and new code and name at least one
plausible way they could differ; if none exists, state that as a verified claim
with evidence.

## Output Requirement

The inventory and the equivalence analysis appear in the plan output; internal
consideration is not enough. Once performed, the analysis stays in the plan
through later depth changes, scope reclassification, or other updates.
