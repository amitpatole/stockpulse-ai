```python
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple
from contextlib import contextmanager


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.
    
    All database operations go through this interface, allowing
    pluggable SQLite or PostgreSQL backends.
    """
    
    @abstractmethod
    def connect(self) -> None:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection."""
        pass
    
    @abstractmethod
    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        """Execute a query without returning results (DML operations).
        
        Args:
            query: SQL query with ? or %s placeholders
            params: Tuple of parameters to bind
        """
        pass
    
    @abstractmethod
    def executemany(self, query: str, params: List[Tuple[Any, ...]]) -> None:
        """Execute multiple queries (bulk DML).
        
        Args:
            query: SQL query with ? or %s placeholders
            params: List of parameter tuples
        """
        pass
    
    @abstractmethod
    def fetchone(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Any]:
        """Fetch a single row from a query.
        
        Args:
            query: SQL SELECT query
            params: Tuple of parameters to bind
            
        Returns:
            Row object or None if no results
        """
        pass
    
    @abstractmethod
    def fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> List[Any]:
        """Fetch all rows from a query.
        
        Args:
            query: SQL SELECT query
            params: Tuple of parameters to bind
            
        Returns:
            List of row objects
        """
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit current transaction."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback current transaction."""
        pass
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions.
        
        Automatically commits on success, rolls back on exception.
        
        Usage:
            with adapter.transaction():
                adapter.execute("UPDATE ...", (...,))
        """
        try:
            yield
            self.commit()
        except Exception:
            self.rollback()
            raise
```