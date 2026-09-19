# Debug Ledger

Use this for the complex-diagnosis branch defined in `SKILL.md`. Keep compact
rows for current-scope symptoms and unresolved hypotheses or tool failures:

| Field | Content |
| --- | --- |
| Symptom | User's wording |
| Expected vs. observed | Behavior and sources; observation regime and any representativeness gap |
| Hypothesis / prior attempts | Suspected or proven cause; failed attempts and the proof they lacked |
| Proof path | Reproduction, source trace, artifact check, probe, or user retest; last verified checkpoint and next discriminator |
| Closure status | One of the statuses below |

For a returning symptom retain closed cause layers; for interrupted diagnosis
preserve controls and storage limits (`continuity-and-recurrence.md`).

## Status Meanings

- `fixed`: Proof observes the repaired behavior; runtime artifacts include the change.
- `not-reproduced`: Checked but absent in named dimensions; state residual risk.
- `deferred`: User or plan moved it out of scope; name the revisit trigger.
- `accepted-residual`: User accepted the remaining risk; name impact and reopening trigger.
- `blocked`: A necessary source, artifact, permission, environment, or proof is missing.

Deferred, accepted-residual, and blocked rows cite their durable findings entry
instead of repeating it (`durable-records.md`). Recording a blocker does not
resolve it.

## Failed-Attempt Rules

Before another fix, explain what changed, what proof was claimed, what still
failed, and why that proof missed the symptom. If unknown, gather proof first;
use a focused probe when live state is the missing evidence.

After two consecutive repairs under the same cause hypothesis leave the
acceptance discriminator materially unchanged, stop implementation. Revalidate
both metric discrimination and the observation regime. Resume only when new
proof changes the cause model, discriminator, or relevant state-space boundary.
