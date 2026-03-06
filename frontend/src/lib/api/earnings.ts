```typescript
/**
 * API helpers for Earnings Calendar endpoints
 */

import { EarningsFilterParams, EarningsPaginatedResponse, EarningsSyncRequest, EarningsSyncResponse } from '@/types/earnings';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

/**
 * Get paginated earnings records with optional filters
 */
export async function getEarnings(params: EarningsFilterParams = {}): Promise<EarningsPaginatedResponse> {
  const queryParams = new URLSearchParams();

  if (params.limit) queryParams.append('limit', params.limit.toString());
  if (params.offset) queryParams.append('offset', params.offset.toString());
  if (params.status) queryParams.append('status', params.status);
  if (params.start_date) queryParams.append('start_date', params.start_date);
  if (params.end_date) queryParams.append('end_date', params.end_date);
  if (params.ticker) queryParams.append('ticker', params.ticker);

  const url = `${API_BASE}/earnings?${queryParams.toString()}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to fetch earnings');
  }

  return response.json();
}

/**
 * Get earnings history for a specific ticker
 */
export async function getEarningsByTicker(
  ticker: string,
  limit: number = 25,
  offset: number = 0
): Promise<EarningsPaginatedResponse> {
  const queryParams = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const url = `${API_BASE}/earnings/${ticker.toUpperCase()}?${queryParams.toString()}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || `Failed to fetch earnings for ${ticker}`);
  }

  return response.json();
}

/**
 * Sync earnings data from external source
 */
export async function syncEarnings(request: EarningsSyncRequest = {}): Promise<EarningsSyncResponse> {
  const url = `${API_BASE}/earnings/sync`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to sync earnings');
  }

  return response.json();
}

/**
 * Calculate EPS surprise percentage
 */
export function calculateEPSSurprise(estimated: number | null, actual: number | null): number | null {
  if (estimated === null || actual === null || estimated === 0) return null;
  return ((actual - estimated) / estimated) * 100;
}

/**
 * Determine if EPS beat, missed, or was neutral
 */
export function getEPSStatus(surprise: number | null): 'beat' | 'miss' | 'neutral' | null {
  if (surprise === null) return null;
  if (surprise > 0.5) return 'beat';
  if (surprise < -0.5) return 'miss';
  return 'neutral';
}

/**
 * Format earnings date as display string
 */
export function formatEarningsDate(dateStr: string, today: Date = new Date()): string {
  const date = new Date(dateStr);
  const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const earningsDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

  if (earningsDate.getTime() === todayDate.getTime()) {
    return 'Today';
  }

  const diffTime = earningsDate.getTime() - todayDate.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays > 0 && diffDays <= 7) {
    return `In ${diffDays} days`;
  }

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
```