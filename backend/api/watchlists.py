"""
TickerPulse AI v3.0 - Watchlist API Routes
Blueprint for watchlist (portfolio group) CRUD: list, create, rename, delete,
and stock membership management.
"""

import logging

from flask import Blueprint, jsonify, request

from backend.database import db_session

logger = logging.getLogger(__name__)

watchlists_bp = Blueprint('watchlists', __name__, url_prefix='/api')

MAX_WATCHLISTS = 20


# ---------------------------------------------------------------------------
# Watchlist collection endpoints
# ---------------------------------------------------------------------------

@watchlists_bp.route('/watchlists', methods=['GET'])
def get_watchlists():
    """List all watchlists with their stock counts.

    Returns:
        JSON array of watchlist objects: id, name, stock_count, created_at.
    """
    with db_session() as conn:
        rows = conn.execute(
            '''
            SELECT w.id, w.name, w.created_at, COUNT(ws.ticker) AS stock_count
            FROM watchlists w
            LEFT JOIN watchlist_stocks ws ON ws.watchlist_id = w.id
            GROUP BY w.id
            ORDER BY w.created_at ASC
            '''
        ).fetchall()
        return jsonify([dict(row) for row in rows])


@watchlists_bp.route('/watchlists', methods=['POST'])
def create_watchlist():
    """Create a new named watchlist.

    Request Body (JSON):
        name (str): Unique watchlist name (required).

    Returns:
        JSON with the new watchlist id, name, and stock_count=0.
        400 if name is missing.
        409 if name already exists.
        400 if the 20-watchlist limit has been reached.
    """
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400

    with db_session() as conn:
        count = conn.execute('SELECT COUNT(*) FROM watchlists').fetchone()[0]
        if count >= MAX_WATCHLISTS:
            return jsonify({'error': f'Maximum {MAX_WATCHLISTS} watchlists allowed'}), 400

        existing = conn.execute(
            'SELECT id FROM watchlists WHERE name = ?', (name,)
        ).fetchone()
        if existing:
            return jsonify({'error': f"A watchlist named '{name}' already exists"}), 409

        cursor = conn.execute('INSERT INTO watchlists (name) VALUES (?)', (name,))
        new_id = cursor.lastrowid
        logger.info("Created watchlist id=%d name=%r", new_id, name)
        return jsonify({'id': new_id, 'name': name, 'stock_count': 0}), 201


# ---------------------------------------------------------------------------
# Single watchlist endpoints
# ---------------------------------------------------------------------------

@watchlists_bp.route('/watchlists/<int:wid>', methods=['GET'])
def get_watchlist(wid):
    """Return a single watchlist with its ticker list.

    Path Parameters:
        wid (int): Watchlist ID.

    Returns:
        JSON with id, name, created_at, tickers (array of ticker strings).
        404 if not found.
    """
    with db_session() as conn:
        wl = conn.execute(
            'SELECT id, name, created_at FROM watchlists WHERE id = ?', (wid,)
        ).fetchone()
        if not wl:
            return jsonify({'error': 'Watchlist not found'}), 404

        ticker_rows = conn.execute(
            'SELECT ticker FROM watchlist_stocks WHERE watchlist_id = ? ORDER BY added_at ASC',
            (wid,),
        ).fetchall()

        return jsonify({
            'id': wl['id'],
            'name': wl['name'],
            'created_at': wl['created_at'],
            'tickers': [row['ticker'] for row in ticker_rows],
        })


@watchlists_bp.route('/watchlists/<int:wid>', methods=['PUT'])
def update_watchlist(wid):
    """Rename a watchlist.

    Path Parameters:
        wid (int): Watchlist ID.

    Request Body (JSON):
        name (str): New unique name (required).

    Returns:
        JSON with updated id and name.
        400 if name is missing, 404 if not found, 409 if name conflicts.
    """
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400

    with db_session() as conn:
        wl = conn.execute(
            'SELECT id FROM watchlists WHERE id = ?', (wid,)
        ).fetchone()
        if not wl:
            return jsonify({'error': 'Watchlist not found'}), 404

        conflict = conn.execute(
            'SELECT id FROM watchlists WHERE name = ? AND id != ?', (name, wid)
        ).fetchone()
        if conflict:
            return jsonify({'error': f"A watchlist named '{name}' already exists"}), 409

        conn.execute('UPDATE watchlists SET name = ? WHERE id = ?', (name, wid))
        logger.info("Renamed watchlist id=%d to %r", wid, name)
        return jsonify({'id': wid, 'name': name})


