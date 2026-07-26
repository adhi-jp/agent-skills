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
- Improvement claims held up only after a closing rerun on a clean, complete
  run with per-eval isolation, complete metrics, and both configs. Batched
  executor passes that collapsed per-eval metrics, and runs where the runner was
  absent, were treated as contaminated or incomplete rather than proof, and the
  effect stayed labeled until a clean rerun existed.
- Excluded or unscored timeout cells made otherwise strong headline deltas
  partial. In a plan-artifact eval pass, asymmetric `with_skill` executor
  timeouts were treated as unmeasured runtime-cost risk rather than harmless
  infrastructure or a reason for more skill prose; a separate scored failure in
  the same run was the actual contract-edit target.
- Evidence labels were useful only when they applied to the current proposal's
  claims, not just to a future extraction or grading format.
- Token and time deltas were cost signals, not standalone proof of improvement
  or regression without transcript evidence, run data, or a predefined budget.
- Some apparent skill failures were measurement-boundary defects: the intended
  behavior happened, but the proof lived outside the recorded output set. Adding
  recorded host, runner, or equivalent non-response evidence changed the grade
  without proving that skill prose caused the improvement.
- Relayed host-agent eval summaries were safest when treated as pointers into
  runner artifacts. Sessions that verified `benchmark.json`, manifests, run
  statuses, `grading.json`, and recorded outputs before accepting a Claude Code
  summary avoided turning prose-only reports into proof.
- High-risk behavior stayed understandable when detailed controls moved into
  references and `SKILL.md` kept only trigger, routing, and stop-gate rules.
- Session-history examples were useful only after being mapped to abstract
  dimensions such as `data contract`, `artifact freshness`, `benchmark
  completeness`, `current-slice blocker`, `tool capability`, or `local anchor`.
- The abstract dimension still needed an artifact-placement decision: narrow
  pressure cases stayed in evals or notes, heavier reusable guidance stayed in
  applicability-scoped references, and only broadly applicable obligations
  belonged in `SKILL.md`.
- Doc-only guarantees repeatedly proved weak. Durable fixes moved important
  rules into structured outputs, script behavior, receipts, pre-edit gates, or
  concrete eval assertions.
- Shared eval infrastructure improved when state moved from harness memory into
  files: agent-scoped workspaces, run manifests, grader prompts, parent-captured
  metrics, exact grading assertion validation, and static reports.
- A June 2026 cross-suite compaction reduced 187 external eval cases to 145 by
  inventorying cases first, delegating bounded read-only ledger passes, and
  deleting or merging only where a retained case or assertion carried the same
  abstract contract. Suites stopped above their numeric targets when the next
  cut would lose a distinct boundary or require an unnatural combined prompt.
- Representative-suite compaction worked when it preserved contract families,
  not merely case counts. The writing suite retained exact-format, locale,
  changelog, durable-proof, commit-message, and workflow-boundary pressure while
  reducing 18 cases to 12.
- Post-compaction review caught coverage that the initial case deletion missed.
  The skill-quality suite kept 12 cases, but folded trigger-only metadata
  pressure and history-extraction/package-coupling pressure into retained cases
  after a coverage-continuity audit, rather than restoring two whole cases.
- Removing a common assertion improved suite quality when the assertion was a
  scenario-specific fallback gate that became vacuous on unrelated cases. The
  guarded behavior remained in owning per-eval expectations, and re-grading
  showed the removed assertion had added scoring noise rather than useful
  discrimination.
- Consolidation helped when it preserved the high-value contracts from old
  skills while retiring duplicate packages, updating eval ownership, and moving
  heavy details into references.
- Security diagnostics became actionable when the warning was translated into
  a source-boundary-sink predicate instead of another reminder sentence. A
  third-party-content warning required preventing original free-form responses
  from entering the coordinator context, while preserving review usefulness
  through bounded structural locations and independent local verification.
- Analyzer prose was useful as primary evidence of what was reported, but not
  as proof of the alleged root cause. Current source inspection still had to
  confirm the path before a durable skill contract was changed.
- Credential-handling corrections held when exactness rules gained an explicit
  safety precedence and every output or persistence sink was audited. Redacting
  chat alone was insufficient when temporary review state, reflected files,
  commit messages, or tool arguments could still reproduce the same literal.
- Contract-closure searches caught sibling artifacts that still taught the old
  unsafe path after the main skill text changed. Eval fixtures and prompts were
  part of the current behavior contract, while old release notes remained
  historical evidence rather than text to rewrite.

## Changes That Risked Degrading Skills

- Copying an older skill wholesale increased token cost and reintroduced stale
  workflow assumptions.
