# Instruction-File Semantics and Divergence Evidence

**Evidence date: 2026-08-30.** Every fact below was gathered or confirmed on
that date. Report this date in every run, and apply the staleness rule at the
end of this document before using the divergence list as the basis for a
decision.

This document is the fixed evidence base for the divergence gate. It records
what each agent host actually does with instruction files, where that behavior
was observed, and the five known divergences between the operating policy this
skill applies and current best practice.

## Evidence labels used here

- `vendor documentation` — the tool vendor's own published documentation.
- `upstream source` — the tool's source code or repository files.
- `runtime probe` — behavior observed locally on a named version and date.
- `secondary source` — practitioner guidance, issue reports, or relayed
  research that was not re-verified against the vendor.
- `empirical study` — published measurement with a citable identifier.

Do not upgrade a label when restating these facts to a user. A relayed report
stays a relayed report.

## Claude Code

Source: `https://code.claude.com/docs/en/memory` and
`https://code.claude.com/docs/en/best-practices`, fetched 2026-08-30
(`vendor documentation`), plus local probes on Claude Code `2.1.251`,
Linux/WSL, 2026-08-30 (`runtime probe`).

- Claude Code reads `CLAUDE.md`, not `AGENTS.md` (`vendor documentation`).
  For a repository that already uses `AGENTS.md`, the documented approach is a
  `CLAUDE.md` whose first line is the import `@AGENTS.md`, optionally followed
  by Claude-specific content. "A symlink also works if you don't need to add
  Claude-specific content" (`ln -s AGENTS.md CLAUDE.md`). On Windows a symlink
  needs Administrator privileges or Developer Mode, so the documentation
  directs Windows users to the import instead.
- Imports resolve relative to the importing file, nest at most four hops,
  skip code spans and fenced blocks, and load at session start. Imported text
  costs the same context as inline text: splitting a file into `@path` imports
  organizes it but does not reduce context. An import resolving outside the
  working directory triggers a one-time approval dialog.
  (`vendor documentation`)
- Plain relative Markdown links are **not** auto-loaded; only `@` imports are.
  A pointer to a reference document is therefore read only when the agent
  decides the stated condition applies. (`vendor documentation`)
- `CLAUDE.local.md` loads alongside `CLAUDE.md` and, within a directory, is
  appended after it — the two are additive, not exclusive. The documentation
  tells users to add `CLAUDE.local.md` to `.gitignore`. The only
  project-level instruction filenames the documentation lists are `CLAUDE.md`,
  `.claude/CLAUDE.md`, and `CLAUDE.local.md`. (`vendor documentation`)
- Block-level HTML comments in a `CLAUDE.md`-family file are stripped before
  the content enters context. A marker written as an HTML comment is therefore
  invisible to Claude Code and visible to every other consumer of the same
  bytes. (`vendor documentation`)
- Size guidance: target under 200 lines per file; longer files consume more
  context and reduce adherence; files over 4 MiB are skipped. An entry that is
  a multi-step procedure, or that only matters for one part of the codebase,
  belongs in a skill or a path-scoped rule rather than in the always-loaded
  file. (`vendor documentation`)
- Content guidance — include: commands an agent cannot guess, style rules that
  differ from defaults, test instructions, repository etiquette,
  project-specific architectural decisions, environment quirks, gotchas.
  Exclude: anything derivable from the code, standard conventions, detailed
  API documentation, frequently changing information, tutorials, file-by-file
  descriptions, self-evident practices. (`vendor documentation`)
- `.claude/rules/*.md` exist as a Claude-specific surface: files without a
  `paths:` frontmatter key load at launch, path-scoped ones load when a
  matching file is read, and the directory supports symlinks. This skill does
  not emit them. (`vendor documentation`)
- Host commands overlap this skill's surface: `/init` suggests improvements
  rather than overwriting an existing `CLAUDE.md`, its newer flow reads
  `AGENTS.md` and other vendors' rule files and presents a reviewable proposal
  before writing; `/import` appends a one-time copy of `AGENTS.md` to
  `CLAUDE.md`; `/doctor` proposes trims of derivable content.
  (`vendor documentation`)
