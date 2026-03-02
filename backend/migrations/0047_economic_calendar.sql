```sql
-- Economic Calendar Tables
-- Tracks economic events, releases, and their impact on monitored stocks

-- Master table for economic events (CPI, Fed Rate, Unemployment, etc.)
CREATE TABLE IF NOT EXISTS economic_events (
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

-- Releases: actual event instances with forecast/actual values and surprise %
CREATE TABLE IF NOT EXISTS economic_releases (
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

-- Stock impacts: links economic events to monitored tickers with sensitivity scores
CREATE TABLE IF NOT EXISTS event_stock_impacts (
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_economic_events_scheduled_date ON economic_events(scheduled_date DESC);
CREATE INDEX IF NOT EXISTS idx_economic_events_country ON economic_events(country);
CREATE INDEX IF NOT EXISTS idx_economic_events_importance ON economic_events(importance);
CREATE INDEX IF NOT EXISTS idx_economic_releases_event_id ON economic_releases(event_id);
CREATE INDEX IF NOT EXISTS idx_economic_releases_status ON economic_releases(status);
CREATE INDEX IF NOT EXISTS idx_event_stock_impacts_event_id ON event_stock_impacts(event_id);
CREATE INDEX IF NOT EXISTS idx_event_stock_impacts_ticker ON event_stock_impacts(ticker);
CREATE INDEX IF NOT EXISTS idx_event_stock_impacts_sensitivity ON event_stock_impacts(sensitivity_score DESC);
```