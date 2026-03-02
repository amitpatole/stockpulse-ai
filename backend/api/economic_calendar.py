"""
TickerPulse AI - Economic Calendar API Blueprint
Endpoints for listing events, viewing impacts, and syncing data.
"""

import logging
from flask import Blueprint, request, jsonify
from backend.core.economic_calendar_manager import EconomicCalendarManager

logger = logging.getLogger(__name__)

bp = Blueprint("economic_calendar", __name__, url_prefix="/api/economic-calendar")


@bp.route("", methods=["GET"])
def list_events():
    """List economic events with optional filtering.

    Query Parameters:
    - start_date: YYYY-MM-DD
    - end_date: YYYY-MM-DD
    - country: Country code (e.g., 'US')
    - importance: 'low' | 'medium' | 'high'
    - limit: 1-100 (default 50)
    - offset: >= 0 (default 0)

    Response:
    {
        "data": [...events...],
        "meta": {"total_count": N, "limit": L, "offset": O, "has_next": bool},
        "errors": []
    }
    """
    try:
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        country = request.args.get("country")
        importance = request.args.get("importance")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        result = EconomicCalendarManager.list_events(
            start_date=start_date,
            end_date=end_date,
            country=country,
            importance=importance,
            limit=limit,
            offset=offset,
        )

        return jsonify(result), 200
    except Exception as e:
        logger.exception("Error listing economic events")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [str(e)],
        }), 500


@bp.route("/<int:event_id>/impacts", methods=["GET"])
def get_event_impacts(event_id: int):
    """Get stocks affected by a specific economic event.

    Path Parameters:
    - event_id: ID of the economic event

    Response:
    {
        "data": {
            "id": 1,
            "event_name": "CPI",
            "country": "US",
            "impacts": [
                {"ticker": "GLD", "sensitivity_score": 8.5},
                ...
            ]
        },
        "meta": {"impact_count": N},
        "errors": []
    }
    """
    try:
        result = EconomicCalendarManager.get_event_impacts(event_id)
        status = 200 if result["data"] else 404
        return jsonify(result), status
    except Exception as e:
        logger.exception("Error fetching event impacts")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [str(e)],
        }), 500


@bp.route("/watchlist-events", methods=["GET"])
def get_watchlist_events():
    """List economic events that affect monitored stocks.

    Query Parameters:
    - limit: 1-100 (default 50)
    - offset: >= 0 (default 0)

    Response:
    {
        "data": [...events with impacts...],
        "meta": {"total_count": N, "limit": L, "offset": O, "has_next": bool},
        "errors": []
    }
    """
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        result = EconomicCalendarManager.get_watchlist_events(limit=limit, offset=offset)

        return jsonify(result), 200
    except Exception as e:
        logger.exception("Error fetching watchlist events")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [str(e)],
        }), 500


@bp.route("/sync", methods=["POST"])
def sync_events():
    """Internal endpoint to trigger economic calendar sync.

    This endpoint is called by the background scheduler.
    In production, this should require authentication or be internal-only.

    Response:
    {
        "data": {"synced_count": N, "errors_count": N},
        "meta": {},
        "errors": []
    }
    """
    try:
        # Import here to avoid circular dependency
        from backend.jobs.sync_economic_calendar import _sync_economic_calendar

        synced_count, errors_count = _sync_economic_calendar()

        return jsonify({
            "data": {
                "synced_count": synced_count,
                "errors_count": errors_count,
            },
            "meta": {},
            "errors": [],
        }), 202
    except Exception as e:
        logger.exception("Error syncing economic calendar")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [str(e)],
        }), 500