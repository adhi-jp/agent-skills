# Review Context Format

Used only when `variant == adversarial-review`. SKILL.md Phase 1 step 8 appends the block to the focus text argument with a single blank line between the two sections:

```xml
<review_context cycle="N">
  <intent><![CDATA[<one-sentence change intent from Phase 0 step 7 DoD item 1>]]></intent>
  <previous_fixes>
    <fix cycle="N-1"><![CDATA[<applied finding title + one-line change summary>]]></fix>
  </previous_fixes>
  <angle_request><![CDATA[<one sentence; present only when V=0 override fired in the previous cycle>]]></angle_request>
  <rejected_findings>
    <rejected cycle="N-1" reason="invalid: file not in diff"><![CDATA[<finding title>]]></rejected>
    <rejected cycle="N-1" reason="reject-out-of-scope: DoD explicit out-of-scope"><![CDATA[<finding title>]]></rejected>
  </rejected_findings>
</review_context>
```

- **`<angle_request>` element (optional)**: present only when the previous cycle terminated at step 12 V=0 and the user chose `Run cycle N+1`. Contains a single sentence asking codex to try a different angle. Omit the element entirely when absent.

**Template note**: this block never carries user-declined findings. A user decline is a deferral — codex should remain free to re-raise the same finding next cycle so the user can reconsider. If a template reader is tempted to add a `<rejected reason="user declined">` element, stop: that would let declined valid findings disappear from subsequent cycles and make Case A falsely claim resolution.

Rules:

- Cycle 1 carries `<intent>` (populated from `SKILL.md` Phase 0 step 7 DoD item 1 pre-collection); `<previous_fixes>` and `<rejected_findings>` are empty.
- `<review_context>` is preceded by this literal instruction, on its own line: `Do not re-report findings in <rejected_findings> unless you have a materially different angle.`
- Every user-facing string inside `<!-- CDATA -->` is quoted as-is. No JSON encoding. No HTML entity escaping. The CDATA wrapper keeps any `<`, `>`, `&` in codex output from terminating the block.
- This skill does not use a separate skip ledger. `<review_context>` is the only cross-cycle carry.
- **`<previous_fixes>` window**: the block carries **only the immediately prior cycle (N-1)**, not a cumulative history. Cycle 3's `<review_context>` contains the 5 fixes from cycle 2; it does NOT also enumerate cycle 1's fixes. Each `<fix>` element uses the compact form `<fix cycle="N-1" category="must-fix|minimal-hygiene"><![CDATA[<title>: <≤40 word summary>]]></fix>` — summaries longer than 40 words are forbidden. Codex only needs the latest ground truth for cross-cycle suppression; older history would inflate the context block without improving review quality. **V=0 exception**: when `cycle_history[N-1].no_fix_cycle == true` (prior cycle was a V=0 override retry and emitted no fixes), cycle N's `<previous_fixes>` skips the empty cycle N-1 and carries fixes from cycle N-2 instead. Without this exception, codex would lose context of cycle 1's applied fixes when cycle 2 was V=0 no-fix, causing re-surfacing of already-fixed findings in cycle 3.
- **`<rejected_findings>` sources**: the block aggregates two kinds of prior-cycle rejections — (1) entries in the `rejected_ledger` returned by `review-scope-guard` (scope-triage rejections: `reject-out-of-scope` / `reject-noise`), and (2) `claude_invalid[]` from the prior cycle's validity check. Each rejection renders as its own `<rejected>` element with the `reason` attribute carrying the original category and rationale (e.g. `reason="reject-out-of-scope: DoD explicit out-of-scope"`, `reason="invalid: file not in diff"`). Ledger entries with `count >= 2` render with an extra hint: `reason="reject-noise: already-rejected (count=N)"` so codex sees how persistent the complaint is. **User-declined findings are NOT included** — a decline is a deferral, not a rejection, and codex is free to re-raise the same finding in the next cycle so the user can reconsider it.
