```sql
-- TickerPulse AI v3.0 - Quota History Table
-- Tracks API quota usage over time for historical analysis and trends

CREATE TABLE IF NOT EXISTS quota_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_name TEXT NOT NULL,
    quota_type TEXT NOT NULL,
    used INTEGER NOT NULL,
    limit_value INTEGER NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(provider_name) REFERENCES api_quotas(provider_name)
);

CREATE INDEX IF NOT EXISTS idx_quota_history_provider 
    ON quota_history(provider_name);

CREATE INDEX IF NOT EXISTS idx_quota_history_provider_time 
    ON quota_history(provider_name, recorded_at);

CREATE INDEX IF NOT EXISTS idx_quota_history_recorded_at 
    ON quota_history(recorded_at);
```