# Message Transport, History Edits, and Trailers

This reference covers getting the message into git intact, choosing between a new
commit and an amend, and keeping authorship trailers correct. The message
*wording* belongs to `vibe-writing`; this is about the bytes git stores and the
history operations around them.

## Amend vs. new commit

Default to a **new** commit. Reach for `--amend` only to fix the immediately
preceding commit that has not been pushed:

- New commit — the normal case, and the only option when HEAD has not moved past
  the branch base (nothing of yours exists to amend).
- `git commit --amend` — fold a fix into the last commit, reword its subject, or
  repair its trailer, **when that commit is unpushed**. Amending a pushed commit
  rewrites shared history; add a follow-up commit instead.

Check the amend-vs-new signal with
`git rev-list --left-right --count <base>...HEAD` — it prints two numbers,
`<behind>  <ahead>`; the second (right) number, your commits past base, is the
ahead count, and 0 ahead means amend is not applicable.

## Transport the message without corruption

Multi-line messages are where shell quoting silently mangles commits. Pick a
transport that preserves bytes:

```sh
# Heredoc — preferred for multi-line bodies and trailers.
# The SINGLE-QUOTED delimiter blocks $-expansion and backticks.
git commit -F - <<'EOF'
feat(scope): summary in imperative mood

Body paragraph explaining why the change exists and what it affects.

Co-Authored-By: Name <email>
EOF

# Message file — equivalent, handy when the body is generated elsewhere.
git commit -F /tmp/commit_msg.txt

# Multiple -m — only for a few distinct SHORT paragraphs (each -m = one paragraph).
git commit -m 'fix(scope): summary' -m 'One-paragraph body.'
```

Pitfalls seen repeatedly:

- A single `-m` with embedded `\n` or raw newlines truncates or mangles the
  message. Use `-F`/heredoc for anything multi-line.
- Repeated `-m` flags for a bullet list split each bullet into its own
  paragraph, inserting blank lines between them. Keep bullets in one body block
  via `-F`/heredoc.
- A double-quoted heredoc delimiter (`<<EOF`) lets the shell expand `$VAR` and
  backticks inside the message. Single-quote it: `<<'EOF'`.
- Markdown code fences pasted into the message become literal bytes and
  contaminate the subject/body. Write the raw message; no fences.

Tooling tendency (from the data): Codex sessions leaned on multiple `-m` plus
`--trailer`; Claude Code sessions favored heredoc/`-F -`. Both are fine. What
both converge on is verifying the stored message afterward.

## Trailers: keep them a real footer

A trailer (`Co-Authored-By`, `Signed-off-by`) is only useful if git parses it as
a footer, not as body prose. The reliable way:

```sh
git commit -m 'feat(scope): summary' --trailer 'Co-Authored-By: Name <email>'
```

`--trailer` makes git place and format the footer correctly. If you instead put
trailers in the body via heredoc/`-F`, they must sit in a footer block: a blank
line after the prose, each trailer on its own `Key: value` line, all last in the
message.

Rules that prevent the common corruptions:

- **Exact token form.** It is `Co-Authored-By` (capital C/A/B, hyphenated) with
  the value `Name <email>` including angle brackets. `Co-authored` or a missing
  `<…>` is not recognized by git, `git blame`, or hosting platforms.
- **No stray `Key: value` ending the body.** A final single line like
  `Verification: passed` right before the trailers gets folded into the trailer
  block and corrupts parsing. End the body with bullets/prose and a blank line,
  then the trailers. If you have a verification section, make it a labeled block
  with bullets, not a one-liner:

  ```text
  Verification:
  - `pytest -q` passed.

  Co-Authored-By: Name <email>
  ```

- **Carry trailers forward when rewording.** `git commit --amend -m '…'`
  replaces the entire message, so it drops trailers already on the commit unless
  you re-add them — re-include every trailer in the same command.
  `git commit --amend --no-edit` instead reuses the full stored message, trailers
  included, so they survive (and `--trailer` then only adds one):

  ```sh
  git commit --amend -m 'feat(scope): reworded summary' \
    --trailer 'Co-Authored-By: Name <email>'
  ```

- **Add trailers only when true.** Use `Co-Authored-By` for genuinely
  agent-authored or collaborative work; use `Signed-off-by` only when policy
  (e.g. DCO) requires it. Do not attach trailers reflexively to a trivial solo
  edit unless repo policy mandates it.

## Authorship trailer by agent and repo convention

Detect the repo's existing convention before committing and replicate it
exactly:

```sh
git log -5 --format='%H%n%B'   # see the precise trailer style already in history
```

Use the authorship trailer that matches the agent which actually authored the
commit, in that agent's exact form, and matching the repo's prior agent commits.
Two forms observed across sessions:

- Claude Code: `Co-Authored-By: Claude Opus 4.x (1M context) <noreply@anthropic.com>`
  — note the model name and the `(1M context)` qualifier and the anthropic.com
  no-reply address. Match the exact model string your environment specifies.
- Codex: `Co-Authored-By: Codex <noreply@openai.com>` — plain `Codex` and the
  openai.com no-reply address.

Pick the one for the agent that wrote the commit; do not invent a format, and do
not attribute the commit to an agent that did not write it.

## Preserve authorship when rewriting

When replaying or rewriting a commit to add a trailer, do not let the rewrite
silently reassign authorship or date:

```sh
git show -s --format='%an %ae %aI' <ref>   # capture original author/date
git commit -C <ref> --trailer 'Key: value' # reuse original message verbatim, append trailer
```

Pass the original author/date (and committer env vars) explicitly when the
operation would otherwise stamp the current identity.

## Always verify the stored message

The command you ran is not proof of what git stored. Confirm the actual artifact:

```sh
git show -s --format=%B HEAD        # full stored subject + body + footer
git log -1 --format=full           # author, committer, and message
git interpret-trailers --parse <<<"$(git show -s --format=%B HEAD)"  # did trailers parse?
git show --stat HEAD               # committed file set
```

If the stored message is wrong — trailer in the body, dropped footer, mangled
newlines — fix it with `git commit --amend` (re-including trailers) while the
commit is still local, then verify again.

## Compact message rules (fallback when vibe-writing is unavailable)

When `vibe-writing` is not available, keep the message usable with these
minimums (vibe-writing's `references/commit-messages.md` is the fuller authority):

- Subject: `type(scope): outcome`, imperative, ≤72 chars, naming the behavior or
  contract that changed — not the editing act.
- No placeholder commit commands. A `git commit` command is allowed only when
  every subject byte is final. Use supplied semantic intent even when it is
  broad; broad and concrete is better than a template. Paths and status output
  can identify type, scope, and file set, but they do not by themselves name the
  outcome. If no behavior or fix class is supplied, read the diff first or stop
  before `git commit`; in response-only command plans, show the
  `git diff -- <path>` or `git diff --cached <path>` inspection step and omit the
  commit command until a concrete subject can be written. A command block or
  heredoc whose subject contains angle-bracket text, unresolved-marker words, or
  instructions to fill the subject later is a shown placeholder command even if
  surrounding prose says not to execute it.
- Body only when it adds durable value the diff cannot recover: the triggering
  failure or review finding, the public/CLI/schema contract, a rejected
  alternative, an accepted risk or non-goal, or verification that changes review
  confidence. Skip file-by-file inventories.
- Small/mechanical changes (lock bumps, generated syncs) are often
  subject-only.
- Keep durable references (issue IDs, error codes, commands, committed paths,
  SHAs); drop local-only provenance (private branch names, temp paths, session
  labels).
