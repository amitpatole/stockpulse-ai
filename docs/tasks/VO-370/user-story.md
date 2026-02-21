# VO-370: Screen reader accessibility issue in watchlist management

## User Story

## VO-368: Screen Reader Accessibility in Watchlist Management

---

### User Story

**As a** visually impaired trader using a screen reader,
**I want** all watchlist management actions (add, remove, reorder, rename) to be fully announced and navigable via keyboard,
**so that** I can manage my watchlists independently without relying on sighted assistance.

---

### Acceptance Criteria

- All interactive watchlist elements (buttons, inputs, list items) have descriptive `aria-label` or `aria-labelledby` attributes
- Add/remove stock actions announce success or failure via `aria-live` region (e.g., "AAPL added to Watchlist 1")
- Watchlist items are implemented as a proper list (`<ul>`/`<li>`) so screen readers convey count and position (e.g., "3 of 7")
- Drag-to-reorder has a keyboard-accessible alternative (e.g., move up/down with arrow keys + explicit ARIA state)
- Modal dialogs (rename, delete confirm) trap focus and return focus to trigger element on close
- No critical actions are conveyed through color or icon alone — all have visible or SR-only text labels
- Passes automated accessibility scan (axe or equivalent) with zero critical violations in the watchlist component

---

### Priority Reasoning

**High.** Accessibility is a legal and ethical baseline, not a nice-to-have. Screen reader users are completely blocked from core functionality. This is a regression risk and a reputational liability if surfaced publicly.

---

### Estimated Complexity

**3 / 5** — Primarily markup and ARIA attribute work. Keyboard reorder alternative is the most involved piece. No backend changes expected.
