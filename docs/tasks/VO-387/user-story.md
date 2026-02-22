# VO-387: Screen reader accessibility issue in research brief export

## User Story

---

## User Story: VO-XXX — Screen Reader Accessibility in Research Brief Export

**As a** trader who relies on a screen reader,
**I want** the batch export UI to fully announce interactive controls and dynamic feedback,
**so that** I can select, configure, and trigger exports without needing sighted assistance.

---

### Acceptance Criteria

**Export Button**
- [ ] Export button has `aria-label` that reflects current state, e.g. `"Export 3 briefs as ZIP"` (dynamic, updates with selection/format)
- [ ] Exporting state announced: button label becomes `"Exporting, please wait"` while in progress
- [ ] Disabled state (`0 selected`) is announced; button is `disabled` or `aria-disabled="true"`

**Error Banner**
- [ ] Error container has `role="alert"` so errors are announced immediately on appearance
- [ ] No `aria-live` required separately — `role="alert"` implies `aria-live="assertive"`

**Export Toolbar Container**
- [ ] Toolbar wrapping element has `aria-label="Batch export"` or `role="toolbar"` with label

**Selection Count**
- [ ] An `aria-live="polite"` region announces count changes, e.g. `"3 briefs selected"` when user checks/unchecks

**Checkbox Controls**
- [ ] Individual brief checkboxes and select-all are navigable and operable via keyboard (Tab, Space)
- [ ] Current icon-button pattern retains `aria-pressed` or `aria-checked` to reflect checked state, if not converted to native `<input type="checkbox">`

**No Regression**
- [ ] Existing `aria-label` on format dropdown and per-brief checkboxes remain intact
- [ ] Mouse/keyboard behavior unchanged

---

### Priority Reasoning

**High.** Accessibility is a legal compliance requirement in most markets (WCAG 2.1 AA). The export feature is a primary workflow action — if a screen reader user cannot operate it, the entire feature is blocked for them. This was caught in QA; ship the fix before the branch merges.

---

### Estimated Complexity

**2 / 5**

All fixes are additive attribute changes and one small dynamic label computation in `page.tsx`. No backend changes, no new components, no state logic changes. Risk of regression is low.
