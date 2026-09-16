# MCP Guardrails

Read this reference before shaping or retrying detailed MCP calls, relying on MCP response fields, selecting expert or batch tools, interpreting timeouts/server faults, or making version/mapping-sensitive recommendations.

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
- Use the current MCP response contract when shaping expert or batch responses:
  prefer `detail: "summary" | "standard" | "full"` plus `include[]`; treat
  `compact` as an old-shape migration hint, not a current expert-tool argument.
- Read current MCP response paths directly. A tool answers `{ result, meta }`
  on success and `{ error, meta }` on failure, with `meta.requestId` on both.
  `inspect-minecraft` request echo lives at `result.subject.requested` /
  `result.subject.resolved`, not `result.summary.subject`;
  `meta.warningDetails[]` points to `meta.warnings[]` by `index`, not by a
  duplicated `message`. Recovery fields sit on the error object:
  `error.fieldErrors[]`, `error.hints[]` (including next-action text),
  `error.didYouMean[]`, `error.suggestedCall`, and `error.exampleCalls[]`.
- `error.exampleCalls[]` entries are schema-valid but may be templates with
  `<...>` placeholders, so never replay one verbatim: fill every placeholder
  from verified workspace or MCP facts first. `error.suggestedCall`, when
  present, is placeholder-free.
- For source lookups, `get-class-source` and `get-class-members` use
  `target: { kind, value }` or `target: { kind: "artifact", artifactId }`;
  they also accept `target: { kind: "workspace" }` with `projectPath`, and
  `target: { kind: "dependency", group, name, versionFromProject }` for
  Fabric/loader dependency classes. Do not use the removed
  `target: { type: "artifact", artifactId }` shape.
- Flat artifact tools (`find-class`, `search-class-source`,
  `get-artifact-file`, `list-artifact-files`, and `index-artifact`) accept
  either a flat `artifactId` or the shared `target` shape, exactly one. All
  five also accept top-level `projectPath`, so each can resolve
  `target.kind="workspace"` and dependency targets without an explicit version
  (such as `versionFromProject`) directly. Resolving first and passing
  `artifactId` is optional; use it when several calls should share one
  indexed artifact.
- `inspect-minecraft` direct `class` / `file` / `search` subjects may
  auto-resolve from workspace context only when exactly one workspace is known
  to the MCP process. No candidate list is published when several are known,
  so use an explicit workspace subject with `projectPath` or an explicit
  `subject.artifact` whenever more than one workspace may be known or the
  answer must be reproducible.
- An `inspect-minecraft` workspace subject resolves exactly like
  `resolve-artifact` `target.kind="workspace"` (project compile mapping and
  loader-derived scope) unless the subject sets `mapping` or `scope`, so its
  `artifactId` can differ from one recorded under an earlier MCP release.
- `inspect-minecraft` workspace `subject.focus` is a structured object, never
  a string. Use `{ kind: "class", className }`, `{ kind: "search", query }`, or
  `{ kind: "file", filePath }`; if a string focus is rejected, take the retry
  shape from `error.exampleCalls[]` and fill its placeholders instead of
  guessing.
- For class member lookup, expect pagination at the 150-member default and
  follow `nextCursor` when needed. Read the shared owner from
  `members.ownerFqn` when present, derive modifiers from `javaSignature`, and
  request `include: ["descriptors"]` or `includeDescriptors: true` when field
  `jvmDescriptor` values are required for Mixins or access entries. Use
  `projection: "names"` or `"signatures"` only for existence/signature triage
  where losing descriptors and annotation metadata is acceptable.
- With `mapping` omitted, `get-class-members` and `batch-class-members`
  inherit the resolved artifact's mapping, even though the advertised schema
  text still says the default is obfuscated. Read the returned namespace
  (`context.mappingNamespace` / `returnedNamespace`) before trusting member
  names, and pass an explicit `mapping` when the namespace matters; an explicit
  value always wins. `batch-class-members` entries carry `context` only at
  `detail: "standard"` or `"full"`.
