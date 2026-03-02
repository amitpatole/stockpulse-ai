```markdown
# Feature: Insider Trading Tracker

## Overview
Monitor SEC Form 4 filings for insider buying and selling activity across portfolio stocks. Provides transaction-level details, aggregate statistics, and sentiment analysis to identify meaningful insider trading patterns.

## Data Model

### Database Tables

#### insiders
Maps CIK (Central Index Key) to ticker for efficient lookups.

```sql
CREATE TABLE insiders (
    cik TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    company_name TEXT,
    insider_count INTEGER DEFAULT 0,
    last_filing_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);
```

#### insider_transactions
Individual Form 4 transactions with sentiment scores.

```sql
CREATE TABLE insider_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cik TEXT NOT NULL,
    ticker TEXT NOT NULL,
    insider_name TEXT,
    title TEXT,  -- Officer title at company
    transaction_type TEXT NOT NULL,  -- 'purchase' | 'sale' | 'grant' | 'exercise'
    shares INTEGER,
    price REAL,
    value REAL,  -- shares * price
    filing_date TIMESTAMP,
    transaction_date TIMESTAMP,
    sentiment_score REAL DEFAULT 0.0,  -- -1.0 to 1.0 (sale to purchase)
    is_derivative BOOLEAN DEFAULT 0,
    filing_url TEXT,
    form4_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(cik) REFERENCES insiders(cik) ON DELETE CASCADE,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);
```

#### insider_aggregate_stats
Aggregate metrics for each CIK by date.

```sql
CREATE TABLE insider_aggregate_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cik TEXT NOT NULL,
    ticker TEXT NOT NULL,
    aggregate_date DATE NOT NULL,
    net_shares_30d INTEGER DEFAULT 0,  -- Purchases - Sales last 30 days
    net_shares_90d INTEGER DEFAULT 0,
    buy_count INTEGER DEFAULT 0,
    sell_count INTEGER DEFAULT 0,
    total_buy_value REAL DEFAULT 0.0,
    total_sell_value REAL DEFAULT 0.0,
    sentiment_avg REAL DEFAULT 0.0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cik, ticker, aggregate_date),
    FOREIGN KEY(cik) REFERENCES insiders(cik) ON DELETE CASCADE,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);
```

### Indexes
- `idx_insider_transactions_ticker` on (ticker, filing_date DESC)
- `idx_insider_transactions_cik` on (cik, filing_date DESC)
- `idx_insider_transactions_type` on (transaction_type, filing_date DESC)
- `idx_insider_transactions_sentiment` on (sentiment_score DESC)
- `idx_insider_aggregate_stats_ticker` on (ticker, aggregate_date DESC)
- `idx_insiders_ticker` on (ticker)

## API Endpoints

### GET /api/insiders/filings
List insider transactions with filtering and pagination.

**Query Parameters:**
- `ticker` (string, optional) - Filter by stock ticker (e.g., 'AAPL')
- `cik` (string, optional) - Filter by CIK
- `type` (enum, optional) - Filter by transaction type: `purchase|sale|grant|exercise|all` (default: all)
- `min_days` (integer, optional) - Filter to last N days (default: 30)
- `min_sentiment` (float, optional) - Filter by minimum sentiment score (-1 to 1)
- `limit` (integer, default: 50, max: 100)
- `offset` (integer, default: 0)

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "ticker": "AAPL",
      "cik": "0000320193",
      "insider_name": "Tim Cook",
      "title": "CEO",
      "transaction_type": "purchase",
      "shares": 500,
      "price": 185.25,
      "value": 92625.00,
      "filing_date": "2026-03-01T10:30:00Z",
      "transaction_date": "2026-02-28",
      "sentiment_score": 0.95,
      "is_derivative": false,
      "filing_url": "https://www.sec.gov/..."
    }
  ],
  "meta": {
    "total_count": 42,
    "limit": 50,
    "offset": 0,
    "has_next": false
  },
  "errors": []
}
```

**Error Cases:**
- `400`: Invalid query parameters (non-numeric limit/offset, invalid type)
- `404`: Ticker/CIK not found
- `500`: Database error

### GET /api/insiders/{cik}/stats
Aggregate sentiment and share flow statistics.

**Path Parameters:**
- `cik` (string) - SEC Central Index Key

**Query Parameters:**
- `days` (integer, optional, default: 30) - Analysis period (7, 30, 90)
- `ticker` (string, optional) - Filter to specific ticker

**Response (200 OK):**
```json
{
  "data": {
    "cik": "0000320193",
    "ticker": "AAPL",
    "period_days": 30,
    "net_shares": 2500,
    "buy_count": 8,
    "sell_count": 2,
    "total_buy_value": 500000.00,
    "total_sell_value": 100000.00,
    "sentiment_avg": 0.72,
    "insider_count": 12,
    "last_filing_date": "2026-03-01T10:30:00Z"
  },
  "meta": {},
  "errors": []
}
```

**Error Cases:**
- `400`: Invalid days parameter (must be 7, 30, or 90)
- `404`: CIK not found
- `500`: Database error

