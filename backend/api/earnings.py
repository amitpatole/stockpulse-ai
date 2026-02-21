"""
TickerPulse AI v3.0 - Earnings Calendar API
Blueprint serving upcoming earnings events with watchlist prioritisation.
"""

import logging
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request

from backend.database import db_session

logger = logging.getLogger(__name__)

earnings_bp = Blueprint('earnings', __name__, url_prefix='/api')

_STALE_THRESHOLD_HOURS = 1


@earnings_bp.route('/earnings', methods=['GET'])
def get_earnings():
    """Return upcoming earnings events within the requested window.

    Query Parameters:
        days (int, default 7): Number of days ahead to include.

    Response:
        {
            "events": [...],
            "stale": bool,
            "as_of": "ISO-8601 timestamp"
        }

    Events are sorted watchlist tickers first, then by earnings_date ascending.
    ``stale: true`` when the newest ``fetched_at`` is older than 1 hour,
    signalling the refresh job has not run recently.
    """
    try:
        days = int(request.args.get('days', 7))
    except (ValueError, TypeError):
        days = 7
    days = max(1, min(days, 90))

    today = date.today().isoformat()
    end_date = (date.today() + timedelta(days=days)).isoformat()

    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT
                e.id,
                e.ticker,
                e.company,
                e.earnings_date,
                e.time_of_day,
                e.eps_estimate,
                e.fiscal_quarter,
                e.fetched_at,
                CASE WHEN ws.ticker IS NOT NULL THEN 1 ELSE 0 END AS on_watchlist
            FROM earnings_events e
            LEFT JOIN watchlist_stocks ws ON ws.ticker = e.ticker
            WHERE e.earnings_date >= ? AND e.earnings_date <= ?
            ORDER BY on_watchlist DESC, e.earnings_date ASC, e.ticker ASC
            """,
            (today, end_date),
        ).fetchall()

        # Determine staleness from the most recently fetched row
        newest_row = conn.execute(
            "SELECT MAX(fetched_at) AS newest FROM earnings_events"
        ).fetchone()

    events = [dict(r) for r in rows]
    for ev in events:
        ev['on_watchlist'] = bool(ev['on_watchlist'])

    stale = True
    newest_fetched_at = newest_row['newest'] if newest_row else None
    if newest_fetched_at:
        try:
            fetched_dt = datetime.fromisoformat(newest_fetched_at)
            age_hours = (datetime.utcnow() - fetched_dt).total_seconds() / 3600
            stale = age_hours > _STALE_THRESHOLD_HOURS
        except (ValueError, TypeError):
            stale = True

    return jsonify({
        'events': events,
        'stale': stale,
        'as_of': newest_fetched_at or '',
    })
