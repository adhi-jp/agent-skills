---
version: 2.0.0
name: minecraft-modding-workbench
description: >
  Use when building, debugging, porting, or inspecting Minecraft Java Edition
  mods for Fabric, NeoForge, or Architectury, including Mixins, access
  wideners, access transformers, mappings, registry/resource issues, NBT
  payloads, mod JAR inspection, remapping, version migration, dependency API
  source lookup, GameTest wiring, client screens, HUD rendering, or runtime
  logs. Also use as a side reference when another planning, execution, or
  review skill is active and the work depends on Minecraft API facts.
---

# Minecraft Modding Workbench

Support fast, version-aware Minecraft modding. Treat the `minecraft-modding`
MCP server as the primary source of truth, then turn verified findings into
working code and assets.

## Scope

- Supports Fabric, NeoForge, and Architectury.
- Requires the `minecraft-modding` MCP server from `@adhisang/minecraft-modding-mcp`.
- Prefer project-aware MCP calls when a workspace exists. Reuse the repository root as `projectPath`.
- Use the high-level MCP 6.3.0 workflow tools first: `inspect-minecraft`,
  `analyze-symbol`, `compare-minecraft`, `validate-project`, `analyze-mod`,
  and `manage-cache`.
- Also use the MCP 6.3.0 validation and batch helpers when they fit:
  `verify-mixin-target` for one-call Mixin owner/member checks and
  accessor/invoker advice, and `batch-class-source`, `batch-class-members`,
  `batch-symbol-exists`, or `batch-mappings` for fixed shortlists that share
  one resolved artifact or Minecraft version.
- Covers Forge-style access transformers through `validate-project` (task `access-transformer`) for NeoForge, in addition to Fabric-style access wideners.
- Use the NBT helpers (`nbt-to-json`, `json-to-nbt`, `nbt-apply-json-patch`) when working with level.dat, chunk, playerdata, or command-driven NBT. Stay in typed JSON while editing and re-encode once at the end.

## Default Behavior

- Produce runnable feature slices, not generic advice.
- Infer loader, version, mappings, modid, package, Java version, and project conventions from the workspace before asking questions.
- Ask only the minimum blocking question when the workspace is absent or contradictory.
- Prefer explicit TODOs or placeholder assets over stalling on art or balance details.
- When the user clearly requests implementation rather than explanation, default to delivering code.
- Respond in the user's language when practical, but keep the workflow and trigger logic language-agnostic.
- Separate facts by verification source when the answer will guide later
  implementation: `Verified by MCP`, `Verified by workspace/source jar
  fallback`, `Runtime/user-observed`, and `Unverified`.

## Implementation-Guiding Output Contract

For plans, debugging explanations, MCP payload/error-recovery answers, eval
answers, and handoffs that guide later implementation, make the provenance
visible before giving version-sensitive recommendations:

- `Project profile`: record confirmed workspace root, loader(s), Minecraft
  version, mapping namespace, Java version, modid, and base package when they
  matter. If no workspace or file evidence is available, explicitly mark the
  missing or assumed fields before using prompt-provided versions as examples.
- `MCP status`: record preflight/schema status before MCP-dependent claims. If
  tools have not actually run, call the MCP step planned or unverified instead
  of writing as if results are known.
- `Verification sources`: separate implementation facts under `Verified by
  MCP`, `Verified by workspace/source jar fallback`, `Runtime/user-observed`,
  and `Unverified`. For fallback/error-recovery tasks or eval-style answers,
  include empty categories as `none yet` when omitting them would blur the
  source boundary.
- `Reference route`: for substantial plans or debugging routes, name the
  loaded references and the relevant skipped categories briefly.

## Quick Path

1. Read or build the project profile: workspace root, loader, Minecraft
   version, mapping, Java version, modules, and normal verification commands.
   If the workspace is absent, record the missing profile facts before making
   version-, loader-, mapping-, or Java-sensitive claims.
2. Run MCP preflight before assuming `minecraft-modding` tools are callable.
3. Use one high-level MCP call first for the relevant fact.
4. Choose a narrow reference route before loading bundled references. Once the
   task shape is known, start with its checklist section and add loader, MCP
   recipe, fallback, or task-specific references only when their conditions match.
5. If a worker restart, timeout, or transport failure occurs, retry once with a
   narrower high-level payload, then switch to the matching fallback playbook.
6. For invalid payloads, consult only the relevant `references/mcp-recipes.md`
   recipe, correct the shape once, and retry the same high-level tool before
   changing tools.
7. For Mixins, access wideners, and access transformers, record owner, name,
   descriptor, namespace, config declaration, and side before editing.
8. For resources, worldgen, loot, models, codecs, HUD, screens, and runtime
   hooks, run the task-specific checklist instead of treating `build` as proof
   of runtime behavior.

