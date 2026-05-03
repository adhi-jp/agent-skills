# MCP Unavailable Fallback

Use this file when the `minecraft-modding` MCP server is missing, older than the
skill recipes expect, stale, timing out, or repeatedly restarting.

## Decision Rules

- If neither `inspect-minecraft` nor `analyze-symbol` is exposed by the host,
  report `minecraft-modding MCP unavailable` once and do not keep searching for
  unrelated tool names.
- If a tool or argument from `SKILL.md` is rejected as unknown, classify the
  installed MCP as older than the recipes, then use an older-compatible tool or
  local fallback.
- If a high-level call restarts or times out, retry once with a narrower
  high-level payload. If that fails, stop using that tool for the current task.
- If a validator restarts once, switch to `validator-fallbacks.md` for that
  validator. Do not loop validators.
- If `ERR_INVALID_INPUT` occurs, fix the payload once using `mcp-recipes.md`.
  Invalid input is not the same as MCP unavailability.

## Project Profile

Before manual jar inspection, record a project profile:

```text
Workspace root:
Loader(s):
Minecraft version:
Mapping namespace:
Java version:
Modules:
Common verification commands:
```

Read these sources first:

- `gradle.properties`
- root `build.gradle` or `build.gradle.kts`
- `settings.gradle`
- module `build.gradle` files
- `fabric.mod.json`
- `META-INF/neoforge.mods.toml`
- existing run configurations or documented project commands

If a value cannot be found, label it as unknown instead of guessing.

## Local Source Lookup Order

Use the narrowest reliable local source before manual cache scans:

1. Existing workspace source and generated sources.
2. Existing runtime or crash logs that name the class, method, registry key, or
   resource path.
3. Project dependency declarations and lockfiles.
4. Gradle caches under `~/.gradle/caches/modules-2/files-2.1/`.
5. Loom or loader caches that contain same-version Minecraft jars or sources.
6. `*-sources.jar` for dependency source.
7. `jar tf` to confirm class or resource presence.
8. `javap -classpath <jar> -p <class>` for signatures when source is missing.

Prefer `rg` for workspace searches. Use shell introspection only for the
specific jar, class, or resource needed for the current fact.

## Vanilla Resource Lookup

For data-driven changes, compare against a same-version vanilla example before
editing multiple schema fields:

- worldgen configured feature
- placed feature
- loot table
- item model definition
- recipe serializer input
- tag or registry reference

Record the exact vanilla file and field differences. A successful compile is not
evidence that runtime codec loading will accept the JSON.

## Fact Record Template

Use this shape in plans, reviews, and final summaries when MCP fallback was used:

```text
Verification source:
  MCP: unavailable/older/stale/validator failed (<short reason>)
  Minecraft version:
  Loader(s):
  Mapping/source:
  Runtime validation:

Verified by workspace/source jar fallback:
- <claim> -- <file, jar, source jar, javap output, or log>

Runtime/user-observed:
- <observed behavior or crash line>
```

Do not mix fallback facts into an `MCP verified` section.
