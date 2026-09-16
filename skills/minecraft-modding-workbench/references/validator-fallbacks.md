# Validator Fallbacks

Use this file when MCP validators are unavailable, restart, timeout, are too
old for the requested validation task, refuse for runtime-jar context, or
return an approximate verdict.

## General Rule

Do not loop a failing validator. After one restart or transport failure, record
the validator as unavailable for the current task and perform the matching
manual checks. Treat `ERR_TOOL_TIMEOUT` the same way for the timed-out fact after
reading `meta.timeout.phase`, `retryRecommendation`, and `workerRestartInitiated`;
narrow or split the request if another MCP validation attempt is still useful,
and do not infer worker replacement completion from `workerRestartInitiated`.

Validator output defaults to `summary-first`. Missing per-result
`resolvedMembers`, `toolHealth`, or `resolutionTrace` in that default shape is
not validator absence. When exact per-result detail matters, retry once before
using these manual checks: `reportMode: "full"` or `explain: true` returns
per-result `resolvedMembers` and `toolHealth`, and only `explain: true` collects
`resolutionTrace`. Access transformer validation does not use `explain`, so it
provides no per-issue `suggestedCall` hints.

`validate-access-widener` and `validate-access-transformer` refuse to judge
entries against a different loader's runtime jar. `ERR_CONTEXT_UNRESOLVED` whose
`error.hints` say to point `gradleUserHome` at the Gradle home holding the
workspace's own loader runtime jars is a context problem, not a defect in the
AW/AT entries: do not edit entries for it. Fix `gradleUserHome` (or generate
those runtime jars) and re-run once, or run the matching manual checks below.
`validate-project` `task="project-summary"` counts that refusal as invalid and
carries its message in warnings, so read the warnings before blaming the
entries. A verdict marked `approximate: true` was checked against a different
Minecraft version of the same loader; read `approximationReasons` and report it
as approximate, not as exact validation for the requested version. Artifact
provenance (`requestedVersion`, `versionApproximated`, `servedLoader`,
`expectedLoader`, `loaderMismatch`) describes the jar actually served.

## Mixin Fallback

Record these facts before editing:

- target owner FQN
- method or field name
- JVM descriptor
- mapping namespace
- side: common, client, or server
- target Minecraft version
- mixin config path and array (`mixins`, `client`, or `server`)

Manual checks:

- Prefer `verify-mixin-target` for a single owner/member existence and accessor/invoker probe when the MCP tool is available and has not timed out for this fact.
- Read the target class source or bytecode for the same Minecraft version.
- Confirm the method or field exists with the recorded descriptor.
- Treat `didYouMean[]` candidates from class lookup as hints; verify the selected owner before editing.
- Confirm injection point ownership and call descriptor for `@At`.
- Prefer accessor or invoker Mixins when access is the only goal.
- Keep client-only targets out of server-reachable mixin arrays.
- Run the narrowest compile task, then the root build when module wiring changed.
- Use a runtime launch or GameTest when the failure would only appear at mixin
  apply time.

## Access Widener Fallback

- Confirm the file path declared in `fabric.mod.json`.
- Confirm the header namespace matches the names used by the entries.
- Confirm the target owner, member name, and descriptor from same-version source
  or bytecode.
- Check that common resources are visible to the runtime source set using the
  access widener.
- Run compile and the relevant Fabric run or GameTest task when access is only
  exercised at runtime.

## Access Transformer Fallback

- Confirm the file is declared in `META-INF/neoforge.mods.toml` or the
  workspace's equivalent metadata.
- Confirm `atNamespace`: usually `mojang` on modern NeoForge, `srg` on legacy
  Forge projects.
- Confirm target owner, field, method, and descriptor from same-version source or
  bytecode.
- Re-run compile after editing entries, then launch or test the path that
  requires transformed access.

## Project Summary Fallback

Read:

- `gradle.properties`
- root and module build files
- `settings.gradle`
- loader metadata files
- mixin configs
- access widener and access transformer declarations
- run configuration names or documented Gradle tasks

Run narrow checks first:

```text
./gradlew :common:compileJava
./gradlew :common:test
./gradlew build
```

Use the actual module names from the workspace. Do not report validator success
when only these fallback checks ran.
