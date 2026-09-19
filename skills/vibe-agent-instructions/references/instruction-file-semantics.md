# Instruction-File Semantics and Divergence Evidence

**Evidence date: 2026-08-30.** Report this date at the divergence gate; the
staleness rule is in the workflow reference, step 3.

## Loaders

Claude Code (vendor documentation `code.claude.com/docs/en/memory` and
`.../best-practices`; runtime probes on Claude Code 2.1.251, Linux):

- Reads `CLAUDE.md`, not `AGENTS.md`. For a repository using `AGENTS.md`, the
  documented pattern is a `CLAUDE.md` whose first line is `@AGENTS.md`,
  optionally followed by Claude-specific content; a symlink is the documented
  alternative when there is none. A Windows symlink needs Administrator rights
  or Developer Mode.
- `@path` imports resolve relative to the importing file, nest up to four
  hops, load at session start, and cost the same context as inline text. Plain
  Markdown links are not auto-loaded.
- `CLAUDE.local.md` is appended after `CLAUDE.md` (additive); the docs say to
  Git-ignore it. Block-level HTML comments are stripped before entering
  context.
- Size: target under 200 lines per file; files over 4 MiB are skipped.
  `.claude/rules/*.md` is a Claude-only surface this skill does not emit.
- The Write and Edit tools refuse to write through a symlinked `CLAUDE.md`
  (`anthropics/claude-code#66559`); editing `AGENTS.md` works, and symlinked
  `CLAUDE.md` and `CLAUDE.local.md` files load correctly.
- `/init` in its newer flow reads `AGENTS.md` and other tools' files and
  proposes changes; `/import` appends a one-time copy of `AGENTS.md` into
  `CLAUDE.md`; `/doctor` proposes trims of derivable content.

Codex CLI (vendor documentation; `codex-rs/core/src/agents_md.rs`; CLI
0.150.1):

- Global: `~/.codex/AGENTS.override.md` if present, else `~/.codex/AGENTS.md`.
- In each directory from the project root down to the working directory, the
  first match among `AGENTS.override.md`, `AGENTS.md`, and configured
  fallbacks is used: an override replaces its sibling `AGENTS.md`.
- The selected files are concatenated root-down, and loading stops silently at
  `project_doc_max_bytes` (32 KiB by default), so a large root file starves
  deeper ones. Symlinks are followed.
- The vendor describes the override for temporary or nested overrides, not
  standing personal rules; `openai/codex` Git-ignores `CLAUDE.md`, `.claude/`,
  and `AGENTS.override.md`.

Other consumers (vendor pages, not individually re-verified):

- Cursor reads `AGENTS.md`, `CLAUDE.md`, and `.cursor/rules`; GitHub Copilot's
  coding agent reads `AGENTS.md`, `.github/copilot-instructions.md`,
  `CLAUDE.md`, and `GEMINI.md`. Through a link or import, such consumers load
  the shared rules twice.
- Gemini CLI reads `GEMINI.md` (and `AGENTS.md` only when `context.fileName`
  names it); Amp, Jules, Kiro, and Cline read `AGENTS.md`; Aider reads nothing
  unconfigured.
- The `agents.md` convention: plain Markdown, the nearest nested file wins, no
  size guidance, no personal-file concept.
- Git with `core.symlinks=false` checks a link out as a text file holding its
  target (`git-config(1)`); scripts that write `CLAUDE.md` can replace a link
  with a copy (`github/spec-kit#1464`).
- No tool reads `AGENTS.local.md`: never create it, and treat an existing one
  as unloaded. Only Codex reads `AGENTS.override.md`.

## Known divergences

- **DV1 (material): the local-rules pairing.** Consequence: Codex loads a root
  `AGENTS.override.md` instead of `AGENTS.md`, so an override holding only
  local rules loses every shared rule; no other tool reads that filename, and
  Codex documents it for temporary or nested use. Mitigation: the managed
  block (a discretionary read that context compaction can drop), the loader
  matrix, and the restart notice.
- **DV2 (moderate): the `CLAUDE.md` link mechanism.** Consequence: Claude Code
  documents the `@AGENTS.md` import as the primary pattern; the link needs
  privileges on Windows, arrives as a text file on `core.symlinks=false`
  checkouts, cannot be written through by Claude Code's Write and Edit tools,
  and can be silently replaced by a script's copy. Mitigation: the stub
  fallback with its trigger, the link-integrity classes, and the restoration
  offers.
- **DV3 (compatible): the pointer-based reference folder.**
  Consequence: it matches the 200-line and 32 KiB guidance, but a pointer is
  not auto-loaded, so each needs a specific read-when condition.
- **DV4 (informational): overlap with host commands.** Consequence: Claude
  Code's `/init` and `/doctor` cover part of this work; this skill's distinct
  value is being tool-agnostic, `AGENTS.md`-first, and tying each update to an
  observation, and it is not a replacement for a host command.
- **DV5 (informational): measured value.** Consequence: a 2026 ablation study
  found no measurable correctness gain from context files on either host
  (`arXiv:2607.27250`), and a smell study found bloat and lint leakage in many
  real files (`arXiv:2606.15828`); claim only consistency and reduced
  re-explanation.

Further sources: HumanLayer, "Writing a good CLAUDE.md" (under 300 lines,
pointers with read-when conditions over eager imports); GitHub, "How to write
a great agents.md" (2025-11).
