# Technical Spec: WCAG 2.1 Level AA Accessibility Implementation

**Ticket**: TP-A11Y-001
**Target**: Close 40% compliance gap via ARIA labels, keyboard navigation, semantic HTML
**Scope**: Frontend only (no DB/API changes)
**Duration**: 3 sprints (phased rollout)

---

## Approach

**3-Phase Frontend-Only Retrofit**:

1. **Phase 1: Core Semantics + ARIA** (Sprint 1)
   - Add `<nav>`, landmark roles (`main`, `region`), heading hierarchy (H1→H2)
   - Retrofit ARIA labels to icon buttons (bell, collapse, settings)
   - Convert toast to `role="alert"` + `aria-live="polite"`

2. **Phase 2: Keyboard Navigation** (Sprint 2)
   - Implement focus management utilities (getFocusableElements, manageFocus)
   - Tab order: skip link → sidebar → main content → footer
   - Modal focus trap (if modals added in future)
   - Arrow key navigation for menus/lists

3. **Phase 3: Automated Testing** (Sprint 3)
   - Set up axe-core scanning in Playwright E2E
   - Add Vitest unit tests for ARIA attributes
   - CI/CD gate: zero critical violations

---

## Files to Modify/Create

### Core Components (Modify)
| File | Changes |
|------|---------|
| `frontend/src/components/layout/Sidebar.tsx` | Add `<nav>`, `aria-label="Navigation"`, skip link, collapse button `aria-expanded` state |
| `frontend/src/components/layout/Header.tsx` | Bell icon: `aria-label="View alerts ({count} unread)"`, search input proper `<label>` |
| `frontend/src/components/ui/Toast.tsx` | Add `role="alert"`, `aria-live="polite"`, `aria-atomic="true"` |
| `frontend/src/components/dashboard/KPICards.tsx` | Replace divs with semantic `<section>`, add `<h2>` headings |
| `frontend/src/components/dashboard/StockCard.tsx` | Add `role="region"`, `aria-labelledby` for card title |
| `frontend/src/app/settings/page.tsx` | Wrap all inputs with `<label>`, add `aria-required`, `aria-invalid` states |

### New Utilities (Create)
| File | Purpose |
|------|---------|
| `frontend/src/lib/a11y.ts` | Helper functions: `getFocusableElements()`, `manageFocus()`, `announceMessage()` |
| `frontend/src/hooks/useAccessibility.ts` | Custom hook: focus management, keyboard event listeners, ARIA state sync |

### Tests (Create)
| File | Coverage |
|------|----------|
| `frontend/src/__tests__/accessibility.test.tsx` | Vitest: ARIA attributes, heading hierarchy, semantic roles on 10+ components |
| `frontend/e2e/accessibility.spec.ts` | Playwright: Tab navigation order, form submission, modal focus (if needed) |
| `frontend/e2e/axe-accessibility.spec.ts` | axe-core: Auto-scan ≥5 routes, assert zero critical violations |

---

## Data Model & API Changes

**None.** This is a client-side component enhancement. No database schema or backend endpoint modifications.

---

## Frontend Implementation Details

### ARIA Label Strategy
- **Icon buttons**: `aria-label="Toggle sidebar"`, `aria-label="View alerts (3)"`
- **Inputs**: `<label htmlFor="id">` or `aria-labelledby="id"`
- **Dynamic regions**: `aria-live="polite"` (toasts, stock updates), `aria-live="assertive"` (critical alerts)

### Keyboard Navigation
- **Tab order**: Skip link → Sidebar toggle → Nav links → Main content → Footer
- **Modals** (future): Trap focus inside, manage with `useEffect` cleanup
- **Arrow keys**: Available in dropdown menus, list navigation
- **Escape**: Close modals, clear search (implement handlers in `useAccessibility`)

### Focus Management
- **Visible focus**: Enforce `:focus-visible` in Tailwind (already available)
- **Focus order**: Document via `tabIndex` props on custom interactive elements
- **Skip link**: Hidden, visible on first Tab key press (CSS: `opacity-0 focus:opacity-100`)

---

## Testing Strategy

### Phase 1: Unit Tests (Vitest)
- Component renders with correct `aria-*` attributes
- Heading hierarchy: no skipped levels (H1→H2→H3)
- Semantic roles present: `role="navigation"`, `role="alert"`, etc.
- **Example**: Test `Sidebar.tsx` has `<nav aria-label="Navigation">`

### Phase 2: E2E Tests (Playwright)
- Keyboard navigation: Tab through page, verify focus visible and in order
- Form submission: Fill form with keyboard only (no mouse), submit with Enter
- Toast announces to accessibility tree with `role="alert"`
- **Example**: Test tab order matches: skip link → sidebar toggle → nav links

### Phase 3: Automated (axe-core)
- Run `axe()` scan on ≥5 key routes in CI/CD
- Assert **zero critical + serious violations**
- Log best-practice warnings for review
- **Plugin**: Use `@axe-core/playwright` + custom reporter

---

## Success Criteria

✅ WCAG 2.1 Level AA: 0 critical + serious violations (axe-core)
✅ Keyboard-only navigation: All interactive elements accessible via Tab + Enter/Space
✅ Screen readers: All dynamic content announced (role="alert" on toasts)
✅ Tests: 100% of modified components have ARIA + keyboard nav tests
✅ Docs: Code review references WCAG_2_1_LEVEL_AA_ACCESSIBILITY.md

---

## Dependencies to Add

```json
{
  "devDependencies": {
    "@axe-core/playwright": "^4.8.0",
    "@axe-core/react": "^4.8.0"
  }
}
```

(Vitest + Playwright already present)
