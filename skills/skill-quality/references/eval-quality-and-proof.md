# Eval Quality and Proof

Read this reference before changing eval prompts, assertions, fixtures, proof paths, suite coverage, or benchmark interpretation, and before reporting a rerun-dependent quality claim.

## Evaluation Iteration Boundaries

Treat each benchmark as a measurement of one exact skill/eval/fixture state,
not as a floating verdict on the current working tree.

- Before a run, record the affected suite, target failure mechanism, relevant
  skill/eval/fixture paths, and the current change boundary (for example the
  working-tree diff or commit plus iteration manifest).
- A skill, assertion, prompt, fixture, or proof-path edit made after a run
  supersedes that run as closing evidence for the changed behavior. Keep the
  earlier result as historical evidence, but label the latest edit's effect
  `Unproven` until the affected suite runs again.
- Run only suites affected by the latest change unless a broader regression
  claim needs more coverage. Re-running unrelated suites does not repair a
  missing closing run for the changed suite.
- Before reporting or committing a measured improvement, verify that the
  cited closing run occurred after the last relevant tracked edit and that its
  manifest points to the intended model, configs, run count, and skill source.
- Treat `source_fixtures.dirty` or equivalent tracked-fixture dirtiness as a
  measurement-boundary warning. The run may measure the recorded working-tree
  fixture bytes, but it is not clean-source proof. Committing those fixture
  edits afterward does not retroactively clean the manifest; clean-source proof
  requires a later post-checkpoint run, when separately authorized, or an
  explicit absence status.
- When suite assertions or case coverage changed between iterations, raw
  pass-rate movement is not an apples-to-apples trend. Compare retained
  contracts or mapped assertions, and report the coverage change separately.
- During a repair loop, use a runner-supported eval-id subset for a
  pre-registered case-specific diagnostic when that execution is authorized.
  Keep the requested config comparison together. A partial run can show whether
  the targeted mechanism is observable in that case, but it is not a full-suite
  closing run and must not supply a package-wide pass rate, regression claim, or
  clean-suite status. After the contract is frozen, run the complete affected
  suite once for closing evidence when the user's authorization includes that
  run; otherwise report the closing run as not performed.
- After changing a skill rule, prompt, assertion, evidence taxonomy, or output
  contract, run a contract-collision audit before the next closing run. Check
  activation and non-applicability rules, workflow steps, output contracts,
  examples, common and per-eval assertions, README text, and current changelog
  guidance for contradictory or stale obligations. A new rule that says a
  narrow answer may use a symbol anchor does not silently supersede an existing
  path-required assertion; a new supplied-source taxonomy does not leave old
  assertions calling the same material workspace-local evidence.

Maintain a compact iteration ledger during repair loops:

| Iteration | Artifact boundary | Target mechanism | Result/anomalies | Decision |
| --- | --- | --- | --- | --- |
| [run directory] | [diff/commit and affected paths] | [contract or measurement question] | [official result and flagged cells] | [keep, edit, rerun, variance, blocked] |

Stop launching more full-suite runs when the next run has no pre-registered
question or when failures move without a stable shared mechanism. More samples
can measure variance; they are not a substitute for deciding what the next run
is intended to prove. Do not make every assertion edit pay for a full-suite run:
use a partial diagnostic while the target contract is still changing, then
freeze the prompt, assertions, fixtures, and proof path before the single
closing full-suite run.

If the benchmark says `REVIEW REQUIRED`, finish anomaly adjudication before a
final commit or closure handoff. Classify every candidate-below-baseline cell,
fixture-dirty signal, infrastructure anomaly, timeout, and mechanical
grader/output contradiction. An owning workflow may still create an explicitly
non-closing reversible checkpoint, but it must preserve the unresolved anomaly
state and continue the repair loop rather than describe the run as clean.

## Eval Design

Update evals in the same change set as behavior changes. Evals should be
discriminating, observable, and hard to pass with the old failure mode.

- Prefer per-eval expectations for narrow behavior. Add a common assertion only
  when it is valid for every eval, including exact-format and verbatim-output
  cases.
