# VO-317: Create API rate limit indicator in data provider status

## User Story

# User Story: API Rate Limit Indicator in Data Provider Status

---

## User Story

**As a** trader using Virtual Office, **I want** to see real-time API rate limit usage for each data provider in the status panel, **so that** I can anticipate data disruptions before they happen and adjust my workflow accordingly.

---

## Acceptance Criteria

- [ ] Data provider status panel displays current rate limit usage (e.g., "420/500 requests/min")
- [ ] Visual indicator (progress bar or color coding) reflects usage severity: green (<70%), yellow (70–90%), red (>90%)
- [ ] Indicator updates in real-time via existing SSE infrastructure — no manual refresh required
- [ ] When rate limit is hit (100%), provider row shows a clear "Rate Limited" state with estimated reset time
- [ ] Each provider tracks its own limit independently (e.g., Alpha Vantage, Polygon, Yahoo Finance)
- [ ] Rate limit data is surfaced via a backend endpoint (`GET /api/providers/status`) that includes `rate_limit_used`, `rate_limit_max`, and `reset_at` fields
- [ ] No alert/notification spam — status updates silently unless user is viewing the panel

---

## Priority Reasoning

**Medium-High.** Rate limit hits cause silent data staleness — the worst kind of failure because users don't know what they don't know. This directly protects trust in the platform's data quality. Theo's instinct is right: visibility here is cheap insurance against user frustration.

---

## Estimated Complexity

**3 / 5**

Backend rate limit tracking is the non-trivial part — requires hooking into each provider's HTTP client to count requests and respect reset windows. Frontend display is straightforward given SSE is already in place.
