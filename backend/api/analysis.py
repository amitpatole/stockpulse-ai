"""
StockPulse AI v3.0 - Analysis API Routes
Blueprint for AI ratings and chart data endpoints.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import sqlite3
import logging

from backend.core.ai_analytics import StockAnalytics
from backend.config import Config

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')


def _get_cached_ratings():
    """Try to read pre-computed ratings from ai_ratings table."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT r.*, s.current_price as live_price, s.price_change as live_change,
                   s.price_change_pct as live_change_pct
            FROM ai_ratings r
            LEFT JOIN stocks s ON r.ticker = s.ticker
            ORDER BY r.ticker
        """).fetchall()
        conn.close()
        if rows:
            return [
                {
                    'ticker': r['ticker'],
                    'rating': r['rating'],
                    'score': r['score'] or 0,
                    'confidence': r['confidence'] or 0,
                    'current_price': r['live_price'] or r['current_price'] or 0,
                    'price_change': r['live_change'] or r['price_change'] or 0,
                    'price_change_pct': r['live_change_pct'] or r['price_change_pct'] or 0,
                    'rsi': r['rsi'] or 0,
                    'sentiment_score': r['sentiment_score'] or 0,
                    'sentiment_label': r['sentiment_label'] or 'neutral',
                    'technical_score': r['technical_score'] or 0,
                    'fundamental_score': r['fundamental_score'] or 0,
                    'updated_at': r['updated_at'],
                }
                for r in rows
            ]
    except Exception as e:
        logger.debug(f"No cached ratings: {e}")
    return None


@analysis_bp.route('/ai/ratings', methods=['GET'])
def get_ai_ratings():
    """Get AI ratings for all active stocks."""
    # First try pre-computed ratings from DB
    cached = _get_cached_ratings()
    if cached:
        return jsonify(cached)
    # Fall back to live calculation
    analytics = StockAnalytics()
    ratings = analytics.get_all_ratings()
    return jsonify(ratings)


@analysis_bp.route('/ai/rating/<ticker>', methods=['GET'])
def get_ai_rating(ticker):
    """Get AI rating for a specific stock."""
    # Try cached first
    cached = _get_cached_ratings()
    if cached:
        for r in cached:
            if r['ticker'].upper() == ticker.upper():
                return jsonify(r)
    # Fall back to live calculation
    analytics = StockAnalytics()
    rating = analytics.calculate_ai_rating(ticker)
    return jsonify(rating)


@analysis_bp.route('/chart/<ticker>', methods=['GET'])
def get_chart_data(ticker):
    """Get historical price data for chart rendering.

    Path Parameters:
        ticker (str): Stock ticker symbol.

    Query Parameters:
        period (str, optional): Time period for data. Defaults to '1mo'.
            Accepted values: '1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'.

    Returns:
        JSON object with:
        - ticker: Stock symbol
        - period: Requested period
        - data: Array of OHLCV data points with timestamps
        - currency_symbol: '$' or currency symbol based on market
        - stats: Summary statistics (current_price, high, low, change, volume)

    Errors:
        404: No data available or no valid data points.
    """
    period = request.args.get('period', '1mo')
    analytics = StockAnalytics()
    price_data = analytics.get_stock_price_data(ticker, period)

    if not price_data or not price_data.get('close'):
        return jsonify({'error': 'No data available'}), 404

    # Filter out None values and prepare data
    timestamps = price_data.get('timestamps', [])
    closes = price_data.get('close', [])
    opens = price_data.get('open', [])
    highs = price_data.get('high', [])
    lows = price_data.get('low', [])
    volumes = price_data.get('volume', [])

    # Create clean data points
    data_points = []
    for i in range(len(timestamps)):
        if closes[i] is not None:
            data_points.append({
                'timestamp': timestamps[i],
                'date': datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d'),
                'open': opens[i],
                'high': highs[i],
                'low': lows[i],
                'close': closes[i],
                'volume': volumes[i]
            })

    if not data_points:
        return jsonify({'error': 'No valid data points'}), 404

    # Calculate price change
    first_price = data_points[0]['close']
    last_price = data_points[-1]['close']
    price_change = last_price - first_price
    price_change_percent = (price_change / first_price) * 100 if first_price else 0

    # Determine currency
    is_indian = '.NS' in ticker.upper() or '.BO' in ticker.upper()
    currency_symbol = '\u20b9' if is_indian else '$'

    return jsonify({
        'ticker': ticker,
        'period': period,
        'data': data_points,
        'currency_symbol': currency_symbol,
        'stats': {
            'current_price': last_price,
            'open_price': first_price,
            'high_price': max([p['high'] for p in data_points if p['high']]),
            'low_price': min([p['low'] for p in data_points if p['low']]),
            'price_change': price_change,
            'price_change_percent': price_change_percent,
            'total_volume': sum([p['volume'] for p in data_points if p['volume']])
        }
    })
