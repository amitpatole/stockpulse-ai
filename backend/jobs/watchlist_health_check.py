"""
Watchlist health check job.

Schedule: 5:00 AM ET, daily
Task: Validate watchlist data integrity and flag problematic records
Output: Log issues, mark unhealthy stocks for review, send SSE notifications
"""
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

from backend.config import Config
from backend.jobs._helpers import (
    _get_watchlist,
    _send_sse,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'watchlist_health_check'
JOB_NAME = 'Watchlist Health Check'


def run_watchlist_health_check() -> None:
    """Validate watchlist data integrity and flag problematic records.

    Steps:
        1. Load active stocks from watchlist.
        2. For each stock, validate:
           - Ticker format (alphanumeric, 1-5 chars)
           - Market field (US or INDIA)
           - Price data exists and is recent (< 24 hours)
           - No null/invalid required fields
        3. Collect validation failures.
        4. Update stocks table with health status flags.
        5. Log comprehensive report.
        6. Notify UI via SSE of any problems.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        watchlist = _get_watchlist()

        if not watchlist:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'Watchlist is empty -- skipping health check.'
            return

        health_issues: Dict[str, List[str]] = {}  # ticker -> list of issues
        stale_count = 0
        invalid_count = 0
        healthy_count = 0

        for stock in watchlist:
            ticker = stock.get('ticker', '').upper()
            issues: List[str] = []

            # --- 1. Validate ticker format ---
            if not _is_valid_ticker(ticker):
                issues.append(f"Invalid ticker format: '{ticker}'")
                invalid_count += 1

            # --- 2. Validate market field ---
            market = stock.get('market', 'US').upper()
            if market not in ('US', 'INDIA'):
                issues.append(f"Invalid market: '{market}' (must be US or INDIA)")

            # --- 3. Check for stale price data ---
            last_price_age = _get_price_data_age(ticker)
            if last_price_age is None:
                issues.append("No price data found in database")
                stale_count += 1
            elif last_price_age > 86400:  # > 24 hours in seconds
                hours = last_price_age / 3600
                issues.append(f"Price data is {hours:.1f} hours old")
                stale_count += 1

            # --- 4. Check for missing critical fields ---
            if not stock.get('name'):
                issues.append("Missing company name")
                invalid_count += 1

            # Collect results
            if issues:
                health_issues[ticker] = issues
            else:
                healthy_count += 1

        # --- 5. Update stocks table with health status ---
        for ticker, issues in health_issues.items():
            _mark_stock_unhealthy(ticker, issues)

        # --- 6. Build report ---
        report_lines = [
            f"Healthy: {healthy_count}",
            f"Stale prices: {stale_count}",
            f"Invalid data: {invalid_count}",
        ]

        if health_issues:
            report_lines.append(f"\nProblems found ({len(health_issues)} stocks):")
            for ticker, issues in sorted(health_issues.items()):
                report_lines.append(f"  {ticker}: {'; '.join(issues)}")

        ctx['result_summary'] = '\n'.join(report_lines)

        # --- 7. Notify UI via SSE ---
        if health_issues:
            _send_sse('watchlist_health_alert', {
                'healthy_count': healthy_count,
                'stale_count': stale_count,
                'invalid_count': invalid_count,
                'problematic_tickers': list(health_issues.keys()),
                'checked_at': datetime.utcnow().isoformat() + 'Z',
            })

        logger.info(
            "[WATCHLIST_HEALTH] Healthy=%d, Stale=%d, Invalid=%d, Total=%d",
            healthy_count, stale_count, invalid_count, len(watchlist),
        )


def _is_valid_ticker(ticker: str) -> bool:
    """Check if ticker format is valid.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol

    Returns
    -------
    bool
        True if ticker is alphanumeric and 1-5 characters
    """
    if not ticker:
        return False
    # Allow alphanumeric and common symbols (-, .)
    return (
        len(ticker) >= 1 and len(ticker) <= 5 and
        all(c.isalnum() or c in '-.' for c in ticker)
    )


def _get_price_data_age(ticker: str) -> Optional[int]:
    """Get age of most recent price data for a ticker.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol

    Returns
    -------
    int or None
        Age of most recent price in seconds, or None if no data found
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        # Query ai_ratings for most recent price update
        row = conn.execute(
            """SELECT updated_at FROM ai_ratings
               WHERE ticker = ? AND updated_at IS NOT NULL
               ORDER BY updated_at DESC LIMIT 1""",
            (ticker.upper(),),
        ).fetchone()
        conn.close()

        if not row:
            return None

        updated_at = row['updated_at']
        if not updated_at:
            return None

        # Parse ISO format timestamp
        try:
            updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            age_seconds = int((datetime.utcnow() - updated_dt.replace(tzinfo=None)).total_seconds())
            return max(0, age_seconds)  # Clamp to >= 0
        except (ValueError, AttributeError):
            return None

    except Exception as exc:
        logger.warning(f"Failed to get price age for {ticker}: {exc}")
        return None


def _mark_stock_unhealthy(ticker: str, issues: List[str]) -> bool:
    """Mark a stock as unhealthy with issue details.

    Parameters
    ----------
    ticker : str
        Stock ticker symbol
    issues : list of str
        List of identified problems

    Returns
    -------
    bool
        True if update succeeded, False otherwise
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        issue_str = '; '.join(issues)

        # Store issues in ai_ratings as a note for manual review
        conn.execute(
            """UPDATE ai_ratings
               SET notes = ?, health_check_at = ?
               WHERE ticker = ?""",
            (issue_str, datetime.utcnow().isoformat(), ticker.upper()),
        )

        # Also mark in stocks table if health_status column exists
        try:
            conn.execute(
                """UPDATE stocks
                   SET health_status = ?, health_check_at = ?
                   WHERE ticker = ?""",
                ('unhealthy', datetime.utcnow().isoformat(), ticker.upper()),
            )
        except sqlite3.OperationalError:
            # Column may not exist yet; that's OK for backward compatibility
            pass

        conn.commit()
        conn.close()
        return True

    except Exception as exc:
        logger.error(f"Failed to mark {ticker} unhealthy: {exc}")
        return False
