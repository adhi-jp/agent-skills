# Profile Settings Implementation Plan

Requirements spec:
`evals/vibe-plan-review/fixtures/profile-review/profile-settings-requirements-spec.md`

## Goal

Add display-name and bio editing to the existing profile settings screen.

## Scope

- In scope: display-name field, bio field, inline validation, save, cancel, and
  focused tests.
- Out of scope: avatar upload, username changes, email preferences, account
  deletion, and audit log surfaces.

## Acceptance Criteria

- A valid display name and bio save successfully and remain visible after
  reload.
- Empty display names and display names over 60 characters show validation
  errors and do not submit.
- Bios over 160 characters show validation errors and do not submit.
- Cancel restores previously saved values without sending a network request.

## Implementation Tasks

- [ ] Inspect the existing profile settings form, endpoint contract, and test
  patterns.
- [ ] Add display-name and bio fields with trim and length validation.
- [ ] Wire save, cancel, loading, and inline error states without changing
  avatar or email preferences.
- [ ] Add focused tests for valid save, display-name validation, bio validation,
  and cancel.

## Verification

- Run `pnpm test -- profile-settings`.
