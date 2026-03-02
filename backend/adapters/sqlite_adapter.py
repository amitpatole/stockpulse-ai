```python
import sqlite3
import logging
from typing import Any, List, Optional, Tuple

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter using sqlite3 module."""
    
    def __init__(self, database_path: str) -> None:
        """Initialize SQLite adapter.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self) -> None:
        """Establish SQLite connection with WAL mode enabled."""
        try:
            self.conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=10.0
            )
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
            logger.info(f"SQLite connection established: {self.database_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close SQLite connection."""
        if self.conn:
            try:
                self.conn.close()
                logger.info("SQLite connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing connection: {e}")
                raise
    
    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        """Execute query without returning results."""
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            cursor.close()
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Execute error: {e}")
            raise
    
    def executemany(self, query: str, params: List[Tuple[Any, ...]]) -> None:
        """Execute multiple queries."""
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            cursor = self.conn.cursor()
            cursor.executemany(query, params)
            self.conn.commit()
            cursor.close()
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"ExecuteMany error: {e}")
            raise
    
    def fetchone(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Any]:
        """Fetch single row."""
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            cursor.close()
            return row
        except sqlite3.Error as e:
            logger.error(f"FetchOne error: {e}")
            raise
    
    def fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> List[Any]:
        """Fetch all rows."""
        if not self.conn:
            raise RuntimeError("Database not connected. Call connect() first.")
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except sqlite3.Error as e:
            logger.error(f"FetchAll error: {e}")
            raise
    
    def commit(self) -> None:
        """Commit transaction."""
        if self.conn:
            try:
                self.conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Commit error: {e}")
                raise
    
    def rollback(self) -> None:
        """Rollback transaction."""
        if self.conn:
            try:
                self.conn.rollback()
            except sqlite3.Error as e:
                logger.error(f"Rollback error: {e}")
                raise
```