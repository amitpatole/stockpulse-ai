```python
"""
TickerPulse AI v3.0 - SQLite Database Adapter
Wraps sqlite3 for thread-safe access with familiar API.
"""

import sqlite3
import logging
from contextlib import contextmanager

from backend.adapters.base import DatabaseAdapter

logger = logging.getLogger(__name__)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter using sqlite3 module."""

    def __init__(self, db_path):
        self.db_path = db_path
        self._connection = None

    def connect(self):
        """Initialize SQLite connection."""
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        logger.info(f"Connected to SQLite database at {self.db_path}")

    def disconnect(self):
        """Close SQLite connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnected from SQLite database")

    @contextmanager
    def get_connection(self):
        """Yield SQLite connection."""
        if self._connection is None:
            self.connect()
        try:
            yield self._connection
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def execute(self, connection, sql, params=()):
        """Execute SQL statement."""
        cursor = connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def executemany(self, connection, sql, params):
        """Execute SQL statement with multiple parameter sets."""
        cursor = connection.cursor()
        cursor.executemany(sql, params)
        return cursor

    def fetchone(self, cursor):
        """Fetch one row."""
        return cursor.fetchone()

    def fetchall(self, cursor):
        """Fetch all rows."""
        return cursor.fetchall()

    def commit(self, connection):
        """Commit transaction."""
        connection.commit()

    def rollback(self, connection):
        """Rollback transaction."""
        connection.rollback()

    def close(self, connection):
        """Close connection."""
        connection.close()

    def initialize_tables(self, connection):
        """Create all tables for SQLite."""
        from backend.database import _EXISTING_TABLES_SQL, _NEW_TABLES_SQL, _INDEXES_SQL

        cursor = connection.cursor()
        for sql in _EXISTING_TABLES_SQL:
            cursor.execute(sql)
        for sql in _NEW_TABLES_SQL:
            cursor.execute(sql)
        for sql in _INDEXES_SQL:
            cursor.execute(sql)
        connection.commit()
        logger.info("SQLite tables initialized")