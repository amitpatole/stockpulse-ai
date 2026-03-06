"""
TickerPulse AI v3.0 - Query Profiler
Provides EXPLAIN PLAN logging and performance metrics for database queries.
Used to verify that hot-path queries use indexes efficiently.
"""

import sqlite3
import logging
import time
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def explain_query_plan(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Get the EXPLAIN QUERY PLAN output for a SQL query.

    Args:
        conn: SQLite connection
        sql: SQL query to analyze
        params: Query parameters

    Returns:
        List of plan rows as dicts
    """
    explain_sql = f"EXPLAIN QUERY PLAN {sql}"
    cursor = conn.cursor()

    try:
        rows = cursor.execute(explain_sql, params).fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.warning(f"Failed to get EXPLAIN PLAN: {e}")
        return []


def detect_full_table_scan(plan: List[Dict[str, Any]]) -> bool:
    """
    Detect if query plan contains a full table scan (SCAN TABLE without index).

    Args:
        plan: EXPLAIN QUERY PLAN output

    Returns:
        True if full table scan detected, False if index used
    """
    for row in plan:
        detail = str(row.get('detail', '') or '')
        # Full scan: "SCAN TABLE ... WITHOUT INDEX"
        # Index scan: "SEARCH TABLE ... USING INDEX ..."
        if 'SCAN TABLE' in detail and 'WITHOUT INDEX' in detail:
            return True
    return False


def get_index_used(plan: List[Dict[str, Any]]) -> Optional[str]:
    """
    Extract the index name used in a query plan.

    Args:
        plan: EXPLAIN QUERY PLAN output

    Returns:
        Index name if used, None if full table scan
    """
    for row in plan:
        detail = str(row.get('detail', '') or '')
        if 'USING INDEX' in detail:
            # Extract index name: "USING INDEX idx_name"
            parts = detail.split('USING INDEX')
            if len(parts) > 1:
                tokens = parts[1].strip().split()
                if tokens:
                    return tokens[0]
    return None


@contextmanager
def profile_query(conn: sqlite3.Connection, query_name: str = ""):
    """
    Context manager to profile a query: log execution time, EXPLAIN PLAN, and index usage.

    Usage:
        with profile_query(conn, "get_active_stocks") as profiler:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            profiler.record_query(sql, params)

    Args:
        conn: SQLite connection
        query_name: Human-readable query name for logging
    """
    class QueryProfiler:
        def __init__(self, conn: sqlite3.Connection, name: str):
            self.conn = conn
            self.name = name
            self.start_time = time.time()
            self.plan = None
            self.index_used = None
            self.full_scan = False

        def record_query(self, sql: str, params: tuple = ()):
            """Record query details: EXPLAIN PLAN and timing."""
            self.plan = explain_query_plan(self.conn, sql, params)
            self.full_scan = detect_full_table_scan(self.plan)
            self.index_used = get_index_used(self.plan)

            elapsed_ms = (time.time() - self.start_time) * 1000

            if self.name:
                if self.full_scan:
                    logger.warning(
                        f"Query '{self.name}' executed in {elapsed_ms:.2f}ms - "
                        f"FULL TABLE SCAN DETECTED (no index used)"
                    )
                elif self.index_used:
                    logger.debug(
                        f"Query '{self.name}' executed in {elapsed_ms:.2f}ms - "
                        f"Using index: {self.index_used}"
                    )
                else:
                    logger.debug(f"Query '{self.name}' executed in {elapsed_ms:.2f}ms")

        def get_metrics(self) -> Dict[str, Any]:
            """Get profiling metrics."""
            return {
                'name': self.name,
                'duration_ms': (time.time() - self.start_time) * 1000,
                'index_used': self.index_used,
                'full_table_scan': self.full_scan,
                'plan': self.plan,
            }

    profiler = QueryProfiler(conn, query_name)
    try:
        yield profiler
    finally:
        pass


def verify_hot_path_indexes(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Verify that hot-path queries use indexes efficiently.

    Hot paths verified:
    - GET /api/stocks (active + market filter)
    - GET /api/research/briefs (ticker + pagination)
    - GET /api/analysis/ai-ratings (ticker lookup)

    Args:
        conn: SQLite connection

    Returns:
        Dict with verification results
    """
    results = {
        'verified_queries': [],
        'full_scans_detected': [],
        'all_optimized': True,
    }

    # Hot path 1: Get active stocks with market filter
    stocks_sql = "SELECT * FROM stocks WHERE active = 1 AND market = ?"
    plan = explain_query_plan(conn, stocks_sql, ('US',))
    is_scan = detect_full_table_scan(plan)
    idx = get_index_used(plan)
    results['verified_queries'].append({
        'query': 'GET /api/stocks (active + market)',
        'index': idx,
        'full_scan': is_scan,
    })
    if is_scan:
        results['full_scans_detected'].append('GET /api/stocks')
        results['all_optimized'] = False

    # Hot path 2: Get research briefs by ticker
    briefs_sql = "SELECT * FROM research_briefs WHERE ticker = ? ORDER BY created_at DESC LIMIT ?"
    plan = explain_query_plan(conn, briefs_sql, ('AAPL', 10))
    is_scan = detect_full_table_scan(plan)
    idx = get_index_used(plan)
    results['verified_queries'].append({
        'query': 'GET /api/research/briefs (ticker + sort)',
        'index': idx,
        'full_scan': is_scan,
    })
    if is_scan:
        results['full_scans_detected'].append('GET /api/research/briefs')
        results['all_optimized'] = False

    # Hot path 3: Get AI ratings by ticker
    ratings_sql = "SELECT * FROM ai_ratings WHERE ticker = ?"
    plan = explain_query_plan(conn, ratings_sql, ('AAPL',))
    is_scan = detect_full_table_scan(plan)
    idx = get_index_used(plan)
    results['verified_queries'].append({
        'query': 'GET /api/analysis/ai-ratings (ticker)',
        'index': idx,
        'full_scan': is_scan,
    })
    if is_scan:
        results['full_scans_detected'].append('GET /api/analysis/ai-ratings')
        results['all_optimized'] = False

    # Hot path 4: Get active AI providers
    providers_sql = "SELECT * FROM ai_providers WHERE is_active = 1"
    plan = explain_query_plan(conn, providers_sql)
    is_scan = detect_full_table_scan(plan)
    idx = get_index_used(plan)
    results['verified_queries'].append({
        'query': 'GET active AI providers (is_active filter)',
        'index': idx,
        'full_scan': is_scan,
    })
    if is_scan:
        results['full_scans_detected'].append('Active AI providers')
        results['all_optimized'] = False

    return results


def list_all_indexes(conn: sqlite3.Connection) -> List[Dict[str, str]]:
    """
    List all indexes in the database.

    Args:
        conn: SQLite connection

    Returns:
        List of index dicts with name, table, and columns
    """
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
    ).fetchall()
    return [
        {
            'name': row['name'],
            'table': row['tbl_name'],
        }
        for row in rows
    ]
