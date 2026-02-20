"""
TickerPulse AI v3.0 - Price Alerts API
Blueprint exposing CRUD endpoints for user-defined price alerts.
"""

import logging

from flask import Blueprint, jsonify, request

from backend.core.alert_manager import create_alert, get_alerts, delete_alert, toggle_alert
from backend.database import db_session

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api')

_VALID_CONDITION_TYPES = {'price_above', 'price_below', 'pct_change'}


@alerts_bp.route('/alerts', methods=['GET'])
def list_alerts():
    """Return all price alerts.

    Returns:
        JSON array of price alert objects.
    """
    return jsonify(get_alerts())


@alerts_bp.route('/alerts', methods=['POST'])
def create_alert_endpoint():
    """Create a new price alert.

    Request Body (JSON):
        ticker         (str)   : Stock ticker — must exist in the stocks table.
        condition_type (str)   : One of 'price_above', 'price_below', 'pct_change'.
        threshold      (float) : Numeric threshold value.

    Returns:
        201 with the created alert object, or 400 on validation failure.
    """
    data = request.get_json(silent=True) or {}

    ticker = str(data.get('ticker', '')).strip().upper()
    condition_type = str(data.get('condition_type', '')).strip()
    threshold_raw = data.get('threshold')

    # Validate required fields
    if not ticker:
        return jsonify({'error': 'Missing required field: ticker'}), 400
    if condition_type not in _VALID_CONDITION_TYPES:
        return jsonify({
            'error': f"Invalid condition_type. Must be one of: {', '.join(sorted(_VALID_CONDITION_TYPES))}"
        }), 400

    try:
        threshold = float(threshold_raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold must be a valid number'}), 400

    # Verify the ticker exists in the stocks table
    with db_session() as conn:
        row = conn.execute(
            'SELECT ticker FROM stocks WHERE ticker = ? AND active = 1', (ticker,)
        ).fetchone()
    if row is None:
        return jsonify({
            'error': f"Ticker '{ticker}' is not in the monitored stocks list. Add it first."
        }), 400

    alert = create_alert(ticker, condition_type, threshold)
    return jsonify(alert), 201


@alerts_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert_endpoint(alert_id: int):
    """Delete a price alert by ID.

    Returns:
        200 on success, 404 if the alert does not exist.
    """
    deleted = delete_alert(alert_id)
    if not deleted:
        return jsonify({'error': f'Alert {alert_id} not found'}), 404
    return jsonify({'success': True, 'id': alert_id})


@alerts_bp.route('/alerts/<int:alert_id>/toggle', methods=['PUT'])
def toggle_alert_endpoint(alert_id: int):
    """Toggle the enabled state of a price alert.

    Returns:
        200 with the updated alert, 404 if the alert does not exist.
    """
    updated = toggle_alert(alert_id)
    if updated is None:
        return jsonify({'error': f'Alert {alert_id} not found'}), 404
    return jsonify(updated)
