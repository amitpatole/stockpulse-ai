# VO-344: Incorrect error handling in stock search autocomplete returns 500 instead of 400

## Technical Design

Here is the technical design spec:

---

## VO-343 Technical Design Spec

### Approach

Three localized fixes across two layers. After reading the actual code, the situation is more nuanced than the issue description suggests:

**The critical gap is in `stock_manager.py`, not `stocks.py`.**  
`backend/core/stock_manager.py:search_stock_ticker()` (line 185) has a bare `except Exception` that catches all Yahoo Finance errors and returns `[]`. This means the endpoint-level handler in `stocks.py` *never fires in production* — real upstream failures silently produce empty results instead of a 500. The endpoint validation in `stocks.py` is already correct and complete; it just can't catch what `stock_manager.py` swallows.

---

### Files to Modify

| File | Change |
|------|--------|
| `backend/core/stock_manager.py` | Remove internal `except` swallow in `search_stock_ticker()`; log and re-raise so the endpoint's try/except can handle it |
| `frontend/src/components/dashboard/StockGrid.tsx` | Add `searchError` state; replace silent `catch {}` at line 47 with status-aware handling; render error banner |

**No changes needed to:**
- `backend/api/stocks.py` — validation (whitespace → 400, >100 chars → 400) and upstream guard (try/except → 500 JSON) are already implemented at lines 231–259
- `frontend/src/lib/api.ts` — `ApiError` with `.status` already exists and is exported
- `backend/tests/test_stocks_api.py` — all cases already written

### Data Model Changes

None.

### API Changes

`GET /api/stocks/search?q=<query>` — behavior changes only:

| Input | Before | After |
|-------|--------|-------|
| Whitespace-only | 500 HTML | 400 `{"error": "..."}` |
| >100 chars | 500 HTML | 400 `{"error": "..."}` |
| Yahoo Finance failure | **200 `[]`** (silently swallowed) | **500** `{"error": "Search service unavailable"}` + log |

### Frontend Changes

In `StockGrid.tsx`: add `searchError` state, import `ApiError`, replace `catch {}` at line 47 with a status check (`err.status === 400` → "Invalid search query", else → "Search unavailable, try again"), clear on new attempts, render below the search input using the existing `addError` banner pattern at line 159.

### Testing Strategy

**Backend:** `python -m pytest backend/tests/test_stocks_api.py -v` — all 8 defined cases must pass. The upstream failure cases (`TestSearchStocksUpstreamFailure`) are specifically gated on the `stock_manager.py` re-raise fix.

**Frontend:** Add React Testing Library tests — mock `searchStocks` to reject with `ApiError(msg, 400)` and `ApiError(msg, 500)`, assert the correct banner text appears. Verify clean state on successful search.
