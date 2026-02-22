# VO-330: Create keyboard navigation in news feed panel

## Technical Design

## VO-391: Keyboard Navigation in News Feed Panel — Technical Design Spec

---

### 1. Approach

Enhance `NewsFeed.tsx` with proper ARIA feed semantics (`role="feed"`, `role="article"`) and a dedicated `useNewsFeedKeyboard` hook that manages focus index state and handles all required key events. Focus is tracked via a `useRef` array pointing to article DOM nodes, enabling imperative `.focus()` calls. When new articles load during the 60-second refresh, the current focus index is preserved by clamping to the new list length rather than resetting.

---

### 2. Files to Create/Modify

- **CREATE**: `frontend/src/hooks/useNewsFeedKeyboard.ts` — keyboard + focus management hook
- **MODIFY**: `frontend/src/components/dashboard/NewsFeed.tsx` — add ARIA roles, wire hook, apply focus ring styles

No backend changes. No API changes. No new pages.

---

### 3. Data Model

No database changes required. Pure frontend feature.

---

### 4. API Spec

No new endpoints. Existing `GET /api/news` is sufficient.

---

### 5. Frontend Component Spec

**Hook**: `useNewsFeedKeyboard`
**File**: `frontend/src/hooks/useNewsFeedKeyboard.ts`

```ts
function useNewsFeedKeyboard(itemCount: number, containerRef: RefObject<HTMLDivElement>): {
  focusedIndex: number | null;
  itemRefs: RefObject<(HTMLElement | null)[]>;
  handleKeyDown: (e: KeyboardEvent) => void;
  activatePanel: () => void;
  releasePanel: () => void;
}
```

Key behaviors:
- `ArrowDown` / `ArrowUp`: move `focusedIndex` ± 1, clamp to `[0, itemCount-1]`, call `itemRefs.current[idx]?.focus()`
- `Home` / `End`: jump to index `0` / `itemCount-1`
- `PageDown` / `PageUp`: advance/retreat by visible item count (estimate: 5)
- `Enter`: programmatically click the focused article's anchor (`itemRefs.current[idx]?.querySelector('a')?.click()`)
- `Escape`: call `releasePanel()` — sets `focusedIndex` to `null`, returns focus to container's parent via `containerRef.current?.blur()`
- On article list refresh: clamp `focusedIndex` to `Math.min(focusedIndex, newCount - 1)` in a `useEffect`

**Modified Component**: `NewsFeed`
**File**: `frontend/src/components/dashboard/NewsFeed.tsx`

Changes:
- Scroll container: add `tabIndex={0}` to make panel focusable; `onFocus={activatePanel}`; `onKeyDown={handleKeyDown}`; `role="feed"`; `aria-label="Recent news"`; `aria-busy={loading}`
- Each article `<div>`: replace with `<article>` element; add `role="article"`, `tabIndex={-1}`, `aria-selected={focusedIndex === i}`, `ref={el => itemRefs.current[i] = el}`
- Focus ring: add `aria-selected` → `ring-2 ring-blue-500` via conditional class (consistent with existing focus patterns)
- `aria-label` on each article: `article.title` for screen reader context

Renders in: `frontend/src/app/page.tsx` — no changes needed there.

---

### 6. Verification

1. **Arrow key navigation**: Click the news panel, press `ArrowDown` — confirm each press moves the blue focus ring to the next article; `ArrowUp` moves it back; `Home`/`End` jump to first/last.

2. **Enter opens article**: Navigate to any item, press `Enter` — confirm the article URL opens in a new tab (same behavior as mouse click).

3. **Focus stability on refresh**: Focus on item 3, wait for the 60-second auto-refresh — confirm the focus ring stays on item 3 (or the last item if the list shrinks), and does not jump to the top.
