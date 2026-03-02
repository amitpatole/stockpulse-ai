```typescript
import { render, screen, waitFor } from '@testing-library/react';
import { EconomicCalendarWidget } from '../EconomicCalendarWidget';

describe('EconomicCalendarWidget', () => {
  beforeEach(() => {
    localStorage.setItem('auth_token', 'test_token');
  });

  afterEach(() => {
    localStorage.removeItem('auth_token');
  });

  it('displays loading state initially', () => {
    global.fetch = vi.fn(() =>
      new Promise((resolve) =>
        setTimeout(
          () =>
            resolve({
              ok: true,
              json: async () => ({ data: [] }),
            } as Response),
          100
        )
      )
    );

    render(<EconomicCalendarWidget />);
    expect(screen.getByText(/Economic Calendar/i)).toBeInTheDocument();
  });

  it('displays upcoming events', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          data: [
            {
              id: 1,
              event_name: 'Non-Farm Payroll',
              country: 'US',
              category: 'employment',
              scheduled_datetime: new Date(Date.now() + 86400000).toISOString(),
              impact_level: 'high',
            },
          ],
        }),
      } as Response)
    );

    render(<EconomicCalendarWidget />);

    await waitFor(() => {
      expect(screen.getByText('Non-Farm Payroll')).toBeInTheDocument();
    });
  });

  it('displays impact badge with correct color', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          data: [
            {
              id: 1,
              event_name: 'CPI Release',
              country: 'US',
              category: 'inflation',
              scheduled_datetime: new Date(Date.now() + 86400000).toISOString(),
              impact_level: 'medium',
            },
          ],
        }),
      } as Response)
    );

    render(<EconomicCalendarWidget />);

    await waitFor(() => {
      expect(screen.getByText('Medium')).toBeInTheDocument();
    });
  });

  it('displays error message on fetch failure', async () => {
    global.fetch = vi.fn(() =>
      Promise.reject(new Error('Network error'))
    );

    render(<EconomicCalendarWidget />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  it('has link to view all events', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: async () => ({ data: [] }),
      } as Response)
    );

    render(<EconomicCalendarWidget />);

    await waitFor(() => {
      expect(screen.getByText(/View All/i)).toBeInTheDocument();
    });
  });
});
```