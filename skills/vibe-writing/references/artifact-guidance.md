# Artifact-Specific Writing Guidance

Read this reference for comments, documentation, reports, policy/support copy,
PR descriptions, progress summaries, changelogs, or commit messages.

## Comments

Keep non-obvious rationale, invariants, compatibility rules, failure modes, and
external constraints. Remove comments that merely narrate visible code.

Remove a comment about deleted code with the code. If a non-obvious rule remains,
state that rule positively without naming what was removed. This does not apply to
decision records, plans, changelogs, or commit messages, which may need to retain
superseded decisions and their rationale.

## Documentation, reports, and policy

Match documentation to its reader; do not add setup steps, support channels,
guarantees, rationale, or business value not supplied.

A saved audit, report, or postmortem must state the supplied subject, trigger,
deviation, and current status so it stands without chat context. Do not impose a
template or invent organizational context.

For a claim correction, use the strongest claim authoritative evidence supports
and state any limitation needed to prevent the old broader claim. If no supported
replacement exists, state the boundary for review.

For policy or support copy, clarify supplied facts without adding obligations,
response guarantees, escalation paths, channels, reassurance, or security reasons.

## Changelogs and PR descriptions

Read [changelog.md](changelog.md) for a changelog or release note. Honor a PR
template exactly; preserve supplied absence statuses such as `Not run`.

## Progress and final summaries

Lead with the result and stay brief unless rationale, verification, limitations,
recovery, or comparison is requested. When they differ, separate what ran,
acceptance coverage, unresolved scope, and unverified delegated edits. A green
suite alone is not completion. Do not send a waiting update without a new result,
blocker, decision, policy change, or requested cadence.

## Commit messages

Read [commit-messages.md](commit-messages.md) for a commit message, transport,
or stored-message repair. That reference controls message content, proof, and
formatting; the workflow holding history authority controls staging, authorization,
and history mutation.
