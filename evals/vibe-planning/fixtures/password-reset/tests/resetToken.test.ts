import { describe, expect, it } from "vitest";

import { createResetToken, isResetTokenExpired } from "../src/auth/resetToken";

describe("reset token expiry", () => {
  it("accepts a newly issued token", () => {
    const token = createResetToken(1_700_000_000_000, 15 * 60 * 1000);

    expect(isResetTokenExpired(token, token.issuedAtMs)).toBe(false);
  });
});
