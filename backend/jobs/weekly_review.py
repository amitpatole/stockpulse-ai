"""
Weekly portfolio review.

Schedule: Sunday 8:00 PM ET
Agents: All agents
Output: Weekly performance summary, sector analysis
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
)

logger = logging.getLogger(__name__)

JOB_ID = 'weekly_review'
JOB_NAME = 'Weekly Review'


def run_weekly_review():
    """Generate a comprehensive weekly portfolio review.

    Steps:
        1. Load the watchlist.
        2. Run Scanner agent for weekly performance data (5-day returns, highs/
           lows, volume trends).
        3. Run Regime agent for weekly regime summary and trend direction.
        4. Run Investigator agent for weekly social/news sentiment overview.
        5. Aggregate the past week's job history and cost data.
        6. Assemble a structured weekly digest.
        7. Persist and push via SSE.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        registry = _get_agent_registry()
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist]

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No stocks in watchlist -- skipping weekly review.'
            return

        review_parts = []
        total_cost = 0.0
        agent_statuses = {}

        # ---- 1. Scanner: Weekly performance ----
        ctx['agent_name'] = 'scanner'
        scanner_result = registry.run_agent('scanner', {
            'tickers': tickers,
            'mode': 'weekly',
            'task': 'weekly_performance',
            'lookback_days': 7,
        })
        if scanner_result and scanner_result.status == 'success':
            review_parts.append(f"## Weekly Performance\n{scanner_result.output}")
            total_cost += scanner_result.estimated_cost
            agent_statuses['scanner'] = 'OK'
        else:
            error_msg = scanner_result.error if scanner_result else 'Agent not available'
            review_parts.append(f"## Weekly Performance\nUnavailable: {error_msg}")
            agent_statuses['scanner'] = 'FAIL'

        # ---- 2. Regime: Weekly trend ----
        regime_result = registry.run_agent('regime', {
            'task': 'weekly_regime',
            'scope': 'weekly',
        })
        if regime_result and regime_result.status == 'success':
            review_parts.append(f"## Market Regime (Weekly)\n{regime_result.output}")
            total_cost += regime_result.estimated_cost
            agent_statuses['regime'] = 'OK'
        else:
            error_msg = regime_result.error if regime_result else 'Agent not available'
            review_parts.append(f"## Market Regime (Weekly)\nUnavailable: {error_msg}")
            agent_statuses['regime'] = 'FAIL'

        # ---- 3. Investigator: Weekly sentiment ----
        investigator_result = registry.run_agent('investigator', {
            'tickers': tickers,
            'task': 'weekly_sentiment',
            'lookback_days': 7,
        })
        if investigator_result and investigator_result.status == 'success':
            review_parts.append(f"## Sentiment Overview (Weekly)\n{investigator_result.output}")
            total_cost += investigator_result.estimated_cost
            agent_statuses['investigator'] = 'OK'
        else:
            error_msg = investigator_result.error if investigator_result else 'Agent not available'
            review_parts.append(f"## Sentiment Overview (Weekly)\nUnavailable: {error_msg}")
            agent_statuses['investigator'] = 'FAIL'

        # ---- 4. Week's operations summary ----
        week_stats = _get_weekly_job_stats()
        review_parts.append(
            f"## Operations Summary (Past 7 Days)\n"
            f"Total job runs: {week_stats['total_runs']}\n"
            f"Successful: {week_stats['success']}\n"
            f"Errors: {week_stats['errors']}\n"
            f"Skipped: {week_stats['skipped']}\n"
            f"Total AI cost: ${week_stats['total_cost']:.4f}"
        )

        # ---- 5. Assemble review ----
        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
        review = (
            f"# Weekly Review - {now_str}\n"
            f"Watchlist: {len(tickers)} stocks\n\n"
            + '\n\n'.join(review_parts)
        )

        ctx['cost'] = total_cost
        status_str = ', '.join(f'{k}={v}' for k, v in agent_statuses.items())
        ctx['result_summary'] = (
            f"Weekly review for {len(tickers)} stocks. Agents: {status_str}."
        )

        # ---- 6. Push via SSE ----
        _send_sse('weekly_review', {
            'review': review,
            'stock_count': len(tickers),
            'agent_statuses': agent_statuses,
            'week_stats': week_stats,
            'generated_at': now_str,
        })


def _get_weekly_job_stats() -> dict:
    """Query job_history for the past 7 days of execution statistics."""
    cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
    stats = {'total_runs': 0, 'success': 0, 'errors': 0, 'skipped': 0, 'total_cost': 0.0}
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT status, cost FROM job_history WHERE executed_at >= ?",
            (cutoff,),
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
        logger.error("Failed to query weekly job stats: %s", exc)

    return stats
