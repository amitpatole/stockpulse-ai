# VO-002: Add watchlist portfolio groups with CRUD

## Technical Design

## Technical Design Spec: Watchlist Portfolio Groups

### Approach
Junction table pattern — `watchlists` + `watchlist_stocks`. Default watchlist seeded deterministically in `init_db()`. New Flask blueprint for 7 endpoints. Frontend lifts active watchlist state to the dashboard page, stores selection in localStorage, and renders a `WatchlistTabs` component above `StockGrid`. Drag-and-drop deferred to v1.1 (no DnD library currently installed).

---

### Files to Modify / Create

| File | Action |
|------|--------|
| `backend/database.py` | Add two new tables + seed migration |
| `backend/core/watchlist_manager.py` | **New** — CRUD DB layer |
| `backend/api/watchlists.py` | **New** — Blueprint with 7 endpoints |
| `backend/app.py` | Register new blueprint |
| `frontend/src/lib/types.ts` | Add `Watchlist`, `WatchlistDetail` types |
| `frontend/src/lib/api.ts` | Add 7 watchlist API functions |
| `frontend/src/components/dashboard/WatchlistTabs.tsx` | **New** — tab bar + CRUD controls |
| `frontend/src/components/dashboard/StockGrid.tsx` | Accept `watchlistId` prop; re-wire add/remove |
| `frontend/src/app/dashboard/page.tsx` | Lift `activeWatchlistId` state; compose tabs + grid |

---

### Data Model Changes

```sql
-- backend/database.py
CREATE TABLE IF NOT EXISTS watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist_stocks (
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL REFERENCES stocks(ticker),
    PRIMARY KEY (watchlist_id, ticker)
);

-- Seed in init_db() (idempotent)
INSERT OR IGNORE INTO watchlists (id, name) VALUES (1, 'My Watchlist');
INSERT OR IGNORE INTO watchlist_stocks (watchlist_id, ticker)
    SELECT 1, ticker FROM stocks WHERE active = 1;
```

Existing `stocks` table is untouched. Foreign keys + `ON DELETE CASCADE` handle junction cleanup.

---

### API Changes

New blueprint mounted at `/api/watchlists`:

| Method | Path | Notes |
|--------|------|-------|
| `GET` | `/api/watchlists` | Returns all watchlists + `stock_count` |
| `POST` | `/api/watchlists` | `{name}` → 409 on duplicate |
| `GET` | `/api/watchlists/<id>` | Returns watchlist + `tickers[]` |
| `PUT` | `/api/watchlists/<id>` | Rename; 409 on duplicate name |
| `DELETE` | `/api/watchlists/<id>` | 400 if it's the last watchlist |
| `POST` | `/api/watchlists/<id>/stocks` | `{ticker, name?}` → upserts `stocks`, inserts junction row |
| `DELETE` | `/api/watchlists/<id>/stocks/<ticker>` | Removes junction row only |

`POST /api/stocks` (existing) remains unchanged for backwards compat. The new `POST /api/watchlists/<id>/stocks` becomes the primary add path from the UI.

---

### Frontend Changes

**`WatchlistTabs`** — Horizontal scrollable tab bar. Each tab: name + delete icon (hidden when only one exists). Double-click triggers inline rename input. `+` button opens inline name entry. Communicates via `onSelect(id)`, `onCreate(name)`, `onRename(id, name)`, `onDelete(id)` callbacks.

**`StockGrid` modifications** — Accepts `watchlistId: number`. Fetches tickers via `GET /api/watchlists/<id>`, then filters the existing `ratings` array (still polled globally every 30s) to that ticker set. `addStock` → `POST /api/watchlists/<id>/stocks`; `removeStock` → `DELETE /api/watchlists/<id>/stocks/<ticker>`.

**Dashboard page** — Owns `activeWatchlistId` state, initialized from `localStorage`. Renders `<WatchlistTabs>` above `<StockGrid>`.

---

### Testing Strategy

**Backend** — `tests/test_watchlist_manager.py`: unit tests for cascade delete, unique constraint enforcement, block-last-delete guard. `tests/test_watchlist_api.py`: all 7 endpoints covering happy path + 400/409 edge cases.

**Frontend** — Component tests for `WatchlistTabs` covering create/rename/delete state transitions. Mock-API tests for the 7 new `api.ts` functions. One integration test: add stock → verify it appears only in the active watchlist's `GET` response.
