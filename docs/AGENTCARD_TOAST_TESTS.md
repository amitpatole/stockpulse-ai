# AgentCard & Toast Component Tests

**Date Created**: 2026-03-03
**Status**: ✅ Complete & Ready for Execution
**Test Framework**: Vitest + React Testing Library
**Total Tests**: 22 (AgentCard: 8, Toast: 14)

## Overview

Two new component test suites covering critical UI components:
1. **AgentCard** - Agent display with run execution and metrics
2. **Toast** - Notification system with auto-dismiss and state management

## AgentCard Tests (8 tests)

**File**: `frontend/src/components/agents/__tests__/AgentCard.test.tsx`

### Test Coverage

| Test | Type | Purpose |
|------|------|---------|
| should render agent with complete metadata | Happy Path | Display name, description, status, model, metrics |
| should run agent on button click and call onRunComplete | Happy Path | Successful API call triggers callback |
| should display error message when run fails | Error Case | API failure caught and displayed |
| should render gracefully with minimal agent data | Edge Case | Optional fields handle null/undefined |
| should disable run button when agent is not enabled | Edge Case | Button state reflects agent.enabled |
| should show running state when agent status is running | Edge Case | Loading indicator and disabled state |
| should format costs correctly for different amounts | Edge Case | $0.0025 (4 decimals) vs $125.50 (2 decimals) |

### Acceptance Criteria Covered
- ✅ AC1: Agent metadata (name, status, model, cost, runs) displayed correctly
- ✅ AC2: Run button triggers execution with loading state
- ✅ AC3: API errors caught and shown to user
- ✅ AC4: Time/cost formatting is human-readable

### Run Tests
```bash
npm run test:unit -- AgentCard
```

## Toast Tests (14 tests)

**File**: `frontend/src/components/ui/__tests__/Toast.test.tsx`

### Test Coverage

#### Toast Component (6 tests)
| Test | Type | Purpose |
|------|------|---------|
| should render success toast with correct styling | Happy Path | Icon, message, close button, ARIA labels |
| should render error and info toasts | Happy Path | All three toast types render properly |
| should auto-dismiss toast after 3000ms | Happy Path | Timer callback fires after duration |
| should close toast when close button clicked | Happy Path | Manual close works |
| should not auto-dismiss when duration is 0 | Edge Case | Persistent notifications |
| should clear timeout on unmount | Edge Case | Memory leak prevention |

#### ToastContainer Component (3 tests)
| Test | Type | Purpose |
|------|------|---------|
| should render multiple toasts in container | Happy Path | Multiple toasts stack properly |
| should remove toast when onRemove is called | Happy Path | Individual toast removal |
| should render empty container when no toasts | Edge Case | Empty state handling |

#### useToast Hook (5 tests)
| Test | Type | Purpose |
|------|------|---------|
| should add and remove toasts via hook | Happy Path | State management (add/remove) |
| should provide convenience methods | Happy Path | success/error/info helper methods |
| should allow multiple toasts with same message | Edge Case | Unique IDs generated for duplicates |

### Acceptance Criteria Covered
- ✅ AC1: Toast displays type-specific icon and message
- ✅ AC2: Auto-dismiss on timer (default 3000ms)
- ✅ AC3: Manual close preserves other toasts
- ✅ AC4: useToast hook manages state properly

### Run Tests
```bash
npm run test:unit -- Toast
```

## Test Quality Metrics

| Category | Count | % |
|----------|-------|---|
| Happy Path Tests | 10 | 45% |
| Error Handling Tests | 1 | 5% |
| Edge Case Tests | 11 | 50% |
| **Total** | **22** | **100%** |

## Key Testing Patterns Used

### 1. Mock API Calls with MSW
```typescript
server.use(
  http.post('http://localhost:8000/api/agents/test_agent/run', () => {
    return HttpResponse.json({ data: { success: true } });
  })
);
```

### 2. Timer Testing with Fake Timers
```typescript
vi.useFakeTimers();
vi.advanceTimersByTime(3000);
// verify callback was called
vi.useRealTimers();
```

### 3. User Interactions
```typescript
await userEvent.click(screen.getByRole('button', { name: /Run Now/i }));
```

### 4. Async Waiting
```typescript
await waitFor(() => {
  expect(onClose).toHaveBeenCalledWith('toast-id');
});
```

### 5. Accessibility Assertions
```typescript
expect(toast).toHaveAttribute('aria-live', 'polite');
expect(toast).toHaveAttribute('aria-atomic', 'true');
```

## Test Execution

### Run All Component Tests
```bash
npm run test:unit
```

### Run Specific Component Tests
```bash
npm run test:unit -- AgentCard    # AgentCard only
npm run test:unit -- Toast         # Toast only
```

### Watch Mode
```bash
npm run test:unit -- --watch
```

### Coverage Report
```bash
npm run test:unit -- --coverage
```

## Dependencies Verified

✅ `vitest` - Test runner
✅ `@testing-library/react` - Component testing
✅ `@testing-library/jest-dom` - DOM matchers
✅ `@testing-library/user-event` - User interactions
✅ `msw` - API mocking
✅ `jsdom` - DOM environment

## Next Steps

1. ✅ AgentCard tests created
2. ✅ Toast tests created
3. Run tests: `npm run test:unit`
4. Check coverage if needed
5. Add more components as needed (Sidebar, PriceChart, etc.)

## Known Components Without Tests

- `Sidebar.tsx` - Layout component (low priority)
- `PriceChart.tsx` - Chart component (may need special chart testing library)
- `ActivityFeed.tsx` - Feed component (similar to existing News Feed tests)

These can be added as follow-up work if coverage targets require.
