# Staging, the Re-Verify Gate, and Recovery

Staging is not committing. Between `git add` and `git commit` there is a cheap
window to catch the large majority of commit mistakes before they become
history. This reference covers the verification gate, partial staging, and how
to recover when something still goes wrong — always preferring the
least-destructive fix.

## The mandatory re-verify gate

After staging and before every commit, confirm what you are actually about to
commit. Looking from several angles catches different failures:

```sh
git diff --cached --name-only   # exact file list — are the right files in, strays out?
git diff --cached --stat        # volume sanity — does the size match intent?
git diff --cached               # read the hunks — is this the change you meant?
git diff --cached --check       # trailing whitespace / line-ending / conflict markers
git status --short              # what remains unstaged, and is that intentional?
```

The file list alone is not enough: read the staged diff. A rename, partial hunk,
or accidental deletion appears there, not in the names.

When the final command will use pathspecs, `--only`, or another option that
could change what `git commit` records, add a command-shape dry run after the
staged-diff gate:

```sh
git commit --dry-run --short -- <path1> <path2>
```

Use this as a safety cross-check for the commit command, not as a substitute for
reading `git diff --cached`; a dry-run summary cannot prove the hunks are the
intended ones.

If a test or deployment is already a commit prerequisite, compare the candidate
bytes with its inputs; partial staging can otherwise make the evidence inapplicable.
An incidental test report creates no new prerequisite or claim of final-byte
coverage.

## Partial staging: only some hunks of a file

When one file mixes in-scope and out-of-scope changes, stage just the relevant
hunks:

```sh
git add -p <file>        # interactively pick hunks (y/n/s to split, e to edit)
git apply --cached <patch>   # apply a specific patch to the index only
```

Partial staging can fail silently — a split that didn't split, a hunk you
skipped that you needed. So treat `git add -p` as needing the same gate: after
selecting, run `git diff --cached <file>` to confirm exactly the intended hunks
landed, and `git diff <file>` to confirm the rest stayed out. Put both commands
in the verification sequence before committing; do not replace the unstaged diff
with a prose note or `git status`, because those do not prove the local-only
hunk still has the intended content.

## Recovery ladder — least destructive first

Match the fix to the mistake. Climb only as far as you must:

```sh
# 1. Unstage (working tree untouched)
git restore --staged <file>      # one file        (HEAD exists)
git reset HEAD                   # everything
git rm --cached -r -- <path>     # unborn repo (no HEAD), or a path NOT yet in HEAD; on a tracked path this STAGES A DELETION

# 2. Undo the last commit, keep the work
git reset --soft HEAD~1          # uncommit, changes stay staged
git reset HEAD~1                 # uncommit, changes stay in working tree (unstaged)

# 3. Fix a just-made local commit in place (only if unpushed)
git commit --amend --no-edit                 # re-stage fix, keep message
git commit --amend --no-edit --trailer '…'   # add/repair a trailer

# 4. Full restart of UNPUSHED work only — destructive, last resort
git reset --hard <known-base>    # to a SHA you captured and the user confirmed
```

Guidance:

- `git restore --staged` needs a HEAD; in an unborn repo it fails with "could
  not resolve HEAD" — use `git rm --cached` instead.
- `git reset --soft HEAD~1` is the workhorse for "undo the commit, I'll re-split
  or fix it" — the changes are preserved and still staged.
- `git reset --hard` and force-push *discard* work. Use `--hard` only to return
  to a SHA you captured beforehand and the user confirmed, and never force-push
  a shared branch (see the safety boundary in `SKILL.md`).
## Transient errors are not fatal

A transient `index.lock: Read-only file system`, a momentary permission error,
or a sandbox I/O hiccup is retryable. Retry the same command (escalating
environment permissions if the setup requires it) rather than deleting
`index.lock` by hand or hacking the index — those workarounds can corrupt state.
