# VO-336: Support social sentiment badge in stock detail page

## User Story

# VO-386: Social Sentiment Badge — Stock Detail Page

---

## User Story

**As a** trader researching a stock, **I want** to see a real-time social sentiment badge on the stock detail page, **so that** I can quickly gauge market mood from social signals without leaving my research workflow.

---

## Acceptance Criteria

- [ ] A sentiment badge is visible on the stock detail page, near the price header
- [ ] Badge displays a sentiment label: `Bullish`, `Neutral`, or `Bearish`
- [ ] Badge includes a numeric sentiment score (e.g., `+0.72`) and a source indicator (e.g., "Reddit / X")
- [ ] Badge color reflects sentiment: green (bullish), grey (neutral), red (bearish)
- [ ] Sentiment data refreshes on page load; stale data (>1hr old) shows a warning indicator
- [ ] If sentiment data is unavailable, badge displays a graceful fallback ("No sentiment data")
- [ ] Sentiment score is sourced from an existing or new data provider; no hardcoded values
- [ ] Tooltip on badge hover shows: score, source, sample size, and last-updated timestamp
- [ ] Badge renders correctly on mobile viewports

---

## Priority Reasoning

Social sentiment is a high-signal input for retail traders and differentiates this platform from basic data dashboards. Low implementation risk — it's additive UI with a clear data contract. Ships value without touching core trading logic.

**Priority: Medium-High**

---

## Complexity Estimate

**3 / 5**

Data provider integration is the main unknown. UI surface is well-defined and isolated to the stock detail component.
