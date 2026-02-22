# VO-330: Create keyboard navigation in news feed panel

## User Story

## VO-390: Keyboard Navigation in News Feed Panel

---

### User Story

As a **power user monitoring multiple stocks**, I want to **navigate the news feed panel using keyboard shortcuts**, so that I can **quickly scan headlines and open articles without switching to my mouse**, keeping my workflow fast and uninterrupted.

---

### Acceptance Criteria

- **Arrow keys** (Up/Down) move focus between news items in the feed
- **Enter** opens the focused news item (link or detail view)
- **Home / End** jump to the first / last item in the visible feed
- **Page Up / Page Down** scroll the feed by a visible page increment
- Focused item is visually highlighted (focus ring, consistent with existing UI)
- Focus is trapped within the panel when it is active; **Escape** releases focus back to the page
- Works correctly when new items load (infinite scroll / live updates) — focus does not jump unexpectedly
- Keyboard navigation is accessible to screen readers (ARIA roles: `feed`, `article`, `aria-selected`)
- No regression to existing mouse/click behavior

---

### Priority Reasoning

**Medium-High.** News feed is a primary interaction surface — users spend significant time here. Keyboard nav directly reduces friction for analysts monitoring fast-moving markets. It's also a prerequisite for full WCAG 2.1 AA compliance, which has been flagged as a broader goal. Low risk of breaking existing functionality.

---

### Estimated Complexity

**3 / 5**

Pure frontend work. The main complexity is handling dynamic list updates (live feed) without disrupting focus state, and ensuring ARIA semantics are correct. No backend changes required.
