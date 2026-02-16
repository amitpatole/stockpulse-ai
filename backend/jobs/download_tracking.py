"""
Download tracking job.

Schedule: Daily at 9:00 AM ET
Agent: Download Tracker
Output: Daily report on repository download statistics
"""
import logging
from datetime import datetime

from backend.config import Config
from backend.jobs._helpers import (
    _get_agent_registry,
    _send_sse,
    job_timer,
)

logger = logging.getLogger(__name__)

JOB_ID = 'download_tracking'
JOB_NAME = 'Download Tracking'


def run_download_tracking():
    """Track repository download statistics.

    Steps:
        1. Run the Download Tracker agent to fetch clone data from GitHub.
        2. Store the data in the database.
        3. Generate a report with download statistics.
        4. Persist to the ``job_history`` table.
        5. Send an SSE event so the UI can display the stats.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        registry = _get_agent_registry()

        # ---- Run Download Tracker agent ----
        ctx['agent_name'] = 'download_tracker'
        
        inputs = {
            'owner': 'amitpatole',
            'repo': 'stockpulse-ai',
        }
        
        # Include GitHub token if available (will be picked up from Config)
        if Config.GITHUB_TOKEN:
            inputs['github_token'] = Config.GITHUB_TOKEN
        
        result = registry.run_agent('download_tracker', inputs)

        if result and result.status == 'success':
            ctx['cost'] = result.estimated_cost
            ctx['result_summary'] = (
                f"Download tracking completed. "
                f"Total clones: {result.metadata.get('total_clones', 0)}, "
                f"Unique clones: {result.metadata.get('unique_clones', 0)}"
            )
            
            # ---- Push report via SSE ----
            _send_sse('download_tracking', {
                'report': result.output,
                'total_clones': result.metadata.get('total_clones', 0),
                'unique_clones': result.metadata.get('unique_clones', 0),
                'repository': result.metadata.get('repository', 'amitpatole/stockpulse-ai'),
                'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            })
        elif result:
            ctx['status'] = 'failed'
            ctx['result_summary'] = f"Download tracker error: {result.error or 'Unknown error'}"
        else:
            ctx['status'] = 'failed'
            ctx['result_summary'] = 'Download tracker agent not available.'
