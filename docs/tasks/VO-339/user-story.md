# VO-339: Create keyboard navigation in news feed panel

## User Story

Good context. The `NewsFeed.tsx` uses plain `<div>` wrappers with no focus management — nothing keyboard-navigable. The existing `useKeyboardShortcuts.ts` handles global shortcuts but has no panel-specific navigation. Here's the user story:

---

## VO-392: Keyboard Navigation — News Feed Panel

**User Story**

> As a keyboard-driven trader, I want to navigate the news feed panel using arrow keys and open articles with Enter, so that I can scan and act on market news without reaching for the mouse.

---

**Acceptance Criteria**

- `N` (when not in an input) focuses the news feed panel and selects the first article
- `ArrowDown` / `ArrowUp` move the selection one article at a time; selection wraps at both ends
- `Enter` on a selected article opens it in a new tab (mirrors existing `<a target="_blank">` behavior)
- `Escape` from within the panel returns focus to the document body
- The active article is visually indicated (focus ring or highlight) and has `aria-selected="true"`
- The article list container has `role="listbox"`, each item has `role="option"` with `tabIndex`
- Scrolls the highlighted item into view when navigating past the visible area (panel is `max-h-[600px] overflow-y-auto`)
- `N` shortcut is registered in the `KeyboardShortcutsModal` help overlay
- Shortcut does not fire when the user is typing in any `INPUT` / `TEXTAREA` / `contenteditable` (matches the existing guard in `useKeyboardShortcuts.ts`)

---

**Priority Reasoning**

Medium. The panel is read-only and mouse-accessible today, so no regression risk. Power users on trading desks heavily favor keyboard workflows — this is a productivity multiplier for the core audience. Sequenced after VO-391 (screen reader accessibility) since the ARIA roles introduced here build on the same accessibility foundation.

---

**Estimated Complexity: 2 / 5**

All work is in `NewsFeed.tsx` and `useKeyboardShortcuts.ts`. No backend changes. State is a single `focusedIndex` integer. The scroll-into-view and wrap-around logic are the only non-trivial pieces.