- Issue `anthropics/claude-code#66559` (opened 2026-06-09, open; labels `bug`,
  `area:security`, `reproduced`): the Write and Edit tools refuse to write
  through a symlinked `CLAUDE.md`; reading the link works and editing
  `AGENTS.md` directly works. (`upstream source`, issue tracker)
- Local loading probe, 2026-08-30, Claude Code `2.1.251`: with `CLAUDE.md`
  and a local-rules file both present as symbolic links, a non-interactive
  session reported both files' marker tokens as loaded project instructions —
  the installed version reads symlinked instruction files. (`runtime probe`)
- Local writing probe, same version and date: asked to append a line to the
  symlinked `CLAUDE.md`, the session answered "Refusing to write
  …/CLAUDE.md: it is a symbolic link. Write to the link's target path
  instead." and changed nothing. The refusal message differs from the one in
  the issue above. (`runtime probe`)
- Coverage limit: the probes cover one version on one platform. Symlink
  loading and the write refusal on other hosts and versions are unverified.

## Codex CLI

Source: `https://learn.chatgpt.com/docs/agent-configuration/agents-md`
("Custom instructions with AGENTS.md"), fetched 2026-08-30
(`vendor documentation`); `codex-rs/core/src/agents_md.rs` and `.gitignore` in
`openai/codex` at `main` (`upstream source`); installed Codex CLI `0.150.1`.

- Global scope: Codex reads `~/.codex/AGENTS.override.md` if it exists,
  otherwise `~/.codex/AGENTS.md`. (`vendor documentation`)
- Project scope: from the project root down to the current directory, in each
  directory along the path Codex checks `AGENTS.override.md`, then
  `AGENTS.md`, then any configured fallback names, and uses **the first match
  in that directory**. An `AGENTS.override.md` therefore *replaces* the
  sibling `AGENTS.md` instead of adding to it. (`vendor documentation`;
  confirmed in `agents_md.rs`, whose candidate list pushes
  `AGENTS.override.md`, then `AGENTS.md`, then configured fallbacks, and
  whose per-directory probe returns on the first match — `upstream source`)
- Codex concatenates the selected files from the root down, skips empty
  files, and stops adding files once the combined size reaches
  `project_doc_max_bytes` (32 KiB by default). The budget is consumed
  root-first and an over-budget document is truncated, so a large root file
  starves the files nearer the working directory, silently.
  (`vendor documentation`; `upstream source`)
- Discovery runs "from the project root to the current working directory,
  inclusive. Symlinks are allowed." (`upstream source`)
- The vendor describes the override file for "temporary global overrides or
  nested directory-specific rules without modifying the base file" — not for
  standing personal rules. (`vendor documentation`)
- `openai/codex/.gitignore` lists, under a "cli tools" heading, `CLAUDE.md`,
  `.claude/`, and `AGENTS.override.md`: OpenAI treats its own override file,
  and any `CLAUDE.md`, as untracked local files. (`upstream source`)
- One user report, `openai/codex#15421`, says a global
  `~/.codex/AGENTS.override.md` was ignored in practice; unresolved.
  (`secondary source`)
- Relayed report that Codex did not follow symlinks before version `0.138`;
  the installed `0.150.1` and the current source allow them.
  (`secondary source`)

## The agents.md convention

Source: `https://agents.md/`, fetched 2026-08-30 (`vendor documentation` for
the convention itself).

- `AGENTS.md` is plain Markdown with no required sections and no prescribed
  headings. Suggested sections are an overview, build and test commands,
  style, testing, security, pull-request conventions, and "anything you'd tell
  a new teammate".
- Nested files: the closest one takes precedence.
- The convention is stewarded by the Agentic AI Foundation under the Linux
  Foundation. The compatibility list names 23 tools; the word "Claude" does
  not appear on the page.
- There is no size guidance, no personal- or local-file concept, and no formal
  specification document — the upstream repository holds the website source
  and a README only. (`upstream source`)

## Git symlink materialization

Source: local `git-config(1)` manual, Git `2.43.0` (`vendor documentation`).

- `core.symlinks`: "If false, symbolic links are checked out as small plain
  files that contain the link text." The default is true, except that clone
  and init probe the filesystem and set it false when appropriate at
  repository creation.
