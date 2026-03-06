# Technical Implementation Spec: WCAG 2.1 Level AA Accessibility

**Goal**: Close 40% compliance gap via ARIA labels, keyboard navigation, and semantic HTML.
**Scope**: Frontend only (no DB/API changes).
**Target**: Zero critical/serious axe-core violations.

---

## Approach

### Phase 1: Component Retrofitting (Priority Order)
1. **Layout Components** (Header, Sidebar) - Affects all pages
   - Add semantic HTML (`<nav>`, `<main>`)
   - Skip link to main content
   - ARIA labels on icon buttons (Bell → "View alerts")

2. **Interactive Elements** (Forms, Buttons, Inputs)
   - Wrap form inputs with `<label>`
   - Add `aria-expanded`, `aria-selected` to toggle/select components
   - Toast messages: `role="alert"` + `aria-live="polite"`

3. **Tables/Grids** (Stock Grid, Search Results)
   - If grid used as table, add semantic roles (`role="table"`, `role="row"`, `role="cell"`)
   - Add column headers with scope

4. **Focus & Keyboard Navigation**
   - Focus trap in modals (using `trapFocus` utility from `a11y.ts`)
   - Tab order follows visual flow
   - Return focus to trigger after modal close

### Phase 2: Testing & Validation
- Vitest: ARIA attributes + keyboard event handling
- Playwright E2E: Full keyboard navigation flow
- axe-core: Automated scanning on CI/CD

---

## Files to Modify/Create

### Frontend Components (Modify)
```
frontend/src/components/layout/Sidebar.tsx       → Add <nav>, skip link, aria-labels
frontend/src/components/layout/Header.tsx        → Icon buttons: aria-label, role="button"
frontend/src/components/ui/Toast.tsx            → role="alert", aria-live="polite"
frontend/src/components/dashboard/StockCard.tsx → Heading hierarchy, data roles
frontend/src/components/dashboard/StockGrid.tsx → Table semantics if grid layout
frontend/src/app/settings/page.tsx              → Form labels, required/invalid states
frontend/src/app/layout.tsx                     → Root <main id="main"> landmark
```

### Utilities (Already Created)
```
frontend/src/lib/a11y.ts                        → Focus management, ARIA helpers ✅
frontend/src/hooks/useAccessibility.ts          → Custom hook for keyboard/focus events
```

### Tests (Create)
```
frontend/src/__tests__/accessibility.test.tsx   → ARIA attributes, heading hierarchy
e2e/accessibility.spec.ts                       → Keyboard navigation flow, form submission
e2e/axe-accessibility.spec.ts                   → axe-core scanning per route
```

### Styles (Add)
```
frontend/src/styles/accessibility.css           → .sr-only, :focus-visible overrides
```

---

## Implementation Details

### Sidebar Navigation
```tsx
<nav aria-label="Main navigation">
  <button aria-label="Toggle sidebar" aria-expanded={isOpen} onClick={toggle} />
  <ul role="list">
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>
```

### Form Inputs
```tsx
<label htmlFor="symbol">Stock Symbol</label>
<input id="symbol" type="text" aria-required="true" />
```

### Icon Buttons
```tsx
<button aria-label="View alerts" className="bell-icon">
  🔔 {unreadCount > 0 && <span aria-label={`${unreadCount} unread`}>{unreadCount}</span>}
</button>
```

### Toast Messages
```tsx
<div role="alert" aria-live="polite" aria-atomic="true" className="toast">
  Settings saved successfully
</div>
```

---

## Testing Strategy

### Vitest Unit Tests
- **ARIA attributes**: Verify `aria-label`, `aria-expanded`, `role` on interactive elements
- **Heading hierarchy**: Validate H1→H2→H3 flow (no skips)
- **Keyboard handling**: Test button clicks with Enter/Space, list navigation with Arrow keys
- **Focus management**: Focus visible, correct tab order, trap/release in modals

**Example**:
```typescript
it('should have aria-label on alert button', () => {
  const button = screen.getByRole('button', { name: /view alerts/i });
  expect(button).toHaveAttribute('aria-label', 'View alerts');
});

it('should trap focus in modal', () => {
  // Open modal, Tab on last element → Focus first element
});
```

### Playwright E2E Tests
- **Keyboard-only navigation**: Tab through entire page, verify visual focus matches semantics
- **Form completion**: Fill & submit settings form using Tab, typing, Enter
- **Landmark roles**: Verify `<nav>`, `<main>`, `<footer>` present via accessibility tree
- **Skip link**: Focus first (hidden), click/Enter → Jump to main content

**Example**:
```typescript
test('keyboard navigation follows visual flow', async ({ page }) => {
  await page.goto('/dashboard');
  await page.keyboard.press('Tab'); // Skip link visible
  await page.keyboard.press('Tab'); // Sidebar toggle focused
  // ... verify order
});
```

### axe-core Automated Scanning
- Run on all routes (dashboard, settings, research, agents)
- Assert zero `critical` or `serious` violations
- Flag `moderate` and `minor` for manual review
- Integrate into CI/CD pipeline

**Example**:
```typescript
test('dashboard meets WCAG AA', async ({ page }) => {
  const violations = await analyzeAccessibility(page);
  expect(violations.critical).toBe(0);
  expect(violations.serious).toBe(0);
});
```

---

## Dependencies

**Already in package.json** (from memory):
- `vitest ^2.1.0` ✅
- `@testing-library/react ^16.0.0` ✅
- `@playwright/test ^1.48.0` ✅

**To Add**:
```json
{
  "devDependencies": {
    "@axe-core/playwright": "^4.8.0",
    "@axe-core/react": "^4.8.0"
  }
}
```

---

## Success Criteria
- ✅ All interactive elements keyboard-navigable (Tab, Enter, Escape, Arrow keys)
- ✅ All buttons/icon-only elements have accessible names (aria-label or text)
- ✅ Proper heading hierarchy (H1 → H2 → H3, no skips)
- ✅ Modals trap focus, return focus on close
- ✅ axe-core: Zero critical/serious violations on all routes
- ✅ Vitest: 95%+ coverage on a11y-related logic
- ✅ Playwright: Full page keyboard navigation test passes
- ✅ CI/CD: axe-core scan runs automatically, blocks merge on violations
