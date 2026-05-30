export type LedgerEntry = {
  accountId: string;
  timestamp: string;
  amount: number;
};

export function exportLedgerJson(entries: LedgerEntry[]): string {
  return JSON.stringify(
    entries.map((entry) => ({
      account_id: entry.accountId,
      timestamp: entry.timestamp,
      amount: entry.amount,
    })),
  );
}
