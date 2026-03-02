# Feature: Economic Calendar

## Overview
Display upcoming economic events (CPI, Fed rates, jobless claims, etc.) with severity levels, actual vs. forecast values, and their impact on monitored stocks. Events are tracked with forecast/actual values and automatic surprise percentage calculations. Real-time backend sync job keeps data current.

---

## Data Model

### Database Tables

**economic_events** - Master table for economic indicators
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique event identifier |
| `event_name` | TEXT NOT NULL | e.g. "CPI", "Federal Funds Rate Decision" |
| `country` | TEXT NOT NULL | Country code: "US", "EU", "UK", "JP", "CA", "AU" |
| `importance` | TEXT NOT NULL | Level: "low", "medium", "high" (enforced by CHECK) |
| `scheduled_date` | TIMESTAMP NOT NULL | When event is expected to release (YYYY-MM-DD HH:MM:SS) |
| `source` | TEXT DEFAULT 'tradingeconomics' | Data source provider |
| `created_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Last update time |
| **UNIQUE** | `(event_name, country, scheduled_date)` | Prevent duplicate events |

**economic_releases** - Instance of each event with forecast/actual values
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique release identifier |
| `event_id` | INTEGER NOT NULL | FK → economic_events (CASCADE) |
| `forecast_value` | REAL | Expected value from economists |
| `actual_value` | REAL | Actual released value |
| `previous_value` | REAL | Previous period's value |
| `surprise_pct` | REAL | `(actual - forecast) / abs(forecast) * 100` (NULL if forecast=0) |
| `release_date` | TIMESTAMP | When actual value released (YYYY-MM-DD HH:MM:SS) |
| `status` | TEXT DEFAULT 'scheduled' | "scheduled" or "released" (enforced by CHECK) |
| `created_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Last update time |
| **UNIQUE** | `(event_id, release_date)` | One release per event+date |

**event_stock_impacts** - Track which tickers are sensitive to each event
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PRIMARY KEY | Unique impact identifier |
| `event_id` | INTEGER NOT NULL | FK → economic_events (CASCADE) |
| `ticker` | TEXT NOT NULL | Stock ticker (FK → stocks, CASCADE) |
| `sensitivity_score` | REAL NOT NULL | Impact sensitivity 0.0–10.0 (enforced by CHECK) |
| `created_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | Last update time |
| **UNIQUE** | `(event_id, ticker)` | One impact per event+ticker |

### Database Schema
```sql
CREATE TABLE economic_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    country TEXT NOT NULL,
    importance TEXT NOT NULL CHECK(importance IN ('low', 'medium', 'high')),
    scheduled_date TIMESTAMP NOT NULL,
    source TEXT DEFAULT 'tradingeconomics',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_name, country, scheduled_date)
);

CREATE TABLE economic_releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    forecast_value REAL,
    actual_value REAL,
    previous_value REAL,
    surprise_pct REAL,
    release_date TIMESTAMP,
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'released')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, release_date),
    FOREIGN KEY(event_id) REFERENCES economic_events(id) ON DELETE CASCADE
);

CREATE TABLE event_stock_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    sensitivity_score REAL NOT NULL CHECK(sensitivity_score >= 0.0 AND sensitivity_score <= 10.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, ticker),
    FOREIGN KEY(event_id) REFERENCES economic_events(id) ON DELETE CASCADE,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

