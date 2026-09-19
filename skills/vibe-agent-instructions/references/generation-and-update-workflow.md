# Generation and Update Workflow

Run the steps in this order; steps 1-3 can each stop the run before anything
is written. The preview, advance-confirmation, and divergence rules are in
SKILL.md Boundaries.

## 1. Inventory

Before any write, record for each root instruction file: its path; its state
(`absent`, `regular file`, or `symbolic link` with its target); whether it is
tracked (`git ls-files -- <path>`); and whether it is ignored
(`git check-ignore -v -- <path>`). Cover `AGENTS.md`, `AGENTS.override.md`,
`CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/`, and any other tool's file
present (`GEMINI.md`, `.github/copilot-instructions.md`, `.cursor/rules`, ...);
other tools' files feed the loader matrix and are never generated or edited.

- A pre-existing root `AGENTS.override.md` is reported with its consequence:
  Codex reads it instead of `AGENTS.md`. If it is tracked, step 2 stops;
  otherwise its rules are kept and the managed block is inserted or repaired
  (step 8).
- With no shell tool, or outside a Git repository, report tracked and ignored
  as `unknown` and ask about every ignore or tracking decision; with no shell,
  derived files use their stubs (step 6).
- When the user states that the target repository's tracked or ignored state
  differs from what this checkout's Git reports, use the stated state and
  label it user-supplied, not observed.

## 2. Conflict stops

These run right after the inventory and take precedence over every later step
for the same file. A stop on one file does not cancel work on the others.

- **Tracked personal file.** `AGENTS.override.md` or `CLAUDE.local.md` is
  tracked: do not write, link, or repair it. Report the path and the reason
  `tracked` (personal rules belong outside shared history), and ask how to
  proceed.
- **Ignored shared or derived file.** An ignore rule matches `AGENTS.md`,
  `CLAUDE.md`, or the reference folder (checked again once step 5 chooses the
  folder): do not write it. Report the rule with its source file and line, and
  offer two options: a previewed change to the ignore rule, or recording the
  repository as non-conforming and leaving the file alone.

## 3. Divergence gate

Report DV1-DV5 from `instruction-file-semantics.md` by label, each with its
consequence, together with the evidence date and whether the evidence is
current (within six months of that date) or **possibly stale** (older). When
it is possibly stale, also ask, before applying anything, whether to proceed
on it or supply fresher evidence. Fresher evidence the user supplies replaces
the items it covers; say which. Do not refresh the evidence from the network
at run time.

Record the user's acceptance of a divergence, or a repository recorded as
non-conforming, as a decision record written with the confirmed change set.

## 4. Repository analysis

Every claim in `AGENTS.md` comes from something read in this repository:
manifests, lockfiles, and task runners; CI workflows (the commands that gate
merges); scripts and Makefiles; the test layout; existing developer docs;
formatter, linter, commit, and branch conventions; recorded environment
quirks. Never assert an unverified command: omit it or list it as unverified.

## 5. `AGENTS.md` and reference documents

Include a one-line purpose; commands an agent cannot guess (setup, build,
test, lint, release); conventions that differ from defaults; etiquette
enforced here; architectural decisions that constrain edits; environment
quirks; the read-when table; and, when a derived file exists, the maintenance
line. Exclude anything derivable from the code, standard conventions, API
docs, tutorials, a restated README, a file-by-file map, frequently changing
facts, rules a linter enforces, and every multi-step procedure, which goes to a
reference document.

