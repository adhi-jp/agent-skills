# Commit Messages

Write for a future reader, not to replay the diff. Use the target patch, recent
repository style, and supplied durable context. If peer reader-visible contracts
share a commit, name their honest shared contract; otherwise return a split
requirement, unless the user keeps them together; then state each change's
reason and why they share the commit. Do not use same-plan or same-session
provenance as cohesion.

## Subject and body

Follow local convention; for Conventional Commits, use `type(scope): outcome`.
Name the behavior or contract, not the editing act.

A commit-message rule the user or repository writes, including one in the
request, overrides the body shape below: its length limits and required sections
bind, its allowance for subject-only messages applies only when subject and diff
already carry the why, and within a limit the why comes first. Fill a required
verification section only from evidence that exists; an unrecorded check is
`not run`. Recent history's habits set subject and trailer style, not message
content. These content rules govern a message being composed or reworded; a
stored-message repair keeps existing body text apart from its defects, which
include malformed bytes and local-only proof.

Write a body whenever subject and diff do not carry why the change exists: the
trigger or cause; each behavior bundled beyond the subject and why it was not
split; a contract, migration, or stored-data effect; a constraint, non-goal,
accepted risk, or rejected alternative; an external ID such as an advisory or
issue; what remains unverified. The why comes first; an unverified note never
replaces it. Preserve source modality. Cut file-by-file inventories, helper and
test lists, generic benefits, and private implementation names unless they are
the only useful durable anchor.

Size follows content: usually one to three short paragraphs or a few grouped
bullets. Use a subject-only message for a mechanical change (lock bumps,
generated syncs) or one whose diff states its own why, such as a changelog
entry, code comment, or test names. Do not turn a body into a feature walkthrough.

Return a requested message as raw message text, with no Markdown fence or wrapper.
For a repair plus diagnosis, put the diagnosis outside the corrected raw payload.

## References and verification

Keep resolvable anchors: committed paths, public APIs, issue or incident IDs,
commands the change affects, error codes, release artifacts, or remote metadata.
Do not use ignored reports, temporary output, local run labels, private tool
sessions, unpublished paths, or chat context as proof. Translate useful local
signal to a durable fact or an explicit absence such as `not measured` or
`benchmark not durably recorded`, never to a check record.

Routine verification (commands run, checks or suites passed, test counts,
reviewer or model credits) is not message content under any heading or label, in
prose, or in any language; it belongs in the workflow's report or PR. Test and
review evidence a handoff carries proves readiness to commit, not message
content. Verification enters a body only as a fact about this change: what was
not or could not be verified; a measurement the claim rests on, with its
conditions and comparison, or an explicit absence such as `not measured`; or a
non-routine check that is itself the proof, such as a packaging build for a
dependency bump, never a rerun of the usual suites. A regression shown failing
before the fix is not body content by default. Credit a reviewer or model only
in trailers the repository convention uses. Do not inflate validation into
runtime, performance, security, or release proof.

## Transport and trailers

Use one message file, editor buffer, heredoc, or complete payload for a multi-line
message; never one `git commit -m` per line or bullet. Keep a bullet list in one
body block. Put required trailers in a final footer block, separated from
the body by a blank line, or leave them to the commit workflow's `--trailer`
transport.

After a body commit or amendment, the history-authority workflow inspects
`git show -s --format=%B HEAD`; it corrects malformed stored bytes before reporting
completion. This skill supplies the corrected payload but does not authorize the
history operation.
