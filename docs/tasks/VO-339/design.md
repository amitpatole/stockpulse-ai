# VO-339: Create keyboard navigation in news feed panel

## Technical Design

Now I have the complete picture. Here is the design spec.

---

## VO-330: Keyboard Navigation — News Feed Panel

### 1. Approach

Add a `focusedIndex` state to `NewsFeed.tsx` and a local `keydown` listener that handles `ArrowUp`/`ArrowDown`/`Enter`/`Escape` when the panel is active. Wire the global `N` shortcut through the existing `KeyboardShortcutsProvider` context using the same registration pattern already in place for the search input: `NewsFeed` registers a `focusNewsFeed` callback on mount, the provider stores and forwards it to `useKeyboardShortcuts`, which calls it when `N` is pressed (outside any input). No backend changes are required.

---

### 2. Files to Create/Modify

- **MODIFY**: `frontend/src/components/dashboard/NewsFeed.tsx`
  (add `focusedIndex` state, ARIA roles, item refs, keydown handler, register with context)
- **MODIFY**: `frontend/src/hooks/useKeyboardShortcuts.ts`
  (add `onFocusNewsFeed?: () => void` option; fire it on `N` key, after the `inInput` guard)
- **MODIFY**: `frontend/src/components/layout/KeyboardShortcutsProvider.tsx`
  (add `registerNewsFeed` to context value and state; pass callback to `useKeyboardShortcuts`)
- **MODIFY**: `frontend/src/components/KeyboardShortcutsModal.tsx`
  (add `{ keys: ['N'], description: 'Focus news feed' }` to the Navigation shortcut group)

---

### 3. Data Model

None. Pure frontend feature, no database changes.

---

### 4. API Spec

None. No new endpoints.

---

### 5. Frontend Component Spec

**Component**: `NewsFeed` — `frontend/src/components/dashboard/NewsFeed.tsx`

**State additions**:
- `focusedIndex: number | null` — `null` means panel is inactive
- `itemRefs: React.RefObject<HTMLDivElement>[]` — one ref per article, rebuilt when `articles` changes
- `listRef: React.RefObject<HTMLDivElement>` — ref on the scrollable container

**ARIA changes** (article list is read-only selection, `listbox`/`option` is the correct pattern):
- Scrollable `<div>` (currently `class="divide-y..."`) → add `role="listbox"` + `ref={listRef}` + `aria-label="News articles"`
- Each article wrapper `<div>` → add `role="option"`, `tabIndex={focusedIndex === i ? 0 : -1}`, `aria-selected={focusedIndex === i}`, `ref={itemRefs[i]}`, visual highlight class when selected (e.g., `bg-slate-700/40 ring-1 ring-blue-500/50`)

**Keyboard handler** (`useEffect`, `window` keydown, active only when `focusedIndex !== null`):

| Key | Behavior |
|---|---|
| `ArrowDown` | `(focusedIndex + 1) % articles.length`, then `scrollIntoView({ block: 'nearest' })` |
| `ArrowUp` | `(focusedIndex - 1 + n) % n`, then `scrollIntoView` |
| `Enter` | `window.open(articles[focusedIndex].url, '_blank', 'noopener,noreferrer')` |
| `Escape` | `setFocusedIndex(null)`, `document.body.focus()` |

**Context registration** (`useEffect` on mount):
```ts
const { registerNewsFeed } = useKeyboardShortcutsContext();
useEffect(() => {
  registerNewsFeed(() => { setFocusedIndex(0); listRef.current?.focus(); });
  return () => registerNewsFeed(null);
}, []);
```

**Renders in**: `frontend/src/app/page.tsx` (unchanged — `<NewsFeed />` already placed in the right sidebar column).

---

### 6. Verification

1. **`N` key → panel activates**: From the dashboard (cursor not in any input), press `N`. The first article gains a visible blue focus ring and `aria-selected="true"`; pressing `ArrowDown` cycles forward and scrolls the item into view when it is below the visible area of the `max-h-[600px]` container.

2. **Enter opens article, Escape exits**: With an article selected, press `Enter` — the article URL opens in a new tab. Press `Escape` — `focusedIndex` resets to `null`, the highlight disappears, and no article has `aria-selected`.

3. **Input guard and help modal**: While typing in the stock search input, pressing `N` does nothing. With the `?` help modal open, the `N` shortcut entry appears in the Navigation group under the label "Focus news feed".
