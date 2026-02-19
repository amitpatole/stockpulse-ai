"""
TickerPulse AI v3.0 - Multi-Agent System
Exports all agents, engines, and the factory function for creating
and registering the default agent set.
"""

import logging
import threading
from typing import Optional

from backend.agents.base import (
    AgentConfig,
    AgentFramework,
    AgentRegistry,
    AgentResult,
    AgentStatus,
    BaseAgent,
)

from backend.agents.scanner_agent import ScannerAgent, SCANNER_CONFIG
from backend.agents.researcher_agent import ResearcherAgent, RESEARCHER_CONFIG
from backend.agents.regime_agent import RegimeAgent, REGIME_CONFIG
from backend.agents.investigator_agent import InvestigatorAgent, INVESTIGATOR_CONFIG
from backend.agents.download_tracker_agent import DownloadTrackerAgent, DOWNLOAD_TRACKER_CONFIG

from backend.agents.crewai_engine import TickerPulseCrewEngine
from backend.agents.openclaw_engine import OpenClawBridge

from backend.agents.tools import (
    StockDataFetcher,
    NewsFetcher,
    TechnicalAnalyzer,
    RedditScanner,
)

logger = logging.getLogger(__name__)

__all__ = [
    # Registry singleton
    "get_registry",
    # Base
    "AgentConfig",
    "AgentFramework",
    "AgentRegistry",
    "AgentResult",
    "AgentStatus",
    "BaseAgent",
    # Agents
    "ScannerAgent",
    "ResearcherAgent",
    "RegimeAgent",
    "InvestigatorAgent",
    "DownloadTrackerAgent",
    # Agent default configs
    "SCANNER_CONFIG",
    "RESEARCHER_CONFIG",
    "REGIME_CONFIG",
    "INVESTIGATOR_CONFIG",
    "DOWNLOAD_TRACKER_CONFIG",
    # Engines
    "TickerPulseCrewEngine",
    "OpenClawBridge",
    # Tools
    "StockDataFetcher",
    "NewsFetcher",
    "TechnicalAnalyzer",
    "RedditScanner",
    # Factory
    "create_default_agents",
]


# ---------------------------------------------------------------------------
# Module-level registry singleton
# ---------------------------------------------------------------------------

_registry: Optional[AgentRegistry] = None
_registry_lock = threading.Lock()


def get_registry(db_path: str = None) -> AgentRegistry:
    """Return the module-level :class:`AgentRegistry` singleton.

    On first call, creates and registers all default agents.  Subsequent
    calls return the same instance regardless of *db_path* so the API and
    scheduled jobs share a single registry.
    """
    global _registry
    if _registry is not None:
        return _registry
    with _registry_lock:
        if _registry is None:
            try:
                from backend.config import Config
                path = db_path or Config.DB_PATH
            except ImportError:
                path = db_path or "stock_news.db"
            _registry = create_default_agents(path)
    return _registry


def create_default_agents(db_path: str = "stock_news.db") -> AgentRegistry:
    """Create and register all four default TickerPulse agents.

    Returns an :class:`AgentRegistry` with the following agents registered:

    - **scanner** -- Stock Scanner (Haiku 4.5) -- fast technical scanning
    - **researcher** -- Research Analyst (Sonnet 4.5) -- deep research briefs
    - **regime** -- Market Regime Analyst (Sonnet 4.5) -- macro regime classification
    - **investigator** -- Social Media Investigator (Haiku 4.5) -- Reddit/social scanning

    The registry persists run history to *db_path* (default: ``stock_news.db``).
    """
    registry = AgentRegistry(db_path=db_path)

    # --- Scanner Agent (Haiku 4.5 -- cheap, fast scanning) ---
    scanner = ScannerAgent()
    registry.register(scanner)

    # --- Researcher Agent (Sonnet 4.5 -- deep reasoning) ---
    researcher = ResearcherAgent()
    registry.register(researcher)

    # --- Market Regime Agent (Sonnet 4.5 -- macro analysis) ---
    regime = RegimeAgent()
    registry.register(regime)

    # --- Investigator Agent (Haiku 4.5 -- Reddit/social scanning) ---
    investigator = InvestigatorAgent()
    registry.register(investigator)

    # --- Download Tracker Agent (Haiku 4.5 -- GitHub analytics) ---
    download_tracker = DownloadTrackerAgent()
    registry.register(download_tracker)

    logger.info(
        f"Registered {len(registry.list_agents())} default agents: "
        f"{', '.join(a['name'] for a in registry.list_agents())}"
    )

    return registry
