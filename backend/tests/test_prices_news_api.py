"""
Focused API Endpoint Tests: Prices & News APIs

Tests for REST endpoints that weren't covered in test_api_endpoints_comprehensive.py:
- Prices API: GET /api/prices/<ticker>, GET /api/prices (REST fallback endpoints)
- News API: GET /api/news, GET /api/alerts

Coverage Strategy:
- 50% Happy path (normal operation)
- 30% Error handling (invalid input, missing data)
- 20% Edge cases (boundaries, empty data, validation)
"""

import pytest
import json
from unittest.mock import patch, MagicMock


# =====================================================================
# FIXTURES - Reusable test data and setup
# =====================================================================

@pytest.fixture
def test_app():
    """Create Flask test application."""
    from backend.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(test_app):
    """Create Flask test client."""
    return test_app.test_client()


@pytest.fixture
def mock_stock_with_price():
    """Mock stock with current price data."""
    return {
        'ticker': 'AAPL',
        'name': 'Apple Inc',
        'market': 'US',
        'active': 1,
        'current_price': 175.50,
        'currency': 'USD',
        'day_change': 2.50,
        'day_change_percent': 1.44,
        'updated_at': '2026-03-03T10:30:00Z',
    }


@pytest.fixture
def mock_all_stocks_with_prices():
    """Mock multiple stocks with prices."""
    return [
        {
            'ticker': 'AAPL',
            'name': 'Apple Inc',
            'market': 'US',
            'active': 1,
            'current_price': 175.50,
            'currency': 'USD',
            'day_change': 2.50,
            'day_change_percent': 1.44,
            'updated_at': '2026-03-03T10:30:00Z',
        },
        {
            'ticker': 'MSFT',
            'name': 'Microsoft Corp',
            'market': 'US',
            'active': 1,
            'current_price': 425.30,
            'currency': 'USD',
            'day_change': -2.10,
            'day_change_percent': -0.49,
            'updated_at': '2026-03-03T10:30:00Z',
        },
        {
            'ticker': 'DELETED',
            'name': 'Deleted Stock',
            'market': 'US',
            'active': 0,  # inactive
            'current_price': 100.00,
            'currency': 'USD',
            'day_change': 0.0,
            'day_change_percent': 0.0,
            'updated_at': '2026-03-03T09:00:00Z',
        }
    ]


@pytest.fixture
def mock_news_articles():
    """Mock news articles from database."""
    return [
        {
            'id': 1,
            'ticker': 'AAPL',
            'title': 'Apple releases new iPhone model',
            'description': 'Apple announces revolutionary new features',
            'url': 'https://example.com/news/apple-iphone',
            'source': 'TechNews',
            'published_date': '2026-03-03T08:00:00Z',
            'sentiment_score': 0.85,
            'sentiment_label': 'bullish',
            'created_at': '2026-03-03T08:30:00Z',
        },
        {
            'id': 2,
            'ticker': 'AAPL',
            'title': 'Apple stock gains on earnings beat',
            'description': 'Strong Q1 earnings report',
            'url': 'https://example.com/news/apple-earnings',
            'source': 'Bloomberg',
            'published_date': '2026-03-02T15:00:00Z',
            'sentiment_score': 0.78,
            'sentiment_label': 'bullish',
            'created_at': '2026-03-02T15:30:00Z',
        },
    ]


@pytest.fixture
def mock_alerts():
    """Mock price alerts with associated news."""
    return [
        {
            'id': 1,
            'ticker': 'AAPL',
            'alert_type': 'price_surge',
            'threshold': 5.0,
            'news_id': 1,
            'created_at': '2026-03-03T08:30:00Z',
            'title': 'Apple releases new iPhone model',
            'url': 'https://example.com/news/apple-iphone',
            'source': 'TechNews',
            'sentiment_score': 0.85,
        },
        {
            'id': 2,
            'ticker': 'MSFT',
            'alert_type': 'price_drop',
            'threshold': -3.0,
            'news_id': None,
            'created_at': '2026-03-03T09:00:00Z',
            'title': None,
            'url': None,
            'source': None,
            'sentiment_score': None,
        }
    ]


# =====================================================================
# PRICES API TESTS - REST Fallback Endpoints
# =====================================================================

