"""
TickerPulse AI v3.0 - Watchlist API Routes
Blueprint for watchlist management endpoints: CRUD and CSV import.
"""

import csv
import io
import logging

from flask import Blueprint, jsonify, request

from backend.core.watchlist_manager import (
    get_all_watchlists,
    get_watchlist,
    create_watchlist,
    rename_watchlist,
    delete_watchlist,
    add_stock_to_watchlist,
)
from backend.database import get_db_connection

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')

_MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB
_MAX_ROWS = 500


@watchlist_bp.route('', methods=['GET'])
def list_watchlists():
    """Return all watchlists with stock counts."""
    return jsonify(get_all_watchlists())


@watchlist_bp.route('', methods=['POST'])
def create_watchlist_endpoint():
    """Create a new watchlist."""
    data = request.json or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Missing required field: name'}), 400
    try:
        wl = create_watchlist(name)
        return jsonify(wl), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409


@watchlist_bp.route('/<int:watchlist_id>', methods=['GET'])
def get_watchlist_endpoint(watchlist_id: int):
    """Return a single watchlist with its tickers."""
    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': 'Watchlist not found'}), 404
    return jsonify(wl)


@watchlist_bp.route('/<int:watchlist_id>', methods=['PUT'])
def rename_watchlist_endpoint(watchlist_id: int):
    """Rename a watchlist."""
    data = request.json or {}
    new_name = data.get('name', '').strip()
    if not new_name:
        return jsonify({'error': 'Missing required field: name'}), 400
    try:
        wl = rename_watchlist(watchlist_id, new_name)
        if wl is None:
            return jsonify({'error': 'Watchlist not found'}), 404
        return jsonify(wl)
    except ValueError as e:
        return jsonify({'error': str(e)}), 409


@watchlist_bp.route('/<int:watchlist_id>', methods=['DELETE'])
def delete_watchlist_endpoint(watchlist_id: int):
    """Delete a watchlist."""
    try:
        found = delete_watchlist(watchlist_id)
        if not found:
            return jsonify({'error': 'Watchlist not found'}), 404
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@watchlist_bp.route('/<int:watchlist_id>/import', methods=['POST'])
def import_watchlist_csv(watchlist_id: int):
    """Import tickers from a CSV file into a watchlist.

    Request: multipart/form-data with field 'file' (.csv, max 1MB, max 500 rows)

    The CSV must contain a column named 'symbol' (case-insensitive).
    Tickers are normalised to uppercase. Only tickers already present in
    the stocks table are accepted; unknown symbols are reported as invalid.
    Duplicates (already in the watchlist) are reported separately.

    Returns:
        200: { added, skipped_duplicates, skipped_invalid, invalid_symbols }
        400: bad file type, empty file, missing symbol column
        404: watchlist not found
        413: file exceeds 1 MB
    """
    # Verify the watchlist exists first
    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': 'Watchlist not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    filename = file.filename or ''
    if not filename.lower().endswith('.csv'):
        return jsonify({'error': 'Unsupported file type. Please upload a .csv file'}), 400

    content = file.read()

    if len(content) > _MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 1 MB'}), 413

    if not content:
        return jsonify({'error': 'File is empty'}), 400

    # Decode — utf-8-sig strips the BOM if present
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            text = content.decode('latin-1')
        except Exception:
            return jsonify({'error': 'Could not decode file. Please use UTF-8 encoding'}), 400

    reader = csv.DictReader(io.StringIO(text))

    fieldnames = reader.fieldnames
    if not fieldnames:
        return jsonify({'error': 'CSV file has no headers'}), 400

    # Case-insensitive search for 'symbol' column
    symbol_col = next(
        (f for f in fieldnames if f.strip().lower() == 'symbol'),
        None,
    )
    if symbol_col is None:
        return jsonify({'error': 'CSV must contain a "symbol" column'}), 400

    added = 0
    skipped_duplicates = 0
    skipped_invalid = 0
    invalid_symbols: list[str] = []

    # Snapshot of tickers already in the watchlist; updated as we add
    existing_tickers: set[str] = set(wl.get('tickers', []))

    row_count = 0
    for row in reader:
        if row_count >= _MAX_ROWS:
            break
        row_count += 1

        raw = row.get(symbol_col, '') or ''
        ticker = raw.strip().upper()
        if not ticker:
            continue

        # Skip duplicates already in the watchlist
        if ticker in existing_tickers:
            skipped_duplicates += 1
            continue

        # Validate that the ticker exists in the stocks table
        conn = get_db_connection()
        try:
            stock_row = conn.execute(
                'SELECT ticker FROM stocks WHERE ticker = ?', (ticker,)
            ).fetchone()
        finally:
            conn.close()

        if stock_row is None:
            skipped_invalid += 1
            invalid_symbols.append(ticker)
            continue

        # Insert into watchlist (add_stock_to_watchlist also invalidates AI cache)
        success = add_stock_to_watchlist(watchlist_id, ticker)
        if success:
            added += 1
            existing_tickers.add(ticker)
        else:
            skipped_duplicates += 1

    return jsonify({
        'added': added,
        'skipped_duplicates': skipped_duplicates,
        'skipped_invalid': skipped_invalid,
        'invalid_symbols': invalid_symbols,
    })
