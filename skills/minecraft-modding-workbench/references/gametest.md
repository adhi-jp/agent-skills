# GameTest and Test Harness Wiring

Use this file when adding, debugging, or reviewing Minecraft GameTests and
runtime test harnesses.

## Decide the Test Type

- Pure Java unit test: formulas, comparators, codecs, packet payload encoding,
  deterministic state machines.
- GameTest or loader runtime test: block/entity interaction, projectile spawn,
  registry/resource load, Mixin behavior, access widener or transformer effects.
- Manual client verification: HUD markers, FOV-sensitive rendering, screens,
  key bindings, GUI scale, visual assets.

Do not treat a unit test as proof of loader event wiring or runtime rendering.

## Fabric Notes

- Fabric API test configuration can create a GameTest source set and run task,
  but discovery still depends on the correct `fabric-gametest` entrypoint for
  the configured project.
- If the GameTest source set is treated as a separate mod at runtime, common
  resources such as an access widener may not resolve unless the workspace
  groups source sets through Loom in the established project pattern.
- Confirm the test module sees common classes and resources before debugging
  individual test logic.

## Architectury Notes

- In multi-loader workspaces, decide which platform's runtime the GameTest is
  meant to exercise.
- Shared test logic can live in common only if the platform test runtime includes
  common outputs and resources.
- Fabric and NeoForge GameTest results do not prove exactly the same loader
  behavior. Record which loader ran.

## NeoForge Notes

- NeoForge GameTest discovery and run tasks differ from Fabric. Use the
  workspace's existing task names and source set layout.
- Access transformer and event bus behavior should be tested on the NeoForge
  runtime path, not inferred from Fabric tests.

## Verification Record

```text
GameTest source set:
Entrypoint/discovery:
Loader runtime:
Common classes/resources visible:
Access widener/transformer visible:
Task run:
Result:
```