CREATE INDEX idx_economic_events_scheduled_date ON economic_events(scheduled_date DESC);
CREATE INDEX idx_economic_events_country ON economic_events(country);
CREATE INDEX idx_economic_events_importance ON economic_events(importance);
CREATE INDEX idx_economic_releases_event_id ON economic_releases(event_id);
CREATE INDEX idx_economic_releases_status ON economic_releases(status);
CREATE INDEX idx_event_stock_impacts_event_id ON event_stock_impacts(event_id);
CREATE INDEX idx_event_stock_impacts_ticker ON event_stock_impacts(ticker);
CREATE INDEX idx_event_stock_impacts_sensitivity ON event_stock_impacts(sensitivity_score DESC);
```

### Sample Data
```json
{
  "events": [
    {
      "id": 1,
      "event_name": "CPI",
      "country": "US",
      "importance": "high",
      "scheduled_date": "2026-03-12 08:30:00",
      "source": "tradingeconomics",
      "created_at": "2026-03-02 10:00:00"
    }
  ],
  "releases": [
    {
      "id": 1,
      "event_id": 1,
      "forecast_value": 2.8,
      "actual_value": 2.85,
      "previous_value": 2.75,
      "surprise_pct": 1.79,
      "release_date": "2026-03-12 08:30:00",
      "status": "released"
    }
  ],
  "impacts": [
    {
      "id": 1,
      "event_id": 1,
      "ticker": "SPY",
      "sensitivity_score": 8.5
    },
    {
      "id": 2,
      "event_id": 1,
      "ticker": "GLD",
      "sensitivity_score": 7.0
    }
  ]
}
```

---

## API Endpoints

All endpoints follow the standard response format:
```json
{
  "data": [...],
  "meta": {...},
  "errors": []
}
```

### GET /api/economic-calendar
List economic events with optional filtering and pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string (YYYY-MM-DD) | — | Filter: events on/after this date |
| `end_date` | string (YYYY-MM-DD) | — | Filter: events on/before this date |
| `country` | string | — | Filter: country code (e.g., "US") |
| `importance` | string | — | Filter: "low", "medium", or "high" |
| `limit` | integer | 50 | Page size (clamped to 1–100) |
| `offset` | integer | 0 | Pagination offset (clamped to ≥0) |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "event_name": "CPI",
      "country": "US",
      "importance": "high",
      "scheduled_date": "2026-03-12 08:30:00",
      "source": "tradingeconomics",
      "created_at": "2026-03-02 10:00:00",
      "updated_at": "2026-03-02 10:00:00"
    }
  ],
  "meta": {
    "total_count": 50,
    "limit": 50,
    "offset": 0,
    "has_next": false
  },
  "errors": []
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/economic-calendar?country=US&importance=high&limit=25&offset=0" \
  -H "Content-Type: application/json"
```

---

### GET /api/economic-calendar/{event_id}/impacts
Get all stocks affected by a specific economic event with sensitivity scores.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `event_id` | integer | ID of the economic event |

**Response (200 OK):**
```json
{
  "data": {
    "id": 1,
    "event_name": "CPI",
    "country": "US",
    "importance": "high",
    "scheduled_date": "2026-03-12 08:30:00",
    "impacts": [
      {
        "ticker": "SPY",
        "sensitivity_score": 8.5
      },
      {
        "ticker": "GLD",
        "sensitivity_score": 7.0
      }
    ]
  },
  "meta": {
    "impact_count": 2
  },
  "errors": []
}
```

**Response (404 Not Found):**
```json
{
  "data": null,
  "meta": {},
  "errors": ["Event not found"]
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/economic-calendar/1/impacts" \
  -H "Content-Type: application/json"
```

---

### GET /api/economic-calendar/watchlist-events
List economic events that affect monitored stocks in the user's watchlist.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Page size (clamped to 1–100) |
| `offset` | integer | 0 | Pagination offset (clamped to ≥0) |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "event_name": "CPI",
      "country": "US",
      "importance": "high",
      "scheduled_date": "2026-03-12 08:30:00",
      "impacts": [
        {
          "ticker": "SPY",
          "sensitivity_score": 8.5
        }
      ]
    }
  ],
  "meta": {
    "total_count": 3,
    "limit": 50,
    "offset": 0,
    "has_next": false
  },
  "errors": []
}
```

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/economic-calendar/watchlist-events?limit=50&offset=0" \
  -H "Content-Type: application/json"
```

---

### POST /api/economic-calendar/sync
Internal endpoint to trigger economic calendar synchronization. Fetches latest economic events from external data sources (currently uses mock data; expandable to TradingEconomics API, FRED, etc.).

**Request Body:**
Empty (no parameters required).

**Response (202 Accepted):**
```json
{
  "data": {
    "synced_count": 3,
    "errors_count": 0
  },
  "meta": {},
  "errors": []
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/economic-calendar/sync" \
  -H "Content-Type: application/json"
```

---

## Dashboard/UI Elements

### Pages

**Economic Calendar Page** (`/economic-calendar`)
- Main calendar view with event listing
- Header: "Economic Calendar" title + subtitle
- Filter panel: Date range, country, importance dropdowns
- Table: Paginated event list with columns
- Pagination controls: Previous/Next buttons + event count display

### Components

**EconomicCalendarTable**
- Root component managing filters and pagination state
- Props: `events`, `meta`, `loading`, `error`, `onFilterChange`, `onPaginate`
- Renders: Filter controls + Table + Pagination
- Pagination: Limit clamped 1–100, offset ≥0, has_next flag

**EconomicEventCard**
- Single table row for one event
- Displays: Event name, country, importance badge (color-coded), scheduled date, affected stock badges
- Row styling: Past events faded (opacity 60%), hover highlight
- Importance colors: low=emerald, medium=yellow, high=red

**StockImpactBadge**
- Inline badge showing affected ticker + sensitivity intensity
- Color-coding by sensitivity: ≥8=red, ≥5=yellow, <5=emerald
- Intensity labels: "Very High" (≥8), "Medium" (5–7), "Low" (<5)
- Tooltip: `{ticker} sensitivity: {score}/10`

