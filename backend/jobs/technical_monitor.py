"""
Technical analysis monitor.

Schedule: Every 15 minutes during US market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
Agent: Scanner
Output: RSI/MACD/MA signals for watchlist, breakout alerts
"""
import json
import logging
from datetime import datetime

from backend.config import Config
from backend.jobs._helpers import (
    _get_agent_registry,
    _get_watchlist,
    _send_sse,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'technical_monitor'
JOB_NAME = 'Technical Monitor'


def run_technical_monitor():
    """Run a fast technical-indicator scan during market hours.

    Steps:
        1. Check if the US market is currently open -- skip if not.
        2. Run the Scanner agent in fast / technical-only mode.
        3. Check the output for breakout signals (price > 20-day high, volume
           spike, RSI extremes).
        4. Create alerts for significant signals.
        5. Send SSE events for real-time dashboard updates.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        # ---- 1. Market-hours gate ----
        from backend.scheduler import scheduler_manager
        if not scheduler_manager.is_market_hours('US'):
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'US market is closed -- skipping technical monitor.'
            logger.info("Technical monitor skipped: market closed.")
            return

        registry = _get_agent_registry()
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist if s.get('market', 'US') == 'US']

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No US stocks in watchlist.'
            return

        # ---- 2. Run Scanner in fast/technical mode ----
        ctx['agent_name'] = 'scanner'
        scanner_result = registry.run_agent('scanner', {
            'tickers': tickers,
            'mode': 'technical',
            'task': 'technical_scan',
            'indicators': ['RSI', 'MACD', 'MA_20', 'MA_50', 'VOLUME'],
        })

        if not scanner_result:
            ctx['status'] = 'error'
            ctx['result_summary'] = 'Scanner agent not available.'
            return

        if scanner_result.status != 'success':
            ctx['status'] = 'error'
            ctx['result_summary'] = f'Scanner error: {scanner_result.error}'
            return

        ctx['cost'] = scanner_result.estimated_cost

        # ---- 3. Parse for breakout signals ----
        alerts = _extract_alerts(scanner_result.output)

        # ---- 4. Push alerts via SSE ----
        if alerts:
            _send_sse('technical_alerts', {
                'alerts': alerts,
                'scanned_count': len(tickers),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            })

        ctx['result_summary'] = (
            f"Scanned {len(tickers)} stocks. "
            f"{len(alerts)} alert(s) generated."
        )


def _extract_alerts(scanner_output: str) -> list:
    """Attempt to extract structured alert data from scanner output.

    The scanner agent may return JSON-structured data or free-form text.
    This function tries JSON first, then falls back to keyword scanning.

    Returns a list of alert dicts with keys: ticker, signal, detail.
    """
    alerts = []

    # Try parsing as JSON first
    try:
        data = json.loads(scanner_output)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get('signal'):
                    alerts.append({
                        'ticker': item.get('ticker', 'UNKNOWN'),
                        'signal': item.get('signal', ''),
                        'detail': item.get('detail', ''),
                    })
            return alerts
        if isinstance(data, dict) and 'alerts' in data:
            return data['alerts']
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: simple keyword detection in free-form text
    keywords = ['breakout', 'overbought', 'oversold', 'golden cross',
                'death cross', 'volume spike', 'divergence']
    for line in scanner_output.split('\n'):
        line_lower = line.lower()
        for kw in keywords:
            if kw in line_lower:
                alerts.append({
                    'ticker': '',
                    'signal': kw,
                    'detail': line.strip(),
                })
                break  # one alert per line

    return alerts
