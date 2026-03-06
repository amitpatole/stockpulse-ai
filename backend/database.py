```python
"""SQLite database management with WAL mode and idempotent migrations."""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional

import aiosqlite

from backend.config import Config

logger = logging.getLogger(__name__)

# ── Synchronous helpers ─────────────────────────────────────────────

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory enabled."""
    path = db_path or Config.DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def db_session(db_path: Optional[str] = None):
    """Context manager that yields a connection and auto-closes it."""
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Async helpers ───────────────────────────────────────────────────

async def get_async_db(db_path: Optional[str] = None) -> aiosqlite.Connection:
    """Return an async SQLite connection."""
    path = db_path or Config.DB_PATH
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


# ── Schema ──────────────────────────────────────────────────────────

_TABLES_SQL = [
    # Watchlist groups (for organizing stocks)
    """
    CREATE TABLE IF NOT EXISTS watchlist_groups (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        name                TEXT NOT NULL UNIQUE,
        description         TEXT,
        color               TEXT DEFAULT '#6366f1',
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Research briefs (AI-generated research documents)
    """
    CREATE TABLE IF NOT EXISTS research_briefs (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker              TEXT NOT NULL,
        title               TEXT NOT NULL,
        content             TEXT NOT NULL,
        executive_summary   TEXT,
        agent_name          TEXT NOT NULL,
        model_used          TEXT,
        has_metrics         INTEGER DEFAULT 0,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Research brief metadata (extended info: key insights, metrics, PDF)
    """
    CREATE TABLE IF NOT EXISTS research_brief_metadata (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        brief_id            INTEGER NOT NULL UNIQUE,
        executive_summary   TEXT,
        key_insights        TEXT,
        key_metrics         TEXT,
        metric_sources      TEXT,
        pdf_url             TEXT,
        pdf_generated_at    TIMESTAMP,
        summary_version     INTEGER DEFAULT 1,
        created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (brief_id) REFERENCES research_briefs(id) ON DELETE CASCADE
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
```