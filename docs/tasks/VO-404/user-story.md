# VO-404: Drag-and-drop reorder for watchlist stocks

## User Story

**As a** trader managing a watchlist, **I want** to drag and drop stocks into a custom order, **so that** my highest-priority positions are always at the top without needing to rename tickers to force alphabetical sorting.

---

### Acceptance Criteria

**Interaction**
- A drag handle (grip icon) is visible on each watchlist row on hover/focus
- Dragging a row and dropping it at a new position reorders the list immediately (optimistic UI)
- The dragged row has a distinct visual state (elevated shadow, reduced opacity on origin slot)
- Dropping outside a valid target snaps the row back to its original position

**Persistence**
- Custom order is saved to the backend via `PATCH /api/watchlist/<id>/reorder` with the new ordered list of tickers
- On page reload, the watchlist renders in the saved custom order
- If the API call fails, the UI rolls back to the pre-drag order and shows an error toast

**Database**
- `watchlist_stocks` gains a `sort_order INTEGER NOT NULL DEFAULT 0` column (migration handles existing rows by assigning sequential values matching current alphabetical order)
- `GET /api/watchlist/<id>` returns tickers ordered by `sort_order ASC`
- Adding a new ticker appends it at the end (`sort_order = MAX(sort_order) + 1`)
- Removing a ticker does not compact remaining `sort_order` values (sparse is fine)

**Accessibility & keyboard**
- Keyboard users can reorder via arrow keys while a row is in "drag mode" (activated via Space/Enter on the handle)
- Screen readers announce position changes (e.g., "AAPL moved to position 2 of 8")

**Regression**
- CSV import appends imported tickers in file order after existing rows
- All existing watchlist CRUD endpoints behave identically (no sort_order exposed in responses that don't need it)

---

### Priority Reasoning

**Medium.** This is a quality-of-life improvement, not a correctness issue — the watchlist works today. However, power users managing 20+ tickers feel the friction of alphabetical-only ordering acutely. It's a visible, high-satisfaction feature with a clear implementation path. Ship after the VO-403 bug fix; don't block on it.

---

### Estimated Complexity

**3 / 5**

- DB migration is low-risk but required — one new column, one backfill query
- New `PATCH /api/watchlist/<id>/reorder` endpoint is straightforward but needs input validation (must be a permutation of existing tickers, no additions/removals)
- Frontend DnD: pick one library (dnd-kit recommended — lighter than react-beautiful-dnd, better touch support) and integrate into the existing watchlist list component
- Optimistic UI + rollback adds meaningful state management work
- Keyboard accessibility for drag-and-drop is non-trivial to get right
