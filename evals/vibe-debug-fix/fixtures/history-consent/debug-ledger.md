# Preview Cache Repair Ledger

## Symptom
- Reported symptom: preview list keeps stale cards after refresh.
- Expected behavior source: `PreviewCache.test.ts`.
- Observed behavior source: failing local regression from the repaired slice.
- Proven cause: refresh cleanup skipped cards whose source id changed.
- Verification path: `npm test -- PreviewCache.test.ts`.
- Closure status: fixed after the regression passed.

## Repair-owned paths
- `src/preview/PreviewCache.ts`
- `src/preview/PreviewCache.test.ts`

