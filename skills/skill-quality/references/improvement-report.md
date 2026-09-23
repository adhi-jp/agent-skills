# Writing an Improvement Report

Read this when writing an improvement report for the agent skill packages in
the repository that contains this file, or when applying one.

That repository holds one package per skill: a `SKILL.md` body that is loaded
whenever the skill is active, conditional `references/`, and an eval suite
under `evals/<skill-name>/evals.json`. You are producing a report, in
`docs/reports/` there, about failures observed in real work — usually in
another repository — so a maintainer can decide what those skills should do
differently. The report changes nothing by itself and is not applied as
written: every proposal is accepted, narrowed, parked, or rejected on its own.

Skill bodies are always-loaded text; every word costs attention and eval
tokens, and rules are rarely deleted. A report that only adds inflates the
package until agents skim it. Write for the smallest change that would have
prevented the failure.

## Record failures, not a catalogue of rules

For each failure state what happened, what the agent read or was told at the
moment of the decision, what it should have done instead, and the evidence
(transcript, command output, sizes, counts). Name the smallest surface that
owns it: one package, one phase, one file. A failure without evidence, or one
a capable agent would not repeat, is not a failure to fix.

## Proposals

Rank them by the failure they prevent. Each proposal names:

- its target file and whether the rule belongs in the always-loaded body or a
  reference;
- the rule itself, one or two sentences, as the agent would read it;
- what it replaces or deletes, or the evidence that no existing rule covers
  the failure;
- the observable behavior change an eval could grade.

Everything you considered and dropped goes in an explicit non-proposals
section with its reason. That section is what stops the next report from
re-proposing it.

## Anti-patterns

- Restating a rule the package already states, in new words.
- A rule for one incident that a capable agent would not repeat.
- New fields, ledgers, receipts, or report shapes with no consumer, no
  demonstrated failure they prevent, and no acceptance criterion they make
  observable.
- A new eval case where extending an existing case's prompt would do.
- A new skill where an existing package already owns that phase.