- `get-class-members` exposes annotation-type member defaults as
  `annotationDefault` when bytecode carries them. Pass `includeAnnotations:
  true` for runtime-visible member annotations. Lean projections drop
  annotation fields; `analyze-mod` `task="members"` includes defaults and
  annotations without a flag.
- If class lookup returns `ERR_CLASS_NOT_FOUND`, inspect
  `error.didYouMean[]` candidates as hints, not assertions. Same-simple-name
  candidates often indicate a moved class; verify the candidate before
  patching imports or descriptors. Candidates that carry their own
  `artifactId`, and `error.nestedJars` on shell misses, are covered in
  `references/dependency-jars.md`.
- `find-class` searches Jar-in-Jar shell nested `.class` inventories, including
  Fabric API umbrella jars. Top-level matches can feed `get-class-source` or
  `get-class-members`, and dotted inner-class matches remain readable through
  `get-class-source`. Nested types render as `<Outer>.<Nested>` with
  `nested: true` and `enclosingClass`. A zero-result search classified
  `partial_coverage` (an artifact flagged `partial-source-no-net-minecraft`)
  is not proof of absence; follow its `get-class-source` suggestion. A
  dependency or shell miss is not evidence of Minecraft obfuscated names; do
  not retry with `mapping="mojang"` unless the artifact is actually a Minecraft
  runtime artifact.
- `resolve-method-mapping-exact`, `analyze-symbol` `task="exact-map"`, and
  workspace method lookups that delegate to it are owner-strict: pass the full
  owner FQN, name, and descriptor. When the queried owner does not itself
  declare the method but other classes declare that name and descriptor, the
  result is `status: "not_found"` with a warning that names those classes and
  says to use `find-mapping` for an owner-agnostic lookup or query the
  declaring class directly; for an owner without a package it also says the
  owner must be fully qualified. Mapping files carry no class hierarchy, so
  inheritance or relocation is a likely explanation to confirm, not something
  the warning proves. A `not_found` without that warning is not proof of
  absence either: check the owner FQN, descriptor, namespace, and version
  before concluding. At
  the expert tools' default `detail: "summary"` without
  `include: ["candidates"]`, a single exact `resolved` answer keeps
  `resolvedSymbol` and `candidateCount: 1` but drops `candidates`;
  `detail: "standard"` or `"full"` keeps them, and `analyze-symbol` reports
  through its own summary and match blocks. `ambiguous` carries
  `ambiguityReasons[]`. Read `warnings` on `find-mapping` and
  `resolve-method-mapping-exact`: a Loom mapping-index entry-budget stop means
  the answer may be incomplete.
- When explaining stale MCP response-shape or retry-posture notes, keep the
  answer narrow: record project profile, MCP status, and all four verification source labels; explain the reference/fallback route only when it materially affects provenance; say that callable schema must be
  inspected before sending corrected payloads; include the `get-class-members`
  pagination, owner, modifier, and descriptor cautions together with the target
  shape; and only name the fallback gate unless MCP has actually failed in the
  current task.
- Validator summaries are summary-first by default. Missing per-result
  `resolvedMembers`, `toolHealth`, or `resolutionTrace` is not proof that the
  detail does not exist; request it as `references/validator-fallbacks.md`
  describes (`resolutionTrace` needs `explain: true`) before falling back when
  exact validator detail matters.
- On unobfuscated versions, read structured
  `mappingContext.unobfuscatedRuntime` and `mappingContext.runtimeValidated`
  flags instead of pattern-matching former warning sentences;
  `get-class-api-matrix` reports `result.unobfuscatedRuntime: true`.
- Bound lifecycle scans explicitly with `fromVersion`, `toVersion`,
  `maxVersions`, `includeTimeline`, and `includeSnapshots` when the task needs
  a narrow history. The current MCP default scan is broad enough that old implicit
  five-version assumptions are unsafe.
