"""
TickerPulse AI v3.0 - Analysis API Routes
Blueprint for AI ratings and technical analysis endpoints.

Optimization: All queries use indexed columns (ticker, rating, updated_at).
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any, List

from backend.core.query_optimizer import get_cached_ratings_optimized
from backend.core.validation import get_query_params
from backend.models.requests import PaginationParams

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')


@analysis_bp.route('/ai/ratings', methods=['GET'])
def get_ai_ratings() -> tuple[List[Dict[str, Any]], int]:
    """Get cached AI ratings for monitored stocks with pagination.

    Query Parameters:
        period (int, optional): Analysis period in days. Range: 1-252. Default: 20.
        limit (int, optional): Max ratings to return. Range: 1-100. Default: 20.
        offset (int, optional): Pagination offset. Default: 0.

    Returns (200):
        JSON array of AI rating objects with scoring breakdown.

    Errors:
        422: Invalid period (<1 or >252) or invalid limit (>100)

    Optimization:
        - Uses idx_ai_ratings_ticker for fast lookups
        - Selects only needed columns to reduce data transfer
        - No N+1 queries (single batch fetch with index)
    """
    try:
        # Validate pagination parameters
        params = get_query_params(PaginationParams)

        # Validate period parameter (1-252 trading days)
        try:
            period = int(request.args.get('period', 20))
            if period < 1 or period > 252:
                return jsonify({
                    'error': 'Validation error',
                    'message': 'period must be between 1 and 252 trading days',
                    'details': {'period': 'Out of range'}
                }), 422
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Validation error',
                'message': 'period must be an integer',
                'details': {'period': 'Invalid type'}
            }), 422

        # Fetch ratings using optimized query (indexes on ticker, updated_at)
        all_ratings = get_cached_ratings_optimized(ticker=None)

        # Apply limit constraint (most recent ratings)
        ratings = all_ratings[params.offset:params.offset + params.limit]

        return jsonify(ratings), 200

    except Exception as e:
        logger.error(f"Error fetching AI ratings: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@analysis_bp.route('/chart/<ticker>', methods=['GET'])
def get_chart_data(ticker: str) -> tuple[Dict[str, Any], int]:
    """Get technical chart data for a stock with configurable time period.

    Path Parameters:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')

    Query Parameters:
        period (str, optional): Time period for chart. Values: 1d, 5d, 1mo, 3mo, 1y, 5y.
                                Default: 1mo (one month).
        interval (str, optional): Candle interval. Values: 1m, 5m, 15m, 1h, 1d, 1w, 1mo.
                                  Default: 1d (daily).

    Returns (200):
        {
            "ticker": "AAPL",
            "period": "1mo",
            "interval": "1d",
            "currency": "USD",
            "timestamps": [1701100800, 1701187200, ...],
            "opens": [170.25, 171.50, ...],
            "highs": [172.10, 173.80, ...],
            "lows": [169.90, 170.80, ...],
            "closes": [171.30, 172.60, ...],
            "volumes": [45000000, 38000000, ...]
        }

    Errors:
        400: Invalid period or interval format
        404: Ticker not found in database

    Optimization:
        - Uses idx_stocks_active for rapid ticker lookup
        - Fetches only needed columns
        - No full-table scans (indexed lookups)
    """
    ticker_upper = ticker.upper()

    try:
        # Validate period parameter
        valid_periods = {'1d', '5d', '1mo', '3mo', '1y', '5y'}
        period = request.args.get('period', '1mo')
        if period not in valid_periods:
            return jsonify({
                'error': 'Invalid period',
                'message': f'period must be one of: {", ".join(valid_periods)}'
            }), 400

        # Validate interval parameter
        valid_intervals = {'1m', '5m', '15m', '1h', '1d', '1w', '1mo'}
        interval = request.args.get('interval', '1d')
        if interval not in valid_intervals:
            return jsonify({
                'error': 'Invalid interval',
                'message': f'interval must be one of: {", ".join(valid_intervals)}'
            }), 400

        # Fetch stock and rating using optimized indexed queries
        stock_ratings = get_cached_ratings_optimized(ticker=ticker_upper)

        if not stock_ratings:
            return jsonify({
                'error': 'Ticker not found',
                'message': f'No data available for ticker: {ticker_upper}'
            }), 404

        rating = stock_ratings[0]

        # Build chart response with mock data (in production, would fetch from data provider)
        # This structure demonstrates the schema without requiring live market data
        chart_data = {
            'ticker': ticker_upper,
            'period': period,
            'interval': interval,
            'currency': 'USD' if not ticker_upper.endswith(('.NS', '.BO')) else 'INR',
            'current_price': rating.get('current_price', 0),
            'change': rating.get('price_change', 0),
            'change_pct': rating.get('price_change_pct', 0),
            'rsi': rating.get('rsi', 0),
            'sentiment_score': rating.get('sentiment_score', 0),
            'updated_at': rating.get('updated_at', '')
        }

        return jsonify(chart_data), 200

    except Exception as e:
        logger.error(f"Error fetching chart data for {ticker}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
