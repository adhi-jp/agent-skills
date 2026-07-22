# Debug Workflow Reference

Read this reference when actively diagnosing, repairing, verifying, or handing off a debug task. It owns the detailed loop ordering and proof requirements.

## Workflow

1. **Continuity preflight**
   - After resume, interruption, context compaction, or a "continue" request,
     re-read the latest user request, outstanding symptoms, ledger statuses,
     and next proof/action before doing new work.
   - Do not drop unresolved symptoms because a prior subtask was completed.

2. **Capture vibe intent**
   - Preserve the user's wording for symptoms, UX concerns, "feels wrong"
     observations, and corrections to offered choices.
   - Translate the wording into observable behavior, expected behavior,
     unknowns, affected users or contexts, and current-scope closure criteria.
   - Treat user free-text changes to offered options as signal. Re-check what
     changed instead of mapping the answer back to the closest original option.

3. **Optional useful-skill and rule preflight**
   - Check project instructions, local docs, and visible skill metadata for
     task-relevant guidance.
   - Use matching available skills only when they directly help with the current
     stack, proof method, writing pass, or tool path.
   - If none apply or one is unavailable, continue with this workflow.

4. **Open the debug ledger**
   - When a concrete runtime regression is the user's active report, open a
     primary-symptom record first: reported symptom, reproduction or first
     failing proof, root-cause hypothesis, minimal patch envelope, positive
     sentinel, negative sentinel, last verified checkpoint, adjacent findings
     held as ledger-only, and the closure status.
   - Maintain a ledger with these fields for each current-scope symptom:
     reported symptom; expected behavior and source; observed behavior and
     source; prior attempts and why each failed or remains unproven; suspected
     causes; probe or instrumentation plan and result when source-only evidence
     cannot distinguish live-state hypotheses; proven cause; affected
     state-space dimensions; verification path; closure status.
   - Closure status is exactly one of `fixed`, `not-reproduced`, `deferred`,
     `accepted-residual`, or `blocked`.
   - Do not claim "fixed" until every current-scope ledger item has proof and a
     closure status.

5. **Analyze existing behavior**
   - Identify current behavior to preserve before changing code.
   - Split it into user-visible output, internal state transition,
     persistence/lifecycle behavior, external contracts, and
     operational/runtime artifacts.
   - Mark each dimension as `preserve`, `change intentionally`, `unknown`, or
     `not applicable`.
   - Treat an `unknown` dimension that affects the current fix as a blocker
     until source trace, local reproduction, or accepted residual resolves it.
   - Add at least one verification item for every `preserve` or
     `change intentionally` dimension that can regress.

6. **Route sources and tool confidence**
   - Before editing unfamiliar external API, framework, protocol, data contract,
     permission, build, deploy, or tool behavior, check the authoritative
     source: official docs, upstream source, local project code, CLI help,
     changelog, useful available skill, or user-provided source material.
   - If a tool fails, classify the failure narrowly: failed command, failed
     mode, failed input shape, unavailable service, missing permission, stale
     artifact, or flaky environment.
   - Choose a narrower retry, fallback proof, or blocker. Do not abandon all
     related tools because one mode or invocation failed.

7. **Build the state-space matrix**
   - For non-trivial fixes, convert user examples into domain-general dimensions
     before naming domain-specific cases.
   - Put an abstract dimension label beside every domain-specific case, probe,
     retest step, or closure criterion. Use labels such as representation,
     runtime artifact, lifecycle, ordering, identity, environment, permission,
     and cleanup. Domain tools may fit the report, but they must not read as
     universal requirements outside that domain.
   - Include relevant dimensions such as input representation, encoding,
     environment/origin, platform/runtime, direction, lifecycle state,
     cache/artifact freshness, permission/role, sync/async path, and
     error/cancel path.
   - For dynamic, visual, streaming, event-driven, queue, cache, or lifecycle
     bugs, include temporal sequence, ordering, overlapping events, per-entity
     identity, reset/cancel behavior, and stale-state cleanup after the final
     event.

8. **Control speculation**
   - Classify each implementation-affecting statement as `verified fact`,
     `hypothesis`, `expert judgment`, `expected outcome`, or `proof result`.
   - Do not act on a `hypothesis`, `expert judgment`, or `expected outcome`
     unless the next step is explicitly a proof step, the user accepts the
     residual risk, or the item is outside the current fix.
   - Convert optimistic language into proof requirements. "This should fix it"
     becomes "the proof needed is ..."; "looks fixed" becomes a recorded manual
     or automated observation.
   - Name one fast disconfirming check that could show the chosen cause or fix
     is wrong.

9. **Choose diagnostic probes at the right time**
   - Run bounded static triage first: nearest source path, relevant tests,
     existing logs, artifact freshness, expected-behavior source, and one fast
     disconfirming check when available.
   - Do not propose a probe solely because the bug is dynamic. Prefer a failing
     regression test, local reproduction, source trace, existing log, or
     artifact inspection when it answers the current question.
   - Trigger this gate before another fix only when bounded triage still leaves
     multiple live-state explanations, static proof would sprawl across many
     files or runtime paths, the original approach is contradicted, or a repeated
     source-only fix comes back "still broken".
   - If the probe needs the user's real environment, compare that burden with
     the value of the observation. Prefer local or artifact-level proof when it
     answers the same question.
   - State the probe question: what branch, state transition, payload,
     artifact, timestamp, ordering, identity, cleanup, or runtime boundary the
     probe must observe to separate the hypotheses.
   - Prefer low-friction probes that fit the user's real observation path:
     existing logger calls, focused trace labels, counters, debug-only dumps,
     test-harness assertions, artifact/package inspection, or narrow runtime
     logs.
   - Avoid broad noisy logging, secret or user-data exposure, expensive startup
     requirements, and permanent diagnostic behavior unless the user accepts the
     retained surface.
   - Before asking the user to run a probe, provide exact build or freshness
     steps, action sequence, expected log or trace signatures, failure evidence
     to capture, and cleanup criteria.
   - Do not make another implementation guess until the probe result,
     equivalent source trace, or accepted residual resolves the unknown.

