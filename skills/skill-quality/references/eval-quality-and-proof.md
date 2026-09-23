# Eval Quality and Proof

Read this reference before changing eval prompts, assertions, fixtures, or suite coverage, and before interpreting a benchmark or reporting a rerun-dependent quality claim.

## Suite Design

A suite should be the smallest set of cases that guards each core contract of
the skill with discriminating pressure; its size follows those contracts, not
a numeric quota. Every case costs configs x runs x (executor + grader), and
`with_skill` cost grows with the skill's own text; the number of assertions in
a case barely matters.

- Combine contracts into one case when a single coherent, realistic prompt
  exercises them, such as several flagged cells from one benchmark or several
  pending proposals for one package. Do not build an artificial matrix of
  unrelated scenarios.
- Adding a case requires naming the contract no retained case covers and why
  extending an existing case's prompt cannot carry it; prefer extending a case
  to adding one.
- Keep each assertion atomic: one gradeable predicate. Many atomic assertions
  in one case are fine; a conjunctive assertion fails more often as its
  conjuncts grow.
- Decide with with/without evidence. An assertion both configurations pass
  (about 90% or more over several runs) is non-discriminating; it dilutes the
  with/without delta and adds grading noise, so delete it unless it guards a
  harm the skill's own instructions could induce, is the only remaining guard
  for a known incident, or guards a destructive or consent boundary. Delete a
  case when a retained case carries its contract, or when all its assertions
  are non-discriminating and none meets those exceptions.
- Include negative pressure for the degeneration that motivated a change, and
  positive pressure that the legitimate behavior still happens.
- A `with_skill`/`without_skill` delta measures the skill's presence, not an
  edit's effect, and a predicate the unchanged skill text already passes
  cannot show that effect. When runs are authorized, measure a new targeted
  case on the unchanged text (before the edit or from a base checkout) in the
  scope where the failure occurred; trim inputs around the task, not that
  scope.
- Do not loosen or delete an assertion to clear a failure without recording
  the discrimination lost and a compensating assertion or `Accepted risk`. If
  an expectation encodes an unsupported product fact, fix the eval, not the
  skill.
- When deleting or merging cases, record for each old case where its contract
  now lives, or the accepted loss, and update the suite `purpose`,
  `coverage_notes`, and scoring notes. Static validation proves structure
  only; claim preserved effectiveness only after an authorized comparative
  run.

## Assertion Design

- A common assertion must hold for every case it governs, including
  activation-only, exact-format, localized, verbatim, narrow-boundary, and
  no-change cases; otherwise keep the check per-eval. A conditional common
  assertion states its observable applicability predicate and what passes
  when the triggering surface is absent; if applicability cannot be observed
  from the delivered prompt and recorded output, move it per-eval.
- Classify each case's delivery mode (executing, response-only,
  artifact-writing, closure-only, or blocked) and make every expectation
  satisfiable in it. Phrase a response-only expectation as the action the
  response describes (`describes the row it would add`) while keeping its
  substantive predicates. The runner's `validate` delivery-mode warnings flag
  the performed-action form; they are advisory and never fail validation or
  block a run. Where no identity is supplied or discoverable, require an
  observable future selection gate instead of an invented owner, command, or
  interface.
- In a no-change or blocked case, naming an existing sufficient rule, eval, or
  artifact is a valid answer, not a proposed mutation.
- Keep any executor-visible `expected_output` to evidence shape and output
  category. Target decisions and target phrases belong only in grader-only
  assertions.
- The grader runs isolated in an empty directory and cannot read fixtures;
  keep it that way rather than giving it the sandbox or fixture access. When a
  verdict depends on fixture semantics (invention, omission, fidelity), carry
  the minimum relevant facts in grader-only assertions or `grader_context`,
  never in executor-visible material, and state that using them counts as
  supplied and that restating every fact is not required. Executors receive
  only declared, git-tracked inputs (the runner refuses to launch with an
  untracked declared input), so a missing or substituted fixture is a delivery
  gap, not a skill failure.
