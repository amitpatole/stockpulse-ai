# VO-343: Incorrect error handling in stock search autocomplete returns 500 instead of 400

## Technical Design

Now I have everything I need. Let me write the spec.

---

## Technical Design Spec: Fix Error Handling in Stock Search Autocomplete

### Approach

The bug lives entirely in the `GET /api/stocks/search` handler. Three input-validation and error-handling gaps cause the endpoint to return unhandled exceptions (Flask HTML 500) instead of proper 400/500 JSON responses. The fix is a targeted surgical patch to the route handler: strip the query, validate it, and wrap the downstream call in a try/except. No schema changes or new abstractions needed.

---

### Files to Modify/Create

| Action | Path |
|--------|------|
| **Modify** | `backend/api/stocks.py` — `search_stocks()` at line 231 |
| **Tests already exist** | `backend/tests/test_stocks_api.py` — all cases defined, currently failing |

---

### Data Model Changes

None. This is a pure request-validation / error-handling fix.

---

### API Changes

**`GET /api/stocks/search?q=<query>`** — behavior changes only:

| Input | Before | After |
|-------|--------|-------|
| `q` missing or `q=` | 200 `[]` | 200 `[]` (no change) |
| `q=   ` (whitespace-only) | 500 HTML (unhandled) | **400** `{"error": "..."}` |
| `q=<>100 chars` | 500 HTML (unhandled) | **400** `{"error": "..."}` |
| `q= AAPL ` (padded) | forwards raw value | strips, forwards `AAPL` |
| upstream `search_stock_ticker` raises | 500 HTML | **500** `{"error": "..."}` JSON |

No new endpoints. No breaking changes to response shape for valid requests.

---

### Frontend Changes

None required for this bug. `Header.tsx:26` has a static search placeholder with no wire-up to the API. The frontend is insulated from the server-side error contract until that component is fully implemented.

---

### Testing Strategy

The test file `backend/tests/test_stocks_api.py` already specifies all required cases. Run them to confirm the fix:

```
python -m pytest backend/tests/test_stocks_api.py -v
```

Specific cases that currently fail and must pass after the fix:

- `TestSearchStocksEmpty::test_whitespace_only_q_returns_400`
- `TestSearchStocksEmpty::test_tab_only_q_returns_400`
- `TestSearchStocksQueryTooLong::test_101_char_query_returns_400`
- `TestSearchStocksQueryTooLong::test_100_char_query_is_accepted`
- `TestSearchStocksQueryTooLong::test_error_body_is_json_not_html`
- `TestSearchStocksValid::test_query_is_stripped_before_passing_to_search`
- `TestSearchStocksUpstreamFailure::test_upstream_exception_returns_500_json`
- `TestSearchStocksUpstreamFailure::test_upstream_exception_body_is_not_html`

No new test cases needed — the existing suite fully covers the contract. Do not add integration tests against live Yahoo Finance; keep tests fully mocked.
