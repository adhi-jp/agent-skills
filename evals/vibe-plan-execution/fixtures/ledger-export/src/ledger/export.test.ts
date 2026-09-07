import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { exportLedgerJson } from "./export.ts";

describe("exportLedgerJson", () => {
  it("exports account ledger entries as JSON", () => {
    assert.equal(
      exportLedgerJson([
        {
          accountId: "acct_123",
          timestamp: "2026-05-24T00:00:00.000Z",
          amount: 1250,
        },
      ]),
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
