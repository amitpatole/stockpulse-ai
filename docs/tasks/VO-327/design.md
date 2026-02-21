# VO-327: Implement multi-timeframe toggle for stock charts

## Technical Design

Now I have everything I need. Let me write the spec.

---

## VO-374: Multi-Timeframe Toggle — Technical Design Spec

### Approach

The backend already supports timeframe-parameterized data at `GET /api/stocks/<ticker>/detail?timeframe=`. The work is primarily frontend: a new stock detail route with a toggle that refetches data on selection and persists the choice in localStorage. One backend addition is required: the `All` timeframe option.

---

### Files to Modify / Create

| Action | Path |
|---|---|
| **Modify** | `backend/api/stocks.py` |
| **Modify** | `frontend/src/lib/api.ts` |
| **Modify** | `frontend/src/lib/types.ts` |
| **Create** | `frontend/src/components/stocks/TimeframeToggle.tsx` |
| **Create** | `frontend/src/components/stocks/StockPriceChart.tsx` |
| **Create** | `frontend/src/app/stocks/[ticker]/page.tsx` |

---

### Data Model Changes

None. All price history is fetched live from yfinance; nothing is stored in SQLite.

---

### API Changes

**`GET /api/stocks/<ticker>/detail?timeframe=<tf>`** — minimal change to `backend/api/stocks.py`:

- Add `All` to the timeframe map: `period='max', interval='1wk'`
- Return `400` with `{"error": "Invalid timeframe"}` for unknown values (currently falls through silently)
- No new endpoint needed; existing structure is sufficient

---

### Frontend Changes

**`frontend/src/lib/types.ts`**
- Add `export type Timeframe = '1D' | '1W' | '1M' | '3M' | '1Y' | 'All'`

**`frontend/src/lib/api.ts`**
- Add `getStockDetail(ticker: string, timeframe: Timeframe): Promise<StockDetail>` calling `/api/stocks/${ticker}/detail?timeframe=${timeframe}`

**`TimeframeToggle.tsx`**
- Renders a `<div role="group" aria-label="Chart timeframe">` with one `<button>` per option
- Accepts `selected`, `onChange` props
- Active button gets a distinct ring/bg style (TailwindCSS)
- Buttons are `min-w-[44px] min-h-[44px]` for touch target compliance

**`StockPriceChart.tsx`**
- Client component owning `timeframe` state (default: read from `localStorage` → fallback `'1M'`)
- Calls `getStockDetail` on mount and on timeframe change via `useApi` hook
- On timeframe change: write to `localStorage('vo_chart_timeframe', tf)`, trigger refetch
- Renders `<TimeframeToggle />` above `<PriceChart />` and `<ChartDataSummary />` (a11y table already built)
- Maps `candles[].close` + `candles[].time` → PriceChart's `{ time, value }` format
- On empty `candles` array: renders a `<p>` fallback ("No data available for this period")

**`/app/stocks/[ticker]/page.tsx`**
- Server component shell fetching stock metadata (`getStocks()` to validate ticker exists)
- Passes ticker down to `<StockPriceChart />` (client boundary)
- Also renders quote stats (price, change %, volume) from the detail response

---

### Testing Strategy

**Backend** (`backend/tests/test_stock_timeframes.py`):
- Parametrize over all 7 timeframes; assert `candles` key present and `200` status
- Assert `400` returned for invalid timeframe string
- Assert `All` maps to `period='max'` (mock yfinance)

**Frontend** (Jest / React Testing Library):
- `TimeframeToggle`: clicking each button calls `onChange` with correct value; active button has correct `aria-pressed` attribute
- `StockPriceChart`: localStorage read on mount sets initial selection; timeframe change triggers refetch; empty candles shows fallback text
- Keyboard: Tab reaches each button, Enter/Space selects it

**Manual / E2E**:
- Mobile viewport: toggle buttons must not overflow (wrap with `flex-wrap`)
- Navigate away and back: localStorage preserves selected timeframe
