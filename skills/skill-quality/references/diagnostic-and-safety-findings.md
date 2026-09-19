# Diagnostic and Safety Findings

Read this reference when the failure signal comes from a security analyzer, policy scanner, trust review, credential-handling warning, or another source-to-boundary-to-sink claim.

Derive the finding's prohibited predicate before choosing prose:

- Record the untrusted or sensitive source, the boundary it crosses, every
  sink it can reach, the behavior that makes the flow unsafe, and which layer
  can actually enforce the boundary. The analyzer report is `Primary source`
  for what the analyzer alleges, not for its root cause or remedy; verify the
  source-to-sink path in current repository artifacts as `Local
  investigation`; keep the root cause `Unproven` only if that path cannot be
  verified.
- Distinguish a wording gap from a data-flow, authority, or output-propagation
  gap. Calling content inert, adding an ignore-instructions reminder, or
  redacting only the final display does not close a finding while the same
  outsider-authored bytes still enter the same model context or a
  preservation rule still sends a sensitive literal to another sink.
- Prefer prevention by construction at the earliest owned boundary: omit the
  unsafe payload, accept only a closed structural record, make the capability
  unavailable when isolation cannot be enforced, or block persistence until a
  safe reference replaces the sensitive content. Downstream warnings and
  redaction are defense in depth, not closure.
- Exactness, verbatim preservation, localization, and reflection rules do not
  outrank credential, privacy, or trust-boundary controls. Audit chat output,
  saved artifacts, temporary state, reflected files, logs, commit messages,
  tool arguments, and delegated context as separate sinks.
- Run a contract-closure search across the owning `SKILL.md`, references,
  README, changelog, eval prompts, fixtures, and assertions, and revise
  current-contract text that still authorizes the flagged path. Historical
  release notes stay as they are.

If enforcement belongs to a host, adapter, or external service, state it as a
capability requirement with a fail-closed fallback; skill prose cannot prove
the host enforces it. Static validation proves artifact consistency only, not
scanner closure, runtime isolation, credential revocation, or absence of other
secret formats. Only a rerun of the reporting analyzer proves its warning
cleared; another authoritative check can prove the underlying safety property
but not that analyzer's outcome.
