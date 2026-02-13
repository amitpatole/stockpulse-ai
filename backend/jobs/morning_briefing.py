"""
Pre-market morning briefing job.

Schedule: 8:30 AM ET, Mon-Fri
Agents: Scanner + Regime
Output: Pre-market summary with overnight moves, pre-market movers, regime assessment
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

JOB_ID = 'morning_briefing'
JOB_NAME = 'Morning Briefing'


def run_morning_briefing():
    """Generate a pre-market morning briefing.

    Steps:
        1. Load the active watchlist from the database.
        2. Run the Scanner agent to scan all stocks for overnight moves and
           pre-market movers.
        3. Run the Regime agent for an overall market health assessment.
        4. Combine the results into a structured morning briefing.
        5. Persist to the ``job_history`` table.
        6. Send an SSE event so the UI can display the briefing immediately.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        registry = _get_agent_registry()
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist]

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No stocks in watchlist -- skipping morning briefing.'
            return

        briefing_parts = []
        total_cost = 0.0

        # ---- 1. Run Scanner agent ----
        ctx['agent_name'] = 'scanner'
        scanner_result = registry.run_agent('scanner', {
            'tickers': tickers,
            'mode': 'pre_market',
            'task': 'morning_scan',
        })

        if scanner_result and scanner_result.status == 'success':
            briefing_parts.append(f"## Scanner Report\n{scanner_result.output}")
            total_cost += scanner_result.estimated_cost
        elif scanner_result:
            briefing_parts.append(
                f"## Scanner Report\nScanner agent returned error: {scanner_result.error}"
            )
        else:
            briefing_parts.append(
                "## Scanner Report\nScanner agent not available."
            )

        # ---- 2. Run Regime agent ----
        regime_result = registry.run_agent('regime', {
            'task': 'market_health',
            'scope': 'pre_market',
        })

        if regime_result and regime_result.status == 'success':
            briefing_parts.append(f"## Regime Assessment\n{regime_result.output}")
            total_cost += regime_result.estimated_cost
        elif regime_result:
            briefing_parts.append(
                f"## Regime Assessment\nRegime agent returned error: {regime_result.error}"
            )
        else:
            briefing_parts.append(
                "## Regime Assessment\nRegime agent not available."
            )

        # ---- 3. Assemble briefing ----
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        briefing = (
            f"# Morning Briefing - {now_str}\n"
            f"Watchlist: {len(tickers)} stocks\n\n"
            + '\n\n'.join(briefing_parts)
        )

        ctx['cost'] = total_cost
        ctx['result_summary'] = (
            f"Morning briefing generated for {len(tickers)} stocks. "
            f"Scanner={'OK' if scanner_result and scanner_result.status == 'success' else 'FAIL'}, "
            f"Regime={'OK' if regime_result and regime_result.status == 'success' else 'FAIL'}."
        )

        # ---- 4. Push detailed briefing via SSE ----
        _send_sse('morning_briefing', {
            'briefing': briefing,
            'stock_count': len(tickers),
            'generated_at': now_str,
        })
