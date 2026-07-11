# Team Report Export Implementation Plan

## Goal

Let team admins export their team's monthly activity report as a PDF.

## Scope

- In scope: a PDF export action on the monthly team report screen for team
  admins.
- Out of scope: report content changes, scheduled report delivery, and
  non-admin export access.

## Acceptance Criteria

- Team admins can download the currently displayed monthly report as a PDF.
- Non-admin members do not see the export action.
- The PDF matches the on-screen report values for the selected month.

## Implementation Tasks

- [ ] Inspect the monthly report data loader and the existing PDF helper.
- [ ] Add the admin-only export action to the monthly report screen.
- [ ] Render the selected month's report data into the PDF layout.
- [ ] Add tests for admin visibility, non-admin absence, and PDF content.

## Verification

- Run `pnpm test -- team-report-export`.
