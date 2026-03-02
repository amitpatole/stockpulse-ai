-- Migration: API Rate Limits Schema
-- Adds tables for tracking API rate limits and usage logs

CREATE TABLE IF NOT EXISTS api_rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT UNIQUE NOT NULL,
    limit_value INTEGER NOT NULL,
    reset_time TIMESTAMP NOT NULL,
    alert_threshold INTEGER DEFAULT 80,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_name) REFERENCES api_rate_limits(provider_name) ON DELETE CASCADE
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_api_usage_logs_provider_created 
  ON api_usage_logs(provider_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_usage_logs_created 
  ON api_usage_logs(created_at DESC);

-- Initialize default providers
INSERT OR IGNORE INTO api_rate_limits (provider_name, limit_value, reset_time, alert_threshold)
VALUES 
  ('CoinGecko', 50, datetime('now', '+1 hour'), 80),
  ('TradingView', 3000, datetime('now', '+1 day'), 80),
  ('SEC', 10, datetime('now', '+8 hours'), 85);