"""
Comprehensive tests for InsiderManager - covers AC1-AC4 with proper mocking.
AC1: Add transaction successfully and handle duplicates
AC2: Filter filings by sentiment, type, date range; pagination enforces boundaries
AC3: Stats correctly calculate net shares, sentiment average, buy/sell counts
AC4: Watchlist returns distinct tickers with filings, pagination metadata correct
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from backend.core.insider_manager import InsiderManager


class TestAddTransactionInsertAndDeduplicate:
    """AC1: Add transaction successfully and handle duplicates without exception."""

    @patch('backend.core.insider_manager.db_session')
    def test_add_transaction_success_returns_id(self, mock_db):
        """Happy path: transaction inserted and lastrowid returned."""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.add_transaction(
            cik='0000320193',
            ticker='AAPL',
            insider_name='Tim Cook',
            title='CEO',
            transaction_type='purchase',
            shares=500,
            price=185.25,
            value=92625.00,
            filing_date=datetime(2026, 3, 1, 10, 30),
            transaction_date=datetime(2026, 2, 28),
            sentiment_score=1.0,
            is_derivative=False,
            filing_url='https://sec.gov/...',
            form4_url='https://sec.gov/form4',
        )

        assert result == 42
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch('backend.core.insider_manager.logger')
    @patch('backend.core.insider_manager.db_session')
    def test_add_transaction_duplicate_constraint_handled_gracefully(self, mock_db, mock_logger):
        """Edge case: UNIQUE constraint violation logged, None returned (not raised)."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("UNIQUE constraint failed")
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.add_transaction(
            cik='0000320193',
            ticker='AAPL',
            insider_name='Tim Cook',
            title='CEO',
            transaction_type='purchase',
            shares=500,
            price=185.25,
            value=92625.00,
            filing_date=datetime(2026, 3, 1),
            transaction_date=datetime(2026, 2, 28),
            sentiment_score=1.0,
        )

        assert result is None
        mock_logger.warning.assert_called_once()

    @patch('backend.core.insider_manager.db_session')
    def test_add_transaction_parameterized_query_prevents_injection(self, mock_db):
        """Security: SQL injection prevented via parameterized queries."""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn

        InsiderManager.add_transaction(
            cik="0000320193'; DROP TABLE insiders; --",
            ticker='AAPL',
            insider_name='Tim Cook',
            title='CEO',
            transaction_type='purchase',
            shares=500,
            price=185.25,
            value=92625.00,
            filing_date=datetime(2026, 3, 1),
            transaction_date=datetime(2026, 2, 28),
            sentiment_score=1.0,
        )

        # Verify parameterized query used (14 placeholders)
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        assert query.count('?') == 14
        assert "DROP TABLE" not in query


class TestListFilingsWithSentimentAndTypeFilters:
    """AC2: Filter filings by sentiment, type, date range; pagination enforces boundaries."""

    @patch('backend.core.insider_manager.db_session')
    def test_list_filings_purchase_type_filter(self, mock_db):
        """Filter: transaction_type='purchase' returns only buy transactions."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        count_result = Mock()
        count_result.fetchone = lambda: {'cnt': 2}

        data_result = Mock()
        data_result.fetchall = lambda: [
            {'id': 1, 'transaction_type': 'purchase', 'sentiment_score': 1.0},
            {'id': 2, 'transaction_type': 'purchase', 'sentiment_score': 1.0},
        ]

        mock_cursor.execute.side_effect = [count_result, data_result]
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.list_filings(
            ticker='AAPL',
            transaction_type='purchase',
            limit=50,
            offset=0,
        )

        assert result['meta']['total_count'] == 2
        assert len(result['data']) == 2

    @patch('backend.core.insider_manager.db_session')
    def test_list_filings_sentiment_minimum_filter(self, mock_db):
        """Filter: min_sentiment=0.5 excludes sales and low-sentiment transactions."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        count_result = Mock()
        count_result.fetchone = lambda: {'cnt': 1}

        data_result = Mock()
        data_result.fetchall = lambda: [{'id': 1, 'sentiment_score': 0.95}]

        mock_cursor.execute.side_effect = [count_result, data_result]
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.list_filings(
            ticker='AAPL',
            min_sentiment=0.5,
            limit=50,
            offset=0,
        )

        count_call = mock_cursor.execute.call_args_list[0]
        where_clause = count_call[0][0]
        assert 'sentiment_score >= ?' in where_clause
        assert result['meta']['total_count'] == 1

    @patch('backend.core.insider_manager.db_session')
    def test_list_filings_pagination_clamped_to_boundaries(self, mock_db):
        """Edge case: limit >100 clamped to 100, offset <0 clamped to 0."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        count_result = Mock()
        count_result.fetchone = lambda: {'cnt': 200}

        data_result = Mock()
        data_result.fetchall = lambda: []

        mock_cursor.execute.side_effect = [count_result, data_result]
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.list_filings(
            limit=500,  # Request 500, should clamp to 100
            offset=-10,  # Request -10, should clamp to 0
        )

        data_call = mock_cursor.execute.call_args_list[1]
        params = data_call[0][1]
        assert params[-2] == 100  # limit clamped
        assert result['meta']['limit'] == 100
        assert result['meta']['offset'] == 0

    @patch('backend.core.insider_manager.db_session')
    def test_list_filings_empty_results_has_next_false(self, mock_db):
        """Edge case: no matching transactions returns empty data with has_next=False."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        count_result = Mock()
        count_result.fetchone = lambda: {'cnt': 0}

        data_result = Mock()
        data_result.fetchall = lambda: []

        mock_cursor.execute.side_effect = [count_result, data_result]
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.list_filings(ticker='INVALID')

        assert result['data'] == []
        assert result['meta']['total_count'] == 0
        assert result['meta']['has_next'] is False


