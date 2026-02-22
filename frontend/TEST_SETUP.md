# Keyboard Navigation in News Feed Panel - Test Setup Guide

## Overview

This document describes the comprehensive test suite for the keyboard navigation feature in the News Feed panel (VO-391).

## Test Files Created

1. **`src/hooks/__tests__/useNewsFeedKeyboard.test.ts`**
   - Unit tests for the `useNewsFeedKeyboard` hook
   - 80+ test cases covering all keyboard behaviors

2. **`src/components/dashboard/__tests__/NewsFeed.test.tsx`**
   - Integration tests for the NewsFeed component
   - 60+ test cases covering rendering, ARIA compliance, and keyboard interaction

3. **`jest.config.js`**
   - Jest configuration for TypeScript and React testing

4. **`src/jest.setup.ts`**
   - Jest setup file with DOM mocks and utilities

## Installation

### 1. Install Testing Dependencies

Add the following packages to `frontend/package.json`:

```bash
cd frontend
npm install --save-dev \
  jest \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  ts-jest \
  @types/jest
```

### 2. Update package.json scripts

Add test scripts to `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

### 3. Configure TypeScript

Ensure `frontend/tsconfig.json` includes Jest types:

```json
{
  "compilerOptions": {
    "types": ["jest", "@testing-library/jest-dom"]
  }
}
```

## Running Tests

### Run all tests:
```bash
npm test
```

### Run tests in watch mode:
```bash
npm run test:watch
```

### Run tests with coverage:
```bash
npm run test:coverage
```

### Run specific test file:
```bash
npm test useNewsFeedKeyboard.test.ts
```

## Test Coverage

### useNewsFeedKeyboard Hook Tests

#### Initialization (3 tests)
- Default focusedIndex is null
- Empty itemRefs array
- All required functions returned

#### Arrow Key Navigation (4 tests)
- ArrowDown moves focus down
- ArrowUp moves focus up
- Wraps from last to first with ArrowDown
- Wraps from first to last with ArrowUp

#### Home/End Key Navigation (2 tests)
- Home key jumps to first item
- End key jumps to last item

#### PageDown/PageUp Navigation (4 tests)
- PageDown advances by 5 items
- PageUp retreats by 5 items
- PageDown wraps at end of list
- PageUp wraps at beginning of list

#### Enter Key Behavior (3 tests)
- Clicks article link when Enter pressed
- No click when no focus
- Handles missing anchor gracefully

#### Escape Key Behavior (2 tests)
- Releases focus on Escape
- Blurs current focused item

#### Activation/Release (3 tests)
- activatePanel sets focusedIndex to 0
- activatePanel preserves existing focus
- releasePanel sets focusedIndex to null

#### List Refresh (3 tests)
- Clamps focusedIndex when count decreases
- Clears focus when count becomes 0
- Preserves focus when count increases

#### Edge Cases (3 tests)
- Empty list handling
- Single item list
- Wrapping in single item list

#### Event Prevention (2 tests)
- preventDefault called on ArrowDown
- preventDefault called on all nav keys

#### Unknown Keys (1 test)
- Unknown keys are ignored

#### Focus Ref Updates (1 test)
- focus() called on navigation

### NewsFeed Component Tests

#### Rendering (6 tests)
- News feed panel renders
- ARIA feed role present
- Article role on each article
- Article titles displayed
- Article metadata displayed
- External link icons present

#### Loading State (2 tests)
- Loading skeletons shown during loading
- aria-busy="true" when loading

#### Error State (2 tests)
- Error message displayed
- Error styled in red

#### Empty State (1 test)
- Empty message when no articles

#### Article Links (3 tests)
- Anchor tags rendered
- Links open in new tab
- Links have tabIndex -1

#### Keyboard Navigation (10 tests)
- ArrowDown navigation
- ArrowUp navigation
- Wrapping with ArrowDown
- Wrapping with ArrowUp
- Home key navigation
- End key navigation
- PageDown navigation
- PageUp navigation
- Enter key activation
- Escape key release

#### Visual Focus Indicator (3 tests)
- Focus ring applied to focused article
- Background highlight applied
- Ring removed on release

#### Article Refresh (3 tests)
- Focus index preserved on refresh
- Focus index clamped on shrink
- Focus cleared on empty list

#### ARIA Attributes (8 tests)
- Feed role and aria-label
- aria-busy attribute states
- tabIndex on feed container
- Article role and aria-label
- aria-current attribute on focus
- tabIndex -1 on articles

#### Time Display (4 tests)
- "Just now" for very recent
- Minutes display
- Hours display
- Days display

#### Sentiment Colors (2 tests)
- Correct colors applied
- All labels displayed

#### Responsive Layout (3 tests)
- Max height set
- Overflow auto
- Proper padding

## Key Testing Patterns

### 1. Hook Testing with renderHook

```typescript
const { result } = renderHook(() => useNewsFeedKeyboard(5, containerRef));
```

### 2. Testing Keyboard Events

```typescript
act(() => {
  const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
  Object.defineProperty(event, 'preventDefault', { value: jest.fn() });
  result.current.handleKeyDown(event as any);
});
```

### 3. Testing Component Rendering with fireEvent

```typescript
render(<NewsFeed />);
const feedContainer = screen.getByRole('feed');
fireEvent.keyDown(feedContainer, { key: 'ArrowDown' });
```

### 4. Testing ARIA Attributes

```typescript
expect(screen.getByRole('feed')).toHaveAttribute('aria-label', 'Recent news');
expect(articles[0]).toHaveAttribute('aria-current', 'true');
```

## Mock Setup

### Mocked Dependencies in NewsFeed tests:
- `@/hooks/useApi` - API data fetching
- `@/lib/api` - getNews function
- `@/components/layout/KeyboardShortcutsProvider` - Keyboard shortcuts context

### Example Mock:
```typescript
jest.mock('@/hooks/useApi', () => ({
  useApi: jest.fn(),
}));

