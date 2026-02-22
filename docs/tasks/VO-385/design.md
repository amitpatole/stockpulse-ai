# VO-385: Race condition in news feed endpoint during concurrent requests

## Technical Design

Now I have a clear picture. Let me write the spec.

---

## Technical Design Spec: VO-382 — Race Condition in News Feed Endpoint

### 1. Approach

Two distinct race conditions exist. First, `_get_monitor()` in `news_fetcher.py` uses an unguarded check-then-act pattern on the module-level `_monitor_cache` global — concurrent callers can all observe `None` simultaneously and race to construct multiple `EnhancedStockNewsMonitor` instances. Second, `get_news()` and `get_stats()` in `news.py` issue two sequential queries (COUNT then SELECT) outside any transaction, and skip `conn.close()` on exception paths, leaking connections under load. The fix is a `threading.Lock()` on the lazy singleton and `try/finally` connection cleanup across all three endpoints.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/agents/tools/news_fetcher.py` — add `_monitor_lock = threading.Lock()` and guard `_get_monitor()` with double-checked locking
- **MODIFY**: `backend/api/news.py` — wrap all `get_db_connection()` calls in `try/finally conn.close()` blocks; wrap multi-query reads in `BEGIN DEFERRED` transactions
- **CREATE**: `backend/tests/test_news_race_condition.py` — concurrent regression test suite

---

### 3. Data Model

No schema changes. Existing `news`, `alerts`, and `stocks` tables are sufficient. SQLite WAL mode (already configured) handles concurrent reads correctly; the fixes eliminate application-layer races above the DB layer.

---

### 4. API Spec

No new endpoints. The three existing endpoints are preserved exactly:

| Method | Path | Change |
|--------|------|--------|
| GET | `/api/news` | Connection cleanup + transaction |
| GET | `/api/alerts` | Connection cleanup (`try/finally`) |
| GET | `/api/stats` | Connection cleanup + transaction |

Response shapes are unchanged. No new query parameters.

---

### 5. Frontend Component Spec

No frontend changes required. This is a pure backend stability fix. The news feed UI components already handle loading/error states via existing API response contracts, which are not modified.

---

### 6. Verification

1. **Singleton test**: Start the Flask dev server, use `wrk` or `ab` to fire 50 concurrent requests at `/api/news` for 5 seconds — confirm zero 500 responses in the log and exactly one `EnhancedStockNewsMonitor` instance created (single log line from its constructor).

2. **Connection leak test**: Run `lsof -p <pid> | grep -c .db` before and after a 10-thread burst to `/api/stats` — the file descriptor count must return to baseline, confirming connections are always closed even when queries raise.

3. **Data integrity test**: Insert a known row, hit `/api/news?page=1&page_size=1` from 10 threads simultaneously — every response must contain `"total"` and `"data"` keys with a non-negative `total` and a `data` array whose length matches `page_size` (or remaining rows), with no `null` article fields for required columns.
