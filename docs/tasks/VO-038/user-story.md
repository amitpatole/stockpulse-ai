# VO-038: Keyboard shortcuts for power users

## User Story

**As a** power user who navigates the platform frequently,
**I want** keyboard shortcuts for search, page navigation, and modal control,
**so that** I can move through the app without touching the mouse and reduce time-on-task.

---

## Acceptance Criteria

**Search**
- [ ] `Ctrl+K` opens the stock search overlay from any page
- [ ] `/` focuses the inline search input when no modal or text field is active
- [ ] `Escape` closes the search overlay and returns focus to the previous element

**Page Navigation**
- [ ] `Ctrl+1` navigates to Dashboard
- [ ] `Ctrl+2` navigates to Agents
- [ ] `Ctrl+3` navigates to Research
- [ ] `Ctrl+4` navigates to News
- [ ] `Ctrl+5` navigates to Settings
- [ ] Navigation shortcuts do not fire when focus is inside a text input or textarea

**Modal Control**
- [ ] `Escape` closes any open modal; if multiple modals are stacked, closes the topmost one
- [ ] `Escape` does not close modals that require explicit confirmation (e.g. destructive actions)

**Shortcut Help Modal**
- [ ] `?` opens a shortcut reference modal listing all available shortcuts, grouped by category
- [ ] Help modal is dismissible via `Escape` or a visible close button
- [ ] Help modal is keyboard-navigable (accessible)

**Implementation**
- [ ] A `useKeyboardShortcuts` hook centralizes all shortcut registration and teardown
- [ ] Shortcuts are registered at the root layout so they are always active
- [ ] `event.preventDefault()` is called only where the shortcut conflicts with a browser default (e.g. `Ctrl+K`)
- [ ] Shortcuts are suppressed when focus is inside `<input>`, `<textarea>`, or `contenteditable` elements, except where explicitly intended (e.g. `Escape`)
- [ ] No shortcut conflicts with standard browser or OS bindings beyond those explicitly overridden

---

## Priority Reasoning

**Medium-High.** Power users — the segment most likely to drive word-of-mouth and retention — are the primary audience for this app. Keyboard shortcuts are a low-cost, high-signal feature that signals craft and reduces friction for daily workflows. The shortcut help modal (`?`) also doubles as discoverability UX for new users. No backend work required; purely frontend. Ships fast and improves perceived quality immediately.

---

## Estimated Complexity: **2 / 5**

| Area | Complexity Driver |
|---|---|
| Hook | `useKeyboardShortcuts` with event listener lifecycle — straightforward |
| Navigation | Wraps existing router calls — trivial |
| Modal control | Requires modal stack awareness; mild coordination with existing modal system |
| Help modal | New component, but purely static content — low effort |
| Edge cases | Input focus suppression, stacked modals, browser conflict avoidance |

The only non-trivial piece is ensuring `Escape` correctly handles stacked modals if the app uses multiple modal layers. If modal state is not already centralized, that's the one area that could add complexity.

---

**Owner:** Frontend
**Depends on:** Existing router and modal infrastructure
