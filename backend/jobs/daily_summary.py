"""
End-of-day summary.

Schedule: 4:30 PM ET, Mon-Fri
Agents: All agents
Output: Complete daily digest with performance, signals, sentiment
"""
import json
import logging
import sqlite3
from datetime import datetime, timedelta

from backend.config import Config
from backend.jobs._helpers import (
    _get_agent_registry,
    _get_watchlist,
    _send_sse,
    job_timer,
    get_job_history,
)

logger = logging.getLogger(__name__)

JOB_ID = 'daily_summary'
JOB_NAME = 'Daily Summary'


def run_daily_summary():
    """Generate a complete end-of-day summary.

    Steps:
        1. Load the watchlist.
        2. Run Scanner agent for closing snapshot (prices, volume, day change).
        3. Run Regime agent for end-of-day market health.
        4. Run Investigator agent for sentiment summary (social + news).
        5. Aggregate today's job history for an execution summary.
        6. Combine everything into a structured daily digest.
        7. Persist and push via SSE.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        registry = _get_agent_registry()
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist]

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No stocks in watchlist -- skipping daily summary.'
            return

        digest_parts = []
        total_cost = 0.0
        agent_statuses = {}

        # ---- 1. Scanner: Closing snapshot ----
        ctx['agent_name'] = 'scanner'
        scanner_result = registry.run_agent('scanner', {
            'tickers': tickers,
            'mode': 'end_of_day',
            'task': 'closing_snapshot',
        })
        if scanner_result and scanner_result.status == 'success':
            digest_parts.append(f"## Market Closing Snapshot\n{scanner_result.output}")
            total_cost += scanner_result.estimated_cost
            agent_statuses['scanner'] = 'OK'
        else:
            error_msg = scanner_result.error if scanner_result else 'Agent not available'
            digest_parts.append(f"## Market Closing Snapshot\nUnavailable: {error_msg}")
            agent_statuses['scanner'] = 'FAIL'

        # ---- 2. Regime: End-of-day health ----
        regime_result = registry.run_agent('regime', {
            'task': 'market_health',
            'scope': 'end_of_day',
        })
        if regime_result and regime_result.status == 'success':
            digest_parts.append(f"## Market Regime\n{regime_result.output}")
            total_cost += regime_result.estimated_cost
            agent_statuses['regime'] = 'OK'
        else:
            error_msg = regime_result.error if regime_result else 'Agent not available'
            digest_parts.append(f"## Market Regime\nUnavailable: {error_msg}")
            agent_statuses['regime'] = 'FAIL'

        # ---- 3. Investigator: Sentiment summary ----
        investigator_result = registry.run_agent('investigator', {
            'tickers': tickers,
            'task': 'daily_sentiment',
        })
        if investigator_result and investigator_result.status == 'success':
            digest_parts.append(f"## Sentiment Summary\n{investigator_result.output}")
            total_cost += investigator_result.estimated_cost
            agent_statuses['investigator'] = 'OK'
        else:
            error_msg = investigator_result.error if investigator_result else 'Agent not available'
            digest_parts.append(f"## Sentiment Summary\nUnavailable: {error_msg}")
            agent_statuses['investigator'] = 'FAIL'

        # ---- 4. Today's job execution summary ----
        today_jobs = _get_todays_job_stats()
        digest_parts.append(
            f"## Job Execution Summary\n"
            f"Total runs today: {today_jobs['total_runs']}\n"
            f"Successful: {today_jobs['success']}\n"
            f"Errors: {today_jobs['errors']}\n"
            f"Skipped: {today_jobs['skipped']}\n"
            f"Total cost: ${today_jobs['total_cost']:.4f}"
        )

        # ---- 5. Assemble digest ----
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        digest = (
            f"# Daily Summary - {now_str}\n"
            f"Watchlist: {len(tickers)} stocks\n\n"
            + '\n\n'.join(digest_parts)
        )

        ctx['cost'] = total_cost
        status_str = ', '.join(f'{k}={v}' for k, v in agent_statuses.items())
        ctx['result_summary'] = (
            f"Daily summary for {len(tickers)} stocks. Agents: {status_str}."
        )

        # ---- 6. Push via SSE ----
        _send_sse('daily_summary', {
            'digest': digest,
            'stock_count': len(tickers),
            'agent_statuses': agent_statuses,
            'generated_at': now_str,
        })


def _get_todays_job_stats() -> dict:
    """Query job_history for today's execution statistics."""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    stats = {'total_runs': 0, 'success': 0, 'errors': 0, 'skipped': 0, 'total_cost': 0.0}
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT status, cost FROM job_history WHERE DATE(executed_at) = ?",
            (today,),
        ).fetchall()
        conn.close()

        for row in rows:
            stats['total_runs'] += 1
            status = row['status']
            if status == 'success':
                stats['success'] += 1
            elif status == 'error':
                stats['errors'] += 1
            elif status == 'skipped':
                stats['skipped'] += 1
            stats['total_cost'] += row['cost'] or 0.0
    except Exception as exc:
        logger.error("Failed to query today's job stats: %s", exc)

    return stats