- Before adding, changing, or keeping a common assertion, check the eval classes
  it will govern, including activation-only, exact-format, localized, verbatim,
  narrow-boundary, and no-change cases. Move scenario-specific stop gates or
  narrow behavior into per-eval expectations.
- For every conditional common assertion, state both its positive applicability
  predicate and its non-applicable result in grader-readable terms. Do not rely
  on the grader to infer that absent artifact sections, option payloads, source
  handling, language rules, or lifecycle proof should pass when the triggering
  surface is absent. The applicability predicate must be observable from the
  delivered prompt and recorded proof surface; otherwise move the assertion to
  the owning per-eval expectations.
- Classify each eval's delivery mode before writing expectations: executing
  changes, response-only decision or command plan, artifact creation/revision,
  closure-only, or blocked/no-change. Every expectation must be satisfiable and
  observable in that mode. Do not require performed commands from a
  response-only case unless the prompt explicitly requests the exact command
  sequence; do not require a complete plan body from a closure-only decision;
  and do not grade a blocked case as completed implementation.
- Within response-only, closure-only, and blocked modes, separate what the
  current response must instantiate from what it must require a future artifact
  or authorized action to instantiate. If a concrete owner, authority, source,
  interface, or other identity is neither supplied nor discoverable in the
  permitted mode, do not require the response to invent it. Require an
  observable future selection or binding gate, its proof or acceptance record,
  and the stop condition that applies until it exists. A compliant assertion
  must fail omission of that future gate without failing a response solely for
  withholding an unsupported current identity.
- Separate the contract under test from auxiliary workflow mechanics. Commands,
  subagents, review transport, artifact rewriting, optional host capabilities,
  and iterative self-correction can materially change runtime, output size, and
  proof surfaces even when the case is meant to test only a decision rule. When
  an auxiliary mechanism is not itself under test, bind it to a deterministic
  non-executing or bounded fallback mode, or split it into a separate case. When
  it is under test, make that second contract and its evidence explicit. Do not
  let an optional capability become a hidden target that dominates the measured
  behavior.
- In a no-change or blocked case, allow the output to prove scope by naming an
  existing rule, eval, or artifact as sufficient and explicitly declining to
  edit it. Do not treat that no-change explanation as a proposed mutation, and
  do not require a new eval, doc, or skill edit merely to demonstrate that
  existing coverage already owns the failure mode.
- Verify that every declared fixture reaches the executor through the runner's
  copy contract. In this repository's git-backed tracked-only sandbox, a newly
  created but untracked fixture is excluded even when it exists in the source
  checkout. Treat a missing or excluded fixture as a fixture-delivery or
  measurement gap, not a skill failure.
- Keep grader adjudication context separate from output obligations, and audit
  grader-visible ground truth separately from executor fixture delivery.
  The isolated grader cannot re-read fixtures, so an assertion about invention,
  omission, or fidelity to fixture-derived facts is unobservable unless its
  prompt carries the minimum relevant facts. Put that adjudication context in a
  per-eval grader-only expectation or another runner-recorded grader-only input;
  do not add it to the executor prompt or to any `expected_output` field the
  executor can see. State that using those facts counts as supplied and that the
  output need not restate every fact unless a separate output contract requires
  it. If the suite cannot provide the context without leaking the target answer,
  rewrite or remove the assertion instead of changing the target skill.
- Before interpreting a missing-file or wrong-artifact response, compare the
  declared fixture set, source fixture dirtiness, sandbox copy strategy,
  excluded-path sample, and change manifest. If the intended target was absent
  and the executor substituted a nearby unrelated fixture, fix the prompt or
  fixture boundary rather than teaching the skill about the substituted
  example.
- Audit runner-provided affordances against the case's authority and delivery
  mode. A designated artifact destination, available tool, optional fallback,
  or conditional transport instruction must not become a request to create a
  file, invoke a capability, broaden scope, or persist state. When the harness
  intends capture or availability only, say so in the executor contract and
  add runner-level regression coverage; do not rely only on the target skill to
  negate the scaffold.
- When a timeout or extreme token/output increase includes repeated tool
  retries, artifact churn, delegated review loops, or optional-capability
  expansion, inspect whether the case accidentally measures that auxiliary
  workflow instead of its stated contract. Treat this as a case-cohesion,
  invocation, or runtime-cost confound before attributing it to the target skill.
  Narrow the auxiliary mode without weakening the behavior, safety, consent, or
  proof requirement the case was designed to test.
