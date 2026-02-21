# VO-325: Add performance comparison mode to stock detail page

## Technical Design

Now I have enough context to write the spec. Key findings: Next.js 16 + React 19 + TypeScript, `lightweight-charts` v5.1.0 (already supports multi-series), existing `/api/stocks/<ticker>/detail?timeframe=` endpoint, no stock detail page route yet, no localStorage in use.

---

## Technical Design Spec: Performance Comparison Mode

### Approach

Build the stock detail page as a new Next.js route (`/stocks/[ticker]`) that renders a multi-series comparison chart. Reuse the existing `/api/stocks/<ticker>/detail` endpoint per ticker — no new API logic needed except a minor period extension. Normalize all series to % return from period start before rendering. Persist comparison tickers via localStorage with a small custom hook.

`lightweight-charts` v5.1.0 already supports multiple series on one chart instance, making this straightforward: primary stock as `AreaSeries`, each comparison ticker as a `LineSeries` with a fixed color from a 4-slot palette.

---

### Files to Modify / Create

**Create:**
- `frontend/src/app/stocks/[ticker]/page.tsx` — new stock detail route
- `frontend/src/components/stocks/ComparisonChart.tsx` — multi-series chart; owns chart instance, mounts/unmounts LineSeries per comparison ticker
- `frontend/src/components/stocks/ComparisonLegend.tsx` — displays symbol + period return % + × remove button per ticker; baseline ticker rendered without ×
- `frontend/src/components/stocks/ComparisonTickerSearch.tsx` — text input + submit; enforces max 4 limit; shows inline error on invalid/missing ticker
- `frontend/src/hooks/useComparisonTickers.ts` — reads/writes `comparisonTickers:<ticker>` key in localStorage; exposes `[tickers, add, remove]`

**Modify:**
- `frontend/src/lib/api.ts` — add `fetchStockDetail(ticker, period)` if not already exported
- `frontend/src/lib/types.ts` — add `ComparisonSeries` type `{ ticker: string; color: string; data: NormalizedPoint[]; periodReturn: number }`
- `backend/api/stocks.py` — add `6M` to allowed timeframes in the detail endpoint (currently supports 1D/1W/1M/3M/1Y); maps to `6mo` for yfinance

---

### Data Model Changes

None. No new DB tables or columns.

---

### API Changes

**Minor:** `GET /api/stocks/<ticker>/detail?timeframe=6M` — add `6M → 6mo` mapping in the existing timeframe switch in `stocks.py`. No schema change.

---

### Frontend Changes

**Normalization utility** (inline in `ComparisonChart.tsx`):
```ts
normalizedValue = ((close - firstClose) / firstClose) * 100
```

**State on the detail page:**
- `period`: `'1D' | '1W' | '1M' | '3M' | '6M' | '1Y'` (default `1M`)
- `comparisonTickers`: from `useComparisonTickers` hook (localStorage)
- `comparisonData`: `Map<ticker, NormalizedPoint[] | Error>` — fetched in parallel via `Promise.allSettled`; Error entries surface as inline legend badges, excluded from chart

**Color palette:** 4 fixed Tailwind-safe hex values (`#f59e0b`, `#10b981`, `#6366f1`, `#ef4444`); assigned by insertion order.

**Period selector:** reuse existing period button pattern from dashboard; triggers re-fetch of all active series.

---

### Testing Strategy

**Backend (`pytest`):**
- `test_stock_detail_6m_timeframe` — assert `GET /api/stocks/AAPL/detail?timeframe=6M` returns candles and no 400.

**Frontend (Jest + React Testing Library):**
- `ComparisonTickerSearch`: enforces max 4, duplicate rejection, invalid ticker inline error
- `useComparisonTickers`: localStorage read/write/remove, survives re-render
- Normalization pure function: first point always 0%, correct sign for gain/loss
- `ComparisonLegend`: renders period return, × fires remove, baseline has no ×
