# VO-011: Add pagination to news and research list endpoints

## Technical Design

Now I have everything I need. Here's the design spec:

---

## Technical Design Spec: Paginated News & Research Endpoints

### 1. Approach

Pure backend surgery — no schema migrations. Replace hard-coded `LIMIT` constants with `LIMIT ? OFFSET ?` parameterized queries driven by `page`/`page_size`. Run a `COUNT(*)` with the identical `WHERE` clause in the same request. Wrap the response in a standard envelope. Frontend `api.ts` needs two small updates to unwrap the envelope and forward `page`/`page_size` from call sites.

Validation: clamp `page_size` to `[1, 100]` and return `400` for explicitly out-of-range values. Both endpoints share the same validation logic — extract a `_parse_pagination()` helper in each file (they're short enough not to warrant a shared utility module).

Note: `research.py` opens a raw `sqlite3` connection while `news.py` uses `get_db_connection()` — a pre-existing inconsistency. Stay consistent within each file; don't refactor it here.

---

### 2. Files to Modify/Create

| Action | Path |
|--------|------|
| Modify | `backend/api/news.py` |
| Modify | `backend/api/research.py` |
| Modify | `frontend/src/lib/api.ts` |
| Create | `backend/tests/test_news_api.py` |
| Create | `backend/tests/test_research_api.py` |

---

### 3. Data Model Changes

None. `COUNT(*)` with existing `WHERE ticker = ?` is sufficient; no new indexes are required at current data volumes.

---

### 4. API Changes

**`GET /api/news`**
- New params: `page` (int, default `1`), `page_size` (int, default `25`, max `100`)
- `page_size > 100` or `page_size < 1` → `400 {"error": "page_size must be between 1 and 100"}`
- Removes hard-coded `LIMIT 50` / `LIMIT 100`; `ticker` filter unchanged
- Response shape:
  ```json
  { "data": [...], "page": 1, "page_size": 25, "total": 312, "has_next": true }
  ```

**`GET /api/research/briefs`**
- Same `page`/`page_size` params and same `400` validation
- Legacy `limit` param: if present, treat as `page_size` (with same max-100 clamp) for backwards compat; log a deprecation warning
- Same response envelope

---

### 5. Frontend Changes

**`frontend/src/lib/api.ts`**
- `getNews(ticker?, page?, pageSize?)` → passes `page`/`page_size` to the URL, unwraps `response.data`; update return type to include `total`/`has_next` or keep returning `NewsArticle[]` depending on call site needs (call sites currently only use the array — safest to keep signature stable and only return `data` array for now)
- `getResearchBriefs(ticker?, page?, pageSize?)` → remove hard-coded `limit=50`, unwrap `response.data`

No component changes required to meet acceptance criteria; pagination UI is out of scope.

---

### 6. Testing Strategy

Use Flask test client with a real in-memory SQLite database seeded per test (same pattern as `test_agents_api.py` but no mocking needed — these routes are pure DB read).

**`test_news_api.py` cases:**
- Default params → 25 rows, correct envelope keys
- `page=2` with 30 seeded rows → 5 rows, `has_next=False`
- `ticker` filter → `total` reflects filtered count, not full table
- `page_size=100` accepted; `page_size=101` → 400; `page_size=0` → 400
- `has_next=True` when more rows exist; `has_next=False` on last page
- `total` always matches a direct `COUNT(*)` against the seed data

**`test_research_api.py` cases:**
- Same envelope shape and boundary cases as news
- Legacy `limit=50` maps to `page_size=50`, returns envelope (not bare array)
- `limit=999` → 400 (not silently clamped)

**Run:**
```
python -m pytest backend/tests/test_news_api.py backend/tests/test_research_api.py -v
```
