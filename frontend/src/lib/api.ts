```typescript
// Add to existing api.ts file

import { PriceAlert, PriceAlertsListResponse } from './types';

// Price Alerts API
export async function getPriceAlerts(
  limit = 20,
  offset = 0,
  ticker?: string,
  activeOnly = false,
): Promise<PriceAlertsListResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  if (ticker) params.append('ticker', ticker);
  if (activeOnly) params.append('active_only', 'true');

  return request(`/price-alerts?${params.toString()}`);
}

export async function getPriceAlert(id: number): Promise<PriceAlert> {
  return request(`/price-alerts/${id}`);
}

export async function createPriceAlert(
  ticker: string,
  alertType: string,
  threshold: number,
): Promise<PriceAlert> {
  return request('/price-alerts', {
    method: 'POST',
    body: JSON.stringify({
      ticker,
      alert_type: alertType,
      threshold,
    }),
  });
}

export async function updatePriceAlert(
  id: number,
  threshold?: number,
  isActive?: boolean,
): Promise<PriceAlert> {
  return request(`/price-alerts/${id}`, {
    method: 'PUT',
    body: JSON.stringify({
      ...(threshold !== undefined && { threshold }),
      ...(isActive !== undefined && { is_active: isActive }),
    }),
  });
}

export async function deletePriceAlert(id: number): Promise<void> {
  await request(`/price-alerts/${id}`, {
    method: 'DELETE',
  });
}
```