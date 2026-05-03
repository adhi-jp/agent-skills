---
version: 1.1.1
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
- Use the high-level v3 entry tools first: `inspect-minecraft`, `analyze-symbol`, `compare-minecraft`, `validate-project`, `analyze-mod`, and `manage-cache`.
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
  fallback`, and `Runtime/user-observed`.

## Quick Path

1. Read or build the project profile: workspace root, loader, Minecraft
   version, mapping, Java version, modules, and normal verification commands.
2. Run MCP preflight before assuming `minecraft-modding` tools are callable.
3. Use one high-level MCP call first for the relevant fact.
4. If a worker restart, timeout, or transport failure occurs, retry once with a
   narrower high-level payload, then switch to the matching fallback playbook.
5. For invalid payloads, read `references/mcp-recipes.md`, correct the shape
   once, and retry the same high-level tool before changing tools.
6. For Mixins, access wideners, and access transformers, record owner, name,
   descriptor, namespace, config declaration, and side before editing.
7. For resources, worldgen, loot, models, codecs, HUD, screens, and runtime
   hooks, run the task-specific checklist instead of treating `build` as proof
   of runtime behavior.

## MCP Preflight

Run this once near the start of a Minecraft modding task, before the first MCP-dependent claim:

1. Check whether the host exposes `minecraft-modding` tools, especially
   `inspect-minecraft` and `analyze-symbol` or their transformed callable names.
2. Record the available high-level tool names, workspace root to use as
   `projectPath`, detected Minecraft version, loader, mapping, and Java version.
3. If neither `inspect-minecraft` nor `analyze-symbol` is available, say
   `minecraft-modding MCP unavailable` once and switch to
   `references/mcp-unavailable-fallback.md`.
4. If a named tool or argument from this skill is rejected as unknown, treat the
   installed MCP as older than these recipes and use the nearest
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
3. Load only the relevant references.
   - Read `references/fabric.md` for Fabric projects.
   - Read `references/neoforge.md` for NeoForge projects.
   - Read `references/architectury.md` for Architectury multi-module projects.
   - Read `references/bootstrap-from-template.md` when the workspace is a sparse template.
   - Read `references/task-checklists.md` for the requested feature slice.
   - Read `references/mcp-recipes.md` when payload shape, recovery, or sequencing is unclear.
   - Read `references/mcp-unavailable-fallback.md` when MCP tools are unavailable, stale, or repeatedly failing.
   - Read `references/dependency-jars.md` when checking Architectury, Fabric API, NeoForge, or other dependency classes.
   - Read `references/rendering-hud.md` for HUD overlays, screens, projection, GUI scale, FOV, or client rendering.
   - Read `references/validator-fallbacks.md` when `validate-project`, Mixin, access widener, or access transformer validators fail.
   - Read `references/gametest.md` when adding or debugging GameTest wiring.
4. Find the closest vanilla example before implementing behavior.
   - Start with `inspect-minecraft` or `analyze-symbol`.
   - Drop to low-level tools only when the high-level answer still leaves the implementation ambiguous.

If no project exists yet, ask only for loader, Minecraft version, modid, and package name.
If the task depends on an external generator or template that is not present, say so explicitly instead of fabricating generated files.

## MCP Guardrails

- Start with the highest-level read-only MCP call that can answer the question.
  - `inspect-minecraft`: versions, artifacts, vanilla classes, source search, raw files.
  - `analyze-symbol`: existence, mappings, lifecycle, workspace compile-time names, API overview.
  - `compare-minecraft`: migration and registry/class diffs.
  - `validate-project`: workspace, Mixin, access widener, and Forge-style access transformer validation.
  - `analyze-mod`: mod JAR summary, search, decompile, remap preview/apply.
  - `manage-cache`: stale cache or index diagnosis, including the `verify` action and preview-then-apply maintenance.
- Reach for these supporting utilities directly when the entry tools do not cover the job:
  - `get-registry-data`: structured registry bodies (blocks, items, biomes, …) via the server data generator for one version.
  - `get-runtime-metrics`: service counters and latency snapshots when cache, search, or index behaviour looks off.
  - `nbt-to-json`, `json-to-nbt`, `nbt-apply-json-patch`: typed-JSON round-trip and RFC6902-style in-place edits for Java Edition NBT payloads.
- Drop to low-level tools only for exact code, exact descriptors, raw registry bodies, detailed validator output, or direct JAR/remap control.
- Keep version and mapping discipline.
  - Pass `projectPath`, `preferProjectVersion=true`, and `preferProjectMapping=true` when supported.
  - Still pass explicit `version` to tools that require it, such as `validate-mixin`, `validate-access-widener`, and `resolve-workspace-symbol`.
  - Treat artifact-backed lookup as a two-step flow: `resolve-artifact` first, then `find-class`, `search-class-source`, `get-artifact-file`, or `list-artifact-files`.
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
  - If `ERR_INVALID_INPUT` occurs, read the reported field errors, correct the
    payload once using `references/mcp-recipes.md`, and retry the same
    high-level tool before changing tools.
  - If you fall back, mark facts from that path as fallback-verified, not MCP-verified.

## Unsupported or Risky Requests

- Do not silently treat Quilt or legacy Forge as Fabric, NeoForge, or Architectury.
- For legacy Forge-only or other unsupported loaders, limit help to verified workspace facts, logs, and migration boundaries. Say that full guidance is outside this skill.
- If MCP is unavailable, misconfigured, or stale, say so immediately, fall back to workspace and log inspection, and keep any fix narrow. The same rule covers version skew: if a tool, task, or argument this skill names (for example, `manage-cache` `action: "verify"`, `validate-project` task `access-transformer`, `analyze-symbol` `api-overview` / `exact-map`, the nested `inspect-minecraft subject.kind: "artifact"` shape, or the NBT helpers) is rejected as unknown, treat it as evidence that the installed MCP is older than what this skill's recipes target, say so explicitly, and route the request through the nearest older-compatible tool or a workspace-only fallback rather than fabricating a different payload shape.
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

- Mixin crash: start with `validate-project`, then `validate-mixin` if you need exact issue detail. Confirm the owner, method name, descriptor, and mapping namespace before patching code.
- Access widener failure (Fabric): start with `validate-project`, then `validate-access-widener` with an explicit `version`. Confirm that the header namespace matches the entry names.
- Access transformer failure (NeoForge): start with `validate-project` (task `access-transformer`), then `validate-access-transformer` with an explicit `version` and `atNamespace`. Confirm the file's entry namespace matches what the workspace expects (usually `mojang` on modern NeoForge, `srg` on legacy projects).
- Registry or missing-content issue: inspect the existing registration flow, confirm registry IDs, then check required resource files. `get-registry-data` returns the vanilla-version entry list only; absence from its output is not evidence of a missing modded, dependency, or datapack entry, so fall back to workspace registration code, dependency metadata, and datagen output for those cases.
- Registry loading error: treat `Failed to parse either`, `No key ...`, and
  `Unknown registry key ...` as resource codec or schema mismatch until proven
  otherwise. Compare against same-version vanilla JSON before broad edits.
- Dependency API uncertainty: read `references/dependency-jars.md` before manual
  cache scanning.
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
