# VO-351: Pagination off-by-one in chart rendering list endpoint

## Technical Design

Now I have the full picture. Here's the technical design spec:

---

## VO-XXX: Pagination Off-by-One in Chart Rendering List Endpoint

### 1. Approach

`GET /api/chart/<ticker>` (`backend/api/analysis.py:126`) currently returns all `data_points` in one response — no pagination at all. The off-by-one manifests the moment pagination is added with the canonical mistake: `offset = page * page_size` instead of `(page - 1) * page_size`. Since chart data comes from yfinance (in-memory list, no SQL), the fix is Python slice arithmetic rather than a SQL `OFFSET` clause. The implementation follows the `_parse_pagination()` helper pattern already established in `news.py:17` and `research.py:19`, keeping the boundary logic consistent across the codebase.

---

### 2. Files to Modify / Create

| File | Action |
|---|---|
| `backend/api/analysis.py` | Add `page`/`page_size` params to `get_chart_data()`; apply `(page-1)*page_size` slice to `data_points`; expand response envelope |
| `backend/tests/test_chart_pagination.py` | **Create** — full boundary and regression test suite |

No other files need changes. No new helpers needed; the slice logic is a two-liner.

---

### 3. Data Model Changes

None. Chart data is computed live from `StockAnalytics.get_stock_price_data()` — no DB table exists or is needed.

---

### 4. API Changes

**`GET /api/chart/<ticker>`** — two new optional query params:

| Param | Type | Default | Constraint |
|---|---|---|---|
| `page` | int | 1 | ≥ 1 |
| `page_size` | int | 25 | 1–100 |

**Response envelope** gains pagination metadata:

```json
{
  "ticker": "AAPL",
  "period": "1mo",
  "data": [...],
  "page": 2,
  "page_size": 25,
  "total": 63,
  "total_pages": 3,
  "has_next": true,
  "currency_symbol": "$",
  "stats": { ... }
}
```

`stats` continues to summarise **all** data points (not just the current page) — separating rendering context from pagination context.

---

### 5. Frontend Changes

None required for the fix itself. The existing chart component consumes the full `data` array; pagination is opt-in for consumers that want it. If the frontend later adopts paginated fetching, it reads `has_next` and increments `page`.

---

### 6. Testing Strategy

**File**: `backend/tests/test_chart_pagination.py`

- **`TestOffByOneRegression`** — the core regression: 10 items, page_size=3 → page 1 = items 0–2, page 2 = items 3–5, page 3 = items 6–8, page 4 = item 9. Assert no item appears twice, no item is skipped.
- **`TestEdgeCases`** — single item (page 1 returns it, page 2 is empty); exactly one full page; empty result set; `page_size` equal to total.
- **`TestLastPagePartial`** — 7 items, page_size=3: last page returns exactly 1 item, not empty and not spilling into a 5th phantom page.
- **`TestPaginationMetadata`** — `total`, `total_pages`, `has_next` are accurate at each page boundary.
- **`TestValidation`** — non-integer `page`/`page_size` → 400; `page_size=0` and `page_size=101` → 400; `page_size=-1` → 400.

Mocking pattern follows VO-343/344: `patch("backend.core.ai_analytics.StockAnalytics.get_stock_price_data")` returns a deterministic fixture of N synthetic OHLCV bars, eliminating yfinance network dependency.
