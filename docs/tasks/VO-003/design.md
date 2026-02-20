# VO-003: Keyboard Shortcuts for Power Users

## Technical Design

---

## Technical Design Spec: Keyboard Shortcuts

### Approach
Pure frontend — no backend or data model changes. A `KeyboardShortcutsProvider` Client Component wraps the root layout children, holding `showHelpModal` state and a `searchInputRef` shared via React context. `Header.tsx` registers its search `<input>` ref on mount. The `useKeyboardShortcuts` hook lives inside the provider, attaches a single `keydown` listener on `window`, and is the sole registration point. Guards prevent shortcut firing inside text inputs (except `Ctrl+*` and `Escape`) and during IME composition for CJK users. `Ctrl+1–5` and `/` call `event.preventDefault()` to suppress browser defaults.

---

### Files to Modify / Create

| File | Action |
|------|--------|
| `frontend/src/hooks/useKeyboardShortcuts.ts` | **New** — keydown listener, all shortcut logic, input + IME guards |
| `frontend/src/components/layout/KeyboardShortcutsProvider.tsx` | **New** — `'use client'` wrapper; holds modal state + searchRef; runs the hook |
| `frontend/src/components/layout/KeyboardShortcutsModal.tsx` | **New** — help modal triggered by `?`; shortcut reference table; closes on `Escape` or backdrop click |
| `frontend/src/app/layout.tsx` | Wrap `<main>` children in `<KeyboardShortcutsProvider>` — root layout stays a Server Component |
| `frontend/src/components/layout/Header.tsx` | Consume context to register `searchInputRef`; remove static `"/"` hint (now functional) |

---

### Data Model Changes
None.

---

### API Changes
None.

---

### Frontend Changes

**`useKeyboardShortcuts(opts)`**
- Accepts: `searchInputRef`, `onOpenHelp`, `onCloseModal`, `router`
- Attaches/removes `keydown` on `window` via `useEffect` cleanup
- **Input guard**: `const inInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable` — skips all non-`Ctrl` shortcuts when true; `Escape` still fires
- **IME guard**: skip if `event.isComposing`
- Shortcut table:

| Key | Action | `preventDefault` |
|-----|--------|-----------------|
| `Ctrl+K` | `searchInputRef.current?.focus()` | Yes |
| `/` | `searchInputRef.current?.focus()` (not in input) | Yes |
| `Ctrl+1–5` | `router.push(ROUTES[digit])` where `ROUTES = ['/', '/agents', '/research', '/scheduler', '/settings']` | Yes |
| `Escape` | `onCloseModal()` | No |
| `?` | `onOpenHelp()` (not in input) | No |

**`KeyboardShortcutsProvider`**
- `'use client'` — sole client boundary introduced at layout level
- State: `showHelp: boolean`, `searchInputRef: RefObject<HTMLInputElement>`
- Exposes context: `{ searchInputRef, setShowHelp }`
- Instantiates `useKeyboardShortcuts` with `useRouter()` from `next/navigation`
- Renders `<KeyboardShortcutsModal open={showHelp} onClose={() => setShowHelp(false)} />`

**`KeyboardShortcutsModal`**
- `fixed inset-0 bg-black/60 z-50` backdrop; centered card
- Two-column shortcut table (Action / Keys) grouped by category: Navigation, Search, General
- Styled to match existing dark slate palette (`bg-slate-900 border-slate-700`)
- Closes on backdrop click or `Escape` (via the global hook)

---

### Testing Strategy

**Unit — `useKeyboardShortcuts`**: Dispatch synthetic `KeyboardEvent`s via `fireEvent`; assert `router.push` receives correct path for `Ctrl+1–5`; assert `focus()` called for `Ctrl+K` and `/`; assert shortcuts suppressed when `target` is an `<input>`; assert IME events (`isComposing: true`) are ignored.

**Component — `KeyboardShortcutsModal`**: Renders full shortcut table; closes on `Escape` keydown and backdrop click; does not close on card click.

**E2E (Playwright)**: `Ctrl+2` → URL is `/agents`; `?` → modal visible; `Escape` → modal gone; `/` → Header search input has focus.
