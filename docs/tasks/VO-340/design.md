# VO-340: Screen reader accessibility issue in chart rendering

## Technical Design

Here's the design spec I wrote:

---

## Summary

**Root cause:** `PriceChart.tsx` wraps a `lightweight-charts` canvas in a plain `<div>` with zero ARIA semantics — screen readers either skip it or produce noise.

**Fix strategy:** Two-layer approach:
1. **Semantic wrapper** — surround the chart with a `<figure role="img">` that `aria-labelledby` the existing title `<h3>` and `aria-describedby` a new summary element.
2. **Visually-hidden fallback content** — a new `ChartDataSummary` component renders an `sr-only` `<p>` (narrative description: range, open/close, trend) plus a small `<table>` of sampled data points for users who want tabular navigation.
3. The `lightweight-charts` canvas div gets `aria-hidden="true"` so readers don't double-announce.

**Files:**
- `frontend/src/components/charts/PriceChart.tsx` — ARIA wrapper + computed summary data
- `frontend/src/components/charts/ChartDataSummary.tsx` — new, isolated sr-only component

**No schema, API, or route changes needed.**

**Testing:** ESLint `jsx-a11y` enforcement, React Testing Library unit tests on the pure `buildChartSummary` helper and component rendering, plus manual VoiceOver/NVDA smoke tests to confirm announce behavior.
