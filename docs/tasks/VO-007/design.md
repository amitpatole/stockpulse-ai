# VO-007: Add keyboard shortcuts for power users

## Technical Design

Here's the design spec I've written:

---

**Key architectural decisions:**

**Client boundary placement** — `layout.tsx` is a Server Component and must stay that way (Next.js 16 App Router). `KeyboardShortcutsProvider` is the thin `'use client'` wrapper inserted just inside `<main>`, keeping the server component tree intact.

**Search ref plumbing** — Rather than `document.querySelector` hacks or global events, `Header.tsx` registers its input ref through context. Clean, typed, and SSR-safe.

**Single registration point** — The hook lives inside `KeyboardShortcutsProvider` only. No per-page `useEffect` duplication, no risk of double-firing.

**Input guard design** — The `inInput` check covers `INPUT`, `TEXTAREA`, and `contentEditable` elements. `Escape` is exempt (always fires) so modals can be dismissed while typing. `Ctrl+*` shortcuts also bypass the guard intentionally.

**Route mapping** — The user story mentions "news" for `Ctrl+4`, but the app has `/scheduler` (no news page). I've mapped to the actual routes: `1→/ 2→/agents 3→/research 4→/scheduler 5→/settings`. Flag this with product if the intent was to add a `/news` page.

**No new abstractions** — The modal is a one-off component, not a generic dialog system. That abstraction can come later if/when more modals land.
