# MCP Guardrails

Read this reference before shaping or retrying detailed MCP calls, relying on MCP 6.3 response fields, selecting expert or batch tools, interpreting timeouts/server faults, or making version/mapping-sensitive recommendations.

## MCP Guardrails

- Start with the highest-level read-only MCP call that can answer the question.
  - `inspect-minecraft`: versions, artifacts, vanilla classes, source search, raw files.
  - `analyze-symbol`: existence, mappings, lifecycle, workspace compile-time names, API overview.
  - `compare-minecraft`: migration and registry/class diffs.
  - `validate-project`: workspace, Mixin, access widener, and Forge-style access transformer validation.
  - `analyze-mod`: mod JAR summary, search, decompile, class source, bytecode-only class members, remap preview/apply.
  - `manage-cache`: stale cache or index diagnosis, including the `verify` action and preview-then-apply maintenance.
- Reach for these supporting utilities directly when the entry tools do not cover the job:
  - `get-registry-data`: structured registry bodies (blocks, items, biomes, …) via the server data generator for one version.
  - `get-runtime-metrics`: service counters and latency snapshots when cache, search, or index behaviour looks off.
  - `nbt-to-json`, `json-to-nbt`, `nbt-apply-json-patch`: typed-JSON round-trip and RFC6902-style in-place edits for Java Edition NBT payloads.
  - `verify-mixin-target`: one-call Mixin owner/member existence check with
    `@Shadow`, `@Accessor`, and `@Invoker` advice; set `autoRemap: true`
    when readable owner/member names must be translated against a version
    target.
  - `batch-class-source`, `batch-class-members`, `batch-symbol-exists`, and
    `batch-mappings`: fixed 1..50-entry read-only shortlists with per-entry
    status and aggregate `summary`; use them when entries share one resolved
    artifact or Minecraft version, not for dependent discovery chains.
- Drop to low-level tools only for exact code, exact descriptors, raw registry bodies, detailed validator output, or direct JAR/remap control.
- Use the MCP 6.3.0 response contract when shaping expert or batch responses:
  prefer `detail: "summary" | "standard" | "full"` plus `include[]`; treat
  `compact` as an old-shape migration hint, not a current expert-tool argument.
- Read MCP 6.3.0 response paths directly. `inspect-minecraft` request echo lives at
  top-level `subject.requested` / `subject.resolved`, not
  `summary.subject`; `meta.warningDetails[]` points to `meta.warnings[]` by
  `index`, not by a duplicated `message`.
- For source lookups, `get-class-source` and `get-class-members` use
  `target: { kind, value }` or `target: { kind: "artifact", artifactId }`;
  they also accept `target: { kind: "workspace" }` with `projectPath`, and
  `target: { kind: "dependency", group, name, versionFromProject }` for
  Fabric/loader dependency classes. Do not use the removed
  `target: { type: "artifact", artifactId }` shape.
- Flat artifact tools (`find-class`, `search-class-source`,
  `get-artifact-file`, `list-artifact-files`, and `index-artifact`) accept
  either a flat `artifactId` or the shared `target` shape, exactly one.
  `find-class` also accepts top-level `projectPath`, so it can resolve
  `target.kind="workspace"` and dependency targets that use
  `versionFromProject` directly. For the other flat tools, resolve first and
  pass `artifactId` when the desired target needs external `projectPath`
  context, such as `workspace` or a dependency target without an explicit
  version.
- `inspect-minecraft` direct `class` / `file` / `search` subjects may
  auto-resolve from workspace context only when exactly one workspace is known
  to the MCP process; several candidates return `workspaceCandidates`. Prefer
  an explicit workspace subject with `projectPath` or an explicit
  `subject.artifact` when the answer must be reproducible.
- `inspect-minecraft` workspace `subject.focus` is a structured object, never
  a string. Use `{ kind: "class", className }`, `{ kind: "search", query }`, or
  `{ kind: "file", filePath }`; if a string focus is rejected, treat returned
  schema-validated `exampleCalls` as retry shapes instead of guessing.
- For class member lookup, expect pagination at the 150-member default and
  follow `nextCursor` when needed. Read the shared owner from
  `members.ownerFqn` when present, derive modifiers from `javaSignature`, and
  request `include: ["descriptors"]` or `includeDescriptors: true` when field
  `jvmDescriptor` values are required for Mixins or access entries. Use
  `projection: "names"` or `"signatures"` only for existence/signature triage
  where losing descriptors and annotation metadata is acceptable.
- `get-class-members` exposes annotation-type member defaults as
  `annotationDefault` when bytecode carries them. Pass `includeAnnotations:
  true` for runtime-visible member annotations. Lean projections drop
  annotation fields; `analyze-mod` `task="members"` includes defaults and
  annotations without a flag.
