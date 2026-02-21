# VO-331: Incorrect error handling in stock search autocomplete returns 500 instead of 400

## Technical Design

Now I have a clear picture of the bug. Here's the design spec:

---

## VO-333: Stock Search Autocomplete Returns 500 Instead of 400

### Approach

The `GET /api/stocks/search` endpoint has a validation gap. The check `if not query` at line 243 of `stocks.py` fails to catch whitespace-only inputs (e.g., `q=   `) since `"   "` is truthy in Python. These pass through to `search_stock_ticker()`, which makes a live HTTP call to Yahoo Finance. If Yahoo Finance returns a non-200 response or malformed JSON for such inputs, and any exception escapes the `except` block (or a future code path is added), Flask defaults to 500. Additionally, the endpoint has no `try/except` wrapper — any unexpected runtime error produces an unhandled 500 rather than a meaningful response.

The frontend (`api.ts:75`) already trims before sending, but the backend must be authoritative for direct API callers.

### Files to Modify

- **`backend/api/stocks.py`** — primary fix: add input validation and endpoint-level error handling in `search_stocks()`
- **`backend/core/stock_manager.py`** — defensive check: assert `query` is stripped before making the Yahoo Finance request (secondary guard)
- **`backend/tests/test_stocks_api.py`** (create if absent) — unit/integration tests for the endpoint

### Data Model Changes

None.

### API Changes

**`GET /api/stocks/search?q=<query>`**

| Scenario | Before | After |
|---|---|---|
| `q=` or missing | `200 []` | `200 []` (unchanged) |
| `q=   ` (whitespace only) | `200 []` or `500` | `400 {"error": "..."}` |
| `q=<>100 chars` | undefined | `400 {"error": "..."}` |
| valid query | `200 [...]` | `200 [...]` (unchanged) |
| upstream failure | `500` | `200 []` (already handled in `search_stock_ticker`) |

Concrete changes in `search_stocks()`:
```python
query = request.args.get('q', '').strip()
if not query:
    return jsonify([])
if len(query) > 100:
    return jsonify({'error': 'Query too long'}), 400
try:
    results = search_stock_ticker(query)
    return jsonify(results)
except Exception as e:
    logger.exception("Unexpected error in stock search")
    return jsonify({'error': 'Search failed'}), 500
```

### Frontend Changes

None required. `api.ts:75` already strips whitespace before sending. `StockGrid.tsx` already handles API errors gracefully via the `ApiError` class.

### Testing Strategy

In `backend/tests/test_stocks_api.py`:
- **400 cases**: `q=   `, `q=` + `Content-Type` tricks, `q=<101-char string>`
- **200 valid**: `q=AAPL` returns array of `StockSearchResult` shaped objects
- **200 empty**: missing `q` param returns `[]`
- **Upstream failure simulation**: mock `search_stock_ticker` to raise `Exception`, assert endpoint returns `500` with JSON body (not Flask's HTML error page)
- **Integration**: end-to-end with real Yahoo Finance stubbed via `responses` library to avoid network dependency in CI
