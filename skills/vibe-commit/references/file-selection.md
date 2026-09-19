# Choosing and Excluding Files

The hardest part of "commit please" is not running git — it is deciding which of
the dirty paths belong in *this* commit. Get this wrong and you either bury an
unrelated change in history or leak a secret. Choose by the user-visible change,
not by directory or file type.

## See the whole picture first

A commit decision needs the full tree:

```sh
git status --short --branch --untracked-files=all   # modified, staged, untracked
git status --ignored                                # ignored paths too
git diff --stat                                      # size/shape of tracked edits
git ls-files --others --exclude-standard             # untracked, ignoring ignored
```

Read new or surprising files before classifying them.

## Separate candidate discovery from lifecycle authority

Discovery makes a path a candidate, not commit-authorized. A new untracked file
needs explicit tracking intent or a mandatory repository/workflow coupling;
relevance, location, or same-session creation is not enough. Keep required
tracked tests, docs, and dependency support with their logical change. State any
deliberately untracked ambiguous path in the summary.

## Select one logical change

A commit is one logical, user-visible change. Group the parts that move together:

- implementation **and** its tests,
- the docs, CHANGELOG, README, or spec the change fulfills,
- the config or fixture the change requires.
- dependency manifests and their lockfiles when the dependency is required by
  the selected implementation.

Split anything whose only connection is "it was dirty at the same time": an
unrelated cleanup, a drive-by typo fix in another module, a refactor riding
along with a feature. Same-session or same-plan provenance is not a reason to
bundle. When two concerns are genuinely independent, make two commits.

Stage by explicit full path so the set is exactly what you chose:

```sh
git add -- src/feature.ts src/feature.test.ts CHANGELOG.md
```

Avoid `git add .`, `git add -A`, and globs while the tree is dirty. Then confirm
with `git diff --cached --name-only` before committing.

## Exclude deliberately

Some dirty paths almost never belong in a feature/fix commit. Recognize and
leave them unstaged:

- generated/build output and run workspaces (stage durable specs, not output);
- agent/tool state, scratch material, and secrets;
- plans and specs unless already tracked as owned changes or independently
  authorized; and
- unrelated lockfiles (keep a matching lockfile with its dependency change).

Respect `.gitignore`. Never force-add an ignored path merely because it was
named; show the matching rule and get explicit confirmation first. For local
config or secret-like data, this blocks including that path. Check with:

```sh
git check-ignore -v <path>     # prints the .gitignore rule and line, or nothing
```

## If a stray slipped into the index

Unstage without touching the working tree, then re-add only what belongs:

```sh
git restore --staged <path>          # repo has commits (HEAD exists)
git rm --cached -r -- <path>         # unborn repo (no HEAD yet), or remove from index
```

`git rm --cached` removes a path from the index but keeps it on disk. Re-inspect
with `git diff --cached --name-only` afterward.
