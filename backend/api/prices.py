"""
TickerPulse AI v3.0 - Prices API Routes
Blueprint for real-time and batch price endpoints.

Optimization: Uses batch_get_stocks_by_tickers() to avoid N+1 lookups.
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

from backend.core.query_optimizer import batch_get_stocks_by_tickers, get_active_stocks_optimized
from backend.database import db_session

logger = logging.getLogger(__name__)

prices_bp = Blueprint('prices', __name__, url_prefix='/api')


@prices_bp.route('/prices', methods=['GET'])
def get_all_prices() -> tuple[Dict[str, Any], int]:
    """Get current prices for all monitored stocks.

    Query Parameters:
        tickers (str, optional): Comma-separated list of tickers to fetch prices for.
                                 If omitted, returns all active stocks.
        market (str, optional): Filter by market ('US', 'India', 'All'). Default: 'All'.

    Returns (200):
        {
            "data": [
                {
                    "ticker": "AAPL",
                    "price": 175.50,
                    "currency": "USD",
                    "change": 2.30,
                    "change_pct": 1.32,
                    "timestamp": "2026-03-03T15:30:00Z",
                    "market": "US"
                },
                ...
            ],
            "meta": {
                "count": 45,
                "timestamp": "2026-03-03T15:30:00Z"
            }
        }

    Optimization:
        - Batch lookup with IN clause (one query, not N queries)
        - SQL-side market filtering (idx_stocks_active_market)
        - Selects only needed columns
    """
    try:
        # Get requested tickers (comma-separated)
        tickers_param = request.args.get('tickers', '')
        market = request.args.get('market', 'All')

        tickers_to_fetch = []
        if tickers_param:
            # User specified specific tickers
            tickers_to_fetch = [t.strip().upper() for t in tickers_param.split(',') if t.strip()]
        else:
            # Fetch all active stocks (SQL-side filtered)
            stocks, _ = get_active_stocks_optimized(market=market, limit=1000, offset=0)
            tickers_to_fetch = [s['ticker'] for s in stocks]

        if not tickers_to_fetch:
            return jsonify({
                'data': [],
                'meta': {'count': 0, 'timestamp': ''}
            }), 200

        # Batch fetch all stocks in a single query (OPTIMIZATION: NOT O(n) loop)
        stocks_dict = batch_get_stocks_by_tickers(tickers_to_fetch)

        # Format response
        prices_data = [
            {
                'ticker': ticker,
                'price': stock.get('current_price', 0),
                'currency': 'USD' if not ticker.endswith(('.NS', '.BO')) else 'INR',
                'change': stock.get('price_change', 0),
                'change_pct': stock.get('price_change_pct', 0),
                'timestamp': stock.get('updated_at', ''),
                'market': stock.get('market', 'US')
            }
            for ticker, stock in stocks_dict.items()
        ]

        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).isoformat()

        return jsonify({
            'data': prices_data,
            'meta': {
                'count': len(prices_data),
                'timestamp': timestamp
            }
        }), 200

    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        return jsonify({
            'error': 'Internal server error',
            'data': [],
            'meta': {'count': 0}
        }), 500


@prices_bp.route('/prices/<ticker>', methods=['GET'])
def get_price(ticker: str) -> tuple[Dict[str, Any], int]:
    """Get current price for a specific stock.

    Path Parameters:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'RELIANCE.NS')

    Returns (200):
        {
            "ticker": "AAPL",
            "price": 175.50,
            "currency": "USD",
            "change": 2.30,
            "change_pct": 1.32,
            "rsi": 65.4,
            "sentiment_score": 0.72,
            "rating": "BUY",
            "timestamp": "2026-03-03T15:30:00Z",
            "market": "US"
        }

    Errors:
        404: Ticker not found in database

    Optimization:
        - Uses batch_get_stocks_by_tickers (single indexed lookup, not linear search)
        - Selects only needed columns
    """
    ticker_upper = ticker.upper()

    try:
        # Batch fetch (even for single ticker, uses indexed path)
        stocks_dict = batch_get_stocks_by_tickers([ticker_upper])

        if not stocks_dict:
            return jsonify({
                'error': 'Ticker not found',
                'message': f'No price data available for ticker: {ticker_upper}'
            }), 404

        stock = stocks_dict[ticker_upper]

        # Get rating data for additional context
        with db_session() as conn:
            cursor = conn.cursor()
            rating_row = cursor.execute(
                'SELECT rating, rsi, sentiment_score FROM ai_ratings WHERE ticker = ?',
                (ticker_upper,)
            ).fetchone()

        price_data = {
            'ticker': ticker_upper,
            'price': stock.get('current_price', 0),
            'currency': 'USD' if not ticker_upper.endswith(('.NS', '.BO')) else 'INR',
            'change': stock.get('price_change', 0),
            'change_pct': stock.get('price_change_pct', 0),
            'market': stock.get('market', 'US'),
            'timestamp': stock.get('updated_at', '')
        }

        # Add rating info if available
        if rating_row:
            price_data.update({
                'rsi': rating_row['rsi'] or 0,
                'sentiment_score': rating_row['sentiment_score'] or 0,
                'rating': rating_row['rating'] or 'UNKNOWN'
            })

        return jsonify(price_data), 200

    except Exception as e:
        logger.error(f"Error fetching price for {ticker}: {e}")
        return jsonify({'error': 'Internal server error'}), 500
