"""
TickerPulse AI v3.0 - Watchlist API
Blueprint exposing watchlist management endpoints, including CSV import
and drag-and-drop reorder support.
"""

import csv
import io
import logging

from flask import Blueprint, jsonify, request

from backend.core.watchlist_manager import (
    add_stock_to_watchlist,
    get_watchlist,
    reorder_watchlist,
)
from backend.database import db_session

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')

_MAX_FILE_BYTES = 1 * 1024 * 1024  # 1 MB
_MAX_ROWS = 500


@watchlist_bp.route('/<int:watchlist_id>', methods=['GET'])
def get_watchlist_route(watchlist_id: int):
    """Return a watchlist with its ordered ticker list.

    Returns:
        200  {id, name, created_at, tickers}
        404  Watchlist not found
    """
    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': f'Watchlist {watchlist_id} not found'}), 404
    return jsonify(wl), 200


@watchlist_bp.route('/<int:watchlist_id>/reorder', methods=['PUT'])
def reorder_stocks(watchlist_id: int):
    """Persist a new drag-and-drop sort order for stocks in a watchlist.

    Request body: {"tickers": ["AAPL", "MSFT", ...]}
    Each ticker is assigned sort_order equal to its index in the list.

    Returns:
        200  {"ok": true}
        400  Missing or invalid tickers field
        404  Watchlist not found
    """
    body = request.get_json(silent=True) or {}
    tickers = body.get('tickers')
    if not isinstance(tickers, list):
        return jsonify({'error': 'tickers must be a list'}), 400
    if not all(isinstance(t, str) for t in tickers):
        return jsonify({'error': 'All tickers must be strings'}), 400
    if len(tickers) > 500:
        return jsonify({'error': 'Too many tickers'}), 400

    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': f'Watchlist {watchlist_id} not found'}), 404

    if not reorder_watchlist(watchlist_id, tickers):
        return jsonify({'error': 'Failed to reorder watchlist'}), 500

    return jsonify({'ok': True}), 200


@watchlist_bp.route('/<int:watchlist_id>/import', methods=['POST'])
def import_csv(watchlist_id: int):
    """Import tickers from a CSV file into a watchlist.

    Request: multipart/form-data with field ``file`` (.csv, ≤ 1 MB).
    The CSV must contain a column whose header is ``symbol`` (case-insensitive).
    Each value is stripped of whitespace and uppercased before lookup.

    Returns:
        200  {added, skipped_duplicates, skipped_invalid, invalid_symbols}
        400  Bad file type / empty file / no symbol column / too many rows
        404  Watchlist not found
        413  File too large
    """
    # Verify watchlist exists
    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': f'Watchlist {watchlist_id} not found'}), 404

    # Validate file presence
    if 'file' not in request.files:
        return jsonify({'error': 'No file field in request'}), 400

    upload = request.files['file']
    filename = upload.filename or ''

    if not filename.lower().endswith('.csv'):
        return jsonify({'error': 'Unsupported file type. Please upload a .csv file'}), 400

    raw = upload.read()
    if not raw:
        return jsonify({'error': 'Uploaded file is empty'}), 400

    if len(raw) > _MAX_FILE_BYTES:
        return jsonify({'error': 'File too large. Maximum size is 1 MB'}), 413

    # Decode — handle BOM gracefully
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('latin-1')

    reader = csv.DictReader(io.StringIO(text))

    # Find the symbol column (case-insensitive)
    if reader.fieldnames is None:
        return jsonify({'error': 'CSV file has no headers'}), 400

    symbol_col = next(
        (f for f in reader.fieldnames if f.strip().lower() == 'symbol'),
        None,
    )
    if symbol_col is None:
        return jsonify({'error': "CSV must contain a 'symbol' column"}), 400

    # Collect tickers, enforcing row limit
    tickers: list[str] = []
    for i, row in enumerate(reader):
        if i >= _MAX_ROWS:
            return jsonify({'error': f'CSV exceeds maximum of {_MAX_ROWS} rows'}), 400
        val = (row.get(symbol_col) or '').strip().upper()
        if val:
            tickers.append(val)

    if not tickers:
        return jsonify({'error': 'No ticker symbols found in CSV'}), 400

    # Look up which symbols exist in the stocks table
    with db_session() as conn:
        rows = conn.execute('SELECT ticker FROM stocks').fetchall()
    known_tickers = {r['ticker'].upper() for r in rows}

    added = 0
    skipped_duplicates = 0
    skipped_invalid = 0
    invalid_symbols: list[str] = []

    # Fetch tickers already in this watchlist to detect duplicates cheaply
    already_in_watchlist = set(wl.get('tickers', []))

    for ticker in tickers:
        if ticker not in known_tickers:
            skipped_invalid += 1
            invalid_symbols.append(ticker)
            continue

        if ticker in already_in_watchlist:
            skipped_duplicates += 1
            continue

        success = add_stock_to_watchlist(watchlist_id, ticker)
        if success:
            added += 1
            already_in_watchlist.add(ticker)
        else:
            # watchlist disappeared mid-import (extremely unlikely)
            skipped_invalid += 1
            invalid_symbols.append(ticker)

    return jsonify({
        'added': added,
        'skipped_duplicates': skipped_duplicates,
        'skipped_invalid': skipped_invalid,
        'invalid_symbols': invalid_symbols,
    }), 200