- Consequence: a committed symbolic link materializes as a one-line text file
  on any checkout where the probe failed. The setting governs checkout
  materialization, not whether the generating host can create links, so a link
  created successfully here can still arrive as text on a teammate's machine.
- Related failure mode in the wild: `github/spec-kit#1464` — a maintenance
  script wrote through `CLAUDE.md` without checking for a link and replaced
  the link with a regular file on every run. `anthropics/claude-code#1388`
  and `#55791` report that symlinked Markdown is loaded but dropped from
  discovery and autocomplete listings. (`secondary source`, issue trackers)

## Secondary consumers

Gathered from vendor pages by a research worker and not individually
re-fetched; treat as `secondary source` for this skill's purposes and verify
before relying on any one of them.

- Cursor CLI reads `AGENTS.md` and `CLAUDE.md` natively, alongside
  `.cursor/rules`.
- GitHub Copilot's coding agent reads `AGENTS.md` (root and nested) plus
  `.github/copilot-instructions.md`, `CLAUDE.md`, and `GEMINI.md`.
- Gemini CLI reads `GEMINI.md` and needs `context.fileName` configured to
  include `AGENTS.md`.
- VS Code has an experimental `chat.useAgentsMdFile` setting, on by default.
- Amp, Jules, Kiro, and Cline read `AGENTS.md` natively. Aider auto-reads
  nothing without configuration. Windsurf's documentation redirects to Devin.
- Consequence for the loader matrix: a repository whose inventory shows Cursor
  or Copilot files has consumers that read **both** `AGENTS.md` and
  `CLAUDE.md`, so a link or import makes them load the shared rules twice.
- Unverified: precedence between `AGENTS.md` and
  `.github/copilot-instructions.md` when both exist.

## Negative results

- **No tool recognizes a filename `AGENTS.local.md`.** Checked against the
  Codex candidate list in `agents_md.rs`, the Claude Code documentation's
  list of project-level filenames, the agents.md page, and the vendor pages
  for the secondary consumers above. Never introduce that filename, and treat
  an existing one in a target repository as a file no agent loads.
- **No tool other than Codex recognizes `AGENTS.override.md`**, and no
  cross-tool convention for personal local rules exists.
- **No tool auto-ignores its own local file**, except Claude Code's opt-in
  personal option during its newer initialization flow.
- Unverified: whether Codex's initialization command preserves an existing
  `AGENTS.md` on re-run. Its documentation says it "scaffolds a starter
  AGENTS.md" and does not document overwrite behavior.

## Measured value

- `arXiv:2606.15828` (2026-06) catalogues configuration smells across 100
  `AGENTS.md` files: lint leakage 62%, context bloat 42%, skill leakage 35%.
  (`empirical study`, abstract read)
- `arXiv:2607.27250` (2026-07-28), 288 runs across Claude Code and Codex on
  17 real tasks: "Context strategy does not measurably move correctness on
  either agent (bounded to <=10-15pp via equivalence testing)"; observed
  failures came from implementation skill rather than missing repository
  knowledge. (`empirical study`, abstract read and citation verified)
- Practitioner guidance (`secondary source`): HumanLayer, "Writing a good
  CLAUDE.md" — "< 300 lines is best, and shorter is even better"; it warns
  against eager `@` imports and recommends a plain pointer with a read-when
  condition to a documentation directory, calling that progressive
  disclosure. GitHub's blog, "How to write a great agents.md" (2025-11),
  recommends commands, testing, structure, style, workflows, and boundaries,
  and publishes no statistics.
- Consequence for how this skill talks about itself: state its value as
  consistency and reduced re-explanation. Do not claim a correctness,
  quality, or speed improvement — no measurement supports one.

## Known divergences

These are the five known differences between the operating policy this skill
applies and current published best practice. Report them by these labels, with
the evidence date, and ask how to proceed before applying the policy, unless
the user's current instruction has explicitly acknowledged these divergences —
in which case still report them with the evidence date before applying
anything. The labels are defined here and used nowhere else.

### DV1 (material) — the local-rules pairing

The policy keeps additional personal rules in `AGENTS.override.md` and links
`CLAUDE.local.md` to it. Under Claude Code the local file is *additive*, so
this works. Under Codex a root `AGENTS.override.md` *replaces* `AGENTS.md`, so
a file holding only local rules makes Codex lose every shared rule. The same
bytes cannot satisfy both loaders unaided. Codex documents the override file
for temporary or nested-directory use rather than standing personal rules, no
other tool recognizes the filename, and OpenAI Git-ignores it in its own
repository.

