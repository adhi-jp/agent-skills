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

Read this file when you already know which high-level MCP entry tool you need,
but you want a payload shape that validates on the MCP surface these recipes target.

This file uses the `minecraft-modding` MCP's canonical hyphenated tool names, such as `inspect-minecraft`, `validate-project`, and `nbt-to-json`.

Some hosts expose the same tools through transformed callable names, such as snake_case function names. When making a tool call, use the callable name shown by the current tool schema. Do not rewrite this document's canonical names or payload examples just because one host uses a transformed function identifier.

These are starting points, not mandatory templates. Keep the first pass small and expand only when `result.summary` says you need more detail.

## Shared Defaults

- Start with `detail: "summary"` unless you already know you need expanded blocks.
- Add `include` only for the exact blocks you need in the same response.
- Expert and batch tools use the same response-shaping vocabulary:
  `detail: "summary" | "standard" | "full"` plus `include[]`. Treat
  `compact` only as an old-shape migration clue.
- Use batch tools for fixed 1..50-entry shortlists that share one resolved artifact or Minecraft version; keep dependent discovery chains sequential.
- Treat `ERR_CLASS_NOT_FOUND.didYouMean[]` as candidate hints that require verification, not as proof that a candidate exists or is the right migration.
- Prefer workspace-aware calls when a real mod workspace exists.
- When a tool still requires `version`, pass it explicitly even if you also pass `projectPath`.
- If `summary` already answers the question, stop there instead of drilling down by default.
- Parallelize only independent read-only discovery calls after loader, version, mapping, and `projectPath` are known.
- Keep dependent chains sequential.
- Do not run `manage-cache`, `index-artifact`, remap apply flows, or other mutating maintenance calls in parallel with calls that depend on the same cache or JAR.
- Worker restart, timeout, or transport failure gets one narrower high-level
  retry. If that fails, stop using that tool for the current task and record
  fallback evidence.
- Do not retry identical calls with `retryClass: "server"`; record the MCP
  server fault and use the relevant fallback path for the current fact.

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
- If you are explaining the recovery instead of running the corrected call,
  record MCP status and verification sources first. Payload-shape facts can be
  recipe-grounded, but target class, version, mapping, and workspace facts stay
  unverified until the corrected call returns.

### Missing file or bad local path: fix the path before changing tools

Observed shape:

```json
{
  "error": {
    "code": "ERR_JAR_NOT_FOUND",
    "detail": "Jar not found: \"/does/not/exist.jar\"."
  }
}
```

What to do:

- Re-check `projectPath`, `jarPath`, or source file paths from the workspace.
- If the file truly does not exist, say so clearly and continue with the files that are actually present.

### `summary.status="not_found"`: a lookup result, not a transport error

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

- Treat this as a lookup result that the symbol, class, or mapping path was not found in the requested version, namespace, and owner, not yet as proof of absence.
- Read `warnings` before concluding: an exact method mapping's `not_found` names other declaring classes only when other classes declare that name and descriptor, and a mapping-index budget stop can leave the answer incomplete (see `mcp-guardrails.md`). A `not_found` without either warning still needs the checks below.
- Double-check the namespace, version, owner FQN (the declaring class for exact method mappings), and descriptor before concluding the feature is unavailable.
- If it is still `not_found`, say so explicitly and propose the closest verified alternative.

### Tool unavailable, timeout, or stale data symptoms

What to do:

- If the tool call itself fails, times out, or returns obviously stale data, say that MCP could not verify the fact.
- Retry with a narrower high-level call first.
- Use `manage-cache` when the problem looks like stale cache or stale index state. A timeout on the first lookup after an MCP upgrade is not that signal; see the failure budget in `mcp-guardrails.md`.
- Fall back to workspace files, logs, and nearby code without inventing descriptors, mappings, or registry IDs.

### Worker restart on a validator: stop the loop

What to do:

- Treat one restart from `validate-project`, `validate-mixin`,
  `validate-access-widener`, or `validate-access-transformer` as enough evidence
  that the validator is not usable for this task.
- Switch to `validator-fallbacks.md`.
- Do not report MCP validator success unless a validator actually returned a
  usable result.

