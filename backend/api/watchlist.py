```python
"""
TickerPulse AI v3.0 - Watchlist API
Blueprint exposing watchlist group management endpoints, including CSV import
and drag-and-drop reorder support.
"""

import csv
import io
import logging

from flask import Blueprint, jsonify, request

from backend.core.watchlist_manager import (
    add_stock_to_watchlist,
    create_watchlist,
    delete_watchlist,
    get_all_watchlists,
    get_watchlist,
    remove_stock_from_watchlist,
    rename_watchlist,
    reorder_watchlist,
    reorder_watchlist_groups,
)
from backend.database import db_session
from backend.core.error_handlers import handle_api_errors, ValidationError, NotFoundError

logger = logging.getLogger(__name__)

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/api/watchlist')

_MAX_FILE_BYTES = 1 * 1024 * 1024  # 1 MB
_MAX_ROWS = 500
_MAX_NAME_LEN = 100


# ---------------------------------------------------------------------------
# Group CRUD
# ---------------------------------------------------------------------------

@watchlist_bp.route('/', methods=['GET'])
@handle_api_errors
def list_watchlists():
    """Return all watchlist groups ordered by sort_order with their stock counts.
    ---
    tags:
      - Watchlist
    summary: List all watchlist groups
    responses:
      200:
        description: All watchlist groups ordered by sort_order.
        schema:
          type: array
          items:
            $ref: '#/definitions/WatchlistGroup'
    """
    groups = get_all_watchlists()
    return jsonify(groups), 200


@watchlist_bp.route('/', methods=['POST'])
@handle_api_errors
def create_watchlist_route():
    """Create a new named watchlist group.
    ---
    tags:
      - Watchlist
    summary: Create a watchlist group
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: Tech Stocks
    responses:
      201:
        description: Watchlist group created.
        schema:
          $ref: '#/definitions/WatchlistGroup'
      400:
        description: Missing or empty name, name too long, or duplicate name.
        schema:
          $ref: '#/definitions/Error'
    """
    body = request.get_json(silent=True) or {}
    name: str = (body.get('name') or '').strip()
    if not name:
        raise ValidationError('name is required')
    if len(name) > _MAX_NAME_LEN:
        raise ValidationError(f'name must be {_MAX_NAME_LEN} characters or fewer')
    try:
        group = create_watchlist(name)
    except ValueError as exc:
        raise ValidationError(str(exc))
    return jsonify(group), 201


@watchlist_bp.route('/<int:watchlist_id>', methods=['GET'])
@handle_api_errors
def get_watchlist_route(watchlist_id: int):
    """Return a watchlist with its ordered ticker list.
    ---
    tags:
      - Watchlist
    summary: Get a watchlist with its tickers
    parameters:
      - name: watchlist_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Watchlist with ordered ticker list.
        schema:
          $ref: '#/definitions/WatchlistDetail'
      404:
        description: Watchlist not found.
        schema:
          $ref: '#/definitions/Error'
    """
    wl = get_watchlist(watchlist_id)
    if wl is None:
        raise NotFoundError(f'Watchlist {watchlist_id} not found')
    return jsonify(wl), 200


@watchlist_bp.route('/<int:watchlist_id>', methods=['PUT'])
@handle_api_errors
def rename_watchlist_route(watchlist_id: int):
    """Rename a watchlist group.
    ---
    tags:
      - Watchlist
    summary: Rename a watchlist group
    consumes:
      - application/json
    parameters:
      - name: watchlist_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
    responses:
      200:
        description: Watchlist renamed.
        schema:
          $ref: '#/definitions/WatchlistGroup'
      400:
        description: Missing or empty name, name too long, or duplicate name.
      404:
        description: Watchlist not found.
    """
    body = request.get_json(silent=True) or {}
    name: str = (body.get('name') or '').strip()
    if not name:
        raise ValidationError('name is required')
    if len(name) > _MAX_NAME_LEN:
        raise ValidationError(f'name must be {_MAX_NAME_LEN} characters or fewer')
    try:
        updated = rename_watchlist(watchlist_id, name)
    except ValueError as exc:
        raise ValidationError(str(exc))
    if updated is None:
        raise NotFoundError(f'Watchlist {watchlist_id} not found')
    return jsonify(updated), 200


@watchlist_bp.route('/<int:watchlist_id>', methods=['DELETE'])
@handle_api_errors
def delete_watchlist_route(watchlist_id: int):
    """Delete a watchlist group and all its stock associations.
    ---
    tags:
      - Watchlist
    summary: Delete a watchlist group
    description: >
      Deletes the watchlist and all stock membership records for it.
      The last remaining watchlist cannot be deleted.
    parameters:
      - name: watchlist_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Watchlist deleted.
      400:
        description: Cannot delete the last watchlist.
      404:
        description: Watchlist not found.
    """
    try:
        deleted = delete_watchlist(watchlist_id)
    except ValueError as exc:
        raise ValidationError(str(exc))
    if not deleted:
        raise NotFoundError(f'Watchlist {watchlist_id} not found')
    return jsonify({'ok': True}), 200


# ---------------------------------------------------------------------------
# Group-level reorder
# ---------------------------------------------------------------------------

@watchlist_bp.route('/reorder', methods=['PUT'])
@handle_api_errors
def reorder_groups():
    """Persist a new drag-and-drop sort order for watchlist groups.
    ---
    tags:
      - Watchlist
    summary: Reorder watchlist groups
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - ids
          properties:
            ids:
              type: array
              items:
                type: integer
    responses:
      200:
        description: Groups reordered successfully.
      400:
        description: Missing or invalid ids field.
    """
    body = request.get_json(silent=True) or {}
    ids = body.get('ids')
    if not isinstance(ids, list):
        raise ValidationError('ids must be a list')
    if not all(isinstance(i, int) for i in ids):
        raise ValidationError('All ids must be integers')
    if len(ids) > 100:
        raise ValidationError('Too many group ids')

    if not reorder_watchlist_groups(ids):
        raise ValidationError('No watchlists found to reorder')

    return jsonify({'ok': True}), 200


# ---------------------------------------------------------------------------
# Stock membership within a group
# ---------------------------------------------------------------------------

@watchlist_bp.route('/<int:watchlist_id>/stocks', methods=['POST'])
@handle_api_errors
def add_stock_to_group(watchlist_id: int):
    """Add a ticker to a specific watchlist group.
    ---
    tags:
      - Watchlist
    summary: Add a ticker to a watchlist
    consumes:
      - application/json
    parameters:
      - name: watchlist_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - ticker
          properties:
            ticker:
              type: string
    responses:
      200:
        description: Ticker added to watchlist.
      400:
        description: Missing ticker field.
      404:
        description: Watchlist not found or ticker unresolvable.
    """
    body = request.get_json(silent=True) or {}
    ticker: str = (body.get('ticker') or '').strip().upper()
    if not ticker:
        raise ValidationError('ticker is required')

    wl = get_watchlist(watchlist_id)
    if wl is None:
        raise NotFoundError(f'Watchlist {watchlist_id} not found')

    name: str | None = (body.get('name') or '').strip() or None
    success = add_stock_to_watchlist(watchlist_id, ticker, name)
    if not success:
        raise NotFoundError(f'Failed to add {ticker} to watchlist')
    return jsonify({'ok': True, 'ticker': ticker}), 200


@watchlist_bp.route('/<int:watchlist_id>/stocks/<string:ticker>', methods=['DELETE'])
@handle_api_errors
def remove_stock_from_group(watchlist_id: int, ticker: str):
    """Remove a ticker from a specific watchlist group.
    ---
    tags:
      - Watchlist
    summary: Remove a ticker from a watchlist
    description: >
      Removes the stock membership record only. The stock record in the
      stocks table is not deleted.
    parameters:
      - name: watchlist_id
        in: path
        type: integer
        required: true
      - name: ticker
        in: path
        type: string
        required: true
    responses:
      200:
        description: Ticker removed from watchlist.
      404:
        description: Watchlist or stock membership not found.
    """
    ticker = ticker.strip().upper()
    wl = get_watchlist(watchlist_id)
    if wl is None:
        raise NotFoundError(f'Watchlist {watchlist_id} not found')

    removed = remove_stock_from_watchlist(watchlist_id, ticker)
    if not removed:
        raise NotFoundError(f'{ticker} is not in watchlist {watchlist_id}')
    return jsonify({'ok': True}), 200


# ---------------------------------------------------------------------------
# Reorder stocks within a group
# ---------------------------------------------------------------------------

@watchlist_bp.route('/<int:watchlist_id>/reorder', methods=['PUT'])
@handle_api_errors
def reorder_stocks(watchlist_id: int):
    """Persist a new drag-and-drop sort order for stocks in a watchlist.
    ---
    tags:
      - Watchlist
    summary: Reorder stocks within a watchlist
    consumes:
      - application/json
    parameters:
      - name: watchlist_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - tickers
          properties:
            tickers:
              type: array
              items:
                type: string
    responses:
      200:
        description: Stocks reordered successfully.
      400:
        description: Missing or invalid tickers field.
      404:
        description: Watchlist not found.
    """
    body = request.get_json(silent=True) or {}
    tickers = body.get('tickers')
    if not isinstance(tickers, list):
        raise ValidationError('tickers must be a list')
    if not all(isinstance(t, str) for t in tickers):
        raise ValidationError('All tickers must be strings')
    if len(tickers) > 500:
        raise ValidationError('Too many tickers')

    wl = get_watchlist(watchlist_id)
    if wl is None:
        raise NotFoundError(f'Watchlist {watchlist_id} not found')

    if not reorder_watchlist(watchlist_id, tickers):
        from backend.core.error_handlers import DatabaseError
        raise DatabaseError('Failed to reorder watchlist')

    return jsonify({'ok': True}), 200


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------

@watchlist_bp.route('/<int:watchlist_id>/import', methods=['POST'])
@handle_api_errors
def import_csv(watchlist_id: int):
    """Import tickers from a CSV file into a watchlist.
    ---
    tags:
      - Watchlist
    summary: Import tickers from CSV
    description: >
      Accepts a multipart/form-data upload with a CSV file (field name: file,
      max 1 MB). The CSV must contain a column whose header is 'symbol'
      (case-insensitive). Each value is stripped and uppercased before lookup.
      Only symbols already present in the stocks table are accepted.
    consumes:
      - multipart/form-data
    parameters:
      - name: watchlist_id
        in: path
        type: integer
        required: true
      - in: formData
        name: file
        type: file
        required: true
    responses:
      200:
        description: Import summary with counts of added and skipped symbols.
      400:
        description: Bad file type, empty file, missing symbol column, or too many rows.
      404:
        description: Watchlist not found.
      413:
        description: File exceeds the 1 MB size limit.
    """
    # Verify watchlist exists
    wl = get_watchlist(watchlist_id)
    if wl is None:
        raise NotFoundError(f'Watchlist {watchlist_id} not found')

    # Validate file presence
    if 'file' not in request.files:
        raise ValidationError('No file field in request')

    upload = request.files['file']
    filename = upload.filename or ''

    if not filename.lower().endswith('.csv'):
        raise ValidationError('Unsupported file type. Please upload a .csv file')

    raw = upload.read()
    if not raw:
        raise ValidationError('Uploaded file is empty')

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
        raise ValidationError('CSV file has no headers')

    symbol_col = next(
        (f for f in reader.fieldnames if f.strip().lower() == 'symbol'),
        None,
    )
    if symbol_col is None:
        raise ValidationError("CSV must contain a 'symbol' column")

    # Collect tickers, enforcing row limit
    tickers: list[str] = []
    for i, row in enumerate(reader):
        if i >= _MAX_ROWS:
            raise ValidationError(f'CSV exceeds maximum of {_MAX_ROWS} rows')
        val = (row.get(symbol_col) or '').strip().upper()
        if val:
            tickers.append(val)

    if not tickers:
        raise ValidationError('No ticker symbols found in CSV')

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
            skipped_invalid += 1
            invalid_symbols.append(ticker)

    return jsonify({
        'added': added,
        'skipped_duplicates': skipped_duplicates,
        'skipped_invalid': skipped_invalid,
        'invalid_symbols': invalid_symbols,
    }), 200
```