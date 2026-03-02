```sql
-- Options Flow Tracker Tables
-- Tracks unusual options activity with volume analysis and alerts

-- Main options flow tracking table
CREATE TABLE IF NOT EXISTS options_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    contract TEXT NOT NULL,  -- e.g., "AAPL 150C 2026-03-31"
    option_type TEXT NOT NULL,  -- 'call' or 'put'
    strike REAL,
    expiration DATE,
    volume INTEGER DEFAULT 0,
    open_interest INTEGER DEFAULT 0,
    bid_ask_spread REAL DEFAULT 0.0,
    iv_percentile INTEGER DEFAULT 0,
    flow_type TEXT NOT NULL,  -- 'unusual_volume' | 'large_trade' | 'put_call_imbalance'
    anomaly_score REAL DEFAULT 0.0,  -- 0-100, severity metric
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_alert BOOLEAN DEFAULT 0,
    user_note TEXT,
    UNIQUE(ticker, contract, created_at),
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- User alert subscription preferences
CREATE TABLE IF NOT EXISTS alert_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    ticker TEXT,  -- NULL = all tickers
    flow_type TEXT,  -- NULL = all types ('unusual_volume' | 'large_trade' | 'put_call_imbalance')
    min_anomaly_score REAL DEFAULT 70.0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_options_flows_ticker ON options_flows(ticker);
CREATE INDEX IF NOT EXISTS idx_options_flows_created_at ON options_flows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_options_flows_is_alert ON options_flows(is_alert);
CREATE INDEX IF NOT EXISTS idx_options_flows_anomaly_score ON options_flows(anomaly_score DESC);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_user_id ON alert_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_alert_subscriptions_active ON alert_subscriptions(is_active, user_id);
```