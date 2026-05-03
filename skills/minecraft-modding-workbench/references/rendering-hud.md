# HUD and Client Rendering

Use this file for HUD overlays, screens, world-to-screen markers, reticles,
FOV-sensitive rendering, GUI scale issues, and client-only event wiring.

## First Split

Separate the problem before editing:

- 2D overlay: fixed GUI coordinates, screen center, hotbar-relative elements,
  text, icons, cooldown bars.
- 3D projection to HUD: entity or world position converted to screen space.
- World rendering: geometry rendered in the level with camera-relative matrices.
- Screen/menu UI: `Screen`, `AbstractContainerScreen`, widgets, tooltips, and
  scissor/pose stack state.

Do not fix a world-to-screen bug by only changing 2D overlay math unless the
target is intentionally crosshair-relative.

## Registration and Side Checks

- Keep renderers, screens, HUD events, key bindings, and client imports behind
  client entrypoints or client-only platform modules.
- In Architectury projects, check whether client setup is centralized in common
  via safe abstractions or split per loader.
- For HUD overlays, verify the actual event in use:
  - Architectury: `ClientGuiEvent.RENDER_HUD` when the workspace uses it.
  - Fabric: Fabric rendering or HUD event available in the configured Fabric API.
  - NeoForge: client event bus hook used by the workspace.

## World-To-Screen Checklist

Record each coordinate space:

1. World position of the target.
2. Camera position and camera rotation for the same frame.
3. View-space vector and front/behind-camera test.
4. Projection to normalized device coordinates or a verified helper.
5. GUI-scaled pixel coordinates.
6. Off-screen clamp behavior and edge margin.

For Minecraft 1.21.x, prefer a verified helper such as
`GameRenderer.projectPointToScreen(Vec3)` when available in the workspace's
source or MCP output.

## FOV and Bow State

- `GameRenderer.getProjectionMatrix(float)` takes FOV degrees. Do not pass
  partial tick as the FOV argument.
- Bow draw, spyglass, status effects, and loader hooks can change effective FOV.
- On NeoForge, verify whether `ClientHooks.getFieldOfView` or an equivalent hook
  participates in the active FOV chain.
- Smooth FOV changes can make a marker disappear if the projection uses stale or
  incomplete FOV state.

## Visibility Checklist

- Alpha, blend state, depth state, and shader color are restored after drawing.
- Pixel thickness survives GUI scale and high FOV.
- Foreground color is visible on dark and light backgrounds.
- Edge clamp does not place the marker outside the GUI-safe bounds.
- Behind-camera targets are culled or represented intentionally.
- Bow drawing, crossbow charged state, and zoom effects are checked separately.

## Verification

Use unit tests only for pure math helpers. Runtime rendering needs runtime
evidence:

- center target
- screen edge target
- behind-camera target
- close target
- far target
- bow drawing or other FOV-changing state
- multiple GUI scales

When a client launch or screenshot cannot run in the current environment, say so
and leave the runtime visual state unverified.