class TestPricesAPI:
    """Tests for Prices REST endpoints (WebSocket fallback)."""

    def test_get_price_single_ticker_happy_path(self, client, mock_stock_with_price):
        """AC1: Get current price for valid ticker."""
        with patch('backend.api.prices.get_all_stocks', return_value=[mock_stock_with_price]):
            response = client.get('/api/prices/AAPL')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert 'data' in data
            price_data = data['data']
            assert price_data['ticker'] == 'AAPL'
            assert price_data['price'] == 175.50
            assert price_data['currency'] == 'USD'
            assert price_data['change'] == 2.50
            assert price_data['change_pct'] == 1.44
            assert 'timestamp' in price_data

    def test_get_price_not_found_error(self, client, mock_stock_with_price):
        """AC1 Error: Ticker not found returns 404."""
        with patch('backend.api.prices.get_all_stocks', return_value=[mock_stock_with_price]):
            response = client.get('/api/prices/NONEXISTENT')
            assert response.status_code == 404

            data = json.loads(response.data)
            assert data['error'] == 'Stock not found'
            assert 'NONEXISTENT' in data['message']

    def test_get_price_invalid_ticker_format_edge_case(self, client):
        """AC1 Edge: Very long ticker format rejected."""
        response = client.get('/api/prices/' + 'A' * 20)  # 20-char ticker (max is 10)
        assert response.status_code == 400

        data = json.loads(response.data)
        assert 'Invalid ticker format' in data['error']

    def test_get_all_prices_happy_path_with_defaults(self, client, mock_all_stocks_with_prices):
        """AC2: Get all prices with default pagination (limit=50, offset=0)."""
        with patch('backend.api.prices.get_all_stocks', return_value=mock_all_stocks_with_prices):
            response = client.get('/api/prices')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert 'data' in data
            assert 'meta' in data
            assert len(data['data']) == 2  # 2 active stocks (DELETED is inactive)
            assert data['meta']['limit'] == 50
            assert data['meta']['offset'] == 0
            assert data['meta']['total'] == 2
            assert data['meta']['has_next'] is False
            assert data['meta']['has_previous'] is False

    def test_get_all_prices_filters_inactive_stocks(self, client, mock_all_stocks_with_prices):
        """AC2 Edge: Only active stocks included (active=1)."""
        with patch('backend.api.prices.get_all_stocks', return_value=mock_all_stocks_with_prices):
            response = client.get('/api/prices')
            assert response.status_code == 200

            data = json.loads(response.data)
            # Verify no deleted/inactive stocks in response
            for price in data['data']:
                assert price['ticker'] != 'DELETED'

    def test_get_all_prices_custom_limit_and_offset(self, client, mock_all_stocks_with_prices):
        """AC2: Pagination with custom limit and offset parameters."""
        large_dataset = mock_all_stocks_with_prices * 20  # Create 40+ prices
        with patch('backend.api.prices.get_all_stocks', return_value=large_dataset):
            response = client.get('/api/prices?limit=25&offset=0')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['meta']['limit'] == 25
            assert data['meta']['offset'] == 0
            assert len(data['data']) == 25
            assert data['meta']['has_next'] is True

    def test_get_all_prices_respects_max_limit(self, client, mock_all_stocks_with_prices):
        """AC2 Error: Max limit enforced (200 max)."""
        with patch('backend.api.prices.get_all_stocks', return_value=mock_all_stocks_with_prices):
            response = client.get('/api/prices?limit=500')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['meta']['limit'] == 200  # Capped at 200

    def test_get_all_prices_invalid_pagination_params_fallback(self, client, mock_all_stocks_with_prices):
        """AC2 Edge: Invalid params revert to defaults gracefully."""
        with patch('backend.api.prices.get_all_stocks', return_value=mock_all_stocks_with_prices):
            response = client.get('/api/prices?limit=invalid&offset=xyz')
            assert response.status_code == 200

            data = json.loads(response.data)
            # Should revert to defaults
            assert data['meta']['limit'] == 50
            assert data['meta']['offset'] == 0


# =====================================================================
# NEWS API TESTS
# =====================================================================

class TestNewsAPI:
    """Tests for News and Alerts endpoints."""

    def test_get_news_all_articles_happy_path(self, client, mock_news_articles):
        """AC1: Get all recent news articles (limit 100)."""
        with patch('backend.api.news.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = mock_news_articles
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get('/api/news')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]['ticker'] == 'AAPL'
            assert data[0]['title'] == 'Apple releases new iPhone model'
            assert 'sentiment_score' in data[0]
            assert 'sentiment_label' in data[0]

    def test_get_news_filter_by_ticker(self, client, mock_news_articles):
        """AC2: Filter news articles by ticker parameter."""
        with patch('backend.api.news.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # Return only AAPL articles when filtered
            filtered = [a for a in mock_news_articles if a['ticker'] == 'AAPL']
            mock_cursor.fetchall.return_value = filtered
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get('/api/news?ticker=AAPL')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert len(data) == 2
            for article in data:
                assert article['ticker'] == 'AAPL'

    def test_get_news_empty_results(self, client):
        """AC1 Edge: Empty news results handled gracefully."""
        with patch('backend.api.news.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get('/api/news?ticker=NONEXISTENT')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data == []

    def test_get_alerts_happy_path(self, client, mock_alerts):
        """AC3: Get recent alerts with associated news (last 50)."""
        with patch('backend.api.news.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = mock_alerts
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get('/api/alerts')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]['id'] == 1
            assert data[0]['ticker'] == 'AAPL'
            assert data[0]['alert_type'] == 'price_surge'
            assert data[0]['title'] == 'Apple releases new iPhone model'

    def test_get_alerts_with_null_news_reference(self, client, mock_alerts):
        """AC3 Edge: Alerts without associated news (news_id=NULL) handled."""
        with patch('backend.api.news.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = mock_alerts
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get('/api/alerts')
            assert response.status_code == 200

            data = json.loads(response.data)
            # Second alert has news_id=None
            assert data[1]['news_id'] is None
            assert data[1]['title'] is None
            assert data[1]['url'] is None


# =====================================================================
# INTEGRATION TESTS - Multi-step workflows
# =====================================================================

class TestPricesNewsIntegration:
    """Tests for workflows combining prices and news APIs."""

    def test_get_price_then_get_related_news_workflow(self, client, mock_stock_with_price, mock_news_articles):
        """Workflow: Get stock price → Get related news articles."""
        # Step 1: Get price for stock
        with patch('backend.api.prices.get_all_stocks', return_value=[mock_stock_with_price]):
            response = client.get('/api/prices/AAPL')
            assert response.status_code == 200

        # Step 2: Get news articles for that ticker
        with patch('backend.api.news.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            filtered = [a for a in mock_news_articles if a['ticker'] == 'AAPL']
            mock_cursor.fetchall.return_value = filtered
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value = mock_conn

            response = client.get('/api/news?ticker=AAPL')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
            assert data[0]['sentiment_score'] == 0.85  # Bullish


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
