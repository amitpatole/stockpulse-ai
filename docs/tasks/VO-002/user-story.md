# VO-002: Keyboard Shortcuts for Power Users

## User Story

**Story**

As a power user monitoring markets throughout the trading day, I want keyboard shortcuts for navigation and search, so that I can move through the app and pull up stock data without lifting my hands off the keyboard — keeping me in flow when speed matters.

---

### Acceptance Criteria

**Navigation (Ctrl+1–5)**
- [ ] `Ctrl+1` navigates to Dashboard
- [ ] `Ctrl+2` navigates to Agents
- [ ] `Ctrl+3` navigates to Research
- [ ] `Ctrl+4` navigates to News
- [ ] `Ctrl+5` navigates to Settings
- [ ] `event.preventDefault()` is called on all Ctrl+number bindings to avoid browser tab switching

**Search**
- [ ] `Ctrl+K` opens the stock search modal and focuses the input
- [ ] `/` focuses the search input when no text field is active; `event.preventDefault()` prevents browser find-in-page
- [ ] `Escape` closes any open modal or dismisses focused search input

**Help Modal (`?`)**
- [ ] Pressing `?` (when no input is focused) opens a keyboard shortcut reference modal
- [ ] Modal displays all registered shortcuts in a clean two-column layout (key → action)
- [ ] Modal is dismissible via `Escape` or clicking outside

**Implementation**
- [ ] A `useKeyboardShortcuts` hook encapsulates all shortcut registration and teardown
- [ ] Hook is registered once in the root layout — no per-page duplication
- [ ] Shortcuts are suppressed when focus is inside `<input>`, `<textarea>`, or `[contenteditable]` (except `Escape` and `Ctrl+*`)
- [ ] No shortcut conflicts with standard browser behavior (Ctrl+W, Ctrl+T, etc.)

**Edge Cases**
- [ ] Shortcuts do not fire during IME composition (CJK input)
- [ ] Disabled or visually hidden routes still accept navigation shortcuts (graceful no-op if route doesn't exist)

---

### Priority Reasoning

**Medium-High.** This is pure power-user polish — zero backend work, low risk. Traders who live in this app all day will notice immediately. The `useKeyboardShortcuts` hook also becomes infrastructure: once it exists, adding future shortcuts costs near zero. Ship it as a self-contained sprint item.

---

### Complexity: 2 / 5

Entirely frontend. The hook pattern is well-established and the scope is tightly bounded:
- `useKeyboardShortcuts` hook with event listener lifecycle management
- Help modal component (static content, no state complexity)
- Root layout wiring

The only non-trivial decision is the focus-guard logic (suppressing shortcuts in text inputs). That's ~10 lines of well-understood DOM logic. No backend, no data model changes.
