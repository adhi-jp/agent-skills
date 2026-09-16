# MCP Unavailable Fallback

Use this file when the `minecraft-modding` MCP server is missing, older than the
skill recipes expect, stale, timing out, or repeatedly restarting.

## Decision Rules

- If neither `inspect-minecraft` nor `analyze-symbol` is exposed by the host,
  report `minecraft-modding MCP unavailable` once and do not keep searching for
  unrelated tool names.
- If every `minecraft-modding` tool is missing right after an MCP upgrade, have
  the user check the host Node.js version against the MCP package's
  `engines.node` requirement: the server refuses to start on an older runtime
  instead of degrading. Report MCP as unavailable until the runtime is fixed.
- If a tool, argument, or response-shaping field that `SKILL.md` names is
  rejected as unknown, classify the installed MCP as older than the MCP surface
  the recipes target or version-skewed, then use an older-compatible tool or
  local fallback.
- Exception: if only `verify-mixin-target` or the `batch-*` tools are missing
  or rejected as unknown, the server may have them disabled
  (`VERIFY_MIXIN_TARGET_OFF`, `BATCH_TOOLS_OFF`) rather than being older. Say
  so, use `validate-project` / `validate-mixin` or single-entry lookups
  instead, and do not classify the rest of the MCP as skewed.
- If a high-level call restarts or times out, retry once with a narrower
  high-level payload. If that fails, stop using that tool for the current task.
- If `validate-project` returns `ERR_TOOL_TIMEOUT`, read `meta.timeout` for
  phase and retry guidance, then split/narrow or switch to validator fallback;
  do not claim validation success from a timeout. If the supervisor answers
  `ERR_LIMIT_EXCEEDED` because its request queue is full, wait or narrow
  instead of queuing more validator work.
- `ERR_LIMIT_EXCEEDED` whose `error.hints` name `MCP_MAX_DOWNLOAD_BYTES` is
  the per-transfer download size cap: it is not retried and no cached copy
  substitutes. `ERR_REPO_FETCH_FAILED` with `error.context.repoFailureCode:
  "ERR_LIMIT_EXCEEDED"` means the repository attempts kept that size-cap
  refusal as the actionable cause. Waiting, narrowing, or retrying does not
  help; ask the user to raise `MCP_MAX_DOWNLOAD_BYTES` and restart MCP, and use
  local fallback meanwhile.
- Jar-in-Jar inner jars have a separate per-entry extraction cap
  (`MCP_MAX_NESTED_JAR_ENTRY_BYTES`), but nested class scanning silently skips
  any inner jar it cannot extract or list, so missing inner-jar classes can mean
  an oversized, unreadable, or unlistable inner jar, or simply no match. Ask the
  user to raise `MCP_MAX_NESTED_JAR_ENTRY_BYTES` and restart MCP only with
  evidence the entry is oversized (for example, the inventory lists the inner
  jar, none of its classes resolve, and its size is known to exceed the cap);
  otherwise inspect that inner jar with local fallback.
- `ERR_REPO_FETCH_FAILED` also covers version-manifest and version-detail
  transport failures (DNS, refused connection, TLS, fetch timeout). When its
  `error.hints` name a cache path and errno, the cached entry is unreadable:
  ask the user to repair that path's permissions or disk state; retrying does
  not help until then. Repository 403/404/410 rejections are remembered
  in-process for about five minutes (a restart clears them), so an immediate
  identical retry fails the same way.
- If a validator restarts once, switch to `validator-fallbacks.md` for that
  validator. Do not loop validators.
- If `ERR_INVALID_INPUT` occurs, fix the payload once using `mcp-recipes.md`.
  Invalid input is not the same as MCP unavailability.
- If an error envelope has `retryClass: "server"`, do not retry the identical
  payload as a transient failure. Record that MCP could not verify the fact and
  continue with the narrowest reliable fallback.

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
