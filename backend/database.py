```python
from typing import List, Dict, Optional
import sqlite3
import logging
from contextlib import contextmanager
from backend.config import Config

logger = logging.getLogger(__name__)

# New tables
_CREATE_ECONOMIC_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS economic_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    event_date TIMESTAMP,
    impact_rating INTEGER,
    ticker_id INTEGER,
    FOREIGN KEY (ticker_id) REFERENCES crypto_tickers (id)
)
"""

_CREATE_CRYPTO_TICKERS_TABLE = """
CREATE TABLE IF NOT EXISTS crypto_tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_CREATE_CRYPTO_PRICES_TABLE = """
CREATE TABLE IF NOT EXISTS crypto_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER,
    price REAL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticker_id) REFERENCES crypto_tickers (id)
)
"""

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
        last_check  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- economic_events ---
    _CREATE_ECONOMIC_EVENTS_TABLE
]

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
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()
```