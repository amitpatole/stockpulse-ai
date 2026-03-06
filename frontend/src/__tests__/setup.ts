/**
 * Test Setup: MSW Server Configuration
 *
 * Configures Mock Service Worker (MSW) for API mocking across all tests.
 * Provides utilities for test components to use.
 */

import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { afterEach, afterAll, beforeAll, vi } from 'vitest';
import '@testing-library/jest-dom';

/**
 * API Mock Handlers
 *
 * Default handlers for common endpoints. Tests can override specific handlers
 * using server.use() to test different scenarios.
 */
export const handlers = [
  // Stocks / Ratings
  http.get('http://localhost:8000/api/ratings', () => {
    return HttpResponse.json({
      data: [
        {
          ticker: 'AAPL',
          current_price: 150.25,
          price_change_pct: 2.5,
          rating: 'buy',
          confidence: 0.85,
          sentiment_score: 0.45,
          rsi: 55,
          score: 7.5,
        },
        {
          ticker: 'GOOGL',
          current_price: 145.75,
          price_change_pct: -1.2,
          rating: 'hold',
          confidence: 0.72,
          sentiment_score: 0.1,
          rsi: 45,
          score: 6.8,
        },
      ],
      meta: { count: 2 },
    });
  }),

  http.get('http://localhost:8000/api/stocks', () => {
    return HttpResponse.json({
      data: [
        { ticker: 'AAPL', name: 'Apple Inc.', active: true },
        { ticker: 'GOOGL', name: 'Alphabet Inc.', active: true },
      ],
      meta: { count: 2 },
    });
  }),

  http.post('http://localhost:8000/api/stocks', async ({ request }) => {
    const body = await request.json() as { ticker?: string; name?: string };
    return HttpResponse.json(
      { data: { ticker: body.ticker, name: body.name, active: true } },
      { status: 201 }
    );
  }),

  http.delete('http://localhost:8000/api/stocks/:ticker', () => {
    return HttpResponse.json({ data: { success: true } });
  }),

  // Search
  http.get('http://localhost:8000/api/search/stocks', ({ request }) => {
    const url = new URL(request.url);
    const query = url.searchParams.get('query') || '';

    const results = [
      {
        ticker: 'AAPL',
        name: 'Apple Inc.',
        exchange: 'NASDAQ',
        type: 'stock',
      },
      {
        ticker: 'MSFT',
        name: 'Microsoft Corporation',
        exchange: 'NASDAQ',
        type: 'stock',
      },
    ].filter((r) => r.ticker.includes(query.toUpperCase()));

    return HttpResponse.json({ data: results, meta: { count: results.length } });
  }),

  // Alerts
  http.get('http://localhost:8000/api/alerts', () => {
    return HttpResponse.json({
      data: [
        { id: '1', ticker: 'AAPL', type: 'price_breach', triggered_at: new Date().toISOString() },
      ],
      meta: { count: 1 },
    });
  }),

  // Agents
  http.get('http://localhost:8000/api/agents', () => {
    return HttpResponse.json({
      data: [
        { id: '1', name: 'Market Regime Agent', status: 'running' },
        { id: '2', name: 'Sentiment Agent', status: 'idle' },
      ],
      meta: { count: 2 },
    });
  }),

  // Settings / Projects
  http.get('http://localhost:8000/api/projects/:id', ({ params }) => {
    return HttpResponse.json({
      data: {
        id: params.id,
        name: 'Default Project',
        description: 'Main trading project',
        ai_provider: 'openai',
        ai_model: 'gpt-4',
        daily_budget: 50,
        monthly_budget: 1000,
      },
    });
  }),

  http.put('http://localhost:8000/api/projects/:id', () => {
    return HttpResponse.json({
      data: {
        id: '1',
        name: 'Updated Project',
        description: 'Updated description',
        ai_provider: 'openai',
        ai_model: 'gpt-4',
        daily_budget: 50,
        monthly_budget: 1000,
      },
    });
  }),

  http.get('http://localhost:8000/api/projects/:id/health', () => {
    return HttpResponse.json({
      data: {
        status: 'healthy',
        api_connected: true,
        budget_remaining: 75.5,
        last_check: new Date().toISOString(),
      },
    });
  }),

  // Research / Briefs
  http.get('http://localhost:8000/api/research/briefs', ({ request }) => {
    const url = new URL(request.url);
    const ticker = url.searchParams.get('ticker') || '';

    return HttpResponse.json({
      data: [
        {
          id: '1',
          ticker: ticker || 'AAPL',
          title: 'Market Analysis Brief',
          content: '# Apple Inc. Analysis\n\nApple shows strong fundamentals...',
          generated_at: new Date().toISOString(),
        },
      ],
      meta: { count: 1 },
    });
  }),

  http.post('http://localhost:8000/api/research/briefs', () => {
    return HttpResponse.json(
      {
        data: {
          id: 'new-brief',
          ticker: 'AAPL',
          title: 'New Market Analysis',
          content: '# Generated Brief\n\nContent here...',
          generated_at: new Date().toISOString(),
        },
      },
      { status: 201 }
    );
  }),

  // Auth
  http.post('http://localhost:8000/api/auth/login', () => {
    return HttpResponse.json({
      data: {
        token: 'test-token-123',
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
      },
    });
  }),

  http.post('http://localhost:8000/api/auth/logout', () => {
    return HttpResponse.json({ data: { success: true } });
  }),

  http.get('http://localhost:8000/api/auth/me', () => {
    return HttpResponse.json({
      data: { id: '1', email: 'test@example.com', name: 'Test User' },
    });
  }),
];