Reference folder: reuse a recognizable existing developer-docs location,
naming it and why; ask when more than one candidate exists or the fit is
unclear; otherwise use `docs/agents/`. Never move or rewrite existing docs;
point at them. Each read-when entry gives a relative path and a specific
trigger ("before changing the release workflow", "when a test fails only in
the container"). Every listed path exists and holds the procedure it is cited
for.

Update mode, when `AGENTS.md` exists: compare each factual claim with the
repository. Tie every added, rewritten, or removed claim in the report to a
named observation (a path, a command, or its output), and change no claim
without one. Keep human-authored rules you cannot verify verbatim and list
them as unverified. Remove nothing silently.

## 6. Derived `CLAUDE.md`

Create the link with `ln -s AGENTS.md CLAUDE.md`, verify that it resolves, and
report it. Write the stub instead (exactly `@AGENTS.md`, nothing else) when no
shell tool is available, link creation fails, or the target repository's
`core.symlinks` is false; report which trigger held. Never copy content into a
derived file.

A regular `CLAUDE.md` with content keeps its Claude-specific part: the file
becomes `@AGENTS.md` as its first non-comment line followed only by that part,
and its shared part moves into `AGENTS.md`, never kept in both.

In update mode, after the conflict stops, classify each existing regular
derived file by path and report its class:

| File | Class | Recognized by | Disposition |
| --- | --- | --- | --- |
| `CLAUDE.md` | link text | one line naming `AGENTS.md` (a link materialized on a `core.symlinks=false` checkout) | restore the link |
| `CLAUDE.md` | identical copy | byte-identical to `AGENTS.md` | restore the link |
| `CLAUDE.md` | conforming import | first non-comment line is `@AGENTS.md` | leave it |
| `CLAUDE.md` | diverged copy | anything else | show the diff against `AGENTS.md`; convert to the import-plus-remainder shape |
| `CLAUDE.local.md` | link text | one line naming `AGENTS.override.md` | restore the link |
| `CLAUDE.local.md` | exact stub | exactly `@AGENTS.override.md` | relink if a link is now possible; otherwise leave it |
| `CLAUDE.local.md` | other content | anything else | move the content into `AGENTS.override.md` below the managed block, then restore the link |

A restoration writes the link, or the stub when a step-6 trigger holds. Every
change here goes through the preview; `CLAUDE.local.md` changes wait for
step 7. User content is never discarded.

## 7. Ignore placement

`AGENTS.override.md` and `CLAUDE.local.md` stay Git-ignored. Settle the
placement before writing either one. It is settled when the user chose it, the
current instruction names it, or the inventory shows both personal paths
already ignored. Otherwise stop: show the pending personal-file contents and
both options with the exact ignore-file change, and ask:

- a `.gitignore` entry, the recommended choice (team-visible; matches vendor
  guidance);
- a `.git/info/exclude` entry (this checkout only).

Creating an absent `.gitignore` is part of this choice. The personal files and
the ignore change are previewed, confirmed, and applied as one change set.

## 8. Local rules and the managed block

Personal rules go only in the root `AGENTS.override.md`, written after step 7.
The file starts with exactly these four lines, followed by the user's rules:

```
<!-- vibe-agent-instructions: local-rules block start -->
<!-- Personal local rules for this repository. Not committed. Not the shared rules. -->
Before applying the rules below, read `AGENTS.md` in this repository's root directory (the directory containing this file) unless it is already in your context; it holds the shared rules.
<!-- vibe-agent-instructions: local-rules block end -->
```

Repair: with both markers present, replace the lines between and including
them; with one marker or none, insert a fresh block at the top. No line outside
the block is deleted, reordered, or reworded.

Then create `CLAUDE.local.md` with `ln -s AGENTS.override.md CLAUDE.local.md`,
or its stub `@AGENTS.override.md` when a step-6 trigger holds.

Whenever the block is created or repaired, tell the user to restart running
agent sessions or have them re-read the files: Codex loads the override
instead of `AGENTS.md` and reaches the shared rules only through the block's
third line, so a session started before the block existed has missed them.

## 9. Size guard

Report the `AGENTS.md` line count against the under-200-line target, and the
bytes Codex auto-loads (the file it selects in each directory from the root to
the working directory, override before `AGENTS.md`) against
`project_doc_max_bytes`: 32 KiB unless the repository or host configures
another value; say which applies. Report an excess as a finding, since Codex
silently stops loading at the limit, root first.

## 10. Report

Give these sections in order:

1. **Inventory**: the step-1 table, naming `AGENTS.md` and
   `AGENTS.override.md` as sources and `CLAUDE.md` and `CLAUDE.local.md` as
   derived.
2. **Divergence check**: the labels, the evidence date, current or possibly
   stale, the user's answer or the open question, and any decision-record
   path.
3. **Changes**: every path created, modified, linked, or previewed and not
   applied; the preview of each changed existing path; each derived file's
   class; the observation behind each update-mode claim change; any stub's
   trigger; conflict stops and why; the ignore placement; and the restart
   notice when the managed block was created or repaired.
4. **Loader matrix**: for Claude Code, Codex, and each other consumer the
   inventory found, what it auto-loads, what it reaches only through a pointer
   (Codex's discretionary read of `AGENTS.md` through the managed block), and
   what is missing; note consumers that read both `AGENTS.md` and `CLAUDE.md`
   and so load the shared rules twice.
5. **Sizes**: step 9.
6. **Unverified items**: preserved unverifiable rules, unconfirmed commands,
   and `unknown` fields.
7. **Next actions**: reviewing and committing the working-tree change, open
   questions, and nested package-level instruction files not generated.
