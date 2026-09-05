---
version: 2.0.0
name: vibe-commit
description: Use when the user asks to commit, stage, or "save" agent-assisted coding changes — including vague requests like "commit this", "commit please", "コミットして", or "/commit" — and the real work is deciding which files belong in the commit, excluding unwanted or generated files, splitting unrelated changes, or fixing a commit's file set, multi-line message transport, history (amend/rebase), or authorship trailers. This skill owns commit execution, message transport, and git safety.
---

# Vibe Commit

## Overview

A vague "commit please" is a request to turn a messy working tree into one
clean, correctly scoped commit — not a request to run `git add -A && git
commit`. The instruction is underspecified on purpose: the user trusts the agent
to decide what belongs in the commit, keep junk out, and leave a message and
history a future maintainer can use.

This skill governs the *execution* of that: which files to stage, what to keep
out, how to re-verify the staged set before committing, how to transport a
multi-line message without corruption, and how to amend or repair a commit while
keeping authorship trailers intact. The guidance here is distilled from real
agent sessions where these exact steps prevented — or, when skipped, caused —
commit mistakes.

## Message content vs. commit execution

Commit work splits cleanly between message content and execution:

- The commit message content must stand on its own: an outcome-focused
  Conventional Commit subject, body only for durable context the diff cannot
  recover, medium-density body wording that names durable contract surfaces
  without becoming a feature walkthrough, a compact `Verification:` section that
  explains what durable proof covers instead of replaying session commands, no
  prompt/session/plan labels, and no Markdown wrappers in message bytes.
- `vibe-commit` owns the **execution**: staging, exclusion, the pre-commit
  verification gate, command safety, history mutation, message transport, and
  trailers as a transport mechanism.

Apply the compact message rules in `references/history-and-trailers.md` whenever
this skill prepares, inspects, amends, or repairs a commit message. The commit's
*bytes* — file set, message transport, trailer footer, and stored message — are
this skill's responsibility, and you verify them after committing.

## Authority and safety boundary

Committing locally is reversible; publishing is not. Stay on the reversible side
of that line unless the user says otherwise.

### Effect And Write Boundaries

<!-- shared-contract:class language=none commit=state-changing effect=state-changing -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
Every workflow phase belongs to one effect class, declared in its own text, and writes nothing beyond what that class and its declared boundary permit.

- A read-only phase reads and reports. Its deliverable is chat: findings, alignment, or direction. It edits no source, test, config, doc, or other file, runs no command that mutates runtime or repository state, and does not stage, commit, tag, push, change versions, delete data, or start services. It writes a file only when the current user explicitly asks for a saved artifact.
- An artifact-only phase creates or updates the artifact it owns — the requirements spec, the plan, the plan-review state, the instruction files, or the text artifacts the request names — and the supporting paths its own text declares: the text it was asked to revise (comments, docstrings, docs), a confirmed reflection into the bound plan, an ignore file it previewed and the user confirmed, or a narrowly confirmed configuration edit its text names. It leaves those verified changes in the working tree. It does not implement executable behavior, does not edit application code or tests as implementation, does not produce an artifact another phase owns, and does not perform release work; its artifact never authorizes same-turn implementation.
- A state-changing phase edits files and runs commands inside the scope its own text declares — the unit it implements, the repair it proves, the fixes it applies, the round it integrates, or the commit it executes — and keeps its edits to the smallest verified unit of that scope. Paths outside the scope, pre-existing working-tree changes it did not make, and runtime or external state beyond the scope stay unwritten unless the current user selects them, and every irreversible or outward-facing operation stays under its own consent.
Where a package declares a stricter or narrower rule in its own text, that declaration controls.
<!-- shared-contract:end effect-write-boundaries -->

The scope this workflow declares is the commit it executes — the index and
history of that commit and the message it transports — and it makes no source
edits.

