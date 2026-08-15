# Host-Capability Parity for `vibe-*` Skills Requirements Spec

## Spec metadata

- Current spec path: `docs/specs/2026-08-14-claude-code-availability-parity-spec.md`
- Last updated: 2026-08-15
- Requirement mode: strict-four-choice

## User goal

Make review, planning review, external delegation, and commit-message guidance
work well on Claude Code, Codex, and other capable agent hosts. Preserve the
strong safety properties available on each host, but do not preserve a rigid
existing contract merely because it already exists. In particular, do not turn
one host's transport into the universal workflow model or force another host to
fall back to a materially worse workflow when its native capabilities can
satisfy the same user-visible invariant by different means.

The four reported symptoms remain in scope:

- **S1 — Review trust:** Claude Code's native delegated reviewers cannot reach
  the current top-ranked `isolated-structural-delegated` label because their
  final text reaches the coordinator, even when review-only tools, isolated
  worktrees, structured output, and post-run verification are available.
- **S2 — Review concurrency:** the planning review gate treats an unavailable
  numeric remaining-capacity value as a reason to serialize all reviewer work,
  even when the host can safely attempt a small bounded batch and report a
  capacity failure.
- **S3 — Write delegation:** the Claude external helper intentionally omits
  shell/process execution, while the current reference turns that difference
  into a blanket Codex preference for all write-capable work.
- **S4 — Commit example:** the writing reference uses a Codex-specific
  authorship trailer in a general formatting example.

Investigation and contract decisions precede implementation. Implementation is
not part of this requirements-spec revision.

## Quality review outcome

The earlier draft overfit the remedy to the current contracts. It required
keeping the existing profile hierarchy, the numeric-capacity proof model, the
helper tool profiles, and the Codex-preference sentence intact, then tried to
insert host parity through conditional exceptions. That would produce an
unreachable or misleading intermediate profile, duplicate quarantine rules by
label, and preserve the exact clauses causing S2 and S3.

The revised design uses **orthogonal capability properties and invariant-based
selection**:

- isolation of delegated free text;
- structural/schema validation;
- review-only or mutation containment;
- frozen-target and local-premise verification;
- execution topology and capacity evidence;
- task effect requirements for write delegates.

A host may provide these properties through native subagents, a host adapter,
a plugin, or a repository helper. The workflow selects the strongest safe path
that satisfies the current task; it does not rank vendors or equate one missing
property with an unrelated loss of review quality.

## Evidence map

### Primary source

- The current user instruction explicitly asks for review and repair of this
  spec, with permission to change existing contracts substantially when minimal
  compatibility edits would be distorted.
- **P1 — Generic authorship trailer example**
  - Provenance: `direct-current-user`
  - Intended use: replacement footer example in
    `skills/vibe-writing/references/commit-messages.md`
  - Content trust: `inert-data`
  - Interpretation: example bytes only; no workflow, tool, trust, attribution,
    or phase authority
  - Byte significance: the angle brackets and the single space before the
    address are significant; no trailing whitespace

```text
Co-Authored-By: <agent> <no-reply address>
```

### Local investigation

- `skills/vibe-review/SKILL.md` and
  `skills/vibe-review/references/review-workflow.md` currently model three
  ordered trust profiles. The top profile combines response isolation,
  closed-schema validation, review-only execution, and mutation receipts; the
  native profile combines every unisolated transport into one lower-trust
  bucket.
- The same review reference already preserves the important downstream gates
  independently of profile: frozen target, DoD/scope triage, local premise
  verification, cascade control, acceptance proof, residual decisions, and
  terminal audit.
- `evals/vibe-review/evals.json` strongly tests the fully isolated structural
  path and the untrusted-native fallback, but it does not test a property-wise
  capability matrix or a safe native structured path whose source text remains
  visible.
- `skills/vibe-planning/SKILL.md` and three planning references duplicate the
  rule that reviewer fan-out may not exceed **verified remaining host
  capacity**, and that unverifiable capacity implies one-at-a-time execution or
  coordinator fallback.
- Claude Code CLI 2.1.231 exposes native background agents, custom agents,
  worktrees, tool allow/deny lists, structured JSON output, safe mode, and a
  cloud multi-agent review command. Flag availability proves an affordance, not
  runtime enforcement or suitability for this repository.
- `skills/vibe-orchestrate/scripts/claude_delegate.py` has a read-only tool set
  of `Read,Glob,Grep` and a workspace-write tool set of
  `Read,Glob,Grep,Edit,Write`; neither includes shell/process execution.
