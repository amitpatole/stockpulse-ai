# VO-332: Missing input validation in chart rendering allows injection

## User Story

---

## User Story: VO-XXX — Input Validation for Chart Rendering Pipeline

**Priority: P1 — Security/Data Integrity**

---

### User Story

> As a **trader using the platform**, I want **chart data to be validated before rendering**, so that **malformed or injected data cannot corrupt my charts, crash my session, or expose the platform to injection attacks.**

---

### Context

QA identified that the chart rendering pipeline accepts unvalidated data end-to-end — from the Yahoo Finance API response through to the `lightweight-charts` frontend renderer. No boundary checks exist for NaN/Infinity values, mismatched array lengths, OHLC relationship integrity, or type safety. This is an injection surface and a reliability risk.

**Critical files:**
- `backend/core/ai_analytics.py` — returns raw external API data unvalidated
- `backend/data_providers/yfinance_provider.py` — only null-checks `close`, skips OHLC/timestamp validation
- `backend/api/analysis.py` — division without zero-check (line ~179), no range guards
- `frontend/src/components/charts/PriceChart.tsx` — passes data directly to `areaSeries.setData()` with no sanitization

---

### Acceptance Criteria

**Backend — Data Provider Layer**
- [ ] Reject or sanitize values that are `NaN`, `Infinity`, or `-Infinity` in all OHLCV fields
- [ ] Validate OHLC relationships: `Low <= Open <= High`, `Low <= Close <= High`
- [ ] Validate timestamps are positive integers in reasonable range (e.g., 2000–2100)
- [ ] Detect and reject mismatched OHLCV array lengths before processing
- [ ] Guard all division operations against zero (e.g., percent change calculations)

**Backend — API Layer**
- [ ] Validate `period` query parameter against an allowlist (e.g., `1d`, `1mo`, `1y`)
- [ ] Return `400` with a structured error if chart data fails validation — never silently drop records and return partial data as if valid
- [ ] Log validation failures with ticker and field info for observability

**Frontend — Chart Component**
- [ ] Validate each `PriceDataPoint` before passing to `areaSeries.setData()`: reject non-finite `value`, validate `time` is a positive number or valid string
- [ ] Render a user-facing error state (not a blank chart) when data is invalid
- [ ] Remove unsafe `as UTCTimestamp`/`as Time` type assertions; add runtime guards

**Testing**
- [ ] Unit tests covering NaN, Infinity, negative price, mismatched arrays, and zero-division inputs
- [ ] At least one integration test verifying a bad data payload returns `400`, not `500` or silent success

---

### Priority Reasoning

This is **P1**. It's a QA-confirmed injection surface on a data rendering path that processes external API responses. A bad actor or corrupted upstream feed could cause client-side crashes, silent data corruption, or — depending on how the rendering library handles injected strings — a script injection vector. Ships before next release.

---

### Complexity Estimate

**3 / 5**

Straightforward validation logic, but touches 4+ files across backend and frontend. No architectural changes needed. Risk is in coverage completeness, not implementation difficulty. One engineer, one sprint cycle.