**Honor `.gitignore` and the agreed scope.** Never `git add -f` an ignored
path, and never stage files outside the change being committed, unless the
user explicitly asks to include that ignored path after you have surfaced why
it is ignored and what risk that creates. Decide scope by the user-visible
change, not by whatever happens to be dirty.

**No surprise side effects.** Do not bump versions, cut releases, or trigger
hooks the repo did not ask for as a byproduct of committing.

### Commit Selection

<!-- shared-contract:begin commit-selection-state-changing source=shared/vibe-contract.md -->
A commit is selected by exactly three sources: an explicit current user request; a bound approved plan item that requires that checkpoint; or a state-changing workflow closing a verified, reviewed unit of its own in-scope changes under its checkpoint default. Routing or invocation, edit permission, a convenient stopping point, the presence of tracked changes in the working tree, and the availability of a commit-execution workflow never select one, and an unverified unit is never a handoff. The commit-execution phase itself executes the commits those sources select and has no checkpoint default of its own.

The checkpoint default: once a self-contained unit of the workflow's own work is implemented, verified, reviewed, and its material findings are dispositioned, the workflow closes it with a local commit of exactly that unit without waiting for a separate commit instruction, rather than letting a multi-unit run accumulate as one undifferentiated working tree. A current no-commit instruction, a bound plan that forbids commits, or project policy against commits suspends the default; then the verified changes stay in the working tree and the reason is reported. The default reaches only local commits of the unit's own verified changes: discovery-only, blocked, unchanged, failing, unverified, or work-in-progress state selects no commit, and the staged set never widens beyond the verified unit — pre-existing working-tree changes the workflow did not make, an artifact whose tracked status would itself be new, and paths outside the unit stay excluded, and neither an available commit-execution workflow nor ambient tracked status is a reason to include them. When the unit's changes cannot be separated from unrelated working-tree state, report the mixed state and ask instead of committing.

Every selected commit is routed through the commit-execution workflow with the verified scope, its test and review evidence, its unrelated-path exclusions, and any proposed message; that workflow owns staging, file-set and exact-diff review, message transport, history safety, and post-commit verification. A request to commit is not a request to push. Push, release preparation, version changes, tags, amend, rebase, reset, stash, squash, destructive actions, including cleanup, force-adds, tracking a newly created artifact, external side effects, and unrelated or ambiguous paths remain separately consent-bound even when a checkpoint was selected; no route, checkpoint, or handoff implicitly authorizes them.
Where a package declares a stricter or narrower rule in its own text, that declaration controls.
<!-- shared-contract:end commit-selection-state-changing -->

This workflow is that commit-execution phase: it executes the commits those
three sources select, keeps no checkpoint default of its own, and runs no
`git push` unless the current user explicitly asks. Scoped checkpoint handoffs
reach it as commit requests for their named paths.

Every handoff still passes this skill's file-set, verification, message,
and history-safety gates, and none of them authorizes broad staging, empty
commits, push, release work, version changes, or history rewriting.

**Separate discovery from lifecycle authority.** Status, diff, path
existence, same-session creation, logical relevance, conventional repository
placement, and commit permission make a path a candidate; they do not by
themselves authorize tracking, staging, or commit membership. A newly
selected untracked artifact needs explicit tracking intent or an applicable
mandatory repository/owning-workflow coupling. Already tracked coupled tests,
docs, specs, README, and changelog changes may remain part of the selected
logical change when their owning contract requires them.

### Commit-Selection Gate

<!-- shared-contract:begin commit-selection-gate source=shared/vibe-contract.md -->
This gate covers plain commits. Observable input: a shell tool call whose command runs `git commit` without a history-rewriting option (an amend or other rewrite belongs to the history-mutation gate), together with the session record for this worktree under `.plans/vibe-sessions/`, reading `status`, `lease.expires_at`, `repository.worktree`, `host_session_id`, `phase`, `effect_mode`, and the `source`, `at`, and `note` of every `events[]` entry of kind `commit-selection`; the directory's other candidate records, to detect a conflicting record; the readable bytes of every artifact named in `artifact_identity`, to detect an identity mismatch; and any supplied prior record, to check `generation`. A plain commit needs a recorded commit-selection source: `user-turn`, `bound-plan-item`, or `specialist-checkpoint` — the three selection sources of the commit contract — while `agent-proposed` records a proposal, not a selection.