## MCP Preflight

Run this once near the start of a Minecraft modding task, before the first MCP-dependent claim:

1. Check whether the host exposes `minecraft-modding` tools and inspect the
   callable schema before the first request, especially `inspect-minecraft`,
   `analyze-symbol`, and their transformed callable names.
2. Record the available high-level tool names, workspace root to use as
   `projectPath`, detected Minecraft version, loader, mapping, and Java version.
3. If neither `inspect-minecraft` nor `analyze-symbol` is available, say
   `minecraft-modding MCP unavailable` once and switch to
   `references/mcp-unavailable-fallback.md`.
4. If a named MCP 6.3.0 tool or argument from this skill is rejected as unknown, treat
   the installed MCP as older than these recipes or version-skewed and use the nearest
   older-compatible path or workspace fallback. Do not keep guessing tool names.
5. If MCP is available, prefer project-aware calls with `projectPath`,
   `preferProjectVersion`, and `preferProjectMapping` when the current tool
   accepts those fields.

## First Pass

1. Detect the project shape.
   - Read `gradle.properties`, `build.gradle`, `build.gradle.kts`, `settings.gradle`, `fabric.mod.json`, `neoforge.mods.toml`, mixin configs, and nearby registration classes.
   - Infer loader, Minecraft version, mappings, Java version, modid, base package, whether the project already uses datagen, and whether the workspace is single-loader or Architectury multi-module.
   - Record the workspace root you will pass as `projectPath` to MCP tools.
2. Read the existing code before writing new code.
   - Match the project's naming, package layout, registration helpers, and client/server split.
   - Reuse existing registries, tabs, packet patterns, and datagen providers when present.
   - Prefer workspace-aware MCP resolution before manual version or mapping selection.
3. Load only the relevant references using the Reference Routing section below.
4. Find the closest vanilla example before implementing behavior.
   - Start with `inspect-minecraft` or `analyze-symbol`.
   - Drop to low-level tools only when the high-level answer still leaves the implementation ambiguous.

If no project exists yet, ask only for loader, Minecraft version, modid, and package name.
For explanation-only tasks with no workspace access, list those facts as missing
or assumed before giving examples.
If the task depends on an external generator or template that is not present, say so explicitly instead of fabricating generated files.

## Reference Routing

Bundled references are optional, conditional context. Do not read or restate the
whole reference bundle just because this skill triggered.

- Default route:
  - Use `SKILL.md`, the project profile, MCP preflight, and one high-level MCP
    lookup when available.
  - Read only the matching section of `references/task-checklists.md` once the
    task shape is known.
- Loader route:
  - Read `references/fabric.md` only for Fabric project structure,
    registration, APIs, entrypoints, datagen, networking, Mixins, or pitfalls.
  - Read `references/neoforge.md` only for NeoForge project structure,
    DeferredRegister, events, capabilities, access transformers, datagen,
    networking, sided access, or pitfalls.
  - Read `references/architectury.md` only for Architectury multi-module
    placement or a slice that crosses common/platform boundaries.
  - Read multiple loader references only when the workspace is multi-loader and
    the changed slice touches those loaders.
- MCP recipe route:
  - Read `references/mcp-recipes.md` only for payload shape, high-level tool
    error recovery, `ERR_INVALID_INPUT`, old-shape/current-shape mismatch, or a
    supporting utility not covered by the high-level call.
  - If a high-level MCP answer is sufficient, do not restate unrelated recipes.
- Fallback route:
  - Read `references/mcp-unavailable-fallback.md` only after preflight shows no
    MCP tools, a named tool or argument is rejected as older MCP, or the failure
    budget routes to fallback.
  - Read `references/validator-fallbacks.md` only after `validate-project`,
    `validate-mixin`, `validate-access-widener`, or
    `validate-access-transformer` is unavailable, restarts, times out, or cannot
    answer.
- Task-specific route:
  - Read `references/dependency-jars.md` for dependency API source lookup.
  - Read `references/rendering-hud.md` for HUD overlays, screens, projection,
    GUI scale, FOV, or client rendering.
  - Read `references/gametest.md` for GameTest or test-harness wiring.
  - Read `references/bootstrap-from-template.md` only for sparse templates.
  - Read `references/project-profile-template.md` when a durable project profile
    is useful.
  - Read `references/subagent-mcp-contract.md` only when delegating Minecraft
    work to another agent.

For substantial plans, debugging explanations, eval outputs, or handoffs where
reference choices affect implementation facts, include a brief reference-route
record: loaded references with reasons, plus skipped reference categories with
reasons. Keep it short; it is provenance, not a summary of every skipped file.

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
  answer narrow: record project profile, MCP status, all four verification
  source labels, and the reference route; say that callable schema must be
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