@watchlists_bp.route('/watchlists/<int:wid>', methods=['DELETE'])
def delete_watchlist(wid):
    """Delete a watchlist (stocks remain in the global registry).

    Path Parameters:
        wid (int): Watchlist ID.

    Returns:
        JSON {'success': True} on success.
        404 if not found, 400 if it is the last watchlist.
    """
    with db_session() as conn:
        wl = conn.execute(
            'SELECT id FROM watchlists WHERE id = ?', (wid,)
        ).fetchone()
        if not wl:
            return jsonify({'error': 'Watchlist not found'}), 404

        total = conn.execute('SELECT COUNT(*) FROM watchlists').fetchone()[0]
        if total <= 1:
            return jsonify({'error': 'Cannot delete the last watchlist'}), 400

        conn.execute('DELETE FROM watchlists WHERE id = ?', (wid,))
        logger.info("Deleted watchlist id=%d", wid)
        return jsonify({'success': True})


# ---------------------------------------------------------------------------
# Watchlist stock membership endpoints
# ---------------------------------------------------------------------------

@watchlists_bp.route('/watchlists/<int:wid>/stocks', methods=['POST'])
def add_stock_to_watchlist(wid):
    """Add a ticker to a watchlist.

    The ticker must already exist as an active stock in the global registry.

    Path Parameters:
        wid (int): Watchlist ID.

    Request Body (JSON):
        ticker (str): Stock ticker symbol (required).

    Returns:
        JSON {'success': True, 'watchlist_id': wid, 'ticker': ticker} with 201.
        400 if ticker missing, 404 if watchlist or ticker not found.
        Duplicate insertions are silently ignored (idempotent).
    """
    data = request.json or {}
    ticker = (data.get('ticker') or '').strip().upper()
    if not ticker:
        return jsonify({'error': 'ticker is required'}), 400

    with db_session() as conn:
        wl = conn.execute(
            'SELECT id FROM watchlists WHERE id = ?', (wid,)
        ).fetchone()
        if not wl:
            return jsonify({'error': 'Watchlist not found'}), 404

        stock = conn.execute(
            'SELECT ticker FROM stocks WHERE ticker = ? AND active = 1', (ticker,)
        ).fetchone()
        if not stock:
            return jsonify({'error': f"Ticker '{ticker}' not found in stock registry"}), 404

        conn.execute(
            'INSERT OR IGNORE INTO watchlist_stocks (watchlist_id, ticker) VALUES (?, ?)',
            (wid, ticker),
        )
        return jsonify({'success': True, 'watchlist_id': wid, 'ticker': ticker}), 201


@watchlists_bp.route('/watchlists/<int:wid>/stocks/<ticker>', methods=['DELETE'])
def remove_stock_from_watchlist(wid, ticker):
    """Remove a ticker from a watchlist (stock stays in the global registry).

    Path Parameters:
        wid (int): Watchlist ID.
        ticker (str): Stock ticker symbol.

    Returns:
        JSON {'success': True} on success.
        404 if watchlist not found.
    """
    ticker = ticker.upper()
    with db_session() as conn:
        wl = conn.execute(
            'SELECT id FROM watchlists WHERE id = ?', (wid,)
        ).fetchone()
        if not wl:
            return jsonify({'error': 'Watchlist not found'}), 404

        conn.execute(
            'DELETE FROM watchlist_stocks WHERE watchlist_id = ? AND ticker = ?',
            (wid, ticker),
        )
        return jsonify({'success': True})
