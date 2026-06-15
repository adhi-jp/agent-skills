# Report Renaming Implementation Plan

## Goal

Rename the reports navigation label while preserving existing report URLs.

## Implementation Tasks

- [ ] Rename the navigation label from "Reports" to "Insights".
- [ ] Keep existing report URLs working through the compatibility shim.
- [ ] Remove the old "reports beta" sidebar entry.
- [ ] Review dashboard copy that still says "Reports".

## Verification

- Run `pnpm test -- reports-navigation`.
