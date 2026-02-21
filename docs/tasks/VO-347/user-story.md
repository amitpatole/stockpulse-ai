# VO-347: Stale cache in watchlist management shows outdated data

## User Story

---

## User Story: VO-343 — Stale Cache in Watchlist Management

---

**User Story**

As a trader managing my watchlist, I want to see up-to-date stock data immediately after adding or removing a stock, so that I can make decisions based on current information rather than stale cached ratings.

---

**Background**

The `ai_ratings` SQLite cache (`updated_at` timestamp) is not invalidated on watchlist mutations. When a stock is added, the frontend may display a cached rating from a previous session. When a stock is removed and re-added, old scores persist. The 30s frontend polling interval compounds the issue — users can sit in a stale state for up to 30s+ after a watchlist change.

---

**Acceptance Criteria**

- When a stock is **added** to a watchlist, its cached rating in `ai_ratings` is invalidated (or force-refreshed) so the next fetch returns a freshly computed rating
- When a stock is **removed**, any stale cache entry for that ticker is cleared or marked dirty
- The `StockGrid` component calls `refetch()` immediately after add/remove operations complete (already partially done for add at line 69 — verify remove follows the same pattern)
- Cache entries older than a configurable TTL (e.g. 5 minutes) are treated as stale and trigger a background recompute on next read
- No user-visible "ghost" ratings appear for stocks no longer in the active watchlist
- QA can reproduce the stale state scenario and confirm it no longer occurs after the fix

---

**Priority Reasoning**

**High.** This is a data-correctness bug in the core product loop — watchlist management is what users do constantly. Showing stale or wrong ratings erodes trust in the AI signals. Found by QA, so it's reproducible and blocking.

---

**Estimated Complexity: 2 / 5**

The data model and fix surface are well-scoped: cache invalidation in `watchlist_manager.py` on add/remove, a TTL check in `_get_cached_ratings()` in `analysis.py`, and verifying `refetch()` is wired correctly in `StockGrid.tsx`. No schema changes required. Risk is low; blast radius is contained to the ratings cache path.
