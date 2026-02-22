# VO-341: Implement performance comparison mode for stock detail page

## Technical Design

Here's the design spec:

---

### 1. Approach

Introduce a `GET /api/stocks/compare` endpoint that accepts up to 5 tickers and a timeframe, fetches OHLCV via yfinance in parallel threads, and returns candles normalized to 100 at period start with pre-computed performance deltas. On the frontend, a new `ComparisonModePanel` handles ticker search and pill removal; a new `ComparisonChart` renders one `AreaSeries` for the primary ticker and `LineSeries` per comparison using `lightweight-charts`. `StockPriceChart` gates between modes via a toggle, sharing existing timeframe state.

---

### 2. Files to Create/Modify

- **CREATE**: `backend/api/compare.py`
- **MODIFY**: `backend/app.py` (register `compare_bp` blueprint)
- **CREATE**: `frontend/src/components/stocks/ComparisonChart.tsx`
- **CREATE**: `frontend/src/components/stocks/ComparisonModePanel.tsx`
- **MODIFY**: `frontend/src/components/stocks/StockPriceChart.tsx` (toggle + comparison state)
- **MODIFY**: `frontend/src/lib/api.ts` (add `getComparisonData`)
- **MODIFY**: `frontend/src/lib/types.ts` (add `ComparisonSeries`, `ComparisonResult`)

---

### 3. Data Model

No schema changes. All data fetched live from yfinance at request time.

---

### 4. API Spec

**`GET /api/stocks/compare`**
- `tickers` — required, comma-separated, max 5 (primary ticker first)
- `timeframe` — optional, default `1M`; same set as detail endpoint

```json
{
  "timeframe": "1M",
  "series": [
    { "ticker": "AAPL", "name": "Apple Inc.", "candles": [{"time": 1706745600, "value": 100.0}], "delta_pct": 0.0, "error": null },
    { "ticker": "MSFT", "name": "Microsoft Corp.", "candles": [{"time": 1706745600, "value": 104.2}], "delta_pct": 4.2, "error": null }
  ]
}
```

`candles[].value` = `(close / first_close) * 100`. `delta_pct` = ticker's final normalized value minus primary's. Failed tickers: `candles: [], error: "No data found"`. Returns `400` if `tickers` missing/exceeds 5 or `timeframe` unrecognized.

---

### 5. Frontend Component Spec

**`ComparisonModePanel`** (`frontend/src/components/stocks/ComparisonModePanel.tsx`)
- "Compare" toggle button; default off
- Ticker search uses existing `searchStocks()` with autocomplete dropdown
- Up to 4 comparison pills: ticker symbol + delta badge (e.g. `+4.2% vs AAPL`) + remove (×)
- Invalid/delisted tickers: inline red error beneath pill
- Renders inside `StockPriceChart` below `TimeframeToggle`

**`ComparisonChart`** (`frontend/src/components/stocks/ComparisonChart.tsx`)
- Primary ticker: filled `AreaSeries` (blue `#3b82f6`, dominant)
- Comparisons: `LineSeries` in palette `['#f59e0b', '#10b981', '#ef4444', '#8b5cf6']`
- Y-axis: "Performance (%)" with 100 baseline always visible
- Legend: horizontal row, wraps on `sm:` breakpoint
- `StockPriceChart` renders `PriceChart` (mode off) or `ComparisonChart` (mode on)

---

### 6. Verification

1. Add MSFT and GOOGL on AAPL's 1M chart — three distinct colored series all start at 100, delta badges show correct relative performance.
2. Enter `XXXX999` — that pill shows inline error; other series unaffected.
3. Toggle mode off — chart reverts to standard single-ticker area chart with no regression.
