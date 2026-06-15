# Billing Recipients Implementation Plan

Requirements spec:
`evals/vibe-plan-review/fixtures/conflict/billing-recipients-requirements-spec.md`

## Goal

Let account owners manage invoice email recipients.

## Implementation Tasks

- [ ] Inspect the billing recipient form and permission checks.
- [ ] Add recipient add/remove persistence and validation.
- [ ] Add an `invoice_recipient_audit_events` table and write an audit event for
  every recipient change.
- [ ] Build an admin audit UI with filters by recipient and billing account.
- [ ] Add tests for recipient delivery-window behavior and audit history.

## Verification

- Run billing recipient and admin audit tests.
