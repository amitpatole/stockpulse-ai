# VO-357: Create drag-and-drop reorder in watchlist stocks

## User Story

Done. Here's the summary:

---

**VO-404: Drag-and-drop reorder for watchlist stocks**

**User Story:** As a trader managing a watchlist, I want to drag and drop stocks into a custom order, so that my highest-priority positions are always at the top without needing to rename tickers to force alphabetical sorting.

**Key acceptance criteria:**
- Grip handle visible on hover/focus; dragging gives immediate visual feedback
- Optimistic UI update with rollback on API failure
- `PATCH /api/watchlist/<id>/reorder` persists the new order
- `watchlist_stocks` gets a `sort_order` column; migration backfills existing rows alphabetically
- `GET /api/watchlist/<id>` returns tickers by `sort_order ASC`
- Keyboard reorder support + screen reader position announcements
- CSV import appends in file order after existing rows

**Priority:** Medium — quality-of-life for power users, not a blocker. Ship after VO-403.

**Complexity: 3/5** — The DB migration and new endpoint are clean, but frontend drag-and-drop with optimistic UI + keyboard accessibility is the real work. Recommend dnd-kit over react-beautiful-dnd (lighter, better touch support). The existing `watchlist_stocks` query at `watchlist_manager.py:60` uses `ORDER BY ticker` — that's the first thing to change.
