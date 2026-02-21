# VO-332: Missing input validation in chart rendering allows injection

## Technical Design

## Technical Design Spec: VO-XXX — Chart Rendering Input Validation

### Approach

Introduce validation at three layers in sequence: a shared backend utility module, the data provider and API layers, and the frontend chart component. No architectural changes — pure defensive validation added at existing boundaries. Central utility avoids duplicating math checks across `yfinance_provider.py` and `ai_analytics.py`.

---

### Files to Modify / Create

| Action | Path |
|--------|------|
| **Create** | `backend/utils/chart_validation.py` — shared validation logic |
| **Modify** | `backend/data_providers/yfinance_provider.py` |
| **Modify** | `backend/core/ai_analytics.py` |
| **Modify** | `backend/api/analysis.py` |
| **Modify** | `frontend/src/components/charts/PriceChart.tsx` |
| **Create** | `tests/test_chart_validation.py` |
| **Create** | `tests/test_analysis_chart_integration.py` |

---

### Data Model Changes

None. All changes are in-process validation — no new DB tables or columns.

---

### API Changes

**`GET /api/analysis/chart/<ticker>?period=`**

- Add allowlist guard at handler entry: `VALID_PERIODS = {'1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'}`. Return `400` with `{"error": "invalid_period", "detail": "..."}` on mismatch.
- Replace silent `None`-filtering loop with calls to `chart_validation.validate_ohlcv_record()`. If validation fails, return `400` with `{"error": "invalid_chart_data", "detail": "<field> out of range for <ticker>"}` — never return partial data silently.
- The existing zero-division guard at line 179 (`if first_price else 0`) stays; extend it to also guard `NaN`/`Infinity` using `math.isfinite()`.

---

### `backend/utils/chart_validation.py` (new)

Centralizes all rules so both `yfinance_provider.py` and `ai_analytics.py` share one source of truth:

```python
# Key functions:
def is_valid_price(v) -> bool          # math.isfinite(v) and v > 0
def is_valid_timestamp(ts: int) -> bool # 946684800 < ts < 4102444800 (2000–2100)
def validate_ohlc_relationships(o, h, l, c) -> bool  # l <= o <= h and l <= c <= h
def validate_ohlcv_arrays(open, high, low, close, volume, timestamps) -> None  # raises ValueError on length mismatch
def sanitize_price_bar(bar: dict, ticker: str) -> dict  # raises ValueError with field + ticker in message
```

Validation failures log `WARNING` with ticker and offending field before raising.

---

### `backend/data_providers/yfinance_provider.py`

In `get_historical()`, replace the existing null-only check with `sanitize_price_bar()` per bar. Call `validate_ohlcv_arrays()` before the loop to catch length mismatches up front. Bars that fail are skipped with a warning; if >50% of bars are rejected, raise and return `None` upstream.

---

### `backend/core/ai_analytics.py`

In `get_stock_price_data()`, after unpacking the API response, call `validate_ohlcv_arrays()` on raw lists before returning. Filter out non-finite values using `is_valid_price()` — consistent with the existing `None` filter in `calculate_ai_rating()`.

---

### Frontend Changes — `PriceChart.tsx`

**Validation helper** (added in-file):
```typescript
function sanitizeChartData(data: PriceDataPoint[]): PriceDataPoint[] {
  return data.filter(d =>
    Number.isFinite(d.value) && d.value > 0 &&
    (typeof d.time === 'string' ? d.time.length > 0 : Number.isFinite(d.time) && d.time > 0)
  );
}
```

**Remove unsafe assertions**: replace `d.time as UTCTimestamp` / `d.time as Time` with a runtime-checked converter that throws on invalid input.

**Error state**: add `const [dataError, setDataError] = useState(false)`. If `sanitizeChartData()` returns empty from non-empty input, set error and render a visible `<div>` with "Chart data unavailable — invalid data received" instead of a blank canvas.

---

### Testing Strategy

**`tests/test_chart_validation.py`** — unit tests:
- `NaN`, `Infinity`, `-Infinity` in each OHLC field → rejected
- `low > high` → OHLC relationship rejected
- Mismatched array lengths → `ValueError`
- Zero `first_price` in percent-change calc → returns `0`, no exception
- Valid timestamp boundary values (year 2000, 2100)

**`tests/test_analysis_chart_integration.py`** — integration tests:
- `GET /api/analysis/chart/AAPL?period=bad` → `400` with `invalid_period`
- Mocked provider returning `NaN` close → `400` with `invalid_chart_data`, not `500`
- Valid payload → `200` with well-formed `data` array

Frontend validation can be covered with a Jest/Vitest unit test on `sanitizeChartData()` directly — no DOM rendering required.