Observable stop, with three outcomes: `allow` when the command is not a commit; `ask` for every plain commit, with a reason that quotes the `source`, `at`, and `note` of the most recent recorded `commit-selection` event and the recorded `phase` — or states that no commit-selection event is recorded, or that the record is absent, malformed, stale, foreign, session-unbound, or conflicting; and `deny`, which this gate never returns. A plain commit is never allowed silently: the recorded `source` is surfaced at the prompt so that a self-attested selection is caught there, and a record in any invalid state yields `ask`, never `deny`.

When no user-installed hook enforces this gate, this wording is the whole gate: a plain commit proceeds only when the workflow can name the selection source it rests on — the user's request, the bound plan item, or the workflow's own checkpoint of a verified unit. When the workflow is router-bound, the router records that source as a `commit-selection` event before the command runs; for a standalone commit with no router active, the direct current-user request or the verified checkpoint handoff is the named selection source, and the phase follows its ordinary confirmation policy. When no source can be named, do not commit, and ask the user if a commit appears to be wanted.
A package may state which of its phases this gate applies to; it may not change the gate's inputs, outcomes, or fields.
<!-- shared-contract:end commit-selection-gate -->

This gate applies to every plain commit the commit-execution phase runs.

### History-Mutation Gate

<!-- shared-contract:begin history-mutation-gate source=shared/vibe-contract.md -->
This gate covers history mutation. Observable input: a shell tool call whose command runs `git commit --amend`, `git rebase`, `git filter-branch` or another `filter-*` rewrite, `git reset --hard`, `git push`, or a scripted or looped replay that rewrites more than one commit — not a plain `git commit`, which the commit-selection gate covers, and not a read-only git command — together with the session record for this worktree under `.plans/vibe-sessions/`, reading `status`, `lease.expires_at`, `repository.worktree`, `host_session_id`, `phase`, `effect_mode`, and the `kind`, `source`, `at`, and `note` of every `events[]` entry; the directory's other candidate records, to detect a conflicting record; the readable bytes of every artifact named in `artifact_identity`, to detect an identity mismatch; and any supplied prior record, to check `generation`.

Observable stop, with three outcomes: `allow` when the command is not a history mutation; `ask` for every matched history mutation, with a reason that names the matched operation and quotes the recorded `phase`, `effect_mode`, and the `kind` and `source` of every recorded event that bears on the operation — or states that the record is absent, malformed, stale, foreign, session-unbound, or conflicting, or that no such event is recorded; and `deny`, which this gate never returns. A matched history mutation is never allowed silently, whatever the record says: the recorded values are surfaced at the prompt so that a self-attested record is caught there rather than trusted. History that has left this machine — pushed, fetched by another clone, or otherwise published — is shared, and no recorded value makes rewriting it silent. The record decides only the wording of the reason, never the outcome: an absent, malformed, stale, foreign, session-unbound, conflicting, or identity-mismatched record yields `ask`, never `deny`.

When no user-installed hook enforces this gate, this wording is the whole gate: before running a matched command, stop and ask the user with that reason, and proceed only on the user's answer.
A package may state which of its phases this gate applies to; it may not change the gate's inputs, outcomes, or fields.
<!-- shared-contract:end history-mutation-gate -->

This gate applies to the history mutations the commit-execution phase runs.

### History Safety

**Do not rewrite shared history.** Amending or rebasing an already-pushed
commit rewrites history other clones depend on. Only amend/rebase commits that
have not left this machine, and never force-push a shared branch without an
explicit, informed request.

