# VO-345: Create drag-and-drop reorder in watchlist stocks

## Technical Design

Here's the design spec for VO-395:

---

### 1. Approach

Use `@dnd-kit/core` + `@dnd-kit/sortable` on the frontend — lightweight, accessibility-aware, handles touch and scroll-while-dragging. Add a `position` column to `watchlist_stocks` for server-side persistence. New `PATCH /api/watchlist/<id>/reorder` endpoint persists order atomically. Frontend applies order optimistically on drop and reverts to a pre-drag snapshot on failure.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/database.py` — add `position` column + index to `watchlist_stocks`, backfill existing rows
- **MODIFY**: `backend/core/watchlist_manager.py` — add `reorder_stocks(watchlist_id, tickers)`, add `ORDER BY position` to `get_watchlist()`
- **CREATE**: `backend/api/watchlist.py` — new blueprint with `PATCH /api/watchlist/<id>/reorder`
- **MODIFY**: `backend/app.py` — register `watchlist_bp`
- **MODIFY**: `frontend/src/components/dashboard/StockGrid.tsx` — `DndContext` wrapper, drag handles, keyboard Up/Down buttons, optimistic update + rollback
- **MODIFY**: `frontend/src/lib/api.ts` — add `reorderWatchlist(watchlistId, tickers)`
- **MODIFY**: `frontend/src/lib/types.ts` — add `position: number` to `Stock` type

---

### 3. Data Model

```sql
ALTER TABLE watchlist_stocks ADD COLUMN position INTEGER NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS idx_watchlist_stocks_pos ON watchlist_stocks (watchlist_id, position);
```

SQLite doesn't support `ADD COLUMN IF NOT EXISTS` — wrap `ALTER TABLE` in a `try/except OperationalError` in `database.py`. Backfill existing rows by ranking alphabetically on first run.

---

### 4. API Spec

```
PATCH /api/watchlist/<int:watchlist_id>/reorder
Body:  { "tickers": ["TSLA", "AAPL", "MSFT"] }
200:   { "ok": true }
400:   { "error": "tickers must be a non-empty list" }
404:   { "error": "watchlist not found" }
```

Single transaction: `UPDATE watchlist_stocks SET position = ? WHERE watchlist_id = ? AND ticker = ?` for each index. Unknown tickers silently skipped — add/remove is a separate flow.

---

### 5. Frontend Component Spec

**`StockGrid`** (`frontend/src/components/dashboard/StockGrid.tsx`) — modified in place, already rendered in `frontend/src/app/page.tsx` so no page-level changes.

- Wrap list in `<DndContext onDragEnd>` + `<SortableContext strategy={verticalListSortingStrategy}>`
- Each `StockCard` becomes a `useSortable` item with a `GripVertical` drag handle (`opacity-0 group-hover:opacity-100`)
- Optimistic: save `snapshot = [...stocks]` before drop → `setStocks(reordered)` → fire API → on catch, `setStocks(snapshot)` + error toast
- Keyboard: "Move up" / "Move down" buttons on each row trigger the same save path; `aria-live="polite"` region announces _"TSLA moved to position 1 of 12"_

---

### 6. Verification

1. **Persistence**: Drag TSLA above AAPL, hard-reload — TSLA stays first; confirm in SQLite: `SELECT ticker, position FROM watchlist_stocks ORDER BY position`.
2. **Rollback**: DevTools → Network → Offline, drag a stock — it snaps back to original position, error toast appears.
3. **Keyboard**: Tab to a row's "Move up" button, press Space — stock shifts one slot, aria-live announces new position, order persists after reload.
