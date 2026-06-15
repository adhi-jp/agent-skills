# Billing Recipients Requirements Spec

## Goal

Allow account owners to edit invoice email recipients for future billing email
delivery.

## Requirements

- Account owners can add and remove invoice email recipients.
- Changes affect future billing emails and reminders only after save.
- Removed recipients receive no future billing emails after the effective
  window.
- The first slice does not add audit-log storage, audit-log tables, admin audit
  UI, or searchable audit history.
- Existing billing permissions remain unchanged.

## Acceptance Criteria

- Added recipients receive future invoice emails.
- Removed recipients are excluded from future invoice emails.
- Unauthorized users cannot change invoice recipients.
- No audit-log storage or audit-log UI is introduced in this slice.

## Out Of Scope

- Audit-log storage.
- Admin audit UI.
- Searchable billing history.
