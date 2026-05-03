# Validator Fallbacks

Use this file when MCP validators are unavailable, restart, timeout, or are too
old for the requested validation task.

## General Rule

Do not loop a failing validator. After one restart or transport failure, record
the validator as unavailable for the current task and perform the matching
manual checks.

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

- Read the target class source or bytecode for the same Minecraft version.
- Confirm the method or field exists with the recorded descriptor.
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