- Keep version and mapping discipline.
  - Pass `projectPath`, `preferProjectVersion=true`, and `preferProjectMapping=true` when supported.
  - `analyze-symbol` can infer an omitted `version` from `projectPath`;
    record the returned `versionInference { version, source }` and warning
    when you rely on it. An explicit `version` still wins.
  - Still pass explicit `version` to tools that require it, such as `validate-access-widener` and `resolve-workspace-symbol`. `validate-mixin` can omit `version` only when `input.mode="project"`, or when `preferProjectVersion: true` is sent with `projectPath`.
  - Prefer direct `target` addressing for `get-class-source`,
    `get-class-members`, and flat artifact tools, with top-level `projectPath`
    when the target needs workspace context. Use `resolve-artifact` first and
    pass `artifactId` when later calls need a shared indexed artifact.
  - An access widener or transformer verdict marked `approximate: true`, or
    provenance with `versionApproximated` or `loaderMismatch`, is not exact
    validation for the requested version; `references/validator-fallbacks.md`
    owns the handling.
- Parallelize only independent read-only discovery calls once `projectPath`, loader, version, and mapping are known.
  - Keep dependent chains sequential.
  - Do not run `manage-cache`, `index-artifact`, or remap/mutating flows in parallel with calls that depend on the same cache or JAR.
- If payload shape is unclear or an entry tool errors, read `references/mcp-recipes.md` before inventing fields or dropping to a lower-level tool.
- Apply the MCP failure budget.
  - If a high-level read tool fails with a worker restart, timeout, or transport
    error, retry once with a narrower high-level payload.
  - A client-side timeout on the first lookup after an MCP upgrade can be a
    one-time re-index of that artifact (artifactIds derive from jar content,
    and nothing bounds that first call end to end), not stale cache or an
    unavailable MCP. Do not prune the cache or declare MCP unavailable for it.
    Keep the same `target` or returned `artifactId` for the one budgeted retry,
    narrowing only the rest of the payload; the persisted index lets that retry
    skip the re-index. Do not add retries beyond the budget.
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
    `ERR_LIMIT_EXCEEDED` because its request queue is full, wait or narrow the
    request instead of queuing more validator work. An `ERR_LIMIT_EXCEEDED`
    whose `error.hints` name `MCP_MAX_DOWNLOAD_BYTES` is the download size cap
    instead, and nested class scanning skips an unusable Jar-in-Jar inner jar
    (oversized ones included) without an error; waiting or narrowing helps
    neither, so follow
    `references/mcp-unavailable-fallback.md`.
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
  - Read `error.retryClass` and `error.issueOrigin` separately on every
    failure; `issueOrigin` (`code_issue`, `tool_issue`, `environment`) can
    differ per response for the same code. `retryClass: "permanent"` (for
    example `ERR_CLASS_NOT_FOUND` or `ERR_WORKSPACE_VERSION_UNRESOLVED`) means
    the identical call cannot succeed: change the request from verified
    evidence or record the fact as unverified, never replay it.
    `retryClass: "environment"` (`ERR_JAVA_UNAVAILABLE`,
    `ERR_DECOMPILER_UNAVAILABLE`, `ERR_DECOMPILER_FAILED`,
    `ERR_REMAPPER_UNAVAILABLE`, `ERR_REGISTRY_GENERATION_FAILED`) means a host
    capability is unavailable or failing: read the specific code and report it
    to the user instead of replaying the call.
  - `ERR_CONTEXT_UNRESOLVED` whose `error.hints` name `gradleUserHome` is the
    access widener/transformer loader-mismatch refusal owned by
    `references/validator-fallbacks.md`, a different case from the one below.
  - `ERR_CONTEXT_UNRESOLVED` on an artifact with no binary jar can report
    `retryClass: "input"` with `issueOrigin: "tool_issue"` when the tool chose
    that artifact. Act on `issueOrigin`: do not "fix the payload" and replay the
    same artifact. Check it with `manage-cache` `action: "inspect"`,
    `selector: { artifactId }`, and `include: ["cacheEntries"]`, then read
    `result.cacheEntries[].meta.binaryJarPath`, or target an explicit jar path.
  - If you fall back, mark facts from that path as fallback-verified, not MCP-verified.