10. **Handle failed attempts**
   - On repeated reports or "still broken" feedback, explain why the last fix
     did not address the symptom before proposing another fix.
   - The next fix must be tied to new proof, a source trace, or a state-space
     finding. Do not make another independent guess.

11. **Fix the smallest verified slice**
    - Prefer reproduction first. If local reproduction is not feasible, use a
      source trace, isolation proof, or exact manual proof path.
    - Keep edits close to the proven cause and existing local patterns.
    - Preserve unrelated behavior and defer adjacent hardening unless it is
      needed to close the primary symptom or a current ledger item with the same
      proven root cause and verification path.

12. **Prove artifact freshness**
    - Before asking the user to retest or declaring a runtime issue fixed,
      prove the tested artifact includes the change: rebuilt package or binary,
      refreshed dev-server bundle, migrated local data, regenerated assets,
      updated lockfile, restarted process, cleared stale cache, or equivalent.

13. **Handle degraded verification**
    - Skipped, unavailable, flaky, environment-limited, or manual-only checks
      are not proof.
    - For each degraded check, choose alternate proof, narrower local proof plus
      explicit residual, user retest contract, accepted residual, or blocker.
      Choose the strongest path that can observe the current contract now:
      alternate proof first, then narrower proof with stated residual, then a
      user retest contract when the user can observe the missing behavior,
      otherwise blocker. Use accepted residual only when the user explicitly
      accepts that risk.
    - Do not count "manual smoke skipped", "not locally reproducible", or "test
      environment cannot observe this" as a pass.

14. **Use a concrete user retest contract when needed**
    - When local proof cannot observe current-scope behavior, choose now:
      alternate proof, blocker, accepted residual, or a full user retest
      contract. Do not defer with "if needed" or promise steps later.
    - Do not present the proof paths as a menu for the user to choose when the
      available evidence already determines the least risky path. If the user
      asks what to test and their environment is the only credible observation
      path, select a user retest contract and leave the ledger item blocked
      until evidence returns.
    - A user retest contract names exact setup, action sequence, expected
      observation, artifact/version freshness marker, failure evidence to
      capture, and the ledger item or matrix row each check closes.
    - The contract is incomplete if it only names what to verify. Include all
      of those fields in the same handoff or keep the item blocked.
    - When exact specifics such as the command, prompts, inputs, or paths are
      unknown, deliver the contract now with explicit stated assumptions or
      clearly labeled placeholders and say how to adapt them. Do not gate the
      contract on clarifying questions the user cannot answer; asking for those
      specifics before writing it is the same banned defer. Do not hand over
      bare `<placeholder>` commands or omit failure evidence and ledger closure
      mapping because a local detail is unknown.
    - Avoid vague requests such as "please retest" or "try it again".

15. **Review recurrence before finishing**
    - If the same class of bug, review finding, or user complaint appears at
      least twice, scan adjacent surfaces for the class of omission before
      finishing.
    - Add at least one disconfirming or negative check for the neighboring case
      most likely to have been missed.

16. **Self-review before closure**
    - After implementation and verification, review the repair slice before
      final repair claims. Use a matching available review workflow when one is
      visible and applicable; otherwise run the review directly in this workflow.
    - Check the ledger closure, minimal patch envelope, preserved behavior,
      verification proof, artifact freshness, temporary or generated surfaces,
      and user-visible summary.
    - Resolve material findings and rerun affected proof before closure, or
      record the remaining item as `deferred`, `accepted-residual`, or `blocked`.

17. **Close repository operations**
    - When the repair changed files and verification plus self-review are
      complete, create a scoped local closure commit by default unless the user
      explicitly said not to commit, project instructions forbid commits, or a
      safety gate blocks the operation.
    - Before staging or committing, refresh dirty worktree and index state,
      identify repair-owned paths, surface unrelated or ambiguous dirty paths,
      and confirm self-review and verification coverage for the repair-owned
      paths.
    - Stage and commit only paths proven to belong to the repair slice. Do not
      mutate unrelated or ambiguous user changes. Push, amend, rebase, stash,
      reset, release preparation, version changes, destructive cleanup, or other
      non-closure history operations still require exact operation-specific
      consent.
    - Use matching available commit-execution and message-writing capabilities
      when they are visible and applicable. If they are unavailable, keep the
      same safeguards in this workflow: verify the staged set before commit,
      use a Conventional Commit message with durable repair outcome and proof,
      and inspect the stored message after commit.
    - When a consented closure commit needs a multi-line message, transport it
      as one complete payload: a single-quoted heredoc such as
      `git commit -F - <<'EOF' ... EOF`, or a message file passed with `-F`.
      Never use repeated `-m` arguments for body lines, bullets, verification
      lines, or trailers, and never embed a raw newline inside a single `-m`
      value. Add trailers with
      `git commit --trailer`, not by typing trailer lines into the message
      payload.
    - After a closure commit, verify the stored message with
      `git show -s --format=%B HEAD` before reporting closure. Defer complex
      history repair beyond the consented closure commit to a commit-execution
      workflow when one is visible.
    - If the user explicitly disabled commits or a safety gate blocks the
      default closure commit, finish with the reviewed uncommitted state,
      verification status, and proposed commit scope or message when useful.