- If class lookup returns `ERR_CLASS_NOT_FOUND`, inspect top-level
  `didYouMean[]` candidates as hints, not assertions. Same-simple-name
  candidates often indicate a moved class; verify the candidate before
  patching imports or descriptors.
- `find-class` searches Jar-in-Jar shell nested `.class` inventories, including
  Fabric API umbrella jars. Top-level matches can feed `get-class-source` or
  `get-class-members`, and dotted inner-class matches remain readable through
  `get-class-source`. A dependency or shell miss is not evidence of Minecraft
  obfuscated names; do not retry with `mapping="mojang"` unless the artifact is
  actually a Minecraft runtime artifact.
- When explaining stale MCP response-shape or retry-posture notes, keep the
  answer narrow: record project profile, MCP status, and all four verification source labels; explain the reference/fallback route only when it materially affects provenance; say that callable schema must be
  inspected before sending corrected payloads; include the `get-class-members`
  pagination, owner, modifier, and descriptor cautions together with the target
  shape; and only name the fallback gate unless MCP has actually failed in the
  current task.
- Validator summaries are summary-first by default. Missing per-result
  `resolvedMembers`, `toolHealth`, or `resolutionTrace` is not proof that the
  detail does not exist; pass `reportMode: "full"` or `explain: true` before
  falling back when exact validator detail matters.
- On unobfuscated versions, read structured
  `mappingContext.unobfuscatedRuntime` and `mappingContext.runtimeValidated`
  flags instead of pattern-matching former warning sentences;
  `get-class-api-matrix` reports top-level `unobfuscatedRuntime: true`.
- Bound lifecycle scans explicitly with `fromVersion`, `toVersion`,
  `maxVersions`, `includeTimeline`, and `includeSnapshots` when the task needs
  a narrow history. The MCP 6.3.0 default scan is broad enough that old implicit
  five-version assumptions are unsafe.
- Keep version and mapping discipline.
  - Pass `projectPath`, `preferProjectVersion=true`, and `preferProjectMapping=true` when supported.
  - `analyze-symbol` can infer an omitted `version` from `projectPath`;
    record the returned `versionInference { version, source }` and warning
    when you rely on it. An explicit `version` still wins.
  - Still pass explicit `version` to tools that require it, such as `validate-mixin`, `validate-access-widener`, and `resolve-workspace-symbol`.
  - Prefer direct `target` addressing for `get-class-source`,
    `get-class-members`, and flat artifact tools when the target is
    self-contained. Use `resolve-artifact` first and pass `artifactId` when
    later calls need a shared indexed artifact or workspace-only context.
- Parallelize only independent read-only discovery calls once `projectPath`, loader, version, and mapping are known.
  - Keep dependent chains sequential.
  - Do not run `manage-cache`, `index-artifact`, or remap/mutating flows in parallel with calls that depend on the same cache or JAR.
- If payload shape is unclear or an entry tool errors, read `references/mcp-recipes.md` before inventing fields or dropping to a lower-level tool.
- Apply the MCP failure budget.
  - If a high-level read tool fails with a worker restart, timeout, or transport
    error, retry once with a narrower high-level payload.
  - If the narrow retry fails, stop using that tool for the current task and use
    the relevant workspace, source jar, Gradle, or log fallback.
  - If `validate-project`, `validate-mixin`, `validate-access-widener`, or
    `validate-access-transformer` restarts once, do not loop. Record the
    validator as unavailable for this task and run
    `references/validator-fallbacks.md`.
  - If `validate-project` returns `ERR_TOOL_TIMEOUT`, read
    `meta.timeout.phase`, `retryRecommendation`, and
    `workerRestartInitiated`. Treat the validator result as unavailable for
    the timed-out fact, then split/narrow the validation or switch to the
    validator fallback; do not report success from a timeout or infer that
    worker replacement completed. If the supervisor returns
    `ERR_LIMIT_EXCEEDED`, wait or narrow the request instead of queuing more
    validator work.
  - If `ERR_INVALID_INPUT` occurs, read the reported field errors, correct the
    payload once using `references/mcp-recipes.md`, and retry the same
    high-level tool before changing tools. When explaining this route without
    actually running the corrected call, record profile assumptions, MCP status,
    and verification-source labels first; target class, API, version, mapping,
    and workspace facts remain unverified until the corrected call succeeds.
  - If the error envelope carries `retryClass: "server"` such as
    `ERR_INTERNAL` or `ERR_DB_FAILURE`, do not retry the identical call as a
    transient failure. Record MCP as unable to verify that fact and use the
    relevant fallback path.
  - If you fall back, mark facts from that path as fallback-verified, not MCP-verified.