Consequence and mitigation: the managed block at the top of the override file
tells the reading agent to read `AGENTS.md` first. That is a discretionary
read, not a durable auto-load: it can be dropped at context compaction, and a
Codex session that started while the block was missing or malformed has
already missed the shared rules. Hence the report's loader matrix, the
restart-sessions notice after any block creation or repair, and the rule that
the block stays at the top of the file. A user who deletes the block returns
Codex to this failure until the next run restores it.

Sources: Codex vendor documentation and `agents_md.rs`; Claude Code memory
documentation; `openai/codex/.gitignore`.

### DV2 (moderate) — the `CLAUDE.md` link mechanism

Claude Code documents the `@AGENTS.md` import stub as the primary pattern and
the symbolic link as the alternative for the case where no Claude-specific
content is needed. The policy prefers the link. A link costs no extra context,
but: it needs privileges on Windows; it materializes as a plain text file on
`core.symlinks=false` checkouts; Claude Code's Write and Edit tools refuse to
write through it (editing `AGENTS.md` directly works, which is what the policy
intends); and third-party scripts that write `CLAUDE.md` can silently replace
the link with a copy. The installed Claude Code reads a symlinked file
correctly. Tools that natively read both filenames load the shared rules
twice.

Consequence and mitigation: the stub fallback with a reported trigger, the
link-integrity classification in update mode, and the restoration offers for a
materialized link or a copy.

Sources: Claude Code memory documentation; `anthropics/claude-code#66559`;
the local writing and loading probes; `git-config(1)`; `github/spec-kit#1464`.

### DV3 (compatible) — the pointer-based reference folder

Keeping `AGENTS.md` short and pushing procedures into a reference folder
matches Claude Code's under-200-line target, HumanLayer's under-300-line
guidance, and Codex's root-first 32 KiB budget; the agents.md convention
imposes no structure. A plain relative path with a read-when condition is the
progressive-disclosure pattern, and unlike an `@` import it does not load
eagerly.

Consequence: because a plain pointer is followed only when an agent decides
the condition applies, the read-when condition must be specific — a vague
"read for more detail" makes the procedure unreachable in practice. Claude
Code's own documentation names skills and path-scoped rule files as its
on-demand mechanisms; emitting those is a possible later addition, not part of
this policy.

Sources: Claude Code best-practices and memory documentation; HumanLayer;
agents.md; Codex vendor documentation.

### DV4 (informational) — overlap with host commands

Claude Code's newer initialization flow already reads `AGENTS.md` and presents
a reviewable proposal before writing, and its doctor command proposes trims of
derivable content. This skill overlaps that surface.

Consequence: the distinct value is being tool-agnostic, `AGENTS.md`-first, and
running a verifiable update mode that ties every changed claim to a repository
observation. Do not present this skill as a replacement for a host command,
and do not reproduce a Claude-only initialization.

Source: Claude Code vendor documentation.

### DV5 (informational) — measured value

The 2026 ablation study found no measurable correctness gain from context
files on either host, and the smell study found bloat and lint leakage in a
large share of real files. Neither contradicts the policy — both argue for
short, non-redundant, pointer-based files — but they do bound what may be
claimed.

Consequence: state the value as consistency and reduced re-explanation.
Never state or imply a correctness or quality improvement, in the generated
files, in the run report, or in any summary.

Sources: `arXiv:2607.27250`; `arXiv:2606.15828`.

## Staleness rule

The evidence date above is 2026-08-30.

- If the current date is within six months of the evidence date, report the
  divergences as current and proceed once the user answers.
- If the current date is more than six months after the evidence date, label
  the comparison **possibly stale** in the report and ask the user whether to
  proceed on this evidence or to supply fresher evidence, before applying the
  policy.
- Fresher evidence the user supplies takes precedence over this document for
  the items it covers. Record which items it replaced, and keep the rest of
  this document in force.
- This document is not refreshed from the network at run time. Changing it is
  a maintenance change to this skill package, not a run-time action.
