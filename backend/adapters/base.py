```python
"""
TickerPulse AI v3.0 - Database Adapter Base Class
Defines interface for database backends (SQLite, PostgreSQL, etc.).
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    All database operations (SQLite, PostgreSQL, etc.) implement this interface.
    """

    @abstractmethod
    def connect(self):
        """Initialize database connection or connection pool."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close database connection or connection pool."""
        pass

    @contextmanager
    @abstractmethod
    def get_connection(self):
        """Get a database connection (yields connection object)."""
        pass

    @abstractmethod
    def execute(self, connection, sql, params=()):
        """Execute a single SQL statement and return cursor."""
        pass

    @abstractmethod
    def executemany(self, connection, sql, params):
        """Execute SQL statement with multiple parameter sets."""
        pass

    @abstractmethod
    def fetchone(self, cursor):
        """Fetch one row from cursor."""
        pass

    @abstractmethod
    def fetchall(self, cursor):
        """Fetch all rows from cursor."""
        pass

    @abstractmethod
    def commit(self, connection):
        """Commit transaction."""
        pass

    @abstractmethod
    def rollback(self, connection):
        """Rollback transaction."""
        pass

    @abstractmethod
    def close(self, connection):
        """Close or return connection."""
        pass

    @abstractmethod
    def initialize_tables(self, connection):
        """Create all required tables if they don't exist."""
        pass