# Feature: API Rate Limit Dashboard

## Overview

The API Rate Limit Dashboard provides real-time visibility into API usage, rate limits, and quotas across all data providers (CoinGecko, TradingView, SEC, etc.). Users can monitor current consumption, historical trends, and receive alerts when approaching rate limit thresholds (80%+).

## Data Model

### Database Tables

**`api_rate_limits`**
```
- id: INTEGER PRIMARY KEY
- provider_name: TEXT UNIQUE (CoinGecko, TradingView, SEC, etc.)
- limit_value: INTEGER (calls per reset period)
- reset_time: TIMESTAMP (when the limit resets)
- alert_threshold: INTEGER (default 80, warning at this percentage)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

**`api_usage_logs`**
```
- id: INTEGER PRIMARY KEY
- provider_name: TEXT FOREIGN KEY → api_rate_limits.provider_name
- endpoint: TEXT (e.g., '/quote', '/search', '/form4')
- timestamp: TIMESTAMP (when the call was made)
- status_code: INTEGER (200, 429, 500, etc.)
- response_time_ms: INTEGER
- created_at: TIMESTAMP (auto-indexed for efficient range queries)
```

Indexes:
- `api_rate_limits(provider_name)` - UNIQUE
- `api_usage_logs(provider_name, created_at)` - For efficient historical queries
- `api_usage_logs(created_at)` - For cleanup/archival queries

### Sample Data

```sql
INSERT INTO api_rate_limits (provider_name, limit_value, reset_time, alert_threshold)
VALUES 
  ('CoinGecko', 50, '2026-03-02T12:00:00Z', 80),
  ('TradingView', 3000, '2026-03-02T23:59:59Z', 80),
  ('SEC', 10, '2026-03-02T16:00:00Z', 85);

INSERT INTO api_usage_logs (provider_name, endpoint, status_code, response_time_ms)
VALUES
  ('CoinGecko', '/quote', 200, 145),
  ('CoinGecko', '/search', 200, 98),
  ('TradingView', '/quote', 200, 230),
  ('SEC', '/form4', 200, 890);
```

## API Endpoints

### GET /api/rate-limits

Returns current usage and status for all configured providers.

**Request**
```bash
curl -X GET http://localhost:8000/api/rate-limits \
  -H "Content-Type: application/json"
```

**Response (200 OK)**
```json
{
  "data": [
    {
      "provider": "CoinGecko",
      "limit_value": 50,
      "current_usage": 42,
      "usage_pct": 84.0,
      "reset_in_seconds": 3600,
      "status": "warning"
    },
    {
      "provider": "TradingView",
      "limit_value": 3000,
      "current_usage": 1200,
      "usage_pct": 40.0,
      "reset_in_seconds": 86400,
      "status": "healthy"
    },
    {
      "provider": "SEC",
      "limit_value": 10,
      "current_usage": 9,
      "usage_pct": 90.0,
      "reset_in_seconds": 28800,
      "status": "critical"
    }
  ],
  "meta": {
    "total_providers": 3,
    "timestamp": "2026-03-02T10:30:00Z"
  }
}
```

**Status Values**:
- `healthy`: usage_pct < 80%
- `warning`: 80% ≤ usage_pct < 95%
- `critical`: usage_pct ≥ 95%

### GET /api/rate-limits/{provider}/history

Returns historical usage data for a specific provider.

**Request**
```bash
curl -X GET "http://localhost:8000/api/rate-limits/CoinGecko/history?hours=24&interval=hourly" \
  -H "Content-Type: application/json"
```

**Query Parameters**
- `hours`: Number of hours to retrieve (default: 24, max: 720)
- `interval`: Aggregation level - `hourly`, `daily` (default: hourly)

**Response (200 OK)**
```json
{
  "data": [
    {
      "timestamp": "2026-03-02T09:00:00Z",
      "usage_pct": 25.0,
      "call_count": 12,
      "errors": 0
    },
    {
      "timestamp": "2026-03-02T10:00:00Z",
      "usage_pct": 38.0,
      "call_count": 19,
      "errors": 1
    },
    {
      "timestamp": "2026-03-02T11:00:00Z",
      "usage_pct": 48.0,
      "call_count": 24,
      "errors": 0
    }
  ],
  "meta": {
    "provider": "CoinGecko",
    "oldest_timestamp": "2026-03-02T09:00:00Z",
    "newest_timestamp": "2026-03-02T11:00:00Z",
    "total_calls": 55,
    "total_errors": 1
  }
}
```

**Error Response (400 Bad Request)**
```json
{
  "data": null,
  "meta": null,
  "errors": [
    {
      "code": "invalid_hours",
      "message": "hours must be between 1 and 720"
    }
  ]
}
```

## Dashboard/UI Elements

### Pages

**Route**: `/api-rate-limits`

Layout:
1. **Header** - Title "API Rate Limits" with refresh button
2. **Provider Grid** - 3-4 column responsive grid showing provider cards
3. **Time Series Chart** - Line chart showing last 24h usage trend across all providers
4. **Details Section** - Click provider card to expand detailed history

### Components

**RateLimitGauge**
```
Props:
  - provider: string
  - usage_pct: number (0-100)
  - limit: number
  - current_usage: number
  - status: 'healthy' | 'warning' | 'critical'

Renders: Circular progress gauge with:
  - Center text showing usage %
  - Color-coded background: green (healthy), yellow (warning), red (critical)
  - Label with provider name and reset time
