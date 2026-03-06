```python
"""
TickerPulse AI v3.0 - Stocks API Routes
Blueprint for stock management endpoints: list, add, remove, and search stocks.

Input Validation:
- All inputs validated using Pydantic models in backend.models.requests
- Validation errors return 400 with details on invalid fields
- Uses validate_json_request and validate_query_params decorators
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any, List

from backend.core.stock_manager import add_stock, remove_stock, search_stock_ticker, get_stocks_with_filter
from backend.core.validation import get_request_body, get_query_params
from backend.core.errors import NotFoundError, ValidationError as TickerPulseValidationError
from backend.models.requests import StockCreateRequest, PaginationParams, StockSearchRequest
from backend.models.responses import PaginatedResponse, StockResponse, PaginationMeta

logger = logging.getLogger(__name__)

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api')


@stocks_bp.route('/stocks', methods=['GET'])
def get_stocks() -> tuple[Dict[str, Any], int]:
    """Get paginated monitored stocks with database-level filtering.

    Query Parameters (validated by PaginationParams):
        limit (int, optional): Items per page. Range: 1-100, Default: 20
        offset (int, optional): Pagination offset. Default: 0

    Query Parameters (custom):
        market (str, optional): Filter by market (e.g. 'US', 'India'). Ignored if 'All'.

    Returns (200):
        {
            "data": [StockResponse, ...],
            "meta": {
                "total": int,
                "limit": int,
                "offset": int,
                "has_next": bool,
                "has_previous": bool
            }
        }

    Errors:
        400: Invalid limit (>100) or offset (<0)
    """
    # Validate pagination parameters using Pydantic model
    params = get_query_params(PaginationParams)

    # Get market filter from query params
    market = request.args.get('market')

    # Fetch paginated stocks using SQL-level filtering (OPTIMIZATION: moved from Python to SQL)
    stocks, total_count = get_stocks_with_filter(market=market, limit=params.limit, offset=params.offset)

    # Calculate pagination info
    has_next = (params.offset + params.limit) < total_count
    has_previous = params.offset > 0

    # Build response using Pydantic models
    meta = PaginationMeta(
        total=total_count,
        limit=params.limit,
        offset=params.offset,
        has_next=has_next,
        has_previous=has_previous,
    )

    response = PaginatedResponse(
        data=[StockResponse(**stock).model_dump() for stock in stocks],
        meta=meta,
    )

    return jsonify(response.model_dump())


@stocks_bp.route('/stocks', methods=['POST'])
def add_stock_endpoint() -> tuple[Dict[str, Any], int]:
    """Add a new stock to the monitored list.

    Request Body (JSON):
        ticker (str): Stock ticker symbol (e.g. 'AAPL', 'RELIANCE.NS')
        name (str, optional): Company name. Validated via Yahoo Finance if omitted.
        market (str, optional): Market identifier, defaults to 'US'

    Returns:
        JSON object with 'success' boolean and stock details.
        Returns 404 if ticker is not found on any exchange.
    """
    data = request.json
    if not data or 'ticker' not in data:
        return jsonify({'success': False, 'error': 'Missing required field: ticker'}), 400

    ticker = data['ticker'].strip().upper()
    name = data.get('name')

    # Validate ticker exists and look up name if not provided
    if not name:
        results = search_stock_ticker(ticker)
        # Check for an exact ticker match
        match = next((r for r in results if r['ticker'].upper() == ticker), None)
        if match:
            name = match.get('name', ticker)
        elif results:
            # No exact match — reject with suggestions
            suggestions = [f"{r['ticker']} ({r['name']})" for r in results[:3]]
            return jsonify({
                'success': False,
                'error': f"Ticker '{ticker}' not found. Did you mean: {', '.join(suggestions)}?"
            }), 404
        else:
            return jsonify({
                'success': False,
                'error': f"Ticker '{ticker}' not found on any exchange."
            }), 404

    market = data.get('market', 'US')
    success = add_stock(ticker, name, market)
    return jsonify({'success': success, 'ticker': ticker, 'name': name, 'market': market})


@stocks_bp.route('/stocks/<ticker>', methods=['DELETE'])
def remove_stock_endpoint(ticker: str) -> tuple[Dict[str, bool], int]:
    """Remove a stock from monitoring (soft delete).

    Path Parameters:
        ticker (str): Stock ticker symbol to remove.

    Returns:
        JSON object with 'success' boolean.
    """
    success = remove_stock(ticker)
    return jsonify({'success': success})


@stocks_bp.route('/stocks/search', methods=['GET'])
def search_stocks() -> tuple[List[Dict[str, str]], int]:
    """Search for stock tickers via Yahoo Finance.

    Query Parameters:
        q (str): Search query string (company name or ticker fragment).

    Returns:
        JSON array of matching stocks with ticker, name, exchange, type fields.
        Returns empty array if query is empty.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    results = search_stock_ticker(query)
    return jsonify(results)
```