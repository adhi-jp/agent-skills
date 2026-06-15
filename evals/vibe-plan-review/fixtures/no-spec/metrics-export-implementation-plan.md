# Metrics Export Implementation Plan

## Goal

Add CSV export for the currently visible usage metrics table.

## Scope

- In scope: export visible rows, preserve current metric labels, and include a
  header row.
- Out of scope: new metrics, scheduled exports, email delivery, and dashboard
  redesign.

## Acceptance Criteria

- The exported CSV has one row per visible metric.
- CSV headers match the visible table labels.
- Empty metric tables export a header-only CSV.

## Implementation Tasks

- [ ] Inspect the metrics table data model and existing export helpers.
- [ ] Add CSV serialization for visible metrics only.
- [ ] Wire the export button and loading state.
- [ ] Add tests for headers, row count, and empty table behavior.

## Verification

- Run `pnpm test -- metrics-export`.