- Broad common assertions broke exact-format, verbatim, or localized cases that
  needed different behavior.
- Prose compression or polish degraded skills when it changed modality,
  explicit absence statuses, local anchors, or the scope of an obligation.
- Plans and skills degraded when they treated one fixture, one UI, or one
  domain as the whole skill boundary.
- Plans and skills also degraded when one sampled case became a named pattern
  section, domain branch, or fixture-derived checklist in `SKILL.md` after only
  a single abstraction step.
- Review-driven changes grew too large when every valid review note became a
  new requirement instead of being classified against the current goal.
- Eval runs became misleading when missing baselines were rendered as zero,
  output characters were treated like model tokens, executor prompts contained
  grading assertions, or static review flows started server processes by
  default.
- Repeated wording-only contract tightening degraded diagnosis when a stable
  failure was really missing recorded proof, prompt-delivery evidence, grader
  input alignment, assertion-scope clarity, or run-variance analysis.
- In a commit-execution skill convergence session, residual failures that moved
  across evals after local wording patches became clearer when treated as one
  shared invalid-placeholder mechanism rather than separate per-eval fixes. The
  pattern applies when the same user-copyable invalid template, future-output
  placeholder, or equivalent mechanism reappears on different eval surfaces; it
  does not make multi-run convergence mandatory for every skill-quality change.
- Skill descriptions caused under-reading when they summarized workflow steps
  instead of only naming trigger conditions.
- Eval automation created a data-boundary risk when private skill/eval content
  would be sent to an external hosted agent without explicit authorization.
- Agents overclaimed improvement when a run passed without a meaningful
  baseline difference, when grader text was ambiguous, or when only a subset of
  newly affected evals ran.
- Timeout or excluded-cell summaries degraded analysis when the aggregate
  pass-rate delta was called clean even though targeted behavior was unscored,
  especially when only `with_skill` timed out on complex orchestration cases.
- Host-continuation stubs and unresolved async placeholders degraded eval
  analysis when agents treated the cell as if it could be removed from the
  official aggregate. The safer classification was prompt/invocation or
  output-set completeness, followed by a caveated official aggregate or a
  recording/prompt fix.
- Self-authored contract deltas and assertions degraded when they copied a
  grader assertion's wording or a literal prompt phrase verbatim. The leakage
  lens had to cover the change owner's own assertions, not only delegated eval
  work, so the rule named an abstract dimension and kept the concrete phrase as
  an example.
- Loosening or deleting assertions to clear a failure raised the headline pass
  rate while lowering discrimination. Durable practice recorded the
  discrimination lost with a compensating assertion or an accepted risk, and a
  deletion or merge of an eval case triggered a check that the contracts it
  guarded were still covered elsewhere.
- Static JSON or runner validation after compaction proved structure and fixture
  integrity, not preserved skill effectiveness. Provider comparisons were
  required before effectiveness claims, and a post-compaction run with a
  candidate-below-baseline cell stayed caveated instead of being relabeled
  clean.
- Numeric targets degraded judgment when treated as quotas. The useful stopping
  rule was whether the next deletion lost a unique state, proof boundary,
  language or exact-output class, or required a synthetic meta-prompt that no
  real user would give.
- Prompt-side inert labels and downstream redaction degraded security triage
  when they were counted as closure even though the reported third-party bytes
  still crossed into the same model context.
- Generic preserve-exactly rules degraded credential safety when agents applied
  them to secret-like literals without a higher-priority redaction and
  fail-closed reflection rule.
- Static validation and synthetic safety fixtures were overread when they were
  reported as proof that an external analyzer cleared or that a host enforced
  isolation at runtime.
- An alternative security check could support the underlying safety property,
  but it could not prove that a named scanner warning disappeared without a
  rerun of that scanner.

## Practical Synthesis

For every skill change, preserve this sequence:

1. Identify the concrete failed behavior or ambiguous eval result.
2. Classify the failure surface: skill contract, eval assertion, measurement or
   recording, prompt or invocation, grader boundary, or variance.
3. For safety diagnostics, derive the prohibited source-boundary-sink predicate
   and the layer that can enforce it.
4. Translate any real skill or eval gap into a reusable contract dimension.
5. Decide whether that dimension belongs in `SKILL.md`, a reference, an eval, or
   notes.
6. Edit the smallest artifact set that owns that contract.
7. Add, tighten, or compact discriminating eval expectations. For compaction,
   reconcile every old case to retained coverage or an accepted risk first.
8. Run a closure search for stale current-contract text, then use the shared
   eval workflow honestly or label unrun proof as absent.
9. Report proof, gaps, and generated artifacts without inflating claims.
