# Debug Workflow Reference

Use this loop before source edits or final repair claims. Resume and recurrence
checks live in `continuity-and-recurrence.md`; output and scope rules live in
`SKILL.md`.

## Workflow

1. **Establish the symptom and intended behavior.** Translate the user's report
   into observable behavior, affected contexts, unknowns, and closure criteria.
   Identify expected and observed behavior sources. Check relevant project rules
   and evidence; missing evidence is a limit, not permission to invent a cause.

2. **Map preservation obligations.** Identify behavior the repair could affect:
   output, state, persistence, external contracts, and runtime artifacts. Mark
   relevant dimensions `preserve`, `change intentionally`, `unknown`, or
   `not applicable`; unresolved current-scope unknowns block implementation.
   For non-trivial fixes use `state-space-matrix.md`, including ordering,
   overlap, identity, and cleanup when relevant. Keep tiny fixes compact.

3. **Test a cause before repairing it.** Keep facts, hypotheses, judgments,
   expected outcomes, and proof distinguishable. An unproven cause calls for a
   proof step, not implementation, unless the user explicitly accepts the
   residual risk. Prefer reproduction; otherwise use source trace, isolation,
   or an exact manual proof path. Name a fast observation that could disprove
   the preferred cause. If a previous hypothesis was refuted, name what would
   falsify its replacement before another patch.

   A mechanism measured in a fixture confirms the user's cause only if its
   constraints, initial state, environment, identity, and timing represent the
   reported path. Otherwise keep it `Unproven` until representative observation
   or explicit risk acceptance resolves the gap.

4. **Escalate proof, not speculation.** Start with bounded triage: nearest code,
   tests, existing logs, artifacts, and expected-behavior source. Read
   `source-routing.md` for unfamiliar external contracts or tool failures. If
   triage leaves multiple live-state hypotheses, sprawling static investigation,
   a contradicted approach, or another source-only guess, read
   `probe-escalation.md`. For repeated failures use `debug-ledger.md` before
   another implementation attempt. If diagnosis must pause, leave the resumable
   discriminator described in `continuity-and-recurrence.md`.

5. **Repair the smallest proven slice.** Follow local patterns and keep adjacent
   hardening out unless it shares the primary symptom's proven cause and proof
   path. Record any rule binding other units before dependent work, under the
   Durable Records gate in `SKILL.md`.

6. **Verify the repair and preserved behavior.** Run proof for every relevant
   preserved or intentionally changed dimension. Existing checks may cover
   several obligations when they run against the fixed code and observe each
   behavior through its own path and assertion; add tests only for remaining
   gaps. Reuse does not waive reproduction, regression, or recurrence proof.
   Read `verification-handoff.md` for runtime freshness, degraded checks, or a
   user retest. Choose a credible proof path now rather than offering a menu
   or promising steps later.

7. **Close.** Apply the recurrence check when needed, then the self-review,
   durable-record, and checkpoint gates in `SKILL.md`. Report proof and limits
   accurately; implementation alone is not closure.
