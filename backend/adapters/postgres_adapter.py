```python
"""
TickerPulse AI v3.0 - PostgreSQL Database Adapter
Uses psycopg3 with connection pooling for production use.
"""

import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional, List, Tuple

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

    def __init__(self, database_url: str, pool_size: int = 10) -> None:
        """Initialize PostgreSQL adapter.

        Parameters
        ----------
        database_url : str
            PostgreSQL connection string (postgresql://user:password@host:port/database)
        pool_size : int
            Maximum connections in pool (default: 10)
            
        Raises
        ------
        ImportError
            If psycopg is not installed
        """
        if not psycopg:
            raise ImportError(
                "psycopg package required for PostgreSQL support. "
                "Install: pip install psycopg[binary]"
            )

        self.database_url = database_url
        self.pool_size = pool_size
        self._pool: Optional[Any] = None

    def connect(self) -> None:
        """Initialize PostgreSQL connection pool."""
        assert SimpleConnectionPool is not None
        self._pool = SimpleConnectionPool(
            self.database_url, min_size=1, max_size=self.pool_size
        )
        logger.info(f"Connected to PostgreSQL with pool size {self.pool_size}")

    def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self._pool:
            self._pool.close()
            self._pool = None
            logger.info("Disconnected from PostgreSQL")

    @contextmanager
    def get_connection(self) -> Generator[Any, None, None]:
        """Get connection from pool.
        
        Yields
        ------
        Any
            PostgreSQL connection object from pool
        """
        if self._pool is None:
            self.connect()
        assert self._pool is not None
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def execute(
        self, connection: Any, sql: str, params: Tuple = ()
    ) -> Any:
        """Execute SQL statement with psycopg3.
        
        Parameters
        ----------
        connection : Any
            PostgreSQL connection from pool
        sql : str
            SQL statement with %s placeholders
        params : Tuple
            Query parameters
            
        Returns
        -------
        Any
            Cursor object with executed statement
        """
        cursor = connection.cursor()
        cursor.execute(sql, params)
        return cursor

    def executemany(
        self, connection: Any, sql: str, params: List[Tuple]
    ) -> Any:
        """Execute SQL statement with multiple parameter sets.
        
        Parameters
        ----------
        connection : Any
            PostgreSQL connection from pool
        sql : str
            SQL statement with %s placeholders
        params : List[Tuple]
            List of parameter tuples
            
        Returns
        -------
        Any
            Cursor object with executed statement
        """
        cursor = connection.cursor()
        cursor.executemany(sql, params)
        return cursor

    def fetchone(self, cursor: Any) -> Optional[Any]:
        """Fetch one row.
        
        Parameters
        ----------
        cursor : Any
            PostgreSQL cursor
            
        Returns
        -------
        Optional[Any]
            Single row or None
        """
        return cursor.fetchone()

    def fetchall(self, cursor: Any) -> List[Any]:
        """Fetch all rows.
        
        Parameters
        ----------
        cursor : Any
            PostgreSQL cursor
            
        Returns
        -------
        List[Any]
            List of rows
        """
        return cursor.fetchall()

    def commit(self, connection: Any) -> None:
        """Commit transaction.
        
        Parameters
        ----------
        connection : Any
            PostgreSQL connection
        """
        connection.commit()

    def rollback(self, connection: Any) -> None:
        """Rollback transaction.
        
        Parameters
        ----------
        connection : Any
            PostgreSQL connection
        """
        connection.rollback()

    def close(self, connection: Any) -> None:
        """Close or return connection.
        
        For pooled connections, this is a no-op as connections
        are managed by the pool. Use putconn() explicitly if needed.
        
        Parameters
        ----------
        connection : Any
            PostgreSQL connection
        """
        pass

    def initialize_tables(self, connection: Any) -> None:
        """Create all tables for PostgreSQL.
        
        Parameters
        ----------
        connection : Any
            PostgreSQL connection
        """
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
```