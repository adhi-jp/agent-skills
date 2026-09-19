# Plan Boundary Controls

Use this file before finalizing a plan that incorporates review comments,
diagnostic findings, audit output, or analyzer warnings, or that gained
additions after its success criteria were written. It decides what belongs in
the plan body, what is deferred, and when iteration stops.

## Plan-Content Classification

Classify every candidate addition; when one fits several classes, use the one
further down this list:

- `spec-level` — goal, success criteria, scope, behavior contract, ambiguity,
  deferred decision: main plan body.
- `proof-level` — verified facts, evidence labels, `Unproven` triage, proof
  path: main plan body.
- `test-level` — acceptance, regression, proof, and equivalence tests: main
  plan body.
- `impl-detail` — pseudocode, control flow, names, signatures, code sketches:
  deferred unless it proves the current slice feasible or is needed to write a
  current-slice test, with that reason stated inline. Cosmetic renames,
  reordering, or prose polish never qualify.
- `history-only` — past revisions, already-actioned feedback, narration of how
  the plan was reached: omitted, or one or two lines when it still explains a
  current decision.

Walk every addition since the previous plan version through this list before
emitting the plan; the resulting plan shape is the record, not a meta-section of
rejections.

## Success Criteria Freeze

Once the current-slice success criteria are written, they are frozen. An
addition is admissible only when it cites a new or restated user requirement, a
newly verified `Primary source` or `Local investigation` constraint the original
criteria missed, or a `must preserve` equivalence dimension that turned out
non-equivalent (which also escalates the plan to `strict`). "Review suggested
it", "for completeness", or "while we are here" is not a basis; such items go to
deferred decisions or `Risks and unproven items` with impact, `Phase
relevance`, fastest proof path, and revisit trigger.

## Diagnostic-Finding Restraint

Treat each diagnostic finding, review comment, audit item, or analyzer warning
as a bounded input:

1. Map it to the smallest change that makes that exact finding false.
2. Check whether an existing contract already covers it and only needs clearer
   placement, wording, or cross-reference.
3. Defer adjacent hardening, detector expansion, new modes, extra fixture
   families, and new policy surfaces unless the finding explicitly requires
   them or new evidence proves the narrow correction cannot work; record them as
   deferred decisions, not current criteria. A later reviewer request for one
   goes through the freeze again.

Keep one authoritative `Review findings and dispositions` table in a
finding-driven plan: accepted rows are the repair queue, and rejected, deferred,
and blocked rows keep their closing evidence. Derive checkpoint scope from the
accepted rows; never keep a second repair or checkpoint list that can drift.

## Completion Gate

Stop iterating and deliver the plan when, for the current slice, no `Unproven`
item remains a `current-slice implementation blocker` (risk level alone exempts
nothing), any behavior inventory is complete with evidence labels, any
equivalence analysis leaves no dimension `Unknown`, selected failure-pattern
sections are cleared with their near-miss note, every success criterion cites
an admissible basis, and tests or proof checks are specific enough to implement
against. Passing the gate makes the plan ready for review and handoff; it never
authorizes implementation around an open blocker, and it is not a budget for
more detail — once it passes, add no more `impl-detail`, speculative options, or
review-driven criteria.
