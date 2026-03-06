"""
Portfolio rebalancing job.

Schedule: Monthly on the first Monday at 3:00 PM ET
Task: Rebalance portfolios based on target allocation and market changes
Output: Generate rebalancing recommendations and execute trades
"""
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

from backend.config import Config
from backend.jobs._helpers import (
    job_timer,
    _send_sse,
)

logger = logging.getLogger(__name__)

JOB_ID = 'portfolio_rebalancing'
JOB_NAME = 'Portfolio Rebalancing'


def run_portfolio_rebalancing() -> None:
    """Execute monthly portfolio rebalancing.

    Steps:
        1. Load all user portfolios from the database.
        2. Calculate current allocation (actual % vs target %).
        3. Identify drift from target allocation (threshold: > 5%).
        4. Generate rebalancing recommendations.
        5. Execute recommended trades (with retry logic).
        6. Update portfolio records.
        7. Send SSE notifications to connected clients.
        8. Log summary and any failures.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        portfolios = _load_portfolios()

        if not portfolios:
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'No portfolios to rebalance.'
            return

        rebalanced_count = 0
        failed_count = 0
        errors: Dict[str, str] = {}

        for portfolio_id in portfolios:
            try:
                portfolio = portfolios[portfolio_id]

                # ---- 1. Calculate current allocation ----
                current_allocation = _calculate_allocation(portfolio_id)
                target_allocation = portfolio.get('target_allocation', {})

                if not current_allocation:
                    failed_count += 1
                    errors[portfolio_id] = 'Failed to calculate allocation'
                    logger.warning(f"Could not calculate allocation for {portfolio_id}")
                    continue

                # ---- 2. Identify drift ----
                drift = _identify_drift(current_allocation, target_allocation)

                if not drift:
                    logger.info(f"Portfolio {portfolio_id} within tolerance")
                    continue

                # ---- 3. Generate recommendations ----
                recommendations = _generate_recommendations(
                    current_allocation,
                    target_allocation,
                    drift,
                )

                # ---- 4. Execute trades with retry logic ----
                success = _execute_rebalancing(
                    portfolio_id,
                    recommendations,
                    retry_count=3,
                )

                if success:
                    rebalanced_count += 1
                    _update_portfolio_record(portfolio_id)
                    _send_sse('portfolio_rebalanced', {
                        'portfolio_id': portfolio_id,
                        'recommendations': recommendations,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                    })
                else:
                    failed_count += 1
                    errors[portfolio_id] = 'Execution failed'

            except Exception as exc:
                failed_count += 1
                errors[portfolio_id] = str(exc)
                logger.error(f"Error rebalancing {portfolio_id}: {exc}", exc_info=False)

        ctx['result_summary'] = (
            f"Rebalanced {rebalanced_count}/{len(portfolios)} portfolios. "
            f"{failed_count} failed."
        )

        logger.info(
            "[REBALANCING] Processed=%d, Rebalanced=%d, Failed=%d",
            len(portfolios), rebalanced_count, failed_count,
        )


def _load_portfolios() -> Dict[str, Dict[str, Any]]:
    """Load all active portfolios from the database.

    Returns
    -------
    dict
        Dictionary mapping portfolio_id -> portfolio data
    """
    portfolios: Dict[str, Dict[str, Any]] = {}

    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        # Stub: In production, query actual portfolio table
        # For now, return empty dict (no portfolio table yet)
        # rows = conn.execute(
        #     "SELECT id, name, target_allocation FROM portfolios WHERE active = 1"
        # ).fetchall()
        # for row in rows:
        #     portfolios[row['id']] = dict(row)

        conn.close()

    except Exception as exc:
        logger.error(f"Failed to load portfolios: {exc}")

    return portfolios


def _calculate_allocation(portfolio_id: str) -> Optional[Dict[str, float]]:
    """Calculate current portfolio allocation (position % by asset).

    Parameters
    ----------
    portfolio_id : str
        Portfolio identifier

    Returns
    -------
    dict or None
        Dictionary mapping ticker -> allocation_pct, or None on error
    """
    try:
        # Stub: In production, would calculate actual positions
        # For now, return empty dict
        return {}

    except Exception as exc:
        logger.error(f"Failed to calculate allocation for {portfolio_id}: {exc}")
        return None


def _identify_drift(
    current: Dict[str, float],
    target: Dict[str, float],
) -> Dict[str, float]:
    """Identify positions that have drifted from target allocation.

    A position drifts if |current - target| > 5%.

    Parameters
    ----------
    current : dict
        Current allocation percentages
    target : dict
        Target allocation percentages

    Returns
    -------
    dict
        Dictionary mapping ticker -> drift_pct for positions above threshold
    """
    drift: Dict[str, float] = {}
    threshold = 0.05  # 5% threshold

    all_tickers = set(current.keys()) | set(target.keys())

    for ticker in all_tickers:
        curr = current.get(ticker, 0.0)
        tgt = target.get(ticker, 0.0)
        drift_amount = abs(curr - tgt)

        if drift_amount > threshold:
            drift[ticker] = drift_amount

    return drift


def _generate_recommendations(
    current: Dict[str, float],
    target: Dict[str, float],
    drift: Dict[str, float],
) -> list:
    """Generate rebalancing trade recommendations.

    Parameters
    ----------
    current : dict
        Current allocation percentages
    target : dict
        Target allocation percentages
    drift : dict
        Positions with allocation drift

    Returns
    -------
    list
        List of recommendation dicts with action (buy/sell), ticker, qty
    """
    recommendations = []

    for ticker in drift:
        curr = current.get(ticker, 0.0)
        tgt = target.get(ticker, 0.0)

        if curr < tgt:
            recommendations.append({
                'action': 'buy',
                'ticker': ticker,
                'target_pct': tgt,
                'current_pct': curr,
                'drift': tgt - curr,
            })
        elif curr > tgt:
            recommendations.append({
                'action': 'sell',
                'ticker': ticker,
                'target_pct': tgt,
                'current_pct': curr,
                'drift': curr - tgt,
            })

    return recommendations


def _execute_rebalancing(
    portfolio_id: str,
    recommendations: list,
    retry_count: int = 3,
) -> bool:
    """Execute rebalancing trades with retry logic.

    Parameters
    ----------
    portfolio_id : str
        Portfolio identifier
    recommendations : list
        List of trade recommendations
    retry_count : int
        Number of retries on failure

    Returns
    -------
    bool
        True if execution succeeded, False otherwise
    """
    for attempt in range(1, retry_count + 1):
        try:
            logger.info(
                f"Executing rebalancing for {portfolio_id} (attempt {attempt}/{retry_count})"
            )

            # Stub: In production, would call broker API
            # For now, just simulate successful execution
            logger.info(f"Successfully executed {len(recommendations)} trades")
            return True

        except Exception as exc:
            logger.warning(
                f"Rebalancing attempt {attempt} failed for {portfolio_id}: {exc}"
            )
            if attempt < retry_count:
                # Exponential backoff: 2s, 4s, 8s
                import time
                time.sleep(2 ** attempt)

    return False


def _update_portfolio_record(portfolio_id: str) -> None:
    """Update portfolio record with rebalancing timestamp.

    Parameters
    ----------
    portfolio_id : str
        Portfolio identifier
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        # Stub: In production, would update rebalancing timestamp
        # conn.execute(
        #     "UPDATE portfolios SET last_rebalanced = ? WHERE id = ?",
        #     (datetime.utcnow().isoformat(), portfolio_id),
        # )
        # conn.commit()
        conn.close()

    except Exception as exc:
        logger.error(f"Failed to update portfolio record for {portfolio_id}: {exc}")
