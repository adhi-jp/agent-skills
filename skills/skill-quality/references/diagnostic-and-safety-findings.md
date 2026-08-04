# Diagnostic and Safety Findings

Read this reference when the failure signal comes from a security analyzer, policy scanner, trust review, credential-handling warning, or another source-to-boundary-to-sink claim.

## Diagnostic And Safety Findings

When the failure signal is a security analyzer, policy scanner, trust review, or
credential-handling warning, derive the warning's prohibited predicate before
choosing prose:

- Record the untrusted or sensitive source, the boundary it crosses, every sink
  it can reach, the behavior that makes the flow unsafe, and which layer can
  actually enforce the boundary. Treat the analyzer report as `Primary source`
  for what the analyzer alleges, not as proof that its root-cause account or
  remediation is correct. Verify the reported source-to-sink path in current
  repository artifacts as `Local investigation`; if that path cannot be
  verified, keep the root cause `Unproven` instead of teaching the skill to the
  scanner's preferred wording.
- Distinguish a wording gap from a data-flow, authority, or output-propagation
  gap. Calling content inert, adding an ignore-instructions reminder, or
  redacting only the final display does not close a finding when the same
  outsider-authored bytes still enter the same model context or when a
  preservation rule still requires a sensitive literal to reach another sink.
- Prefer prevention by construction at the earliest owned boundary: omit the
  unsafe payload, accept only a closed structural record, make the capability
  unavailable when isolation cannot be enforced, or block persistence until a
  safe reference replaces sensitive content. Use downstream warnings and
  redaction as defense in depth, not as proof that the original flow is gone.
- Make conflicting obligations explicit. Exactness, verbatim preservation,
  localization, reflection, and meaning-preservation rules apply only within
  their safe domain; they do not outrank credential, privacy, or trust-boundary
  controls. Audit chat output, saved artifacts, temporary state, reflected
  files, logs, commit messages, tool arguments, and delegated context as
  separate sinks when applicable.
- Run a contract-closure audit across the owning `SKILL.md`, references, README,
  changelog, eval prompts, fixtures, and assertions. Remove or revise stale
  current-contract text that still authorizes the flagged path. Historical
  release notes remain historical evidence and are not rewritten as current
  instructions.

If enforcement belongs to a host, adapter, or external service, state that
dependency as a capability requirement and define the fail-closed fallback.
Skill prose can require and report the boundary, but it cannot prove that the
host enforces it. Static validation proves artifact consistency only; it does
not prove scanner closure, runtime isolation, credential revocation, or absence
of undiscovered secret formats. Only a rerun of the reporting analyzer proves
that its warning cleared; another authoritative check may prove the underlying
safety property, but not that analyzer-specific outcome.
