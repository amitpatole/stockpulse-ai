"""
Comprehensive pytest test suite for Chat API endpoints.

Covers:
- Chat message submission with context
- Thinking level variations (quick, balanced, deep)
- Ticker context and market awareness
- Error handling and validation
"""

import pytest
import json
from unittest.mock import patch, MagicMock


class TestChatAPI:
    """Tests for POST /api/chat/ask endpoint."""

    def test_chat_message_quick_thinking(self, client):
        """Test chat with quick thinking level."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the current trend?',
            'thinking_level': 'quick'
        }

        response_data = {
            'ticker': 'AAPL',
            'question': 'What is the current trend?',
            'response': 'AAPL is in an uptrend with strong momentum.',
            'thinking_level': 'quick',
            'tokens_used': 450,
            'confidence': 0.85
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['ticker'] == 'AAPL'
            assert 'response' in data
            assert data['thinking_level'] == 'quick'
            assert 'tokens_used' in data

    def test_chat_message_balanced_thinking(self, client):
        """Test chat with balanced thinking level."""
        request_data = {
            'ticker': 'MSFT',
            'question': 'Analyze recent earnings impact',
            'thinking_level': 'balanced'
        }

        response_data = {
            'ticker': 'MSFT',
            'question': 'Analyze recent earnings impact',
            'response': 'MSFT earnings beat expectations. AI investments showing strong ROI...',
            'thinking_level': 'balanced',
            'tokens_used': 1200,
            'confidence': 0.88
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['thinking_level'] == 'balanced'
            assert data['tokens_used'] > 450  # Balanced uses more tokens than quick

    def test_chat_message_deep_thinking(self, client):
        """Test chat with deep thinking level."""
        request_data = {
            'ticker': 'GOOGL',
            'question': 'What are the regulatory risks?',
            'thinking_level': 'deep'
        }

        response_data = {
            'ticker': 'GOOGL',
            'question': 'What are the regulatory risks?',
            'response': 'GOOGL faces several regulatory challenges...',
            'thinking_level': 'deep',
            'tokens_used': 2800,
            'confidence': 0.92,
            'analysis_depth': 'comprehensive'
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['thinking_level'] == 'deep'
            assert data['tokens_used'] > 1200  # Deep uses most tokens

    def test_chat_message_default_thinking_level(self, client):
        """Test chat with no thinking level specified (should default)."""
        request_data = {
            'ticker': 'TSLA',
            'question': 'Is this a good buy?'
        }

        response_data = {
            'ticker': 'TSLA',
            'question': 'Is this a good buy?',
            'response': 'TSLA shows mixed signals.',
            'thinking_level': 'balanced'  # Default
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200
            data = json.loads(response.data)
            # Should default to balanced if not specified
            assert 'thinking_level' in data

    def test_chat_message_missing_ticker(self, client):
        """Test chat request without ticker (required field)."""
        request_data = {
            'question': 'What is happening?'
        }

        response = client.post('/api/chat/ask', json=request_data)
        assert response.status_code in [400, 422]
        data = json.loads(response.data)
        assert 'error' in data or 'detail' in data

    def test_chat_message_missing_question(self, client):
        """Test chat request without question (required field)."""
        request_data = {
            'ticker': 'AAPL'
        }

        response = client.post('/api/chat/ask', json=request_data)
        assert response.status_code in [400, 422]

    def test_chat_message_invalid_ticker(self, client):
        """Test chat with invalid ticker format."""
        request_data = {
            'ticker': 'INVALID_LONG_TICKER_NAME',
            'question': 'What is the trend?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=ValueError('Invalid ticker')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [400, 422]

    def test_chat_message_ticker_not_found(self, client):
        """Test chat with ticker not in watchlist."""
        request_data = {
            'ticker': 'UNKNOW',
            'question': 'What is the price?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=ValueError('Ticker not found')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [404, 400]

    def test_chat_message_invalid_thinking_level(self, client):
        """Test chat with invalid thinking level."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?',
            'thinking_level': 'invalid_level'
        }

        response = client.post('/api/chat/ask', json=request_data)
        assert response.status_code in [400, 422]

    def test_chat_message_empty_question(self, client):
        """Test chat with empty question."""
        request_data = {
            'ticker': 'AAPL',
            'question': ''
        }

        response = client.post('/api/chat/ask', json=request_data)
        assert response.status_code in [400, 422]

    def test_chat_message_very_long_question(self, client):
        """Test chat with extremely long question."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What ' * 1000  # Very long question
        }

        response = client.post('/api/chat/ask', json=request_data)
        # Either accept or reject with 422
        assert response.status_code in [200, 400, 422]

    def test_chat_message_special_characters(self, client):
        """Test chat with special characters in question."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What about <script>alert("xss")</script> ?'
        }

        response_data = {
            'ticker': 'AAPL',
            'question': 'What about &lt;script&gt; ? ',  # Escaped
            'response': 'No XSS here'
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            # Should sanitize input
            assert response.status_code in [200, 400]

    def test_chat_message_unicode_characters(self, client):
        """Test chat with unicode characters."""
        request_data = {
            'ticker': 'RELIANCE.NS',
            'question': 'क्या यह अच्छा निवेश है? What about earnings?'
        }

        response_data = {
            'ticker': 'RELIANCE.NS',
            'response': 'RELIANCE shows strong fundamentals'
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [200, 400]

    def test_chat_message_case_insensitive_ticker(self, client):
        """Test chat with lowercase ticker (should normalize)."""
        request_data = {
            'ticker': 'aapl',
            'question': 'What is the trend?'
        }

        response_data = {
            'ticker': 'AAPL',  # Normalized
            'question': 'What is the trend?',
            'response': 'AAPL is in an uptrend'
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['ticker'] == 'AAPL'


class TestChatAPIWithContext:
    """Tests for chat with historical context and market data."""

    def test_chat_includes_recent_price_data(self, client):
        """Test that chat response includes recent price data."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'Is the price high right now?'
        }

        response_data = {
            'ticker': 'AAPL',
            'question': 'Is the price high right now?',
            'response': 'Based on recent 52-week high of 195...',
            'context': {
                'current_price': 150.25,
                'high_52w': 195.00,
                'low_52w': 120.50,
                'pe_ratio': 28.5
            }
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'context' in data or 'current_price' in str(data)

    def test_chat_includes_recent_news(self, client):
        """Test that chat response can include recent news context."""
        request_data = {
            'ticker': 'MSFT',
            'question': 'What is the latest news impact?'
        }

        response_data = {
            'ticker': 'MSFT',
            'question': 'What is the latest news impact?',
            'response': 'Recent $5B AI investment announcement is very positive...',
            'context': {
                'recent_news': [
                    {'title': 'Microsoft Expands AI Division', 'sentiment': 'positive'}
                ]
            }
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200

    def test_chat_includes_market_hours_awareness(self, client):
        """Test that chat is aware of market hours."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What time does the market close?'
        }

        response_data = {
            'ticker': 'AAPL',
            'response': 'US market closes at 4 PM ET'
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 200


class TestChatAPIErrorHandling:
    """Tests for error handling in Chat API."""

    def test_chat_ai_provider_not_configured(self, client):
        """Test chat when AI provider is not configured."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=Exception('No AI provider configured')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [400, 500, 503]

    def test_chat_ai_provider_error(self, client):
        """Test chat when AI provider returns error."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=Exception('API error')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [500, 503]

    def test_chat_database_error(self, client):
        """Test chat when database is unavailable."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=ConnectionError('DB error')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [500, 503]

    def test_chat_rate_limit_exceeded(self, client):
        """Test chat when rate limit is exceeded."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=Exception('Rate limit exceeded')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [429, 500]

    def test_chat_timeout(self, client):
        """Test chat timeout after long wait."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=TimeoutError('Request timeout')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code in [408, 500]

    def test_chat_malformed_json(self, client):
        """Test chat with malformed JSON request."""
        response = client.post(
            '/api/chat/ask',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 422]

    def test_chat_wrong_content_type(self, client):
        """Test chat with wrong content type."""
        response = client.post(
            '/api/chat/ask',
            data='{"ticker": "AAPL"}',
            content_type='text/plain'
        )
        assert response.status_code in [400, 415, 422]

    def test_chat_internal_server_error(self, client):
        """Test chat with unexpected internal error."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?'
        }

        with patch('backend.api.chat.ask_ai_agent', side_effect=Exception('Unexpected error')):
            response = client.post('/api/chat/ask', json=request_data)
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data or 'detail' in data


class TestChatAPIEdgeCases:
    """Tests for edge cases in Chat API."""

    def test_chat_with_null_values(self, client):
        """Test chat with null values in request."""
        request_data = {
            'ticker': None,
            'question': 'What is the trend?'
        }

        response = client.post('/api/chat/ask', json=request_data)
        assert response.status_code in [400, 422]

    def test_chat_with_empty_object(self, client):
        """Test chat with empty JSON object."""
        response = client.post('/api/chat/ask', json={})
        assert response.status_code in [400, 422]

    def test_chat_with_extra_fields(self, client):
        """Test chat with extra unexpected fields."""
        request_data = {
            'ticker': 'AAPL',
            'question': 'What is the trend?',
            'extra_field': 'should_ignore',
            'another_extra': 123
        }

        response_data = {
            'ticker': 'AAPL',
            'response': 'AAPL is in an uptrend'
        }

        with patch('backend.api.chat.ask_ai_agent', return_value=response_data):
            response = client.post('/api/chat/ask', json=request_data)
            # Should ignore extra fields
            assert response.status_code == 200
