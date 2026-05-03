# Common Task Checklists

Start with the matching high-level recipe in `references/mcp-recipes.md`, then use the checklist below to make sure the delivered slice is actually complete.

## Table of Contents

1. [Simple Block or Item](#simple-block-or-item)
2. [Container Block or Block Entity](#container-block-or-block-entity)
3. [Entity or Mob](#entity-or-mob)
4. [Mixin, Access Widener, or Access Transformer](#mixin-access-widener-or-access-transformer)
5. [Worldgen or Data-Driven Content](#worldgen-or-data-driven-content)
6. [HUD, Screens, or Client Rendering](#hud-screens-or-client-rendering)
7. [Projectile, Targeting, or Homing Logic](#projectile-targeting-or-homing-logic)
8. [GameTest or Runtime Test Harness](#gametest-or-runtime-test-harness)
9. [Porting or Compatibility Fixes](#porting-or-compatibility-fixes)
10. [Mod JAR Analysis](#mod-jar-analysis)
11. [NBT or Save Data](#nbt-or-save-data)

## Simple Block or Item

Deliverables:

- Register the block or item.
- Register the `BlockItem` separately unless the project helper already does it.
- Add the creative tab entry if the project uses one.
- Add `blockstates`, models, loot tables, and lang keys as needed.
- Update datagen providers instead of hand-writing JSON if the project already uses datagen.
- Add tags, recipes, or advancements when the request implies them.
- In Architectury, keep the slice in `common` only when the workspace already uses loader-agnostic registry helpers there.

Vanilla anchors:

- A simple solid block or simple consumable item of the same category.
- The matching vanilla JSON layout for blockstates, item models, and loot tables.

Common misses:

- Missing `BlockItem`
- Missing loot table
- Wrong asset path or casing
- Registration performed in the wrong lifecycle phase

## Container Block or Block Entity

Deliverables:

- Block registration
- Block entity type and implementation
- Menu or container type
- Screen and screen registration when the UI is visible
- Data sync or menu slots needed for interaction
- Save and load logic for persistent state
- Blockstate, models, loot table, and lang entries

Vanilla anchors:

- `ChestBlock`, `ChestBlockEntity`, `ChestMenu`, `ChestScreen`
- `BarrelBlock` for a simpler container pattern
- `FurnaceBlock` when progress bars or recipes are involved

Common misses:

- Screen registered on the wrong side
- Missing block entity ticker or sync path
- Menu type not registered
- Interaction opening the UI on the client instead of the server

## Entity or Mob

Deliverables:

- `EntityType` registration
- Entity class
- Attributes
- Renderer
- Model or render layer definition
- Client-side registration
- Spawn egg if the request wants one
- AI goals or brain setup
- Lang entries and placeholder texture paths if art is missing
- Spawn rules or spawn placement when relevant

Vanilla anchors:

- The nearest vanilla mob, renderer, and model pipeline
- Vanilla attribute and goal setup for the same behavior style

Common misses:

- Attributes not registered
- Renderer registered on the wrong side
- Spawn egg created without a registered entity type
- Goals added but navigation or target selectors left unconfigured

## Mixin, Access Widener, or Access Transformer

Recipe:

- Start with `validate-project`. Pass `discover: ["mixins", "access-wideners", "access-transformers"]` when you want a whole-workspace read, and drop entries that do not apply to the loader.
- For Fabric workspaces, drop to `validate-mixin` or `validate-access-widener` only when you need exact issue detail.
- For NeoForge workspaces, drop to `validate-access-transformer` with an explicit `atNamespace` when the project-level summary flags an AT entry.

Checklist:

- Prefer a loader event or API hook over a Mixin when one exists.
- Prefer accessor or invoker Mixins when field or method access is the only goal.
- Record the exact owner, method name, descriptor, and mapping namespace before writing the change.
- Update the mixin config, access widener, or `neoforge.mods.toml` access transformer declaration together with the code change.
- Read the target class source to confirm the injection point or member still exists in this Minecraft version.
- For access transformers, match `atNamespace` to the actual file (`mojang` on modern NeoForge, `srg` on legacy Forge projects). Mixed-namespace files are a frequent cause of silent AT no-ops.

Common misses:

- Wrong mapping namespace
- Wrong descriptor
- Injection point moved in the target version
- Client-only targets referenced from common code
- Access transformer entry using `srg` names on a modern NeoForge (mojmap) workspace, or vice versa
- NeoForge AT file added but not declared in `neoforge.mods.toml`

## Worldgen or Data-Driven Content

Deliverables:

- Configured feature, placed feature, biome modifier, or loader-specific hook
- Registry keys and registration
- Data JSON or datagen providers for worldgen assets
- Tags, loot tables, lang keys, or recipes if the feature introduces new content

Vanilla anchors:

- The nearest vanilla ore, structure, biome modifier, or placed feature path
- The relevant registry entries and vanilla JSON layout
- Before writing worldgen JSON, identify one same-version vanilla configured
  feature and one same-version vanilla placed feature.
- List the fields intentionally changed from vanilla.

Verification:

- Run MCP project or resource validation when available.
- If MCP is unavailable, compare against same-version vanilla resources and run
  the lightest resource-load path available: existing GameTest, configured
  datagen/resource validation, platform run task, or `runClient`.
- Do not mark natural generation, loot, item model definitions, biome modifiers,
  or registry resources as working from `./gradlew build` alone.
- Treat runtime log lines such as `Failed to parse either`, `No key ...`, and
  `Unknown registry key ...` as codec or schema mismatches until proven
  otherwise.

Common misses:

- Wrong registry key namespace
- Data files in the wrong folder
- Feature registered but never injected into biome generation
- Old worldgen API copied into a newer Minecraft version
- Build passes but runtime registry/resource load fails
- Vanilla JSON from a different Minecraft version copied into the current version

## HUD, Screens, or Client Rendering

Recipe:

- Read `references/rendering-hud.md` before changing projection math, HUD event
  registration, GUI scale handling, or screen tooltip/render flow.
- Use MCP or workspace source to verify the relevant vanilla/client method signature before copying examples.

Checklist:

- Keep client-only imports behind client entrypoints or client-only platform modules.
- Separate fixed 2D overlay math from world-to-screen projection.
- Record world position, camera position, front/behind-camera decision,
  projected coordinates, GUI-scaled pixels, and clamp behavior for entity
  markers.
- For Minecraft 1.21.x, prefer a verified helper such as `GameRenderer.projectPointToScreen(Vec3)` when available.
- Do not pass partial tick to an API that expects FOV degrees.
- Check bow draw, zoom, GUI scale, off-screen targets, and behind-camera targets.
- Restore render state such as blend, depth, shader color, and pose stack balance when the workspace APIs require it.

Common misses:

- Renderer registered on the wrong side
- Screen or HUD event only wired for one loader in a multi-loader project
- Projection uses stale or incomplete FOV state
- Marker appears only at screen edges because NDC or GUI scaling is wrong
- Unit tests cover math but no runtime visual state was verified

## Projectile, Targeting, or Homing Logic

Checklist:

- Separate pure Java targeting math from runtime entity, projectile, and event behavior.
- Verify projectile spawn hooks, entity hit callbacks, damage source behavior,
  and enchantment/event side effects in the target Minecraft version.
- Record server/client authority. Client-side reticles or previews must not be treated as server targeting proof.
- Use unit tests for scoring, ranges, priorities, and serialization.
- Use GameTest or runtime launch for projectile spawn, entity hit, Mixin injection, loader event, or networking behavior.
- For HUD indicators tied to targets, also run the HUD checklist.

Common misses:

- Unit tests pass but loader event wiring never fires
- Homing or lock-on state stored on the wrong side
- Projectile helper bypasses vanilla hooks or enchantment callbacks
- Target filtering differs between preview HUD and server logic

## GameTest or Runtime Test Harness

Recipe:

- Read `references/gametest.md`.
- Confirm which loader runtime the test task exercises before treating it as coverage.

Checklist:

- Identify the GameTest source set, entrypoint/discovery path, and run task.
- Confirm common classes and resources are visible to the test runtime.
- For Fabric, check whether `fabric-gametest` entrypoint overlay is required.
- For Architectury, check source set grouping before debugging access widener resolution.
- For NeoForge, verify the NeoForge-specific run task and discovery path.
- Record which loader passed and which loader remains unverified.

Common misses:

- Test source set is treated as a separate mod and cannot see the common access widener
- Fabric GameTest pass is treated as proof of NeoForge event or AT behavior
- Runtime registry/resource load is not exercised by ordinary unit tests

## Porting or Compatibility Fixes

Recipe:

- Start with `compare-minecraft` or `analyze-symbol`.
- Use lower-level diffs only for the class or symbol that actually broke.

Checklist:

- Update mappings before changing logic that might already be correct.
- Check loader lifecycle changes across the source and target versions.
- Revalidate Mixins, access wideners, registry names, and resource paths after the port.
- If the failure is a removed symbol, say so explicitly and name the verified replacement or closest alternative.

Common misses:

- Old method names copied into a new mapping namespace
- Loader lifecycle changes across versions
- Registry bootstrap moved or renamed
- Vanilla method signatures changed without obvious compile errors

## Mod JAR Analysis

Recipe:

- Start with `analyze-mod` summary.
- Use search, decompile, class source, or remap preview only after metadata confirms the JAR is the right target.

Checklist:

- Confirm loader, modid, version, dependencies, and mixin configs first.
- Check that the JAR matches the same Minecraft version and loader family as the user's workspace.
- Prefer remap preview before any mutating remap action.
- Cross-check suspicious targets against vanilla source and the user's current version.

Common misses:

- Looking at the wrong loader build of the same mod
- Comparing against a different Minecraft version
- Assuming a dependency is optional when the metadata marks it required

## NBT or Save Data

Recipe:

- Decode with `nbt-to-json` (`compression: "auto"`) to get typed JSON.
- Edit in typed JSON directly, or apply `nbt-apply-json-patch` with RFC6902 operations for structural changes.
- Re-encode once with `json-to-nbt`, matching the original compression format.

Checklist:

- Identify the source (level.dat, chunk region, playerdata, `/data` command output, datapack fixture, datagen artifact) before editing, since compression and expected fields differ per source.
- **Back up the original binary before editing live save data.** Minecraft does not version these files; a bad re-encode is not recoverable, so always work against a copy and keep the original untouched until the edited output has been re-decoded and verified.
- **Stop on `.mca` region containers.** These helpers operate on raw NBT payloads, not Anvil region files. If the target is an `.mca`, extract the chunk payload with a region tool first, or abort and say the input is unsupported.
- Preserve `DataVersion` unless the edit is a deliberate upgrade. A mismatched `DataVersion` triggers Minecraft's auto-upgrade path, which may rewrite nearby fields.
- For level.dat and playerdata, expect `gzip` compression. For `/data` command output, expect plain (no compression).
- Preserve the typed-JSON envelope `{ "rootName", "root": { "type", "value" } }` returned by `nbt-to-json`. `json-to-nbt` rejects a bare `{ type, value }` document, and `nbt-apply-json-patch` paths must start at `/root/...`.
- When building test fixtures, check in the typed JSON form and re-encode at runtime or build time instead of committing binary NBT blobs.
- For registry-shaped data (items, blocks, biome feature keys), cross-check against `get-registry-data` for the same version before writing non-trivial values.

Common misses:

- Editing the raw NBT binary by hand instead of round-tripping through typed JSON
- Re-encoding without matching the source compression
- Dropping the `rootName` / `root` envelope when editing typed JSON
- Running helpers directly on `.mca` region files
- Editing live save data without a pre-edit backup
- Bumping `DataVersion` silently during an unrelated edit
- Hardcoding registry IDs that have been renamed in the target version
