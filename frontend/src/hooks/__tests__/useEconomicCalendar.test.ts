```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useEconomicCalendar } from '../useEconomicCalendar';
import { vi } from 'vitest';

describe('useEconomicCalendar', () => {
  beforeEach(() => {
    localStorage.setItem('auth_token', 'test_token');
    vi.clearAllMocks();
  });

  it('fetches upcoming events with default options', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          data: [
            {
              id: 1,
              event_name: 'NFP',
              country: 'US',
              category: 'employment',
              scheduled_datetime: new Date().toISOString(),
              impact_level: 'high',
            },
          ],
          meta: { total_count: 1, has_next: false },
        }),
      } as Response)
    );

    const { result } = renderHook(() => useEconomicCalendar());

    await waitFor(() => {
      expect(result.current.events.length).toBe(1);
    });

    expect(result.current.events[0].event_name).toBe('NFP');
  });

  it('applies filters correctly', async () => {
    global.fetch = vi.fn();

    renderHook(() =>
      useEconomicCalendar({
        country: 'US',
        category: 'employment',
        minImpact: 'high',
      })
    );

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('country=US'),
        expect.any(Object)
      );
    });
  });

  it('loads more events on demand', async () => {
    let callCount = 0;
    global.fetch = vi.fn(() => {
      callCount++;
      return Promise.resolve({
        ok: true,
        json: async () => ({
          data: Array.from({ length: 20 }, (_, i) => ({
            id: callCount === 1 ? i + 1 : i + 21,
            event_name: `Event ${callCount === 1 ? i + 1 : i + 21}`,
            country: 'US',
            category: 'employment',
            scheduled_datetime: new Date().toISOString(),
            impact_level: 'medium',
          })),
          meta: { total_count: 40, has_next: callCount === 1 },
        }),
      } as Response);
    });

    const { result } = renderHook(() => useEconomicCalendar());

    await waitFor(() => {
      expect(result.current.events.length).toBe(20);
    });

    result.current.loadMore();

    await waitFor(() => {
      expect(result.current.events.length).toBe(40);
    });
  });

  it('handles errors gracefully', async () => {
    global.fetch = vi.fn(() =>
      Promise.reject(new Error('API error'))
    );

    const { result } = renderHook(() => useEconomicCalendar());

    await waitFor(() => {
      expect(result.current.error).toBe('API error');
    });
  });
});
```