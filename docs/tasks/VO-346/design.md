# VO-346: Support performance comparison mode in stock detail page

## Technical Design

---

### 1. Approach

Add a new `/api/stocks/compare` endpoint that fetches OHLCV data for up to 4 symbols via yfinance and returns normalized % return time series (rebased to 0% at the first candle of the requested timeframe). On the frontend, `StockPriceChart` manages comparison state (symbols list + fetched overlay data) synced to the URL via `?compare=SPY,MSFT`; when comparison is active it also normalizes the primary stock's candle data client-side so all series share the same % return axis. `PriceChart` gains a `compareOverlays` prop and renders each overlay as a `LineSeries` using lightweight-charts' native multi-series support.

---

### 2. Files to Create/Modify

- CREATE: `backend/api/compare.py` (new blueprint with `/api/stocks/compare` endpoint)
- MODIFY: `backend/app.py` (import and register `compare_bp`)
- CREATE: `frontend/src/components/stocks/CompareInput.tsx` (symbol chips + add input)
- MODIFY: `frontend/src/components/stocks/StockPriceChart.tsx` (compare state, URL sync, data fetch, primary normalization)
- MODIFY: `frontend/src/components/charts/PriceChart.tsx` (accept and render `compareOverlays` as `LineSeries`)
- MODIFY: `frontend/src/lib/api.ts` (add `getCompareData` function)
- MODIFY: `frontend/src/lib/types.ts` (add `ComparePoint`, `CompareSeries`, `CompareResponse` types)

---

### 3. Data Model

No database changes. All comparison data is fetched live from yfinance on demand, consistent with how `GET /api/stocks/<ticker>/detail` already works.

---

### 4. API Spec

**`GET /api/stocks/compare`**

| Param | Description |
|---|---|
| `symbols` | Comma-separated tickers, max 4 (e.g. `SPY,MSFT,QQQ`) |
| `timeframe` | One of `1D \| 1W \| 1M \| 3M \| 1Y` — maps to existing `_TIMEFRAME_MAP` |

Response `200 OK`:
```json
{
  "SPY": {
    "points": [
      { "time": 1700000000, "value": 0.0 },
      { "time": 1700086400, "value": 1.34 }
    ],
    "current_pct": 1.34
  },
  "INVALID": {
    "error": "No data for selected range"
  }
}
```

Each `value` is `(close / first_close - 1) * 100`. Symbols with no yfinance data get an `error` key instead of `points`. Returns `400` if `symbols` is missing or exceeds 4.

---

### 5. Frontend Component Spec

**`CompareInput` — `frontend/src/components/stocks/CompareInput.tsx`**

- Text input with placeholder "Add symbol (max 4)"; Enter or "+" button calls `onAdd(symbol.toUpperCase())`
- Each active symbol renders as a colored chip `[SPY ×]`; `×` calls `onRemove(symbol)`
- Symbols with an API `error` show an inline warning below their chip: `"SPY: No data for selected range"`
- Props: `symbols`, `colors`, `warnings`, `onAdd`, `onRemove`; input disabled at 4 symbols
- Renders in: `StockPriceChart.tsx`, directly below `TimeframeToggle`

**`StockPriceChart` changes:**

- Parse `?compare` on mount via `useSearchParams`; maintain `compareSymbols: string[]` state
- On change: call `getCompareData(symbols, timeframe)`, store in `compareData: CompareResponse`
- When active, normalize primary candles to % return points before passing to `PriceChart`
- Assign colors from fixed palette `['#f59e0b', '#10b981', '#8b5cf6', '#ef4444']`
- URL sync via `router.replace` (not push, to avoid polluting history)

**`PriceChart` changes:**

- New optional prop: `compareOverlays?: { symbol: string; color: string; points: { time: number; value: number }[] }[]`
- When present: primary series switches from `AreaSeries` to `LineSeries`; one `LineSeries` added per overlay
- Legend bar beneath chart: color swatch + symbol + current % return (e.g. `SPY +1.34%`)
- Y-axis label changes to `%` when overlays are active
- No overlays = existing behavior completely unchanged

**Loading state:** Inline spinner next to `CompareInput` while fetch is in-flight. Invalid symbols surface as chip warnings — no page-level error.

---

### 6. Verification

1. **Overlay rendering**: Add `SPY` on any stock detail page — confirm a second line appears rebased to 0% at the chart's left edge with a legend chip showing `SPY ±X.XX%`. Switch timeframe to `1W` — both lines rebase to the new window without removing `SPY` from the input.
2. **URL shareability**: Add `SPY` and `MSFT`, copy the URL (`?compare=SPY,MSFT`), open in a new tab — both overlays load immediately from the param.
3. **Invalid symbol**: Type `ZZZZZ` — chip appears with inline warning "No data for selected range", no extra line is drawn, primary chart is unaffected.
