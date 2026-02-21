# VO-375: Screen reader accessibility issue in agent run history

## User Story

# VO-372: Screen Reader Accessibility in Agent Run History

## User Story

**As a** visually impaired trader using a screen reader,
**I want** the agent run history to be fully navigable and announced correctly by assistive technology,
**so that** I can review past agent executions, their statuses, and outputs without relying on visual cues.

---

## Acceptance Criteria

- [ ] All agent run history entries have proper ARIA roles (`role="list"`, `role="listitem"`) or use semantic HTML equivalents
- [ ] Each run entry announces: agent name, run status (success/failure/running), timestamp, and duration
- [ ] Status indicators (icons/colors) have accessible text alternatives (`aria-label` or visually hidden text)
- [ ] Interactive elements (expand/collapse, retry, view logs) are keyboard-focusable and have descriptive `aria-label` attributes
- [ ] Dynamic updates (new runs appearing, status changes) trigger `aria-live` announcements so screen readers notify without focus disruption
- [ ] Error states and failure messages are programmatically associated with their run entry
- [ ] Passes WCAG 2.1 AA compliance check for the run history component

---

## Priority Reasoning

**High.** Accessibility is both a legal obligation and a user trust issue. A platform managing financial workflows cannot exclude users with disabilities. This was caught in QA — shipping it means shipping a known regression.

---

## Complexity: 3 / 5

Localized to the agent run history component. No backend changes required. Complexity comes from handling dynamic/live updates correctly with `aria-live` regions without creating announcement noise.