### Deterministic server fault: do not retry the same call

Observed shape:

```json
{
  "error": {
    "code": "ERR_INTERNAL",
    "detail": "Unexpected server error.",
    "retryClass": "server"
  }
}
```

What to do:

- Treat `retryClass: "server"` like a permanent retry posture for the identical
  call.
- Do not spend the normal transient retry budget on the same payload.
- Record that MCP could not verify the fact and switch to the narrow workspace,
  source jar, Gradle, or log fallback for the task.

## Old Shape to Current Shape

Use this section when an older example or model memory suggests a removed or
stale payload or response path. The recipes here prefer current MCP shapes.

When answering a stale-shape or retry-posture question, keep the response as an
MCP-shape correction unless the current task already reached a real fallback
condition. Include: callable schema must be inspected before corrected payloads;
all four verification source labels; the relevant table rows below; and a brief fallback reason only when it materially affects provenance. Do not paste a full validator, loader, GameTest, source
jar, or Gradle fallback playbook just because a fallback gate is named.

| Old or risky shape | Current shape |
| --- | --- |
| expert or batch `compact: true` / `compact: false` | `detail: "summary"` / `detail: "full"` plus `include[]` for specific field groups |
| `target: "1.21.1"` | `subject: { "kind": "version", "version": "1.21.1", ... }` where the tool supports a version subject |
| flat artifact `target` under `inspect-minecraft` | `subject: { "kind": "artifact", "artifact": { "type": "resolve-target", "target": { "kind": "jar", "value": "/path.jar" } } }` |
| bare class name passed as the whole subject | `subject: { "kind": "class", "className": "<fqcn>" }` or the workspace `focus: { "kind": "class", "className": "<fqcn>" }` form |
| workspace path as a top-level string | `subject: { "kind": "workspace", "projectPath": "/path/to/mod", ... }` where the tool expects a workspace subject |
| workspace `subject.focus` as a string | `focus: { "kind": "class", "className": "<fqcn>" }`, `{ "kind": "search", "query": "<text>" }`, or `{ "kind": "file", "filePath": "<path>" }`; a rejected string focus returns `error.exampleCalls[]` shapes; fill any `<...>` placeholders before retrying |
| reading requested inspect input from `result.summary.subject.requested` | read `result.subject.requested` / `result.subject.resolved`, or correlate by `meta.requestId` |
| reading warning text from `meta.warningDetails[].message` | read `meta.warnings[detail.index]` |
| `get-class-source` / `get-class-members` `target: { "type": "artifact", "artifactId": "..." }` | `target: { "kind": "artifact", "artifactId": "..." }`; for member reads also mention the 150-member default page, `nextCursor`, shared `members.ownerFqn`, modifiers from `javaSignature`, and `include: ["descriptors"]` or `includeDescriptors: true` when field descriptors matter |
| relying on `get-class-members` per-member `accessFlags` or always-present `ownerFqn` | derive modifiers from `javaSignature`; read owner from `members.ownerFqn` and fall back to per-member `ownerFqn` only when inherited members expose multiple owners |
| expecting field `jvmDescriptor` by default | pass `include: ["descriptors"]` or `includeDescriptors: true`; method and constructor descriptors remain present for overloads |
| using full member output for simple existence checks | pass `projection: "names"` or `"signatures"`; do not use lean projections when descriptors or annotation metadata matter |
| treating class-not-found as a dead end | inspect `error.didYouMean[]` candidates and verify any chosen candidate before patching imports, descriptors, or mappings |
| matching unobfuscated-version warning text | read `mappingContext.unobfuscatedRuntime`, `mappingContext.runtimeValidated`, or `result.unobfuscatedRuntime` on `get-class-api-matrix` |
| interpreting missing per-result validator `resolvedMembers`, `toolHealth`, or `resolutionTrace` as absence | pass `reportMode: "full"` or `explain: true` for `resolvedMembers` / `toolHealth`, and `explain: true` for `resolutionTrace`; default validator output is `summary-first` |
| treating `validate-project` timeout as success or a restart loop | read `ERR_TOOL_TIMEOUT` `meta.timeout`; split/narrow or use validator fallback, and do not infer replacement completion from `workerRestartInitiated` |
| unbounded `analyze-symbol task="lifecycle"` using old five-version assumptions | pass `fromVersion`, `toVersion`, `maxVersions`, `includeTimeline`, and `includeSnapshots` for the intended range |
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
      "artifactId": "<artifactId returned by an earlier resolve>"
    }
  }
}
```

Copy the `artifactId` from an earlier resolve response; ids are opaque, content-derived handles, so never build one from a mapping or version name.

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

If a workspace `subject.focus` string is rejected, read the returned
`error.exampleCalls[]`, fill any `<...>` placeholders, and choose the class, search, or file object shape that matches
the intended retry. Do not coerce prose into a focus shape yourself; `task:
"auto"` dispatches from `subject.kind` and `focus.kind`, not from natural
language.

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

`analyze-symbol` can infer an omitted `version` when `projectPath` is supplied. If you rely on that, record the returned `versionInference { version, source }` and warning. Keep an explicit `version` when reproducibility matters or workspace detection is uncertain.

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

Use `api-overview` when you want a single mapping-aware class/members table without chaining `get-class-api-matrix` manually. For an exact-descriptor mapping, use `task: "exact-map"` with `owner`, `name`, `descriptor`, `sourceMapping`, and `targetMapping` populated; it is owner-strict, so read `mcp-guardrails.md` before treating its `not_found` as absence.

### Trace a symbol over a bounded version range

```json
{
  "task": "lifecycle",
  "detail": "summary",
  "toVersion": "1.21.1",
  "fromVersion": "1.20.6",
  "maxVersions": 20,
  "includeTimeline": false,
  "includeSnapshots": false,
  "sourceMapping": "mojang",
  "subject": {
    "kind": "method",
    "owner": "net.minecraft.world.item.Item",
    "name": "useOn",
    "descriptor": "(Lnet/minecraft/world/item/context/UseOnContext;)Lnet/minecraft/world/InteractionResult;"
  }
}
```

For lifecycle work, always bound the range you intend. The current MCP surface accepts
`fromVersion`, `toVersion`, `maxVersions`, `includeTimeline`, and
`includeSnapshots` only for `task: "lifecycle"`; the old implicit narrow scan is
not the default.

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

`task: "versions"` (like `compare-versions`) diffs both jars in the mojang namespace, so its counts are not comparable with diffs recorded under earlier MCP releases. Read `warnings` before using the lists: a mapping that is unavailable, or present on only one side, degrades the diff to obfuscated names, and a pair straddling the unobfuscation boundary whose obfuscated mappings cannot load is flagged as having added/removed lists that are not meaningful.

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

## `verify-mixin-target`

Use this for a single owner/member probe before writing or repairing a Mixin `@Shadow`, `@Accessor`, or `@Invoker`. It verifies existence and access advice from bytecode without requiring a whole source/config validation. Use `validate-project` or `validate-mixin` when you need config discovery, injection-point validation, side checks, or batch project health.

```json
{
  "target": { "kind": "version", "value": "1.21.10" },
  "owner": "net.minecraft.world.entity.LivingEntity",
  "member": { "kind": "method", "name": "tick", "descriptor": "()V" },
  "mapping": "mojang",
  "autoRemap": true
}
```

Set `autoRemap: true` only when a version-based target lets the tool translate readable owner/member names into the artifact namespace. If the probe says an accessor or invoker shape is needed, still verify the mixin member name and descriptor against the workspace's mapping namespace before editing.

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
  "reportMode": "full",
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

Use the default `summary-first` validator output for triage. When the work needs
per-result `resolvedMembers` or `toolHealth`, request `reportMode: "full"` or
`explain: true`; `resolutionTrace` is collected only with `explain: true`. Do
this before declaring the validator unable to provide detail.

`validate-project` has a supervisor-owned timeout. If it returns `ERR_TOOL_TIMEOUT`, inspect `meta.timeout.phase`, `retryRecommendation`, and `workerRestartInitiated`; split or narrow the validation, or switch to `validator-fallbacks.md` for that fact. Do not report validator success from a timeout.

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

Pass `atNamespace: "srg"` for legacy Forge projects whose AT files still use SRG identifiers. The access transformer path does not use `explain`, so do not expect per-issue `suggestedCall` hints from it. For a loader-mismatch refusal or an `approximate: true` verdict, see `validator-fallbacks.md`.

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

### Read mod class members without decompiling

```json
{
  "task": "members",
  "detail": "summary",
  "subject": {
    "kind": "class",
    "jarPath": "/path/to/mod.jar",
    "className": "com.example.mymod.mixin.PlayerMixin"
  }
}
```

`task: "members"` reads constructors, fields, and methods directly from bytecode, including private/protected members, and returns `extractionMethod: "bytecode-only"`. Prefer it over `class-source` when you only need signatures from a mod jar.

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

Start with `summary`. Use `search`, `class-source`, `members`, `decompile`, or `remap` only after metadata tells you the jar is the right target.

## Source and artifact lookup helpers

`get-class-source` and `get-class-members` accept the shared `target` shape directly. Use `target: { "kind": "workspace" }` with `projectPath` for workspace-derived Minecraft versions, and `target: { "kind": "dependency", "group": "net.fabricmc.fabric-api", "name": "fabric-api", "versionFromProject": true }` for loader dependency classes. Reuse `target: { "kind": "artifact", "artifactId": "..." }` after a prior resolve.

Flat artifact tools (`find-class`, `search-class-source`, `get-artifact-file`, `list-artifact-files`, `index-artifact`) accept exactly one of `artifactId` or `target`, plus top-level `projectPath` for `target.kind="workspace"` and dependency targets without an explicit version. Use direct `target` when it fits; resolving first to an `artifactId` is optional (see `mcp-guardrails.md`).

`get-artifact-file` can read exact entries directly from a backing jar when the source index has no row. Treat `deliveryMode: "jar-read-through"` as exact jar evidence. `dependency-jars.md` covers which entries it serves, size and binary handling, and what a miss reports.

Jar-in-Jar shell jars carry `qualityFlags: ["shell-jar"]` and `provenance.nestedJars`. `find-class` searches nested `.class` inventories for simple or qualified names, deduplicates repeated class names, honors `limit`, and returns dotted inner-class names that can be read through `get-class-source`. `get-class-source` and `get-class-members` redirect only when one nested jar uniquely contains a top-level class. If the tool returns `ERR_NESTED_JAR_AMBIGUOUS`, resolve the intended nested jar as its own artifact through the `resolve-artifact` shapes in `error.exampleCalls[]` / `error.suggestedCall` instead of guessing; `dependency-jars.md` has the recovery. A dependency or shell miss is not evidence of Minecraft obfuscation and should not trigger a `mapping="mojang"` retry unless the artifact is a Minecraft runtime artifact.

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

Returns a `typedJson` document `{ "rootName": string, "root": <typed node> }`. The root can be any typed node; Minecraft files usually decode to a compound root `{ "type": "compound", "value": { ... } }`. All re-encode and patch payloads must preserve that document — a bare `{ "type": ..., "value": ... }` node is rejected with `ERR_NBT_INVALID_TYPED_JSON`, and RFC6902 paths point into that document (`/root/...`), not `/value/...`. `compression: "auto"` detects gzip versus raw by header; force `"gzip"` or `"none"` to fail fast when the source format is known.

Every typed node is `{ "type", "value" }`. Keep these value rules when writing or patching nodes:

- `long` values and `longArray` elements are decimal strings, never JSON numbers.
- `float` / `double` non-finite values are the strings `"NaN"`, `"Infinity"`, and `"-Infinity"`.
- A `list` node also carries `elementType`, and every element's `type` must match it.

When `ERR_NBT_INVALID_TYPED_JSON` returns, read `error.fieldErrors[0].path` (an RFC 6901 pointer to the offending node, or `typedJson` for the whole document) and the expected/received types in `error.hints`, then fix that node once. If the document cannot be repaired from evidence, regenerate it with `nbt-to-json` from the source payload; the `nbt-to-json` entry in `error.exampleCalls[]` is a template whose placeholder must be replaced with the real payload.

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

Pick compression to match the original source: `"gzip"` for level.dat and playerdata, `"none"` for `/data` command output and most fixture files. Round-trip (`nbt-to-json` → `json-to-nbt` → `nbt-to-json`) against a known sample when editing live save data to confirm the document matches before writing.

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

Tag edits on a compound root use paths under `/root/value/...` because the document wraps the root node under `root` and a compound keeps its tags under `value`. Whole-document pointers such as `/rootName` or `/root` are also valid; an empty pointer is rejected. Keep a `test` op before destructive edits so the patch fails fast if the source schema has drifted. Preserve `DataVersion` unless the edit is a deliberate upgrade — silently bumping it triggers Minecraft's auto-upgrade path and can rewrite adjacent fields on load.

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

Switch to `executionMode: "apply"` only after the preview output is what you expected. After `delete` or `prune` apply, read `warnings` and the removed counts: a download-cache entry the tool could not remove (for example a locked or read-only file) returns a warning and is not counted, while a removal failure on other file-backed cache kinds can fail the operation with an error. Keep mutating actions (`delete`, `prune`, `rebuild`) serial with any other call that reads the same `artifactId`, `projectPath`, or `jarPath`.

## Recovery Moves

- Validation error on an entry tool: fix the payload shape here before dropping
  to a low-level tool. Keep payload-shape recovery separate from target
  Minecraft facts; no class, API, version, mapping, or workspace fact is
  MCP-verified until the corrected call succeeds.
- Artifact context missing in `inspect-minecraft`: switch to a workspace subject with structured `focus`, rely on direct-subject workspace auto-resolution only when exactly one workspace is known, or resolve the artifact explicitly with the nested `artifact: { type, ... }` shape first. If a string focus is rejected, take the shape from `error.exampleCalls[]` and fill any `<...>` placeholders from verified facts before retrying.
- Inspect response correlation: use `result.subject.requested` /
  `result.subject.resolved`, not `result.summary.subject`.
- Workspace mapping unresolved: keep `projectPath`, but also pass an explicit `version` and state that compile mapping detection was uncertain. If `analyze-symbol` inferred a version, record `versionInference`.
- `ERR_WORKSPACE_VERSION_UNRESOLVED` (from `analyze-symbol`, workspace `target`s, or `inspect-minecraft` workspace subjects): the workspace Minecraft version could not be detected. It is `retryClass: "permanent"`, not an invalid payload, so skip the fix-once payload loop; supply an explicit version from workspace evidence, or record the version as missing.
- `summary.status="not_found"`: verify namespace, version, owner FQN (the declaring class for exact method mappings), and descriptor once, read `warnings` and any `didYouMean[]` hints, then treat the symbol as absent only when no warning names another declaring class or an incomplete mapping index, and choose a verified alternative.
- Access transformer namespace mismatch: set `atNamespace` to match the file header (`mojang` on modern NeoForge, `srg` on legacy projects) and re-run `validate-project` / `validate-access-transformer` before editing entries.
- NBT decode fails with "invalid compression" or a truncated header: retry with `compression: "auto"`, then commit to the detected format when re-encoding.
- Error envelope has `retryClass: "server"`: do not retry the identical call as
  transient; use fallback evidence or report the MCP server fault.
- Error envelope has `retryClass: "permanent"` or `"environment"`, or `ERR_CONTEXT_UNRESOLVED` reports `issueOrigin: "tool_issue"`: do not replay the identical call or re-send the same artifact behind a payload fix; follow the posture in `mcp-guardrails.md`.
- `validate-project` returns `ERR_TOOL_TIMEOUT`, or the supervisor answers `ERR_LIMIT_EXCEEDED` because its request queue is full: narrow/split the request or wait; do not queue more validator work or claim validation success. A size-cap `ERR_LIMIT_EXCEEDED` is different; see `mcp-unavailable-fallback.md`.
- Suspected stale MCP data: read `get-runtime-metrics`, then run `manage-cache` with `action: "verify"` before a mutating call.
- File or jar path error: fix the path or say the fixture is missing. Do not pretend the file was analyzed.
