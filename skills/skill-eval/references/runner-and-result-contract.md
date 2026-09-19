# Eval Runner and Result Contract

Read this reference before executing `run` or drafting a run sequence, before relying on what the runner delivers, records, or grades, and before diagnosing or reporting an iteration or comparison.

## Commands

- `python3 skills/skill-eval/scripts/eval_runner.py` has three commands:
  `validate <suite-json>`, `run <suite-json> [options]`, and
  `report <iteration-dir> [--compare <other-iteration-dir>]`. The suite path is
  positional. `run` options are `--agent`, `--model`, `--executor-model`,
  `--grader-model`, `--config`, `--eval-id`, `--runs`, `--skill-path`,
  `--timeout`, `--concurrency`, `--npm-cache`, and `--workspace`. Do not invent
  aliases such as `--evals`, `--iteration-dir`, `--configuration`, or `--mode`,
  and do not split one bounded matrix into separate per-config runs.
- Standard sequence after explicit run authorization:

```sh
python3 skills/skill-eval/scripts/eval_runner.py validate evals/vibe-planning/evals.json
python3 skills/skill-eval/scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --eval-id E03 --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py run evals/vibe-planning/evals.json --agent codex --config with_skill,without_skill --runs 1
python3 skills/skill-eval/scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-1
python3 skills/skill-eval/scripts/eval_runner.py report evals/vibe-planning/workspace/codex/iteration-2 --compare evals/vibe-planning/workspace/codex/iteration-1
```

  The first `run` is a case diagnostic and the second the full-suite form.
- `run` drives the whole matrix: for each eval x config x run it spawns a
  fresh executor subprocess with the prompt only, then a fresh grader
  subprocess, then aggregates a raw `with_skill` versus `without_skill`
  comparison. `--agent` selects a registered provider (`claude` and `codex` are
  built in); the core path is provider-neutral, and Claude-only metric
  precision is additive.
- `--model` is passed verbatim to the provider CLI for both roles, and
  `--executor-model` / `--grader-model` override it per role. The resolved
  values are recorded as `executor_model` and `grader_model` beside `model` in
  the manifest and benchmark; absence means the provider's default, never a
  guessed id.
- Bounds: `--runs` 1..5 (default 1); `--timeout` per subprocess (default
  600 s); `--concurrency` 1..16 (default 4) concurrent provider subprocesses
  per invocation. Simultaneous invocations add up, so a user-stated
  concurrency is the total across them unless the user allows more: split the
  cap between invocations, never between the requested configs. A failed or
  timed-out executor is a failed run, its grader is skipped, and nothing is
  retried.
- All input validation (suite shape, eval ids, the `with_skill` source,
  provider availability, bounds, and declared inputs being git-tracked) runs
  before any subprocess. Invalid input exits non-zero with zero launches; an
  unknown or empty `--eval-id` also creates no iteration. An empty suite exits
  0 with an explicit empty result.
- A non-empty Codex run first probes an executor-shaped and a grader-shaped
  invocation, records the evidence at
  `evals/<skill-name>/workspace/codex/preflight.json`, and stops with zero
  suite cells if either probe fails.
- `validate` and the `run` preflight print advisory delivery-mode warnings:
  an expectation opening with performed-action wording (`Writes`, `Adds`,
  `Allocates`, `Reads`, `Commits`, and similar) in a case whose prompt carries
  a response-only marker. Negated (`Writes no …`) and alternative (`Writes or
  proposes …`) forms are not flagged. The match is heuristic, so review each
  warning against the case.

## Partial Diagnostics, Closing Runs, And Base Comparisons

- `--eval-id E01,E03` runs only the named ids with the requested config
  matrix. Use it only for an authorized, pre-registered diagnostic while a
  case's prompt, assertion, fixture, or proof path is still changing, and never
  report its result as the suite's. `SKILL.md` defines its non-closing labels
  and the freeze before the closing run, which is the same matrix run once
  without `--eval-id`.
- The runner takes the repository root from the nearest ancestor of the suite
  path that holds both `evals/` and `AGENTS.md` (else the current directory)
  and reads the skill source and fixtures from there; the default workspace
  sits next to the suite unless `--workspace` is given. For a base comparison,
  point the run at the base checkout's own suite path (a clone or worktree at
  the base commit, outside the working tree, with any copied inputs tracked
  there). Before using the result as base evidence, confirm that the recorded
  `skill_path` in `benchmark.json` lies inside that checkout and that its skill
  package matches the base commit with no uncommitted changes; a `skill_path`
  inside the working tree measured the candidate.

## Long Runs And Failures

