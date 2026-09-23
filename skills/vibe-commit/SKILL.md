---
version: 4.0.0
name: vibe-commit
description: Use when the user asks to commit, stage, or "save" agent-assisted coding changes — including vague requests like "commit this", "commit please", "コミットして", or "/commit" — and the real work is deciding which files belong in the commit, excluding unwanted or generated files, splitting unrelated changes, or fixing a commit's file set, multi-line message transport, history (amend/rebase), or authorship trailers. This skill owns commit execution, message transport, and git safety.
---

# Vibe Commit

## Overview

A commit request means one clean, correctly scoped commit, not `git add -A &&
git commit`. Select the user-visible change, exclude unrelated or unsafe paths,
read the staged diff, transport the message safely, and inspect the stored
commit. For a command-only or represented-state request, show the applicable
sequence without claiming it ran; for a blocked request, stop at the blocker.

## Message content vs. commit execution

This skill owns staging, verification, message transport, trailers, and history
safety. Use `references/history-and-trailers.md` whenever preparing, inspecting,
amending, or repairing a message. In a response-only plan, `Verification:`
bullets use only supplied evidence: a check the supplied state does not record
as passed is `not run`, never a passed result.

## Authority and safety boundary

Committing locally is reversible; publishing is not. Stay on the reversible side
of that line unless the user says otherwise.

### Effect And Write Boundaries

<!-- shared-contract:class language=none commit=state-changing effect=state-changing -->
<!-- shared-contract:begin effect-write-boundaries source=shared/vibe-contract.md -->
**Write nothing beyond what the phase's declared effect class and boundary permit.**

- Apply the effect class the phase declares in its own text; where this package states a narrower limit, the narrower limit wins.
- Read-only: report in chat; edit no file, run no state-mutating command, and never stage, commit, tag, push, change versions, delete data, or start services. Write a file only when the user explicitly asks for a saved artifact.
- Artifact-only: create or update only the artifact the phase owns and the supporting paths its text declares, such as a confirmed plan reflection or a decision record, and leave them in the working tree.
- Never let an artifact-only phase implement executable behavior, edit code or tests as implementation, produce another phase's artifact, do release work, or treat its artifact as same-turn implementation authority.
- State-changing: edit and run commands only inside the declared scope, in its smallest verified unit; leave other paths, pre-existing changes, and runtime or external state untouched unless the user selects them.
- These limits cover shell commands (redirection, `sed -i`, `tee`, `mv`, `cp`, `rm`, `git checkout --`) as well as file tools; report a refused write as a boundary stop and never retry it through another tool.
- Keep every irreversible or outward-facing operation under its own consent.
<!-- shared-contract:end effect-write-boundaries -->

The scope this workflow declares is the commit it executes — that commit's
index, history, and message — and it makes no source edits.

**Honor `.gitignore` and the agreed scope.** Never `git add -f` an ignored
path, and never stage files outside the change being committed, unless the
user explicitly asks to include that ignored path after you have surfaced why
it is ignored and what risk that creates.

### Durable Records

Before committing, check `docs/decisions/README.md`, or the records themselves
when `docs/decisions/` exists but the index is missing, for accepted records
whose `paths` the staged diff touches. Read
`references/durable-records.md` when one does, when the file set includes a
decision record or findings report, and before handing a decision or finding
forward. This phase ordinarily writes neither `docs/decisions/` nor
`docs/reports/findings/`; it passes them on as the carry-forward packet that
reference defines.

### Commit Selection

<!-- shared-contract:begin commit-selection-state-changing source=shared/vibe-contract.md -->
**Only an explicit user request, a bound plan item, or the workflow's own verified checkpoint selects a commit.**