- For a semantic assertion, define the predicate and the prohibited outcome,
  not a magic phrase, and run a paraphrase preflight: two materially different
  compliant phrasings and one non-compliant phrasing. Examples introduced with
  `such as` or `or equivalent` are alternatives.
- For a mechanically inspectable property (absolute sandbox links, exact
  prefixes, forbidden keys, file-change sets), prefer structured fields,
  explicit delimiters, or a deterministic check scoped to the relevant field
  or response region. In a composite response, name the region an assertion
  governs (explanation, payload, command transport, post-action checks): a
  fenced transport does not fail a payload-only contract, and a prohibited
  identifier may be quoted to diagnose the bad input but must be absent from
  the corrected or public payload.
- When optional commands, subagents, review loops, or artifact rewriting are
  not the contract under test, bind them to a bounded mode so they cannot
  dominate runtime or output.

## Runs And Iterations

- A run measures one exact skill, prompt, assertion, fixture, and proof-path
  state; until the affected suite runs again after an edit, label the edit's
  effect `Unproven`. Rerunning unrelated suites does not replace that missing
  closing run.
- `source_fixtures.dirty` means the run measured working-tree bytes. It is not
  clean-source proof, and committing the fixtures afterward does not clean it
  retroactively.
- While a case contract is still changing, use an authorized `--eval-id`
  diagnostic with the requested configs; it is non-closing. Then freeze the
  skill, prompts, assertions, fixtures, and proof path and run the full
  affected suite once for closing evidence, when authorized. Do not launch a
  run that has no pre-registered question to answer.
- Finish `REVIEW REQUIRED` anomaly adjudication before a final commit or
  closure handoff; an earlier checkpoint must keep the anomalies open.
- Do not send private skill packages, eval content, outputs, or session
  excerpts to an external agent or hosted service without explicit user or
  project authorization.

## Reading Results

- Read recorded outputs, not only grades. Bytes that violate an assertion the
  grader passed are a grader false positive; bytes that satisfy an assertion
  the grader failed, including a lexical miss on a semantic predicate, are a
  grader false negative. Neither is evidence for a skill edit, and a corrected
  reading stays diagnostic.
- For a candidate-below-baseline cell, compare both outputs assertion by
  assertion under the same predicate. If only vocabulary or tense separates
  them, record a paired grader inconsistency; do not teach the skill to echo
  the baseline or the grader.
- An adjusted aggregate that excludes stub, placeholder, timeout, or other
  anomalous cells is diagnostic only: report the official result first and
  name the excluded cells and the criterion. Excluded or timed-out cells,
  especially asymmetric `with_skill` ones, leave the targeted behavior
  unmeasured.
- Final-response prose, copied ids, and self-reported counts are not
  execution proof without recorded runner or host evidence. If an action
  happened but was not recorded, fix the recording or downgrade the proof
  claim; never make the agent deny the action.
- When both configurations pass, the eval may not show the skill helped. Token
  and time deltas are cost signals, not proof on their own.
- Compare iterations only when skill source, prompts, fixtures, assertion set,
  and proof surface match; otherwise compare retained contracts and report the
  coverage change separately. A rerun after several simultaneous changes (skill
  text, runner recording, assertions) proves the combined state was measured,
  not which change moved the score.
- A regression against an older iteration is a lead: executor, grader, and
  runner drift move untouched predicates. Cases chosen because they scored low
  tend to score higher on any rerun, so confirm with fresh same-window runs of
  the unchanged and the changed text on the fixed case set; otherwise report
  the comparison as exploratory.
- A single miss, or low-frequency scatter across repeated runs, is variance
  until a stable mechanism appears; use repeated runs before editing again.
- Write `improved` or `optimized` only after a clean, complete closing run
  (same eval set, per-eval isolation, complete metrics, both configs) after the
  last relevant edit; otherwise label the effect `Unproven` or `Accepted risk`.
