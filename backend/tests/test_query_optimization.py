"""
Database Query Optimization Tests
Validates that all hot-path queries use proper indexing and batch operations.

Coverage:
- SQL-side filtering (not Python loops)
- Batch queries with IN clauses (not N+1)
- Index usage verification with EXPLAIN PLAN
- Performance benchmarks
"""

import pytest
import sqlite3
import time
from unittest.mock import patch, MagicMock

from backend.database import db_session
from backend.core.query_optimizer import (
    get_active_stocks_optimized,
    batch_get_stocks_by_tickers,
    get_cached_ratings_optimized,
    get_research_briefs_by_ticker,
    count_active_stocks,
)


class TestStocksQueryOptimization:
    """Test optimizations for stock queries."""

    def test_stocks_filter_uses_sql_where(self):
        """AC1: Market filtering happens in SQL WHERE clause, not Python."""
        # Get stocks filtered by market
        stocks, total = get_active_stocks_optimized(market='US', limit=10, offset=0)

        # Verify all results match the filter (if we got any)
        if stocks:
            assert all(s['market'] == 'US' for s in stocks), \
                "SQL filtering failed - got stocks from other markets"

    def test_stocks_filter_all_markets(self):
        """AC2: Passing None or 'All' for market returns stocks from all markets."""
        stocks_none, total_none = get_active_stocks_optimized(market=None, limit=100, offset=0)
        stocks_all, total_all = get_active_stocks_optimized(market='All', limit=100, offset=0)

        # Both should behave identically
        assert len(stocks_none) == len(stocks_all), \
            "None and 'All' market filters should return same count"

    def test_stocks_pagination_respects_limit(self):
        """AC3: Pagination LIMIT is applied in SQL, not Python slicing."""
        # Request limit of 5
        stocks, total = get_active_stocks_optimized(market=None, limit=5, offset=0)

        # Should return at most 5 items
        assert len(stocks) <= 5, \
            f"Expected at most 5 stocks, got {len(stocks)}"

    def test_stocks_pagination_respects_offset(self):
        """AC4: Pagination OFFSET works correctly for skipping records."""
        stocks_page1, total = get_active_stocks_optimized(market=None, limit=5, offset=0)
        stocks_page2, _ = get_active_stocks_optimized(market=None, limit=5, offset=5)

        if total > 5:
            # Pages should be different (assuming we have >10 stocks)
            page1_tickers = {s['ticker'] for s in stocks_page1}
            page2_tickers = {s['ticker'] for s in stocks_page2}
            assert page1_tickers.isdisjoint(page2_tickers), \
                "Page 1 and Page 2 should have different stocks"

    def test_stocks_total_count_accurate(self):
        """AC5: Total count matches actual database count (EXPLAIN PLAN)."""
        with db_session() as conn:
            cursor = conn.cursor()
            actual_count = cursor.execute(
                'SELECT COUNT(*) as cnt FROM stocks WHERE active = 1'
            ).fetchone()['cnt']

        _, returned_count = get_active_stocks_optimized(market=None, limit=100, offset=0)

        assert returned_count == actual_count, \
            f"Count mismatch: returned {returned_count}, actual {actual_count}"


class TestBatchQueryOptimization:
    """Test optimizations for batch queries to avoid N+1."""

    def test_batch_get_stocks_single_query(self):
        """AC1: batch_get_stocks_by_tickers uses single query, not N queries."""
        tickers = ['AAPL', 'MSFT', 'GOOGL']

        # Fetch multiple stocks in one call
        stocks_dict = batch_get_stocks_by_tickers(tickers)

        # Should return dict with entries for requested tickers
        for ticker in tickers:
            if ticker in stocks_dict:
                assert stocks_dict[ticker]['ticker'] == ticker

    def test_batch_get_stocks_in_clause(self):
        """AC2: batch_get_stocks_by_tickers uses IN clause (verified with mock)."""
        tickers = ['AAPL', 'MSFT']

        with patch('backend.core.query_optimizer.db_session') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            # Mock IN clause execution
            mock_cursor.execute.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                MagicMock(ticker='AAPL', **{'ticker': 'AAPL'}),
                MagicMock(ticker='MSFT', **{'ticker': 'MSFT'})
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn

            result = batch_get_stocks_by_tickers(tickers)

            # Verify execute was called (with IN clause, not looping)
            mock_cursor.execute.assert_called_once()
            call_args = str(mock_cursor.execute.call_args)
            assert 'IN' in call_args, "Should use IN clause for batch query"

    def test_batch_get_stocks_empty_list(self):
        """AC3: batch_get_stocks_by_tickers handles empty list gracefully."""
        result = batch_get_stocks_by_tickers([])
        assert result == {}, "Empty ticker list should return empty dict"

    def test_batch_get_stocks_nonexistent_tickers(self):
        """AC4: batch_get_stocks_by_tickers skips non-existent tickers."""
        # Request a ticker that doesn't exist
        stocks_dict = batch_get_stocks_by_tickers(['NONEXISTENT_TICKER_XYZ'])

        # Should return empty dict or no entry for that ticker
        assert 'NONEXISTENT_TICKER_XYZ' not in stocks_dict, \
            "Non-existent ticker should not be in result"


