"""
TickerPulse AI v3.0 - Price Alerts API
Blueprint exposing CRUD endpoints for user-defined price alerts.
"""

import logging
import re

from flask import Blueprint, jsonify, request

from backend.core.alert_manager import create_alert, get_alerts, delete_alert, toggle_alert
from backend.core.settings_manager import get_setting, set_setting
from backend.database import db_session

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api')

_VALID_SOUND_TYPES = {'chime', 'bell', 'beep'}

_SOUND_DEFAULTS = {
    'alert_sound_enabled': 'true',
    'alert_sound_type': 'chime',
    'alert_sound_volume': '70',
    'alert_mute_when_active': 'false',
}

_VALID_CONDITION_TYPES = {'price_above', 'price_below', 'pct_change'}

_TICKER_RE = re.compile(r'^[A-Z]{1,5}$')
_THRESHOLD_MAX = 1_000_000


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
    if not _TICKER_RE.match(ticker):
        return jsonify({'error': 'ticker must be 1–5 uppercase letters'}), 400
    if condition_type not in _VALID_CONDITION_TYPES:
        return jsonify({
            'error': f"Invalid condition_type. Must be one of: {', '.join(sorted(_VALID_CONDITION_TYPES))}"
        }), 400

    try:
        threshold = float(threshold_raw)
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold must be a valid number'}), 400

    if not (0 < threshold <= _THRESHOLD_MAX):
        return jsonify({'error': f'threshold must be > 0 and ≤ {_THRESHOLD_MAX}'}), 400

    if condition_type == 'pct_change' and threshold > 100:
        return jsonify({'error': 'threshold for pct_change must be ≤ 100'}), 400

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


@alerts_bp.route('/alerts/sound-settings', methods=['GET'])
def get_sound_settings():
    """Return current alert sound settings.

    Returns:
        JSON with enabled, sound_type, volume, mute_when_active fields.
    """
    enabled = get_setting('alert_sound_enabled', _SOUND_DEFAULTS['alert_sound_enabled']) == 'true'
    sound_type = get_setting('alert_sound_type', _SOUND_DEFAULTS['alert_sound_type'])
    volume = int(get_setting('alert_sound_volume', _SOUND_DEFAULTS['alert_sound_volume']))
    mute_when_active = get_setting('alert_mute_when_active', _SOUND_DEFAULTS['alert_mute_when_active']) == 'true'
    return jsonify({
        'enabled': enabled,
        'sound_type': sound_type,
        'volume': volume,
        'mute_when_active': mute_when_active,
    })


@alerts_bp.route('/alerts/sound-settings', methods=['PUT'])
def update_sound_settings():
    """Update alert sound settings (partial update supported).

    Request Body (JSON, all fields optional):
        enabled          (bool) : Whether alert sounds are enabled.
        sound_type       (str)  : One of 'chime', 'bell', 'beep'.
        volume           (int)  : Volume from 0 to 100.
        mute_when_active (bool) : Whether to mute when tab is focused.

    Returns:
        200 with the updated settings, or 400 on validation failure.
    """
    data = request.get_json(silent=True) or {}

    if 'sound_type' in data:
        if data['sound_type'] not in _VALID_SOUND_TYPES:
            return jsonify({
                'error': f"Invalid sound_type. Must be one of: {', '.join(sorted(_VALID_SOUND_TYPES))}"
            }), 400

    if 'volume' in data:
        try:
            volume = int(data['volume'])
        except (TypeError, ValueError):
            return jsonify({'error': 'volume must be an integer'}), 400
        if not (0 <= volume <= 100):
            return jsonify({'error': 'volume must be between 0 and 100'}), 400

    if 'enabled' in data:
        set_setting('alert_sound_enabled', 'true' if data['enabled'] else 'false')
    if 'sound_type' in data:
        set_setting('alert_sound_type', data['sound_type'])
    if 'volume' in data:
        set_setting('alert_sound_volume', str(int(data['volume'])))
    if 'mute_when_active' in data:
        set_setting('alert_mute_when_active', 'true' if data['mute_when_active'] else 'false')

    enabled = get_setting('alert_sound_enabled', _SOUND_DEFAULTS['alert_sound_enabled']) == 'true'
    sound_type = get_setting('alert_sound_type', _SOUND_DEFAULTS['alert_sound_type'])
    volume_out = int(get_setting('alert_sound_volume', _SOUND_DEFAULTS['alert_sound_volume']))
    mute_when_active = get_setting('alert_mute_when_active', _SOUND_DEFAULTS['alert_mute_when_active']) == 'true'
    return jsonify({
        'enabled': enabled,
        'sound_type': sound_type,
        'volume': volume_out,
        'mute_when_active': mute_when_active,
    })
