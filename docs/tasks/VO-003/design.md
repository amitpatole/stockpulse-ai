# VO-003 Technical Design: Pagination for News & Research Endpoints

## Approach

Add `page` / `page_size` query parameters to both list endpoints using a paired COUNT + paginated SELECT pattern. A shared helper validates and parses pagination params to keep both handlers consistent. Response shape changes from a bare array to a wrapper envelope — the only breaking change.

## Files to Modify

| File | Change |
|---|---|
| `backend/api/news.py` | Paginate `GET /api/news`; replace hardcoded `LIMIT 50`/`LIMIT 100` |
| `backend/api/research.py` | Paginate `GET /api/research/briefs`; retire the `limit` param |
| `backend/tests/test_news_research_api.py` | **Create** — new test file (no existing coverage) |

No new files in production code. No schema migrations.

## Data Model Changes

None. Both tables (`news`, `research_briefs`) already have an indexed `created_at` column that drives the `ORDER BY`. The `COUNT(*)` companion queries read the same columns already queried.

## API Changes

### Shared validation logic (inline helper in each file)

```
def _parse_pagination(args) -> tuple[int, int] | Response:
    page      = args.get('page', 1)
    page_size = args.get('page_size', 25)
    # coerce to int; raise 400 on ValueError
    # clamp page_size to [1, 100]; raise 400 if page < 1
```

### `GET /api/news`

**Before:** returns `[{...}, ...]` — hardcoded `LIMIT 50` or `LIMIT 100`

**After:** returns `{ "data": [...], "page": 1, "page_size": 25, "total": 312 }`

SQL pattern (both ticker-filtered and global):
```sql
-- count
SELECT COUNT(*) FROM news [WHERE ticker = ?]

-- data
SELECT * FROM news [WHERE ticker = ?]
ORDER BY created_at DESC
LIMIT ? OFFSET ?
```

### `GET /api/research/briefs`

**Before:** returns `[{...}, ...]` — accepts `limit` param (default 50, max 200)

**After:** same envelope as news; `limit` param removed.

```sql
SELECT COUNT(*) FROM research_briefs [WHERE ticker = ?]

SELECT * FROM research_briefs [WHERE ticker = ?]
ORDER BY created_at DESC
LIMIT ? OFFSET ?
```

Note: `research.py` currently opens its own `sqlite3.connect(Config.DB_PATH)` rather than using `get_db_connection()`. Leave that as-is to avoid scope creep; it works correctly.

## Frontend Changes

None required by this task. The response envelope is additive — existing consumers reading the top-level object will see the array under `data` rather than at root. Frontend teams should update news/research data-fetching hooks to read `response.data` and store `total` for future "load more" UI, but that is out of scope for VO-003.

## Testing Strategy

Create `backend/tests/test_news_research_api.py` following the Flask test client pattern used in `test_agents_api.py`.

**Cases to cover:**

- Default params → page 1, page_size 25, `total` matches seeded row count
- Explicit `?page=2&page_size=10` → correct OFFSET slice returned
- Ticker filter + pagination → `total` is ticker-scoped, not global
- `page_size=200` → silently clamped to 100
- `page=0` → 400
- `page_size=0` → 400
- `page=abc` → 400
- Empty result set → `{ data: [], page: 1, page_size: 25, total: 0 }`
- `research.py`: `limit` param ignored / not recognized (backwards compat check)