**Never let a scripted rewrite delete live files without a separate confirmed
stop.** When a scripted or looped multi-commit rewrite drops paths from
history, derive each step's target list from that commit's own tree (e.g.
`git ls-tree`), never from an ambient whole-worktree snapshot (`git status`,
`-uall`, or similar) — the two are different states, and conflating them
deletes files unrelated to the commit being rewritten. Print the full
resolved list first and require an explicit confirmed stop before any
deletion executes; a preview a script can run straight past is not a gate. A
backup limits damage if something goes wrong — it never substitutes for that
per-path confirmation, and it does not by itself authorize deleting a live
working-tree file. See `references/history-and-trailers.md`.

## Core workflow: "commit please" → one clean commit

Follow this spine. Each step names the load-bearing command; the references go
deeper on the judgment calls.

1. **Discover everything.** `git status --short --branch --untracked-files=all`
   and `git status --ignored` show every modified, staged, untracked, and
   ignored path in one view. Add `git log -1 --oneline` and `git branch
   --show-current` so you know the branch and the commit you might extend.
2. **Inspect intent.** Read the actual changes — `git diff --stat`, then `git
   diff -- <file>` for specific files and `git diff -- <newfile>` (or open it)
   for untracked ones. Decide what each path *is* before deciding whether it
   belongs.
3. **Classify and select.** Sort every changed path into (a) the core
   deliverable that forms ONE logical change — implementation plus its tests and
   the docs/CHANGELOG/spec it fulfills — versus (b) out-of-scope edits or
   generated artifacts. For every newly selected untracked artifact, verify
   tracking intent or mandatory coupling before staging it. Split unrelated
   concerns into separate commits. See `references/file-selection.md`.
4. **Exclude deliberately.** Leave generated, scratch, unowned plan/spec, build,
   unrelated lock, agent-state (`.agents/`, `.claude/`, `.codex/`), and secret
   paths unstaged. A verified requirements or plan artifact named by an owning
   workflow's scoped checkpoint handoff is owned content, not generic scratch.
   A lockfile that records a dependency change needed by the selected commit is
   in-scope with the manifest; do not drop it just because it is a lockfile.
   When unsure whether a path is ignored, `git check-ignore -v <path>`. See
   `references/file-selection.md`.
5. **Stage explicitly.** `git add -- <path1> <path2> …` by full name. Avoid `git
   add .` / `-A` / globs in a dirty tree — they silently sweep in strays. For a
   file with mixed in-scope and out-of-scope hunks, `git add -p <file>`.
6. **Re-verify the staged set (mandatory gate).** Before committing, confirm
   what you are about to commit: `git diff --cached --name-only` (exact files),
   `git diff --cached --stat` (volume sanity), `git diff --cached` (read the
   hunks), `git diff --cached --check` (whitespace/line-ending errors). In-scope
   files present, out-of-scope/ignored files absent, diff matches intent. This
   2–3 second gate is the single highest-leverage habit; see
   `references/staging-and-recovery.md`.
7. **Reconcile message to the exact target diff (mandatory internal gate).** Read
   the complete final staged patch and map every material concern to the proposed
   type, scope, outcome, body coverage, and one-commit or split decision. Bind
   the decision to the current staged bytes; source drift invalidates it. Show a
   detailed public receipt only for complex or multi-package changes,
   reword/amend work, a supplied-message conflict, or a user-requested audit. In
   those cases, keep the receipt compact but explicit about the source target,
   peer concerns and shared contract, type/scope/outcome bases, subject/body
   coverage, one-commit or split decision, supplied-message disposition, and the
   rule that source-patch drift requires reconciliation again. See
   `references/history-and-trailers.md`.
8. **Decide amend vs. new.** Create a NEW commit by default. Only `--amend` to
   fix the immediately preceding, unpushed commit. See
   `references/history-and-trailers.md`.
