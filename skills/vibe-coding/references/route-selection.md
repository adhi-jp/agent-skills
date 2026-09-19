# Route Selection Reference

Read this before performing a router-owned row, when no commit-execution
specialist is visible, and whenever a commit turn prepares or inspects
commit-message wording. Classification itself is the table and tie-breaks in
`SKILL.md`.

## Direct Implementation

Establish the surface, the acceptance, and the verification from the request
or local evidence before editing. When the surface is clear but acceptance or
verification is not, ask that one question, unless the answer would open a
second surface; then the work is planning. Make the smallest change that meets
the acceptance, run the verification, and report the result; create no spec or
plan. If the edit reveals a defect in existing behavior, a second surface, or
an unsettled acceptance, stop, report it, and classify the next turn to the row
that owns it. Read the decision and open-findings indexes before editing, and
write any qualifying decision record or findings entry before the row closes.

## Maintenance

Work under the repository's own policy: a dependency update includes its
lockfile and the verification that the tree still builds and tests; a build
repair fixes the build and nothing else; a test-only edit changes tests and
their fixtures only; a chore stays within the paths the request names; release
preparation happens only on the user's explicit request, and each release,
version, tag, or push action inside it stays separately consent-bound.
Reader-visible coupling the repository requires, such as a changelog or README
line, is part of the unit. A defect the edit reveals makes the next turn
`debug-and-repair`. Read both indexes before the edit, and write any qualifying
decision record or findings entry before the unit closes.

## Workflow Control

`cancel workflow` clears live routing state; `replace workflow` clears it and
starts the new goal as a new workflow; an unrelated top-level skill or mode
invocation, or a specialist's finish gate with no further related instruction,
ends or suspends `vibe-coding`. A stale-context clarification asks one question
and routes nothing until it is answered. At the finish gate, report an
unpersisted carry-forward packet as unpersisted, with the one action that would
persist it. This row writes nothing.

## Commit Execution

When a commit turn needs message wording and `vibe-writing` is visible, it is
auxiliary authority for the message only: subject wording, body value,
verification wording, durable references, trailers as content, and multi-line
transport shape. History authority stays with the commit workflow, project
rules, and explicit user consent.

When no commit-execution specialist is visible, report
`matched-but-unavailable`. If the user chooses to proceed, run the commit under
the commit-selection contract yourself, with the same file-set, message, and
post-commit checks, taking message guidance from a visible `vibe-writing`, or
otherwise from repository commit rules, recent local history, and any supplied
checkpoint message. A skill that offers only a commit command may help execute
that fallback; it is never the primary route.