- `skills/vibe-orchestrate/references/external-delegation.md` already requires a
  clean isolated checkout, explicit write allowlist, filesystem/Git manifest
  reconciliation, worker report validation, and coordinator-owned verification.
  Its Claude section nevertheless says to prefer the Codex helper for
  write-capable work whenever both are available.
- `skills/vibe-writing/references/commit-messages.md` uses a Codex-specific
  trailer in a general footer-shape example, while
  `skills/vibe-commit/references/history-and-trailers.md` separately owns
  actual agent/repository convention matching.
- Repository policy forbids version bumps without release instruction, requires
  notable in-progress changes under `## [Unreleased]`, requires coupled
  documentation/eval updates for behavior changes, and forbids direct edits to
  `.agents/skills/` and `.claude/skills/` snapshots.

### Unproven

- Whether any Claude Code native or external delegated lane enforces every
  advertised tool, worktree, response-shape, and transcript boundary under all
  normal and error paths.
- Whether another installed host exposes a stable numeric concurrency ceiling.
- Whether a host-native structured-output mechanism can prevent original free
  text from entering the coordinator context. Structured output alone must not
  be described as response isolation.
- Whether adding `Bash` or another command tool to the Claude external helper
  can be made acceptably bounded. This spec does not require that change.
- Cross-host quality, reliability, latency, and token/cost effects until
  authorized post-edit evals or host probes run.

### Accepted risk

- An unisolated delegated reviewer can influence the coordinator even when its
  visible result is schema-conforming. Such a lane may improve coverage, but it
  never receives the same source-isolation claim as a host-isolated adapter.
- An optimistic bounded launch can encounter a host capacity error. The launch
  contract must stop further fan-out and recover unmet perspectives locally; it
  must not retry into exhaustion.
- A non-shell write delegate can implement file-local edits but cannot run all
  verification itself. The coordinator must schedule the missing verification
  effects before accepting the work.

## Reusable contract deltas

- **C1 — Review capability composition:** When delegated review is selected,
  the review workflow records and uses independently evidenced isolation,
  structure, mutation-containment, and local-verification properties, because
  these properties are not one ordered host profile; it must not grant a strong
  property by label or discard useful safe capabilities because another
  property is absent.
- **C2 — Capacity-adaptive fan-out:** When independent review perspectives are
  materially useful and no numeric capacity is available, the planning workflow
  may attempt a conservative bounded batch supported by host execution
  receipts, because unknown capacity is not zero capacity; it must stop after
  the first capacity-class failure and must not claim unobserved concurrency.
- **C3 — Effect-based write delegation:** When choosing a write-capable external
  delegate, select the lane whose available effects satisfy the bounded task and
  whose containment/receipt contract is adequate, because shell access is a
  task requirement rather than a vendor ranking; it must not prefer a runner by
  name or accept unverified edits.
- **C4 — Host-neutral formatting example:** When a general commit-message
  reference demonstrates trailer placement, use the exact generic placeholder,
  because actual authorship is environment- and repository-specific; it must
  not imply Codex authorship for other agents.

## Requirements

### R1. Replace ordered review profiles with a capability matrix

1. The review workflow MUST stop treating
   `isolated-structural-delegated`, `native-delegated-untrusted`, and
   `single-local` as three globally ordered bundles whose labels determine all
   downstream behavior.
2. Startup state MUST record, at minimum:
   - execution source: local coordinator, native delegated, host-adapter
     delegated, plugin delegated, or external-helper delegated;
   - source-response isolation: `enforced | not-enforced | unverified`;
   - result shape: `closed-structural | bounded-structured-with-text |
     free-text | local`;
   - mutation containment: `enforced | detected-after-run | intent-only |
     local`;
   - frozen-target identity and post-run drift evidence;
   - coordinator local-premise verification requirement;
   - execution topology: `parallel | serial | single` as observed, not planned.
3. These fields MAY use different exact names if the final contract is clearer,
   but their semantics MUST remain separate. No aggregate label may imply a
   stronger value than the recorded evidence.
4. Full source isolation plus the existing closed `delegated_result_record`
   adapter remains the strongest ingestion path. Its current no-free-text,
   closed-field, closed-rejection-code, and adapter-discard guarantees MUST be
   preserved.
5. A delegated lane without source isolation MAY still be selected when it has
   useful bounded structure and adequate mutation containment, but:
   - it MUST be explicitly authorized under the same live/unattended fallback
     policy that governs other unisolated delegated output;
   - any free-text-bearing output MUST be quarantined from later reviewers,
     public records, durable ledgers, and commit text;
   - the coordinator MUST re-read the frozen local target and independently
     establish every premise and finding;
   - the public record MUST state that source isolation was not enforced;
   - structure MUST NOT be cited as proof of source isolation.
