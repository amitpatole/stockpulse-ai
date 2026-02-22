# VO-345: Create drag-and-drop reorder in watchlist stocks

## User Story

Good. I'll write this as a new user story — Theo's feature request deserves its own ticket. Here it is:

---

## VO-395: Drag-and-Drop Reorder in Watchlist Stocks

---

### User Story

**As a** trader managing a watchlist,
**I want** to drag and drop stocks into a custom order,
**so that** my highest-priority positions stay at the top and I can scan my watchlist the way I think, not alphabetically.

---

### Acceptance Criteria

- User can drag any stock row in the watchlist and drop it at a new position
- Order persists across page reloads and sessions (stored server-side per user)
- Drag handle is visible on hover; row highlights while dragging to indicate valid drop zones
- Order updates optimistically on drop with a silent background save; reverts on API failure
- Keyboard alternative: accessible reorder via up/down controls for non-mouse users
- Works correctly with watchlists of 1 stock (no drag) and 50+ stocks (no perf degradation)
- Existing watchlist add/remove behavior is unchanged

---

### Priority Reasoning

**Medium.** Watchlist is the daily-driver view for power users — Theo's request signals this is a real workflow friction point. Custom ordering is table-stakes UX for any watchlist tool. No blocking dependencies; purely additive. Not P1 because it doesn't fix broken functionality, but should land within the next 2 sprints.

---

### Estimated Complexity

**3 / 5**

Frontend drag-and-drop (HTML5 DnD or a lightweight lib like `@dnd-kit`) is well-understood but has edge cases (touch support, accessibility, scroll-while-dragging). Backend needs a new `position` column and a PATCH endpoint to persist order. Main risk is accessibility completeness and optimistic-update rollback logic.
