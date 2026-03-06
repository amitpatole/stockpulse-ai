"""
Shared pytest fixtures for all API endpoint tests.

Provides:
- Flask test app and client
- Mock data generators for stocks, news, agents, etc.
- Database connection mocks
- Common test utilities
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from contextlib import contextmanager
from typing import Generator


# =========================================================================
# FIXTURES: Flask App & Client
# =========================================================================

@pytest.fixture
def test_app():
    """Create Flask test app with testing configuration."""
    from backend.app import create_app
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(test_app):
    """Create Flask test client."""
    return test_app.test_client()


@pytest.fixture
def app_context(test_app):
    """Provide application context for tests."""
    with test_app.app_context():
        yield test_app


# =========================================================================
# FIXTURES: Mock Data Generators
# =========================================================================

@pytest.fixture
def mock_stocks():
    """Generate realistic stock test data."""
    return [
        {
            'ticker': 'AAPL',
            'name': 'Apple Inc',
            'market': 'US',
            'active': 1,
            'current_price': 150.25,
            'price_change_pct': 2.5,
            'last_updated': '2025-03-03T16:00:00',
            'added_at': '2025-01-01T00:00:00'
        },
        {
            'ticker': 'MSFT',
            'name': 'Microsoft Corp',
            'market': 'US',
            'active': 1,
            'current_price': 320.50,
            'price_change_pct': -1.2,
            'last_updated': '2025-03-03T16:00:00',
            'added_at': '2025-01-02T00:00:00'
        },
        {
            'ticker': 'GOOGL',
            'name': 'Alphabet Inc',
            'market': 'US',
            'active': 1,
            'current_price': 140.75,
            'price_change_pct': 0.8,
            'last_updated': '2025-03-03T16:00:00',
            'added_at': '2025-01-03T00:00:00'
        },
        {
            'ticker': 'TSLA',
            'name': 'Tesla Inc',
            'market': 'US',
            'active': 1,
            'current_price': 200.10,
            'price_change_pct': 3.2,
            'last_updated': '2025-03-03T16:00:00',
            'added_at': '2025-01-04T00:00:00'
        },
        {
            'ticker': 'NVDA',
            'name': 'NVIDIA Corp',
            'market': 'US',
            'active': 1,
            'current_price': 875.40,
            'price_change_pct': 5.1,
            'last_updated': '2025-03-03T16:00:00',
            'added_at': '2025-01-05T00:00:00'
        },
        {
            'ticker': 'RELIANCE.NS',
            'name': 'Reliance Industries',
            'market': 'India',
            'active': 1,
            'current_price': 2750.00,
            'price_change_pct': -0.5,
            'last_updated': '2025-03-03T16:00:00',
            'added_at': '2025-01-06T00:00:00'
        },
        {
            'ticker': 'TCS.NS',
            'name': 'Tata Consultancy',
            'market': 'India',
            'active': 1,
            'current_price': 3850.50,
            'price_change_pct': 1.3,
            'last_updated': '2025-03-03T16:00:00',
            'added_at': '2025-01-07T00:00:00'
        },
        {
            'ticker': 'DELETED_STOCK.US',
            'name': 'Deleted Corp',
            'market': 'US',
            'active': 0,
            'current_price': 100.0,
            'price_change_pct': 0.0,
            'last_updated': '2025-01-01T00:00:00',
            'added_at': '2025-01-08T00:00:00'
        },
    ]


@pytest.fixture
def mock_news_articles():
    """Generate realistic news article test data."""
    return [
        {
            'id': 1,
            'ticker': 'AAPL',
            'title': 'Apple Reports Strong Q4 Earnings',
            'description': 'Apple exceeded expectations with 15% YoY growth',
            'url': 'https://example.com/apple-q4',
            'source': 'Reuters',
            'published_date': '2025-03-03',
            'sentiment_score': 0.85,
            'sentiment_label': 'positive',
            'engagement_score': 42.5,
            'created_at': '2025-03-03T10:00:00'
        },
        {
            'id': 2,
            'ticker': 'AAPL',
            'title': 'Apple Faces Supply Chain Challenges',
            'description': 'New supply constraints may impact Q1 production',
            'url': 'https://example.com/apple-supply',
            'source': 'CNBC',
            'published_date': '2025-03-02',
            'sentiment_score': -0.45,
            'sentiment_label': 'negative',
            'engagement_score': 18.3,
            'created_at': '2025-03-02T14:30:00'
        },
        {
            'id': 3,
            'ticker': 'MSFT',
            'title': 'Microsoft Expands AI Division',
            'description': 'Microsoft announces $5B investment in AI infrastructure',
            'url': 'https://example.com/msft-ai',
            'source': 'Bloomberg',
            'published_date': '2025-03-01',
            'sentiment_score': 0.72,
            'sentiment_label': 'positive',
            'engagement_score': 65.2,
            'created_at': '2025-03-01T09:15:00'
        },
        {
            'id': 4,
            'ticker': 'MSFT',
            'title': 'Microsoft Stock Consolidates',
            'description': 'No major catalyst in sight for near-term movement',
            'url': 'https://example.com/msft-consol',
            'source': 'MarketWatch',
            'published_date': '2025-02-28',
            'sentiment_score': 0.05,
            'sentiment_label': 'neutral',
            'engagement_score': 5.1,
            'created_at': '2025-02-28T16:45:00'
        },
        {
            'id': 5,
            'ticker': 'GOOGL',
            'title': 'Google Search Algorithm Update',
            'description': 'Algorithm changes favor enterprise solutions',
            'url': 'https://example.com/google-algo',
            'source': 'TechCrunch',
            'published_date': '2025-02-27',
            'sentiment_score': 0.55,
            'sentiment_label': 'positive',
            'engagement_score': 32.7,
            'created_at': '2025-02-27T11:20:00'
        },
    ]


@pytest.fixture
def mock_alerts():
    """Generate realistic alert test data."""
    return [
        {
            'id': 1,
            'ticker': 'AAPL',
            'news_id': 2,
            'alert_type': 'price_change',
            'message': 'Apple down 5% on supply chain concerns',
            'created_at': '2025-03-02T14:35:00'
        },
        {
            'id': 2,
            'ticker': 'MSFT',
            'news_id': 3,
            'alert_type': 'major_news',
            'message': 'Microsoft announces $5B AI investment',
            'created_at': '2025-03-01T09:20:00'
        },
        {
            'id': 3,
            'ticker': 'TSLA',
            'news_id': None,
            'alert_type': 'volatility',
            'message': 'TSLA volatility increased to 35%',
            'created_at': '2025-02-28T15:00:00'
        },
    ]


@pytest.fixture
def mock_ai_ratings():
    """Generate realistic AI rating test data."""
    return [
        {
            'ticker': 'AAPL',
            'rating_score': 8.5,
            'confidence': 0.92,
            'recommendation': 'strong_buy',
            'analysis': 'Strong fundamentals with positive momentum',
            'period_days': 5,
            'created_at': '2025-03-03T10:00:00'
        },
        {
            'ticker': 'MSFT',
            'rating_score': 7.8,
            'confidence': 0.88,
            'recommendation': 'buy',
            'analysis': 'Solid AI investments driving growth',
            'period_days': 5,
            'created_at': '2025-03-03T10:00:00'
        },
        {
            'ticker': 'GOOGL',
            'rating_score': 6.5,
            'confidence': 0.85,
            'recommendation': 'hold',
            'analysis': 'Neutral with regulatory uncertainty',
            'period_days': 5,
            'created_at': '2025-03-03T10:00:00'
        },
        {
            'ticker': 'TSLA',
            'rating_score': 4.2,
            'confidence': 0.78,
            'recommendation': 'sell',
            'analysis': 'Elevated valuation concerns',
            'period_days': 5,
            'created_at': '2025-03-03T10:00:00'
        },
    ]


@pytest.fixture
def mock_research_briefs():
    """Generate realistic research brief test data."""
    return [
        {
            'id': 1,
            'ticker': 'AAPL',
            'title': 'Apple Q4 2024: Earnings Beat Analysis',
            'content': 'Apple delivered strong Q4 results exceeding expectations...',
            'ai_generated': True,
            'created_at': '2025-03-03T10:00:00'
        },
        {
            'id': 2,
            'ticker': 'MSFT',
            'title': 'Microsoft AI Strategy: $5B Investment Implications',
            'content': 'Microsoft\'s latest AI investment signals aggressive strategy...',
            'ai_generated': True,
            'created_at': '2025-03-02T14:30:00'
        },
        {
            'id': 3,
            'ticker': 'GOOGL',
            'title': 'Google Search Update: Market Impact',
            'content': 'Recent algorithm changes show focus on enterprise...',
            'ai_generated': True,
            'created_at': '2025-03-01T09:15:00'
        },
    ]


@pytest.fixture
def mock_agents():
    """Generate realistic agent test data."""
    return [
        {
            'id': 1,
            'name': 'research_analyst',
            'role': 'Senior Research Analyst',
            'goal': 'Analyze stocks and generate research briefs',
            'backstory': 'Expert in fundamental and technical analysis',
            'model': 'claude-haiku-4-5-20251001',
            'provider': 'anthropic',
            'enabled': True,
            'tags': ['research', 'analysis'],
            'created_at': '2025-01-01T00:00:00'
        },
        {
            'id': 2,
            'name': 'sentiment_analyst',
            'role': 'Sentiment Analysis Agent',
            'goal': 'Analyze market sentiment from news',
            'backstory': 'Expert in natural language processing and sentiment analysis',
            'model': 'claude-haiku-4-5-20251001',
            'provider': 'anthropic',
            'enabled': True,
            'tags': ['sentiment', 'news'],
            'created_at': '2025-01-02T00:00:00'
        },
        {
            'id': 3,
            'name': 'portfolio_manager',
            'role': 'Portfolio Manager',
            'goal': 'Manage and rebalance portfolio',
            'backstory': 'Expert in portfolio optimization',
            'model': 'claude-haiku-4-5-20251001',
            'provider': 'anthropic',
            'enabled': False,
            'tags': ['portfolio', 'risk'],
            'created_at': '2025-01-03T00:00:00'
        },
    ]


@pytest.fixture
def mock_agent_runs():
    """Generate realistic agent run execution test data."""
    now = datetime.utcnow()
    return [
        {
            'id': 1,
            'agent_name': 'research_analyst',
            'status': 'success',
            'output': 'Generated comprehensive research brief for AAPL',
            'tokens_input': 1250,
            'tokens_output': 3420,
            'estimated_cost': 0.0342,
            'duration_ms': 3450,
            'started_at': (now - timedelta(hours=2)).isoformat(),
            'completed_at': (now - timedelta(hours=1, minutes=58)).isoformat()
        },
        {
            'id': 2,
            'agent_name': 'sentiment_analyst',
            'status': 'success',
            'output': 'Analyzed sentiment from 45 news articles',
            'tokens_input': 2100,
            'tokens_output': 1850,
            'estimated_cost': 0.0285,
            'duration_ms': 2150,
            'started_at': (now - timedelta(hours=1)).isoformat(),
            'completed_at': (now - timedelta(minutes=58)).isoformat()
        },
        {
            'id': 3,
            'agent_name': 'research_analyst',
            'status': 'error',
            'output': 'Failed to fetch data',
            'tokens_input': 500,
            'tokens_output': 0,
            'estimated_cost': 0.0,
            'duration_ms': 1200,
            'started_at': (now - timedelta(minutes=30)).isoformat(),
            'completed_at': (now - timedelta(minutes=29)).isoformat(),
            'error': 'API rate limit exceeded'
        },
    ]


@pytest.fixture
def mock_download_stats():
    """Generate realistic download statistics test data."""
    now = datetime.utcnow()
    return [
        {
            'id': 1,
            'repo_owner': 'tickerpulse',
            'repo_name': 'ai-research',
            'total_downloads': 15420,
            'last_24h': 234,
            'last_7d': 1850,
            'last_30d': 8750,
            'period': 'all',
            'timestamp': now.isoformat()
        },
        {
            'id': 2,
            'repo_owner': 'tickerpulse',
            'repo_name': 'data-toolkit',
            'total_downloads': 8920,
            'last_24h': 128,
            'last_7d': 950,
            'last_30d': 4200,
            'period': 'all',
            'timestamp': now.isoformat()
        },
    ]


@pytest.fixture
def mock_download_daily():
    """Generate realistic daily download breakdown test data."""
    data = []
    for days_ago in range(7):
        date = (datetime.utcnow() - timedelta(days=days_ago)).date()
        data.append({
            'id': days_ago + 1,
            'repo_owner': 'tickerpulse',
            'repo_name': 'ai-research',
            'date': date.isoformat(),
            'downloads': 200 + (days_ago * 10),
            'timestamp': datetime.utcnow().isoformat()
        })
    return data


@pytest.fixture
def mock_ai_providers():
    """Generate realistic AI provider configuration test data."""
    return [
        {
            'id': 1,
            'name': 'Anthropic',
            'provider_id': 'anthropic',
            'api_key_set': True,
            'is_active': True,
            'models': ['claude-opus-4-6', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'],
            'rate_limit': 100000,
            'cost_per_1m_tokens': 15.0,
            'created_at': '2025-01-01T00:00:00'
        },
        {
            'id': 2,
            'name': 'OpenAI',
            'provider_id': 'openai',
            'api_key_set': False,
            'is_active': False,
            'models': ['gpt-4-turbo', 'gpt-4o'],
            'rate_limit': 50000,
            'cost_per_1m_tokens': 30.0,
            'created_at': '2025-01-02T00:00:00'
        },
        {
            'id': 3,
            'name': 'Google',
            'provider_id': 'google',
            'api_key_set': False,
            'is_active': False,
            'models': ['gemini-pro', 'gemini-1-5-pro'],
            'rate_limit': 75000,
            'cost_per_1m_tokens': 20.0,
            'created_at': '2025-01-03T00:00:00'
        },
    ]


# =========================================================================
# FIXTURES: Mock Database Helpers
# =========================================================================

@pytest.fixture
def mock_db_connection():
    """Create a mock database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit = MagicMock()
    mock_conn.rollback = MagicMock()
    mock_conn.close = MagicMock()
    return mock_conn


