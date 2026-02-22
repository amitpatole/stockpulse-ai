"""
TickerPulse AI v3.0 - Watchlist API
Endpoints for watchlist management including drag-and-drop stock reordering.
"""

import logging

from flask import Blueprint, jsonify, request

from backend.core.watchlist_manager import reorder_stocks, get_watchlist

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint('watchlist', __name__)


@watchlist_bp.route('/api/watchlist/reorder', methods=['PATCH'])
def reorder():
    """Reorder stocks within a watchlist.

    Request body::

        { "watchlist_id": 1, "tickers": ["MSFT", "AAPL", "GOOGL"] }

    Responses:
        200  { "ok": true }
        400  { "error": "missing watchlist_id or tickers" }
        400  { "error": "Ticker list does not match watchlist contents exactly" }
        404  { "error": "watchlist not found" }
    """
    data = request.get_json(silent=True) or {}
    watchlist_id = data.get('watchlist_id')
    tickers = data.get('tickers')

    if (
        not isinstance(watchlist_id, int)
        or isinstance(watchlist_id, bool)
        or not isinstance(tickers, list)
        or len(tickers) == 0
    ):
        return jsonify({'error': 'missing watchlist_id or tickers'}), 400

    # Normalise tickers to uppercase strings; reject non-string entries
    normalised: list[str] = []
    for t in tickers:
        if not isinstance(t, str) or not t.strip():
            return jsonify({'error': 'missing watchlist_id or tickers'}), 400
        normalised.append(t.strip().upper())

    try:
        found = reorder_stocks(watchlist_id, normalised)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    if not found:
        return jsonify({'error': 'watchlist not found'}), 404

    return jsonify({'ok': True})
