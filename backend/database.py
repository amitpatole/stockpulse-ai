```python
"""
TickerPulse AI v3.0 - Database Connection Manager
Thread-safe database helper with context-manager support and table initialisation.
"""

import os
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.config import Config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

if Config.DB_TYPE == 'postgresql':
    SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
else:
    from backend.database import get_db_connection

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
        last_check  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]
```