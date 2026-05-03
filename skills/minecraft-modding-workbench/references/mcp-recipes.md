# MCP Recipes

## Table of Contents

1. [When to Read This](#when-to-read-this)
2. [Shared Defaults](#shared-defaults)
3. [Common Error Shapes](#common-error-shapes)
4. [Old Shape to Current Shape](#old-shape-to-current-shape)
5. [MCP Unavailable Fallback](#mcp-unavailable-fallback)
6. [`inspect-minecraft`](#inspect-minecraft)
7. [`analyze-symbol`](#analyze-symbol)
8. [`compare-minecraft`](#compare-minecraft)
9. [`validate-project`](#validate-project)
10. [`analyze-mod`](#analyze-mod)
11. [`get-registry-data`](#get-registry-data)
12. [`get-runtime-metrics`](#get-runtime-metrics)
13. [NBT Helpers](#nbt-helpers)
14. [`manage-cache`](#manage-cache)
15. [Recovery Moves](#recovery-moves)

## When to Read This

Read this file when you already know which high-level MCP entry tool you need, but you want a payload shape that validates on the current v3 surface.

This file uses the `minecraft-modding` MCP's canonical hyphenated tool names, such as `inspect-minecraft`, `validate-project`, and `nbt-to-json`.

Some hosts expose the same tools through transformed callable names, such as snake_case function names. When making a tool call, use the callable name shown by the current tool schema. Do not rewrite this document's canonical names or payload examples just because one host uses a transformed function identifier.

These are starting points, not mandatory templates. Keep the first pass small and expand only when `result.summary` says you need more detail.

## Shared Defaults

- Start with `detail: "summary"` unless you already know you need expanded blocks.
- Add `include` only for the exact blocks you need in the same response.
- Prefer workspace-aware calls when a real mod workspace exists.
- When a tool still requires `version`, pass it explicitly even if you also pass `projectPath`.
- If `summary` already answers the question, stop there instead of drilling down by default.
- Parallelize only independent read-only discovery calls after loader, version, mapping, and `projectPath` are known.
- Keep dependent chains sequential.
- Do not run `manage-cache`, `index-artifact`, remap apply flows, or other mutating maintenance calls in parallel with calls that depend on the same cache or JAR.
- Worker restart, timeout, or transport failure gets one narrower high-level
  retry. If that fails, stop using that tool for the current task and record
  fallback evidence.

## Common Error Shapes

Treat the exact field names below as representative of the current MCP surface, not as a promise that every failure uses the same envelope forever.

### Validation error: fix the payload and retry the same high-level tool

Observed shape:

```json
{
  "error": {
    "code": "ERR_INVALID_INPUT",
    "detail": "Request validation failed.",
    "fieldErrors": [
      {
        "path": "version",
        "message": "version is required for non-workspace tasks."
      }
    ],
    "hints": [
      "Check fieldErrors and submit a valid tool argument payload."
    ]
  }
}
```

What to do:

- Read `fieldErrors` first.
- Fix the missing or malformed field and retry the same entry tool.
- Do not drop to a low-level tool just because the first payload was invalid.

### Missing file or bad local path: fix the path before changing tools

Observed shape:

```json
{
  "error": {
    "code": "ERR_INVALID_INPUT",
    "detail": "Jar not found: \"/does/not/exist.jar\"."
  }
}
```

What to do:

- Re-check `projectPath`, `jarPath`, or source file paths from the workspace.
- If the file truly does not exist, say so clearly and continue with the files that are actually present.

### `summary.status="not_found"`: absence is a result, not a transport error

Observed shape:

```json
{
  "result": {
    "summary": {
      "status": "not_found",
      "headline": "The symbol could not be resolved in 1.21.1."
    }
  }
}
```

What to do:

- Treat this as evidence that the symbol, class, or mapping path is not present in the requested version or namespace.
- Double-check the namespace, version, and owner before concluding the feature is unavailable.
- If it is still `not_found`, say so explicitly and propose the closest verified alternative.

### Tool unavailable, timeout, or stale data symptoms

What to do:

- If the tool call itself fails, times out, or returns obviously stale data, say that MCP could not verify the fact.
- Retry with a narrower high-level call first.
- Use `manage-cache` when the problem looks like stale cache or stale index state.
- Fall back to workspace files, logs, and nearby code without inventing descriptors, mappings, or registry IDs.

### Worker restart on a validator: stop the loop

What to do:

- Treat one restart from `validate-project`, `validate-mixin`,
  `validate-access-widener`, or `validate-access-transformer` as enough evidence
  that the validator is not usable for this task.
- Switch to `validator-fallbacks.md`.
- Do not report MCP validator success unless a validator actually returned a
  usable result.

## Old Shape to Current Shape

Use this section when an older example or model memory suggests a flat payload.
The current recipes prefer nested `subject` objects.

| Old or risky shape | Current shape |
| --- | --- |
| `target: "1.21.1"` | `subject: { "kind": "version", "version": "1.21.1", ... }` where the tool supports a version subject |
| flat artifact `target` under `inspect-minecraft` | `subject: { "kind": "artifact", "artifact": { "type": "resolve-target", "target": { "kind": "jar", "value": "/path.jar" } } }` |
| bare class name passed as the whole subject | `subject: { "kind": "class", "name": "<fqcn>" }` or the tool-specific `focus` form |
| workspace path as a top-level string | `subject: { "kind": "workspace", "projectPath": "/path/to/mod", ... }` where the tool expects a workspace subject |
| changing tools after `ERR_INVALID_INPUT` | fix `fieldErrors` and retry the same high-level tool once |

Do not invent an intermediate payload shape to satisfy both old and current
examples. Use the callable schema shown by the host and these current recipes.

## MCP Unavailable Fallback

If `inspect-minecraft` and `analyze-symbol` are not available, or if the current
MCP is older than these recipes, read `mcp-unavailable-fallback.md`.

Fallback facts must be labelled separately:

```text
Verified by workspace/source jar fallback:
- <claim> -- <evidence>
```

Dependency API inspection should follow `dependency-jars.md` instead of ad hoc
Gradle cache searches.

## `inspect-minecraft`

### List stable versions

```json
{
  "task": "versions",
  "detail": "summary",
  "includeSnapshots": false,
  "limit": 10
}
```

### Resolve the artifact for a specific version

```json
{
  "task": "artifact",
  "detail": "summary",
  "subject": {
    "kind": "version",
    "version": "1.21.1",
    "mapping": "mojang",
    "scope": "merged"
  }
}
```

### Resolve an already-known artifactId

```json
{
  "task": "artifact",
  "detail": "summary",
  "subject": {
    "kind": "artifact",
    "artifact": {
      "type": "resolved-id",
      "artifactId": "yarn-1.21.1"
    }
  }
}
```

### Point discovery through a jar or coordinate target

```json
{
  "task": "artifact",
  "detail": "summary",
  "subject": {
    "kind": "artifact",
    "artifact": {
      "type": "resolve-target",
      "target": {
        "kind": "jar",
        "value": "/path/to/mod.jar"
      }
    },
    "mapping": "mojang",
    "scope": "merged"
  }
}
```

The `subject.kind: "artifact"` form requires the nested `artifact: { type, ... }` object. The flat `target` shape from older docs is no longer accepted.

### Read a vanilla class through workspace context

```json
{
  "task": "class-source",
  "detail": "summary",
  "subject": {
    "kind": "workspace",
    "projectPath": "/path/to/mod",
    "mapping": "mojang",
    "scope": "merged",
    "preferProjectVersion": true,
    "focus": {
      "kind": "class",
      "className": "net.minecraft.server.MinecraftServer"
    }
  }
}
```

### Search vanilla sources through workspace context

```json
{
  "task": "search",
  "detail": "summary",
  "subject": {
    "kind": "workspace",
    "projectPath": "/path/to/mod",
    "mapping": "mojang",
    "scope": "merged",
    "preferProjectVersion": true,
    "focus": {
      "kind": "search",
      "query": "tickServer"
    }
  }
}
```

## `analyze-symbol`

### Check whether a class exists

```json
{
  "task": "exists",
  "detail": "summary",
  "version": "1.21.1",
  "sourceMapping": "mojang",
  "subject": {
    "kind": "class",
    "name": "net.minecraft.world.item.Item"
  }
}
```

### Map a method between namespaces

```json
{
  "task": "map",
  "detail": "summary",
  "version": "1.21.1",
  "sourceMapping": "mojang",
  "targetMapping": "yarn",
  "subject": {
    "kind": "method",
    "owner": "net.minecraft.world.entity.player.Player",
    "name": "tick",
    "descriptor": "()V"
  }
}
```

If a direct namespace path returns `summary.status="partial"`, keep the same symbol input but retry with the namespace pair your workspace actually compiles against, or fall back to `get-class-api-matrix` / `find-mapping` for exact recovery.

### Resolve the compile-visible workspace name

```json
{
  "task": "workspace",
  "detail": "summary",
  "projectPath": "/path/to/mod",
  "version": "1.21.1",
  "sourceMapping": "mojang",
  "subject": {
    "kind": "method",
    "owner": "net.minecraft.world.entity.player.Player",
    "name": "tick",
    "descriptor": "()V"
  }
}
```

### Overview a class's member API across mappings

```json
{
  "task": "api-overview",
  "detail": "summary",
  "version": "1.21.1",
  "sourceMapping": "mojang",
  "subject": {
    "kind": "class",
    "name": "net.minecraft.world.entity.player.Player"
  },
  "includeKinds": ["method", "field"]
}
```

Use `api-overview` when you want a single mapping-aware class/members table without chaining `get-class-api-matrix` manually. For an exact-descriptor mapping, use `task: "exact-map"` with `owner`, `name`, `descriptor`, `sourceMapping`, and `targetMapping` populated.

## `compare-minecraft`

### Get a migration overview between two versions

```json
{
  "task": "versions",
  "detail": "summary",
  "subject": {
    "kind": "version-pair",
    "fromVersion": "1.20.6",
    "toVersion": "1.21.1"
  }
}
```

### Diff a single class across versions

```json
{
  "task": "class-diff",
  "detail": "summary",
  "subject": {
    "kind": "class",
    "className": "net.minecraft.server.MinecraftServer",
    "fromVersion": "1.20.6",
    "toVersion": "1.21.1",
    "mapping": "mojang",
    "sourcePriority": "loom-first"
  }
}
```

## `validate-project`

### Summarize a workspace's Mixin, access widener, and access transformer health

```json
{
  "task": "project-summary",
  "detail": "summary",
  "version": "1.21.1",
  "mapping": "yarn",
  "atNamespace": "mojang",
  "preferProjectVersion": true,
  "preferProjectMapping": true,
  "subject": {
    "kind": "workspace",
    "projectPath": "/path/to/mod",
    "discover": ["mixins", "access-wideners", "access-transformers"]
  },
  "include": ["workspace"]
}
```

Drop `access-transformers` from `discover` on Fabric-only workspaces, and drop `access-wideners` on NeoForge-only workspaces, to avoid "no candidates" warnings for kinds the project does not use.

### Validate one edited Mixin directly

```json
{
  "task": "mixin",
  "detail": "summary",
  "version": "1.21.1",
  "mapping": "yarn",
  "preferProjectVersion": true,
  "preferProjectMapping": true,
  "subject": {
    "kind": "mixin",
    "input": {
      "mode": "path",
      "path": "/path/to/mod/src/main/java/com/example/mymod/mixin/PlayerMixin.java"
    }
  },
  "include": ["issues", "recovery"]
}
```

### Validate a NeoForge Access Transformer directly

```json
{
  "task": "access-transformer",
  "detail": "summary",
  "version": "1.21.1",
  "atNamespace": "mojang",
  "preferProjectVersion": true,
  "subject": {
    "kind": "access-transformer",
    "input": {
      "mode": "path",
      "path": "/path/to/mod/src/main/resources/META-INF/accesstransformer.cfg"
    }
  },
  "include": ["issues", "recovery"]
}
```

Pass `atNamespace: "srg"` for legacy Forge projects whose AT files still use SRG identifiers. Set `explain: true` to add a `suggestedCall` recovery hint per issue.

## `analyze-mod`

### Summarize a mod JAR first

```json
{
  "task": "summary",
  "detail": "summary",
  "subject": {
    "kind": "jar",
    "jarPath": "/path/to/mod.jar"
  }
}
```

### Search decompiled mod source

```json
{
  "task": "search",
  "detail": "summary",
  "subject": {
    "kind": "jar",
    "jarPath": "/path/to/mod.jar"
  },
  "query": "onPlayerTick",
  "searchType": "method",
  "limit": 20
}
```

### Load one decompiled class

```json
{
  "task": "class-source",
  "detail": "summary",
  "subject": {
    "kind": "class",
    "jarPath": "/path/to/mod.jar",
    "className": "com.example.mymod.mixin.PlayerMixin"
  },
  "maxLines": 120
}
```

### Preview a remap without mutating the JAR

```json
{
  "task": "remap",
  "detail": "summary",
  "subject": {
    "kind": "jar",
    "jarPath": "/path/to/mod.jar"
  },
  "executionMode": "preview",
  "targetMapping": "mojang"
}
```

Start with `summary`. Use `search`, `class-source`, `decompile`, or `remap` only after metadata tells you the jar is the right target.

## `get-registry-data`

Runs the server data generator to return structured registry content for **one vanilla Minecraft version**. Use when you need the vanilla-version ID list (blocks, items, biomes, feature keys, …) rather than a best-effort grep across sources. The tool takes `version` / `registry` / limit arguments only — it does not see `projectPath`, loader, mods, dependency jars, or datapacks, so absence from its output is NOT evidence that a modded, dependency-provided, or datapack-defined entry is missing. For modded content, check workspace registration code, generated resources, dependency metadata, and loader/datagen output instead.

### List registries with counts only

```json
{
  "version": "1.21.1",
  "includeData": false
}
```

### Fetch entries for a single registry

```json
{
  "version": "1.21.1",
  "registry": "block",
  "maxEntriesPerRegistry": 500
}
```

Use `registry: "minecraft:worldgen/biome"` or other fully qualified registry IDs when the short name is ambiguous. First runs are slow because the generator warms up; subsequent calls for the same version read from cache.

## `get-runtime-metrics`

No parameters. Read counters and latency snapshots when cache, search, or index behaviour looks off.

```json
{}
```

Pair with `manage-cache` to decide whether to `prune`, `rebuild`, `verify`, or take no action. Do not run `get-runtime-metrics` in parallel with mutating cache actions, since the metrics include in-flight work.

## NBT Helpers

Use this set for level.dat, extracted chunk payloads, playerdata, datapack fixture generation, and `/data` command output. These helpers operate on raw NBT payloads only — keep the typed JSON form for edits and re-encode once.

**Stop on `.mca` Anvil region files.** These helpers are not region-container aware. Feeding an `.mca` file in directly will either fail mid-workflow or, worse, treat a region's internal frame as a raw NBT body and round-trip a corrupted payload. Extract the target chunk's NBT with a region-aware tool first, edit the extracted payload with the recipes below, then repack with the same region tool. Back up the source `.mca` before any of this.

When editing live save data (level.dat, playerdata, extracted chunk payloads), copy the original binary before the first decode. Minecraft does not version these files, so a bad re-encode cannot be rolled back by the game.

### Decode a base64-encoded NBT payload

```json
{
  "nbtBase64": "CgAAAwALRGF0YVZlcnNpb24AAA9xAA==",
  "compression": "auto"
}
```

Returns a `typedJson` envelope of the shape `{ "rootName": string, "root": { "type": "compound", "value": { ... } } }`. All re-encode and patch payloads must preserve that envelope — a bare `{ "type": "compound", "value": ... }` document is rejected with `ERR_NBT_INVALID_TYPED_JSON`, and RFC6902 paths start at `/root/...`, not `/value/...`. `compression: "auto"` detects gzip versus raw by header; force `"gzip"` or `"none"` to fail fast when the source format is known.

### Re-encode typed JSON into NBT

```json
{
  "typedJson": {
    "rootName": "",
    "root": {
      "type": "compound",
      "value": {
        "DataVersion": { "type": "int", "value": 3953 }
      }
    }
  },
  "compression": "gzip"
}
```

Pick compression to match the original source: `"gzip"` for level.dat and playerdata, `"none"` for `/data` command output and most fixture files. Round-trip (`nbt-to-json` → `json-to-nbt` → `nbt-to-json`) against a known sample when editing live save data to confirm the envelope matches before writing.

### Apply small edits without a manual round-trip

```json
{
  "typedJson": {
    "rootName": "",
    "root": {
      "type": "compound",
      "value": {
        "DataVersion": { "type": "int", "value": 3953 }
      }
    }
  },
  "patch": [
    { "op": "test", "path": "/root/value/DataVersion/value", "value": 3953 },
    { "op": "replace", "path": "/root/value/DataVersion/value", "value": 3955 },
    { "op": "add", "path": "/root/value/CustomTag", "value": { "type": "string", "value": "hello" } }
  ]
}
```

Paths must start at `/root/...` because the decoded envelope wraps the compound under `root`. Keep a `test` op before destructive edits so the patch fails fast if the source schema has drifted. Preserve `DataVersion` unless the edit is a deliberate upgrade — silently bumping it triggers Minecraft's auto-upgrade path and can rewrite adjacent fields on load.

## `manage-cache`

### Summarize cache health

```json
{
  "action": "summary",
  "detail": "summary",
  "include": ["health"]
}
```

### Preview what a prune would remove

```json
{
  "action": "prune",
  "executionMode": "preview",
  "cacheKinds": ["mapping", "decompiled-source"],
  "selector": { "olderThan": "2026-01-01" },
  "include": ["preview"]
}
```

### Verify on-disk integrity without mutating

```json
{
  "action": "verify",
  "detail": "summary",
  "include": ["health", "warnings"]
}
```

Switch to `executionMode: "apply"` only after the preview output is what you expected. Keep mutating actions (`delete`, `prune`, `rebuild`) serial with any other call that reads the same `artifactId`, `projectPath`, or `jarPath`.

## Recovery Moves

- Validation error on an entry tool: fix the payload shape here before dropping to a low-level tool.
- Artifact context missing in `inspect-minecraft`: switch to a workspace subject with `focus`, or resolve the artifact explicitly with the nested `artifact: { type, ... }` shape first.
- Workspace mapping unresolved: keep `projectPath`, but also pass an explicit `version` and state that compile mapping detection was uncertain.
- `summary.status="not_found"`: verify namespace and version once, then treat the symbol as absent and choose a verified alternative.
- Access transformer namespace mismatch: set `atNamespace` to match the file header (`mojang` on modern NeoForge, `srg` on legacy projects) and re-run `validate-project` / `validate-access-transformer` before editing entries.
- NBT decode fails with "invalid compression" or a truncated header: retry with `compression: "auto"`, then commit to the detected format when re-encoding.
- Suspected stale MCP data: read `get-runtime-metrics`, then run `manage-cache` with `action: "verify"` before a mutating call.
- File or jar path error: fix the path or say the fixture is missing. Do not pretend the file was analyzed.