@contextmanager
def mock_db_session(mock_conn):
    """Context manager for mock database sessions."""
    try:
        yield mock_conn
        mock_conn.commit()
    except Exception:
        mock_conn.rollback()
        raise
    finally:
        mock_conn.close()


@pytest.fixture
def mock_search_stock_ticker():
    """Mock the stock search function."""
    def _search(query: str):
        query_upper = query.upper()
        stocks = {
            'AAPL': {'ticker': 'AAPL', 'name': 'Apple Inc', 'exchange': 'NASDAQ'},
            'MSFT': {'ticker': 'MSFT', 'name': 'Microsoft Corp', 'exchange': 'NASDAQ'},
            'GOOGL': {'ticker': 'GOOGL', 'name': 'Alphabet Inc', 'exchange': 'NASDAQ'},
            'TSLA': {'ticker': 'TSLA', 'name': 'Tesla Inc', 'exchange': 'NASDAQ'},
            'RELIANCE.NS': {'ticker': 'RELIANCE.NS', 'name': 'Reliance Industries', 'exchange': 'BSE'},
        }
        if query_upper in stocks:
            return stocks[query_upper]
        return None
    return _search


# =========================================================================
# FIXTURES: Parametrize Helpers
# =========================================================================

@pytest.fixture
def pagination_test_cases():
    """Common pagination test cases for parameterized tests."""
    return [
        {'limit': 10, 'offset': 0, 'name': 'first_page'},
        {'limit': 20, 'offset': 0, 'name': 'default_limit'},
        {'limit': 50, 'offset': 50, 'name': 'second_page_large'},
        {'limit': 1, 'offset': 0, 'name': 'single_item'},
        {'limit': 100, 'offset': 0, 'name': 'max_limit'},
    ]


