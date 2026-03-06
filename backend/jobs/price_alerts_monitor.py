"""
Price alerts monitoring job.

Schedule: Every 30 minutes during US market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
Task: Monitor stock prices and trigger alerts when thresholds are hit
Output: Create alert records and notify via SSE
"""
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any

from backend.config import Config
from backend.jobs._helpers import (
    _get_watchlist,
    _send_sse,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'price_alerts_monitor'
JOB_NAME = 'Price Alerts Monitor'


def run_price_alerts_monitor() -> None:
    """Monitor stock prices and trigger alerts when thresholds are hit.

    Steps:
        1. Check if US market is currently open.
        2. Load active stocks from watchlist.
        3. Fetch current prices for each stock.
        4. Check against configured price alert thresholds.
        5. Create alert records for triggered thresholds.
        6. Send SSE notifications for UI updates.
        7. Log summary of alerts generated.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        # ---- 1. Market-hours gate ----
        from backend.scheduler import scheduler_manager
        if not scheduler_manager.is_market_hours('US'):
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'US market is closed -- skipping price alerts.'
            logger.debug("Price alerts monitor skipped: market closed.")
            return

        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist if s.get('market', 'US') == 'US']

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No US stocks in watchlist.'
            return

        # ---- 2. Fetch current prices and check thresholds ----
        alerts_generated = 0
        alerts_list: List[Dict[str, Any]] = []

        for ticker in tickers:
            try:
                current_price = _fetch_current_price(ticker)
                if current_price is None:
                    logger.warning(f"Failed to fetch price for {ticker}")
                    continue

                # ---- 3. Check price alert thresholds ----
                triggered_alerts = _check_price_thresholds(ticker, current_price)

                if triggered_alerts:
                    # ---- 4. Create alert records ----
                    for alert_type, threshold, detail in triggered_alerts:
                        success = _create_alert(
                            ticker=ticker,
                            alert_type=alert_type,
                            message=detail,
                            current_price=current_price,
                            threshold=threshold,
                        )
                        if success:
                            alerts_generated += 1
                            alerts_list.append({
                                'ticker': ticker,
                                'type': alert_type,
                                'current_price': current_price,
                                'threshold': threshold,
                                'detail': detail,
                            })

            except Exception as exc:
                logger.error(f"Error processing price alerts for {ticker}: {exc}")

        # ---- 5. Send SSE notifications ----
        if alerts_list:
            _send_sse('price_alerts', {
                'alerts': alerts_list,
                'count': len(alerts_list),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            })

        ctx['result_summary'] = (
            f"Monitored {len(tickers)} stocks. "
            f"Generated {alerts_generated} alert(s)."
        )
        logger.info(
            "[PRICE ALERTS] Monitored=%d, Alerts=%d",
            len(tickers), alerts_generated,
        )


def _fetch_current_price(ticker: str) -> Optional[float]:
    """Fetch the current price for a ticker.

    This is a stub that returns None for demonstration.
    In production, this would call a market data provider (Alpha Vantage,
    IB, Polygon, etc.).

    Parameters
    ----------
    ticker : str
        Stock ticker symbol

    Returns
    -------
    float or None
        Current stock price, or None if fetch failed
    """
    try:
        # TODO: Replace with actual market data API call
        # Stub: return None (production code would call real API)
        return None
    except Exception as exc:
        logger.error(f"Failed to fetch price for {ticker}: {exc}")
        return None


def _check_price_thresholds(
    ticker: str,
    current_price: float,
) -> List[tuple]:
    """Check if current price hits any configured thresholds.

    Parameters
    ----------
    ticker : str
        Stock ticker
    current_price : float
        Current stock price

    Returns
    -------
    list of tuple
        List of (alert_type, threshold, detail) tuples for triggered alerts
    """
    triggered = []

    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        # Fetch price alert configuration (stub table)
        # In production, would query actual alert config table
        # For now, we use hardcoded thresholds or a stub

        # Example: Check for 5% moves from previous close
        ai_rating = conn.execute(
            "SELECT current_price FROM ai_ratings WHERE ticker = ?",
            (ticker,),
        ).fetchone()

        conn.close()

        if ai_rating:
            previous_price = ai_rating['current_price']
            if previous_price and previous_price > 0:
                pct_change = ((current_price - previous_price) / previous_price) * 100

                if pct_change >= 5.0:
                    triggered.append((
                        'price_up_5pct',
                        previous_price * 1.05,
                        f"{ticker} up {pct_change:.1f}% from {previous_price:.2f}",
                    ))

                if pct_change <= -5.0:
                    triggered.append((
                        'price_down_5pct',
                        previous_price * 0.95,
                        f"{ticker} down {abs(pct_change):.1f}% from {previous_price:.2f}",
                    ))

    except Exception as exc:
        logger.error(f"Failed to check thresholds for {ticker}: {exc}")

    return triggered


def _create_alert(
    ticker: str,
    alert_type: str,
    message: str,
    current_price: float,
    threshold: float,
) -> bool:
    """Create an alert record in the database.

    Parameters
    ----------
    ticker : str
        Stock ticker
    alert_type : str
        Type of alert (price_up_5pct, price_down_5pct, etc.)
    message : str
        Human-readable alert message
    current_price : float
        Current stock price
    threshold : float
        The threshold value that triggered the alert

    Returns
    -------
    bool
        True if alert was created, False otherwise
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)

        # Insert into alerts table
        conn.execute(
            """INSERT INTO alerts
               (ticker, alert_type, message)
               VALUES (?, ?, ?)""",
            (ticker, alert_type, message),
        )

        conn.commit()
        conn.close()
        logger.info(f"Alert created: {ticker} {alert_type} at {current_price}")
        return True

    except Exception as exc:
        logger.error(f"Failed to create alert for {ticker}: {exc}")
        return False