- Before a full matrix that recent runs show to be expensive, tell the user
  the cell count (evals x configs x runs), total concurrency, per-subprocess
  timeout, and a wall-time range derived from recorded runner durations, and
  get their decision when it materially exceeds their apparent budget or
  expectation. The forecast is operational: never enter it into result
  artifacts or present it as a measured metric.
- Launch a long run only through a control handle whose interrupt behavior is
  known (an interactive PTY or a job or session id), and record the handle
  before waiting. To cancel: start no replacement or retry, send a graceful
  interrupt through that handle, wait a bounded interval, and only if still
  necessary and authorized send TERM to the exact runner and its children.
  Confirm that the controlling session ended and that no matching child
  processes remain; Ctrl-C bytes written to a non-TTY, killing by process
  name, or a signal command's exit status does not prove the run stopped. An
  interrupted iteration is non-closing. The runner submits its matrix up
  front and has no cell-level cooperative cancellation.
- An authorized run is not authorization for unlimited retries. Classify the
  failed role call first. Once explicit capacity or overload recurs at
  concurrency 1, raising concurrency is not a remedy; another full run needs a
  material change (a later service window, an authorized model change, or a
  changed workload) or a new user decision. A partial diagnostic answers a
  pre-registered content question; it is not a service-health probe.
- Classify infrastructure failures only as far as recorded evidence supports:
  `provider_capacity_explicit` for an exact selected-model capacity response,
  `provider_overloaded_explicit` for an explicit overload response,
  `provider_exit_unclassified` for a nonzero exit without enough diagnostics,
  and `sandbox_or_runtime_initialization` for failure while establishing the
  provider runtime. Keep `executor_failed` and `grader_failed` apart. Host
  approval or control failures are not suite-cell results.

## Delivery And Grading

- For the `with_skill` source, the runner resolves `--skill-path` from the
  repository root and rejects
  `.agents/skills` snapshots, `.claude/skills` links, files not named
  `SKILL.md`, and paths outside `skills/<skill-name>/`; the executor prompt
  says to read that source rather than a host skill tool or cached copy.
- Each executor runs in a per-run sandbox outside the source checkout that
  holds only the case's declared fixture roots (`files`, relative layout
  kept), the case's `support_files` (both configs), and the root `.gitignore`
  scaffold (recorded under `delivery.scaffold_files`), plus the target package
  and suite-level `skill_support_files` for `with_skill` only. Other cases,
  suite definitions, grading context, previous results, and repository
  instruction files such as `AGENTS.md` are not copied unless declared. A task
  document that is itself a skill file is delivered symmetrically as a
  declared exception, and its comparison limit is kept. Delivery is an input
  boundary, not proof that the host cannot read the original checkout.
- Git-backed delivery copies tracked working-tree bytes, so a new fixture must
  be tracked first. Source fixture dirtiness is recorded separately; identical
  bytes from a dirty source are not a clean-source measurement.
- `npm_projects` names declared fixture roots that need an installed test
  runtime; such a run requires `--npm-cache <path>` holding every dependency
  the committed manifests and lockfiles select. Before any provider cell, the
  runner prepares each project once, serially, with offline `npm ci`, install
  scripts disabled, and no audit or funding requests. A missing cache or failed
  setup stops the evaluation, possibly leaving an iteration directory with
  setup receipts and no benchmark; it never becomes a scored skill failure or
  an executor repair task. Executors get sandbox-local copies of the prepared
  dependencies, with manifest, lockfile, runtime, and dependency identities
  recorded at delivery (not re-hashed after execution). A cache listing is not
  readiness proof.
- The grader runs in an atomically created empty directory, never in the
  executor sandbox. Claude graders run without tools or session persistence;
  Codex graders ignore user configuration and rules and run with shell,
  multi-agent, and web search disabled. These are CLI controls, not an OS
  sandbox. The grader receives the original task as inert context (to identify
  supplied facts, selected branches, authority, and delivery mode, not as a
  restatement checklist), the recorded output, optional `grader_context`,
  retained sandbox differences, executor evidence, and the assertions. Pass or
  fail comes from its structured verdict, never from the executor's own
  claims.
- `grader_context` is a per-case UTF-8 string of at most 16 KiB, rejected
  rather than truncated when larger, that carries only fixture facts the task
  lacks and an assertion needs; it reaches only the grader. `expected_output`
  is descriptive suite metadata and is injected into neither role. A fixture
  manifest proves identity, not content; include a whole fixture only when the
  assertion evaluates all of it.
- The executor prompt names one capture path in the sandbox, identical for
  both configs and labeled as a capture destination, not a request: executors
  write it only when the task or the workflow's own deliverable contract
  requires a file. A written file is copied to `outputs/plan.md` and folded
  into the grader's recorded output under `Written Plan Artifact` (capped,
  truncation recorded); otherwise `written_artifact.captured = false`.
