"""
TickerPulse AI - Rate Limit Manager
Tracks API usage across providers and calculates current/historical metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Literal

from backend.database import db_session

logger = logging.getLogger(__name__)

# Default reset intervals per provider (in seconds)
DEFAULT_RESET_INTERVALS = {
    'CoinGecko': 3600,      # 1 hour
    'TradingView': 86400,   # 24 hours
    'SEC': 28800,           # 8 hours
}

# Provider status threshold
ALERT_THRESHOLD_DEFAULT = 80
CRITICAL_THRESHOLD = 95


class RateLimitManager:
    """Manages API rate limit tracking and analytics."""

    @staticmethod
    def log_api_call(
        provider_name: str,
        endpoint: str,
        status_code: int,
        response_time_ms: int
    ) -> None:
        """
        Log an API call to the usage logs table.
        
        Parameters
        ----------
        provider_name : str
            Name of the provider (CoinGecko, TradingView, SEC)
        endpoint : str
            API endpoint called (e.g., '/quote', '/search')
        status_code : int
            HTTP response status code
        response_time_ms : int
            Response time in milliseconds
        """
        try:
            # Ensure provider exists in api_rate_limits
            RateLimitManager.ensure_provider_exists(provider_name)
            
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO api_usage_logs
                    (provider_name, endpoint, status_code, response_time_ms, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (provider_name, endpoint, status_code, response_time_ms)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log API call for {provider_name}: {e}", exc_info=True)

    @staticmethod
    def ensure_provider_exists(provider_name: str) -> None:
        """
        Ensure provider exists in api_rate_limits table.
        Creates entry with default values if missing.
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Check if provider exists
                cursor.execute(
                    "SELECT id FROM api_rate_limits WHERE provider_name = ?",
                    (provider_name,)
                )
                
                if cursor.fetchone() is None:
                    # Create default entry
                    reset_interval = DEFAULT_RESET_INTERVALS.get(provider_name, 3600)
                    reset_time = datetime.utcnow() + timedelta(seconds=reset_interval)
                    
                    cursor.execute(
                        """
                        INSERT INTO api_rate_limits
                        (provider_name, limit_value, reset_time, alert_threshold)
                        VALUES (?, ?, ?, ?)
                        """,
                        (provider_name, 100, reset_time.isoformat(), ALERT_THRESHOLD_DEFAULT)
                    )
                    conn.commit()
                    logger.info(f"Created default rate limit entry for {provider_name}")
        except Exception as e:
            logger.error(f"Failed to ensure provider {provider_name} exists: {e}", exc_info=True)

    @staticmethod
    def get_current_usage(provider_name: str) -> Dict[str, any]:
        """
        Get current usage metrics for a provider.
        
        Returns
        -------
        dict with keys:
            - provider: str
            - limit_value: int
            - current_usage: int (count of logs in current period)
            - usage_pct: float (0-100+)
            - reset_in_seconds: int (seconds until reset)
            - status: 'healthy' | 'warning' | 'critical'
        """
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Get provider limit and reset time
                cursor.execute(
                    """
                    SELECT limit_value, reset_time, alert_threshold
                    FROM api_rate_limits
                    WHERE provider_name = ?
                    """,
                    (provider_name,)
                )
                
                row = cursor.fetchone()
                if not row:
                    return {
                        'provider': provider_name,
                        'limit_value': 0,
                        'current_usage': 0,
                        'usage_pct': 0.0,
                        'reset_in_seconds': 0,
                        'status': 'unknown'
                    }
                
                limit_value = row[0]
                reset_time_str = row[1]
                alert_threshold = row[2]
                
                # Parse reset time
                reset_time = datetime.fromisoformat(reset_time_str.replace('Z', '+00:00'))
                now = datetime.utcnow()
                reset_in_seconds = max(0, int((reset_time - now).total_seconds()))
                
                # Calculate reset interval (if reset_time is in past, use default)
                reset_interval = DEFAULT_RESET_INTERVALS.get(provider_name, 3600)
                cutoff_time = now - timedelta(seconds=reset_interval)
                
                # Count logs in current period
                cursor.execute(
                    """
                    SELECT COUNT(*) as count
                    FROM api_usage_logs
                    WHERE provider_name = ? AND created_at > ?
                    """,
                    (provider_name, cutoff_time.isoformat())
                )
                
                current_usage = cursor.fetchone()[0]
                
                # Calculate percentage
                usage_pct = (current_usage / limit_value * 100) if limit_value > 0 else 0.0
                
                # Determine status
                if usage_pct >= CRITICAL_THRESHOLD:
                    status = 'critical'
                elif usage_pct >= alert_threshold:
                    status = 'warning'
                else:
                    status = 'healthy'
                
                return {
                    'provider': provider_name,
                    'limit_value': limit_value,
                    'current_usage': current_usage,
                    'usage_pct': round(usage_pct, 1),
                    'reset_in_seconds': reset_in_seconds,
                    'status': status
                }
        except Exception as e:
            logger.error(f"Failed to get current usage for {provider_name}: {e}", exc_info=True)
            return {
                'provider': provider_name,
                'limit_value': 0,
                'current_usage': 0,
                'usage_pct': 0.0,
                'reset_in_seconds': 0,
                'status': 'error'
            }

    @staticmethod
    def get_all_providers() -> List[Dict[str, any]]:
        """Get current usage for all configured providers."""
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT DISTINCT provider_name FROM api_rate_limits ORDER BY provider_name"
                )
                providers = [row[0] for row in cursor.fetchall()]
            
            return [RateLimitManager.get_current_usage(p) for p in providers]
        except Exception as e:
            logger.error(f"Failed to get all providers: {e}", exc_info=True)
            return []

    @staticmethod
    def get_usage_history(
        provider_name: str,
        hours: int = 24,
        interval: Literal['hourly', 'daily'] = 'hourly'
    ) -> List[Dict[str, any]]:
        """
        Get historical usage data for a provider.
        
        Parameters
        ----------
        provider_name : str
            Name of the provider
        hours : int
            Number of hours to retrieve (1-720)
        interval : str
            Aggregation interval ('hourly' or 'daily')
        
        Returns
        -------
        list of dicts with keys:
            - timestamp: str (ISO format)
            - usage_pct: float
            - call_count: int
            - errors: int (count of non-2xx responses)
        """
        # Validate parameters
        hours = max(1, min(720, hours))
        
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                
                # Get time range
                now = datetime.utcnow()
                cutoff = now - timedelta(hours=hours)
                
                # Get limit for percentage calculation
                cursor.execute(
                    "SELECT limit_value FROM api_rate_limits WHERE provider_name = ?",
                    (provider_name,)
                )
                row = cursor.fetchone()
                limit_value = row[0] if row else 100
                
                # Build aggregation query
                if interval == 'daily':
                    time_format = "DATE(created_at)"
                else:  # hourly
                    time_format = "DATE(created_at) || ' ' || CAST(CAST(strftime('%H', created_at) AS INTEGER) AS TEXT) || ':00'"
                
                cursor.execute(
                    f"""
                    SELECT
                        {time_format} as period,
                        COUNT(*) as call_count,
                        SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as error_count
                    FROM api_usage_logs
                    WHERE provider_name = ? AND created_at > ?
                    GROUP BY period
                    ORDER BY period ASC
                    """,
                    (provider_name, cutoff.isoformat())
                )
                
                history = []
                for row in cursor.fetchall():
                    period, call_count, error_count = row
                    error_count = error_count or 0
                    
                    # Calculate usage percentage
                    usage_pct = (call_count / limit_value * 100) if limit_value > 0 else 0.0
                    
                    history.append({
                        'timestamp': f"{period}:00Z" if interval == 'hourly' else f"{period}T00:00:00Z",
                        'usage_pct': round(usage_pct, 1),
                        'call_count': call_count,
                        'errors': error_count
                    })
                
                return history
        except Exception as e:
            logger.error(f"Failed to get usage history for {provider_name}: {e}", exc_info=True)
            return []

    @staticmethod
    def update_provider_limit(
        provider_name: str,
        limit_value: int,
        alert_threshold: Optional[int] = None
    ) -> bool:
        """
        Update rate limit for a provider.
        
        Parameters
        ----------
        provider_name : str
            Name of the provider
        limit_value : int
            New limit value
        alert_threshold : int, optional
            New alert threshold percentage
        
        Returns
        -------
        bool
            True if update successful
        """
        try:
            RateLimitManager.ensure_provider_exists(provider_name)
            
            with db_session() as conn:
                cursor = conn.cursor()
                
                if alert_threshold is not None:
                    cursor.execute(
                        """
                        UPDATE api_rate_limits
                        SET limit_value = ?, alert_threshold = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE provider_name = ?
                        """,
                        (limit_value, alert_threshold, provider_name)
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE api_rate_limits
                        SET limit_value = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE provider_name = ?
                        """,
                        (limit_value, provider_name)
                    )
                
                conn.commit()
                logger.info(f"Updated rate limit for {provider_name}: limit={limit_value}")
                return True
        except Exception as e:
            logger.error(f"Failed to update provider limit for {provider_name}: {e}", exc_info=True)
            return False