# VO-011: Add pagination to news and research list endpoints

## User Story

## User Story: Paginated News & Research Endpoints

---

**User Story**

As a frontend developer consuming the TickerPulse API, I want `GET /api/news` and `GET /api/research/briefs` to support `page` and `page_size` query parameters, so that I can load data incrementally and avoid slow payloads as the database grows.

---

**Current State**

- `/api/news`: hard-coded `LIMIT 50` (per-ticker) or `LIMIT 100` (global). No offset.
- `/api/research/briefs`: has a `limit` param (default 50, max 200) but no offset, no total count.
- Neither endpoint tells the client how many total records exist or whether there's a next page.

---

**Acceptance Criteria**

- Both endpoints accept `page` (1-indexed, default `1`) and `page_size` (default `25`, max `100`) query parameters
- Responses wrap the array in an envelope:
  ```json
  { "data": [...], "page": 1, "page_size": 25, "total": 312, "has_next": true }
  ```
- Invalid/out-of-range params (e.g. `page_size=999`) are clamped or return a `400` with a clear error message
- Existing `ticker` filter still works alongside pagination
- `GET /api/news` removes its hard-coded `LIMIT 50/100` and routes all result-set sizing through the new params
- `GET /api/research/briefs` deprecates the bare `limit` param in favor of the new scheme (or maps it as `page_size` for backwards compat)
- A `total` count query runs alongside each data query (efficient `COUNT(*)` with same `WHERE` clause)

---

**Priority Reasoning**

Medium-high. Not user-facing today, but this is defensive infrastructure — it prevents a class of performance regressions as news volume grows. The hard-coded limits are a hack, not a safety net. Better to fix the contract now before frontend clients bake in assumptions about response shape.

---

**Estimated Complexity: 2 / 5**

Both files are simple, self-contained Flask routes with direct SQLite queries. The change is mechanical: swap hard-coded limits for parameterized `LIMIT/OFFSET`, add a `COUNT(*)` query, and wrap the response. No schema migrations needed. Risk is low.
