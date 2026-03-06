"""SQLite database management with WAL mode and idempotent migrations."""

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
    # Stock data (with watchlist group support)
    """
    CREATE TABLE IF NOT EXISTS stocks (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker              TEXT NOT NULL UNIQUE,
        company_name        TEXT,
        current_price       REAL,
        price_change_pct    REAL,
        market_cap          TEXT,
        active              INTEGER DEFAULT 1,
        group_id            INTEGER,
        sort_order          INTEGER DEFAULT 0,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES watchlist_groups(id) ON DELETE SET NULL
    )
    """,
    # AI ratings (existing table structure for reference)
    """
    CREATE TABLE IF NOT EXISTS ai_ratings (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker              TEXT NOT NULL,
        rating              TEXT,
        score               REAL,
        rsi                 REAL,
        sentiment_score     REAL,
        sentiment_label     TEXT,
        technical_score     REAL,
        fundamental_score   REAL,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticker) REFERENCES stocks(ticker)
    )
    """,
    # News articles (existing table structure for reference)
    """
    CREATE TABLE IF NOT EXISTS news (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker              TEXT NOT NULL,
        title               TEXT NOT NULL,
        content             TEXT,
        sentiment_label     TEXT,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticker) REFERENCES stocks(ticker)
    )
    """,
    # Price alerts (user-configured thresholds)
    """
    CREATE TABLE IF NOT EXISTS price_alerts (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker              TEXT NOT NULL,
        alert_type          TEXT NOT NULL,
        threshold           REAL NOT NULL,
        is_active           INTEGER DEFAULT 1,
        triggered_count     INTEGER DEFAULT 0,
        last_triggered_at   TIMESTAMP,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, alert_type, threshold),
        FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
    )
    """,
]

_INDEXES_SQL = [
    # Watchlist group indexes
    "CREATE INDEX IF NOT EXISTS idx_stocks_group_order ON stocks(group_id, sort_order)",
    "CREATE INDEX IF NOT EXISTS idx_stocks_active_group ON stocks(active, group_id)",

    # Research briefs indexes
    "CREATE INDEX IF NOT EXISTS idx_research_briefs_ticker ON research_briefs(ticker)",
    "CREATE INDEX IF NOT EXISTS idx_research_briefs_created ON research_briefs(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_research_briefs_ticker_created ON research_briefs(ticker, created_at DESC)",

    # Research metadata indexes
    "CREATE INDEX IF NOT EXISTS idx_metadata_brief ON research_brief_metadata(brief_id)",
    "CREATE INDEX IF NOT EXISTS idx_metadata_created ON research_brief_metadata(created_at DESC)",

    # Stock and ratings indexes (for metrics extraction)
    "CREATE INDEX IF NOT EXISTS idx_stocks_ticker ON stocks(ticker)",
    "CREATE INDEX IF NOT EXISTS idx_stocks_active ON stocks(active)",
    "CREATE INDEX IF NOT EXISTS idx_ai_ratings_ticker ON ai_ratings(ticker)",
    "CREATE INDEX IF NOT EXISTS idx_ai_ratings_updated ON ai_ratings(updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_news_ticker ON news(ticker)",
    "CREATE INDEX IF NOT EXISTS idx_news_created ON news(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_news_ticker_created ON news(ticker, created_at DESC)",

    # Price alerts indexes
    "CREATE INDEX IF NOT EXISTS idx_price_alerts_ticker_active ON price_alerts(ticker, is_active)",
    "CREATE INDEX IF NOT EXISTS idx_price_alerts_created ON price_alerts(created_at DESC)",
]


def init_all_tables(db_path: Optional[str] = None) -> None:
    """Create every table and apply indexes. Safe to call multiple times."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        for sql in _TABLES_SQL:
            cursor.execute(sql)
        for sql in _INDEXES_SQL:
            cursor.execute(sql)
        conn.commit()
        logger.info("Database tables initialized with price alerts schema")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to initialize tables: {e}")
        raise
    finally:
        conn.close()


def migrate_add_price_alerts_table(db_path: Optional[str] = None) -> None:
    """Add price_alerts table if it doesn't exist (idempotent)."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM price_alerts LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Creating price_alerts table...")
            cursor.execute("""
                CREATE TABLE price_alerts (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker              TEXT NOT NULL,
                    alert_type          TEXT NOT NULL,
                    threshold           REAL NOT NULL,
                    is_active           INTEGER DEFAULT 1,
                    triggered_count     INTEGER DEFAULT 0,
                    last_triggered_at   TIMESTAMP,
                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ticker, alert_type, threshold),
                    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX idx_price_alerts_ticker_active ON price_alerts(ticker, is_active)")
            cursor.execute("CREATE INDEX idx_price_alerts_created ON price_alerts(created_at DESC)")
            logger.info("price_alerts table created")