9. **Compose the message.** Conventional Commits `type(scope): summary`
   (imperative, ≤72 chars) naming the outcome, blank line, then a body only when
   it preserves durable context the diff cannot recover. For body-worthy
   commits, use a medium-density shape: one to three short paragraphs or a few
   labeled bullets that group changes by durable surface, constraint, non-goal,
   or risk. If the message wants a long feature walkthrough, file inventory, or
   manual-test transcript, summarize or split the commit. Detect the repo's
   trailer convention first: `git log -5 --format='%H%n%B'`.
10. **Transport the message safely.** For any multi-line body, use a heredoc
   (`git commit -F - <<'EOF' … EOF`, single-quoted delimiter) or `git commit -F
   <file>`. Add or repair authorship trailers with a `git commit ... --trailer
   'Key: value'` command — including `git commit --amend ... --trailer` or `git
   commit -C <ref> --trailer ...` for local rewrites — not by typing them into
   the body or a synthesized message payload. Never embed raw newlines in a
   single `-m`. See `references/history-and-trailers.md`.
11. **Post-verify the stored commit.** `git show -s --format=%B HEAD` confirms
    subject/body/trailer landed byte-correct and the trailer parsed as a footer;
    for newly added or repaired authorship trailers, also confirm the command
    path used `git commit ... --trailer`. For body messages, inspect the stored
    message for low-signal verification dumps, bullets that only list session
    commands without review meaning, and local-only proof-source leakage such as
    git-unmanaged local generated artifacts, ignored result files, local-only
    run IDs, or private tool-session records. Compare the stored message with
    the exact committed patch and the internal pre-commit reconciliation;
    `git show --stat HEAD` is only an auxiliary file-set check. A semantic
    mismatch remains incomplete and is repaired only within existing
    unpushed-history authority. `git status --short` confirms only
    intentionally-left files remain and nothing leaked.
12. **Recover reversibly if wrong.** Prefer the least-destructive fix:
    `git restore --staged <file>` to unstage, `git reset --soft HEAD~1` to undo
    a commit while keeping changes, `git commit --amend --no-edit --trailer …`
    to fix a just-made local commit. See `references/staging-and-recovery.md`.

## When the request is narrower

Not every invocation is a full "commit please." Jump to the relevant reference:

- a response-only task supplies represented repository state and says not to
  inspect or mutate the ambient checkout → treat the supplied staged, dirty,
  verification, permission, and history facts as the target state. Show the
  complete decision and command gates that would apply without executing them;
  do not replace represented changes with an empty eval sandbox or claim that
  represented commands actually ran.
- "did I stage the right things?", "check what's staged", split a commit, drop a
  stray file → `references/staging-and-recovery.md`
- "this got committed and shouldn't have", undo/unstage, fix a wrong file set,
  recover lost work → `references/staging-and-recovery.md`
- fix the last commit, amend, reword, add/fix a `Co-Authored-By`, multi-line
  message corruption → `references/history-and-trailers.md`
- a rewrite must drop or delete paths across multiple commits (not just a
  trailer repair) → `references/history-and-trailers.md`
- "what should I commit / leave out?", excluding generated or secret files →
  `references/file-selection.md`
- "commit the staged changes" → do not invent extra staging, but still run the
  mandatory staged-set gate before committing and the stored-commit verification
  after committing.
- "show the exact commit command" or "commit command only" → include the exact
  `git commit ...` invocation, but do not collapse the answer to that one line.
  The safe artifact is the command sequence: staged-set verification, commit
  command, then stored-message/file-set verification. Simple docs commits and
  trailer-only commits are not exempt.
- the user supplies `git status`, `git diff`, or `git log` excerpts → treat them
  as evidence, but still run or show the corresponding inspection commands in
  the sequence. Do not jump from supplied excerpts straight to staging,
  committing, amending, or splitting.
