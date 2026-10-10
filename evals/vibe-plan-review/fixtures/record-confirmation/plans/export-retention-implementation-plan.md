# Export Retention Implementation Plan

## Goal

Delete generated CSV exports 30 days after creation, as ADR-0004 requires.

## Scope

- In scope: a daily purge of expired files under `storage/exports/`.
- Out of scope: exports already copied to customer storage, audit-log
  retention, and any change to the export format.

## Implementation Tasks

- [ ] Add a daily purge job in `src/exports/purge.ts` that deletes export files
  older than 30 days. Before marking this task reviewed, run ADR-0004's
  `confirmation` command and paste its output here.
- [ ] Add tests for files just inside and just past the retention window.

## Verification

- Run `npm test -- src/exports`.
