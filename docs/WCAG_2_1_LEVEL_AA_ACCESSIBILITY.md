# Feature: WCAG 2.1 Level AA Accessibility

## Overview
Implement keyboard navigation, ARIA labels, and semantic HTML to close 40% compliance gap. Enable screen reader users and keyboard-only navigation across dashboard, navigation, modals, tables, and forms.

## Data Model
**No database changes required.** This is a frontend accessibility retrofit with no API or schema modifications.

## API Endpoints
**No API changes required.** All work is client-side component enhancement.

## Dashboard/UI Elements

### Interactive Components Requiring ARIA/Keyboard Updates
| Component | Current Gap | Required Changes |
|-----------|-----------|----------|
| **Sidebar Navigation** | Missing nav semantics, no skip link | Add `<nav>`, skip link to main content |
| **Collapse Button** | No aria-label, no keyboard focus | Add `aria-label="Toggle sidebar"`, `aria-expanded` |
| **Header Bell (Alerts)** | Icon-only button, no label | Add `aria-label="View alerts"`, show unread badge count in label |
| **Toast Messages** | Not announced to screen readers | Add `role="alert"` + `aria-live="polite"` |
| **Settings Form** | No associated labels | Wrap inputs in `<label>` or add `aria-labelledby` |
| **KPI Cards** | No heading hierarchy | Add proper `<h2>` headings, data roles |
| **Stock Grid/Table** | No table semantics if displayed as grid | Add `role="table"`, `role="row"`, `role="cell"` if needed |
| **Search Input** | Placeholder as label, no association | Convert to `<label>` + proper `for` attribute |

### Keyboard Navigation Focus Order
1. Skip link (hidden, visible on focus) → Main content
2. Sidebar toggle button → All nav links → Collapse button
3. Tab order follows visual left-to-right, top-to-bottom flow
4. Focus trap in modals (if any added), properly released on close
5. All interactive elements: buttons, links, inputs keyboard-accessible (Enter/Space for buttons, Arrow keys for menus)

## Business Rules
- **WCAG 2.1 Level AA compliance**: All POUR principles (Perceivable, Operable, Understandable, Robust)
- **Keyboard accessibility**: Every interactive element keyboard-navigable without mouse
- **Screen reader compatibility**: All dynamic content (toasts, alerts, status updates) announced via aria-live regions
- **Focus management**: Visible focus indicators (default browser or custom), no invisible focus traps
- **Color contrast**: Maintain 4.5:1 for text (already good in dark theme)
- **Alt text**: Icon-only buttons use aria-label, no decorative images need alt=""
- **Heading hierarchy**: H1 for page title, H2 for sections (prevents jumping levels)

## Edge Cases
- **Toast auto-dismiss timing**: Screen readers may miss fast toasts → Use `aria-live="assertive"` + longer duration for important alerts
- **Dynamic lists (stock feed)**: Add `aria-live="polite"` to containers updating frequently
- **Modal dialogs**: Manage focus (trap in modal, return to trigger), add `role="dialog"` + `aria-labelledby`
- **Autocomplete/typeahead**: Add `aria-expanded`, `aria-owns`, `aria-selected` if implemented
- **Disabled elements**: Use `disabled` attribute or `aria-disabled="true"` + visual indicator

## Testing Strategy

### Unit Tests (Vitest)
- **ARIA attributes presence**: Verify aria-label, aria-expanded, role attributes exist on correct elements
- **Keyboard event handling**: Test Enter/Space on buttons, Arrow keys on lists, Escape to close modals
- **Focus management**: Verify focus visible, moves in correct order, trapped in modals

### E2E Tests (Playwright)
- **Keyboard navigation flow**: Tab through entire page, verify order matches design
- **Screen reader announcements** (via Playwright accessibility testing): Verify page landmark roles, heading hierarchy
- **Toast announcements**: Confirm toast messages in accessibility tree with `role="alert"`
- **Form submission with keyboard**: Fill form with keyboard only, submit with Enter

### Automated a11y Testing (axe-core)
- Install `@axe-core/playwright` + `@axe-core/react`
- Run axe scans on all routes in CI/CD
- Assert zero critical/serious violations
- Flag best-practice items for review

### Manual Testing
- Test with screen readers: NVDA (Windows), JAWS (Windows), VoiceOver (Mac)
- Keyboard-only navigation using Tab/Shift+Tab, Enter, Escape, Arrow keys
- Firefox DevTools Accessibility Inspector for heading hierarchy, color contrast

## Files to Modify/Create

### Frontend Components (Modify)
- `frontend/src/components/layout/Sidebar.tsx` - Add nav semantics, skip link, aria-labels, keyboard trap on collapse
- `frontend/src/components/layout/Header.tsx` - Add aria-label to bell button, improve search input label association
- `frontend/src/components/ui/Toast.tsx` - Add `role="alert"`, `aria-live="polite"`, `aria-atomic="true"`
- `frontend/src/components/dashboard/StockCard.tsx` - Add heading hierarchy, proper data labeling
- `frontend/src/app/settings/page.tsx` - Wrap form inputs with labels, add required/invalid states

### Utility/Hook (Create)
- `frontend/src/hooks/useAccessibility.ts` - Custom hook for managing focus, keyboard events, ARIA state
- `frontend/src/lib/a11y.ts` - Helper functions: getFocusableElements(), manageFocus(), announceMessage()

### Tests (Create)
- `frontend/src/__tests__/accessibility.test.tsx` - ARIA attributes, heading hierarchy, landmark roles
- `frontend/e2e/accessibility.spec.ts` - Keyboard navigation, form submission, modal focus
- `frontend/e2e/axe-accessibility.spec.ts` - axe-core automated scanning on each route

### Dependencies (Add)
```json
{
  "devDependencies": {
    "@axe-core/playwright": "^4.8.0",
    "@axe-core/react": "^4.8.0",
    "vitest": "^1.0.0",
    "playwright": "^1.40.0"
  }
}
```

## Changes & Deprecations
- Initial implementation (Sprint N): All interactive components retrofitted
- Future: Audit for color contrast, animation preferences (prefers-reduced-motion)
