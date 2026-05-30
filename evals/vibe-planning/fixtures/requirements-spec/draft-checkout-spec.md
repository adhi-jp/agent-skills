# Checkout Retry Requirements Spec

## Approval state
- Status: Draft
- Current spec path: specs/checkout-retry-spec.md
- Last updated: 2026-05-24
- Approval note: Awaiting product decision on retry count and duplicate-charge behavior.

## Current requirements

### Confirmed requirements
- Users should be able to retry a failed card payment from checkout.

### Proposed defaults
- Show the existing failure message with a retry action.

### Decisions needed
- Decide whether a retry creates a fresh payment intent or reuses the failed one.
- Decide the maximum retry count.

### Assumptions
- The current payment provider supports safe retry semantics.

### Out of scope
- New saved-card management.

## Acceptance criteria
- A failed payment can be retried from checkout after approval of retry semantics.

## Open risks and unknowns
- Duplicate-charge prevention is not approved.
- Provider retry semantics are unverified.

## Revision notes
- Draft created from initial checkout-retry idea.

