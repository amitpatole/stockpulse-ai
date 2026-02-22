# VO-345: Create drag-and-drop reorder in watchlist stocks

## User Story

# User Story: Drag-and-Drop Watchlist Reorder

## User Story
As a trader, I want to drag and drop stocks in my watchlist to reorder them, so that I can prioritize my most important positions at the top without navigating through settings.

---

## Acceptance Criteria

- [ ] Stocks in the watchlist have a visible drag handle (or are draggable by row)
- [ ] Dragging a stock row updates its position in real time with a visual placeholder
- [ ] New order persists after page refresh (saved to backend)
- [ ] Order is per-user (not global)
- [ ] Works on desktop (mouse); touch support is out of scope for v1
- [ ] No existing watchlist functionality is broken (add, remove, price updates)
- [ ] If a reorder request fails, the UI reverts to the previous order and shows an error

---

## Priority Reasoning

**Medium priority.** This is a quality-of-life feature, not a blocker. Traders who actively manage large watchlists will get immediate value — disorganized watchlists create friction during fast-moving markets. No external dependencies. Straightforward to ship.

---

## Estimated Complexity

**3 / 5**

- Frontend: drag-and-drop library integration (e.g. `dnd-kit` or `@dnd-kit/sortable`) + optimistic UI update
- Backend: new `PATCH /watchlist/reorder` endpoint, add `position` column to watchlist table, update ordering logic
- Risk: race conditions if price WebSocket updates fire mid-drag
