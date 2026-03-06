# Technical Design: Frontend Component Test Suite

**Date**: 2026-03-03
**Status**: Design Review
**Goal**: Increase test coverage from <5% to 80%+ on critical components (Dashboard, Research, Settings)

---

## Approach

**Two-Layer Testing Strategy**:
1. **Unit Tests (Vitest)**: Component rendering, hooks, business logic, isolated API mocking
2. **Integration Tests (Playwright)**: User workflows, navigation, toast notifications, API interactions

**Coverage Targets**:
- Settings Page: 85%+ (complex provider management + budget validation)
- Research Page: 80%+ (data loading, filtering, XSS sanitization)
- Dashboard (StockGrid): 80%+ (search, add/remove, keyboard navigation)
- Custom Hooks (useApi, useSSE): 90%+ (core request/streaming logic)

**Testing Principles**:
- Mock API layer (`@/lib/api.ts`) – test behavior, not HTTP
- Test user workflows, not implementation details
- Fixtures for consistent mock data (stocks, providers, briefs)
- Happy path + error cases + edge cases

---

## Files to Modify/Create

### Setup & Configuration
- `frontend/vitest.config.ts` **NEW** – Vitest configuration, resolver aliases (@/)
- `frontend/src/__tests__/setup.ts` **NEW** – Global test utilities, fetch mocks, cleanup
- `frontend/tsconfig.test.json` **NEW** – Test-specific TypeScript config (types: ['vitest/globals'])

### Test Files (Vitest Unit Tests)

#### Components
- `frontend/src/components/__tests__/KPICards.test.tsx` **NEW** – Mock ratings data, render states
- `frontend/src/components/__tests__/StockCard.test.tsx` **NEW** – Delete handler, rating display
- `frontend/src/components/__tests__/StockGrid.test.tsx` **NEW** – Search, add/remove, keyboard nav, error states
- `frontend/src/components/__tests__/PriceChart.test.tsx` **NEW** – Render checks (LightweightCharts library)
- `frontend/src/components/__tests__/ProviderCard.test.tsx` **NEW** – Save/test handlers, API key visibility toggle
- `frontend/src/components/__tests__/Header.test.tsx` **NEW** – Title/subtitle rendering
- `frontend/src/components/ui/__tests__/Toast.test.tsx` **NEW** – Toast queue, removal, context

#### Hooks
- `frontend/src/hooks/__tests__/useApi.test.ts` **NEW** – Loading, error, refetch, refresh interval, AbortController
- `frontend/src/hooks/__tests__/useSSE.test.ts` **NEW** – Connection lifecycle, message handling, cleanup

#### Pages (Server/Client)
- `frontend/src/app/__tests__/settings.test.tsx` **NEW** – Provider loading, budget validation, save flows
- `frontend/src/app/__tests__/research.test.tsx` **NEW** – Brief list, filter, generate, markdown sanitization
- `frontend/src/app/__tests__/dashboard.test.tsx` **NEW** – StockGrid integration, loading/error states

### E2E Integration Tests (Playwright)
- `e2e/dashboard.spec.ts` **NEW** – Search → Add → Remove → View ratings workflow
- `e2e/research.spec.ts` **NEW** – Filter → Generate → View brief (XSS payload test)
- `e2e/settings.spec.ts` **EXTEND** – Provider config → Test → Save → Health check display

### Test Utilities & Fixtures
- `frontend/src/__tests__/mocks/api.ts` **NEW** – Mock API functions, realistic responses
- `frontend/src/__tests__/fixtures/stocks.json` **NEW** – Sample stock data (AAPL, GOOGL, TSLA)
- `frontend/src/__tests__/fixtures/providers.json` **NEW** – Mock AI providers (OpenAI, Anthropic, Google, xAI)
- `frontend/src/__tests__/fixtures/briefs.json` **NEW** – Research brief templates

### Package & Configuration Updates
- `frontend/package.json` **MODIFY** – Add devDependencies: vitest, @vitest/ui, @testing-library/react, @testing-library/user-event, @testing-library/dom, jsdom, playwright

---

## Test Coverage Matrix

