```python
"""
TickerPulse AI v3.0 - SQLite Database Adapter
Wraps sqlite3 for thread-safe access with familiar API.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional, List, Tuple

from backend.adapters.base import DatabaseAdapter

logger = logging.getLogger(__name__)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter using sqlite3 module."""

    def __init__(self, db_path: str) -> None:
        """Initialize SQLite adapter.
        
        Parameters
        ----------
        db_path : str
            Path to SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Initialize SQLite connection."""
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        assert self._connection is not None
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA foreign_keys=ON")
        logger.info(f"Connected to SQLite database at {self.db_path}")

    def disconnect(self) -> None:
        """Close SQLite connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Disconnected from SQLite database")

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield SQLite connection."""
        if self._connection is None:
            self.connect()
        assert self._connection is not None
        try:
            yield self._connection
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

    def execute(
        self, connection: sqlite3.Connection, sql: str, params: Tuple = ()
    ) -> sqlite3.Cursor:
        """Execute SQL statement.
        
        Parameters
        ----------
        connection : sqlite3.Connection
            Database connection
        sql : str
            SQL statement with ? placeholders
        params : Tuple
            Query parameters
            
        Returns
        -------
        sqlite3.Cursor
            Cursor with executed statement
        """
        cursor = connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def executemany(
        self, connection: sqlite3.Connection, sql: str, params: List[Tuple]
    ) -> sqlite3.Cursor:
        """Execute SQL statement with multiple parameter sets.
        
        Parameters
        ----------
        connection : sqlite3.Connection
            Database connection
        sql : str
            SQL statement with ? placeholders
        params : List[Tuple]
            List of parameter tuples
            
        Returns
        -------
        sqlite3.Cursor
            Cursor with executed statement
        """
        cursor = connection.cursor()
        cursor.executemany(sql, params)
        return cursor

    def fetchone(self, cursor: sqlite3.Cursor) -> Optional[sqlite3.Row]:
        """Fetch one row.
        
        Parameters
        ----------
        cursor : sqlite3.Cursor
            Database cursor
            
        Returns
        -------
        Optional[sqlite3.Row]
            Single row or None
        """
        return cursor.fetchone()

    def fetchall(self, cursor: sqlite3.Cursor) -> List[sqlite3.Row]:
        """Fetch all rows.
        
        Parameters
        ----------
        cursor : sqlite3.Cursor
            Database cursor
            
        Returns
        -------
        List[sqlite3.Row]
            List of rows
        """
        return cursor.fetchall()

    def commit(self, connection: sqlite3.Connection) -> None:
        """Commit transaction.
        
        Parameters
        ----------
        connection : sqlite3.Connection
            Database connection
        """
        connection.commit()

    def rollback(self, connection: sqlite3.Connection) -> None:
        """Rollback transaction.
        
        Parameters
        ----------
        connection : sqlite3.Connection
            Database connection
        """
        connection.rollback()

    def close(self, connection: sqlite3.Connection) -> None:
        """Close connection.
        
        Parameters
        ----------
        connection : sqlite3.Connection
            Database connection
        """
        connection.close()

    def initialize_tables(self, connection: sqlite3.Connection) -> None:
        """Create all tables for SQLite.
        
        Parameters
        ----------
        connection : sqlite3.Connection
            Database connection
        """
        from backend.database import (
            _EXISTING_TABLES_SQL,
            _NEW_TABLES_SQL,
            _INDEXES_SQL,
        )

        cursor = connection.cursor()
        for sql in _EXISTING_TABLES_SQL:
            cursor.execute(sql)
        for sql in _NEW_TABLES_SQL:
            cursor.execute(sql)
        for sql in _INDEXES_SQL:
            cursor.execute(sql)
        connection.commit()
        logger.info("SQLite tables initialized")
```