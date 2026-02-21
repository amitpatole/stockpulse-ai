# VO-343: Stale Cache in Watchlist Management

## Technical Design

---

### Approach

Three targeted changes, no schema migrations:

1. **Cache invalidation on mutation** — `watchlist_manager.py` deletes the `ai_ratings` row for a ticker immediately after `add_stock_to_watchlist()` and `remove_stock_from_watchlist()`. The next `GET /api/ai/ratings` call computes a fresh rating live and repopulates the cache.

2. **TTL enforcement in the ratings fetcher** — `_get_cached_ratings()` in `analysis.py` filters out rows where `updated_at` is older than a configurable TTL constant (default 5 min) using `datetime('now', '-5 minutes')` in the SQL query. Stale rows become cache misses; the existing live-compute fallback handles repopulation.

3. **Frontend verification** — `StockGrid.tsx` already calls `refetch()` after both add (line 69) and remove (line ~213). No code changes required; confirm both paths are exercised in testing.

---

### Files to Modify/Create

| Action | Path | Change |
|--------|------|--------|
| **Modify** | `backend/core/watchlist_manager.py` | `DELETE FROM ai_ratings WHERE ticker = ?` at end of `add_stock_to_watchlist()` and `remove_stock_from_watchlist()` |
| **Modify** | `backend/api/analysis.py` | Add `AND updated_at > datetime('now', '-5 minutes')` to the SELECT in `_get_cached_ratings()`; extract TTL as a module-level constant |
| **Verify (no change)** | `frontend/src/components/dashboard/StockGrid.tsx` | Confirm `refetch()` fires on remove at line ~213 |

---

### Data Model Changes

None. `ai_ratings.updated_at` already exists (`TIMESTAMP DEFAULT CURRENT_TIMESTAMP`) and is set on every cache write. No new columns or tables required.

---

### API Changes

None. `GET /api/ai/ratings` is unchanged from the caller's perspective — it always returns the freshest available data. The TTL filter is an internal detail of `_get_cached_ratings()`.

---

### Frontend Changes

No code changes. `StockGrid.tsx` already wires `refetch()` correctly on both mutations. The 30s polling interval (`refreshInterval: 30000` in `useApi`) remains in place as a background safety net.

---

### Testing Strategy

**Unit — `backend/core/watchlist_manager.py`**
- After `add_stock_to_watchlist(ticker)`, assert no row exists in `ai_ratings` for that ticker
- After `remove_stock_from_watchlist(ticker)`, same assertion
- Confirm function still succeeds when no `ai_ratings` row exists (idempotent delete)

**Unit — `backend/api/analysis.py`**
- Seed `ai_ratings` with a row where `updated_at` is 10 minutes ago; assert `_get_cached_ratings()` excludes it (treated as cache miss)
- Seed with a row updated 1 minute ago; assert it is returned
- Confirm the live-compute fallback fires and repopulates the cache row on a miss

**Integration**
- Add ticker → seed a stale `ai_ratings` row → `GET /api/ai/ratings`: response must contain a freshly computed rating, not the stale one
- Remove ticker → `GET /api/ai/ratings`: ticker must not appear in response

All tests use SQLite in-memory; no live Yahoo Finance calls.
