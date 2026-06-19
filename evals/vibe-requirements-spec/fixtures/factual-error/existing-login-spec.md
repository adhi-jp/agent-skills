# Login Requirements Spec

## Spec metadata
- Current spec path: specs/login-spec.md
- Last updated: 2026-06-16
- Requirement mode: freestyle

## User goal

Allow existing users to sign in with email and password.

## Evidence and constraints

### Local evidence
- specs/login-spec.md is the current requirements spec path for this fixture.

### External evidence
- None provided.

### Unverified facts
- Existing production authentication behavior has not been inspected.

## Current requirements

### Confirmed requirements
- Signed-in access starts with email and password login.
- Password reset remains part of the first useful authentication slice.

### Proposed defaults
- Keep session duration and remember-me behavior unchanged unless later evidence
  shows a required change.

### Ideas or options
- SSO login can be considered after the first password-login slice is accepted.

### Decisions needed

#### Blocking decisions
- None for the first password-login slice.

#### Can default
- Keep current password reset behavior unchanged.

#### Later decisions
- Decide whether SSO login should be added in a later authentication slice.

### Assumptions
- Existing users already have email/password credentials.

### Out of scope
- SSO login is out of scope for the first useful slice.
- Removing password login is out of scope.

## Acceptance criteria
- Existing users can sign in with email and password.
- Password reset remains available.
- The first authentication slice does not require SSO login.

## Open risks and unknowns
- Existing authentication provider capabilities are unverified.
