# Final Quality Checks

Read this reference before finalizing or committing a tracked skill or eval change. Apply only the checks relevant to the current change and proof surface; it is a closure audit, not a requirement to add more prose.

## Degeneration Checks

Before finalizing, reject these common regressions:

- Broad rewrites that erase known-good contracts to fix one eval.
- Copying an old skill wholesale instead of recovering the minimal useful rule.
- Turning examples, fixtures, or session anecdotes into universal requirements.
- Promoting named pattern sections, domain-specific branches, fixture-derived
  checklists, or single-example taxonomies into `SKILL.md` unless multiple
  independent evidence sources or a user-approved scope make them part of the
  skill contract.
- Echoing grader-assertion wording or a literal prompt phrase verbatim into
  `SKILL.md` or a self-authored assertion instead of naming the abstract
  dimension.
- Pasting universal checklists into every workflow.
- Requiring a companion skill, model, server, browser, or network path when the
  skill should be self-contained or provider-neutral.
- Moving process details into the description field so agents follow metadata
  instead of reading the body.
- Leaving a long `SKILL.md` append-only when conditional procedures, detailed
  checklists, domain variants, repeated examples, tool detail, or historical
  rationale obscure activation, scope, stop gates, and load-bearing invariants.
- Moving load-bearing always-applicable rules into references solely to hit a
  fixed line or word target, or creating references without explicit
  applicability routing from `SKILL.md`.
- Weakening proof paths because they are expensive.
- Continuing wording-only contract tightening after clean reruns leave the
  targeted failure unchanged.
- Continuing per-cell wording patches when a failure moves across evals and
  repeated runs have not shown a stable skill-contract gap.
- Re-running the entire suite after every local assertion edit when an
  authorized partial diagnostic can answer the pre-registered question, or
  presenting that partial diagnostic as full-suite closing proof.
- Tightening a target skill or assertion around the exact wording of one grader
  false negative when the response satisfied the non-exact semantic predicate.
- Treating a failure that moves across evals after a targeted fix as a new local
  wording problem instead of a shared mechanism.
- Treating a data-flow or credential-propagation warning as a wording-only
  problem while the flagged source-to-sink path remains authorized elsewhere.
- Preserving exact or verbatim content across a sensitive sink without an
  explicit safety-precedence rule and a fail-closed path.
- Claiming that skill prose, static validation, or a synthetic fixture proves
  host isolation, credential revocation, or external analyzer clearance.
- Leaving invalid placeholder text in executable or user-copyable examples
  because nearby prose says to replace it later.
- Expanding common assertions so exact-format, localized, or verbatim cases
  become impossible to satisfy.
- Forcing every suite toward one numeric target, deleting narrow cases without a
  contract ledger, or replacing natural prompts with artificial multi-scenario
  matrices.
- Counting skipped, flaky, unavailable, self-graded, or incomplete evals as
  proof.
- Replacing the official runner aggregate with a diagnostic adjusted aggregate
  that excludes scored anomalous cells.
- Counting an unrerun or contaminated run — no closing rerun, collapsed
  aggregate metrics, or lost per-eval isolation — as proof of improvement.
- Calling a run "closing" when a relevant skill, assertion, prompt, fixture, or
  proof-path edit happened afterward.
- Comparing headline pass rates across changed assertion sets as though they
  measured the same denominator and contract.
- Treating a source-checkout fixture as delivered evidence without checking
  that the runner copied it into the executor sandbox.
- Requiring execution proof, full artifact content, or implementation completion
  from an eval mode that can only record a response-only decision, closure, or
  blocker.
- Treating an ambiguous represented project as the ambient runner checkout, or
  repairing that prompt-boundary defect with more skill prose.
- Treating a runner path, tool, fallback, or transport affordance as user
  authority, or trying to cancel that authority leakage only with downstream
  skill wording.
- Treating non-authorizing capture transport as optional after the represented
  workflow independently requires an artifact, leaving the grader without the
  complete deliverable while a sandbox-only copy exists.
- Encoding conditional common assertions without an explicit observable
  applicability predicate and non-applicable result, so graders fail cases
  solely because an irrelevant surface is absent.
- Promoting an entire reference checklist into `SKILL.md` after one miss, or
  keeping a repeatedly missed load-bearing invariant reference-only without
  evaluating instruction reachability.
- Calling a run contract-clean because the grader and sanity summary passed
  while recorded output bytes violate a mechanically inspectable assertion.
- Treating a grader false negative over mechanically compliant bytes as proof
  that another skill sentence is needed, or writing a whole-output predicate
  when the contract applies to one structured field.
- Treating a dirty tracked-fixture run as clean-source proof, or assuming a
  later fixture commit retroactively changes the run manifest.
- Treating a checkpoint made before `REVIEW REQUIRED` anomalies are adjudicated
  as final closure, or losing the unresolved anomaly state after that
  checkpoint.
- Copying the iteration ledger, intermediate scores, or failed repair
  hypotheses into `CHANGELOG.md` instead of recording the final durable
  behavior and proof status.