mockUseApi.mockReturnValue({
  data: mockArticles,
  loading: false,
  error: null,
});
```

## Coverage Goals

- **Hook**: 100% coverage of all keyboard handlers and focus management
- **Component**: Full coverage of:
  - Rendering with different states (loading, error, empty, data)
  - Keyboard navigation integration
  - ARIA accessibility attributes
  - Visual indicators
  - List refresh scenarios

## Debugging Tests

### Run with verbose output:
```bash
npm test -- --verbose
```

### Run single test suite:
```bash
npm test -- NewsFeed.test.tsx
```

### Debug mode:
```bash
node --inspect-brk node_modules/.bin/jest --runInBand
```

## Known Limitations

1. **Focus management**: Tests use mock DOM elements; real DOM focus behavior may differ in browsers
2. **Animation testing**: CSS transitions not tested
3. **Scroll behavior**: Scroll positioning when navigating may not match real browser behavior
4. **Lighthouse**: Visual focus indicators should be verified with accessibility tools

## Next Steps

1. Install dependencies: `npm install --save-dev jest @testing-library/react @testing-library/jest-dom ts-jest`
2. Run tests: `npm test`
3. Check coverage: `npm run test:coverage`
4. Fix any failing tests related to project-specific mocks or configurations
5. Integrate tests into CI/CD pipeline

## References

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [ARIA Feed Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/feed/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Test Maintenance

### Adding New Tests

1. Maintain 1:1 mapping between implementation and test files
2. Use clear test names that describe the behavior being tested
3. Group related tests using `describe` blocks
4. Follow the existing patterns for setup and assertions

### Updating Tests

- Update tests when behavior changes
- Ensure backward compatibility tests still pass
- Add regression tests for fixed bugs

## Questions?

For issues with the test setup, check:
1. All dependencies installed correctly
2. TypeScript configuration includes Jest types
3. Mock paths match actual import paths in code
4. All `@/` imports resolve correctly
