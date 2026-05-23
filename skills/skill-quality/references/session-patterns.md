# Session-Derived Skill Improvement Patterns

This reference summarizes patterns observed from local Codex session history,
plans, changelog entries, eval definitions, and generated benchmark artifacts in
this repository. Use it for rationale, not as an additional checklist to paste
into skill outputs.

## Improvements That Helped

- Narrow contract changes worked better than broad rewrites. Examples include
  adding plan-only boundaries, per-step skill routing, corrective self-review,
  current-slice blocker triage, and explicit artifact freshness rules.
- Eval hardening was most effective when assertions named the observable
  failure: exact fixture facts, proof paths, no fake baselines, no unavailable
  skill leakage, no universal checklist output, and no weak proof substitute.
- Expected-output summaries could weaken discrimination when the runner showed
  them to executors; summaries needed evidence shape, not the target decision,
  and answer-specific details belonged in grader-only assertions.
- Incorrect eval expectations were fixed in the eval instead of teaching the
  skill to invent unsupported product facts.
- A 100 percent pass rate did not end review when grader notes exposed
  false-positive risk; hardening assertions and rerunning was more reliable.
- Evidence labels were useful only when they applied to the current proposal's
  claims, not just to a future extraction or grading format.
- Token and time deltas were cost signals, not standalone proof of improvement
  or regression without transcript evidence, run data, or a predefined budget.
- High-risk behavior stayed understandable when detailed controls moved into
  references and `SKILL.md` kept only trigger, routing, and stop-gate rules.
- Session-history examples were useful only after being mapped to abstract
  dimensions such as `data contract`, `artifact freshness`, `benchmark
  completeness`, `current-slice blocker`, `tool capability`, or `local anchor`.
- Doc-only guarantees repeatedly proved weak. Durable fixes moved important
  rules into structured outputs, script behavior, receipts, pre-edit gates, or
  concrete eval assertions.
- Shared eval infrastructure improved when state moved from harness memory into
  files: agent-scoped workspaces, run manifests, grader prompts, parent-captured
  metrics, exact grading assertion validation, static reports, and compatible
  baseline fingerprints.
- Consolidation helped when it preserved the high-value contracts from old
  skills while retiring duplicate packages, updating eval ownership, and moving
  heavy details into references.

## Changes That Risked Degrading Skills

- Copying an older skill wholesale increased token cost and reintroduced stale
  workflow assumptions.
- Broad common assertions broke exact-format, verbatim, or localized cases that
  needed different behavior.
- Prose compression or polish degraded skills when it changed modality,
  explicit absence statuses, local anchors, or the scope of an obligation.
- Plans and skills degraded when they treated one fixture, one UI, or one
  domain as the whole skill boundary.
- Review-driven changes grew too large when every valid review note became a
  new requirement instead of being classified against the current goal.
- Eval runs became misleading when missing baselines were rendered as zero,
  output characters were treated like model tokens, executor prompts contained
  grading assertions, or static review flows started server processes by
  default.
- Skill descriptions caused under-reading when they summarized workflow steps
  instead of only naming trigger conditions.
- Eval automation created a data-boundary risk when private skill/eval content
  would be sent to an external hosted agent without explicit authorization.
- Agents overclaimed improvement when a run passed without a meaningful
  baseline difference, when grader text was ambiguous, or when only a subset of
  newly affected evals ran.

## Practical Synthesis

For every skill change, preserve this sequence:

1. Identify the concrete failed behavior or ambiguous eval result.
2. Translate it into a reusable contract dimension.
3. Edit the smallest artifact set that owns that contract.
4. Add or tighten discriminating eval expectations.
5. Run or prepare the shared eval workflow honestly.
6. Report proof, gaps, and generated artifacts without inflating claims.
