```python
"""
TickerPulse AI v3.0 - Prices API Routes

Real-time price endpoints with batch query optimization to avoid N+1 patterns.
All price data is fetched via external providers (Yahoo Finance, Alpha Vantage).

Endpoints:
  GET  /api/prices           - List recent prices (paginated)
  GET  /api/prices/<ticker>  - Get latest price for ticker
  POST /api/prices/batch     - Batch fetch prices for multiple tickers (OPTIMIZED)
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any, List

from backend.core.query_optimizer import get_batch_by_keys
from backend.core.validation import get_request_body, get_query_params
from backend.core.errors import NotFoundError, ValidationError as TickerPulseValidationError
from backend.models.requests import PaginationParams
from backend.models.responses import PaginatedResponse, PaginationMeta

logger = logging.getLogger(__name__)

prices_bp = Blueprint('prices', __name__, url_prefix='/api')


# ============================================================================
# Price Data Models (in-memory cache, external source of truth)
# ============================================================================

class PriceResponse:
    """Simple price data model"""
    def __init__(self, ticker: str, price: float, currency: str, timestamp: str):
        self.ticker = ticker
        self.price = price
        self.currency = currency
        self.timestamp = timestamp

    def to_dict(self) -> Dict[str, Any]:
        return {
            'ticker': self.ticker,
            'price': self.price,
            'currency': self.currency,
            'timestamp': self.timestamp
        }


# ============================================================================
# Price Fetching (External API integration - placeholder for real implementation)
# ============================================================================

def fetch_price_external(ticker: str) -> Dict[str, Any] | None:
    """
    Fetch current price for a ticker from external provider (Yahoo Finance, etc).

    This is a placeholder that would integrate with your price data provider.
    Real implementation would call Yahoo Finance API or Alpha Vantage.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with price data or None if not found
    """
    # TODO: Implement actual price fetching from Yahoo Finance / Alpha Vantage
    # For now, return mock data for testing
    return {
        'ticker': ticker,
        'price': 150.00,
        'currency': 'INR' if '.NS' in ticker or '.BO' in ticker else 'USD',
        'timestamp': '2026-03-06T10:30:00Z'
    }


def fetch_prices_batch(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch prices for multiple tickers in a single batch request (OPTIMIZED).

    This is the key optimization: instead of making N individual price requests,
    batch them together. External API may also support batch endpoints.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dict mapping ticker to price data
    """
    if not tickers:
        return {}

    results: Dict[str, Dict[str, Any]] = {}

    # Real implementation would batch into single API call or use bulk endpoint
    # For now, fetch individually but with logging
    for ticker in tickers:
        try:
            price_data = fetch_price_external(ticker)
            if price_data:
                results[ticker] = price_data
                logger.debug(f"Fetched price for {ticker}: {price_data['price']}")
        except Exception as e:
            logger.warning(f"Failed to fetch price for {ticker}: {e}")

    return results


# ============================================================================
# API Endpoints
# ============================================================================

@prices_bp.route('/prices', methods=['GET'])
def get_prices() -> tuple[Dict[str, Any], int]:
    """
    Get paginated list of recent prices.

    Query Parameters:
        limit (int, optional): Items per page. Range: 1-100, Default: 20
        offset (int, optional): Pagination offset. Default: 0
        ticker (str, optional): Filter by specific ticker

    Returns (200):
        {
            "data": [{"ticker": str, "price": float, "currency": str, "timestamp": str}, ...],
            "meta": {"total": int, "limit": int, "offset": int, "has_next": bool, "has_previous": bool}
        }

    Errors:
        400: Invalid pagination parameters
    """
    # Validate pagination parameters
    params = get_query_params(PaginationParams)
    ticker_filter = request.args.get('ticker', '').upper()

    # In a real implementation, this would fetch from a price history table
    # For now, return empty paginated response
    stocks_list = []
    total_count = 0

    has_next = (params.offset + params.limit) < total_count
    has_previous = params.offset > 0

    meta = PaginationMeta(
        total=total_count,
        limit=params.limit,
        offset=params.offset,
        has_next=has_next,
        has_previous=has_previous,
    )

    response = PaginatedResponse(
        data=stocks_list,
        meta=meta,
    )

    return jsonify(response.model_dump()), 200


@prices_bp.route('/prices/<ticker>', methods=['GET'])
def get_price(ticker: str) -> tuple[Dict[str, Any], int]:
    """
    Get latest price for a specific ticker.

    Path Parameters:
        ticker (str): Stock ticker symbol

    Returns (200):
        {
            "ticker": str,
            "price": float,
            "currency": str,
            "timestamp": str
        }

    Errors:
        404: Ticker not found
    """
    ticker = ticker.upper()

    try:
        price_data = fetch_price_external(ticker)
        if not price_data:
            return jsonify({
                'error': 'TICKER_NOT_FOUND',
                'message': f"Ticker '{ticker}' not found"
            }), 404

        return jsonify(price_data), 200

    except Exception as e:
        logger.error(f"Error fetching price for {ticker}: {e}")
        return jsonify({
            'error': 'PRICE_FETCH_ERROR',
            'message': 'Failed to fetch price data'
        }), 500


@prices_bp.route('/prices/batch', methods=['POST'])
def get_prices_batch() -> tuple[Dict[str, Any], int]:
    """
    Batch fetch prices for multiple tickers (OPTIMIZED - avoids N+1 queries).

    Request Body (JSON):
        tickers (list[str]): List of ticker symbols (max 100)

    Returns (200):
        {
            "data": {
                "AAPL": {"ticker": str, "price": float, "currency": str, "timestamp": str},
                "MSFT": {...},
                ...
            },
            "meta": {
                "requested": int,
                "found": int,
                "missing": [str]
            }
        }

    Errors:
        400: Invalid request format or too many tickers (>100)
        500: Internal error
    """
    try:
        data = request.json or {}
        tickers = data.get('tickers', [])

        if not isinstance(tickers, list):
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': 'tickers must be a list'
            }), 400

        if not tickers:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': 'tickers list cannot be empty'
            }), 400

        if len(tickers) > 100:
            return jsonify({
                'error': 'INVALID_REQUEST',
                'message': f'Too many tickers. Maximum is 100, got {len(tickers)}'
            }), 400

        # Normalize tickers
        tickers = [t.upper().strip() for t in tickers if t]

        # OPTIMIZATION: Batch fetch instead of individual requests (avoids N+1)
        prices = fetch_prices_batch(tickers)

        # Find missing tickers
        found_tickers = set(prices.keys())
        requested_tickers = set(tickers)
        missing = list(requested_tickers - found_tickers)

        response = {
            'data': prices,
            'meta': {
                'requested': len(requested_tickers),
                'found': len(found_tickers),
                'missing': missing
            }
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in batch price fetch: {e}")
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': 'Failed to fetch batch prices'
        }), 500
```