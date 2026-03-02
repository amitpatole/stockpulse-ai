```python
"""
Migration 0044: Add asset_type column to stocks table for crypto support.

This migration adds the `asset_type` column ('stock'|'crypto'|'etf') to the stocks
table to distinguish between different asset classes while maintaining backward
compatibility (default 'stock').
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def up(cursor: Any) -> None:
    """Add asset_type column to stocks table."""
    try:
        cursor.execute("PRAGMA table_info(stocks)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'asset_type' not in columns:
            cursor.execute("""
                ALTER TABLE stocks ADD COLUMN asset_type TEXT DEFAULT 'stock'
            """)
            logger.info("✓ Added asset_type column to stocks table")
    except Exception as e:
        logger.error(f"Failed to add asset_type column: {e}")
        raise


def down(cursor: Any) -> None:
    """Revert: Remove asset_type column from stocks table."""
    # SQLite doesn't support DROP COLUMN easily, so we skip downgrade
    # In production, use a backup + restore strategy
    logger.warning("Downgrade not supported for this migration (SQLite limitation)")
```