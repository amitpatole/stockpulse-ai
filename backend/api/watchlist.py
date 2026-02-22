"""
TickerPulse AI v3.0 - Watchlist API
Blueprint exposing watchlist read and stock-reorder endpoints.
"""

import logging

from flask import Blueprint, jsonify, request

from backend.core.watchlist_manager import get_watchlist, reorder_stocks

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')


@watchlist_bp.route('/<int:watchlist_id>', methods=['GET'])
def fetch_watchlist(watchlist_id: int):
    """Return a watchlist with its tickers in persisted position order.

    Returns:
        200: { "id": 1, "name": "My Watchlist", "tickers": ["TSLA", "AAPL", ...] }
        404: { "error": "watchlist not found" }
    """
    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': 'watchlist not found'}), 404
    return jsonify(wl)


@watchlist_bp.route('/<int:watchlist_id>/reorder', methods=['PATCH'])
def reorder_watchlist(watchlist_id: int):
    """Persist a new stock display order for a watchlist.

    Body:
        { "tickers": ["TSLA", "AAPL", "MSFT"] }

    Returns:
        200: { "ok": true }
        400: { "error": "tickers must be a non-empty list" }
        404: { "error": "watchlist not found" }
    """
    body = request.get_json(silent=True) or {}
    tickers = body.get('tickers')

    if not tickers or not isinstance(tickers, list) or not all(isinstance(t, str) for t in tickers):
        return jsonify({'error': 'tickers must be a non-empty list'}), 400

    success = reorder_stocks(watchlist_id, tickers)
    if not success:
        return jsonify({'error': 'watchlist not found'}), 404

    return jsonify({'ok': True})
