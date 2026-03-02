```python
"""
TickerPulse AI v3.0 - PostgreSQL Database Adapter
Uses psycopg3 with connection pooling for production use.
"""

import logging
from contextlib import contextmanager

try:
    import psycopg
    from psycopg_pool import SimpleConnectionPool
except ImportError:
    psycopg = None
    SimpleConnectionPool = None

from backend.adapters.base import DatabaseAdapter

logger = logging.getLogger(__name__)


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter using psycopg3 with connection pooling."""

    def __init__(self, database_url, pool_size=10):
        """
        Initialize PostgreSQL adapter.

        Parameters
        ----------
        database_url : str
            PostgreSQL connection string
        pool_size : int
            Maximum connections in pool (default: 10)
        """
        if not psycopg:
            raise ImportError(
                "psycopg package required for PostgreSQL support. "
                "Install: pip install psycopg[binary]"
            )

        self.database_url = database_url
        self.pool_size = pool_size
        self._pool = None

    def connect(self):
        """Initialize PostgreSQL connection pool."""
        self._pool = SimpleConnectionPool(
            self.database_url, min_size=1, max_size=self.pool_size
        )
        logger.info(f"Connected to PostgreSQL with pool size {self.pool_size}")

    def disconnect(self):
        """Close PostgreSQL connection pool."""
        if self._pool:
            self._pool.close()
            self._pool = None
            logger.info("Disconnected from PostgreSQL")

    @contextmanager
    def get_connection(self):
        """Get connection from pool."""
        if self._pool is None:
            self.connect()
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def execute(self, connection, sql, params=()):
        """Execute SQL statement with psycopg3."""
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
        """Close connection (returned to pool)."""
        pass

    def initialize_tables(self, connection):
        """Create all tables for PostgreSQL."""
        from backend.database import (
            _EXISTING_TABLES_SQL_POSTGRES,
            _NEW_TABLES_SQL_POSTGRES,
            _INDEXES_SQL_POSTGRES,
        )

        cursor = connection.cursor()
        for sql in _EXISTING_TABLES_SQL_POSTGRES:
            cursor.execute(sql)
        for sql in _NEW_TABLES_SQL_POSTGRES:
            cursor.execute(sql)
        for sql in _INDEXES_SQL_POSTGRES:
            cursor.execute(sql)
        connection.commit()
        logger.info("PostgreSQL tables initialized")