| Component | Happy Path | Error State | Edge Cases | Loading | Count |
|-----------|-----------|-----------|-----------|---------|-------|
| **ProviderCard** | Save, Test, API key visibility | Invalid key, API error, network timeout | No models, null values | Spinner states | 12 |
| **StockGrid** | Search, Add, Remove, Keyboard nav | Search error, Add fails, Network error | Empty results, Duplicate add | Loading skeleton | 15 |
| **StockCard** | Render rating, Delete button | Delete fails | Missing fields, null rating | N/A | 6 |
| **Settings Page** | Load providers, Save budget, Framework select | Validation errors, Load fails | Budget > daily, Negative values | Async states | 18 |
| **Research Page** | List briefs, Filter, Generate, Sanitize XSS | Load fails, Gen fails, Render error | Empty list, No briefs, Markdown edge cases | Async states | 16 |
| **Dashboard Page** | StockGrid integration, Rates refresh | API error cascade | Missing stocks | Full workflow | 8 |
| **useApi Hook** | Load, refetch, refresh interval | Error retry, AbortError | null data, component unmount | Signal cleanup | 14 |
| **useSSE Hook** | Open, message, close | Reconnect, Error message | Null events, cleanup on unmount | State transitions | 10 |
| **Toast Component** | Show, Auto-remove, Remove button | Multiple stacked | Clear all, Long text | Position/timing | 8 |

**Total Tests**: ~100+ unit tests + 5+ integration suites

---

## Data Model & Fixtures

### Mock API Response Shape
```typescript
// Stock data
{ ticker: 'AAPL', name: 'Apple Inc.', rating: 8, trend: 'bullish' }

// AI Provider
{ name: 'openai', display_name: 'OpenAI', configured: true, default_model: 'gpt-4', models: [...] }

// Research Brief
{ id: '1', ticker: 'AAPL', title: '...', content: '...' (markdown), created_at, agent_name }

// Budget
{ monthly_budget: 50, daily_warning: 5 }
```

---

## Testing Strategy

### Unit Tests (Vitest + Testing Library)

**ProviderCard Example**:
```typescript
describe('ProviderCard', () => {
  test('renders provider name and status', () => {
    const provider = { name: 'openai', configured: true, ... };
    render(<ProviderCard provider={provider} onSave={vi.fn()} />);
    expect(screen.getByText('OpenAI')).toBeInTheDocument();
    expect(screen.getByText('Configured')).toBeInTheDocument();
  });

  test('disables save button when API key is empty', async () => {
    render(<ProviderCard provider={mockProvider} onSave={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Save/ })).toBeDisabled();
  });

  test('calls onSave with correct arguments when save clicked', async () => {
    const onSave = vi.fn();
    render(<ProviderCard provider={mockProvider} onSave={onSave} />);
    await userEvent.type(screen.getByPlaceholderText(/API key/), 'sk-1234');
    await userEvent.click(screen.getByRole('button', { name: /Save/ }));
    expect(onSave).toHaveBeenCalledWith('openai', 'sk-1234', expect.any(String));
  });

  test('shows error toast on API save failure', async () => {
    const onSave = vi.fn().mockRejectedValue(new Error('API error'));
    render(<ProviderCard provider={mockProvider} onSave={onSave} onError={vi.fn()} />);
    // ... trigger save
    // await waitFor(() => expect(onError).toHaveBeenCalled());
  });
});
```

### E2E Tests (Playwright)

**Dashboard Workflow Example**:
```typescript
test('user can search, add, and view stock', async ({ page }) => {
  await page.goto('/');
  await page.fill('input[placeholder="Search stocks"]', 'AAPL');
  await page.waitForSelector('button:has-text("AAPL")');
  await page.click('button:has-text("AAPL")');
  await page.waitForSelector('[data-ticker="AAPL"]'); // StockCard appears
  expect(await page.locator('[data-ticker="AAPL"]').count()).toBe(1);
});
```

---

## Implementation Order

1. **Phase 1** (Setup): vitest.config.ts, test setup, fixtures, mocks
2. **Phase 2** (Hooks): useApi, useSSE hooks tests (foundation for components)
3. **Phase 3** (UI Components): Toast, Header, PriceChart (simple, no API)
4. **Phase 4** (Complex Components): StockCard, StockGrid, ProviderCard (with API mocks)
5. **Phase 5** (Pages): Settings, Research, Dashboard (integration tests)
6. **Phase 6** (E2E): Playwright workflows, XSS injection tests
7. **Phase 7** (Coverage Report): Generate coverage.html, identify gaps

---

## Success Criteria

- ✅ All 100+ unit tests pass (0% flakiness)
- ✅ All E2E tests pass on ci environment
- ✅ Coverage: Settings 85%+, Research 80%+, Dashboard 80%+, Hooks 90%+
- ✅ API mocks are realistic (match actual responses)
- ✅ No snapshot tests (tests behavior, not HTML strings)
- ✅ Tests document expected behavior (readable, not brittle)
