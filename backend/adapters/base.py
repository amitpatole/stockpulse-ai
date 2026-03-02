```python
"""
TickerPulse AI v3.0 - Database Adapter Base Class
Defines interface for database backends (SQLite, PostgreSQL, etc.).
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator, Optional, List, Tuple


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    All database operations (SQLite, PostgreSQL, etc.) implement this interface.
    """

    @abstractmethod
    def connect(self) -> None:
        """Initialize database connection or connection pool."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection or connection pool."""
        pass

    @contextmanager
    @abstractmethod
    def get_connection(self) -> Generator[Any, None, None]:
        """Get a database connection (yields connection object)."""
        pass

    @abstractmethod
    def execute(self, connection: Any, sql: str, params: Tuple = ()) -> Any:
        """Execute a single SQL statement and return cursor.
        
        Parameters
        ----------
        connection : Any
            Database connection object
        sql : str
            SQL statement with parameterized placeholders
        params : Tuple
            Query parameters (default: empty tuple)
            
        Returns
        -------
        Any
            Cursor object with executed statement
        """
        pass

    @abstractmethod
    def executemany(self, connection: Any, sql: str, params: List[Tuple]) -> Any:
        """Execute SQL statement with multiple parameter sets.
        
        Parameters
        ----------
        connection : Any
            Database connection object
        sql : str
            SQL statement with parameterized placeholders
        params : List[Tuple]
            List of parameter tuples
            
        Returns
        -------
        Any
            Cursor object
        """
        pass

    @abstractmethod
    def fetchone(self, cursor: Any) -> Optional[Any]:
        """Fetch one row from cursor.
        
        Parameters
        ----------
        cursor : Any
            Database cursor object
            
        Returns
        -------
        Optional[Any]
            Single row or None if no rows
        """
        pass

    @abstractmethod
    def fetchall(self, cursor: Any) -> List[Any]:
        """Fetch all rows from cursor.
        
        Parameters
        ----------
        cursor : Any
            Database cursor object
            
        Returns
        -------
        List[Any]
            List of rows (empty list if no rows)
        """
        pass

    @abstractmethod
    def commit(self, connection: Any) -> None:
        """Commit transaction.
        
        Parameters
        ----------
        connection : Any
            Database connection object
        """
        pass

    @abstractmethod
    def rollback(self, connection: Any) -> None:
        """Rollback transaction.
        
        Parameters
        ----------
        connection : Any
            Database connection object
        """
        pass

    @abstractmethod
    def close(self, connection: Any) -> None:
        """Close or return connection.
        
        Parameters
        ----------
        connection : Any
            Database connection object
        """
        pass

    @abstractmethod
    def initialize_tables(self, connection: Any) -> None:
        """Create all required tables if they don't exist.
        
        Parameters
        ----------
        connection : Any
            Database connection object
        """
        pass
```