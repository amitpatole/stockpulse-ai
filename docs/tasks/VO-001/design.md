# VO-001: Watchlist Portfolio Groups with CRUD

## Technical Design Spec

### Approach

Introduce watchlists as a thin layer over the existing `stocks` table. The `stocks` table becomes a global ticker registry; named watchlists are tracked via two new tables. The active watchlist is persisted in `localStorage` — no session changes needed. Drag-and-drop is deferred to v2 per the user story guidance.

---

### Files to Modify / Create

**Backend**
- `backend/database.py` — add `watchlists` + `watchlist_stocks` table creation and migration in `init_all_tables()`
- `backend/api/watchlists.py` — new blueprint with all 8 watchlist endpoints
- `backend/app.py` — register `watchlists_bp` in `_register_blueprints()`

**Frontend — Create**
- `frontend/src/components/dashboard/WatchlistSelector.tsx` — dropdown + "+ New Watchlist" button
- `frontend/src/hooks/useWatchlists.ts` — CRUD hook wrapping watchlist API calls

**Frontend — Modify**
- `frontend/src/lib/types.ts` — add `Watchlist`, `WatchlistDetail` interfaces
- `frontend/src/lib/api.ts` — add all watchlist API functions
- `frontend/src/components/dashboard/StockGrid.tsx` — accept `watchlistId` prop; route add/remove through watchlist endpoints instead of `/api/stocks`
- `frontend/src/app/page.tsx` — compose `WatchlistSelector` above `StockGrid`, pass active watchlist state

---

### Data Model Changes

```sql
CREATE TABLE IF NOT EXISTS watchlists (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watchlist_stocks (
    watchlist_id INTEGER NOT NULL REFERENCES watchlists(id) ON DELETE CASCADE,
    ticker       TEXT NOT NULL,
    added_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (watchlist_id, ticker)
);
```

**Migration** (runs once in `init_all_tables()`): if no rows exist in `watchlists`, insert `"My Watchlist"` and populate `watchlist_stocks` from all `active = 1` rows in `stocks`.

---

### API Changes

| Method | Path | Action |
|--------|------|--------|
| `GET` | `/api/watchlists` | List all watchlists with `stock_count` |
| `POST` | `/api/watchlists` | Create (enforces unique name, max 20) |
| `GET` | `/api/watchlists/<id>` | Return watchlist + ticker array |
| `PUT` | `/api/watchlists/<id>` | Rename |
| `DELETE` | `/api/watchlists/<id>` | Delete (cascades to junction table) |
| `POST` | `/api/watchlists/<id>/stocks` | Add ticker (also inserts into `stocks` if new) |
| `DELETE` | `/api/watchlists/<id>/stocks/<ticker>` | Remove ticker from this watchlist only |

Existing `/api/stocks` and `/api/ai/ratings` endpoints are unchanged. `StockGrid` fetches `GET /api/watchlists/<id>` to get the active ticker list, then filters the ratings array client-side.

---

### Frontend Changes

- **`WatchlistSelector`**: dropdown of watchlist names with inline rename (double-click), delete (with `window.confirm`), and "+ New Watchlist" button. Active watchlist ID stored in `localStorage` key `activeWatchlistId`.
- **`useWatchlists`**: manages watchlist list state, exposes `create`, `rename`, `remove`, `addStock`, `removeStock`. Uses `useApi` pattern.
- **`StockGrid`**: receives `watchlistId: number` and `tickers: string[]` props. Filters `AIRating[]` to only tickers in the active watchlist. Add/remove calls hit watchlist-scoped endpoints.
- **Empty state**: when `tickers.length === 0`, render a prompt: *"No stocks yet — search above to add one."*

---

### Testing Strategy

**Backend**
- Unit: migration idempotency (run `init_all_tables()` twice, assert one default watchlist)
- Unit: max-20 watchlist limit returns 400
- Unit: `DELETE /api/watchlists/<id>` cascades — ticker absent from `watchlist_stocks`, present in `stocks`
- Unit: duplicate ticker in same watchlist returns 409

**Frontend**
- Component test `WatchlistSelector`: renders watchlist names, calls `onCreate` on submit
- Component test `StockGrid`: with `tickers=["AAPL"]` filters ratings to only AAPL card
- Integration (manual): create watchlist → add stock → refresh page → active watchlist restored from `localStorage`
