# VO-345: Create drag-and-drop reorder in watchlist stocks

## Technical Design

### 1. Approach

Add a `position` column to `watchlist_stocks` and a new `PATCH /api/watchlist/reorder` endpoint that atomically rewrites positions for a given watchlist. On the frontend, replace the existing `moveUp`/`moveDown` buttons in `StockGrid.tsx` with `@dnd-kit/sortable`, applying an optimistic update on drag-end and reverting with an error toast if the API call fails.

---

### 2. Files to Create/Modify

- **MODIFY**: `backend/database.py` — add `position INTEGER NOT NULL DEFAULT 0` to `watchlist_stocks`, add migration for existing rows
- **MODIFY**: `backend/core/watchlist_manager.py` — add `reorder_stocks()`, update `get_watchlist()` to `ORDER BY position`, update `add_stock_to_watchlist()` to append at `MAX(position)+1`
- **CREATE**: `backend/api/watchlist.py` — `watchlist_bp` with `PATCH /api/watchlist/reorder`
- **MODIFY**: `backend/app.py` — register `watchlist_bp`
- **MODIFY**: `frontend/src/lib/types.ts` — add `position: number` to `Stock`
- **MODIFY**: `frontend/src/lib/api.ts` — add `reorderWatchlist(watchlistId, tickers)`
- **MODIFY**: `frontend/src/components/dashboard/StockGrid.tsx` — integrate `@dnd-kit/sortable`, replace `moveUp`/`moveDown` with drag-and-drop
- **MODIFY**: `frontend/src/components/dashboard/StockCard.tsx` — accept `dragHandleProps`, render grip icon handle

---

### 3. Data Model

```sql
-- Add to watchlist_stocks (migration for existing rows assigns sequential position)
ALTER TABLE watchlist_stocks ADD COLUMN position INTEGER NOT NULL DEFAULT 0;

UPDATE watchlist_stocks
SET position = (
  SELECT COUNT(*) FROM watchlist_stocks ws2
  WHERE ws2.watchlist_id = watchlist_stocks.watchlist_id
    AND ws2.ticker < watchlist_stocks.ticker
);
```

---

### 4. API Spec

**`PATCH /api/watchlist/reorder`**

Request:
```json
{ "watchlist_id": 1, "tickers": ["MSFT", "AAPL", "GOOGL"] }
```

Response `200`:
```json
{ "ok": true }
```

Response `400`: `{ "error": "missing watchlist_id or tickers" }`
Response `404`: `{ "error": "watchlist not found" }`

Implementation: single transaction that sets `position = idx` for each ticker in the provided order. Tickers not in the list are rejected with `400`.

---

### 5. Frontend Component Spec

**Component**: `StockGrid.tsx` (`frontend/src/components/dashboard/StockGrid.tsx`)

- Wrap the stock list in `<DndContext>` + `<SortableContext items={tickers}>` from `@dnd-kit/sortable`
- Each `StockCard` wrapped in a `useSortable(ticker)` hook; pass `attributes`, `listeners`, `setNodeRef`, `transform`, `isDragging` down as props
- `StockCard` renders a `GripVertical` (lucide) icon that receives `dragHandleProps` (`listeners` + `attributes`); row gets `style={{ transform }}` for live preview and reduced opacity when `isDragging`
- `onDragEnd`: apply optimistic reorder to local state immediately, call `reorderWatchlist(watchlistId, newOrder)`, on error restore previous state and call `toast.error("Reorder failed — order restored")`
- Remove `moveUp`/`moveDown` buttons and their keyboard handler logic
- Loading state: drag handle disabled while reorder request in-flight
- Price WebSocket updates use `ticker` as key — order change only touches array index, no re-fetch triggered

**Renders in**: `frontend/src/app/page.tsx` (already imported, no change needed)

---

### 6. Verification

1. **Persistence**: Drag AAPL above MSFT, refresh the page — AAPL must still appear first.
2. **Revert on failure**: With DevTools set to offline, drag a stock — after drop it should snap back and show the error toast.
3. **No breakage during live updates**: With the WebSocket price stream active, drag a card — prices must continue updating and no cards should jump or reset position mid-drag.
