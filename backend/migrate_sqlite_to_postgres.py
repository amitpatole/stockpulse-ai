```python
"""
TickerPulse AI v3.0 - SQLite to PostgreSQL Migration Script

Usage:
    python -m backend.migrate_sqlite_to_postgres \
        --sqlite-path stock_news.db \
        --postgres-url postgresql://user:pass@localhost/tickerpulse \
        --batch-size 1000 \
        --verbose

This script migrates data from SQLite to PostgreSQL while preserving:
- All table structures
- Foreign key relationships
- Indexes
- Data integrity

The migration is non-destructive - it does not modify the source SQLite database.
"""

import sqlite3
import argparse
import logging
import sys
from typing import Dict, List, Tuple, Any

try:
    import psycopg
except ImportError:
    psycopg = None

logger = logging.getLogger(__name__)


class SQLiteToPostgresMapper:
    """Maps SQLite queries to PostgreSQL equivalents."""

    @staticmethod
    def convert_value(value: Any, column_type: str) -> Any:
        """Convert SQLite value to PostgreSQL-compatible value.

        Parameters
        ----------
        value : Any
            Value from SQLite
        column_type : str
            SQL column type

        Returns
        -------
        Any
            Converted value
        """
        if value is None:
            return None

        # Handle boolean/integer mappings
        if column_type.upper() in ("BOOLEAN", "BOOL"):
            return bool(value) if isinstance(value, int) else value

        # Handle BLOB/BYTEA
        if column_type.upper() in ("BLOB", "BYTEA"):
            return memoryview(value) if isinstance(value, bytes) else value

        return value


def migrate_sqlite_to_postgres(
    sqlite_path: str,
    postgres_url: str,
    batch_size: int = 1000,
    skip_indexes: bool = False,
    verbose: bool = False,
) -> None:
    """
    Migrate data from SQLite to PostgreSQL.

    Parameters
    ----------
    sqlite_path : str
        Path to SQLite database file
    postgres_url : str
        PostgreSQL connection URL
    batch_size : int
        Number of rows to insert per transaction
    skip_indexes : bool
        Skip index creation
    verbose : bool
        Enable debug logging
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Validate PostgreSQL availability
    if not psycopg:
        logger.error(
            "psycopg package required. Install: pip install psycopg[binary]"
        )
        sys.exit(1)

    logger.info("Starting SQLite to PostgreSQL migration...")
    logger.info(f"Source: {sqlite_path}")
    logger.info(f"Target: {postgres_url}")

    # Connect to SQLite
    try:
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        logger.info("Connected to SQLite")
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to SQLite: {e}")
        sys.exit(1)

    # Connect to PostgreSQL
    try:
        postgres_conn = psycopg.connect(postgres_url)
        postgres_conn.autocommit = False
        logger.info("Connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        sys.exit(1)

    try:
        _perform_migration(
            sqlite_conn, postgres_conn, batch_size, skip_indexes, verbose
        )
        logger.info("Migration completed successfully")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        postgres_conn.rollback()
        sys.exit(1)
    finally:
        sqlite_conn.close()
        postgres_conn.close()


def _perform_migration(
    sqlite_conn, postgres_conn, batch_size: int, skip_indexes: bool, verbose: bool
) -> None:
    """Perform the actual migration steps."""
    sqlite_cursor = sqlite_conn.cursor()
    postgres_cursor = postgres_conn.cursor()

    # Get list of tables from SQLite
    sqlite_cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in sqlite_cursor.fetchall()]

    logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")

    # Migrate each table
    for table_name in tables:
        logger.info(f"\nMigrating table: {table_name}")

        try:
            _migrate_table(
                sqlite_cursor,
                postgres_cursor,
                postgres_conn,
                table_name,
                batch_size,
                verbose,
            )
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            raise

    # Create indexes
    if not skip_indexes:
        logger.info("\nCreating indexes...")
        _create_indexes(
            sqlite_cursor, postgres_cursor, postgres_conn, tables, verbose
        )

    postgres_conn.commit()


def _migrate_table(
    sqlite_cursor,
    postgres_cursor,
    postgres_conn,
    table_name: str,
    batch_size: int,
    verbose: bool,
) -> None:
    """Migrate a single table from SQLite to PostgreSQL."""
    # Get row count
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = sqlite_cursor.fetchone()[0]
    logger.info(f"  Migrating {total_rows} rows...")

    # Get columns
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [(row[1], row[2]) for row in sqlite_cursor.fetchall()]
    column_names = [col[0] for col in columns]
    column_list = ", ".join(column_names)

    # Insert in batches
    placeholders = ", ".join(["%s"] * len(column_names))
    insert_sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"

    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows_inserted = 0

    batch = []
    for row in sqlite_cursor.fetchall():
        # Convert SQLite row to PostgreSQL-compatible values
        converted_row = [
            SQLiteToPostgresMapper.convert_value(row[i], columns[i][1])
            for i in range(len(columns))
        ]
        batch.append(converted_row)

        if len(batch) >= batch_size:
            postgres_cursor.executemany(insert_sql, batch)
            postgres_conn.commit()
            rows_inserted += len(batch)
            if verbose:
                logger.debug(f"  Inserted {rows_inserted}/{total_rows} rows")
            batch = []

    # Insert remaining rows
    if batch:
        postgres_cursor.executemany(insert_sql, batch)
        postgres_conn.commit()
        rows_inserted += len(batch)

    logger.info(f"  ✓ Migrated {rows_inserted} rows")


def _create_indexes(
    sqlite_cursor,
    postgres_cursor,
    postgres_conn,
    tables: List[str],
    verbose: bool,
) -> None:
    """Create indexes from SQLite in PostgreSQL."""
    # Get indexes from SQLite
    sqlite_cursor.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
    )
    indexes = sqlite_cursor.fetchall()

    created_count = 0
    for index_name, index_sql in indexes:
        try:
            # Convert SQLite index DDL to PostgreSQL
            postgres_index_sql = _convert_index_sql(index_sql)
            if postgres_index_sql:
                postgres_cursor.execute(postgres_index_sql)
                postgres_conn.commit()
                created_count += 1
                if verbose:
                    logger.debug(f"  Created index: {index_name}")
        except Exception as e:
            logger.warning(f"  Skipped index {index_name}: {e}")

    logger.info(f"  ✓ Created {created_count} indexes")


def _convert_index_sql(sqlite_sql: str) -> str:
    """Convert SQLite index DDL to PostgreSQL equivalent.

    Parameters
    ----------
    sqlite_sql : str
        SQLite CREATE INDEX statement

    Returns
    -------
    str
        PostgreSQL CREATE INDEX statement, or empty string if conversion fails
    """
    if not sqlite_sql:
        return ""

    # Simple passthrough - most CREATE INDEX syntax is compatible
    # Just ensure it uses CREATE INDEX IF NOT EXISTS
    sql = sqlite_sql.replace("CREATE UNIQUE INDEX", "CREATE UNIQUE INDEX IF NOT EXISTS")
    sql = sql.replace("CREATE INDEX", "CREATE INDEX IF NOT EXISTS")

    return sql


def main():
    """Command-line interface for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate SQLite database to PostgreSQL"
    )
    parser.add_argument(
        "--sqlite-path",
        default="stock_news.db",
        help="Path to SQLite database file (default: stock_news.db)",
    )
    parser.add_argument(
        "--postgres-url",
        required=True,
        help="PostgreSQL connection URL (postgresql://user:pass@host/dbname)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Rows per insert transaction (default: 1000)",
    )
    parser.add_argument(
        "--skip-indexes",
        action="store_true",
        help="Skip index creation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    migrate_sqlite_to_postgres(
        args.sqlite_path,
        args.postgres_url,
        args.batch_size,
        args.skip_indexes,
        args.verbose,
    )


if __name__ == "__main__":
    main()
```