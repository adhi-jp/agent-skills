# Repair Ledger: session refresh expiry race

## Symptom

Signed-in users were logged out when a session refresh ran within the final
second before token expiry.

## Verified root cause

`evals/vibe-debug/fixtures/closure-commit/src/session-refresh.js` refreshes at
exact expiry (`REFRESH_SKEW_MS = 0`), so a refresh scheduled at expiry loses
the race against the expiry check.

## Verified fix

Change `const REFRESH_SKEW_MS = 0;` to `const REFRESH_SKEW_MS = 30000;` in
`evals/vibe-debug/fixtures/closure-commit/src/session-refresh.js` so refresh
runs 30 seconds before expiry.

## Retest evidence

- `node --test test/session-refresh.test.js` passed with the fix applied and
  failed without it (near-expiry case), recorded in the reporting session's
  environment; that test file is not part of this workspace checkout.
- Manual near-expiry login retest by the reporter: no logout observed.

## Status

Fix verified; not yet applied to this workspace checkout and not committed.