- `change_manifest` records retained net added, modified, and deleted paths
  and ignored additions at capture, excluding runner scaffolding and prepared
  dependencies. An empty manifest means no retained change, not no write: it
  cannot show transient writes, external effects, successful reads, or read
  order. `ignored: true` marks only untracked executor additions the sandbox
  reported as ignored.
- `executor_evidence` is a tool and delegation trace collected identically for
  both configs: for Claude (`source = host`), tool names, host-issued tool-use
  ids, and session-bound sub-agent record ids from the host transcript; for
  Codex (`source = runner`), one entry per item parsed from the executor's
  `codex exec --json` stream. The grader sees only closed-vocabulary program
  names (`other` otherwise), validated ids, and `(in_progress)` marks; paths,
  command text, output, and reasoning never reach it. An entry the runner could
  not parse confidently carries `parse_error` and reads as a hint. Plain
  read-only reads of the executor's own delivered skill package are omitted
  from the grader's list, kept in `run.json`, and counted in
  `grader_omitted_skill_reads`. A listed id proves only that the provider
  recorded the item, not that a command succeeded, a file was read, or a
  delegation ran. When no trace can be built, `captured = false`, the section
  is omitted, and absence is not disproof.
- The grader verdict is schema-constrained and keyed by each assertion's
  1-based `id`. Grader output the runner cannot parse is `grader_unparseable`,
  excluded from the comparison, and never a scored 0%. Failed or timed-out
  calls keep bounded `outputs/executor_stderr.txt` or
  `outputs/grader_stderr.txt` and a `failure` object in `run.json`.

## Artifacts And Metrics

- `run` writes `iteration_manifest.json` and, per run, `prompt.md`,
  `grader_prompt.md`, `outputs/`, `grading.json`, `metrics.json`, and
  `run.json` under `evals/<skill-name>/workspace/<agent>/iteration-N/`, plus
  `benchmark.json` and `benchmark.md` at the iteration root. The benchmark
  carries per-eval and overall raw pass rates, the `with_skill`/`without_skill`
  comparison, executor metrics, suite coverage, a `sanity_checks` section
  (infrastructure failures, scored-0% cells, candidate-below-baseline cells,
  dirty declared fixture roots, partial selections), and a `Failed assertions`
  section listing each scored cell's failed assertions with the grader's
  evidence and each unscored cell's status.
- `grading.json` lists every assertion (`common_assertions` then per-eval
  `expectations`) exactly once, in order, with `text`, `passed`, and
  `evidence`; an assertion the grader omits is recorded as failed.
- `report <iteration-dir>` re-renders `benchmark.md` from `benchmark.json`;
  `--compare <other-iteration-dir>` adds the other iteration's raw per-eval
  rates. Compare recorded delivery, runner, suite, treatment, fixture,
  dependency, model, and coverage identities first: changed inputs are a
  different measurement series, missing historical identity is unknown, and
  agreement is necessary but not sufficient for a causal reading. `report`
  starts no server or browser, binds no port, writes no PID file, and leaves
  no background process.
- Metrics are never hand-typed or estimated, and no flag injects them. Claude
  usage comes from its JSON envelope, Codex usage from the `turn.completed`
  event, and Codex executor duration from the runner's own timer. Displayed
  time and tokens are executor-only (grader cost excluded); `± stddev` appears
  only when more than one run captured the value. A missing value is shown as
  absent with a reason, never as `0`.

## Result Verification And Reporting

These rules detail the `SKILL.md` Result Closure steps.

- A finished run is not a clean result. Stop to verify on `REVIEW REQUIRED`,
  `error_run_count > 0`, any `grader_unparseable`, `grader_failed`,
  `executor_failed`, or timeout status, any scored-0% or
  candidate-below-baseline cell, or a dirty source fixture. A partial
  selection is `REVIEW REQUIRED` by construction.
- A flagged cell's recorded outputs are `outputs/output.txt` and
  `outputs/grader_output.txt`. Never report a grader- or runner-side failure
  as a skill score: fix the cause and rerun, or report the cell as an excluded
  infrastructure failure with the reason.
- If a semantically compliant answer failed for lacking a preferred phrase,
  or a candidate failed where the baseline passed only on vocabulary or tense,
  record a lexical false negative or a paired grader inconsistency, keep the
  official aggregate unchanged, and route the assertion repair to the quality
  owner instead of adding the phrase to the skill.
- In the report, say when any cell was excluded or re-graded and give the
  corrected reading.
- Explaining a partial selection does not make it full-suite proof. A rate
  across a changed prompt, assertion, fixture, or skill source is not
  like-for-like, whether or not `report --compare` produced it; treat the
  earlier number as a non-comparator.
