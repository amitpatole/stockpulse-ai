# VO-337: Screen reader accessibility issue in chart rendering

## User Story

> As a **visually impaired user relying on a screen reader**, I want **the price/cost charts to convey their data meaningfully through assistive technology**, so that **I can understand financial trends and agent spend data without depending on visual rendering**.

---

## Background

`PriceChart` (`frontend/src/components/charts/PriceChart.tsx`) renders using `lightweight-charts`, which mounts into a bare `<div ref={containerRef}>` with no ARIA attributes. The canvas-based output is completely opaque to screen readers — users hear nothing, or at best an unlabelled region. This affects:

- The **Daily Spend** chart on the Agents page (`/agents`)
- Any future consumer of `PriceChart`

We already fixed screen reader gaps on the stock detail page (commit `30200ac`). Charts are the remaining blind spot.

---

## Acceptance Criteria

- [ ] The chart container has `role="img"` and an `aria-label` that includes the chart title and the data range (e.g. "Daily Spend chart, Jan 1 – Feb 21, values from $0.12 to $4.87")
- [ ] A visually-hidden `<table>` (CSS `sr-only`) is rendered alongside the canvas, containing the same time/value pairs displayed in the chart; it is updated whenever `data` changes
- [ ] The visually-hidden table has a `<caption>` matching the chart title
- [ ] When `data` is empty, the accessible label reads "No data available" (consistent with the existing empty-state text)
- [ ] The canvas element itself is marked `aria-hidden="true"` to prevent double-announcement
- [ ] No visual regression — the rendered chart appearance is unchanged for sighted users
- [ ] Verified with VoiceOver (macOS) and NVDA (Windows) that a screen reader announces the chart title and can navigate the data table

---

## Priority Reasoning

**Medium-High.** This is a known WCAG 2.1 AA violation (Success Criterion 1.1.1 Non-text Content). We're a fintech product — accessibility failures expose us to legal risk and exclude a real segment of users. We already shipped a fix for the stock detail page; charts are the next highest-visibility gap. Not blocking a release, but should land in the next sprint.

---

## Estimated Complexity: 2 / 5

The fix is contained to a single component (`PriceChart.tsx`). No backend changes. No new dependencies — the accessible table is plain HTML. The main work is deriving the label string from `data` and writing the `sr-only` table render. A single engineer can complete it in one session including manual screen reader verification.
