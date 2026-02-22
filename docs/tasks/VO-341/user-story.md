# VO-341: Implement performance comparison mode for stock detail page

## User Story

# User Story: Performance Comparison Mode — Stock Detail Page

---

## User Story

**As a** trader using the stock detail page,
**I want** to overlay multiple stocks on a single chart with normalized performance,
**so that** I can quickly assess relative momentum and make faster, better-informed position decisions.

---

## Acceptance Criteria

- [ ] User can add 1–4 comparison tickers via a search input on the stock detail page
- [ ] Chart normalizes all selected tickers to 100 at the selected period's start (percent-change basis)
- [ ] Supported time ranges: 1D, 1W, 1M, 3M, 6M, 1Y (consistent with existing chart controls)
- [ ] Each ticker rendered in a distinct color with a legend; primary ticker visually dominant
- [ ] Comparison tickers can be individually removed without losing others
- [ ] Performance delta vs. primary ticker displayed per comparison ticker (e.g., "+4.2% vs AAPL")
- [ ] Mode activates/deactivates via a toggle; default state is off
- [ ] Loading and error states handled per ticker (invalid/delisted tickers show inline error)
- [ ] No regression to existing single-ticker chart behavior when mode is off
- [ ] Mobile-responsive — legend collapses gracefully on smaller screens

---

## Priority Reasoning

**High.** Comparative analysis is a daily workflow for active traders. Currently users must open multiple tabs and mentally reconcile charts — this consolidates that into a single view. Direct competitive pressure: most retail platforms (TradingView, Finviz) offer this. High perceived value, low switching cost if we don't have it.

---

## Estimated Complexity

**3 / 5**

Frontend-heavy. Core work is chart normalization logic and multi-series rendering. Backend likely already serves the required OHLCV data per ticker — this is mostly a UI composition problem. Main risk is performance with multiple concurrent data fetches and keeping the chart legible with 4+ series.