## Unsupported or Risky Requests

- Do not silently treat Quilt or legacy Forge as Fabric, NeoForge, or Architectury.
- For legacy Forge-only or other unsupported loaders, limit help to verified workspace facts, logs, and migration boundaries. Say that full guidance is outside this skill.
- If MCP is unavailable, misconfigured, or stale, say so immediately, fall back to workspace and log inspection, and keep any fix narrow. The same rule covers version skew: if an MCP 6.3.0 tool, task, response-shaping argument, or input shape this skill names (for example, `detail` / `include[]`, `manage-cache` `action: "verify"`, `validate-project` task `access-transformer`, `analyze-symbol` lifecycle range controls, `get-class-source` / `get-class-members` `target.kind`, or the NBT helpers) is rejected as unknown, treat it as evidence that the installed MCP is older than what this skill's recipes target, say so explicitly, and route the request through the nearest older-compatible tool or a workspace-only fallback rather than fabricating a different payload shape.
- If workspace files contradict the prompt, call out the contradiction and resolve it from checked files before coding.
- If the request depends on a symbol, event, registry entry, or vanilla hook you cannot verify, say that it is unverified or unsupported instead of inventing it. Offer the closest verified alternative.

## Core Workflow

1. Inspect vanilla or existing mod code that already solves the same problem.
2. Translate that pattern into the user's loader, module boundary, and mapping namespace.
3. If the template is too empty, bootstrap the missing project skeleton first.
   - Add only the minimum entrypoints, registration classes, client hooks, and datagen wiring needed for the requested feature.
   - Do not create every possible system up front.
4. Implement the whole slice in one pass.
   - Include registrations.
   - Include client wiring when needed.
   - Include required JSON resources or datagen hooks.
   - Include lang keys, loot tables, blockstates, models, tags, recipes, or screen wiring when the feature needs them.
   - In Architectury workspaces, keep shared gameplay logic in `common` and loader-specific wiring in platform modules unless the workspace already uses another verified pattern.
5. Run the verification loop before calling the task done.
6. Report assumptions, placeholders, follow-up tasks, and verification sources briefly.

## Delivery Rules

- Match the current project style before introducing a new abstraction.
- Do not invent mapping names, event names, registration order, or descriptors. Verify them.
- Prefer stable loader APIs or events over Mixins when the loader already exposes a clean hook.
- When the project is template-only, create the smallest working scaffold that can compile and host the requested feature.
- In Architectury projects, keep code in `common` by default and move only loader-bound code to `fabric` or `neoforge`.
- In Architectury templates that already route both loaders through a shared init method, do not add no-op platform edits just to mirror a shared content change.
- Use `@ExpectPlatform`, Architectury abstractions, or a plain Java interface/service split only when the code truly needs platform-specific behavior.
- Keep side separation correct. Put renderer, screen, and other client-only code behind the proper client entrypoint or event.
- Prefer datagen when the request creates repeated JSON or more than a couple of content entries.
- Preserve existing helper classes, registries, and package structure instead of replacing them wholesale.
- Keep fixes narrow during debugging. Identify the concrete failure first, then patch the cause.

## Verification Loop

Run verification as part of the default workflow, not as an optional extra.

1. Run `./gradlew build` after structural code changes.
2. Run the loader's datagen task when datagen was added or updated, or when generated resources are the project's normal asset path.
   - Fabric: `./gradlew runDatagen`
   - NeoForge: run the project's configured datagen task or run configuration.
   - Architectury: run the root build and the relevant platform datagen task when the workspace defines one.
3. Treat resource-heavy and runtime-heavy changes as more than compile checks.
   - For worldgen, loot tables, item model definitions, biome modifiers, recipe
     serializers, registry resources, access wideners, and access transformers,
     do not mark the work as working from `build` alone.
   - Use MCP resource or project validation when available. If unavailable,
     compare against at least one vanilla resource from the same Minecraft
     version, then use the lightest resource-load path available: focused
     GameTest, configured datagen/resource validation, platform run task, or
     `runClient`.
4. Run a client launch when the change touches rendering, menus, screens, entity models, HUD overlays, or runtime-only behavior and the environment allows it.
   - Use the project's existing `runClient` task or equivalent.
   - In Architectury workspaces, prefer the platform-specific client run task that exercises the changed module.
   - For HUD and projection work, capture runtime evidence when possible and
     check center, edge, behind-camera, close/far target, GUI scale, and bow/FOV
     states.
5. Run or extend automated tests when the project already has them or when the new logic is isolated enough to justify them.
   - Prefer existing GameTests, loader test harnesses, or integration tests for gameplay behavior.
   - Add focused unit tests for pure Java helpers, codecs, serializers, or data transforms.
