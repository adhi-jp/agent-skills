---
version: 2.1.1
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

Read `references/mcp-guardrails.md` before detailed MCP payload construction,
expert/batch-tool selection, response-field interpretation, retry or fallback
decisions, or version/mapping-sensitive recommendations. Keep these invariants
visible:

- start with the highest-level read-only tool that can answer the fact;
- inspect callable schema and correct invalid input once before changing tools;
- retry one narrower high-level request only for bounded transport/restart
  failures, never an identical deterministic server fault;
- keep project version, mapping, artifact, and workspace provenance explicit;
- mark fallback facts as fallback-verified, not MCP-verified.


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

## Verification And Debugging Reference

Read `references/verification-and-debugging.md` before declaring an
implementation complete or when diagnosing Mixin/access, registry/resource
codec, dependency, HUD/rendering, GameTest, NBT, cache/index, model/texture,
side-only, or version-porting failures. It owns the detailed Gradle, datagen,
runtime, resource, and category-specific verification paths. A green build
alone is not runtime proof for resource-heavy or runtime-only changes.


## References

- Fabric patterns: `references/fabric.md`
- NeoForge patterns: `references/neoforge.md`
- Architectury patterns: `references/architectury.md`
- Template bootstrap patterns: `references/bootstrap-from-template.md`
- Delivery checklists by task shape: `references/task-checklists.md`
- MCP payload and recovery recipes: `references/mcp-recipes.md`
- Detailed MCP guardrails: `references/mcp-guardrails.md`
- MCP unavailable fallback: `references/mcp-unavailable-fallback.md`
- Dependency API source lookup: `references/dependency-jars.md`
- HUD and client rendering: `references/rendering-hud.md`
- Validator fallbacks: `references/validator-fallbacks.md`
- Verification and fast debugging: `references/verification-and-debugging.md`
- GameTest wiring: `references/gametest.md`
- Project profile template: `references/project-profile-template.md`
- Subagent MCP contract: `references/subagent-mcp-contract.md`
- For current upstream migration guidance, consult the official Fabric, NeoForge, and Architectury docs or release notes that match the target loader and Minecraft version instead of relying on hardcoded URLs.
