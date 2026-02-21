# VO-371: Screen reader accessibility issue in agent run history

## User Story

## User Story: VO-368 — Screen Reader Accessibility in Agent Run History

---

### User Story

**As a** visually impaired trader using a screen reader,
**I want** the agent run history to be fully navigable and descriptively announced,
**so that** I can review past AI agent actions and outcomes without relying on visual cues.

---

### Acceptance Criteria

- All agent run history entries are wrapped in appropriate semantic HTML (`<table>`, `<list>`, or `<article>` elements — whichever matches current structure)
- Each run entry includes an `aria-label` or `aria-describedby` that conveys: agent name, run status (success/failure/running), timestamp, and duration
- Status indicators (icons, color badges) have text equivalents via `aria-label` or visually hidden `<span>` — color alone must not convey state
- Interactive elements (retry, view details, cancel) are reachable via keyboard tab order and have descriptive labels (not just "button" or "click here")
- Dynamic updates (new runs appearing, status changes) are announced via an `aria-live` region with appropriate politeness level (`polite` for new runs, `assertive` for failures)
- No keyboard focus traps in the run history panel
- Verified passing with at least one screen reader (NVDA + Chrome or VoiceOver + Safari)

---

### Priority Reasoning

**High.** Accessibility is a legal compliance requirement (WCAG 2.1 AA) and a trust signal for enterprise clients. Bugs in this area carry reputational and regulatory risk. Agent run history is a core workflow surface — traders reference it constantly.

---

### Estimated Complexity

**3 / 5**

Likely no backend changes needed. Scope is contained to the run history component. Main effort is auditing the existing markup, adding ARIA attributes, and testing with real screen reader tooling. Risk is moderate — live region behavior can be tricky to tune without over-announcing.

---

**Assignee:** Frontend eng with accessibility experience preferred.
**Linked area:** Agent run history UI component.
