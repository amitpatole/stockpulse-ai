```typescript
// Add to existing types file

export interface PriceAlert {
  id: number;
  ticker: string;
  alert_type: 'above' | 'below' | 'change_percent_up' | 'change_percent_down';
  threshold: number;
  is_active: boolean;
  triggered_count: number;
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PriceAlertTriggerEvent {
  alert_id: number;
  ticker: string;
  alert_type: string;
  threshold: number;
  current_price: number;
  timestamp: string;
}

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PriceAlertsListResponse {
  alerts: PriceAlert[];
  meta: PaginationMeta;
}
```