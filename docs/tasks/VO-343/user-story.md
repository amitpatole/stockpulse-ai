# VO-343: Incorrect error handling in stock search autocomplete returns 500 instead of 400

## User Story

---

## User Story: VO-343 — Correct Error Handling in Stock Search Autocomplete

**Story**
As a trader using the stock search autocomplete, I want invalid search inputs to return clear error feedback instead of a generic server error, so that I understand what went wrong and can correct my query without thinking the platform is broken.

---

**Background**

The `/api/stocks/search` endpoint currently has no input validation and no exception handling at the route level. Invalid client inputs (whitespace-only queries, queries exceeding 100 characters) should return `400 Bad Request`, but instead bubble up as `500 Internal Server Error`. The test suite already codifies the correct behavior — the implementation just doesn't match it.

---

**Acceptance Criteria**

- `GET /api/stocks/search?q=   ` (whitespace-only) returns `400` with `{"error": "..."}` JSON body
- `GET /api/stocks/search?q=<query over 100 chars>` returns `400` with a descriptive error message
- `GET /api/stocks/search` (missing `q`) returns `[]` with `200` (existing behavior, preserve it)
- Upstream exceptions from `search_stock_ticker()` (e.g. network failure) return `500` with `{"error": "..."}` — never an unhandled Flask traceback
- All existing tests in `test_stocks_api.py` pass
- Frontend `StockGrid.tsx` surfaces a user-facing error message on search failure (currently silently clears results)

---

**Priority Reasoning**

**High.** A `500` on user-controlled input is a correctness bug and a bad user experience — it signals a server crash when the real problem is the query. It also masks real `500`s (upstream failures), making on-call triage harder. The fix is low-risk and well-scoped.

---

**Estimated Complexity: 2 / 5**

The test suite already defines the contract. Work is:
1. Add input validation + `try/except` in `backend/api/stocks.py:search_stocks()`
2. Surface the error in `StockGrid.tsx:doSearch()` instead of silent failure

No schema changes, no new dependencies.
