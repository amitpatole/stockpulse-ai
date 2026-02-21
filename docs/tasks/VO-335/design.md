# VO-335: Screen Reader Accessibility Issue in Chart Rendering

## Technical Design Spec

---

## Approach

`PriceChart.tsx` renders a `lightweight-charts` canvas element inside a bare `<div>` with no ARIA semantics. Screen readers skip it entirely or announce meaningless noise. The fix is:

1. Annotate the chart container with `role="img"` and a dynamic `aria-label` derived from the data.
2. Inject a visually-hidden `<table>` with a condensed data summary (first/last price, min/max, trend) that screen readers can traverse.
3. Hide the canvas from the accessibility tree (`aria-hidden="true"` on the container div that `lightweight-charts` owns) so readers don't double-announce.

No new dependencies. No backend or schema changes.

---

## Files to Modify / Create

| File | Change |
|---|---|
| `frontend/src/components/charts/PriceChart.tsx` | Add ARIA wrapper, visually-hidden summary table, aria-hidden on canvas div |
| `frontend/src/components/charts/ChartDataSummary.tsx` | **New** — isolated presentational component for the sr-only table; keeps PriceChart readable |

---

## Data Model Changes

None.

---

## API Changes

None.

---

## Frontend Changes

### `PriceChart.tsx`

- Wrap the chart `<div ref={containerRef}>` in an outer `<figure>` with `role="img"` and `aria-labelledby` pointing to the title `<h3>` (already rendered) and `aria-describedby` pointing to the summary element.
- Pass `aria-hidden="true"` to `containerRef`'s div so the raw canvas is invisible to the accessibility tree.
- Derive a concise label string from `data`: first date, last date, open value, close value, direction (up/down/flat). Pass to `ChartDataSummary`.

```
// Computed from data prop:
const summary = useMemo(() => buildChartSummary(data), [data]);
```

`buildChartSummary` (co-located helper): returns `{ firstDate, lastDate, min, max, open, close, trend }` — pure function, easy to unit test.

### `ChartDataSummary.tsx`

Renders a `<div className="sr-only">` containing:
- A one-line description: `"Price chart: [title]. From [firstDate] to [lastDate]. Range $[min]–$[max]. Opened at $[open], closed at $[close] ([trend])."` as a `<p>`.
- A `<table>` with a small sample of data points (first, last, and up to 5 evenly-spaced intermediates) for users who want to navigate tabularly.

### `PriceChartProps` interface additions

```ts
interface PriceChartProps {
  data: PriceDataPoint[];
  title?: string;
  height?: number;
  color?: string;
  // existing ↑
  symbol?: string;   // optional, enriches aria-label ("AAPL price chart")
}
```

No breaking changes — `symbol` is optional.

---

## Testing Strategy

**Linting / static:**
- Enable `eslint-plugin-jsx-a11y` rules explicitly in `frontend/eslint.config.mjs` (plugin is already in node_modules). The `role="img"` + `aria-label`/`aria-labelledby` pair will be enforced going forward.

**Unit tests (install React Testing Library once for frontend):**
- `buildChartSummary` pure function: assert correct `trend`, `min`, `max`, first/last dates for a known fixture array.
- `ChartDataSummary`: render with fixture data → assert `.sr-only` element present, assert table has correct row count.
- `PriceChart`: render with `data=[]` → assert "No chart data available" text; render with data → assert `role="img"` on figure, assert `aria-hidden="true"` on canvas wrapper div.

**Manual / assistive-tech verification:**
- VoiceOver (macOS) + Safari: navigate to the chart; reader must announce title and summary description, then offer table navigation.
- NVDA + Chrome (Windows): same smoke test.
- Keyboard-only: `Tab` into the `<figure>` region; summary table cells reachable.

**Regression:**
- Visual snapshot of `PriceChart` (if snapshots are added): ensure the `sr-only` div does not affect visible layout.
