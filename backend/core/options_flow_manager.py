"""
TickerPulse AI v3.0 - Options Flow Manager
Manages options flow detection, alert generation, and per-stock configuration.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from backend.database import db_session
from backend.config import Config

logger = logging.getLogger(__name__)


class OptionsFlowManager:
    """Manages options flow tracking, detection, and alerts."""

    # Severity thresholds (unusual_ratio multiplier)
    SEVERITY_LOW_MIN = 2.0
    SEVERITY_LOW_MAX = 3.0
    SEVERITY_MEDIUM_MIN = 3.0
    SEVERITY_MEDIUM_MAX = 5.0
    SEVERITY_HIGH_MIN = 5.0

    # Default configuration
    DEFAULT_VOLUME_SPIKE_THRESHOLD = 2.0

    def __init__(self):
        """Initialize the manager."""
        pass

    def get_flows(
        self,
        ticker: Optional[str] = None,
        hours: int = 24,
        min_ratio: float = 2.0,
        flow_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict:
        """Get recent options flows with pagination.

        Parameters
        ----------
        ticker : str, optional
            Filter by specific ticker
        hours : int
            Time window in hours (default 24)
        min_ratio : float
            Minimum unusual_ratio to return (default 2.0)
        flow_type : str, optional
            Filter by flow_type ('call_spike', 'put_spike', 'unusual_volume')
        limit : int
            Maximum results (default 100)
        offset : int
            Pagination offset (default 0)

        Returns
        -------
        Dict
            Paginated flows with meta information
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()

                # Build WHERE clause
                where_clauses = ["detected_at >= datetime('now', ?||' hours')"]
                params = [f"-{hours}"]

                if ticker:
                    where_clauses.append("ticker = ?")
                    params.append(ticker)

                if min_ratio > 0:
                    where_clauses.append("unusual_ratio >= ?")
                    params.append(min_ratio)

                if flow_type:
                    where_clauses.append("flow_type = ?")
                    params.append(flow_type)

                where_sql = " AND ".join(where_clauses)

                # Get total count
                count_sql = f"SELECT COUNT(*) as total FROM options_flows WHERE {where_sql}"
                cursor.execute(count_sql, params)
                total_count = cursor.fetchone()["total"]

                # Get paginated results
                limit = max(1, min(limit, 100))
                offset = max(0, offset)

                query_sql = f"""
                    SELECT * FROM options_flows
                    WHERE {where_sql}
                    ORDER BY detected_at DESC, unusual_ratio DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                cursor.execute(query_sql, params)
                flows = [dict(row) for row in cursor.fetchall()]

                return {
                    "data": flows,
                    "meta": {
                        "total_count": total_count,
                        "has_next": (offset + limit) < total_count,
                    },
                }
        except Exception as e:
            logger.error(f"Error getting flows: {e}")
            return {"data": [], "meta": {"total_count": 0, "has_next": False}}

    def get_alerts(
        self,
        ticker: Optional[str] = None,
        severity: Optional[str] = None,
        dismissed: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict:
        """Get options alerts with pagination.

        Parameters
        ----------
        ticker : str, optional
            Filter by ticker
        severity : str, optional
            Filter by severity ('high', 'medium', 'low')
        dismissed : bool
            Include dismissed alerts (default False = unread only)
        limit : int
            Results per page (max 100)
        offset : int
            Pagination offset

        Returns
        -------
        Dict
            Paginated alerts with meta
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()

                where_clauses = []
                params = []

                if not dismissed:
                    where_clauses.append("dismissed = 0")

                if ticker:
                    where_clauses.append("ticker = ?")
                    params.append(ticker)

                if severity:
                    where_clauses.append("severity = ?")
                    params.append(severity)

                where_sql = (
                    " AND ".join(where_clauses) if where_clauses else "1=1"
                )

                # Get total count
                count_sql = f"SELECT COUNT(*) as total FROM options_alerts WHERE {where_sql}"
                cursor.execute(count_sql, params)
                total_count = cursor.fetchone()["total"]

                # Get paginated results
                limit = max(1, min(limit, 100))
                offset = max(0, offset)

                query_sql = f"""
                    SELECT * FROM options_alerts
                    WHERE {where_sql}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                cursor.execute(query_sql, params)
                alerts = [dict(row) for row in cursor.fetchall()]

                return {
                    "data": alerts,
                    "meta": {
                        "total_count": total_count,
                        "has_next": (offset + limit) < total_count,
                    },
                }
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return {"data": [], "meta": {"total_count": 0, "has_next": False}}

    def dismiss_alert(self, alert_id: int) -> bool:
        """Mark an alert as dismissed (read).

        Parameters
        ----------
        alert_id : int
            Alert ID to dismiss

        Returns
        -------
        bool
            True if successful
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE options_alerts SET dismissed = 1 WHERE id = ?",
                    (alert_id,),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error dismissing alert: {e}")
            return False

    def create_flow(
        self,
        ticker: str,
        flow_type: str,
        option_type: str,
        strike_price: float,
        expiry_date: str,
        volume: int,
        open_interest: int,
        unusual_ratio: float,
        price_action: str = "neutral",
    ) -> Optional[int]:
        """Create a new options flow record.

        Returns
        -------
        Optional[int]
            Flow ID if successful, None otherwise
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO options_flows
                    (ticker, flow_type, option_type, strike_price, expiry_date,
                     volume, open_interest, unusual_ratio, price_action, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticker,
                        flow_type,
                        option_type,
                        strike_price,
                        expiry_date,
                        volume,
                        open_interest,
                        unusual_ratio,
                        price_action,
                        datetime.utcnow().isoformat(),
                    ),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating flow: {e}")
            return None

    def create_alert(
        self,
        ticker: str,
        flow_id: Optional[int],
        alert_type: str,
        severity: str,
        message: str,
    ) -> Optional[int]:
        """Create a new options alert.

        Returns
        -------
        Optional[int]
            Alert ID if successful
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO options_alerts
                    (ticker, flow_id, alert_type, severity, message)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (ticker, flow_id, alert_type, severity, message),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            return None

    def get_config(self, ticker: str) -> Dict:
        """Get tracking configuration for a ticker.

        Returns
        -------
        Dict
            Config with enabled, volume_spike_threshold
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM options_flow_config WHERE ticker = ?",
                    (ticker,),
                )
                row = cursor.fetchone()

                if row:
                    return dict(row)
                else:
                    # Return default config
                    return {
                        "ticker": ticker,
                        "enabled": 1,
                        "volume_spike_threshold": self.DEFAULT_VOLUME_SPIKE_THRESHOLD,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
        except Exception as e:
            logger.error(f"Error getting config for {ticker}: {e}")
            return {
                "ticker": ticker,
                "enabled": 1,
                "volume_spike_threshold": self.DEFAULT_VOLUME_SPIKE_THRESHOLD,
            }

    def set_config(
        self,
        ticker: str,
        enabled: Optional[int] = None,
        volume_spike_threshold: Optional[float] = None,
    ) -> bool:
        """Update tracking configuration for a ticker.

        Returns
        -------
        bool
            True if successful
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()

                # Check if config exists
                cursor.execute(
                    "SELECT 1 FROM options_flow_config WHERE ticker = ?",
                    (ticker,),
                )
                exists = cursor.fetchone()

                if exists:
                    # Update existing
                    updates = []
                    params = []

                    if enabled is not None:
                        updates.append("enabled = ?")
                        params.append(enabled)

                    if volume_spike_threshold is not None:
                        updates.append("volume_spike_threshold = ?")
                        params.append(
                            max(1.0, volume_spike_threshold)
                        )  # Minimum 1.0x

                    if updates:
                        updates.append("updated_at = ?")
                        params.append(datetime.utcnow().isoformat())
                        params.append(ticker)

                        query = (
                            f"UPDATE options_flow_config SET {', '.join(updates)} WHERE ticker = ?"
                        )
                        cursor.execute(query, params)
                else:
                    # Insert new
                    cursor.execute(
                        """
                        INSERT INTO options_flow_config
                        (ticker, enabled, volume_spike_threshold, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            ticker,
                            enabled if enabled is not None else 1,
                            max(
                                1.0,
                                volume_spike_threshold
                                if volume_spike_threshold is not None
                                else self.DEFAULT_VOLUME_SPIKE_THRESHOLD,
                            ),
                            datetime.utcnow().isoformat(),
                        ),
                    )

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting config for {ticker}: {e}")
            return False

    def calculate_severity(self, unusual_ratio: float) -> str:
        """Calculate alert severity based on unusual ratio.

        Parameters
        ----------
        unusual_ratio : float
            Volume ratio (current / 20-day average)

        Returns
        -------
        str
            'low', 'medium', or 'high'
        """
        if unusual_ratio >= self.SEVERITY_HIGH_MIN:
            return "high"
        elif unusual_ratio >= self.SEVERITY_MEDIUM_MIN:
            return "medium"
        else:
            return "low"