- Write expectations against visible output, files, commands, records, or
  decisions, not against style taste.
- For a natural-language assertion whose contract is semantic rather than
  exact-format, define the required predicate and prohibited outcome instead of
  a magic phrase. Before an expensive run, perform a paraphrase preflight: check
  at least two materially different, minimally compliant phrasings and one
  non-compliant phrasing against the assertion. Examples introduced with
  `such as`, `including`, or `or equivalent` are alternatives unless the
  contract independently requires every item. If a compliant paraphrase fails
  only because it omitted assertion wording, repair the assertion or grader
  boundary rather than copying that wording into the target skill.
- For mechanically inspectable output properties, audit the recorded artifact
  directly and make the grader boundary equally explicit. Examples include
  forbidden absolute sandbox links, runner or eval-file citations, exact
  prefixes, missing required paths, file-change sets, and secret-like literal
  reproduction. A grader pass does not override contradictory output bytes,
  and runner `Sanity checks: OK` proves only the anomaly classes the runner
  computes, not every suite contract. If repeated graders miss a mechanical
  property, add a deterministic check when supported or sharpen the assertion
  with the concrete prohibited predicate without leaking the target answer to
  the executor.
- For a composite response, partition the proof surface before grading:
  explanatory or diagnostic prose, the primary artifact payload, command or
  transport examples, and post-action checks are separate regions. An
  assertion about raw payload bytes, Markdown fences, standalone shape,
  forbidden provenance, or exact prefixes must name the region it governs
  unless it intentionally governs the whole response. Necessary labels or a
  fenced shell transport outside an unfenced message payload do not violate a
  payload-only contract; a prohibited local identifier may be quoted to
  diagnose the bad input but must remain absent from the corrected or public
  payload. Prefer structured fields or explicit delimiters when region
  boundaries matter. If the grader cannot observe the target region
  deterministically, move the requirement to a scoped per-eval expectation or
  change the output contract instead of applying a whole-response predicate.
- Apply byte-level adjudication in both directions. When recorded bytes satisfy
  a mechanical assertion that the grader marked failed, record a grader false
  negative instead of tightening unrelated skill prose. Scope deterministic
  predicates to the relevant JSON path, field, array element, or output region
  so inert copies of the same word elsewhere do not create false failures.
  Keep the official aggregate unchanged and report the artifact-level corrected
  reading as diagnostic only.
- If the eval runner shows `expected_output` or an expected-output summary to
  the executor, keep that summary high-level: describe the evidence shape and
  output category, not the target decision or named contract. Put
  discriminating answer details only in grader-only assertions, fixtures, or
  hidden grader material so the baseline is not handed the target behavior.
- Apply that leakage discipline to your own contract delta and self-authored
  assertions, not only to delegated eval work: a `SKILL.md` line or
  self-authored assertion must not copy a grader assertion's wording or a
  literal prompt phrase verbatim. Name the abstract dimension (Failure To
  Contract) and keep the concrete phrase only as a labeled example.
- Include negative pressure for the degeneration that motivated the change:
  global skill lists, fake baselines, universal checklists, weak proof
  substitutes, unsupported claims, stale assumptions, or overfit fixture names.
- Keep baselines meaningful. A 100 percent pass rate for both `with_skill` and
  `without_skill` usually means the assertion is not discriminating.
- Do not hide grader ambiguity by loosening expectations. Clarify the assertion
  or add a programmatic check when the property is mechanical. When you relax or
  delete an assertion or a both-config-pass eval to clear a failure, record the
  discrimination lost and add a compensating assertion or an explicit `Accepted
  risk`.
- If an eval expectation encodes an unsupported product fact, correct the eval
  instead of teaching the skill to invent that fact.

### Eval Suite Compaction

Treat case-count reduction as an eval-quality change, not mechanical cleanup.
Before deleting, merging, or folding a case, inventory the current suite and
write a compaction ledger with:

- old case IDs and the abstract contract dimensions each guards
- the retained case, per-eval expectation, common assertion, or fixture that
  will carry each dimension
