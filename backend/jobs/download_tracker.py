"""
Daily download tracker job.

Schedule: 9:00 AM ET daily
Agent: Download Tracker
Output: Repository download statistics summary
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

JOB_ID = 'download_tracker'
JOB_NAME = 'Download Tracker'


def run_download_tracker():
    """Track GitHub repository download statistics.

    Steps:
        1. Run the Download Tracker agent to fetch clone statistics from GitHub API.
        2. Store the data in the database.
        3. Persist job results to the ``job_history`` table.
        4. Send an SSE event so the UI can display the update.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        registry = _get_agent_registry()

        # Run Download Tracker agent
        ctx['agent_name'] = 'download_tracker'
        result = registry.run_agent('download_tracker', {})

        if result and result.status == 'success':
            ctx['status'] = 'completed'
            ctx['cost'] = result.estimated_cost
            ctx['result_summary'] = result.output
            
            # Send SSE event
            _send_sse('download_tracker', {
                'summary': result.output,
                'metadata': result.metadata,
                'timestamp': datetime.utcnow().isoformat(),
            })
            
            logger.info(f"Download tracker completed: {result.output}")
            
        elif result:
            ctx['status'] = 'failed'
            ctx['result_summary'] = f"Download tracker failed: {result.error}"
            logger.error(f"Download tracker agent error: {result.error}")
        else:
            ctx['status'] = 'failed'
            ctx['result_summary'] = "Download tracker agent not available"
            logger.error("Download tracker agent not found in registry")
