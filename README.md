# Agent Skills

Codex skill packages maintained in this workspace for public distribution.

## Included Skills

### `minecraft-modding-workbench`

Version-aware Minecraft modding skill for Fabric, NeoForge, and Architectury
projects. It is designed around the `minecraft-modding` MCP server from
`@adhisang/minecraft-modding-mcp` and focuses on full implementation slices,
version-aware debugging, mapping work, mod JAR inspection, and multi-loader
project structure.

### `vibe-planning-guard`

Planning-first skill for turning rough change requests into verified,
option-aware implementation plans. It emphasizes workspace inspection,
evidence-labeled claims, recovery-safe replacement planning, and explicit stop
conditions when implementation blockers remain unproven.

## Repository Layout

- `skills/minecraft-modding-workbench/`: Minecraft modding skill package
- `skills/vibe-planning-guard/`: planning and design-review skill package
- `CHANGELOG.md`: repository-level change history

## Package Contents

Each skill package ships with:

- `SKILL.md`: the main workflow and decision rules

Some packages also include `references/` or other helper assets that are
specific to the skill.

## Notes

- `minecraft-modding-workbench` is scoped to Fabric, NeoForge, and
  Architectury. Legacy Forge-only projects should be treated as a separate
  toolchain check, not as NeoForge by default.
- `vibe-planning-guard` is for planning, not implementation. It should stay
  light on tiny, already-clear edits unless the user explicitly asks for
  planning or risk review.
