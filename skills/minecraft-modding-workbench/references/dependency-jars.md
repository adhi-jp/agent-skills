# Dependency JAR and Source Lookup

Use this file when checking API surfaces from Architectury, Fabric API,
NeoForge, or another mod dependency.

## Preferred Flow

1. Start with MCP when available.
   - Use `analyze-mod` for a dependency jar summary, metadata, search, or class
     source.
   - Use workspace-aware symbol lookup for Minecraft classes that dependency
     APIs reference.
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

## Reporting

Report dependency facts with the artifact and source path:

```text
Verified by dependency source jar fallback:
- `CreativeTabRegistry` exposes <method> in Architectury API <version>
  Source: ~/.gradle/.../architectury-<version>-sources.jar
```

If only bytecode was available, say `source unavailable; signature verified with
javap`.
