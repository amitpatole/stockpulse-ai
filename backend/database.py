```python
"""
TickerPulse AI v3.0 - Database Connection Manager
Thread-safe SQLite helper with context-manager support and table initialisation.
"""

import sqlite3
import logging
from contextlib import contextmanager

from backend.config import Config

logger = logging.getLogger(__name__)


# Global adapter instance
_adapter = None


def get_adapter():
    """Get or create the database adapter instance."""
    global _adapter
    if _adapter is None:
        from backend.adapters import get_db_adapter
        _adapter = get_db_adapter()
    return _adapter


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory enabled.

    Parameters
    ----------
    db_path : str, optional
        Override the default database path from Config.

    Notes
    -----
    * ``check_same_thread=False`` is required so Flask (and APScheduler)
      threads can share the connection safely.  SQLite itself serialises
      writes, so this is safe for the read-heavy workload of TickerPulse.
    """
    path = db_path or Config.DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')  # better concurrent-read perf
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


@contextmanager
def db_session(db_path: str | None = None):
    """Context manager that yields a connection and auto-closes it.

    Usage::

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT ...')
            conn.commit()

    Note: For multi-database support, this function delegates to the
    configured adapter (SQLite or PostgreSQL). The db_path parameter
    is only used for SQLite connections.
    """
    # Use adapter-based connection if DB_TYPE is postgres
    if Config.DB_TYPE.lower() == "postgres":
        adapter = get_adapter()
        with adapter.get_connection() as conn:
            yield conn
    else:
        # SQLite path (backward compatible)
        conn = get_db_connection(db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

# Existing tables (carried over from stock_monitor.py / settings_manager.py)
_EXISTING_TABLES_SQL = [
    # --- news ---
    """
    CREATE TABLE IF NOT EXISTS news (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker          TEXT NOT NULL,
        title           TEXT NOT NULL,
        description     TEXT,
        url             TEXT UNIQUE,
        source          TEXT,
        published_date  TEXT,
        sentiment_score REAL,
        sentiment_label TEXT,
        engagement_score REAL DEFAULT 0,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- alerts ---
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker      TEXT NOT NULL,
        news_id     INTEGER,
        alert_type  TEXT,
        message     TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (news_id) REFERENCES news (id)
    )
    """,
    # --- monitor_status ---
    """
    CREATE TABLE IF NOT EXISTS monitor_status (
        id          INTEGER PRIMARY KEY,
        last_check  TIMESTAMP,
        status      TEXT,
        message     TEXT
    )
    """,
    # --- stocks ---
    """
    CREATE TABLE IF NOT EXISTS stocks (
        ticker   TEXT PRIMARY KEY,
        name     TEXT,
        market   TEXT DEFAULT 'US',
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active   INTEGER DEFAULT 1
    )
    """,
    # --- settings ---
    """
    CREATE TABLE IF NOT EXISTS settings (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- ai_providers ---
    """
    CREATE TABLE IF NOT EXISTS ai_providers (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name TEXT NOT NULL,
        api_key       TEXT NOT NULL,
        model         TEXT,
        is_active     INTEGER DEFAULT 0,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- api_quotas ---
    """
    CREATE TABLE IF NOT EXISTS api_quotas (
        id              INTEGER PRIMARY KEY,
        provider_name   TEXT NOT NULL,
        quota_type      TEXT NOT NULL,
        limit_value     INTEGER NOT NULL,
        used            INTEGER DEFAULT 0,
        reset_at        TIMESTAMP,
        last_updated    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(provider_name, quota_type)
    )
    """,
    # --- api_rate_limits (for rate limit dashboard) ---
    """
    CREATE TABLE IF NOT EXISTS api_rate_limits (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name   TEXT UNIQUE NOT NULL,
        limit_value     INTEGER NOT NULL,
        reset_time      TIMESTAMP NOT NULL,
        alert_threshold INTEGER DEFAULT 80,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- api_usage_logs (for rate limit dashboard) ---
    """
    CREATE TABLE IF NOT EXISTS api_usage_logs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name   TEXT NOT NULL,
        endpoint        TEXT NOT NULL,
        status_code     INTEGER,
        response_time_ms INTEGER,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_name) REFERENCES api_rate_limits(provider_name) ON DELETE CASCADE
    )
    """,
]

# PostgreSQL versions of existing tables
_EXISTING_TABLES_SQL_POSTGRES = [
    # --- news ---
    """
    CREATE TABLE IF NOT EXISTS news (
        id              SERIAL PRIMARY KEY,
        ticker          TEXT NOT NULL,
        title           TEXT NOT NULL,
        description     TEXT,
        url             TEXT UNIQUE,
        source          TEXT,
        published_date  TEXT,
        sentiment_score REAL,
        sentiment_label TEXT,
        engagement_score REAL DEFAULT 0,
        created_at      TIMESTAMP DEFAULT NOW()
    )
    """,
    # --- alerts ---
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id          SERIAL PRIMARY KEY,
        ticker      TEXT NOT NULL,
        news_id     INTEGER,
        alert_type  TEXT,
        message     TEXT,
        created_at  TIMESTAMP DEFAULT NOW(),
        FOREIGN KEY (news_id) REFERENCES news (id)
    )
    """,
    # --- monitor_status ---
    """
    CREATE TABLE IF NOT EXISTS monitor_status (
        id          INTEGER PRIMARY KEY,
        last_check  TIMESTAMP,
        status      TEXT,
        message     TEXT
    )
    """,
    # --- stocks ---
    """
    CREATE TABLE IF NOT EXISTS stocks (
        ticker   TEXT PRIMARY KEY,
        name     TEXT,
        market   TEXT DEFAULT 'US',
        added_at TIMESTAMP DEFAULT NOW(),
        active   INTEGER DEFAULT 1
    )
    """,
    # --- settings ---
    """
    CREATE TABLE IF NOT EXISTS settings (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at TIMESTAMP DEFAULT NOW()
    )
    """,
    # --- ai_providers ---
    """
    CREATE TABLE IF NOT EXISTS ai_providers (
        id            SERIAL PRIMARY KEY,
        provider_name TEXT NOT NULL,
        api_key       TEXT NOT NULL,
        model         TEXT,
        is_active     INTEGER DEFAULT 0,
        created_at    TIMESTAMP DEFAULT NOW(),
        updated_at    TIMESTAMP DEFAULT NOW()
    )
    """,
    # --- api_quotas ---
    """
    CREATE TABLE IF NOT EXISTS api_quotas (
        id              SERIAL PRIMARY KEY,
        provider_name   TEXT NOT NULL,
        quota_type      TEXT NOT NULL,
        limit_value     INTEGER NOT NULL,
        used            INTEGER DEFAULT 0,
        reset_at        TIMESTAMP,
        last_updated    TIMESTAMP DEFAULT NOW(),
        UNIQUE(provider_name, quota_type)
    )
    """,
    # --- api_rate_limits (for rate limit dashboard) ---
    """
    CREATE TABLE IF NOT EXISTS api_rate_limits (
        id              SERIAL PRIMARY KEY,
        provider_name   TEXT UNIQUE NOT NULL,
        limit_value     INTEGER NOT NULL,
        reset_time      TIMESTAMP NOT NULL,
        alert_threshold INTEGER DEFAULT 80,
        created_at      TIMESTAMP DEFAULT NOW(),
        updated_at      TIMESTAMP DEFAULT NOW()
    )
    """,
    # --- api_usage_logs (for rate limit dashboard) ---
    """
    CREATE TABLE IF NOT EXISTS api_usage_logs (
        id              SERIAL PRIMARY KEY,
        provider_name   TEXT NOT NULL,
        endpoint        TEXT NOT NULL,
        status_code     INTEGER,
        response_time_ms INTEGER,
        created_at      TIMESTAMP DEFAULT NOW(),
        FOREIGN KEY (provider_name) REFERENCES api_rate_limits(provider_name) ON DELETE CASCADE
    )
    """,
]


def init_all_tables():
    """Initialize all database tables if they don't exist."""
    adapter = get_adapter()
    
    if Config.DB_TYPE.lower() == 'postgres':
        sql_list = _EXISTING_TABLES_SQL_POSTGRES
    else:
        sql_list = _EXISTING_TABLES_SQL
    
    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            for sql in sql_list:
                cursor.execute(sql)
            conn.commit()
        logger.info("All tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing tables: {e}", exc_info=True)
        raise


# Create indexes for rate limit tables
def init_rate_limit_indexes():
    """Create indexes for efficient rate limit querying."""
    adapter = get_adapter()
    
    index_sqls = [
        """
        CREATE INDEX IF NOT EXISTS idx_api_usage_logs_provider_created 
        ON api_usage_logs(provider_name, created_at DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_api_usage_logs_created 
        ON api_usage_logs(created_at DESC)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_api_rate_limits_provider 
        ON api_rate_limits(provider_name)
        """,
    ]
    
    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            for sql in index_sqls:
                cursor.execute(sql)
            conn.commit()
        logger.info("Rate limit indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}", exc_info=True)


# Initialize default rate limit entries
def init_default_rate_limits():
    """Initialize default rate limit entries for known providers."""
    adapter = get_adapter()
    
    defaults = [
        ('CoinGecko', 50, 80),
        ('TradingView', 3000, 80),
        ('SEC', 10, 85),
    ]
    
    try:
        with adapter.get_connection() as conn:
            cursor = conn.cursor()
            from datetime import datetime, timedelta
            
            for provider_name, limit_value, alert_threshold in defaults:
                # Check if provider already exists
                cursor.execute(
                    "SELECT id FROM api_rate_limits WHERE provider_name = %s" if Config.DB_TYPE.lower() == 'postgres' else "SELECT id FROM api_rate_limits WHERE provider_name = ?",
                    (provider_name,)
                )
                if cursor.fetchone():
                    continue
                
                # Set reset time based on provider
                reset_intervals = {
                    'CoinGecko': 3600,      # 1 hour
                    'TradingView': 86400,   # 24 hours
                    'SEC': 28800,           # 8 hours
                }
                reset_interval = reset_intervals.get(provider_name, 3600)
                reset_time = datetime.utcnow() + timedelta(seconds=reset_interval)
                
                cursor.execute(
                    "INSERT INTO api_rate_limits (provider_name, limit_value, reset_time, alert_threshold) VALUES (%s, %s, %s, %s)" if Config.DB_TYPE.lower() == 'postgres' else "INSERT INTO api_rate_limits (provider_name, limit_value, reset_time, alert_threshold) VALUES (?, ?, ?, ?)",
                    (provider_name, limit_value, reset_time.isoformat(), alert_threshold)
                )
            
            conn.commit()
        logger.info("Default rate limits initialized")
    except Exception as e:
        logger.error(f"Error initializing default rate limits: {e}", exc_info=True)
```