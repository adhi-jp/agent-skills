# Verification and Fast Debugging

Read this reference before closing an implementation slice or when the task matches a Mixin, access, registry, resource-codec, dependency, HUD/rendering, NBT, cache, model, side-only, or porting failure category.

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