6. If a command cannot run in the current environment, say so explicitly and still perform static validation with MCP tools and code inspection.
   - In sandboxed environments, retry Gradle with a writable `GRADLE_USER_HOME` before treating home-directory lock or cache failures as project issues.

At minimum, aim to leave the project in a state that passes `build` or has a concrete, localized reason why it cannot.

## Fast Debugging Order

- Mixin crash: start with `validate-project`, then `verify-mixin-target` for one owner/member probe or `validate-mixin` when source/config validation is needed. Use `reportMode: "full"` or `explain: true` before deciding validator detail is unavailable. Confirm the owner, method name, descriptor, and mapping namespace before patching code.
- Access widener failure (Fabric): start with `validate-project`, then `validate-access-widener` with an explicit `version`. Confirm that the header namespace matches the entry names. If Fabric GameTests fail before discovery because a common access widener is not found, treat it as test runtime wiring first: record the loader runtime, GameTest source set, `fabric-gametest` entrypoint/discovery path, Loom `mods` sourceSet grouping, and common resource visibility before changing feature code.
- Access transformer failure (NeoForge): start with `validate-project` (task `access-transformer`), then `validate-access-transformer` with an explicit `version` and `atNamespace`. Confirm the file's entry namespace matches what the workspace expects (usually `mojang` on modern NeoForge, `srg` on legacy projects).
- Registry or missing-content issue: inspect the existing registration flow, confirm registry IDs, then check required resource files. `get-registry-data` returns the vanilla-version entry list only; absence from its output is not evidence of a missing modded, dependency, or datapack entry, so fall back to workspace registration code, dependency metadata, and datagen output for those cases. For exact `assets/**` or `data/**` files inside vanilla or mod artifacts, use `get-artifact-file`; `list-artifact-files` only indexes Java source paths, and `deliveryMode: "jar-read-through"` means the file came directly from the backing jar.
- Registry loading error: treat `Failed to parse either`, `No key ...`, and
  `Unknown registry key ...` as resource codec or schema mismatch until proven
  otherwise. For worldgen JSON, compare against one same-version vanilla
  configured feature and one same-version vanilla placed feature even when the
  log names only `configured_feature`, then record which fields were
  intentionally changed before broad edits or replacement JSON examples.
- Dependency API uncertainty: first try dependency targets on `get-class-source` / `get-class-members`, or `find-class` with top-level `projectPath` when you only know a simple or qualified class name in a workspace-resolved dependency. Read `references/dependency-jars.md` before manual cache scanning. Treat Fabric API umbrella jars and other Jar-in-Jar shells through `qualityFlags: ["shell-jar"]`, `provenance.nestedJars`, nested `find-class` search, and unique nested-jar redirects; if MCP returns `ERR_NESTED_JAR_AMBIGUOUS`, choose from `nestedJarCandidates` instead of guessing.
- HUD, screen, or projection bug: read `references/rendering-hud.md` before changing math or render registration.
- NBT payload corruption or schema drift: decode with `nbt-to-json`, edit in typed JSON (or `nbt-apply-json-patch`), preserve `DataVersion`, then re-encode with `json-to-nbt` using matching compression.
- Cache or index anomalies: read `get-runtime-metrics` before mutating anything, then run `manage-cache` with `action: "verify"` in preview mode before `prune`, `rebuild`, or `delete`.
- Texture or model issue: verify resource location casing, JSON paths, generated assets, and item-block model linkage.
- Side-only crash: inspect client init, renderer registration, and `level.isClientSide()` or equivalent boundaries.
- Porting failure: start with `compare-minecraft`, then diff the affected class signatures, then update mappings and loader-specific APIs.

When one of these categories matches, read the corresponding section in `references/task-checklists.md` and the loader-specific `Common Pitfalls` section before broad rewrites.

## References

- Fabric patterns: `references/fabric.md`
- NeoForge patterns: `references/neoforge.md`
- Architectury patterns: `references/architectury.md`
- Template bootstrap patterns: `references/bootstrap-from-template.md`
- Delivery checklists by task shape: `references/task-checklists.md`
- MCP payload and recovery recipes: `references/mcp-recipes.md`
- MCP unavailable fallback: `references/mcp-unavailable-fallback.md`
- Dependency API source lookup: `references/dependency-jars.md`
- HUD and client rendering: `references/rendering-hud.md`
- Validator fallbacks: `references/validator-fallbacks.md`
- GameTest wiring: `references/gametest.md`
- Project profile template: `references/project-profile-template.md`
- Subagent MCP contract: `references/subagent-mcp-contract.md`
- For current upstream migration guidance, consult the official Fabric, NeoForge, and Architectury docs or release notes that match the target loader and Minecraft version instead of relying on hardcoded URLs.
