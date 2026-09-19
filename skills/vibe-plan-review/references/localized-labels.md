# Localized Labels

Use this reference for item output, decisions, reflection, and summaries.

## Language Selection

Match the user's language. Preserve non-sensitive paths, commands, identifiers,
and `.<plan-name>.review.md`. In Japanese use the exact labels below; otherwise
translate prose naturally while keeping approved, revise-before-execution, held,
and deleted equivalent. Choice identifiers stay stable in every language.

## Japanese Label Set

Use this exact per-item output shape:

```text
判定: <問題なし | 要修正 | 要確認 | ブロッカー>
指摘:
- <finding or "なし">
推奨アクション: <recommended action>
ユーザー選択肢:
- 1 承認: <meaning for this item>
- 2 修正: <meaning for this item>
- 3 保留: <meaning for this item>
- 4 削除: <meaning for this item>
```

Judgments: `問題なし` (no material issue), `要修正` (revise before execution),
`要確認` (user decision or clarification needed), and `ブロッカー` (cannot safely
continue).

Decisions: `1` `承認` (keep), `2` `修正` (keep after revision), `3` `保留`
(keep unresolved), and `4` `削除` (remove only after reflection confirmation).
Accept one unambiguous label or identifier, including surrounding prose such as
`2でお願いします`; ask when choices conflict. An identifier only decides the
current item, never reflection, scope, or implementation.

## Reflection Semantics

On reflection, approved items remain executable; revised items carry their
accepted revision or a revise marker; held items stay unresolved; deleted items
are removed.
