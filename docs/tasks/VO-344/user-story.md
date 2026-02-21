# VO-344: Incorrect error handling in stock search autocomplete returns 500 instead of 400

## User Story

---

## User Story: VO-343 — Correct Error Handling in Stock Search Autocomplete

---

### User Story

**As a** trader using the stock search autocomplete,
**I want** invalid search inputs and upstream failures to return meaningful error responses,
**so that** I understand why a search failed and the app behaves predictably rather than crashing silently.

---

### Context

QA identified that the `/api/stocks/search` endpoint returns HTTP 500 for cases that are the client's fault (whitespace-only queries, oversized inputs). The backend also exposes raw unhandled exceptions from Yahoo Finance. The frontend currently swallows all errors silently.

---

### Acceptance Criteria

**Backend — Input Validation (400 Bad Request)**
- [ ] Whitespace-only query (e.g. `?q=   `) returns `400` with JSON body `{ "error": "..." }`
- [ ] Query exceeding 100 characters returns `400` with JSON body `{ "error": "..." }`
- [ ] All error responses are `application/json`, never HTML error pages

**Backend — Upstream Failures (500 Internal Server Error)**
- [ ] Unhandled exceptions from `search_stock_ticker()` are caught at the endpoint level
- [ ] Upstream failures return `500` with JSON body `{ "error": "Search temporarily unavailable" }`
- [ ] Errors are logged server-side

**Frontend**
- [ ] `ApiError` with status `400` surfaces a user-visible message (e.g. "Invalid search query")
- [ ] `ApiError` with status `500` surfaces a user-visible message (e.g. "Search unavailable, try again")
- [ ] Silent `catch {}` in `StockGrid.tsx:47` replaced with error state

**Tests**
- [ ] All existing tests in `test_stocks_api.py` pass (they already define the expected behavior)
- [ ] Frontend error states covered by component tests

---

### Priority Reasoning

**High.** This is a correctness bug with user-visible impact: failed searches give zero feedback, and malformed inputs can bubble up as 500s — which pollutes error monitoring and obscures real server failures. Low risk fix, high signal/noise improvement.

---

### Estimated Complexity

**2 / 5** — Localized changes to one endpoint (`stocks.py`), one core function (`stock_manager.py`), one frontend component (`StockGrid.tsx`), and one API client (`api.ts`). Tests already written and defining expected behavior.
