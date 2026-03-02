```python
"""
TickerPulse AI v3.0 - API Quota Manager
Tracks API usage and quota limits across all data providers.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from backend.database import get_adapter

logger = logging.getLogger(__name__)


class QuotaStatus:
    """Status indicator for quota usage"""
    NORMAL = 'normal'      # < 50% used
    WARNING = 'warning'    # 50-80% used
    CRITICAL = 'critical'  # > 80% used


class QuotaManager:
    """Manages API quotas across all providers"""

    def __init__(self):
        self.adapter = get_adapter()

    def record_usage(
        self,
        provider_name: str,
        quota_type: str,
        limit_value: int,
        used: int,
        reset_at: Optional[datetime] = None,
    ) -> None:
        """
        Record or update API quota usage for a provider.

        Parameters
        ----------
        provider_name : str
            Name of the provider (e.g., 'sec', 'tradingview', 'coingecko')
        quota_type : str
            Type of quota (e.g., 'daily_requests', 'bulk_submissions')
        limit_value : int
            Hard limit for this quota
        used : int
            Current usage count
        reset_at : datetime, optional
            When the quota resets
        """
        try:
            reset_time = reset_at.isoformat() + 'Z' if reset_at else None
            now = datetime.utcnow().isoformat() + 'Z'

            sql = """
            INSERT INTO api_quotas (provider_name, quota_type, limit_value, used, reset_at, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider_name, quota_type) DO UPDATE SET
                limit_value = excluded.limit_value,
                used = excluded.used,
                reset_at = excluded.reset_at,
                last_updated = excluded.last_updated
            """

            with self.adapter.get_connection() as conn:
                self.adapter.execute(
                    conn,
                    sql,
                    (provider_name, quota_type, limit_value, used, reset_time, now)
                )
                conn.commit()

            # Also record to history for trend analysis
            self.record_quota_history(provider_name, quota_type, used, limit_value)

            logger.debug(
                f"Recorded quota: {provider_name}/{quota_type} = {used}/{limit_value}"
            )
        except Exception as e:
            logger.error(f"Error recording quota for {provider_name}: {e}")

    def record_quota_history(
        self,
        provider_name: str,
        quota_type: str,
        used: int,
        limit_value: int,
    ) -> None:
        """
        Record a historical snapshot of quota usage.

        Parameters
        ----------
        provider_name : str
            Name of the provider
        quota_type : str
            Type of quota
        used : int
            Current usage count
        limit_value : int
            Quota limit
        """
        try:
            now = datetime.utcnow().isoformat() + 'Z'

            sql = """
            INSERT INTO quota_history (provider_name, quota_type, used, limit_value, recorded_at)
            VALUES (?, ?, ?, ?, ?)
            """

            with self.adapter.get_connection() as conn:
                self.adapter.execute(
                    conn,
                    sql,
                    (provider_name, quota_type, used, limit_value, now)
                )
                conn.commit()

            logger.debug(
                f"Recorded quota history: {provider_name}/{quota_type} = {used}/{limit_value}"
            )
        except Exception as e:
            logger.error(f"Error recording quota history for {provider_name}: {e}")

    def get_quota_history(
        self,
        provider_name: Optional[str] = None,
        hours: int = 48,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get historical quota data for analysis.

        Parameters
        ----------
        provider_name : str, optional
            Filter by specific provider. If None, returns all providers.
        hours : int
            Number of hours of history to retrieve (default: 48)
        limit : int
            Maximum number of records to return (clamped to 100)

        Returns
        -------
        list
            Historical quota records with timestamp
        """
        try:
            # Clamp limit to 100
            limit = min(limit, 100)
            limit = max(limit, 1)

            cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat() + 'Z'

            if provider_name:
                sql = """
                SELECT provider_name, quota_type, used, limit_value, recorded_at
                FROM quota_history
                WHERE provider_name = ? AND recorded_at >= ?
                ORDER BY recorded_at DESC
                LIMIT ?
                """
                params = (provider_name, cutoff_time, limit)
            else:
                sql = """
                SELECT provider_name, quota_type, used, limit_value, recorded_at
                FROM quota_history
                WHERE recorded_at >= ?
                ORDER BY recorded_at DESC
                LIMIT ?
                """
                params = (cutoff_time, limit)

            history = []
            with self.adapter.get_connection() as conn:
                cursor = self.adapter.execute(conn, sql, params)
                if cursor:
                    for row in self.adapter.fetchall(cursor):
                        # Calculate percent_used
                        limit_val = row['limit_value']
                        used_val = row['used']
                        percent_used = int((used_val / limit_val * 100)) if limit_val > 0 else 0

                        history.append({
                            'provider': row['provider_name'],
                            'quota_type': row['quota_type'],
                            'used': used_val,
                            'limit': limit_val,
                            'percent_used': percent_used,
                            'recorded_at': row['recorded_at'],
                        })

            return list(reversed(history))  # Return in chronological order
        except Exception as e:
            logger.error(f"Error retrieving quota history: {e}")
            return []

    def get_provider_analytics(self, provider_name: str, hours: int = 48) -> Dict[str, Any]:
        """
        Get analytics for a specific provider's quotas.

        Parameters
        ----------
        provider_name : str
            Name of the provider
        hours : int
            Number of hours to analyze

        Returns
        -------
        dict
            Analytics including peak usage, average usage, etc.
        """
        try:
            history = self.get_quota_history(provider_name, hours=hours, limit=1000)

            if not history:
                return {
                    'provider': provider_name,
                    'peak_usage_percent': 0,
                    'average_usage_percent': 0,
                    'quota_types': [],
                }

            # Group by quota type and calculate stats
            quota_stats = {}
            for record in history:
                qt = record['quota_type']
                if qt not in quota_stats:
                    quota_stats[qt] = []
                quota_stats[qt].append(record['percent_used'])

            # Calculate aggregates
            peak_usage = 0
            avg_usage = 0
            total_percent = 0
            total_count = 0

            for qt, usages in quota_stats.items():
                peak_usage = max(peak_usage, max(usages) if usages else 0)
                total_percent += sum(usages)
                total_count += len(usages)

            avg_usage = int(total_percent / total_count) if total_count > 0 else 0

            return {
                'provider': provider_name,
                'peak_usage_percent': peak_usage,
                'average_usage_percent': avg_usage,
                'quota_types': list(quota_stats.keys()),
                'hours_analyzed': hours,
                'total_records': len(history),
            }
        except Exception as e:
            logger.error(f"Error calculating provider analytics for {provider_name}: {e}")
            return {
                'provider': provider_name,
                'peak_usage_percent': 0,
                'average_usage_percent': 0,
                'quota_types': [],
            }

    def increment_usage(
        self,
        provider_name: str,
        quota_type: str,
        amount: int = 1,
    ) -> None:
        """
        Increment usage count for a quota.

        Parameters
        ----------
        provider_name : str
            Name of the provider
        quota_type : str
            Type of quota
        amount : int
            Amount to increment by (default: 1)
        """
        try:
            now = datetime.utcnow().isoformat() + 'Z'

            sql = """
            UPDATE api_quotas
            SET used = used + ?, last_updated = ?
            WHERE provider_name = ? AND quota_type = ?
            """

            with self.adapter.get_connection() as conn:
                self.adapter.execute(conn, sql, (amount, now, provider_name, quota_type))
                conn.commit()

            logger.debug(f"Incremented {provider_name}/{quota_type} by {amount}")
        except Exception as e:
            logger.error(f"Error incrementing quota for {provider_name}: {e}")

    def get_quota(
        self,
        provider_name: str,
        quota_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get quota details for a specific provider and quota type.

        Parameters
        ----------
        provider_name : str
            Name of the provider
        quota_type : str
            Type of quota

        Returns
        -------
        dict or None
            Quota object with provider, quota_type, limit, used, percent_used, status, reset_at
        """
        try:
            sql = """
            SELECT provider_name, quota_type, limit_value, used, reset_at, last_updated
            FROM api_quotas
            WHERE provider_name = ? AND quota_type = ?
            """

            with self.adapter.get_connection() as conn:
                cursor = self.adapter.execute(conn, sql, (provider_name, quota_type))
                row = self.adapter.fetchone(cursor) if cursor else None

            if not row:
                return None

            return self._format_quota_row(row)
        except Exception as e:
            logger.error(f"Error retrieving quota for {provider_name}: {e}")
            return None

    def get_all_quotas(self) -> List[Dict[str, Any]]:
        """
        Get all quotas across all providers.

        Returns
        -------
        list
            List of quota objects
        """
        try:
            sql = """
            SELECT provider_name, quota_type, limit_value, used, reset_at, last_updated
            FROM api_quotas
            ORDER BY provider_name, quota_type
            """

            quotas = []
            with self.adapter.get_connection() as conn:
                cursor = self.adapter.execute(conn, sql, [])
                if cursor:
                    for row in self.adapter.fetchall(cursor):
                        quotas.append(self._format_quota_row(row))

            return quotas
        except Exception as e:
            logger.error(f"Error retrieving all quotas: {e}")
            return []

    def get_provider_quotas(self, provider_name: str) -> List[Dict[str, Any]]:
        """
        Get all quotas for a specific provider.

        Parameters
        ----------
        provider_name : str
            Name of the provider

        Returns
        -------
        list
            List of quota objects for that provider
        """
        try:
            sql = """
            SELECT provider_name, quota_type, limit_value, used, reset_at, last_updated
            FROM api_quotas
            WHERE provider_name = ?
            ORDER BY quota_type
            """

            quotas = []
            with self.adapter.get_connection() as conn:
                cursor = self.adapter.execute(conn, sql, [provider_name])
                if cursor:
                    for row in self.adapter.fetchall(cursor):
                        quotas.append(self._format_quota_row(row))

            return quotas
        except Exception as e:
            logger.error(f"Error retrieving quotas for {provider_name}: {e}")
            return []

    def _format_quota_row(self, row: Any) -> Dict[str, Any]:
        """Format a quota database row into the API response format."""
        limit_value = row['limit_value']
        used = row['used']

        # Calculate percentage used
        percent_used = int((used / limit_value * 100)) if limit_value > 0 else 0

        # Determine status
        if percent_used < 50:
            status = QuotaStatus.NORMAL
        elif percent_used < 80:
            status = QuotaStatus.WARNING
        else:
            status = QuotaStatus.CRITICAL

        return {
            'provider': row['provider_name'],
            'quota_type': row['quota_type'],
            'limit': limit_value,
            'used': used,
            'percent_used': percent_used,
            'reset_at': row['reset_at'],
            'status': status,
            'last_updated': row['last_updated'],
        }


# Global instance
_quota_manager: Optional[QuotaManager] = None


def get_quota_manager() -> QuotaManager:
    """Get or create the global quota manager instance."""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
```