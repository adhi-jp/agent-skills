# Dependency JAR and Source Lookup

Use this file when checking API surfaces from Architectury, Fabric API,
NeoForge, or another mod dependency.

## Preferred Flow

1. Start with MCP when available.
   - Use `get-class-source` or `get-class-members` with
     `target: { kind: "dependency", group, name, versionFromProject: true }`
     and `projectPath` for loader or Fabric API classes when the workspace
     declares the dependency version.
   - Use `analyze-mod` for a dependency jar summary, metadata, search,
     bytecode-only `members`, class source, or remap preview.
   - Use direct `target` on `find-class`, `search-class-source`,
     `get-artifact-file`, `list-artifact-files`, and `index-artifact`. Add
     top-level `projectPath` when the dependency target has no explicit
     version (such as `versionFromProject`); resolving first to an `artifactId`
     is optional.
   - Dependency reads honor a non-obfuscated `mapping` only for source-backed
     jars (`qualityFlags` includes `"source-backed"`). Otherwise the response
     reports `mappingApplied: "obfuscated"`, the
     `"dependency-mapping-unverified"` flag, and a warning, and the names are
     the jar's compiled names; do not present them as remapped.
     `context.minecraftVersion: "unknown"` is expected for dependency
     artifacts, and `"binary-jar-no-classes"` marks a jar without classes.
   - Use workspace-aware symbol lookup for Minecraft classes that dependency
     APIs reference. If `analyze-symbol` infers `version` from `projectPath`,
     record the returned `versionInference` block and warning.
   - If the tool reports invalid input, fix the payload once with
     `mcp-recipes.md`.
2. If MCP cannot answer, inspect Gradle dependency declarations.
   - Check root and module `build.gradle` or `build.gradle.kts`.
   - Check `gradle.properties` for version variables.
   - Confirm which module sees the dependency at compile time.
3. Locate the dependency in Gradle caches.
   - Typical path:
     `~/.gradle/caches/modules-2/files-2.1/<group>/<artifact>/<version>/`
   - Prefer `*-sources.jar` over bytecode.
   - Use the binary jar only when source is absent.
4. Confirm the exact class, method, or resource.
   - MCP `ERR_CLASS_NOT_FOUND` `error.didYouMean[]` entries are candidate
     hints; verify any chosen class before editing imports or descriptors.
     Candidates come from the requested artifact and the artifact the lookup
     ended on; an entry carrying its own `artifactId` was found in that other
     artifact, so query it there.
   - `jar tf <jar>` checks whether a class or resource exists.
   - `javap -classpath <jar> -p <fqcn>` checks signatures when source is not
     available.
   - If decompilation is required, keep it targeted to one class.

## Architectury API Notes

- Shared code can use Architectury abstractions only when the dependency is
  visible to the shared module.
- For creative tabs, events, registry helpers, and `@ExpectPlatform`, verify the
  exact package and method names in the workspace's configured Architectury API
  version.
- Do not assume a method from an online example exists in the configured
  `architectury_api_version`.

## Fabric API Notes

- Fabric API is modular. Verify that the module providing an event or helper is
  present and declared in `fabric.mod.json` dependencies when required.
- Fabric API umbrella artifacts may resolve as Jar-in-Jar shell jars. When MCP reports `qualityFlags: ["shell-jar"]`, use `provenance.nestedJars`; run `find-class` on the shell to search nested `.class` inventories for simple or qualified names before manual cache scanning. A class miss on a shell includes `error.nestedJars` (inner jar entry names to target next); `error.nestedJarsTruncated: true` means that list was shortened, so absence from it is not proof. `ERR_NESTED_JAR_AMBIGUOUS` means several inner jars contain the class and publishes no candidate-list field: pick the `resolve-artifact` entry in `error.exampleCalls[]` (or `error.suggestedCall`) whose jar target and reason match the intended module, resolve that nested jar as its own artifact, and query against the returned `artifactId` instead of guessing. A shell or dependency miss is not evidence that Minecraft runtime names are obfuscated.
- GameTest support is tied to Fabric API test configuration and entrypoints; see
  `gametest.md` before changing test wiring.
- Prefer Fabric events over Mixins when an event exists for the target behavior.

## NeoForge Notes

- Current NeoForge projects commonly use Mojang names. Verify access
  transformer namespace before writing entries.
- Constructor-injected `IEventBus` registration is the current pattern for many
  1.21.x projects, but follow the workspace if it already uses a verified
  alternate pattern.
- For FOV or rendering hooks, check the NeoForge API source and vanilla source
  together; loader hooks can wrap vanilla behavior.

## Resource Files in Dependency or Mod Jars

`get-artifact-file` can read exact entries directly from a backing jar even when `list-artifact-files` shows only Java source paths: `assets/**`, `data/**`, root-level files, and `META-INF/**` entries such as `fabric.mod.json`, `META-INF/MANIFEST.MF`, `<mod>.mixins.json`, and license files. Treat `deliveryMode: "jar-read-through"` as jar-backed evidence. Read-through text is capped at 512 KiB and flagged `truncated` when cut; binary entries return metadata with `contentOmittedReason`, not file content; traversal-shaped paths fail with `ERR_INVALID_INPUT`. A miss publishes no structured nearby-path field; any nearby paths appear only as `error.hints` text.

## Reporting

Report dependency facts with the artifact and source path:

```text
Verified by dependency source jar fallback:
- `CreativeTabRegistry` exposes <method> in Architectury API <version>
  Source: ~/.gradle/.../architectury-<version>-sources.jar
```

If only bytecode was available, say `source unavailable; signature verified with
javap`.
