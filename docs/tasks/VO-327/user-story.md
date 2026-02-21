# VO-327: Implement multi-timeframe toggle for stock charts

## User Story

# VO-374: Multi-Timeframe Toggle for Stock Charts

## User Story

**As a** trader using the Virtual Office platform, **I want** to toggle between multiple time periods on stock charts (1D, 1W, 1M, 3M, 1Y, All), **so that** I can quickly assess price action across different timeframes without leaving the page or opening external tools.

---

## Acceptance Criteria

- [ ] Chart displays a timeframe toggle bar with options: **1D, 1W, 1M, 3M, 1Y, All**
- [ ] Selecting a timeframe updates the chart data and X-axis labels without a full page reload
- [ ] Active timeframe is visually highlighted in the toggle
- [ ] Default timeframe on page load is **1M**
- [ ] Selected timeframe persists if the user navigates away and returns (localStorage)
- [ ] Chart gracefully handles missing data for a given range (e.g., newly listed stock with no 1Y data)
- [ ] Toggle is keyboard-accessible and screen-reader compatible
- [ ] Works on mobile — toggle is touch-friendly and does not overflow on small screens

---

## Priority Reasoning

**High.** Charts are the core analytical surface in Virtual Office. Users currently have no way to contextualize short-term moves against longer-term trends. This is table-stakes functionality for any trading platform and a frequent friction point — users are opening TradingView or Yahoo Finance as a supplement. Closing that gap keeps engagement on-platform.

---

## Estimated Complexity

**3 / 5**

Frontend work is moderate (state management, dynamic data fetch, axis re-rendering). Backend needs timeframe-aware data endpoints if not already parameterized. Main risk is chart library compatibility with dynamic data ranges — needs a spike if we haven't done dynamic reloading before.

---

*Owner: Theo (feature request). Assign to frontend + backend pair.*
