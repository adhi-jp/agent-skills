# Durable Records

Read this reference before recording a settled decision, deferring a finding, closing a unit, or starting the phase. It carries the shared decision-record and deferred-findings obligations and, where this phase reads or writes records, their formats; the phase's own boundary text in `SKILL.md` names the directories it may write.

## Decision records

<!-- shared-contract:begin decision-records source=shared/vibe-contract.md -->
**Record a settled decision that binds work beyond the current unit before the next dependent action.**

- A decision qualifies when it constrains work beyond the current unit: structure, interface or contract, data model or persisted format, dependency, build, deployment, security or permission boundary, a convention or policy another unit must follow, or a standing user constraint.
- Require, in addition, at least one of: a viable alternative was rejected; it reverses or supersedes an earlier decision or a default; it settled an ambiguous instruction or a repeated correction; it was AI-selected or proxy-selected with cross-unit effect.
- Read the unit as the piece of work the phase closes and checkpoints, and a decision as settled the moment the deciding actor's answer is recorded: the user's turn, the adopted proxy result, or the gate outcome.
- Never record a choice whose rule and reason are both evident from the code, a choice reversible in one commit with no downstream contract, task sequencing, requirements or acceptance criteria, a residual finding, or a rule with no rationale.
- Record a bug root cause or repair only when it sets a rule another unit must follow; the commit message and regression test carry the rest. Record a spec item only when it sets a durable product constraint or non-goal.
- Record a residual finding only when it sets a lasting policy, citing the finding id; put a rule with no rationale in the project instruction file and link it.
- Treat only the rule as recoverable from the code; rationale, rejected alternatives, and reversals never are, so a decision meeting both criteria is recorded even when its rule is in the diff.
- Write one decision per record and cite the record id from the spec, plan, or ledger instead of restating its rationale.
- Write the record immediately after the decision is settled and before the next dependent action; reconcile status, links, index, and consequences at unit close; sweep for unrecorded qualifying decisions at the finish gate.
- Select a checkpoint or update an implementation progress ledger only when no unrecorded qualifying decision remains.
- Read the decision index and the open-findings index when a planning, execution, repair, review, orchestration, or router-owned phase starts; open only the applicable records and findings; read an accepted record's considered options before proposing an alternative it covers.
- Perform the confirmation checks of the applicable records at review or verification; at commit time, check a diff touching an accepted record's paths for conformance or its superseding record in the same commit, and otherwise report the conflict.
- Hand a decision forward as a carry-forward packet when this phase may not write it: the decision, rejected alternatives, rationale, provenance, scope, and proposed status (`proposed | accepted`); the next writing phase records it.
- Carry a packet in the phase summary and conversation state; report an unpersisted packet at the finish gate as unpersisted, with the one action that would persist it; never claim a packet is durable.
- Ask the user once per repository, at the first checkpoint that would include a record or report, whether records and reports join that repository's checkpoints; write the answer as a record and apply it to later checkpoints.
  - Until the answer exists the file stays untracked and the summary says so; an ignore rule keeps the file local and the summary says so.
- Treat an unratified agent-selected record as an assumption to surface whenever it would narrow a live user request; it binds nothing the user has not accepted.

Example: choosing UTC for persisted timestamps after rejecting local time is recorded although the rule is visible in the code; one retry added to one call is a commit-message fact unless other call sites must follow it.

Exception: a read-only phase or commit execution writes a record only on the user's explicit saved-artifact request; otherwise it hands the packet forward.
<!-- shared-contract:end decision-records -->

## Deferred findings

<!-- shared-contract:begin deferred-findings source=shared/vibe-contract.md -->
**Write every defect or concern discovered but deliberately not addressed to the findings report before the unit closes.**

- Count as a finding a deferred or blocked item, an accepted residual, a scope-blocked plan item, a dropped or later-round contracted item, and any defect or concern outside the unit's scope that the phase chose not to fix.
- Write the entry immediately when the deferral is decided; reconcile entries and the index at unit close and at the finish gate; the chat report names the report path and repeats the open ids.
- Write the report from every state-changing phase except commit execution and from every artifact-only phase, inside the report directory the phase's own text declares.
- Hand a finding forward as a carry-forward packet from a read-only phase or commit execution, carrying its title, severity, scope, evidence, why it was not addressed, who decided, and revisit trigger; write a file only on the user's saved-artifact request.
- Keep the report the one durable carrier for deferred, blocked, unresolved, and accepted-residual items; a plan ledger, debug ledger, review summary, or worker report cites the finding id instead of restating it.
- Never convert a current blocker into a finding to unblock the unit; a finding records work the unit legitimately does not do.
- Read the open-findings index when a planning, execution, repair, review, orchestration, or router-owned phase starts and open the findings whose scope names a path or component the unit touches or whose title names its subject.
- Close a finding by updating its original entry's status and closure fields and its index row when a later unit resolves it; a read-only phase proposes the closure in its packet.
- Record who decided the deferral (`user`, `agent`, or `proxy`); an accepted residual needs recorded user acceptance, and an agent-deferred item is surfaced to the user in the summary.

Exception: when no material unaddressed finding exists at unit close, no report file is created and the summary says so.
<!-- shared-contract:end deferred-findings -->