### Hooks

**useEconomicEvents()**
- State: events, meta, loading, error, filters
- Methods:
  - `setStartDate(date | null)` – Filter by start date
  - `setEndDate(date | null)` – Filter by end date
  - `setCountry(country | null)` – Filter by country
  - `setImportance(importance | null)` – Filter by importance
  - `setLimit(limit)` – Update page size (auto-clamped 1–100)
  - `setOffset(offset)` – Update pagination offset (auto-clamped ≥0)
  - `refetch()` – Manual data refresh
- Auto-fetches when filters/limit/offset change

---

## Business Rules

1. **Unique Events:** event_name + country + scheduled_date must be unique. Duplicate upserts update existing record.
2. **Cascade Deletes:** Deleting an event cascades to releases and impacts.
3. **Surprise Calculation:** `(actual - forecast) / abs(forecast) * 100`; NULL if forecast = 0.
4. **Sensitivity Clamping:** 0.0 ≤ sensitivity_score ≤ 10.0 (enforced at DB + code layer).
5. **Pagination Boundaries:** limit clamped 1–100, offset clamped ≥0 to prevent invalid queries.
6. **Status Transitions:** Events start as "scheduled", change to "released" when actual_value is available.
7. **Background Sync:** Job runs every 6 hours, catches errors per event (continues on failure).
8. **Watchlist Filtering:** Only returns events with at least one impact in event_stock_impacts.

---

## Edge Cases

1. **Empty Results:** When no events match filters, return empty `data: []`, `meta.total_count: 0`, `has_next: false`.
2. **Zero Forecast:** Surprise % is NULL (avoid division by zero).
3. **Past Events:** Displayed but visually faded (opacity 60%).
4. **Missing Impacts:** Event row displays "No impacts" placeholder if impacts array is empty.
5. **Pagination Overflow:** `offset > total_count` returns empty data; client should adjust offset.
6. **Null Values:** forecast_value, actual_value, previous_value can be NULL before release.
7. **Concurrent Updates:** SQLite row-level locks prevent race conditions on upsert_event.
8. **Network Failures:** Sync job logs error per event and continues processing others.

---

## Security

- **Input Validation:** Date strings validated YYYY-MM-DD format; country/importance enum-checked.
- **Parameterized Queries:** All SQL uses ? placeholders (prevents SQL injection).
- **No Hardcoded Credentials:** External API calls require config from environment variables.
- **Rate Limiting:** API endpoints enforce standard rate limits (see `/documentation/09-api-guidelines.md`).
- **Authentication:** All endpoints authenticated via existing auth middleware.

---

## Testing

### Unit Tests
- `test_economic_calendar_manager.py`: CRUD operations, filtering logic, pagination bounds, surprise calculation, cascade deletes
- Acceptance criteria:
  - AC1: Upsert event and release with all fields populated
  - AC2: Filter by date range, country, importance (boundary cases)
  - AC3: Surprise % calculated correctly (zero forecast handling)
  - AC4: Deleting event cascades to releases and impacts

### API Integration Tests
- `test_economic_calendar_api.py`: All 4 endpoints with valid/invalid inputs
- Test cases: 200 OK, 404 not found, 400 validation error, empty results, pagination

### Frontend Component Tests
- `test_economic_calendar_page.tsx` (Vitest): Rendering, filter state, loading/error states
- `test_economic_calendar_e2e.ts` (Playwright): Calendar navigation, filter interaction, pagination clicks

### Acceptance Criteria
- **AC1:** Events list renders with correct column headers and data
- **AC2:** Filters (date, country, importance) update event list on change
- **AC3:** Pagination: Previous disabled at offset=0, Next disabled when has_next=false
- **AC4:** Loading state shows spinner while fetching; error state displays error message
- **AC5:** Empty results show placeholder; past events visually faded
- **AC6:** Sensitivity badges color-coded by score; tooltip shows exact score

---

## Changes & Deprecations

### v1.0 (Initial Release)
- Added 3 tables: economic_events, economic_releases, event_stock_impacts
- Implemented 4 API endpoints: list, impacts, watchlist, sync
- Created frontend components: calendar page, table, badges
- Added background sync job (6-hour interval)
- Mock data provider (expandable to real APIs)

---

## Related Documentation
- **API Guidelines:** `documentation/09-api-guidelines.md` (response format, error handling)
- **Database Schema:** `documentation/08-database-schema.md` (foreign keys, indexes)
- **Testing Guide:** `documentation/24-testing.md` (unit/E2E patterns)