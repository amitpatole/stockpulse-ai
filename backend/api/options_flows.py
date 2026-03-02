```python
"""
TickerPulse AI - Options Flow API Endpoints
REST API for querying options flows and managing alert subscriptions.
"""

import logging
from datetime import datetime
from typing import Optional, List

from flask import Blueprint, request, jsonify, g
from flask_login import login_required, current_user

from backend.database import db_session, get_adapter
from backend.config import Config

logger = logging.getLogger(__name__)

options_flows_bp = Blueprint('options_flows', __name__, url_prefix='/api/options')


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_response_format(data, total_count: int, limit: int, offset: int):
    """Format response following TickerPulse convention.

    Parameters
    ----------
    data : list
        The data payload.
    total_count : int
        Total count of items (for pagination).
    limit : int
        Items per page.
    offset : int
        Offset in results.

    Returns
    -------
    dict
        Response in {data, meta, errors} format.
    """
    has_next = (offset + limit) < total_count
    return {
        'data': data,
        'meta': {
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': has_next,
        },
        'errors': None,
    }


def _validate_pagination(limit: int = 20, offset: int = 0) -> tuple:
    """Validate and clamp pagination parameters.

    Parameters
    ----------
    limit : int
        Requested limit.
    offset : int
        Requested offset.

    Returns
    -------
    tuple
        Clamped (limit, offset).
    """
    # Clamp limit to [1, 100]
    if limit < 1:
        limit = 1
    elif limit > 100:
        limit = 100
    
    # Offset must be >= 0
    if offset < 0:
        offset = 0
    
    return limit, offset


# ---------------------------------------------------------------------------
# Options Flows Endpoints
# ---------------------------------------------------------------------------

@options_flows_bp.route('/flows', methods=['GET'])
@login_required
def list_flows():
    """Get recent options flows with optional filtering.

    Query Parameters
    ----------------
    ticker : str, optional
        Filter by ticker symbol.
    flow_type : str, optional
        Filter by flow type: 'unusual_volume' | 'large_trade' | 'put_call_imbalance'.
    min_anomaly_score : float, optional
        Only return flows with anomaly_score >= this value (default: 0).
    limit : int, optional
        Items per page [1-100] (default: 20).
    offset : int, optional
        Pagination offset (default: 0).

    Returns
    -------
    dict
        {data: [flows], meta: {total_count, limit, offset, has_next}, errors: null}
    """
    try:
        # Parse query parameters
        ticker = request.args.get('ticker', '').upper()
        flow_type = request.args.get('flow_type', '')
        min_anomaly_score = float(request.args.get('min_anomaly_score', 0.0))
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        limit, offset = _validate_pagination(limit, offset)

        with db_session() as conn:
            adapter = get_adapter()
            cursor = conn.cursor()

            # Build query
            where_clauses = []
            params = []

            if ticker:
                where_clauses.append('ticker = ?')
                params.append(ticker)
            
            if flow_type:
                where_clauses.append('flow_type = ?')
                params.append(flow_type)
            
            if min_anomaly_score > 0:
                where_clauses.append('anomaly_score >= ?')
                params.append(min_anomaly_score)

            where_clause = ' AND '.join(where_clauses) if where_clauses else '1=1'

            # Get total count
            count_sql = f'SELECT COUNT(*) as cnt FROM options_flows WHERE {where_clause}'
            cursor.execute(count_sql, params)
            total_count = cursor.fetchone()['cnt']

            # Get paginated results
            sql = f"""
                SELECT id, ticker, contract, option_type, strike, expiration, 
                       volume, open_interest, bid_ask_spread, iv_percentile,
                       flow_type, anomaly_score, created_at, is_alert, user_note
                FROM options_flows
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            cursor.execute(sql, params + [limit, offset])
            rows = cursor.fetchall()

            flows = [dict(row) for row in rows]

            return jsonify(_get_response_format(flows, total_count, limit, offset))

    except ValueError as exc:
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INVALID_PARAM', 'message': str(exc)}]
        }), 400
    except Exception as exc:
        logger.error(f"Error listing flows: {exc}")
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INTERNAL_ERROR', 'message': 'Failed to list flows'}]
        }), 500


@options_flows_bp.route('/flows/<ticker>', methods=['GET'])
@login_required
def get_ticker_flows(ticker: str):
    """Get flows for a specific ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol.

    Query Parameters
    ----------------
    limit : int, optional
        Items per page [1-100] (default: 20).
    offset : int, optional
        Pagination offset (default: 0).

    Returns
    -------
    dict
        {data: [flows], meta: {total_count, limit, offset, has_next}, errors: null}
    """
    ticker = ticker.upper()
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    limit, offset = _validate_pagination(limit, offset)

    try:
        with db_session() as conn:
            adapter = get_adapter()
            cursor = conn.cursor()

            # Count
            cursor.execute(
                'SELECT COUNT(*) as cnt FROM options_flows WHERE ticker = ?',
                (ticker,)
            )
            total_count = cursor.fetchone()['cnt']

            # Fetch
            cursor.execute("""
                SELECT id, ticker, contract, option_type, strike, expiration,
                       volume, open_interest, bid_ask_spread, iv_percentile,
                       flow_type, anomaly_score, created_at, is_alert, user_note
                FROM options_flows
                WHERE ticker = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (ticker, limit, offset))
            rows = cursor.fetchall()

            flows = [dict(row) for row in rows]

            return jsonify(_get_response_format(flows, total_count, limit, offset))

    except Exception as exc:
        logger.error(f"Error getting flows for {ticker}: {exc}")
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INTERNAL_ERROR', 'message': f'Failed to get flows for {ticker}'}]
        }), 500


@options_flows_bp.route('/flows/<int:flow_id>', methods=['PATCH'])
@login_required
def update_flow(flow_id: int):
    """Update a flow (e.g., add user note, mark as viewed).

    Parameters
    ----------
    flow_id : int
        The flow ID.

    Request Body
    ------------
    {
        "user_note": "string",
        "is_alert": boolean
    }

    Returns
    -------
    dict
        Updated flow object.
    """
    try:
        data = request.get_json() or {}
        user_note = data.get('user_note')
        is_alert = data.get('is_alert')

        with db_session() as conn:
            cursor = conn.cursor()

            # Fetch existing flow
            cursor.execute(
                'SELECT * FROM options_flows WHERE id = ?',
                (flow_id,)
            )
            flow = cursor.fetchone()
            if not flow:
                return jsonify({
                    'data': None,
                    'meta': None,
                    'errors': [{'code': 'NOT_FOUND', 'message': f'Flow {flow_id} not found'}]
                }), 404

            # Update fields
            update_fields = []
            params = []
            if user_note is not None:
                update_fields.append('user_note = ?')
                params.append(user_note)
            if is_alert is not None:
                update_fields.append('is_alert = ?')
                params.append(int(is_alert))

            if update_fields:
                sql = f"UPDATE options_flows SET {', '.join(update_fields)} WHERE id = ?"
                params.append(flow_id)
                cursor.execute(sql, params)
                conn.commit()

            # Return updated flow
            cursor.execute('SELECT * FROM options_flows WHERE id = ?', (flow_id,))
            updated = dict(cursor.fetchone())

            return jsonify({
                'data': updated,
                'meta': None,
                'errors': None
            })

    except Exception as exc:
        logger.error(f"Error updating flow {flow_id}: {exc}")
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INTERNAL_ERROR', 'message': 'Failed to update flow'}]
        }), 500


# ---------------------------------------------------------------------------
# Alert Subscriptions Endpoints
# ---------------------------------------------------------------------------

@options_flows_bp.route('/alerts/subscriptions', methods=['GET'])
@login_required
def get_subscriptions():
    """Get user's alert subscriptions.

    Returns
    -------
    dict
        {data: [subscriptions], meta: null, errors: null}
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else g.get('user_id')
        
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, ticker, flow_type, min_anomaly_score, is_active, created_at
                FROM alert_subscriptions
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            rows = cursor.fetchall()

            subscriptions = [dict(row) for row in rows]

            return jsonify({
                'data': subscriptions,
                'meta': None,
                'errors': None
            })

    except Exception as exc:
        logger.error(f"Error fetching subscriptions for user: {exc}")
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INTERNAL_ERROR', 'message': 'Failed to fetch subscriptions'}]
        }), 500


@options_flows_bp.route('/alerts/subscriptions', methods=['POST'])
@login_required
def create_subscription():
    """Create an alert subscription.

    Request Body
    ------------
    {
        "ticker": "AAPL",  // optional, null = all tickers
        "flow_type": "unusual_volume",  // optional, null = all types
        "min_anomaly_score": 70.0,  // optional, default 70
        "is_active": true
    }

    Returns
    -------
    dict
        {data: subscription, meta: null, errors: null}
    """
    try:
        data = request.get_json() or {}
        user_id = current_user.id if hasattr(current_user, 'id') else g.get('user_id')

        ticker = data.get('ticker')
        flow_type = data.get('flow_type')
        min_anomaly_score = float(data.get('min_anomaly_score', 70.0))
        is_active = int(data.get('is_active', 1))

        # Validate flow_type if provided
        valid_types = ['unusual_volume', 'large_trade', 'put_call_imbalance']
        if flow_type and flow_type not in valid_types:
            return jsonify({
                'data': None,
                'meta': None,
                'errors': [{'code': 'INVALID_PARAM', 'message': f'Invalid flow_type: {flow_type}'}]
            }), 400

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alert_subscriptions
                (user_id, ticker, flow_type, min_anomaly_score, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, ticker, flow_type, min_anomaly_score, is_active))
            conn.commit()

            sub_id = cursor.lastrowid
            cursor.execute(
                'SELECT id, ticker, flow_type, min_anomaly_score, is_active, created_at FROM alert_subscriptions WHERE id = ?',
                (sub_id,)
            )
            subscription = dict(cursor.fetchone())

            return jsonify({
                'data': subscription,
                'meta': None,
                'errors': None
            }), 201

    except ValueError as exc:
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INVALID_PARAM', 'message': str(exc)}]
        }), 400
    except Exception as exc:
        logger.error(f"Error creating subscription: {exc}")
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INTERNAL_ERROR', 'message': 'Failed to create subscription'}]
        }), 500


@options_flows_bp.route('/alerts/subscriptions/<int:sub_id>', methods=['DELETE'])
@login_required
def delete_subscription(sub_id: int):
    """Delete an alert subscription.

    Parameters
    ----------
    sub_id : int
        The subscription ID.

    Returns
    -------
    dict
        {data: null, meta: null, errors: null} (204 No Content)
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else g.get('user_id')

        with db_session() as conn:
            cursor = conn.cursor()

            # Verify ownership
            cursor.execute(
                'SELECT user_id FROM alert_subscriptions WHERE id = ?',
                (sub_id,)
            )
            row = cursor.fetchone()
            if not row or row['user_id'] != user_id:
                return jsonify({
                    'data': None,
                    'meta': None,
                    'errors': [{'code': 'NOT_FOUND', 'message': f'Subscription {sub_id} not found'}]
                }), 404

            cursor.execute('DELETE FROM alert_subscriptions WHERE id = ?', (sub_id,))
            conn.commit()

            return '', 204

    except Exception as exc:
        logger.error(f"Error deleting subscription {sub_id}: {exc}")
        return jsonify({
            'data': None,
            'meta': None,
            'errors': [{'code': 'INTERNAL_ERROR', 'message': 'Failed to delete subscription'}]
        }), 500
```