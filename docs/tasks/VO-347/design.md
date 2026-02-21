# VO-347: Stale cache in watchlist management shows outdated data

## Technical Design

## VO-343 Technical Design Spec — Stale Cache in Watchlist Management

---

### Approach

Three targeted changes address the bug at its root causes:

1. **Cache invalidation on mutation** — `watchlist_manager.py` deletes the `ai_ratings` row for a ticker on add/remove, forcing a fresh compute on next read.
2. **TTL enforcement on read** — `_get_cached_ratings()` in `analysis.py` filters out rows where `updated_at` is older than a configurable TTL, treating them as absent (which triggers the live-compute fallback already in `get_ai_ratings()`).
3. **Frontend refetch verification** — `StockGrid.tsx` already calls `refetch()` at line 69 (add) and line 214 (remove). No change needed; this is confirmed correct.

No schema changes are required. `ai_ratings.updated_at` already exists.

---

### Files to Modify

| File | Change |
|------|--------|
| `backend/core/watchlist_manager.py` | Invalidate `ai_ratings` row for `ticker` at end of `add_stock_to_watchlist()` and `remove_stock_from_watchlist()` |
| `backend/api/analysis.py` | Add TTL filter in `_get_cached_ratings()`; add `AI_RATINGS_CACHE_TTL_SECONDS` constant |
| `frontend/src/components/dashboard/StockGrid.tsx` | Verify only — no functional changes expected |

---

### Data Model Changes

None. The existing `ai_ratings.updated_at TIMESTAMP` column is sufficient. Deleting a row on mutation and filtering stale rows by TTL on read covers both invalidation strategies without schema additions.

---

### API Changes

None. The existing `GET /api/ai/ratings` endpoint already re-computes live ratings for tickers absent from the cache. Once invalidation deletes the row, the next call triggers that fallback path automatically.

---

### Frontend Changes

`StockGrid.tsx` is already wired correctly:
- `handleSelect` (add, line 69): `refetch()` fires immediately after `addStock()` resolves.
- `handleRemoveStock` (remove, line 214): `refetch()` fires immediately after `deleteStock()` resolves.

The 30s polling interval (`refreshInterval: 30000`, line 12) remains unchanged — the manual `refetch()` on mutation already bypasses the wait.

---

### Implementation Detail

**`watchlist_manager.py`** — append to both mutation functions:
```python
# Invalidate stale cache so next ratings fetch recomputes fresh
with db_session() as conn:
    conn.execute("DELETE FROM ai_ratings WHERE ticker = ?", (ticker,))
```

**`analysis.py`** — add TTL constant and filter:
```python
AI_RATINGS_CACHE_TTL_SECONDS = 300  # 5 minutes, configurable

def _get_cached_ratings():
    cutoff = datetime.utcnow() - timedelta(seconds=AI_RATINGS_CACHE_TTL_SECONDS)
    rows = conn.execute("""
        SELECT * FROM ai_ratings
        WHERE updated_at >= ?
        ORDER BY ticker
    """, (cutoff.isoformat(),)).fetchall()
```

---

### Testing Strategy

- **Unit**: Mock `db_session` in `watchlist_manager.py` tests; assert `DELETE FROM ai_ratings` is executed for the correct ticker on add and remove.
- **Unit**: Mock `sqlite3.connect` in `analysis.py` tests; assert rows older than TTL are excluded from the returned list.
- **Integration**: Add a stock → confirm `ai_ratings` row is absent → call `/api/ai/ratings` → confirm fresh rating returned with current `updated_at`.
- **Integration**: Remove and re-add a stock → confirm no stale score persists between the two add events.
- **QA regression**: Reproduce the original scenario (add stock, immediately check grid) — confirm no ghost rating from a prior session appears.
