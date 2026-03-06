```python
"""
Price alert management - CRUD operations and threshold checking.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import sqlite3

from backend.database import db_session
from backend.core.errors import NotFoundError, ValidationError as TickerPulseValidationError
from backend.models.requests import PriceAlertCreateRequest, PriceAlertUpdateRequest
from backend.models.responses import PriceAlertResponse, PaginationMeta

logger = logging.getLogger(__name__)

VALID_ALERT_TYPES = {"above", "below", "change_percent_up", "change_percent_down"}


def create_price_alert(request: PriceAlertCreateRequest) -> PriceAlertResponse:
    """Create a new price alert with validation."""
    if request.alert_type not in VALID_ALERT_TYPES:
        raise TickerPulseValidationError(f"Invalid alert_type: {request.alert_type}")

    with db_session() as conn:
        cursor = conn.cursor()

        # Verify ticker exists
        cursor.execute("SELECT ticker FROM stocks WHERE ticker = ? AND active = 1", (request.ticker,))
        if not cursor.fetchone():
            raise TickerPulseValidationError(f"Stock ticker '{request.ticker}' not found in watchlist")

        # Check for duplicate alert
        cursor.execute(
            "SELECT id FROM price_alerts WHERE ticker = ? AND alert_type = ? AND threshold = ?",
            (request.ticker, request.alert_type, request.threshold)
        )
        if cursor.fetchone():
            raise TickerPulseValidationError(
                f"Alert already exists for {request.ticker} {request.alert_type} {request.threshold}"
            )

        # Create alert
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            """
            INSERT INTO price_alerts (ticker, alert_type, threshold, is_active, created_at, updated_at)
            VALUES (?, ?, ?, 1, ?, ?)
            """,
            (request.ticker, request.alert_type, request.threshold, now, now)
        )
        alert_id = cursor.lastrowid
        conn.commit()

        # Fetch and return created alert
        return get_price_alert(alert_id)


def get_price_alert(alert_id: int) -> PriceAlertResponse:
    """Get a single price alert by ID."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM price_alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()

    if not row:
        raise NotFoundError(f"Price alert {alert_id} not found")

    return _row_to_response(row)


def list_price_alerts(
    limit: int = 20,
    offset: int = 0,
    ticker: Optional[str] = None,
    active_only: bool = False,
) -> Dict[str, Any]:
    """List price alerts with pagination and filters."""
    with db_session() as conn:
        cursor = conn.cursor()

        # Build query
        where_clauses = []
        params = []

        if ticker:
            where_clauses.append("ticker = ?")
            params.append(ticker.upper())

        if active_only:
            where_clauses.append("is_active = 1")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        cursor.execute(f"SELECT COUNT(*) as count FROM price_alerts WHERE {where_sql}", params)
        total = cursor.fetchone()["count"]

        # Get paginated results
        cursor.execute(
            f"""
            SELECT * FROM price_alerts
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        rows = cursor.fetchall()

    alerts = [_row_to_response(row) for row in rows]
    meta = PaginationMeta(
        total=total,
        limit=limit,
        offset=offset,
        has_next=offset + limit < total,
        has_previous=offset > 0,
    )

    return {
        "alerts": alerts,
        "meta": meta.model_dump(),
    }


def update_price_alert(
    alert_id: int,
    request: PriceAlertUpdateRequest,
) -> PriceAlertResponse:
    """Update an existing price alert."""
    # Verify alert exists
    alert = get_price_alert(alert_id)

    with db_session() as conn:
        cursor = conn.cursor()

        # Build update query
        updates = []
        params = []

        if request.threshold is not None:
            updates.append("threshold = ?")
            params.append(request.threshold)

        if request.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if request.is_active else 0)

        if not updates:
            return alert  # No updates

        updates.append("updated_at = ?")
        params.append(datetime.now(timezone.utc).isoformat())
        params.append(alert_id)

        update_sql = ", ".join(updates)
        cursor.execute(
            f"UPDATE price_alerts SET {update_sql} WHERE id = ?",
            params
        )
        conn.commit()

    return get_price_alert(alert_id)


def delete_price_alert(alert_id: int) -> None:
    """Delete a price alert."""
    # Verify alert exists
    get_price_alert(alert_id)

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM price_alerts WHERE id = ?", (alert_id,))
        conn.commit()


def check_price_thresholds(ticker: str, current_price: float) -> List[int]:
    """
    Check which price alerts are triggered for a ticker at given price.
    Returns list of triggered alert IDs (that haven't been triggered today).
    """
    triggered_ids = []

    with db_session() as conn:
        cursor = conn.cursor()

        # Get active alerts for this ticker
        cursor.execute(
            """
            SELECT id, alert_type, threshold, last_triggered_at
            FROM price_alerts
            WHERE ticker = ? AND is_active = 1
            """,
            (ticker,)
        )
        alerts = cursor.fetchall()

    # Check each alert's threshold
    today = datetime.now(timezone.utc).date().isoformat()

    for alert in alerts:
        alert_id = alert["id"]
        alert_type = alert["alert_type"]
        threshold = alert["threshold"]
        last_triggered = alert["last_triggered_at"]

        # Skip if already triggered today
        if last_triggered and last_triggered.startswith(today):
            continue

        triggered = False

        if alert_type == "above" and current_price >= threshold:
            triggered = True
        elif alert_type == "below" and current_price <= threshold:
            triggered = True
        elif alert_type == "change_percent_up":
            # Would need baseline price to check percentage change
            # For now, skip percentage alerts (requires enhanced price tracking)
            pass
        elif alert_type == "change_percent_down":
            pass

        if triggered:
            triggered_ids.append(alert_id)
            _mark_alert_triggered(alert_id)

    return triggered_ids


def _mark_alert_triggered(alert_id: int) -> None:
    """Mark an alert as triggered and update metadata."""
    now = datetime.now(timezone.utc).isoformat()

    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE price_alerts
            SET triggered_count = triggered_count + 1,
                last_triggered_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (now, now, alert_id)
        )
        conn.commit()


def _row_to_response(row: sqlite3.Row) -> PriceAlertResponse:
    """Convert database row to PriceAlertResponse."""
    return PriceAlertResponse(
        id=row["id"],
        ticker=row["ticker"],
        alert_type=row["alert_type"],
        threshold=row["threshold"],
        is_active=bool(row["is_active"]),
        triggered_count=row["triggered_count"],
        last_triggered_at=row["last_triggered_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
```