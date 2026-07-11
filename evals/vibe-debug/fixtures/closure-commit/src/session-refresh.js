const REFRESH_SKEW_MS = 0;

function scheduleRefresh(session, refreshFn, now = Date.now()) {
  const delay = Math.max(0, session.expiresAt - REFRESH_SKEW_MS - now);
  return setTimeout(() => refreshFn(session), delay);
}

module.exports = { scheduleRefresh, REFRESH_SKEW_MS };
