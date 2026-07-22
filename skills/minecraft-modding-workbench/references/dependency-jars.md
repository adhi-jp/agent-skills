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
     `get-artifact-file`, and `list-artifact-files` when the dependency target
     is self-contained. `find-class` can also take top-level `projectPath` for
     `target.kind="workspace"` and dependency targets using
     `versionFromProject`; for the other flat artifact tools, resolve first and
     pass `artifactId` when workspace context is needed.
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
   - MCP `ERR_CLASS_NOT_FOUND.didYouMean[]` entries are candidate hints; verify
     any chosen class before editing imports or descriptors.
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
- Fabric API umbrella artifacts may resolve as Jar-in-Jar shell jars. When MCP reports `qualityFlags: ["shell-jar"]`, use `provenance.nestedJars`; run `find-class` on the shell to search nested `.class` inventories for simple or qualified names before manual cache scanning. If `ERR_NESTED_JAR_AMBIGUOUS` returns `nestedJarCandidates`, choose the module jar explicitly instead of guessing. A shell or dependency miss is not evidence that Minecraft runtime names are obfuscated.
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

`get-artifact-file` can read exact text entries under `assets/**` and `data/**` directly from a backing jar even when `list-artifact-files` shows only Java source paths. Treat `deliveryMode: "jar-read-through"` as jar-backed evidence. Binary assets return metadata with `contentOmittedReason`, not file content.

## Reporting

Report dependency facts with the artifact and source path:

```text
Verified by dependency source jar fallback:
- `CreativeTabRegistry` exposes <method> in Architectury API <version>
  Source: ~/.gradle/.../architectury-<version>-sources.jar
```

If only bytecode was available, say `source unavailable; signature verified with
javap`.
