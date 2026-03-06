/**
 * Type definitions for Earnings Calendar feature
 */

export interface EarningsRecord {
  id: number;
  ticker: string;
  earnings_date: string; // YYYY-MM-DD
  estimated_eps: number | null;
  actual_eps: number | null;
  estimated_revenue: number | null; // in billions
  actual_revenue: number | null; // in billions
  surprise_percent: number | null;
  fiscal_quarter: string | null; // Q1-Q4
  fiscal_year: number | null;
  status: 'upcoming' | 'reported';
}

export interface EarningsFilterParams {
  limit?: number;
  offset?: number;
  status?: 'upcoming' | 'reported';
  start_date?: string; // YYYY-MM-DD
  end_date?: string; // YYYY-MM-DD
  ticker?: string;
}

export interface EarningsPaginatedResponse {
  data: EarningsRecord[];
  meta: {
    total: number;
    limit: number;
    offset: number;
    has_next: boolean;
    has_previous: boolean;
  };
}

export interface EarningsSyncRequest {
  ticker?: string;
  force_refresh?: boolean;
}

export interface EarningsSyncResponse {
  success: boolean;
  message: string;
  count: number;
}

export interface EarningsDisplayRecord extends EarningsRecord {
  epsStatus?: 'beat' | 'miss' | 'neutral';
  revenueStatus?: 'beat' | 'miss' | 'neutral';
  isToday?: boolean;
  daysUntil?: number;
}