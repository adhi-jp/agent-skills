# External Delegation

Read this reference before launching `scripts/codex_delegate.py` or
`scripts/claude_delegate.py`, selecting a profile, or accepting a helper
receipt.

## When To Use

Use a helper only as optional transport for a bounded external CLI worker inside
an already-selected workflow phase. It does not grant approval, proceed,
consent, review-disposition, or commit authority. Supply a required `--model`,
an absolute `--artifact-dir`, and the delegated `--cwd`; use `--prompt-file`
when prompt content should travel by file.

## Two-Layer Authorization

The outer host owns every escalation and records authorization once. The inner
runner must never prompt. Do not silently replace a failed runner or model:
narrow the contract, obtain the needed decision, or stop. The helpers carry
runner-specific profiles; their canary proves the selected profile rather than
assuming it is safe.

## Preflight And Canary

Run `preflight` and one tool-capable canary before work for every distinct
execution fingerprint, then pass its receipt to `run` with
`--preflight-receipt` and an appropriate `--preflight-max-age`. The receipt is
valid only within that maximum age and when its fingerprint digest matches.
Re-canary before fan-out after any fingerprint input changes.

The fingerprint includes exact bytes of each helper and shared module, runner
version, model, effort, sandbox or profile, runtime profile, result-schema
identity, state home, and manifest limits. Use `--manifest-max-files` and
`--manifest-max-total-bytes` to keep both manifest ceilings explicit.

## Running Bounded Work

Delegate only in a disposable or isolated Git worktree with a clean `HEAD`
baseline. For workspace writes, require exact non-root relative
`--allowed-write` paths; pre-seed any directory that must exist inside that
allowlist. Keep the artifact directory outside the delegated cwd. Prompt-file
transport is preferred for bounded prompt input. Writes require
`--result-schema worker-report-v1`; the worker-reported files must equal the
observed scope, and the coordinator verifies that reconciliation.

## Receipt Verification

A handle or `running` state is not completion. Require the helper's structured
receipt and terminal evidence before inspection, verification, or another
writer.

- Codex requires JSONL `turn.completed` and no `turn.failed`, as well as the
  helper's successful terminal checks.
- Claude requires terminal result JSON with `subtype` `success`, `is_error`
  false, and `terminal_reason` `completed`. When a schema is selected, the
  helper must revalidate `structured_output` and reject disagreement with
  `result`.

## Failure Classes And Recovery

Fail closed: do not treat an unrecognized receipt or runner response as a
success. Classify and repair at the owning boundary rather than retrying into a
different contract.

- Preflight: binary not found, version failure, state-home not writable, or
  authentication failure.
- Setup: a missing, stale, unsuccessful, or fingerprint-mismatched preflight
  receipt (emitted as one preflight-required class whose `reason` field names
  the exact cause); invalid cwd; missing Git baseline; dirty worktree; manifest
  unavailable or over ceiling; invalid or missing write allowlist; empty
  prompt; or artifact directory inside cwd.
- Run: timeout, network/provider failure, CLI contract mismatch, receipt
  mismatch, or scope violation.
- Claude additionally classifies a recognized permission denial; an
  unrecognized permission receipt becomes a generic failure.

## Claude Runner Differences

Claude tool-profile enforcement detects contract drift but does not provide an
OS sandbox. The read-only profile denies writes by omitting them; the write
profile uses `acceptEdits`. Never use `bypassPermissions` or
`--dangerously-skip-permissions`. The safe-mode minimal profile is part of the
fingerprint and must pass its own canary before work.

## Worker Prohibitions

Delegated workers must not stage, commit, push, release, or mutate history.
The coordinator owns verification and the commit boundary.

## Artifact Handling

Create artifact directories with mode 0700 and keep them outside the delegated
cwd. Retention is caller-owned. Do not attach raw artifacts to chat or commits
by default.
