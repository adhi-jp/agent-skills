# Change Recovery Checklist

Use this file when the request replaces, restores, rolls back, or rewrites
existing behavior. Recover or replace behavior without discarding evidence that
already exists in repository history.

## Required Checks

1. Identify the target behavior: what is broken, missing, or undesired now, and
   what should exist after the change.
2. Find the last known-good implementation in `git log`, tags, release notes,
   related tests, and blame history; prefer the latest commit linked to
   known-good behavior.
3. Prove the historical state was good — passing tests, release tags, user
   confirmation, or issue history. Without that proof it is `Unproven`.
4. Read the historical code, tests, config, migrations, and assets directly and
   capture what differed and why it mattered.
5. Build the two-column (historical and current) behavior contract inventory
   from `behavioral-equivalence-analysis.md`, compare the rows side by side,
   separate accidental regressions from intentional product changes, and note
   surrounding changes that make direct restoration unsafe.
6. When the restoration touches persisted config or schema, lifecycle or
   initialization order, build or release packaging, or a trust boundary, apply
   the matching `failure-pattern-checklist.md` sections.
7. Plan from verified evidence only: reuse proven behavior, and turn an
   unverifiable or no-longer-fitting historical implementation into a proof
   task. Then classify every equivalence dimension against the inventory,
   whether or not the new implementation uses a different API.

## If Git History Is Incomplete

A missing clean commit does not make recovery impossible. Check release tags,
packaged artifacts, or deployment snapshots; historical tests; checked-in
screenshots, fixtures, contracts, or sample payloads; ADRs, specs, support docs,
or runbooks; and user-provided evidence of what "correct" meant. If one proves
the old behavior, continue and label the evidence honestly. If none does, do not
fake a restoration plan: reframe the work as forensic discovery or net-new
behavior design and say that it cannot yet be treated as a verified restoration.

## Stop Conditions

Report the blocker and request the missing proof instead of planning the
replacement as understood when:

- no known-good commit can be found;
- a candidate historical commit cannot be shown to have been correct;
- the historical implementation depends on removed infrastructure that has not
  been revalidated; or
- the request conflicts with the known-good behavior and the new desired
  behavior is still ambiguous.

For brand-new projects or repository migrations with no meaningful historical
state, skip restoration framing and plan new behavior after saying no verified
prior implementation exists.
