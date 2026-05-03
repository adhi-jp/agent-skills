# Project Profile Template

Use this template to avoid re-discovering version and loader facts in long
Minecraft modding sessions. Keep project-specific profiles in the project
workspace, not in this distributed skill package.

```text
Project:
Workspace root:
Mod ID:
Base package:

Minecraft version:
Java version:
Mapping namespace:

Loader(s):
Fabric Loader:
Fabric API:
NeoForge:
Architectury API:

Modules:
- common:
- fabric:
- neoforge:

Resource layout:
Datagen task(s):
GameTest task(s):
Client run task(s):

Common verification commands:
- ./gradlew build
- ./gradlew :<module>:compileJava
- ./gradlew :<module>:test

MCP status:
Available tools:
Fallback source jars/cache paths:
Known runtime validation gaps:
```

Fill only values confirmed from workspace files, MCP, logs, or user-provided
project documentation.
