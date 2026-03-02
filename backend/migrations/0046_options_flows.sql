-- Options Flow Tracker Tables
-- Tracks unusual options activity with volume analysis and alerts

-- Main options flow tracking table
CREATE TABLE IF NOT EXISTS options_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    flow_type TEXT NOT NULL,  -- 'call_spike' | 'put_spike' | 'unusual_volume'
    option_type TEXT NOT NULL,  -- 'call' | 'put'
    strike_price REAL,
    expiry_date TEXT,  -- YYYY-MM-DD
    volume INTEGER DEFAULT 0,
    open_interest INTEGER DEFAULT 0,
    unusual_ratio REAL DEFAULT 1.0,  -- current_volume / 20-day_avg
    price_action TEXT DEFAULT 'neutral',  -- 'bullish' | 'bearish' | 'neutral'
    detected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- User-facing alerts with dismissal state
CREATE TABLE IF NOT EXISTS options_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    flow_id INTEGER,
    alert_type TEXT NOT NULL,  -- 'volume_spike' | 'unusual_ratio' | 'expiry_approaching'
    severity TEXT DEFAULT 'medium',  -- 'low' | 'medium' | 'high'
    message TEXT NOT NULL,
    dismissed INTEGER DEFAULT 0,  -- 0 = unread, 1 = dismissed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
    FOREIGN KEY(flow_id) REFERENCES options_flows(id) ON DELETE CASCADE
);

-- Per-stock tracking configuration
CREATE TABLE IF NOT EXISTS options_flow_config (
    ticker TEXT PRIMARY KEY,
    enabled INTEGER DEFAULT 1,
    volume_spike_threshold REAL DEFAULT 2.0,  -- Multiplier of 20-day average
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_options_flows_ticker ON options_flows(ticker);
CREATE INDEX IF NOT EXISTS idx_options_flows_detected ON options_flows(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_options_flows_unusual_ratio ON options_flows(unusual_ratio DESC);
CREATE INDEX IF NOT EXISTS idx_options_alerts_ticker ON options_alerts(ticker);
CREATE INDEX IF NOT EXISTS idx_options_alerts_severity ON options_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_options_alerts_dismissed ON options_alerts(dismissed);