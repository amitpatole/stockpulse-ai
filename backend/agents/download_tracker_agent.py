"""
StockPulse AI v3.0 - Download Tracker Agent
Monitors repository downloads (clones) from GitHub and tracks statistics.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional
import requests

from backend.agents.base import AgentConfig, AgentResult, BaseAgent
from backend.config import Config
from backend.database import db_session

logger = logging.getLogger(__name__)

# Default config
DOWNLOAD_TRACKER_CONFIG = AgentConfig(
    name="download_tracker",
    role="Download Tracker",
    goal=(
        "Monitor GitHub repository clone statistics and track unique downloads "
        "over time. Provide insights into repository popularity and usage patterns."
    ),
    backstory=(
        "You are a repository analytics agent that monitors GitHub traffic data. "
        "You track clone counts (downloads) and provide reports on repository "
        "growth and adoption metrics."
    ),
    model="claude-haiku-4-5-20251001",
    provider="anthropic",
    max_tokens=2048,
    temperature=0.3,
    tags=["analytics", "github", "downloads"],
)


class DownloadTrackerAgent(BaseAgent):
    """Download Tracker Agent - monitors GitHub repository clone statistics."""

    def __init__(self, config: Optional[AgentConfig] = None):
        super().__init__(config or DOWNLOAD_TRACKER_CONFIG)
        # Use token from Config if available
        self.github_token = Config.GITHUB_TOKEN or None

    def _fetch_github_clones(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Fetch clone statistics from GitHub API.
        
        Parameters
        ----------
        owner : str
            Repository owner (username or organization)
        repo : str
            Repository name
            
        Returns
        -------
        dict or None
            Clone statistics data or None if error
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/traffic/clones"
        headers = {
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
        
        # Add token if available (increases rate limit)
        if self.github_token:
            headers['Authorization'] = f'Bearer {self.github_token}'
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            # GitHub returns 403 if user doesn't have access to traffic data
            if response.status_code == 403:
                logger.warning(
                    f"Access denied to traffic data for {owner}/{repo}. "
                    "This data is only available to repository owners/admins."
                )
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching GitHub clones for {owner}/{repo}: {e}")
            return None

    def _store_clone_data(self, owner: str, repo: str, data: Dict[str, Any]) -> None:
        """Store clone statistics in the database.
        
        Parameters
        ----------
        owner : str
            Repository owner
        repo : str
            Repository name
        data : dict
            Clone statistics from GitHub API
        """
        with db_session() as conn:
            cursor = conn.cursor()
            
            # Store summary data
            cursor.execute(
                """
                INSERT INTO download_stats (
                    repository, total_clones, unique_clones, 
                    recorded_at, data_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"{owner}/{repo}",
                    data.get('count', 0),
                    data.get('uniques', 0),
                    datetime.utcnow().isoformat(),
                    json.dumps(data)
                )
            )
            
            # Store daily breakdown if available
            for clone_day in data.get('clones', []):
                cursor.execute(
                    """
                    INSERT INTO download_stats_daily (
                        repository, date, clones, unique_clones, recorded_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        f"{owner}/{repo}",
                        clone_day.get('timestamp', ''),
                        clone_day.get('count', 0),
                        clone_day.get('uniques', 0),
                        datetime.utcnow().isoformat()
                    )
                )

    def _generate_report(self, owner: str, repo: str, data: Dict[str, Any]) -> str:
        """Generate a human-readable report from clone statistics.
        
        Parameters
        ----------
        owner : str
            Repository owner
        repo : str
            Repository name
        data : dict
            Clone statistics from GitHub API
            
        Returns
        -------
        str
            Formatted report
        """
        report_lines = [
            f"# Download Statistics Report for {owner}/{repo}",
            f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Summary (Last 14 Days)",
            f"- Total Clones: {data.get('count', 0)}",
            f"- Unique Clones: {data.get('uniques', 0)}",
            "",
        ]
        
        # Add daily breakdown
        clones = data.get('clones', [])
        if clones:
            report_lines.append("## Daily Breakdown")
            for clone_day in clones:
                timestamp = clone_day.get('timestamp', 'Unknown')
                count = clone_day.get('count', 0)
                uniques = clone_day.get('uniques', 0)
                report_lines.append(
                    f"- {timestamp[:10]}: {count} clones ({uniques} unique)"
                )
            report_lines.append("")
        
        # Add insights
        if clones:
            avg_daily = data.get('count', 0) / len(clones) if clones else 0
            report_lines.append("## Insights")
            report_lines.append(f"- Average daily clones: {avg_daily:.1f}")
            report_lines.append(
                f"- Unique clone ratio: {data.get('uniques', 0) / max(data.get('count', 1), 1) * 100:.1f}%"
            )
        
        return "\n".join(report_lines)

    def execute(self, inputs: Dict[str, Any] = None) -> AgentResult:
        """Execute the download tracker agent.
        
        inputs (optional):
            owner: str -- GitHub repository owner (default: 'amitpatole')
            repo: str -- GitHub repository name (default: 'stockpulse-ai')
            github_token: str -- GitHub API token for authentication
        """
        inputs = inputs or {}
        owner = inputs.get('owner', 'amitpatole')
        repo = inputs.get('repo', 'stockpulse-ai')
        
        # Allow token override via inputs
        if 'github_token' in inputs:
            self.github_token = inputs['github_token']
        
        logger.info(f"Download tracker agent: fetching clone data for {owner}/{repo}")
        
        # Fetch clone data from GitHub
        clone_data = self._fetch_github_clones(owner, repo)
        
        if clone_data is None:
            return AgentResult(
                agent_name=self.name,
                framework="native",
                status="error",
                output=(
                    "Unable to fetch clone statistics. This data is only available "
                    "to repository owners/admins. Please ensure you have a GitHub token "
                    "with appropriate permissions."
                ),
                error="Access denied or API error",
                metadata={
                    'repository': f"{owner}/{repo}",
                    'access_required': 'admin or owner',
                }
            )
        
        # Store data in database
        try:
            self._store_clone_data(owner, repo, clone_data)
            logger.info(f"Stored clone data for {owner}/{repo}")
        except Exception as e:
            logger.error(f"Error storing clone data: {e}")
            return AgentResult(
                agent_name=self.name,
                framework="native",
                status="error",
                output=f"Failed to store clone data: {str(e)}",
                error=str(e),
                metadata={'repository': f"{owner}/{repo}"}
            )
        
        # Generate report
        report = self._generate_report(owner, repo, clone_data)
        
        return AgentResult(
            agent_name=self.name,
            framework="native",
            status="success",
            output=report,
            metadata={
                'repository': f"{owner}/{repo}",
                'total_clones': clone_data.get('count', 0),
                'unique_clones': clone_data.get('uniques', 0),
                'data_days': len(clone_data.get('clones', [])),
            }
        )