- discrimination lost, including distinct state, language, exact-format,
  no-change, failure, or proof-boundary pressure
- the decision: keep, merge, delete, or `Accepted risk`

Compress by contract overlap, not by a uniform case-count target. A narrow,
expensive, passing, or both-config-passing case may still be the only regression
guard for a known failure. Keep it when no stronger case naturally covers the
same behavior. Stop when the next cut would lose a distinct contract, require an
artificial multi-scenario prompt, or broaden a common assertion beyond every eval
class it would govern.

Prefer these compaction moves:

- remove a common assertion that is scenario-specific or vacuous on unrelated
  cases, after moving its pressure to the owning per-eval expectations
- merge cases only when one realistic prompt can exercise the combined behavior
  without becoming a harness-only matrix
- fold repeated expectations into their owning case while preserving the
  strongest observable positive and negative pressure
- remove a case when a stronger retained case covers the same contract and the
  lost input variation is explicitly recorded

After compaction, reconcile every old case to retained coverage or accepted
risk; update suite `purpose`, `coverage_notes`, and scoring notes if their
coverage description changed. Static validation proves schema and fixture
integrity only. Do not claim preserved discrimination, effectiveness, or cost
improvement without an authorized clean comparative rerun; if that rerun is not
performed, report it as not measured.

External eval prompts stay under `evals/<skill-name>/`; generated run output
stays under `evals/<skill-name>/workspace/<agent>/` and is not committed unless
the user explicitly asks.

## Running And Reading Evals

For this repository, use the shared runner:

```sh
python3 skills/skill-eval/scripts/eval_runner.py validate evals/<skill-name>/evals.json
python3 skills/skill-eval/scripts/eval_runner.py run evals/<skill-name>/evals.json --agent codex --eval-id E01 --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py run evals/<skill-name>/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py report evals/<skill-name>/workspace/codex/iteration-N
```

The `--eval-id` form is a partial diagnostic while the case contract is still
changing. Its benchmark must remain visibly non-closing. Omit `--eval-id` for
the final full-suite run.

Keep eval workflows provider-neutral and file-contract based. Do not make the
shared runner depend on local-only skill snapshots, one host's UI, or
Claude-Code-only paths.
For this repository's `with_skill` runs, use the authoritative source skill
package directly; do not substitute an installed host skill tool,
`.agents/skills` snapshot, `.claude/skills` link, or cached skill copy.

`run` drives execution, grading, aggregation, and reporting end to end. It
spawns fresh executor subprocesses with the prompt only, then fresh grader
subprocesses with the recorded output plus assertions. No agent hand-runs
prompts, hand-records outputs, injects token counts, or grades its own output.
`run` writes `iteration_manifest.json` and, per run, `prompt.md`,
`grader_prompt.md`, `outputs/`, `grading.json`, `metrics.json`, and `run.json`,
plus `benchmark.json` and `benchmark.md` at the iteration root.

`report <iteration-dir>` only re-renders `benchmark.md` from `benchmark.json`;
it must not start a server, open a browser, bind a port, write a PID file, or
leave a background process.

Treat missing metrics, missing grades, missing configs, failed or timed-out
executors, grader failures, omitted assertions, or reused legacy artifacts as
incomplete proof, not as a pass. Also treat an abnormal aggregate-metric shift
between runs — for example `mean_tokens` collapsing — or executor batching that
loses per-eval isolation as a stop-and-verify condition, not a pass.

When cells are excluded or unscored because an executor timed out, classify
whether the surface is runner/grader infrastructure, prompt or invocation,
runtime-cost/complexity, run variance, or a real skill behavior failure before
using the aggregate delta or editing skill prose. If excluded or timeout cells
hide targeted behavior, especially asymmetrically in `with_skill`, report those
evals as unmeasured or cost-risk evidence until a complete rerun or separate
scored artifact clears them; do not call the run clean or harmless merely
because the pass-rate aggregate omits the cells.