class TestGetStatsAggregation:
    """AC3: Stats correctly calculate net shares, sentiment average, buy/sell counts."""

    @patch('backend.core.insider_manager.db_session')
    def test_get_stats_net_shares_purchases_minus_sales(self, mock_db):
        """Calculation: net_shares = purchase_shares - sale_shares."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # First call: fetch transactions
        txn_result = Mock()
        txn_result.fetchall = lambda: [
            {'transaction_type': 'purchase', 'shares': 1000, 'value': 185000, 'sentiment_score': 1.0, 'ticker': 'AAPL'},
            {'transaction_type': 'sale', 'shares': 300, 'value': 55000, 'sentiment_score': -1.0, 'ticker': 'AAPL'},
        ]

        # Second call: insider count
        count_result = Mock()
        count_result.fetchone = lambda: {'cnt': 2}

        # Third call: max filing date
        date_result = Mock()
        date_result.fetchone = lambda: {'last_date': datetime(2026, 3, 1)}

        mock_cursor.execute.side_effect = [txn_result, count_result, date_result]
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.get_stats(cik='0000320193', days=30)

        assert result['data']['net_shares'] == 700  # 1000 - 300
        assert result['data']['buy_count'] == 1
        assert result['data']['sell_count'] == 1

    @patch('backend.core.insider_manager.db_session')
    def test_get_stats_no_transactions_returns_error(self, mock_db):
        """Edge case: no matching transactions returns error."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        txn_result = Mock()
        txn_result.fetchall = lambda: []

        mock_cursor.execute.return_value = txn_result
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.get_stats(cik='9999999999', days=30)

        assert result['data'] is None
        assert 'No transactions found' in result['errors'][0]


class TestGetWatchlistActivityPagination:
    """AC4: Watchlist returns distinct tickers with filings, pagination metadata correct."""

    def test_get_watchlist_activity_empty_tickers_list_returns_empty(self):
        """Edge case: empty tickers list returns empty data."""
        result = InsiderManager.get_watchlist_activity(tickers=[], limit=50, offset=0)

        assert result['data'] == []
        assert result['meta']['total_count'] == 0
        assert result['meta']['has_next'] is False

    @patch('backend.core.insider_manager.db_session')
    def test_get_watchlist_activity_pagination_has_next_calculation(self, mock_db):
        """Pagination: has_next=True when (offset + limit) < total_count."""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        # First call: total count of distinct tickers
        count_result = Mock()
        count_result.fetchone = lambda: {'cnt': 10}

        # Second call: paginated ticker groups
        tickers_result = Mock()
        tickers_result.fetchall = lambda: [
            {
                'ticker': 'AAPL',
                'company_name': 'Apple',
                'latest_filing_date': datetime(2026, 3, 1),
                'transaction_count': 5,
                'net_sentiment': 0.6,
            },
        ]

        # Third call: filings for AAPL
        filings_result = Mock()
        filings_result.fetchall = lambda: []

        mock_cursor.execute.side_effect = [count_result, tickers_result, filings_result]
        mock_db.return_value.__enter__.return_value = mock_conn

        result = InsiderManager.get_watchlist_activity(
            tickers=['AAPL', 'MSFT'],
            limit=5,
            offset=0,
        )

        # offset=0, limit=5, total=10: has_next should be True (0+5 < 10)
        assert result['meta']['has_next'] is True
        assert result['meta']['offset'] == 0
        assert result['meta']['limit'] == 5