- Adding a new rule or evidence taxonomy without checking for collisions with
  existing applicability rules, output contracts, examples, and eval
  assertions.

## Self-Check

Before reporting completion:

- Is the failure signal tied to evidence, not guesswork?
- Did surprising, repeated, tool-related, or artifact-related eval failures get
  classified by failure surface before skill text changed?
- For analyzer or safety findings, does the owned skill/eval contract stop
  authorizing the prohibited source-boundary-sink path, or was it only
  relabeled? If runtime enforcement is host-owned, is the actual runtime
  property still reported as unproven?
- Did exactness, preservation, and reflection obligations get checked for
  conflict with credential, privacy, or trust-boundary controls at every
  applicable sink?
- If enforcement is host-owned, is the capability requirement and fail-closed
  fallback explicit, with scanner/runtime closure still labeled unproven?
- Does each execution-proof assertion have recorded host, runner, or equivalent
  artifact evidence rather than prose-only IDs or counts?
- Is there a contract delta before changing skill text or eval behavior?
- Are examples mapped to reusable dimensions?
- Did each mapped dimension pass the artifact-placement gate before becoming
  always-visible `SKILL.md` guidance?
- After the change, is `SKILL.md` still scannable for activation, scope, stop
  gates, and load-bearing invariants, with conditional detail routed to
  reachable references instead of retained or removed by arbitrary size?
- Did wording edits preserve modality, exceptions, anchors, and absence
  statuses?
- For eval compaction, did the ledger reconcile old cases, replacement coverage,
  lost discrimination, and accepted risks before deletion or merge?
- Did the smallest coupled files change, including evals and changelog when
  required?
- Are baseline, grader, token, timing, and report claims honest?
- Did the cited closing run occur after the last relevant edit, and does the
  iteration ledger identify what that run was intended to prove?
- Were case-specific repair checks run as visibly partial diagnostics, with the
  prompt, assertions, fixtures, and proof path frozen before the final full-suite
  closing run?
- If iterations changed prompts, assertions, fixtures, or proof surfaces, were
  coverage changes separated from raw score movement?
- Are declared fixtures present in the executor sandbox under the runner's copy
  contract, not merely present or untracked in the source checkout?
- For fixture-semantic assertions, does the isolated grader receive the minimum
  grader-only ground truth needed to distinguish supplied facts from inventions,
  without requiring the output to restate facts or leaking them to the executor?
- Can every assertion be satisfied from the eval's delivery mode and recorded
  proof surface?
- Is the represented evidence universe explicitly aligned with the executor's
  actual workspace and delivered fixtures, without accidental ambient-checkout
  substitution?
- Are represented workflow facts and executor action mode bound separately, so
  response-only delivery neither overwrites supplied state with ambient state
  nor claims an unperformed mutation?
- For a public structured record, are delivered input, internally retained
  state, and permitted serialization separate, with internal arrays, keys, and
  values omitted from public output?
- Are runner and host affordances explicitly non-authorizing unless the
  represented user or owning workflow independently permits their use?
- After artifact authority was established, did the proof path separately bind
  the logical artifact identity and the destination that must contain complete
  grader-visible bytes?
- Do conditional common assertions state an observable applicability predicate
  and what passes by non-applicability instead of requiring the grader to infer
  it?
- If a reference-owned invariant was promoted or kept reference-only, is that
  placement supported by repeated reachability evidence rather than one noisy
  cell?
- Did targeted mechanical assertions get checked against recorded output bytes,
  not only grader verdicts or the runner sanity summary, and were contradictory
  verdicts classified as false positives or false negatives without rewriting
  the official aggregate?
- Did each non-exact semantic assertion survive a paraphrase preflight instead
  of requiring a magic phrase or every illustrative example?
- For a composite response, does each mechanical assertion identify its target
  region instead of grading diagnostic prose, artifact payload, transport, and
  post-action checks as one undifferentiated byte stream?
- If tracked fixtures were dirty, is the run reported as a working-tree
  measurement rather than clean-source proof, without assuming a later commit
  retroactively changes its manifest?
- Were all `REVIEW REQUIRED` anomalies adjudicated before final commit or
  closure handoff, or explicitly preserved across a non-closing checkpoint?
- After the latest edit, did a contract-collision audit remove stale or
  contradictory rules, examples, evidence labels, prompts, and assertions?
- For a no-change or blocked case, did the grader distinguish naming an existing
  sufficient artifact from proposing an edit, and avoid requiring a new
  mutation solely as proof?
- If any adjusted aggregate excludes anomalous cells, is it labeled diagnostic
  and kept separate from the official runner result?
- Does the changelog summarize final durable behavior and proof status rather
  than reproducing the iteration ledger or local run diary?
- Are generated workspaces left uncommitted?
- Did you avoid version bumps unless this is release preparation?

For historical patterns behind these rules, read
`references/session-patterns.md` when the task asks for rationale or when a
change feels like it could make the skill larger but not better.
