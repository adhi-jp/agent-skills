# Team Report Export Requirements Spec

## Goal

Let team admins export their team's monthly activity report as a PDF.

## Requirements

- Only team admins can trigger the export for their own team.
- The export uses the report month currently selected on screen.
- Exported values must match the on-screen report for that month at export
  time.
- The export action is disabled while report data is still loading.

## Acceptance Criteria

- A team admin can download a PDF of the selected month's report.
- Members without the admin role never see or reach the export action.
- The PDF values match the on-screen values for the same month.
- No export starts while the report is loading.

## Out Of Scope

- Report content or metric changes.
- Scheduled or emailed report delivery.
- Cross-team or organization-wide exports.
