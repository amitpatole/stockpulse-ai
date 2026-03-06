```python
"""
TickerPulse AI v3.0 - Analysis API Routes
Blueprint for AI ratings and chart data endpoints with optimized caching.
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
    """Try to read pre-computed ratings from ai_ratings table.
    
    Optimization: Select only required columns instead of * for better
    memory efficiency when dealing with potentially large result sets.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT 
                ticker, rating, score, confidence, current_price, price_change, 
                price_change_pct, rsi, sentiment_score, sentiment_label, 
                technical_score, fundamental_score, updated_at
            FROM ai_ratings 
            ORDER BY ticker
        """).fetchall()
        conn.close()
        if rows:
            return [
                {
                    'ticker': r['ticker'],
                    'rating': r['rating'],
                    'score': r['score'] or 0,
                    'confidence': r['confidence'] or 0,
                    'current_price': r['current_price'] or 0,
                    'price_change': r['price_change'] or 0,
                    'price_change_pct': r['price_change_pct'] or 0,
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


def _validate_period_parameter(period_str: str | None) -> tuple[int | None, dict | None]:
    """
    Validate and parse period parameter as integer (1-252).
    
    Returns:
        (period_value, error_response) - either period value is set, or error_response is set
    """
    if period_str is None:
        return None, None
    
    try:
        period = int(period_str)
        if period < 1 or period > 252:
            logger.warning(f"Period out of range: {period} (must be 1-252)")
            return None, (jsonify({
                'error': 'Invalid period parameter',
                'message': 'period must be an integer between 1 and 252',
                'received': period_str
            }), 422)
        return period, None
    except (ValueError, TypeError):
        logger.warning(f"Invalid period parameter: {period_str} (not an integer)")
        return None, (jsonify({
            'error': 'Invalid period parameter',
            'message': 'period must be an integer between 1 and 252',
            'received': period_str
        }), 422)


def _validate_limit_parameter(limit_str: str | None) -> tuple[int | None, dict | None]:
    """
    Validate and parse limit parameter as integer (1-1000).
    
    Returns:
        (limit_value, error_response) - either limit value is set, or error_response is set
    """
    if limit_str is None:
        return None, None
    
    try:
        limit = int(limit_str)
        if limit < 1 or limit > 1000:
            logger.warning(f"Limit out of range: {limit} (must be 1-1000)")
            return None, (jsonify({
                'error': 'Invalid limit parameter',
                'message': 'limit must be an integer between 1 and 1000',
                'received': limit_str
            }), 422)
        return limit, None
    except (ValueError, TypeError):
        logger.warning(f"Invalid limit parameter: {limit_str} (not an integer)")
        return None, (jsonify({
            'error': 'Invalid limit parameter',
            'message': 'limit must be an integer between 1 and 1000',
            'received': limit_str
        }), 422)


@analysis_bp.route('/ai/ratings', methods=['GET'])
def get_ai_ratings():
    """Get AI ratings for all active stocks.

    Query Parameters:
        period (int, optional): Analysis period in days (1-252). Default: None.
        limit (int, optional): Max ratings to return (1-1000). Default: None.

    Serves cached ratings from ai_ratings table, then computes live ratings
    for any active stocks that are missing from the cache.
    
    Optimization: Uses optimized query to get active tickers with index support
    and filters are applied at the database level where possible.
    
    Errors:
        422: Invalid period or limit parameter
    """
    # TP-C02: Validate period parameter
    period_str = request.args.get('period', None)
    if period_str is not None:
        period, error = _validate_period_parameter(period_str)
        if error:
            return error
    
    # TP-C02: Validate limit parameter
    limit_str = request.args.get('limit', None)
    if limit_str is not None:
        limit, error = _validate_limit_parameter(limit_str)
        if error:
            return error
    
    analytics = StockAnalytics()

    # Optimization: Get only ticker column from active stocks using indexed query
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        active_tickers = {
            row['ticker']
            for row in conn.execute("SELECT ticker FROM stocks WHERE active = 1 ORDER BY ticker").fetchall()
        }
        conn.close()
    except Exception:
        active_tickers = set()

    # Try cached ratings
    cached = _get_cached_ratings()
    cached_map = {}
    if cached:
        cached_map = {r['ticker']: r for r in cached}

    # Find active stocks missing from cache
    missing = active_tickers - set(cached_map.keys())

    # Compute live ratings for missing stocks
    for ticker in missing:
        try:
            rating = analytics.calculate_ai_rating(ticker)
            cached_map[ticker] = rating
        except Exception as e:
            logger.error(f"Error calculating rating for {ticker}: {e}")
            cached_map[ticker] = {
                'ticker': ticker,
                'rating': 'ERROR',
                'score': 0,
                'confidence': 0,
                'message': str(e)
            }

    # Return only active stocks, sorted by ticker
    results = [cached_map[t] for t in sorted(active_tickers) if t in cached_map]
    
    # Apply limit if specified
    if limit_str is not None and limit > 0:
        results = results[:limit]
    
    return jsonify(results)


@analysis_bp.route('/ai/rating/<ticker>', methods=['GET'])
def get_ai_rating(ticker):
    """Get AI rating for a specific stock.
    
    Optimization: Uses indexed ticker lookup for efficient single-record retrieval.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT ticker, rating, score, confidence, current_price, price_change, price_change_pct, rsi, sentiment_score, sentiment_label, technical_score, fundamental_score, updated_at FROM ai_ratings WHERE ticker = ?", 
            (ticker.upper(),)
        ).fetchone()
        conn.close()
        if row:
            return jsonify(dict(row))
    except Exception:
        pass
    
    # Fall back to live calculation
    analytics = StockAnalytics()
    rating = analytics.calculate_ai_rating(ticker)
    return jsonify(rating)


@analysis_bp.route('/chart/<ticker>', methods=['GET'])
def get_chart_data(ticker: str):
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
        400: Invalid period parameter
        404: No data available or no valid data points.
    """
    # Validate and sanitize period parameter
    VALID_PERIODS = {'1d', '5d', '1mo', '3mo', '6mo', '1y', '5y', 'max'}
    period = request.args.get('period', '1mo').strip().lower()

    if period not in VALID_PERIODS:
        logger.warning(f"Invalid period requested: {period} for ticker {ticker}")
        return jsonify({
            'error': 'Invalid period parameter',
            'message': f"Period must be one of: {', '.join(sorted(VALID_PERIODS))}",
            'received': period
        }), 400

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
```