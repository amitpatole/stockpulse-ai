```markdown
# Feature: Earnings Calendar

## Overview
Display an earnings calendar view showing upcoming and past earnings dates with estimates and actual results. Users can filter by date range, view earnings history, and see EPS estimates vs actuals with surprise percentages.

## Data Model

### Database Tables
- `earnings_calendar` - Stores earnings dates, estimates, and actuals for stocks

### Database Schema
```sql
CREATE TABLE IF NOT EXISTS earnings_calendar (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker              TEXT NOT NULL,
    earnings_date       TEXT NOT NULL,
    estimated_eps       REAL,
    actual_eps          REAL,
    estimated_revenue   REAL,
    actual_revenue      REAL,
    surprise_percent    REAL,
    fiscal_quarter      TEXT,
    fiscal_year         INTEGER,
    status              TEXT DEFAULT 'upcoming',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker),
    UNIQUE(ticker, earnings_date),
    INDEX idx_ticker_date (ticker, earnings_date DESC),
    INDEX idx_status_date (status, earnings_date DESC)
)
```

### Sample Data
```json
{
  "id": 1,
  "ticker": "AAPL",
  "earnings_date": "2026-04-28",
  "estimated_eps": 1.82,
  "actual_eps": 1.95,
  "estimated_revenue": 91.5,
  "actual_revenue": 93.7,
  "surprise_percent": 7.14,
  "fiscal_quarter": "Q2",
  "fiscal_year": 2026,
  "status": "reported",
  "created_at": "2026-03-06T12:00:00Z",
  "updated_at": "2026-03-06T12:00:00Z"
}
```

## API Endpoints

### GET /api/earnings
List earnings with filters (upcoming, past, date range).

**Request Parameters:**
- `limit` (int, optional): Items per page. Range: 1-100, Default: 25
- `offset` (int, optional): Pagination offset. Default: 0
- `status` (string, optional): Filter by status: "upcoming", "reported". Default: all
- `start_date` (string, optional): ISO date (YYYY-MM-DD). Show earnings on or after this date
- `end_date` (string, optional): ISO date (YYYY-MM-DD). Show earnings on or before this date
- `ticker` (string, optional): Filter by specific ticker

**Response Example:**
```bash
curl "http://localhost:5000/api/earnings?status=upcoming&limit=25&offset=0"
```

```json
{
  "data": [
    {
      "id": 1,
      "ticker": "AAPL",
      "earnings_date": "2026-04-28",
      "estimated_eps": 1.82,
      "actual_eps": null,
      "estimated_revenue": 91.5,
      "actual_revenue": null,
      "surprise_percent": null,
      "fiscal_quarter": "Q2",
      "fiscal_year": 2026,
      "status": "upcoming"
    }
  ],
  "meta": {
    "total": 150,
    "limit": 25,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  }
}
```

### GET /api/earnings/{ticker}
Get earnings history for a specific ticker.

**Response Example:**
```bash
curl "http://localhost:5000/api/earnings/AAPL?limit=10"
```

```json
{
  "data": [
    {
      "id": 5,
      "ticker": "AAPL",
      "earnings_date": "2026-01-30",
      "estimated_eps": 1.75,
      "actual_eps": 1.89,
      "estimated_revenue": 89.2,
      "actual_revenue": 92.1,
      "surprise_percent": 8.0,
      "fiscal_quarter": "Q1",
      "fiscal_year": 2026,
      "status": "reported"
    }
  ],
  "meta": {
    "total": 25,
    "limit": 10,
    "offset": 0,
    "has_next": true,
    "has_previous": false
  }
}
```

### POST /api/earnings/sync
Sync earnings data from external data source (admin endpoint).

**Request Body:**
```json
{
  "ticker": "AAPL",
  "force_refresh": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Synced 5 earnings records for AAPL",
  "count": 5
}
```

## Dashboard/UI Elements

### Pages
- `/earnings` - Main earnings calendar page
  - Display mode toggle: Calendar view / List view
  - Date range filter (date picker)
  - Status filter (upcoming / reported)
  - Ticker search/filter
  - Pagination controls

### Components
- **EarningsCalendar.tsx** - Calendar grid showing earnings by month
  - Month/year navigation
  - Earnings cells with EPS data
  - Click to view details
  - Indicators for beat/miss/neutral

- **EarningsTable.tsx** - Tabular list view
  - Sortable columns (ticker, date, EPS, surprise)
  - Row highlighting for beats/misses
  - Inline detail expansion
  - Color coding: green for beats, red for misses, gray for upcoming

- **EarningsDetail.tsx** - Modal/drawer with full details
  - Ticker and company name
  - Estimated vs actual comparison
  - Historical performance chart
  - Related news articles

- **EarningsFilters.tsx** - Filter controls
  - Date range picker (start/end date)
  - Status dropdown (upcoming/reported)
  - Ticker search input
  - Apply/Reset buttons

## Business Rules
- Earnings data is cached for 24 hours after sync
- Only users with stocks in their watchlist can see earnings
- Dates are displayed in user's timezone
- EPS surprise calculated as: (actual_eps - estimated_eps) / estimated_eps * 100
- Status values: "upcoming" (before earnings_date), "reported" (on or after earnings_date)
- One earnings record per ticker per date (UNIQUE constraint)
- Earnings cascade delete with parent stock

## Edge Cases
- **No estimates available**: Display "—" for estimated fields
- **Earnings date is today**: Display as "Today" with special highlighting
- **No earnings history**: Show "No earnings found" message with suggestion to add stocks
- **Multiple records same date**: Use UNIQUE constraint to prevent duplicates
- **Timezone mismatch**: Always store in UTC, convert to user timezone on display
- **Very old earnings**: Show in list but hide from calendar after 2 years

## Security
- Earnings data is read-only for regular users
- Only admin can call /api/earnings/sync
- No sensitive data in earnings records
- All inputs validated with Pydantic models

## Testing
### Unit Tests
- Earnings filtering by status, date range, ticker
- Pagination calculation (has_next, has_previous)
- EPS surprise calculation
- Date range validation

### E2E Tests
- View upcoming earnings
- View past earnings
- Filter by status
- Filter by date range
- View earnings detail modal
- Pagination navigation
```