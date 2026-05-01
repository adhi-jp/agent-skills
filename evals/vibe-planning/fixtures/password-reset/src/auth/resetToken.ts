export type ResetToken = {
  token: string;
  issuedAtMs: number;
  expiresAtMs: number;
};

export function createResetToken(nowMs: number, ttlMs: number): ResetToken {
  return {
    token: "fixture-token",
    issuedAtMs: nowMs,
    expiresAtMs: nowMs + ttlMs
  };
}

export function isResetTokenExpired(token: ResetToken, nowMs: number) {
  return nowMs >= token.expiresAtMs;
}