- Name the source before committing: the current user's request, an approved bound-plan checkpoint, or this workflow's checkpoint default for its own verified unit. With none, do not commit; ask whether a commit is wanted.
- Never treat routing, invocation, edit permission, a convenient stopping point, tracked changes, or an available commit workflow as a source. Commit execution has no checkpoint default of its own.
- Checkpoint default: once a self-contained unit is implemented, verified, reviewed, and its material findings dispositioned, commit exactly that unit locally without waiting for a separate instruction; never let several units pile up uncommitted.
- Select nothing from discovery-only, blocked, unchanged, failing, unverified, or work-in-progress state.
- Stage only the unit: exclude pre-existing changes the workflow did not make, paths outside the unit, and any artifact that would become newly tracked; if the unit cannot be separated from other changes, report the mixed state and ask.
- Route each selected commit through commit execution with its scope, test and review evidence, exclusions, and any proposed message; that workflow owns staging, diff review, message transport, and post-commit verification.
- Before a push, amend, rebase, HEAD-moving reset (soft, mixed, or hard), `filter-*` rewrite, or scripted replay of several commits, get the user's explicit authorization for that operation; a commit request or checkpoint never grants it, and published history is shared.
- Never treat a commit request or checkpoint as consent to release, version changes, tags, stash, squash, destructive cleanup, force-adds, tracking a new artifact, or external side effects; each needs its own.

Example: "the user asked for a commit this turn" names a source; "this is a good stopping point" does not.

Exception: a current no-commit instruction, a bound plan that forbids commits, or project policy suspends the default; leave the verified changes in the working tree and report why.
<!-- shared-contract:end commit-selection-state-changing -->

This workflow is that commit execution; a scoped checkpoint handoff arrives as a
commit request for its named paths and passes every gate below.

### History Safety

**Do not rewrite shared history.** Amend or rebase only commits that have not
left this machine. When you stop for consent to rewrite pushed history or
force-push a shared branch, say in the same answer what it would cost — other
clones diverge and collaborators may have to rebase, reset, or reconcile
duplicated commits — and name the correction paths you offer, including whether
a later commit can reach the defect at all.

**Never let a scripted rewrite delete live files without a separate confirmed
stop.** When a scripted or looped multi-commit rewrite drops paths from
history, derive each commit's target list from its own tree (`git ls-tree -r`
with a directory's literal prefix), never from `git status` or another
worktree snapshot, which deletes files unrelated to that commit. Confirm range
and tree queries succeeded before trusting an empty result. Print the full
resolved list and require an explicit confirmed stop before any deletion; a
preview a script can run past is not a gate, and a backup is never deletion
authority. Follow `references/history-and-trailers.md`.

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
   generated artifacts. A newly selected untracked artifact needs explicit
   tracking intent or a mandatory repository or owning-workflow coupling;
   relevance, placement, same-session creation, or commit permission only makes
   it a candidate. Split unrelated concerns into separate commits; split only
   when a single honest shared contract cannot cover the whole patch. See
   `references/file-selection.md`.
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
   files present, out-of-scope/ignored files absent, and the diff matches intent.
   A declared verification prerequisite must cover candidate bytes; an incidental
   test report creates no new prerequisite.
7. **Reconcile message to the exact target diff (mandatory internal gate).** Read
   the complete final staged patch and map every material concern to the proposed
   type, scope, outcome, body coverage, and one-commit or split decision. Source
   drift requires reconciliation again. If an accepted decision record binds the
   changed path, stop and report any non-conformance.
8. **Decide amend vs. new.** Create a NEW commit by default. Only `--amend` to
   fix the immediately preceding, unpushed commit. See
   `references/history-and-trailers.md`.
9. **Compose the message.** Conventional Commits `type(scope): summary`
   (imperative, ≤72 chars) naming the outcome, blank line, then a body only when
   it preserves durable context the diff cannot recover. Detect the repo's
   trailer convention first: `git log -5 --format='%H%n%B'`.
10. **Transport the message safely.** For any multi-line body, use a heredoc
   (`git commit -F - <<'EOF' … EOF`, single-quoted delimiter) or `git commit -F
   <file>`. Add or repair authorship trailers with a `git commit ... --trailer
   'Key: value'` command — including `git commit --amend ... --trailer` or `git
   commit -C <ref> --trailer ...` for local rewrites — not by typing them into
   the body or a synthesized message payload. Never embed raw newlines in a
   single `-m`. See `references/history-and-trailers.md`.
11. **Post-verify the stored commit.** Read `git show -s --format=%B HEAD` and
    the committed patch; use `git status --short` to confirm only intended files
    remain. Repair a mismatch only within existing unpushed-history authority.
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
- a user-named path is absent from `git status` → check `git check-ignore -v
  <path>` before deciding. If it is ignored, especially local config or
  secret-like data, do not force-add it merely because the path was named; state
  that the requested scope cannot be fully committed without an explicit
  override after the ignore rule is known.