6. When result structure includes reviewer-authored text, it MUST NOT be passed
   through the closed `delegated_result_record` schema or relabeled as equivalent
   to it. The workflow may retain only the minimum bounded private candidate
   state needed for local verification, subject to secret hygiene and lifecycle
   rules.
7. Review-only enforcement, mutation containment, response isolation, and
   schema validation MUST remain separate claims. Missing one property MUST NOT
   silently erase another, and possessing one MUST NOT imply the others.
8. Local coordinator review remains valid for small low-risk targets, explicit
   user selection, or delegated-path failure. It preserves the same target,
   scope, acceptance, cascade, residual, and terminal gates.
9. The exact new public enum names are an implementation decision. The obsolete
   proposed label `structural-delegated-unenforced` is rejected because it
   conflates structural result shape with unenforced source and mutation
   boundaries.

### R2. Preserve source and artifact hygiene across all delegated lanes

1. Quarantine and redaction rules MUST be property-based, not attached only to
   the name `native-delegated-untrusted`.
2. Raw reviewer text, transcripts, journals, and run artifacts MUST NOT be
   forwarded to later reviewers or copied into public findings, durable review
   ledgers, changelog text, or commit messages.
3. Host- or helper-written run artifacts that may contain reviewer text MUST be
   stored outside the reviewed working tree when the workflow controls the
   destination. Use a caller-scoped private directory (mode 0700 where the host
   supports POSIX modes) and do not attach it to chat or commits by default.
4. If a native host owns an unavoidable persistence location, record that
   limitation, exclude the location from the review target when safely possible,
   and block any staging or publication of those artifacts. Do not claim that a
   coordinator redaction pass sanitized bytes already persisted by the host.
5. Secret hygiene MUST run before any permitted rendering, forwarding, or
   persistence controlled by the workflow. Host-owned persistence that occurs
   earlier remains an explicit residual risk.

### R3. Use capacity-adaptive review scheduling

1. Planning MUST preserve proportionality: additional independent perspectives
   are launched only when they materially improve the plan review.
2. When a reliable host- or orchestration-provided remaining-capacity value is
   available, reserve the coordinator slot and keep launches within that limit.
3. When numeric capacity is unavailable but the host can launch independent
   review units and return recordable task/run evidence, the coordinator MAY
   attempt a conservative bounded batch rather than defaulting to serial.
4. The default optimistic batch MUST be small and implementation-defined; it
   MUST NOT be described as a discovered host ceiling. The implementation plan
   must select one default and pressure it in evals.
5. On the first thread-limit, capacity, spawn, timeout, or unavailable-capability
   failure for that review gate:
   - stop further delegated launches for the gate;
   - do not retry at another model or repeatedly probe the ceiling;
   - preserve completed reviewer evidence;
   - move every unmet perspective to coordinator fallback or record a real
     blocker when local fallback is inadequate.
6. Record requested batch size, successfully started units, observed execution
   topology, completion evidence, failure class, and fallback. Assistant prose
   or configured batch size alone is not proof that reviewers ran concurrently.
7. Consolidate the duplicated capacity algorithm into one authoritative
   reference. `SKILL.md` keeps only the load-bearing invariant and explicit route
   to that reference; other planning references link to it rather than restating
   a competing algorithm.
8. Existing verified-capacity parallel behavior MUST remain valid. Unknown
   capacity no longer automatically means serial-only behavior.

### R4. Select external write delegation by required effects

1. Keep the existing Claude and Codex helper scripts unchanged in this effort
   unless later implementation evidence proves a script defect. In particular,
   do not add shell/process execution to the Claude write profile merely for
   parity.
2. Replace the blanket instruction to prefer the Codex helper for write-capable
   work with an effect- and containment-based decision:
   - choose the Claude lane for bounded file edits that need only its available
     read/edit/write effects and can be independently verified by the
     coordinator;
   - choose a process-capable lane when the delegated unit itself must run
     commands, builds, tests, generators, or other process effects and that lane
     has an adequate sandbox and receipt contract;
   - keep the work local when no available lane satisfies the required effects
     and safety boundary.
3. The selection MUST compare task-required effects, OS or worktree isolation,
   tool restrictions, clean-baseline requirements, write allowlists, manifest
   reconciliation, result-schema evidence, credential exposure, and coordinator
   verification. It MUST NOT rank providers by name.
