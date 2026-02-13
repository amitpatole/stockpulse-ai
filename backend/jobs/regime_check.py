"""
Market regime pulse check.

Schedule: Every 2 hours during market hours
Agent: Regime
Output: Quick market health assessment
"""
import json
import logging
from datetime import datetime

from backend.config import Config
from backend.jobs._helpers import (
    _get_agent_registry,
    _send_sse,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'regime_check'
JOB_NAME = 'Regime Check'


def run_regime_check():
    """Perform a quick market-regime pulse check.

    Steps:
        1. Verify the US market is open -- skip if not.
        2. Run the Regime agent for a quick health assessment.
        3. Parse the regime classification (bull/bear/neutral/volatile).
        4. Send SSE event with the regime status.
        5. Persist to job_history.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        # ---- 1. Market-hours gate ----
        from backend.scheduler import scheduler_manager
        if not scheduler_manager.is_market_hours('US'):
            ctx['status'] = 'skipped'
            ctx['result_summary'] = 'US market is closed -- skipping regime check.'
            logger.info("Regime check skipped: market closed.")
            return

        registry = _get_agent_registry()

        # ---- 2. Run Regime agent ----
        ctx['agent_name'] = 'regime'
        regime_result = registry.run_agent('regime', {
            'task': 'pulse_check',
            'scope': 'intraday',
        })

        if not regime_result:
            ctx['status'] = 'error'
            ctx['result_summary'] = 'Regime agent not available.'
            return

        if regime_result.status != 'success':
            ctx['status'] = 'error'
            ctx['result_summary'] = f'Regime agent error: {regime_result.error}'
            return

        ctx['cost'] = regime_result.estimated_cost

        # ---- 3. Parse regime classification ----
        regime_label = _classify_regime(regime_result.output)

        # ---- 4. Push SSE event ----
        _send_sse('regime_update', {
            'regime': regime_label,
            'detail': regime_result.output[:500],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        })

        ctx['result_summary'] = f"Regime pulse: {regime_label}."


def _classify_regime(output: str) -> str:
    """Extract a simple regime label from the agent's output.

    Tries JSON first, then keyword detection.  Falls back to ``'unknown'``.
    """
    # Try JSON
    try:
        data = json.loads(output)
        if isinstance(data, dict):
            for key in ('regime', 'classification', 'label', 'status'):
                if key in data:
                    return str(data[key]).lower()
    except (json.JSONDecodeError, TypeError):
        pass

    # Keyword scan
    output_lower = output.lower()
    for label in ('bullish', 'bull', 'bearish', 'bear', 'volatile',
                  'neutral', 'risk-off', 'risk-on', 'correction',
                  'recovery'):
        if label in output_lower:
            return label

    return 'unknown'