Runner artifacts prove what the runner invoked, recorded, graded, and
aggregated. When a claim or assertion depends on prompt delivery, host, tool,
delegation, file, artifact, metric, timing, or other execution proof, audit the
evidence surface and compare the proof requirement with the recorded output set
before reading the grade as a skill signal or making root-cause or skill-quality
claims. Inspect the recorded invocation, output artifact, metric source, or
equivalent non-response evidence. Final-response prose, copied invocation IDs,
role labels, and self-reported call counts are not execution proof unless
corroborated by recorded host or runner evidence or an equivalent non-response
artifact.

If a scored executor output is only a host-continuation stub, waiting message,
tool-use placeholder, or other unresolved async artifact, do not silently
remove the cell from the official aggregate or call it an infrastructure
exclusion. Classify it as a prompt, invocation, recording, or output-set
completeness surface, report the official aggregate with that caveat, and fix
the eval prompt, runner recording, or proof path before treating the adjusted
reading as measured improvement.

When you compute an adjusted aggregate that excludes a scored stub,
placeholder, timeout, or other anomalous cell for diagnosis, label it as
diagnostic only. Report the official runner aggregate first, list the excluded
cell ids/configs and exclusion criterion, and use the adjusted number only to
localize unmeasured or contaminated behavior. Do not replace the benchmark's
official result, mark the run clean, or use the adjusted reading as proof of
improvement until a clean rerun or separately scored artifact measures the same
behavior.

Pure graders stay bound to the suite assertions recorded for the run. The
change owner treats surprising, repeated, missing, ambiguous, or
both-config-passing grades as evidence to interpret before editing skill or
eval behavior.

Read the recorded executor output as well as the grade for the targeted
mechanism. When the bytes violate a mechanical assertion that the grader marked
passed, record a grader false positive and keep the run non-closing for that
mechanism even if the official aggregate and sanity summary are clean. Keep the
official aggregate unchanged; artifact-level contract audit determines whether
the run can support the narrower closure claim.

The converse also applies: when recorded bytes satisfy a mechanically
inspectable assertion that the grader marked failed, record a grader false
negative and do not treat that verdict as evidence for a skill edit. If the
property is structural, parse and inspect the relevant field rather than asking
the grader to infer field scope from the whole output. Official runner results
remain unchanged; any corrected reading is diagnostic until the grader or
deterministic check is fixed and rerun.

For a non-exact natural-language assertion, also inspect whether the recorded
answer satisfies the semantic predicate through equivalent wording. A verdict
that depends on repeating one unstated phrase is a lexical grader false negative,
not evidence for another skill sentence. Keep the official aggregate unchanged;
either repair the assertion around the predicate and rerun the affected case, or
record the isolated anomaly and stop when there is no stable contract gap.

For a candidate-below-baseline signal, compare the candidate and baseline
outputs and verdict evidence assertion by assertion under the same semantic
predicate. If an equivalent or stronger candidate behavior fails while the
baseline passes because of vocabulary, future-tense realization, or another
distinction outside that predicate, classify the asymmetric verdict as a paired
grader inconsistency. Preserve the official aggregate and keep the correction
diagnostic; do not teach the target skill to echo the baseline or grader. Keep
unrelated assertion failures separate so one inconsistent verdict does not
promote the whole cell to a pass.

Before comparing two iterations, confirm whether their skill source, prompts,
fixtures, assertion set, and recorded proof surface are equivalent. If not,
state which contract changed and avoid presenting the aggregate delta as a
direct model or skill improvement. A newer run can validate the new contract,
but it does not retroactively isolate which prior edit caused the difference.

Treat eval execution as a data-boundary decision. Do not send private skill
packages, eval prompts, fixtures, outputs, or session excerpts to an external
agent or hosted service unless the user or project explicitly authorizes that
data movement. Prefer local file-contract workflows when privacy is unclear.

## Result Analysis

Compare behavior before declaring improvement:

- Which failures changed from fail to pass, and which old passes stayed intact?
- Did the baseline also pass? If yes, the eval may not prove the skill helped.
- Did a new or targeted eval show any of these? If so, inspect prompt leakage,
  expected-output summaries, named capability hints, assertion applicability,
  and whether the eval is regression-only before claiming skill value.
  - a high `without_skill` pass rate
  - both configs pass
  - a high `with_skill` rate whose magnitude of help is unreadable because the
    baseline delta was not measured or read
  - a baseline that improved after an eval edit
