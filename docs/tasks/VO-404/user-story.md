# VO-404: Incorrect error handling in news feed endpoint returns 500 instead of 400

## User Story

---

## User Story: VO-404 — News Feed Endpoint Returns 500 for Invalid Pagination Params

**As a** client consuming the news feed API, **I want** out-of-range or non-integer pagination parameters to return `400 Bad Request` with a clear error message, **so that** I can diagnose client-side mistakes immediately rather than seeing opaque 500s that look like server failures.

---

### Root Cause

`GET /api/news` in `backend/api/news.py`. The view passed `page` and `page_size` query strings directly to `int()` and database `LIMIT`/`OFFSET` calculations with no validation. A non-integer string caused an unhandled `ValueError`, and a negative page caused a negative `OFFSET` passed to SQLite — both paths raised unhandled exceptions that Flask converted to 500 responses.

---

### Acceptance Criteria

- Requests with out-of-range or non-integer values for `page` or `page_size` return `400 Bad Request`, not `500`
- A non-integer value (e.g. `page=abc`) returns:
  ```json
  {"error": "page and page_size must be integers"}
  ```
- A non-positive page (e.g. `page=0`, `page=-1`) returns:
  ```json
  {"error": "page must be a positive integer"}
  ```
- An out-of-range page_size (e.g. `page_size=0`, `page_size=200`) returns:
  ```json
  {"error": "page_size must be between 1 and 100"}
  ```
- Callers that omit `page` or `page_size` continue to receive the existing defaults (1 and 25 respectively) — no breaking change
- All existing 200 paths unaffected — no regression
- New tests in `backend/tests/test_news_api.py` cover each validation case

---

### Priority Reasoning

**Medium-High.** Low blast radius, but it produces misleading 500s that pollute logs and confuse API clients into thinking there's a server fault. The fix is a small validation helper — cost-to-fix is negligible.

---

### Estimated Complexity: **1 / 5**

Single `_parse_pagination()` helper with `try/except ValueError` and two range checks. Tests cover the new 400 paths plus a smoke test for the existing 200 path. No schema changes, no new dependencies.