@pytest.fixture
def invalid_pagination_cases():
    """Invalid pagination parameters for error testing."""
    return [
        {'limit': 0, 'offset': 0, 'expected_status': 422},
        {'limit': -1, 'offset': 0, 'expected_status': 422},
        {'limit': 101, 'offset': 0, 'expected_status': 422},
        {'limit': 'abc', 'offset': 0, 'expected_status': 422},
        {'limit': 20, 'offset': -1, 'expected_status': 422},
    ]


@pytest.fixture
def chart_period_test_cases():
    """Valid and invalid chart period test cases."""
    return {
        'valid': ['1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'],
        'invalid': ['1h', '30m', '10d', '2y', '10y', 'invalid', '']
    }


# =========================================================================
# UTILITIES
# =========================================================================

def assert_json_response(response, expected_status: int = 200):
    """Assert response is JSON and has expected status."""
    assert response.status_code == expected_status
    assert response.content_type == 'application/json'
    return json.loads(response.data)


def assert_error_response(response, expected_status: int, error_field: str = 'error'):
    """Assert response is an error with expected status."""
    data = assert_json_response(response, expected_status)
    assert error_field in data or 'detail' in data
    return data


def assert_paginated_response(response, expected_status: int = 200):
    """Assert response has pagination metadata."""
    data = assert_json_response(response, expected_status)
    assert 'data' in data
    assert 'meta' in data
    meta = data['meta']
    assert 'total' in meta
    assert 'limit' in meta
    assert 'offset' in meta
    assert 'has_next' in meta
    assert 'has_previous' in meta
    return data
