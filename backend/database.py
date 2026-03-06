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
    # Watchlist Groups (new)
    """
    CREATE TABLE IF NOT EXISTS watchlist_groups (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL UNIQUE,
        description     TEXT,
        color           TEXT DEFAULT '#6366f1',
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # Stocks (modified with group support)
    """
    CREATE TABLE IF NOT EXISTS stocks (
        ticker          TEXT PRIMARY KEY,
        name            TEXT,
        market          TEXT DEFAULT 'US',
        group_id        INTEGER REFERENCES watchlist_groups(id) ON DELETE SET NULL,
        sort_order      INTEGER DEFAULT 0,
        added_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active          INTEGER DEFAULT 1
    )
    """,
]

_INDEXES_SQL = [
    """CREATE INDEX IF NOT EXISTS idx_stocks_group_order ON stocks(group_id, sort_order)""",
]


def init_db():
    """Initialize database tables and indexes."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Create all tables
        for sql in _TABLES_SQL:
            cursor.execute(sql)
        
        # Create all indexes
        for sql in _INDEXES_SQL:
            cursor.execute(sql)
        
        logger.info("Database initialized successfully")


if __name__ == '__main__':
    init_db()
```