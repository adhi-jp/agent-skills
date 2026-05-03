# Subagent MCP Contract

Use this as a handoff checklist when delegating Minecraft modding investigation,
implementation, or review to another agent.

## Required Context

Provide:

- workspace root as `projectPath`
- loader(s)
- Minecraft version
- mapping namespace
- Java version
- changed modules or files
- whether MCP was available in the parent task
- relevant reference files to read

## Tool Contract

Tell the subagent:

- Use high-level `minecraft-modding` tools first when available.
- Always pass `projectPath` for workspace-aware facts.
- Use `preferProjectVersion` and `preferProjectMapping` when the current tool
  accepts them.
- If `ERR_INVALID_INPUT` occurs, read `mcp-recipes.md`, correct the payload once,
  and retry the same high-level tool.
- If a worker restart, timeout, or transport failure occurs, retry once with a
  narrower high-level payload, then fall back.
- If a validator restarts once, do not loop it. Use `validator-fallbacks.md`.
- Do not pass a bare string `target` where the recipe requires a nested subject
  or artifact shape.
- For dependency API facts, use `dependency-jars.md`.

## Required Output

Ask for facts in this shape:

```text
Verified by MCP:
- ...

Verified by workspace/source jar fallback:
- ...

Runtime/user-observed:
- ...

Unverified:
- ...
```

If the subagent falls back, it must say `MCP not authoritative for this fact` for
each fallback-derived API or descriptor claim.

## Review Context Template

When handing Minecraft code to a review workflow, include:

- loader split and changed modules
- mapping namespace and Minecraft version
- Mixin target owner/name/descriptor
- access widener or transformer namespace
- client/server boundary concerns
- resource codec or registry load risks
- runtime-only behavior that compile/tests do not exercise
- manual verification gaps