/**
 * MSW Server Instance
 *
 * Established before all tests, cleaned up after.
 */
export const server = setupServer(...handlers);

// Start server before all tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'error',
  });
});

// Reset handlers after each test (allows per-test overrides)
afterEach(() => {
  server.resetHandlers();
});

// Cleanup after all tests
afterAll(() => {
  server.close();
});

/**
 * Test Utilities
 */

/**
 * Mock data generators for consistent test data
 */
export const mockData = {
  stock: (overrides = {}) => ({
    ticker: 'AAPL',
    name: 'Apple Inc.',
    active: true,
    ...overrides,
  }),

  rating: (overrides = {}) => ({
    ticker: 'AAPL',
    current_price: 150.25,
    price_change_pct: 2.5,
    rating: 'buy' as const,
    confidence: 0.85,
    sentiment_score: 0.45,
    rsi: 55,
    score: 7.5,
    ...overrides,
  }),

  alert: (overrides = {}) => ({
    id: '1',
    ticker: 'AAPL',
    type: 'price_breach',
    triggered_at: new Date().toISOString(),
    ...overrides,
  }),

  agent: (overrides = {}) => ({
    id: '1',
    name: 'Test Agent',
    status: 'running' as const,
    ...overrides,
  }),

  project: (overrides = {}) => ({
    id: '1',
    name: 'Test Project',
    description: 'Test Description',
    ai_provider: 'openai',
    ai_model: 'gpt-4',
    daily_budget: 50,
    monthly_budget: 1000,
    ...overrides,
  }),

  brief: (overrides = {}) => ({
    id: '1',
    ticker: 'AAPL',
    title: 'Test Brief',
    content: '# Test Content',
    generated_at: new Date().toISOString(),
    ...overrides,
  }),
};

/**
 * Wait for async state updates in tests
 * Useful for testing useApi hooks and async effects
 */
export const waitForAsync = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Mock localStorage for settings persistence tests
 */
export const setupLocalStorageMock = () => {
  const store: Record<string, string> = {};

  Object.defineProperty(window, 'localStorage', {
    value: {
      getItem: (key: string) => store[key] || null,
      setItem: (key: string, value: string) => {
        store[key] = value.toString();
      },
      removeItem: (key: string) => {
        delete store[key];
      },
      clear: () => {
        Object.keys(store).forEach((key) => delete store[key]);
      },
    },
  });

  return store;
};

// Setup localStorage by default
setupLocalStorageMock();

// Suppress console errors in tests (can be enabled per-test if needed)
const originalError = console.error;
beforeAll(() => {
  console.error = vi.fn((...args: unknown[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render')
    ) {
      return;
    }
    originalError.call(console, ...args);
  });
});

afterAll(() => {
  console.error = originalError;
});
