"""
TickerPulse AI v3.0 - Stocks API Routes
Blueprint for stock management endpoints: list, add, remove, search, and group management.

Input Validation:
- All inputs validated using Pydantic models in backend.models.requests
- Validation errors return 400 with details on invalid fields
- Uses validate_json_request and validate_query_params decorators
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any, List

from backend.core.stock_manager import (
    add_stock, remove_stock, search_stock_ticker, get_stocks_with_filter,
    create_watchlist_group, get_watchlist_groups, get_watchlist_group_stocks,
    update_watchlist_group, delete_watchlist_group, move_stock_to_group,
    reorder_stocks_in_group
)
from backend.core.validation import get_request_body, get_query_params
from backend.core.errors import NotFoundError, ValidationError as TickerPulseValidationError
from backend.models.requests import (
    StockCreateRequest, PaginationParams, StockSearchRequest,
    WatchlistGroupCreateRequest, WatchlistGroupUpdateRequest,
    MoveStockToGroupRequest, ReorderStocksRequest
)
from backend.models.responses import (
    PaginatedResponse, StockResponse, PaginationMeta,
    WatchlistGroupResponse, WatchlistGroupDetailResponse
)

logger = logging.getLogger(__name__)

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api')


# ============================================================================
# Stocks Endpoints
# ============================================================================

@stocks_bp.route('/stocks', methods=['GET'])
def get_stocks() -> tuple[Dict[str, Any], int]:
    """Get paginated monitored stocks with database-level filtering.

    Query Parameters (validated by PaginationParams):
        limit (int, optional): Items per page. Range: 1-100, Default: 20
        offset (int, optional): Pagination offset. Default: 0

    Query Parameters (custom):
        market (str, optional): Filter by market (e.g. 'US', 'India'). Ignored if 'All'.
        group_id (int, optional): Filter by group ID.

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
    """
    params = get_query_params(PaginationParams)

    market = request.args.get('market')
    group_id_str = request.args.get('group_id')
    group_id = None
    if group_id_str:
        try:
            group_id = int(group_id_str)
        except ValueError:
            return jsonify({'error': 'Invalid group_id'}), 400

    stocks, total_count = get_stocks_with_filter(
        market=market, group_id=group_id, limit=params.limit, offset=params.offset
    )

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

    if not name:
        results = search_stock_ticker(ticker)
        match = next((r for r in results if r['ticker'].upper() == ticker), None)
        if match:
            name = match.get('name', ticker)
        elif results:
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


# ============================================================================
# Watchlist Groups Endpoints
# ============================================================================

@stocks_bp.route('/watchlist-groups', methods=['GET'])
def get_groups() -> tuple[Dict[str, Any], int]:
    """Get all watchlist groups with stock counts.

    Returns (200):
        {
            "data": [WatchlistGroupResponse, ...],
            "meta": {"total": int}
        }
    """
    groups = get_watchlist_groups()
    return jsonify({
        'data': [
            WatchlistGroupResponse(
                id=g['id'],
                name=g['name'],
                description=g['description'],
                color=g['color'],
                stock_count=g['stock_count'],
                created_at=g['created_at'],
                updated_at=g['updated_at'],
            ).model_dump() for g in groups
        ],
        'meta': {'total': len(groups)}
    })


@stocks_bp.route('/watchlist-groups', methods=['POST'])
def create_group() -> tuple[Dict[str, Any], int]:
    """Create a new watchlist group.

    Request Body (JSON):
        name (str): Group name (required, must be unique)
        description (str, optional): Group description
        color (str, optional): Hex color code (default: #6366f1)

    Returns (201):
        WatchlistGroupResponse with the created group details.

    Errors:
        400: Invalid input or duplicate group name
    """
    data = request.json or {}
    
    try:
        req = WatchlistGroupCreateRequest(**data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    group_id = create_watchlist_group(req.name, req.description, req.color or '#6366f1')

    if group_id is None:
        return jsonify({'error': 'Failed to create group (name may already exist)'}), 409

    return jsonify({
        'id': group_id,
        'name': req.name,
        'description': req.description,
        'color': req.color or '#6366f1',
        'stock_count': 0,
        'created_at': None,
        'updated_at': None,
    }), 201


@stocks_bp.route('/watchlist-groups/<int:group_id>', methods=['GET'])
def get_group_detail(group_id: int) -> tuple[Dict[str, Any], int]:
    """Get a specific watchlist group with its stocks.

    Path Parameters:
        group_id (int): Group ID

    Returns (200):
        WatchlistGroupDetailResponse with the group and ordered stock list.
    """
    groups = get_watchlist_groups()
    group = next((g for g in groups if g['id'] == group_id), None)

    if not group:
        return jsonify({'error': 'Group not found'}), 404

    stocks = get_watchlist_group_stocks(group_id)

    return jsonify(
        WatchlistGroupDetailResponse(
            id=group['id'],
            name=group['name'],
            description=group['description'],
            color=group['color'],
            stocks=stocks,
            created_at=group['created_at'],
            updated_at=group['updated_at'],
        ).model_dump()
    )


@stocks_bp.route('/watchlist-groups/<int:group_id>', methods=['PUT'])
def update_group(group_id: int) -> tuple[Dict[str, Any], int]:
    """Update a watchlist group.

    Path Parameters:
        group_id (int): Group ID

    Request Body (JSON):
        name (str, optional): New group name
        description (str, optional): New description
        color (str, optional): New hex color code

    Returns (200):
        Updated WatchlistGroupResponse
    """
    data = request.json or {}

    try:
        req = WatchlistGroupUpdateRequest(**data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    success = update_watchlist_group(
        group_id, req.name, req.description, req.color
    )

    if not success:
        return jsonify({'error': 'Failed to update group'}), 400

    groups = get_watchlist_groups()
    group = next((g for g in groups if g['id'] == group_id), None)

    if not group:
        return jsonify({'error': 'Group not found'}), 404

    return jsonify(
        WatchlistGroupResponse(
            id=group['id'],
            name=group['name'],
            description=group['description'],
            color=group['color'],
            stock_count=group['stock_count'],
            created_at=group['created_at'],
            updated_at=group['updated_at'],
        ).model_dump()
    )


@stocks_bp.route('/watchlist-groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id: int) -> tuple[Dict[str, bool], int]:
    """Delete a watchlist group (stocks revert to ungrouped).

    Path Parameters:
        group_id (int): Group ID

    Returns (200):
        {"success": true}
    """
    success = delete_watchlist_group(group_id)
    return jsonify({'success': success})


@stocks_bp.route('/watchlist-groups/<int:group_id>/stocks', methods=['PUT'])
def reorder_group_stocks(group_id: int) -> tuple[Dict[str, Any], int]:
    """Reorder stocks in a group via drag-and-drop.

    Path Parameters:
        group_id (int): Group ID

    Request Body (JSON):
        ticker_order (List[str]): List of tickers in desired order

    Returns (200):
        {"success": true, "stocks": [ordered tickers]}
    """
    data = request.json or {}

    try:
        req = ReorderStocksRequest(**data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    success = reorder_stocks_in_group(group_id, req.ticker_order)

    if not success:
        return jsonify({'error': 'Failed to reorder stocks'}), 400

    return jsonify({
        'success': True,
        'stocks': req.ticker_order,
    })


# ============================================================================
# Stock-Group Assignment
# ============================================================================

@stocks_bp.route('/stocks/<ticker>/group', methods=['POST'])
def assign_stock_to_group(ticker: str) -> tuple[Dict[str, Any], int]:
    """Move a stock to a group or remove from group.

    Path Parameters:
        ticker (str): Stock ticker

    Request Body (JSON):
        group_id (int, optional): Group ID. If null, removes stock from group.

    Returns (200):
        {"success": true, "ticker": "AAPL", "group_id": 1}
    """
    data = request.json or {}

    try:
        req = MoveStockToGroupRequest(**data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    success = move_stock_to_group(ticker, req.group_id)

    if not success:
        return jsonify({'error': 'Failed to move stock to group'}), 400

    return jsonify({
        'success': True,
        'ticker': ticker.upper(),
        'group_id': req.group_id,
    })