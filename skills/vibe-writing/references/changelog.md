# Changelog Entries

## Format

The repository owns the format. Use, in order: the user's instruction,
repository policy, then the existing changelog's observable headings, categories,
ordering, and dates. Conform without restructuring, renaming, or reordering it.
If no format exists, propose rather than impose one.

Return the requested changelog slice directly. Preserve any requested headings;
"entry only" removes wrapper prose, not required headings. Keep the resolved
artifact language. This guidance does not authorize commits, releases, version
changes, or promotion from `Unreleased`.

## Content

Write for the repository's resolved audience. State the changed observable
contract, useful durable anchors, supplied verification or an explicit absence,
and migration guidance for genuinely breaking changes. Lead incompatible removals
with `**Breaking:**`; do not rely on a category or prior deprecation to convey it.

Do not invent impact, security, performance, reliability, rollout, or incident
claims. Internal refactors with no reader-visible effect normally belong only in
commit history. Do not paste Conventional Commit subjects, git-log lines, or PR
titles into entries.

Use evidence a future reader can resolve: committed files, repository or CI
metadata, release artifacts, public documentation, stable commands, or identifiers.
Do not cite ignored local reports, temporary output, local run labels, private
tool sessions, or unpublished paths as proof. Preserve supplied current facts
unless their only stated source is such local material; otherwise translate the
provenance to a durable command or explicit absence status.

Keep `Unreleased` as the current contract, strongest durable verification, and
accepted residual risk. Replace superseded run commentary rather than keeping an
iteration diary or assertion-level analysis.