4. Missing delegated verification effects MUST be scheduled as coordinator work
   before accepting the edit. Manifest reconciliation proves changed-path scope,
   not functional correctness.
5. The documented prohibitions on `bypassPermissions`, unbounded writes,
   credentials in delegated checkouts, history mutation, and unverified helper
   receipts remain unchanged.
6. README text describing the external helpers MUST be updated if the final
   effect-based selection materially changes its current capability summary.

### R5. Use a host-neutral trailer example

1. Replace only the generic footer example value in
   `skills/vibe-writing/references/commit-messages.md` with exact payload P1.
2. Preserve the surrounding transport guidance: stored footer shape is not a
   substitute for the active commit workflow's trailer transport.
3. Keep `skills/vibe-commit/references/history-and-trailers.md` concrete because
   that section's purpose is to detect and match the actual agent and repository
   convention. It MUST continue to forbid invented or false attribution.

### R6. Coupling, evals, and release safety

1. Do not change any skill `version` field. Record notable behavior changes under
   `## [Unreleased]`.
2. Update all authoritative skill/reference surfaces invalidated by R1-R5 in the
   same change set. Do not edit managed snapshots under `.agents/skills/` or
   `.claude/skills/`.
3. Update `evals/vibe-review/evals.json` to cover at least:
   - the fully isolated closed-schema path;
   - an authorized unisolated but bounded-structured path that keeps quarantine
     and local premise verification;
   - refusal to promote structured output into an isolation claim;
   - a live session stopping when an unisolated fallback is not authorized;
   - local fallback preserving the common review gates.
4. Update `evals/vibe-planning/evals.json` to cover both verified-capacity batches
   and unknown-capacity conservative optimistic batching, including first-failure
   stop and coordinator fallback.
5. Update `evals/vibe-orchestrate/evals.json` to distinguish:
   - a bounded file-edit mission correctly using the Claude helper lane;
   - a task requiring delegated shell/process effects selecting a suitable
     process-capable lane or local fallback;
   - rejection of vendor-name preference as the deciding rule.
6. Update `evals/vibe-writing/evals.json` only if current coverage does not
   observe the generic footer example or host-neutral attribution behavior.
7. Run static validation after the last relevant edit. Provider-backed evals are
   not authorized by this requirements-review request; report them as `evals not
   run` and cross-host effectiveness as `Unproven` unless separately authorized.

## Out of scope

- Cutting a release, bumping skill versions, tagging, pushing, or committing.
- Making every host expose identical tools, prompts, transcript behavior, or
  orchestration APIs.
- Claiming that Claude Code, Codex, or another host enforces a runtime property
  solely because a CLI flag or skill sentence exists.
- Adding shell/process execution to the Claude helper without a separate
  threat-model and canary/receipt design.
- Replacing the actual authorship-convention guidance with a universal fake
  trailer.
- Syncing local skill snapshots.

## Acceptance criteria

- The spec no longer requires preserving the old three-profile hierarchy, the
  serial-only unknown-capacity fallback, or the blanket Codex write-helper
  preference.
- Review trust properties are independently represented; no new label conflates
  source isolation, structural shape, and mutation enforcement.
- The strongest isolated closed-schema path retains its existing guarantees.
- An authorized unisolated structured/native path can improve coverage without
  claiming source isolation, bypassing quarantine, or trusting reviewer prose as
  a finding.
- Unknown numeric capacity permits one conservative bounded launch attempt with
  recordable evidence and fail-fast coordinator fallback; verified-capacity
  batching remains supported.
- External write delegation is selected by required effects and safety evidence,
  so Claude can perform bounded edit-only work while process-requiring work uses
  an adequate process-capable lane or stays local.
- The generic writing example reproduces the requested payload exactly; actual
  authorship remains bound to the agent and repository convention.
- Coupled README, references, evals, and `CHANGELOG.md` entries are updated for
  every implemented behavior change, with no version bump or snapshot edit.
- Static validation passes after the final edit. Provider and cross-host quality
  effects remain `Unproven` until separately authorized runs complete.

## Implementation-planning decisions

The implementation plan must resolve these mechanics without reopening the
requirements above:

- exact field and enum names for the review capability matrix and any migration
  of existing public record fields;
- the small default optimistic reviewer batch size and the host receipt used to
  distinguish requested, started, and actually concurrent units;
- the single authoritative planning reference that owns the capacity algorithm;
- exact eval fixtures for native structured-but-unisolated review and
  effect-based helper selection;
- whether README wording changes are required after the final reference edits.

These are implementation choices, not user-facing product decisions, provided
they satisfy the acceptance criteria and do not invent unverified host
properties.