- a commit subject needs evidence → choose a concrete Conventional Commit
  subject before showing an executable `git commit`, or stop before the commit
  command. Use supplied user intent even when it is broad: a named feature, bug
  fix, module, or behavior change is enough for a conservative subject. Do not
  defer a usable broad subject to future diff output merely to make it more
  precise. If paths/status are the only evidence and no behavior or fix class is
  supplied, inspect `git diff` or `git diff --cached` first; in a response-only
  command plan, show that inspection step and omit `git commit` until a concrete
  subject can be written. A commit command block whose subject contains
  angle-bracket text, unresolved-marker words, or instructions to fill the
  subject later is still an invalid shown command even if prose says not to run
  it.
- partial staging is needed → verify both sides with file-specific diffs:
  `git diff --cached <file>` for the committed hunk and `git diff <file>` for
  the intentionally-left local hunk. Show both as explicit verification
  commands before committing; a prose note or `git status` is not a substitute.
- an amend/rebase would touch pushed history → name the concrete collaboration
  risk: other clones can diverge and collaborators may have to rebase, reset, or
  reconcile duplicated commits.
- a user-named path is absent from `git status` → check `git check-ignore -v
  <path>` before deciding. If it is ignored, especially local config or
  secret-like data, do not force-add it merely because the path was named; state
  that the requested scope cannot be fully committed without an explicit
  override after the ignore rule is known.

## Common mistakes

- `git add .` / `-A` / a glob in a dirty tree, sweeping in unrelated edits,
  generated output, lock files, or secrets.
- Committing immediately after `git add` without re-reading the staged diff.
- Force-adding or accidentally committing ignored/scratch content (eval
  workspaces, `plans/`, `.codex/`, `.env`).
- Committing a whole generated directory instead of just its durable spec
  (`evals/<name>/` vs. `evals/<name>/evals.json`).
- Multi-line message corruption from a single `-m` with embedded newlines, or a
  double-quoted heredoc that lets the shell expand `$`/backticks.
- Trailer corruption: trailers typed into the body, added through
  `git interpret-trailers --trailer` plus plumbing or a synthesized message
  file, dropped when rewording with `--amend -m` (re-add with `--trailer`),
  wrong capitalization, or a stray `Key: value` body line folding into the
  footer.
- Mixing unrelated concerns into one commit so blame, bisect, and revert get
  messy.
- Destructive recovery without a plan (`git reset --hard`, force-push) that
  loses work or rewrites shared history.
- A scripted rewrite deriving its deletion targets from a global `git status`
  snapshot, or deleting right after printing a preview with no confirmed stop
  in between — see `references/history-and-trailers.md`.

## Self-check

Before reporting the commit done:

- Does the staged set match the user-visible change, with no out-of-scope,
  generated, ignored, or secret files?
- Did every newly selected untracked artifact have explicit tracking intent or
  mandatory coupling, rather than only relevance, path placement, or commit
  permission?
- Did you read `git diff --cached` (not just the file list) and run `--check`?
- Did internal message-to-diff reconciliation cover every material concern and
  invalidate on source drift? When the change is complex, multi-package,
  reword/amend, conflicted with a supplied message, or audit-requested, did the
  public receipt expose that decision clearly?
- Is the subject a Conventional Commit naming the outcome, with the body kept to
  context the diff cannot recover?
- Did you verify the **stored** commit (`git show -s --format=%B HEAD` and
  the exact committed patch, with `git show --stat HEAD` as auxiliary), not just
  the command you ran?
- If a trailer was required, did it land as a parsed footer in the exact
  authorship form for the agent that wrote the commit and the repo's existing
  convention?
- If an authorship trailer was newly added or repaired, did the transport path
  use `git commit --trailer`, `git commit --amend ... --trailer`, or `git commit
  -C ... --trailer`, never a hand-edited footer, raw append, or plumbing-created
  message?
- Did anything outside the agreed scope get committed, pushed, or rewritten?
- If the rewrite deleted any path, did it pass the commit-scoped, confirmed-stop
  gate in `references/history-and-trailers.md` rather than an ambient snapshot
  or an unconfirmed preview?
