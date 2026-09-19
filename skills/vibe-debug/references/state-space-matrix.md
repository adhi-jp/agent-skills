# State-Space Matrix

Convert the reported example into relevant dimensions; it is evidence of where
the bug appeared, not the repair's full boundary. Name the abstract contract
before domain cases. Domain tools serve that contract, not every debug task.

## Common Dimensions

Choose only dimensions the repair could affect:

| Dimension | Example boundaries |
| --- | --- |
| Representation/encoding | Raw, parsed, normalized, URL/serialized/stored/displayed; commas, spaces, Unicode, escaping |
| Environment | Local/staging/production, host/origin, platform, tenant, clock, feature flag |
| Permission/trust | Role, token scope, caller identity, cross-origin boundary |
| Direction/route | Forward/reverse, source/target, import/export, primary/fallback |
| Lifecycle/error | Load, save, retry, cancel, timeout, partial write, rollback, recovery |
| Runtime artifact | Cache, bundle, binary, migration, package, running process |

For dynamic or concurrent bugs also consider sequence and ordering, overlapping
work, per-entity identity and stale references, reset/cancel, and final cleanup.
These expose failures hidden by static screenshots or single happy-path tests.

## Matrix Output

For non-trivial fixes, use compact rows:

| Abstract dimension | Cases in scope | Preserve/change | Proof |
| --- | --- | --- | --- |
| Representation | Raw ID, encoded label, persisted value | Preserve round trip | Save/reopen test |
| Lifecycle | First save, retry, cancel | Change retry only | Regression and cancel check |

Rows are proof obligations, not separate new tests. Apply the proof-reuse rule
in `debug-workflow.md`; tiny fixes need no exhaustive matrix.
