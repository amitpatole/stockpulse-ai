# VO-370: Screen reader accessibility issue in watchlist management

## Technical Design

## VO-368: Screen Reader Accessibility — Technical Design Spec

### Approach

Pure frontend markup and ARIA work — no backend changes. Two files are the main targets: `StockGrid.tsx` (container/search/announce) and `StockCard.tsx` (per-item actions). Use the existing `KeyboardShortcutsModal.tsx` as the in-codebase reference for correct modal/focus-trap patterns.

---

### Files to Modify/Create

| File | Change |
|---|---|
| `frontend/src/components/dashboard/StockGrid.tsx` | Add `<ul>` wrapper, `aria-live` region, search listbox ARIA, keyboard reorder logic |
| `frontend/src/components/dashboard/StockCard.tsx` | Add `<li>`, descriptive `aria-label` on all buttons, SR-only text for color-only indicators |
| `frontend/src/components/dashboard/WatchlistRenameModal.tsx` | **New** — focus-trapped rename dialog (mirror `KeyboardShortcutsModal` pattern) |
| `frontend/src/components/dashboard/WatchlistDeleteModal.tsx` | **New** — focus-trapped delete confirmation dialog |

No new routes, no new API endpoints, no DB changes.

---

### Data Model & API Changes

None. The backend watchlist CRUD (`watchlist_manager.py`) is already complete. The existing `deleteStock` and `addStock` functions in `api.ts` are sufficient.

---

### Frontend Changes

**StockGrid.tsx**
- Wrap stock list in `<ul role="list" aria-label="Watchlist">` with each `StockCard` rendered in `<li>`
- Add `<div aria-live="polite" aria-atomic="true" className="sr-only">` that receives messages like `"AAPL added to watchlist"` / `"AAPL removed from watchlist"` on action completion
- Search results dropdown: add `role="listbox"` on the dropdown container, `role="option"` + `aria-selected` on each result, `aria-controls` + `aria-expanded` on the input
- Add local `order` state (array of tickers); expose Move Up / Move Down buttons per card, visible only on keyboard focus (`focus-within`). Use `aria-keyshortcuts` to document arrow key behavior.

**StockCard.tsx**
- Remove button: change from hover-only opacity to always visible (keyboard-focusable), add `aria-label={`Remove ${ticker} from watchlist`}`
- All rating/sentiment badges: add `<span className="sr-only">` with text label alongside the color dot (e.g., `<span className="sr-only">Rating: Strong Buy</span>`)
- RSI/sentiment progress bars: add `role="meter"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-label`
- Wrap the entire card in a focusable element with `aria-label={`${ticker}, ${price}, ${change}%`}`

**WatchlistRenameModal / WatchlistDeleteModal (new)**
- Pattern: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to modal heading
- Focus trap on mount (first focusable element), Escape closes, focus returns to trigger button on close
- Mirrors existing `KeyboardShortcutsModal.tsx` implementation exactly

---

### Testing Strategy

- **Automated**: Add axe-core to the frontend test suite (`jest-axe`); write a snapshot + axe scan test for `StockGrid` and `StockCard` asserting zero critical violations
- **Unit**: Test `aria-live` message state updates in `StockGrid` on add/remove actions using React Testing Library (`getByRole('status')`)
- **Keyboard**: Manual test plan covering: Tab order through cards → Move Up/Down reorder → modal open/close focus return → search dropdown arrow navigation
- **No backend tests needed**
