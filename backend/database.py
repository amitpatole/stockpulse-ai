(Add to the _TABLES_SQL list in existing file)

```python
    # Earnings calendar (earnings dates, estimates, and actuals)
    """
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
        FOREIGN KEY(ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
        UNIQUE(ticker, earnings_date)
    )
    """,
```

Also add to _INDEXES_SQL list:
```python
    # Earnings calendar indexes
    """CREATE INDEX IF NOT EXISTS idx_earnings_ticker_date 
       ON earnings_calendar(ticker, earnings_date DESC)""",
    """CREATE INDEX IF NOT EXISTS idx_earnings_status_date 
       ON earnings_calendar(status, earnings_date DESC)""",
```