# Commit Messages

Write for a future reader, not to replay the diff. Use the target patch, recent
repository style, and supplied durable context. If peer reader-visible contracts
share a commit, name their honest shared contract; otherwise return a split
requirement. Do not use same-plan or same-session provenance as cohesion.

## Subject and body

Follow local convention; for Conventional Commits, use `type(scope): outcome`.
Name the behavior or contract, not the editing act.

Use a body only when it preserves value the subject and diff cannot: trigger,
public contract, compatibility or migration, design constraint, non-goal,
accepted risk, or meaningful verification. Preserve source modality. Cut
file-by-file inventories, helper and test lists, generic benefits, and private
implementation names unless they are the only useful durable anchor.

Keep an ordinary body to one to three short paragraphs or a few grouped bullets.
Use a subject-only message for a small or mechanical change with no durable
context. Do not turn a body into a feature walkthrough.

Return a requested message as raw message text, with no Markdown fence or wrapper.
For a repair plus diagnosis, put the diagnosis outside the corrected raw payload.

## References and verification

Keep resolvable anchors: committed paths, public APIs, issue or incident IDs,
commands, error codes, release artifacts, or remote metadata. Do not use ignored
reports, temporary output, local run labels, private tool sessions, unpublished
paths, or chat context as proof. Translate useful local signal to a durable fact
or an explicit absence such as `not measured` or `benchmark not durably recorded`.

`Verification:` is selected proof, not a command log. Use one heading with
adjacent bullets. Keep stable rerunnable commands when useful and say what each
proves when that is not already clear; preserve explicit absence status instead
of inventing proof. Do not inflate validation into runtime, performance, security,
or release proof.

## Transport and trailers

Use one message file, editor buffer, heredoc, or complete payload for a multi-line
message; never one `git commit -m` per line or bullet. Keep adjacent verification
bullets consecutive. Put required trailers in a final footer block, separated from
the body by a blank line, or leave them to the commit workflow's `--trailer`
transport.

After a body commit or amendment, the history-authority workflow inspects
`git show -s --format=%B HEAD`; it corrects malformed stored bytes before reporting
completion. This skill supplies the corrected payload but does not authorize the
history operation.
