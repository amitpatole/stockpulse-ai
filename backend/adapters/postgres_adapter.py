```python
import logging
from typing import Any, List, Optional, Tuple

try:
    import psycopg
    from psycopg_pool import ConnectionPool
except ImportError:
    raise ImportError(
        "psycopg3 required for PostgreSQL support. "
        "Install with: pip install psycopg[binary] psycopg-pool"
    )

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter using psycopg 3."""
    
    def __init__(self, connection_string: str, min_size: int = 1, max_size: int = 10) -> None:
        """Initialize PostgreSQL adapter.
        
        Args:
            connection_string: PostgreSQL connection string (postgresql://user:pass@host/dbname)
            min_size: Minimum pool connections
            max_size: Maximum pool connections
        """
        self.connection_string = connection_string
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[ConnectionPool] = None
    
    def connect(self) -> None:
        """Establish PostgreSQL connection pool."""
        try:
            self.pool = ConnectionPool(
                self.connection_string,
                min_size=self.min_size,
                max_size=self.max_size,
                open=True
            )
            logger.info(
                f"PostgreSQL connection pool established "
                f"(min={self.min_size}, max={self.max_size})"
            )
        except psycopg.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close PostgreSQL connection pool."""
        if self.pool:
            try:
                self.pool.close()
                logger.info("PostgreSQL connection pool closed")
            except psycopg.Error as e:
                logger.error(f"Error closing pool: {e}")
                raise
    
    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        """Execute query without returning results."""
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                conn.commit()
        except psycopg.Error as e:
            logger.error(f"Execute error: {e}")
            raise
    
    def executemany(self, query: str, params: List[Tuple[Any, ...]]) -> None:
        """Execute multiple queries."""
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    for param_tuple in params:
                        cur.execute(query, param_tuple)
                conn.commit()
        except psycopg.Error as e:
            logger.error(f"ExecuteMany error: {e}")
            raise
    
    def fetchone(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Any]:
        """Fetch single row."""
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    row = cur.fetchone()
                    return row
        except psycopg.Error as e:
            logger.error(f"FetchOne error: {e}")
            raise
    
    def fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> List[Any]:
        """Fetch all rows."""
        if not self.pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    return rows
        except psycopg.Error as e:
            logger.error(f"FetchAll error: {e}")
            raise
    
    def commit(self) -> None:
        """Commit transaction (pool manages per-connection)."""
        pass
    
    def rollback(self) -> None:
        """Rollback transaction (pool manages per-connection)."""
        pass
```