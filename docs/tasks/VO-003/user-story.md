# VO-003: Add pagination to news and research list endpoints

## User Story

**As a** frontend developer consuming the news and research APIs,
**I want** `GET /api/news` and `GET /api/research/briefs` to support `page` and `page_size` query parameters,
**so that** the UI can load data incrementally and avoid stalling on large payloads as the database grows.

---

## Acceptance Criteria

- [ ] `GET /api/news` accepts `page` (default: 1) and `page_size` (default: 25, max: 100) query parameters
- [ ] `GET /api/research/briefs` accepts the same `page` / `page_size` parameters; the existing `limit` parameter is removed or deprecated
- [ ] Both endpoints return a wrapper object with `data` (the result array), `page`, `page_size`, and `total` (total row count for that filter)
- [ ] Invalid parameter values (non-integer, `page < 1`, `page_size < 1`) return HTTP 400 with a descriptive error message
- [ ] `page_size` is capped server-side at 100; requesting a higher value silently clamps to 100 (no error)
- [ ] SQL queries use `LIMIT ? OFFSET ?` with bound parameters — no string interpolation
- [ ] Ticker-filtered requests (`?ticker=AAPL&page=2`) paginate correctly within the filtered set
- [ ] `total` reflects the count for the active filter (ticker-scoped or global), not the entire table
- [ ] Existing hardcoded `LIMIT 50` / `LIMIT 100` in `news.py` are replaced; no magic numbers remain
- [ ] API contract change is documented in the endpoint docstrings

---

## Priority Reasoning

**P2 — Medium.** Both endpoints currently return unbounded or loosely bounded result sets (hardcoded `LIMIT 100` in news, `LIMIT 200` max in research). This is fine today but becomes a real problem as data accumulates — slow queries, large JSON payloads, and potential UI freezes. It also blocks building any "load more" or infinite-scroll UX. Not a blocker for current functionality, but a prerequisite for any serious data volume.

---

## Complexity: 2 / 5

Both endpoints are simple SELECT queries in Flask. Adding `LIMIT`/`OFFSET` with a companion `COUNT(*)` query is mechanical work. The only meaningful decisions are the response envelope shape (must not silently break existing clients) and input validation. No schema migrations required.
