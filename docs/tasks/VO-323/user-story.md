# VO-323: Create API rate limit indicator in data provider status

## User Story

# User Story: API Rate Limit Indicator in Data Provider Status

**VO-381** | Submitted by: Theo

---

## User Story

As a **trader using the Virtual Office platform**, I want to **see real-time API rate limit usage for each data provider in the status panel**, so that **I can proactively manage my data requests and avoid hitting limits that would disrupt my research workflow**.

---

## Acceptance Criteria

- [ ] Data provider status panel displays current rate limit usage (e.g., "847 / 1000 requests used")
- [ ] Visual indicator (progress bar or color-coded badge) reflects usage: green (<70%), yellow (70–90%), red (>90%)
- [ ] Indicator updates in real-time or on a configurable polling interval (default: 30s)
- [ ] Shows reset time countdown when limit is at or near capacity (e.g., "Resets in 4m 32s")
- [ ] Each provider tracked independently (e.g., Alpha Vantage, Polygon, Yahoo Finance shown separately)
- [ ] Graceful degradation if a provider does not expose rate limit headers — show "Limit unknown"
- [ ] Clicking the indicator opens a detail tooltip with: requests used, limit ceiling, window duration, reset timestamp
- [ ] Backend exposes a `/api/providers/rate-limits` endpoint returning structured rate limit state per provider

---

## Priority Reasoning

**Medium-High.** Users hitting silent rate limits is a recurring pain point — it causes data gaps and chart errors with no clear explanation. This feature turns a frustrating black box into actionable visibility. Low implementation risk, high trust dividend.

---

## Estimated Complexity

**3 / 5**

- Backend: intercept and parse rate limit headers per provider, persist state in memory or lightweight cache
- Frontend: extend existing status panel UI, add polling logic
- Edge cases: providers with no standard headers, burst vs. rolling windows