```

**UsageTimeSeries**
```
Props:
  - provider: string
  - data: Array<{timestamp, usage_pct, call_count}>
  - hours: number (24, 48, 72, etc.)
  - interval: 'hourly' | 'daily'

Renders: Line chart with:
  - X-axis: Time (last N hours)
  - Y-axis: Usage percentage (0-100)
  - Color-coded zones: green <80%, yellow 80-95%, red ≥95%
  - Tooltip on hover showing exact timestamp/percentage/call count
```

**ProviderStatusCard**
```
Props:
  - provider: string
  - limit: number
  - current_usage: number
  - usage_pct: number
  - reset_in_seconds: number
  - status: 'healthy' | 'warning' | 'critical'
  - onClick: () => void

Renders: Card with:
  - Status badge (color-coded icon)
  - Provider name + limit
  - Usage bar (0-100%)
  - Reset countdown timer
  - Click → expands to show detailed history
```

**RateLimitDashboard (Page)**
```
Layout:
  - Header with refresh button + last update timestamp
  - Provider cards grid (responsive 2-4 columns)
  - Time series chart showing all providers
  - Details section (expanded when card clicked)
```

### State Management

**useRateLimits Hook**
```typescript
{
  providers: Array<{
    provider: string
    limit_value: number
    current_usage: number
    usage_pct: number
    reset_in_seconds: number
    status: string
  }>,
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  getHistory: (provider: string, hours: number) => Promise<Array>
}
```

- Auto-polls GET /api/rate-limits every 30 seconds
- Manual refresh via refresh() button
- Detailed history fetched on-demand

## Business Rules

- **Tracking**: Decorator on `_make_request()` in each data provider automatically logs all API calls with timestamp, status code, response time
- **Usage Calculation**: `current_usage = COUNT(logs where created_at > NOW() - reset_interval) / limit_value`
- **Reset Time**: Extracted from provider response headers; if missing, use hardcoded intervals:
  - CoinGecko: hourly (3600s)
  - TradingView: daily (86400s)
  - SEC: 8 hours (28800s)
- **Status Determination**:
  - Healthy: usage % < alert_threshold (default 80%)
  - Warning: alert_threshold ≤ usage % < 95%
  - Critical: usage % ≥ 95%
- **Alert Threshold**: Configurable per provider in DB; defaults to 80%
- **Cleanup**: Logs older than 90 days are automatically archived/deleted (via background job)

## Edge Cases

- **No logs recorded yet**: Displays 0% usage, "healthy" status, no data in history chart
- **Provider not in api_rate_limits table**: Auto-create entry on first API call with sensible defaults
- **Rate limit exceeded (429 response)**: Log call with status 429; usage % may exceed 100%
- **Missing reset_time**: Use hardcoded intervals per provider
- **Concurrent API calls**: Log entries created independently; counts are eventually consistent
- **Historical data gap**: Chart shows only available data; empty periods omitted
- **Very small limits** (e.g., SEC = 10/day): Percentage quickly reaches warning/critical
- **Provider response time spikes**: response_time_ms logged; max value clamped at 60,000ms

## Security

- **Authentication**: All endpoints require valid API key / session token (inherited from parent API)
- **Authorization**: Users can only view rate limits for providers their role has access to
- **Input Validation**:
  - `hours` parameter: 1-720 range, integer only
  - `interval`: enum validation (hourly, daily)
  - `provider` in URL: whitelist against known provider names
- **Rate Limiting**: GET /api/rate-limits polling is self-rate-limited (max 2 requests/second per user to avoid feedback loops)
- **Data Privacy**: No PII in logs; only API provider names, endpoints, timing, status codes are logged

## Testing

### Unit Tests (`test_rate_limit_manager.py`)
- Calculate usage % from log count + limit
- Status determination logic (healthy/warning/critical thresholds)
- Reset time countdown calculation
- Handling missing reset_time (use provider defaults)
- Edge cases: zero logs, zero limit, large values
- Auto-create missing provider entries

### E2E Tests (`test_api_rate_limits_page.tsx`)
- Dashboard renders without errors
- All provider cards display correctly with current usage
- Gauges show accurate percentages and color coding
- Click provider card → detailed history expands
- Time series chart renders 24h data
- Refresh button updates data
- Status badges show correct colors (green/yellow/red)
- Reset countdown timer updates in real-time

### Integration Tests (`test_rate_limits_api.py`)
- GET /api/rate-limits returns all providers in correct format
- GET /api/rate-limits/{provider}/history with various hour ranges
- Pagination boundaries (hours=1, hours=720)
- Invalid interval parameter returns 400 error
- Missing provider returns 404 error
- Response times consistently <100ms

## Changes & Deprecations

**Version 1.0** (2026-03-02)
- Initial release: Rate limit tracking + real-time dashboard
- Providers: CoinGecko, TradingView, SEC
- Features: Current usage gauges, 24h history chart, status alerts

---

## Acceptance Criteria

1. **AC1**: Dashboard displays all API providers' current usage % in real-time (auto-refresh every 30s)
2. **AC2**: Gauges color-code by status (green <80%, yellow 80-95%, red ≥95%)
3. **AC3**: Historical chart shows last 24h usage trends per provider
4. **AC4**: Click provider card → expands detailed history with hourly breakdown
5. **AC5**: All queries return <100ms; handles 10K+ logs/day efficiently
6. **AC6**: Status alerts correctly identify critical usage (≥95%) and warn (80-95%)