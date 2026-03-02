"""
TickerPulse AI v3.0 - Options Flow API Routes
Endpoints for retrieving options flows, alerts, and configuration.
"""

from flask import Blueprint, jsonify, request
import logging

from backend.core.options_flow_manager import OptionsFlowManager

logger = logging.getLogger(__name__)

options_bp = Blueprint("options", __name__, url_prefix="/api/options")

# Global manager instance
_manager = None


def get_manager() -> OptionsFlowManager:
    """Get or create the options flow manager."""
    global _manager
    if _manager is None:
        _manager = OptionsFlowManager()
    return _manager


@options_bp.route("/flows", methods=["GET"])
def list_flows():
    """List recent options flows with filtering and pagination.

    Query Parameters:
        ticker (str, optional): Filter by ticker
        hours (int, optional, default 24): Time window
        min_ratio (float, optional, default 2.0): Minimum unusual ratio
        flow_type (str, optional): 'call_spike', 'put_spike', 'unusual_volume'
        limit (int, default 100, max 100): Results per page
        offset (int, default 0): Pagination offset

    Returns:
        JSON object with data array and meta (total_count, has_next)
    """
    try:
        ticker = request.args.get("ticker")
        hours = int(request.args.get("hours", 24))
        min_ratio = float(request.args.get("min_ratio", 2.0))
        flow_type = request.args.get("flow_type")
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))

        # Validate inputs
        if hours < 1 or hours > 730:  # Max 30 days
            return jsonify({"errors": [{"code": "INVALID_HOURS", "message": "hours must be 1-730"}]}), 400

        if min_ratio < 1.0:
            return jsonify({"errors": [{"code": "INVALID_RATIO", "message": "min_ratio must be >= 1.0"}]}), 400

        if limit < 1 or limit > 100:
            limit = 100

        if offset < 0:
            offset = 0

        manager = get_manager()
        result = manager.get_flows(
            ticker=ticker,
            hours=hours,
            min_ratio=min_ratio,
            flow_type=flow_type,
            limit=limit,
            offset=offset,
        )

        return jsonify(result)
    except ValueError as e:
        return jsonify({"errors": [{"code": "INVALID_PARAM", "message": str(e)}]}), 400
    except Exception as e:
        logger.error(f"Error listing flows: {e}")
        return jsonify({"errors": [{"code": "INTERNAL_ERROR", "message": "Internal server error"}]}), 500


@options_bp.route("/alerts", methods=["GET"])
def list_alerts():
    """List options alerts with pagination.

    Query Parameters:
        ticker (str, optional): Filter by ticker
        severity (str, optional): 'high', 'medium', 'low'
        limit (int, default 50, max 100): Results per page
        offset (int, default 0): Pagination offset

    Returns:
        JSON object with data array and meta (total_count, has_next)
    """
    try:
        ticker = request.args.get("ticker")
        severity = request.args.get("severity")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        if severity and severity not in ("high", "medium", "low"):
            return jsonify({"errors": [{"code": "INVALID_SEVERITY", "message": "severity must be 'high', 'medium', or 'low'"}]}), 400

        if limit < 1 or limit > 100:
            limit = 50

        if offset < 0:
            offset = 0

        manager = get_manager()
        result = manager.get_alerts(
            ticker=ticker,
            severity=severity,
            dismissed=False,  # Only unread
            limit=limit,
            offset=offset,
        )

        return jsonify(result)
    except ValueError as e:
        return jsonify({"errors": [{"code": "INVALID_PARAM", "message": str(e)}]}), 400
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        return jsonify({"errors": [{"code": "INTERNAL_ERROR", "message": "Internal server error"}]}), 500


@options_bp.route("/alerts/<int:alert_id>/dismiss", methods=["PUT"])
def dismiss_alert(alert_id: int):
    """Mark an alert as dismissed (read).

    Parameters:
        alert_id (int): Alert ID

    Returns:
        JSON with success status
    """
    try:
        manager = get_manager()
        success = manager.dismiss_alert(alert_id)

        if success:
            return jsonify({"data": {"alert_id": alert_id, "dismissed": True}})
        else:
            return jsonify({"errors": [{"code": "NOT_FOUND", "message": "Alert not found"}]}), 404
    except Exception as e:
        logger.error(f"Error dismissing alert: {e}")
        return jsonify({"errors": [{"code": "INTERNAL_ERROR", "message": "Internal server error"}]}), 500


@options_bp.route("/config/<ticker>", methods=["GET"])
def get_config(ticker: str):
    """Get options flow tracking configuration for a stock.

    Parameters:
        ticker (str): Stock ticker

    Returns:
        JSON with enabled, volume_spike_threshold
    """
    try:
        manager = get_manager()
        config = manager.get_config(ticker)
        return jsonify({"data": config})
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({"errors": [{"code": "INTERNAL_ERROR", "message": "Internal server error"}]}), 500


@options_bp.route("/config/<ticker>", methods=["PUT"])
def update_config(ticker: str):
    """Update options flow tracking configuration.

    Request Body (JSON):
        enabled (int, optional): 1 or 0
        volume_spike_threshold (float, optional): Minimum 1.0

    Returns:
        JSON with updated config
    """
    try:
        data = request.json or {}
        enabled = data.get("enabled")
        threshold = data.get("volume_spike_threshold")

        if enabled is not None and enabled not in (0, 1):
            return jsonify({"errors": [{"code": "INVALID_ENABLED", "message": "enabled must be 0 or 1"}]}), 400

        if threshold is not None and threshold < 1.0:
            return jsonify({"errors": [{"code": "INVALID_THRESHOLD", "message": "volume_spike_threshold must be >= 1.0"}]}), 400

        manager = get_manager()
        success = manager.set_config(
            ticker=ticker,
            enabled=enabled,
            volume_spike_threshold=threshold,
        )

        if success:
            config = manager.get_config(ticker)
            return jsonify({"data": config})
        else:
            return jsonify({"errors": [{"code": "UPDATE_FAILED", "message": "Failed to update config"}]}), 500
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"errors": [{"code": "INTERNAL_ERROR", "message": "Internal server error"}]}), 500