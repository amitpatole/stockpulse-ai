```python
import os
import logging
from typing import Literal, Union

from .base import DatabaseAdapter

logger = logging.getLogger(__name__)


def get_db_adapter(db_type: Union[Literal["sqlite", "postgres"], None] = None) -> DatabaseAdapter:
    """Factory function to get database adapter based on DB_TYPE env var.
    
    Args:
        db_type: Override environment variable (sqlite or postgres)
        
    Returns:
        DatabaseAdapter instance (SQLiteAdapter or PostgresAdapter)
        
    Raises:
        ValueError: If unsupported db_type or missing required env vars
        
    Environment Variables:
        DB_TYPE: "sqlite" (default) or "postgres"
        DATABASE_PATH: Path to SQLite file (default: app.db)
        DATABASE_URL: PostgreSQL connection string (required if DB_TYPE=postgres)
        DB_POOL_MIN: Min pool size for PostgreSQL (default: 1)
        DB_POOL_MAX: Max pool size for PostgreSQL (default: 10)
    """
    db_type = db_type or os.getenv("DB_TYPE", "sqlite").lower()
    
    if db_type == "postgres":
        from .postgres_adapter import PostgresAdapter
        
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            raise ValueError(
                "DATABASE_URL environment variable required for PostgreSQL. "
                "Format: postgresql://user:password@host:port/database"
            )
        
        min_size = int(os.getenv("DB_POOL_MIN", "1"))
        max_size = int(os.getenv("DB_POOL_MAX", "10"))
        
        logger.info(f"Initializing PostgreSQL adapter (pool: {min_size}-{max_size})")
        return PostgresAdapter(connection_string, min_size=min_size, max_size=max_size)
    
    elif db_type == "sqlite":
        from .sqlite_adapter import SQLiteAdapter
        
        database_path = os.getenv("DATABASE_PATH", "app.db")
        logger.info(f"Initializing SQLite adapter ({database_path})")
        return SQLiteAdapter(database_path)
    
    else:
        raise ValueError(
            f"Unsupported database type: {db_type}. "
            f"Valid options: sqlite, postgres"
        )


__all__ = ["DatabaseAdapter", "get_db_adapter"]
```