# Source Routing and Tool Confidence

Use the narrowest authoritative source for the question; memory is not evidence
of an external contract, permission, data shape, packaging, or tool behavior.

## Source Routing

| Question | Preferred source |
| --- | --- |
| Expected behavior | User requirement, spec, acceptance criteria, tests, known-good behavior |
| Local behavior | Code, tests, schema/config, logs, artifacts, reproduction |
| External API/framework/protocol | Official docs, upstream source/spec, vendor changelog, supplied source material |
| Tool semantics | `--help`, man page, official docs, wrapper source, logs, minimal dry run |
| Artifact the user tested | Build/version metadata, package contents, process/cache/migration state, runtime logs |

When the primary source is unavailable, state the limit and bound claims to what
the fallback proves.

## Tool-Confidence Ledger

Classify a failure before changing strategy: command/flags/path/environment;
mode or transport; input shape; unavailable service; permission; transient
failure; or stale artifact. Record the narrow classification and try a matching
retry or fallback. One failed worker, mode, or input does not discredit the
whole toolchain. Before hand-editing generated output, check whether generation
or source-schema proof remains usable and whether manual edits will survive it.
