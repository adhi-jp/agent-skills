import { describe, expect, it } from "vitest";

import { exportLedgerJson } from "./export";

describe("exportLedgerJson", () => {
  it("exports account ledger entries as JSON", () => {
    expect(
      exportLedgerJson([
        {
          accountId: "acct_123",
          timestamp: "2026-05-24T00:00:00.000Z",
          amount: 1250,
        },
      ]),
    ).toBe(
      JSON.stringify([
        {
          account_id: "acct_123",
          timestamp: "2026-05-24T00:00:00.000Z",
          amount: 1250,
        },
      ]),
    );
  });
});
