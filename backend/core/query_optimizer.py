```python
"""
Query Optimizer - Utility functions for optimized database queries.

This module provides reusable patterns for:
- Batch queries (avoid N+1 patterns)
- Indexed filtering (leverage composite indexes)
- Pagination with minimal overhead
- Query profiling and analysis
"""

import sqlite3
import logging
from typing import List, Dict, Tuple, Optional, Any
from contextlib import contextmanager

from backend.config import Config
from backend.database import db_session

logger = logging.getLogger(__name__)


# ============================================================================
# Batch Query Utilities
# ============================================================================

def get_batch_by_keys(
    table: str,
    key_column: str,
    keys: List[str],
    columns: Optional[List[str]] = None,
    batch_size: int = 100
) -> Dict[str, Dict[str, Any]]:
    """
    Fetch multiple rows by key efficiently, handling large lists.

    Splits large key lists into batches to avoid query string limits.

    Args:
        table: Table name to query
        key_column: Primary key column name (e.g., 'ticker')
        keys: List of key values to fetch
        columns: Specific columns to select (default: all)
        batch_size: Max keys per query (default: 100)

    Returns:
        Dict mapping key values to row dictionaries
    """
    if not keys:
        return {}

    columns_str = ', '.join(columns) if columns else '*'
    results: Dict[str, Dict[str, Any]] = {}

    with db_session() as conn:
        cursor = conn.cursor()
        for i in range(0, len(keys), batch_size):
            batch = keys[i:i + batch_size]
            placeholders = ','.join('?' * len(batch))
            sql = f"SELECT {columns_str} FROM {table} WHERE {key_column} IN ({placeholders})"

            try:
                cursor.execute(sql, batch)
                for row in cursor.fetchall():
                    # Use the key_column value as the result key
                    key = row[key_column]
                    results[key] = dict(row)
            except Exception as e:
                logger.error(f"Batch query failed for {table}: {e}")

    return results


def get_batch_by_ids(
    table: str,
    ids: List[int],
    columns: Optional[List[str]] = None,
    batch_size: int = 100
) -> Dict[int, Dict[str, Any]]:
    """
    Fetch multiple rows by integer ID efficiently.

    Convenience wrapper for get_batch_by_keys with id column.

    Args:
        table: Table name to query
        ids: List of integer IDs to fetch
        columns: Specific columns to select
        batch_size: Max IDs per query

    Returns:
        Dict mapping ID to row dictionaries
    """
    return get_batch_by_keys(table, 'id', ids, columns, batch_size)


# ============================================================================
# Filtered Query Utilities
# ============================================================================

def get_filtered_with_pagination(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 20,
    offset: int = 0,
    order_by: Optional[str] = None,
    columns: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch paginated rows with optional filtering.

    Executes two queries: COUNT (metadata) + SELECT (data).
    Uses parameterized queries to prevent SQL injection.

    Args:
        table: Table name
        filters: Dict of {column: value} for WHERE clause (AND conditions)
        limit: Rows per page (1-100)
        offset: Starting row
        order_by: Optional ORDER BY clause (e.g., 'created_at DESC')
        columns: Specific columns to select (default: all)

    Returns:
        Tuple of (rows as dicts, total count)
    """
    columns_str = ', '.join(columns) if columns else '*'

    # Build WHERE clause
    where_parts = []
    params = []
    if filters:
        for col, val in filters.items():
            where_parts.append(f"{col} = ?")
            params.append(val)

    where_clause = " WHERE " + " AND ".join(where_parts) if where_parts else ""

    with db_session() as conn:
        cursor = conn.cursor()

        # Get total count
        count_sql = f"SELECT COUNT(*) as cnt FROM {table}{where_clause}"
        try:
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['cnt']
        except Exception as e:
            logger.error(f"Count query failed: {e}")
            total_count = 0

        # Get paginated data
        order_clause = f" ORDER BY {order_by}" if order_by else ""
        data_sql = f"SELECT {columns_str} FROM {table}{where_clause}{order_clause} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        try:
            cursor.execute(data_sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Select query failed: {e}")
            rows = []

    return rows, total_count


# ============================================================================
# Specialized Query Patterns
# ============================================================================

def get_active_records(
    table: str,
    limit: int = 20,
    offset: int = 0,
    filter_market: Optional[str] = None,
    order_by: str = 'ticker'
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch active (soft-deleted=0) records with pagination.

    Optimized for stocks table pattern: WHERE active = 1 AND market = ?

    Args:
        table: Table name
        limit: Rows per page
        offset: Starting row
        filter_market: Optional market filter (e.g., 'US', 'India')
        order_by: Column to sort by

    Returns:
        Tuple of (rows, total_count)
    """
    filters = {'active': 1}
    if filter_market and filter_market != 'All':
        filters['market'] = filter_market

    return get_filtered_with_pagination(
        table,
        filters=filters,
        limit=limit,
        offset=offset,
        order_by=order_by
    )


def get_recent_records(
    table: str,
    ticker: Optional[str] = None,
    days: int = 30,
    limit: int = 20,
    offset: int = 0,
    timestamp_column: str = 'created_at'
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch recent records by ticker with pagination.

    Optimized for research_briefs and news patterns.

    Args:
        table: Table name
        ticker: Optional ticker filter
        days: How many days back to fetch
        limit: Rows per page
        offset: Starting row
        timestamp_column: Name of timestamp column

    Returns:
        Tuple of (rows, total_count)
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # Build dynamic WHERE clause
        where_parts = [f"{timestamp_column} >= datetime('now', '-{days} days')"]
        params = []

        if ticker:
            where_parts.append("ticker = ?")
            params.append(ticker)

        where_clause = " WHERE " + " AND ".join(where_parts)

        # Count query
        count_sql = f"SELECT COUNT(*) as cnt FROM {table}{where_clause}"
        try:
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['cnt']
        except Exception as e:
            logger.error(f"Count query failed: {e}")
            total_count = 0

        # Data query with ORDER BY for recent first
        data_sql = (
            f"SELECT * FROM {table}{where_clause} "
            f"ORDER BY {timestamp_column} DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        try:
            cursor.execute(data_sql, params)
            rows = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Select query failed: {e}")
            rows = []

    return rows, total_count


# ============================================================================
# Query Analysis & Profiling
# ============================================================================

def explain_query(sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Run EXPLAIN QUERY PLAN to analyze query performance.

    Useful for debugging why indexes aren't being used.

    Args:
        sql: SQL query to analyze
        params: Query parameters

    Returns:
        List of explain plan rows (opcode, p1, p2, p3, p4, p5, comment)
    """
    with db_session() as conn:
        cursor = conn.cursor()
        explain_sql = f"EXPLAIN QUERY PLAN {sql}"

        try:
            cursor.execute(explain_sql, params or [])
            results = [dict(row) for row in cursor.fetchall()]
            return results
        except Exception as e:
            logger.error(f"EXPLAIN QUERY PLAN failed: {e}")
            return []


def get_table_stats(table: str) -> Dict[str, Any]:
    """
    Get table statistics: row count, index list, memory usage.

    Args:
        table: Table name

    Returns:
        Dict with row_count, indexes, and estimated_size_mb
    """
    with db_session() as conn:
        cursor = conn.cursor()

        # Row count
        row_count = 0
        try:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            row_count = cursor.fetchone()['cnt']
        except Exception:
            pass

        # Indexes
        indexes = []
        try:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?",
                (table,)
            )
            indexes = [row['name'] for row in cursor.fetchall()]
        except Exception:
            pass

        # Estimate size (page_count * page_size)
        size_mb = 0.0
        try:
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            size_mb = (page_count * page_size) / (1024 * 1024)
        except Exception:
            pass

        return {
            'row_count': row_count,
            'index_count': len(indexes),
            'indexes': indexes,
            'estimated_size_mb': round(size_mb, 2)
        }
```