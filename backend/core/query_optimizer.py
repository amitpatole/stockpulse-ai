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

        try:
            cursor.execute(data_sql, params + [limit, offset])
            rows = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Data query failed: {e}")
            rows = []

    return rows, total_count


def get_research_briefs_by_ticker(
    ticker: str,
    limit: int = 25,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch research briefs for a specific ticker with pagination.

    Uses composite index: idx_research_briefs_ticker_created

    Args:
        ticker: Stock ticker to filter by
        limit: Rows per page
        offset: Starting row

    Returns:
        Tuple of (briefs list, total count)
    """
    return get_filtered_with_pagination(
        table='research_briefs',
        filters={'ticker': ticker},
        limit=limit,
        offset=offset,
        order_by='created_at DESC',
        columns=['id', 'ticker', 'title', 'content', 'agent_name', 'model_used', 'created_at']
    )


def get_brief_with_metadata(brief_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch research brief with its metadata in a single query.

    Args:
        brief_id: ID of the research brief

    Returns:
        Combined brief + metadata dict, or None if not found
    """
    with db_session() as conn:
        cursor = conn.cursor()
        try:
            # Join research_briefs with metadata
            row = cursor.execute("""
                SELECT
                    rb.id, rb.ticker, rb.title, rb.content, rb.executive_summary,
                    rb.agent_name, rb.model_used, rb.has_metrics, rb.created_at, rb.updated_at,
                    rbm.executive_summary as meta_summary, rbm.key_insights, rbm.key_metrics,
                    rbm.metric_sources, rbm.pdf_url, rbm.pdf_generated_at
                FROM research_briefs rb
                LEFT JOIN research_brief_metadata rbm ON rb.id = rbm.brief_id
                WHERE rb.id = ?
            """, (brief_id,)).fetchone()

            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"Error fetching brief with metadata: {e}")

    return None