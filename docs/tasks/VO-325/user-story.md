# VO-325: Add performance comparison mode to stock detail page

## User Story

# User Story: Performance Comparison Mode — Stock Detail Page

---

## User Story

**As a** retail trader using the stock detail page,
**I want** to overlay multiple stocks or indices on the same chart for a selected time period,
**so that** I can quickly assess how my stock is performing relative to benchmarks or competitors without switching tabs.

---

## Acceptance Criteria

- User can add up to 4 comparison tickers via a search input on the stock detail page
- Comparison tickers render as distinct colored lines on the existing price chart, normalized to % return from the start of the selected period
- Supported time periods: 1D, 1W, 1M, 3M, 6M, 1Y (reuses existing period selector)
- A legend displays each ticker's symbol and period return (e.g., AAPL +12.4%)
- User can remove individual comparison tickers via an "×" control on the legend
- Comparison mode persists across page refreshes (stored in localStorage)
- If a comparison ticker is invalid or data is unavailable, it shows a non-blocking inline error and excludes that ticker from the chart
- Baseline ticker (the page's primary stock) is always visible and cannot be removed

---

## Priority Reasoning

**High.** Comparison is the most natural next step after viewing a single stock — traders always benchmark. This directly increases session depth and makes the detail page a decision-making hub rather than a data display. Theo's instinct here is right; it closes the gap with Bloomberg/TradingView for casual use cases without requiring a full terminal build.

---

## Estimated Complexity

**3 / 5**

Chart normalization logic and multi-series rendering are the core work. API calls are additive (reuse existing price endpoint per ticker). localStorage persistence is lightweight. Main risk: chart library support for dynamic series — needs a spike if not already confirmed.