### GET /api/insiders/watchlist/activity
List latest insider filings for user's watchlist stocks.

**Query Parameters:**
- `days` (integer, default: 7) - Look back period in days
- `limit` (integer, default: 50, max: 100)
- `offset` (integer, default: 0)

**Response (200 OK):**
```json
{
  "data": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "latest_filing_date": "2026-03-01T10:30:00Z",
      "transaction_count": 3,
      "filings": [
        {
          "id": 1,
          "insider_name": "Tim Cook",
          "transaction_type": "purchase",
          "shares": 500,
          "sentiment_score": 0.95
        }
      ],
      "net_sentiment": 0.75
    }
  ],
  "meta": {
    "total_count": 5,
    "limit": 50,
    "offset": 0,
    "has_next": false
  },
  "errors": []
}
```

## Dashboard/UI Elements

### Pages
- `/dashboard/insiders` - Main insider trading page with 3 tabs

### Components

#### InsiderActivityWidget
Dashboard summary card showing:
- Latest insider filing count (last 7 days)
- Net sentiment indicator (color-coded: green for buy bias, red for sell)
- Quick link to full insider page

#### InsiderFilings
Paginated transaction table with:
- Insider name, title, company
- Transaction type (color-coded)
- Shares, price, value
- Filing date
- Sentiment score
- Drill-down to SEC filing

#### InsiderStats
Aggregate metrics display:
- Net share flow (30/90 day)
- Buy/sell ratio
- Average sentiment score
- Insider count
- Total transaction value

#### InsiderAggregateChart
Time-series chart showing:
- 30/90-day net share flow trend
- Buy/sell volume bars
- Sentiment line overlay

## Business Rules

- **Sentiment Calculation**: purchases (+1.0) to sales (-1.0), weighted by volume
- **Derivative Handling**: Options exercises marked as derivatives but included in sentiment
- **CIK Mapping**: Ticker must exist in stocks table before insiders record created
- **Cascading Deletes**: Removing stock cascades to insiders and all related transactions
- **Sync Frequency**: Daily job at 9 PM ET fetches prior day's Form 4 filings
- **Data Freshness**: Insiders table updated with filing dates for last_filing_date tracking
- **Pagination**: Max 100 results per page, offset must be non-negative
- **Rate Limiting**: 100 requests/minute per IP on all endpoints

## Edge Cases

- **Empty Results**: No insiders for ticker → empty data array, has_next: false
- **Derivative Transactions**: Options exercises included in counts but flagged as derivatives
- **Price Data**: Some filings lack transaction price → value = 0
- **Concurrent Sync**: Multiple sync jobs prevented by database UNIQUE constraints
- **Stale CIK**: Ticker delisted/renamed → orphaned records handled by cascading delete
- **Partial Failures**: If Form 4 parse fails, skip transaction but continue sync

## Security

- **Authentication**: Rate-limited (100 req/min per IP), no auth required
- **Data Validation**: 
  - CIK format: uppercase 10-digit with leading zeros stripped
  - Ticker: uppercase alphanumeric only
  - Transaction counts: non-negative integers
  - Prices: non-negative floats, clamped to [0, 1M]
- **Injection Prevention**: All queries parameterized, no string interpolation
- **PII Handling**: Insider names/titles are public SEC data
- **HTTPS**: All SEC API calls over HTTPS

## Testing

### Unit Tests (`test_insider_provider.py`)

Verify SEC Form 4 parsing:
- Valid Form 4 XML parsing (ticker, CIK, insider, transaction details)
- Sentiment score calculation (buy +1.0, sale -1.0, weighted by volume)
- Derivative detection (option exercises flagged)
- Price normalization (invalid prices → 0)
- CIK cleanup (leading zeros stripped to match ticker mapping)

Verify error handling:
- Network timeouts → None returned (retried by sync job)
- Malformed XML → logged, transaction skipped
- Missing required fields → skipped with warning
- Rate limit (429) → backoff and retry

### Integration Tests (`test_insiders_api.py`)

Verify endpoints:
- `/api/insiders/filings` pagination, filtering by type/date, 404 on missing ticker
- `/api/insiders/{cik}/stats` calculations (net shares, sentiment avg), 404 on missing CIK
- `/api/insiders/watchlist/activity` watchlist filtering, pagination

Verify data integrity:
- Cascading deletes (ticker removed → insiders, transactions removed)
- Unique constraints (duplicate filings rejected)
- Foreign key constraints (cik/ticker must exist)

### E2E Tests (`frontend/src/components/insiders/__tests__/`)

Verify UI:
- Widget renders on dashboard with color-coded sentiment
- Filter dropdown changes work (transaction type, date range)
- Pagination buttons work (next/prev disabled appropriately)
- Drill-down to SEC filing opens in new window
- Chart updates on 30/90 day toggle

## Changes & Deprecations

**v1.0** (2026-03-02)
- Initial insider trading tracker with Form 4 filings
- Three new API endpoints
- Daily sync job at 9 PM ET
- Dashboard widget + dedicated insider page
```