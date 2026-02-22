"""
TickerPulse AI v3.0 - Watchlist API Routes
Blueprint for watchlist CRUD and CSV bulk-import endpoints.
"""

import csv
import io
import logging
import sqlite3

from flask import Blueprint, jsonify, request

from backend.core.watchlist_manager import (
    get_all_watchlists,
    create_watchlist,
    get_watchlist,
    rename_watchlist,
    delete_watchlist,
    add_stock_to_watchlist,
    remove_stock_from_watchlist,
)
from backend.database import db_session

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')

_MAX_IMPORT_BYTES = 1_048_576   # 1 MB
_MAX_IMPORT_ROWS  = 500


# ---------------------------------------------------------------------------
# Watchlist CRUD
# ---------------------------------------------------------------------------

@watchlist_bp.route('', methods=['GET'])
def list_watchlists():
    """Return all watchlists with stock counts."""
    return jsonify(get_all_watchlists())


@watchlist_bp.route('', methods=['POST'])
def create_watchlist_endpoint():
    """Create a new watchlist.

    Request Body (JSON):
        name (str): Watchlist name.
    """
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400
    try:
        wl = create_watchlist(name)
        return jsonify(wl), 201
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409


@watchlist_bp.route('/<int:watchlist_id>', methods=['GET'])
def get_watchlist_endpoint(watchlist_id: int):
    """Return a single watchlist with its tickers."""
    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': 'Watchlist not found'}), 404
    return jsonify(wl)


@watchlist_bp.route('/<int:watchlist_id>', methods=['PATCH'])
def rename_watchlist_endpoint(watchlist_id: int):
    """Rename a watchlist.

    Request Body (JSON):
        name (str): New watchlist name.
    """
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400
    try:
        wl = rename_watchlist(watchlist_id, name)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    if wl is None:
        return jsonify({'error': 'Watchlist not found'}), 404
    return jsonify(wl)


@watchlist_bp.route('/<int:watchlist_id>', methods=['DELETE'])
def delete_watchlist_endpoint(watchlist_id: int):
    """Delete a watchlist (cannot delete the last one)."""
    try:
        deleted = delete_watchlist(watchlist_id)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    if not deleted:
        return jsonify({'error': 'Watchlist not found'}), 404
    return jsonify({'success': True})


@watchlist_bp.route('/<int:watchlist_id>/stocks', methods=['POST'])
def add_stock_endpoint(watchlist_id: int):
    """Add a single stock to a watchlist.

    Request Body (JSON):
        ticker (str): Stock ticker symbol.
    """
    data = request.get_json(silent=True) or {}
    ticker = (data.get('ticker') or '').strip().upper()
    if not ticker:
        return jsonify({'error': 'ticker is required'}), 400
    ok = add_stock_to_watchlist(watchlist_id, ticker)
    if not ok:
        return jsonify({'error': 'Watchlist not found'}), 404
    return jsonify({'success': True, 'ticker': ticker})


@watchlist_bp.route('/<int:watchlist_id>/stocks/<ticker>', methods=['DELETE'])
def remove_stock_endpoint(watchlist_id: int, ticker: str):
    """Remove a stock from a watchlist."""
    removed = remove_stock_from_watchlist(watchlist_id, ticker.upper())
    if not removed:
        return jsonify({'error': 'Stock not found in watchlist'}), 404
    return jsonify({'success': True})


# ---------------------------------------------------------------------------
# CSV bulk import
# ---------------------------------------------------------------------------

@watchlist_bp.route('/<int:watchlist_id>/import', methods=['POST'])
def import_csv(watchlist_id: int):
    """Bulk-import tickers from a CSV file into a watchlist.

    Request: multipart/form-data with field ``file`` (.csv, max 1 MB, max 500 rows).

    The CSV must contain a ``symbol`` column (case-insensitive).
    Each symbol is uppercased and validated against the ``stocks`` table.
    Symbols not present in ``stocks`` are skipped and reported in
    ``invalid_symbols``.  Duplicate entries are silently skipped.

    Returns:
        200 JSON:
            added            (int)   – tickers successfully inserted
            skipped_duplicates (int) – already present in the watchlist
            skipped_invalid  (int)   – not found in stocks table
            invalid_symbols  (list)  – list of unrecognised symbols
        400 – bad file type / missing symbol column / empty file
        404 – watchlist not found
        413 – file too large
    """
    # -- Watchlist existence check ------------------------------------------
    wl = get_watchlist(watchlist_id)
    if wl is None:
        return jsonify({'error': 'Watchlist not found'}), 404

    # -- File presence & extension check -------------------------------------
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded; expected multipart field "file"'}), 400

    file = request.files['file']
    filename = (file.filename or '').lower()
    if not filename.endswith('.csv'):
        return jsonify({'error': 'Unsupported file type; only .csv files are accepted'}), 400

    # -- Size check ----------------------------------------------------------
    raw = file.read()
    if len(raw) > _MAX_IMPORT_BYTES:
        return jsonify({'error': 'File too large; maximum is 1 MB'}), 413

    if not raw:
        return jsonify({'error': 'Uploaded file is empty'}), 400

    # -- Parse CSV -----------------------------------------------------------
    try:
        # Strip UTF-8 BOM if present and decode
        text = raw.lstrip(b'\xef\xbb\xbf').decode('utf-8-sig', errors='replace')
        reader = csv.DictReader(io.StringIO(text))
    except Exception as exc:
        logger.warning("CSV parse error: %s", exc)
        return jsonify({'error': 'Could not parse CSV file'}), 400

    # Find the 'symbol' header case-insensitively
    if reader.fieldnames is None:
        return jsonify({'error': 'CSV file has no header row'}), 400

    symbol_col = next(
        (h for h in reader.fieldnames if h.strip().lower() == 'symbol'),
        None,
    )
    if symbol_col is None:
        return jsonify({'error': 'CSV must contain a "symbol" column'}), 400

    # Collect candidate symbols (max _MAX_IMPORT_ROWS)
    raw_symbols: list[str] = []
    for i, row in enumerate(reader):
        if i >= _MAX_IMPORT_ROWS:
            break
        val = (row.get(symbol_col) or '').strip().upper()
        if val:
            raw_symbols.append(val)

    if not raw_symbols:
        return jsonify({'error': 'No symbols found in the CSV file'}), 400

    # -- Validate symbols against stocks table --------------------------------
    with db_session() as conn:
        placeholders = ','.join('?' for _ in raw_symbols)
        valid_rows = conn.execute(
            f"SELECT ticker FROM stocks WHERE ticker IN ({placeholders})",
            raw_symbols,
        ).fetchall()
    valid_tickers = {r['ticker'] for r in valid_rows}

    invalid_symbols = [s for s in raw_symbols if s not in valid_tickers]
    skipped_invalid = len(invalid_symbols)

    # -- Insert valid tickers in a single session ----------------------------
    added = 0
    skipped_duplicates = 0

    with db_session() as conn:
        for ticker in raw_symbols:
            if ticker not in valid_tickers:
                continue
            try:
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO watchlist_stocks (watchlist_id, ticker)"
                    " VALUES (?, ?)",
                    (watchlist_id, ticker),
                )
                if cursor.rowcount == 1:
                    added += 1
                else:
                    skipped_duplicates += 1
            except sqlite3.IntegrityError:
                skipped_duplicates += 1

    return jsonify({
        'added': added,
        'skipped_duplicates': skipped_duplicates,
        'skipped_invalid': skipped_invalid,
        'invalid_symbols': invalid_symbols,
    })