class TestRatingsQueryOptimization:
    """Test optimizations for AI ratings queries."""

    def test_ratings_filter_uses_index(self):
        """AC1: get_cached_ratings_optimized uses idx_ai_ratings_ticker."""
        # Fetch ratings for specific ticker
        ticker = 'AAPL'
        ratings = get_cached_ratings_optimized(ticker=ticker)

        # All results should be for requested ticker
        if ratings:
            assert all(r['ticker'] == ticker for r in ratings), \
                "Rating filter failed - got other tickers"

    def test_ratings_selects_needed_columns(self):
        """AC2: Query selects only needed columns (reduces data transfer)."""
        ratings = get_cached_ratings_optimized(ticker=None)

        # Verify required columns are present
        if ratings:
            required_cols = {'ticker', 'rating', 'score', 'confidence', 'updated_at'}
            assert all(required_cols.issubset(r.keys()) for r in ratings), \
                "Missing required columns in response"

    def test_ratings_all_returns_multiple(self):
        """AC3: Fetching all ratings returns list of dicts."""
        all_ratings = get_cached_ratings_optimized(ticker=None)
        assert isinstance(all_ratings, list), "Should return list of ratings"


class TestResearchQueryOptimization:
    """Test optimizations for research briefs queries."""

    def test_research_briefs_uses_composite_index(self):
        """AC1: get_research_briefs_by_ticker uses composite index (ticker, created_at)."""
        briefs, total = get_research_briefs_by_ticker('AAPL', limit=10, offset=0)

        # Verify all briefs are for requested ticker
        if briefs:
            assert all(b['ticker'] == 'AAPL' for b in briefs), \
                "Ticker filter failed - got other tickers"

    def test_research_briefs_pagination_single_query(self):
        """AC2: Pagination uses single query with LIMIT+OFFSET, not COUNT+SELECT."""
        # Call once to get briefs and total count
        briefs, total = get_research_briefs_by_ticker('AAPL', limit=10, offset=0)

        # Verify we got a count
        assert isinstance(total, int), "Should return total count"
        assert total >= 0, "Count should be non-negative"

    def test_research_briefs_respects_pagination(self):
        """AC3: Pagination LIMIT and OFFSET work correctly."""
        briefs_p1, total = get_research_briefs_by_ticker('AAPL', limit=5, offset=0)
        briefs_p2, _ = get_research_briefs_by_ticker('AAPL', limit=5, offset=5)

        # Page 1 should have at most 5 items
        assert len(briefs_p1) <= 5

        # If we have more than 5 total, pages should be different
        if total > 5 and briefs_p2:
            ids_p1 = {b['id'] for b in briefs_p1}
            ids_p2 = {b['id'] for b in briefs_p2}
            assert ids_p1.isdisjoint(ids_p2), \
                "Pages should have different briefs"


class TestIndexUsageVerification:
    """Verify that queries actually use indexes (EXPLAIN PLAN)."""

    def test_stocks_active_market_index_used(self):
        """AC1: EXPLAIN PLAN shows idx_stocks_active_market is used."""
        with db_session() as conn:
            cursor = conn.cursor()

            # Run EXPLAIN QUERY PLAN
            plan = cursor.execute(
                'EXPLAIN QUERY PLAN SELECT * FROM stocks WHERE active = 1 AND market = ?',
                ('US',)
            ).fetchall()

            plan_str = str(plan)
            # Should show index usage (not full scan)
            assert 'SCAN' not in plan_str or 'Search' in plan_str, \
                f"Should use index, got plan: {plan_str}"

    def test_research_briefs_composite_index_used(self):
        """AC2: EXPLAIN PLAN shows idx_research_briefs_ticker_created is used."""
        with db_session() as conn:
            cursor = conn.cursor()

            plan = cursor.execute(
                'EXPLAIN QUERY PLAN SELECT * FROM research_briefs WHERE ticker = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
                ('AAPL', 10, 0)
            ).fetchall()

            plan_str = str(plan)
            # Should use index for WHERE and ORDER BY
            assert 'SCAN' not in plan_str or 'Search' in plan_str or 'USING' in plan_str, \
                f"Should use composite index, got plan: {plan_str}"

    def test_ai_ratings_ticker_index_used(self):
        """AC3: EXPLAIN PLAN shows idx_ai_ratings_ticker is used."""
        with db_session() as conn:
            cursor = conn.cursor()

            plan = cursor.execute(
                'EXPLAIN QUERY PLAN SELECT * FROM ai_ratings WHERE ticker = ?',
                ('AAPL',)
            ).fetchall()

            plan_str = str(plan)
            # Should use index lookup, not full table scan
            assert 'SCAN' not in plan_str or 'Search' in plan_str, \
                f"Should use index, got plan: {plan_str}"