- Did token or time cost increase? Treat deltas as cost signals. Call them
  regressions only when transcript evidence, run data, or a predefined budget
  proves the cost is not justified by useful behavior.
- Were any targeted evals excluded, unscored, or timed out? If yes, read the
  aggregate as partial and identify which behavior is unmeasured before
  accepting a headline delta.
- Did a grader failure expose unclear assertions instead of a skill defect?
- For a semantic assertion, would two different compliant paraphrases pass, or
  is the grader rewarding one phrase rather than the contract predicate?
- Did a conditional common assertion explicitly tell the grader what happens
  when its triggering surface is absent, or did absence get misgraded as
  failure?
- Did the recorded output set contain the proof the assertion requires, or did
  the proof live only in host UI, private transcript, or unrecorded tool state?
- Did the skill overfit to a fixture, phrase, project class, or old session?
- Did the change create new obligations, dependencies, or workflow authority
  beyond the user's goal?
- For any compacted suite, does every old case map to retained coverage or an
  explicit accepted risk, and did the merge remain a natural skill prompt?
  Lost coverage is a regression even when every remaining eval passes.

If repeated wording-only contract changes do not move the targeted failure,
stop tightening prose. Inspect runner recording, prompt delivery, grader inputs,
assertion scope, output-set completeness, and run variance before another skill
text edit. When that stop condition becomes tracked behavior, add or propose
generic eval coverage for the retry-stop and proof-boundary rule instead of a
local-case checklist.

If a similar failure moves to a different eval after each targeted wording fix,
treat that as a moving-failure pattern rather than proof that every new cell
needs another local sentence. Compare the per-run and cross-run evidence first:
which assertions fail, whether the failed dimension changes direction, whether
with-skill remains near ceiling, and whether multi-run results show a stable
cell or only scattered single-run misses. If repeated runs show low-frequency
scatter, classify the surface as run variance, prompt or runner leakage, or
measurement boundary and stop editing skill prose. If repeated runs show a
stable shared mechanism, choose the broad owner and update that rule or eval
pressure once instead of adding per-cell patches.

If a targeted fix makes one eval pass while the same failure mechanism appears
in another eval, stop treating the remaining failure as a local wording problem.
Classify the shared mechanism, choose its owning artifact, and update the broad
rule or eval pressure that owns it before adding another per-eval wording patch.
Keep invalid placeholder text out of executable commands, final-answer
templates, and other user-copyable guidance; if a placeholder must be discussed
as evidence, label it as non-copyable evidence instead of a template.

If adding a missing recorded evidence artifact changes the outcome, describe
the prior result as a measurement-boundary correction or proof-path
reclassification unless a separate run isolates a skill-contract change as the
cause.

If a proof-path or runner-recording change and a skill-contract change land in
the same rerun, separate what the artifacts prove from what they cannot isolate.
A grader prompt or verdict that directly cites the new recorded evidence can
prove the proof path is functioning, but it does not by itself prove how much of
the pass-rate change came from the skill text, the runner evidence, grader
behavior, or run variance.

When the proof path, recording contract, assertion boundary, or skill text
changes, rerun before claiming improvement. Treat single-run headline deltas and
unstable baselines as caveats. If single-run results repeatedly show a moving
failure or a volatile baseline, use repeated runs or an equivalent separately
scored artifact before deciding whether to edit again; report per-run spread and
whether the same cell fails consistently. If an action happened but the proof
was not recorded, fix or downgrade the proof claim instead of making the agent
deny or hide the real action.

Do not claim quality, token, time, reliability, safety, or trigger improvement
unless the run data or review evidence proves that exact claim. Writing
`improved` or `optimized` specifically requires a closing rerun on a clean,
complete run — same eval set, per-eval isolation, complete metrics, both
configs; without it, label the effect `Unproven` or `Accepted risk` rather than
a pass.

Keep the iteration ledger out of user-facing changelog prose. `CHANGELOG.md`
should summarize the final durable contract change, validation command, and
honest final proof or absence status. Intermediate scores, failed hypotheses,
per-iteration narration, and local run directories belong in generated
artifacts or temporary quality notes unless one is itself a durable warning
maintainers must preserve.
