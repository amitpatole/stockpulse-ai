```python
"""
TickerPulse AI v3.0 - Database Adapter Factory
Provides factory function for multi-database support (SQLite, PostgreSQL).
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_db_adapter(db_type=None):
    """
    Factory function to create appropriate database adapter.

    Parameters
    ----------
    db_type : str, optional
        Database type ('sqlite' or 'postgres'). Defaults to Config.DB_TYPE.

    Returns
    -------
    DatabaseAdapter
        Instance of SQLiteAdapter or PostgresAdapter
    """
    from backend.config import Config

    db_type = (db_type or Config.DB_TYPE).lower()

    if db_type == "sqlite":
        from backend.adapters.sqlite_adapter import SQLiteAdapter

        db_path = Config.DB_PATH
        logger.info(f"Using SQLite adapter: {db_path}")
        return SQLiteAdapter(db_path)

    elif db_type == "postgres":
        from backend.adapters.postgres_adapter import PostgresAdapter

        database_url = Config.DATABASE_URL
        pool_size = Config.DB_POOL_SIZE
        logger.info(f"Using PostgreSQL adapter with pool size {pool_size}")
        return PostgresAdapter(database_url, pool_size)

    else:
        raise ValueError(
            f"Unsupported database type: {db_type}. Use 'sqlite' or 'postgres'."
        )


__all__ = ["get_db_adapter"]
```