"""
Reddit mention scanner.

Schedule: Every 60 minutes during market hours
Agent: Investigator
Output: Trending mentions, unusual activity flags
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

JOB_ID = 'reddit_scanner'
JOB_NAME = 'Reddit Scanner'

# Subreddits monitored for stock mentions
TARGET_SUBREDDITS = [
    'wallstreetbets',
    'stocks',
    'investing',
    'options',
    'stockmarket',
    'smallstreetbets',
]


def run_reddit_scan():
    """Scan Reddit for stock mentions and unusual activity.

    Steps:
        1. Check if the US market is currently open -- skip if not.
        2. Load the active watchlist to know which tickers to watch.
        3. Run the Investigator agent to scan Reddit posts/comments.
        4. Flag any unusual spikes in mention frequency.
        5. Persist results and send SSE events.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        # ---- 1. Market-hours gate ----
        from backend.scheduler import scheduler_manager
        if not scheduler_manager.is_market_hours('US'):
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'US market is closed -- skipping Reddit scan.'
            logger.info("Reddit scanner skipped: market closed.")
            return

        registry = _get_agent_registry()
        watchlist = _get_watchlist()
        tickers = [s['ticker'] for s in watchlist]

        if not tickers:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No stocks in watchlist.'
            return

        # ---- 2. Run Investigator agent ----
        ctx['agent_name'] = 'investigator'
        investigator_result = registry.run_agent('investigator', {
            'tickers': tickers,
            'task': 'reddit_scan',
            'subreddits': TARGET_SUBREDDITS,
            'lookback_hours': 1,
        })

        if not investigator_result:
            ctx['status'] = 'error'
            ctx['result_summary'] = 'Investigator agent not available.'
            return

        if investigator_result.status != 'success':
            ctx['status'] = 'error'
            ctx['result_summary'] = f'Investigator error: {investigator_result.error}'
            return

        ctx['cost'] = investigator_result.estimated_cost

        # ---- 3. Parse trending mentions ----
        trending = _parse_trending(investigator_result.output, tickers)

        # ---- 4. Send SSE notification ----
        if trending:
            _send_sse('reddit_trending', {
                'trending': trending,
                'subreddits': TARGET_SUBREDDITS,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
            })

        ctx['result_summary'] = (
            f"Scanned {len(TARGET_SUBREDDITS)} subreddits for {len(tickers)} tickers. "
            f"{len(trending)} trending mention(s) found."
        )


def _parse_trending(output: str, tickers: list) -> list:
    """Extract trending ticker mentions from investigator output.

    Returns a list of dicts with keys: ticker, mentions, sentiment, detail.
    """
    trending = []

    # Try JSON parse first
    try:
        data = json.loads(output)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict) and 'trending' in data:
            return data['trending']
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: look for ticker symbols in the text
    output_upper = output.upper()
    for ticker in tickers:
        ticker_upper = ticker.upper()
        # Count raw occurrences as a rough proxy for "trending"
        count = output_upper.count(ticker_upper)
        if count >= 2:
            trending.append({
                'ticker': ticker,
                'mentions': count,
                'sentiment': 'unknown',
                'detail': f'{ticker} mentioned {count} times in scan output.',
            })

    return trending