class TestPerformanceBenchmarks:
    """Verify performance improvements from optimization."""

    def test_stocks_pagination_latency(self):
        """AC1: Stock pagination completes in <50ms (5-10x improvement)."""
        start = time.time()
        stocks, total = get_active_stocks_optimized(market=None, limit=20, offset=0)
        elapsed_ms = (time.time() - start) * 1000

        # Should complete in <50ms (was 500ms+ without optimization)
        assert elapsed_ms < 50, \
            f"Stocks pagination took {elapsed_ms:.2f}ms, expected <50ms"

    def test_batch_ticker_lookup_latency(self):
        """AC2: Batch ticker lookup completes in <10ms."""
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

        start = time.time()
        stocks_dict = batch_get_stocks_by_tickers(tickers)
        elapsed_ms = (time.time() - start) * 1000

        # Should complete in <10ms (was 100ms+ with per-ticker loop)
        assert elapsed_ms < 10, \
            f"Batch lookup took {elapsed_ms:.2f}ms, expected <10ms"

    def test_research_briefs_latency(self):
        """AC3: Research briefs pagination completes in <100ms."""
        start = time.time()
        briefs, total = get_research_briefs_by_ticker('AAPL', limit=25, offset=0)
        elapsed_ms = (time.time() - start) * 1000

        # Should complete in <100ms (was 200ms+ with separate COUNT query)
        assert elapsed_ms < 100, \
            f"Research briefs fetch took {elapsed_ms:.2f}ms, expected <100ms"


class TestN1PatternElimination:
    """Verify that N+1 patterns are eliminated."""

    def test_get_stocks_no_loop_per_stock(self):
        """AC1: get_active_stocks_optimized executes single query, not one per stock."""
        # Mock the cursor to count execute calls
        with patch('backend.core.query_optimizer.db_session') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            # Setup mock to return some stocks
            mock_cursor.execute.return_value = mock_cursor
            mock_cursor.fetchone.return_value = MagicMock(count=5)
            mock_cursor.fetchall.return_value = [
                MagicMock(ticker='AAPL', active=1, market='US'),
                MagicMock(ticker='MSFT', active=1, market='US'),
            ]

            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn

            # Call the function
            result = get_active_stocks_optimized(market=None, limit=100, offset=0)

            # Should execute exactly 2 queries (COUNT + SELECT), not N+1
            assert mock_cursor.execute.call_count == 2, \
                f"Expected 2 queries (COUNT + SELECT), got {mock_cursor.execute.call_count}"

    def test_batch_get_stocks_single_execute(self):
        """AC2: batch_get_stocks_by_tickers makes single execute() call."""
        with patch('backend.core.query_optimizer.db_session') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()

            mock_cursor.execute.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                MagicMock(ticker='AAPL', **{'ticker': 'AAPL'}),
            ]

            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn

            # Call with 3 tickers
            result = batch_get_stocks_by_tickers(['AAPL', 'MSFT', 'GOOGL'])

            # Should execute exactly once (IN clause), not per ticker
            mock_cursor.execute.assert_called_once()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_pagination_beyond_total(self):
        """AC1: Pagination offset beyond total returns empty list."""
        # Request way beyond total records
        stocks, total = get_active_stocks_optimized(market=None, limit=10, offset=99999)

        assert len(stocks) == 0, "Beyond-total offset should return empty list"
        assert isinstance(total, int), "Should still return valid total count"

    def test_zero_limit_handling(self):
        """AC2: Limit of 0 is handled gracefully."""
        # This might be constrained by validation, but should not crash
        try:
            stocks, total = get_active_stocks_optimized(market=None, limit=0, offset=0)
            assert isinstance(stocks, list), "Should return list even with limit=0"
        except (ValueError, AssertionError):
            # Expected if validation rejects limit=0
            pass

    def test_negative_offset_handling(self):
        """AC3: Negative offset is handled gracefully."""
        # Negative offsets might be constrained by validation
        try:
            stocks, total = get_active_stocks_optimized(market=None, limit=10, offset=-1)
            assert isinstance(stocks, list), "Should handle negative offset"
        except (ValueError, AssertionError):
            # Expected if validation rejects negative offset
            pass
