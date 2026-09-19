# Evidence and Failure Classification

Read this reference when the quality decision depends on relayed or delegated analysis, session history, represented workflow state, structured public output, runner affordances, or artifact capture.

## Relayed And Delegated Evidence

- A relayed host-agent eval summary is a pointer, not proof. Verify
  root-cause, improvement, or changelog claims against `benchmark.json`,
  `iteration_manifest.json`, `run.json`, `grading.json`, and recorded outputs;
  if they are unavailable, keep artifact-dependent claims `Unproven`.
- When delegated review, extraction, or benchmark analysis feeds a tracked
  decision, ask the delegate for evidence, unsupported claims, and surfaces
  that must not change; do not assume this skill's context transfers.

## Session-History Audits

- Count a candidate as skill-driven edit evidence only when the skill trigger,
  read, or decision, the tracked patch, and the verification (or its explicit
  absence) fall inside one turn: one user request plus its directly associated
  assistant, tool, edit, and verification steps before the next unrelated
  request. Co-occurrence elsewhere in the same session file does not count;
  mark such joins low-confidence or excluded.
- A same-turn no-change decision is skill use, not edit evidence.
- Exclude current-audit search output, quoted skill bodies, session metadata,
  reference-only reads, and eval-runner sandbox sessions.
- For large histories, split extraction into bounded ranges or questions,
  keep per-session notes outside tracked packages, and synthesize before
  editing.

## Binding The Eval's Universe

- Evidence: bind which sources count, whether a verified target workspace,
  runner-delivered fixtures, or supplied represented material. If a prompt
  meant to rely on supplied excerpts says `this project` or otherwise invites
  the ambient checkout, fix the prompt binding instead of teaching the skill to
  ignore a legitimately bound workspace.
- Represented state versus action mode: a response-only prompt may supply
  facts such as `changes staged` or `commit authorized` while forbidding the
  executor to inspect or mutate the sandbox, and it must state both. Do not let
  an empty ambient checkout overwrite supplied state, and do not treat a
  represented action as performed. Response-only delivery changes what may be
  executed and proved, not the represented workflow's required outcome.
- Structured public output: keep delivered input, internally retained state,
  and public serialization separate; input availability does not authorize
  reproducing it. If projection leakage survives skill wording, fix the owning
  prompt, fixture, or output schema, and prefer deterministic key checks.
- Authority: a runner-provided output path, tool, fallback, or transport is
  not user authority. If scaffolding induces unrequested writes or scope, make
  it explicitly non-authorizing in the runner or prompt contract and test that
  symmetrically across configs, instead of adding downstream skill prose.
- Proof transport: once an artifact is independently authorized, its complete
  bytes must reach the grader through the capture destination, while its
  logical identity stays a repository-relative path, never a sandbox or
  capture path. Writing in a chat-only case is an authority failure; a
  sandbox-only artifact the grader never received is a recording gap.
