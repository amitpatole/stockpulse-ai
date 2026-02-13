"""
StockPulse AI v3.0 - CrewAI Orchestration Engine
Maps AgentConfig objects to CrewAI Agent objects, builds Tasks and Crews,
and routes to the correct LLM using ai_providers.py settings.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.base import AgentConfig, AgentResult

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Graceful CrewAI import
# ------------------------------------------------------------------
try:
    from crewai import Agent as CrewAgent, Task as CrewTask, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    CrewAgent = None
    CrewTask = None
    Crew = None
    Process = None
    logger.info("CrewAI not installed -- StockPulseCrewEngine will operate in fallback mode")

# ------------------------------------------------------------------
# Model pricing (per 1M tokens)
# ------------------------------------------------------------------
MODEL_PRICING = {
    # Anthropic
    "claude-haiku-4-5-20251001":  {"input": 1.0,  "output": 5.0},
    "claude-sonnet-4-5-20250929": {"input": 3.0,  "output": 15.0},
    # Fallback defaults
    "default_input": 2.0,
    "default_output": 10.0,
}


def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate cost in USD for a given model and token counts."""
    pricing = MODEL_PRICING.get(model, {})
    rate_in = pricing.get("input", MODEL_PRICING["default_input"])
    rate_out = pricing.get("output", MODEL_PRICING["default_output"])
    cost = (tokens_in / 1_000_000 * rate_in) + (tokens_out / 1_000_000 * rate_out)
    return round(cost, 6)


# ------------------------------------------------------------------
# LLM factory -- creates the right LLM object for CrewAI
# ------------------------------------------------------------------
def _build_crewai_llm(config: AgentConfig) -> Any:
    """Build a CrewAI-compatible LLM from an AgentConfig.

    CrewAI accepts litellm model strings directly, so we construct
    the appropriate provider/model string and set the API key.
    """
    if not CREWAI_AVAILABLE:
        return None

    try:
        from backend.config import Config
    except ImportError:
        Config = None  # type: ignore[assignment,misc]

    model = config.model
    provider = config.provider

    # Map provider to litellm prefix
    if provider == "anthropic":
        api_key = getattr(Config, 'ANTHROPIC_API_KEY', '') if Config else ''
        llm_string = f"anthropic/{model}"
    elif provider == "openai":
        api_key = getattr(Config, 'OPENAI_API_KEY', '') if Config else ''
        llm_string = f"openai/{model}"
    elif provider == "google":
        api_key = getattr(Config, 'GOOGLE_AI_KEY', '') if Config else ''
        llm_string = f"google/{model}"
    elif provider == "xai":
        api_key = getattr(Config, 'XAI_API_KEY', '') if Config else ''
        llm_string = model
    else:
        llm_string = model
        api_key = ''

    # CrewAI 0.40+ accepts a string directly as the llm parameter
    return llm_string


def _build_crewai_agent(config: AgentConfig, tools: Optional[List] = None) -> Any:
    """Convert an AgentConfig into a CrewAI Agent object."""
    if not CREWAI_AVAILABLE or CrewAgent is None:
        return None

    llm = _build_crewai_llm(config)

    agent = CrewAgent(
        role=config.role,
        goal=config.goal,
        backstory=config.backstory,
        llm=llm,
        tools=tools or [],
        verbose=True,
        max_iter=5,
        memory=True,
    )
    return agent


# ------------------------------------------------------------------
# The Engine
# ------------------------------------------------------------------
class StockPulseCrewEngine:
    """Orchestration engine that maps StockPulse AgentConfig objects to
    CrewAI Agent/Task/Crew objects and runs them.

    Supports:
      - Sequential process (agents run one after another)
      - Hierarchical process (manager agent delegates to workers)
    """

    def __init__(self):
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._tools_cache: Dict[str, List] = {}

    @property
    def is_available(self) -> bool:
        return CREWAI_AVAILABLE

    def register_agent_config(self, config: AgentConfig, tools: Optional[List] = None):
        """Register an AgentConfig (and optional tool list) for later crew assembly."""
        self._agent_configs[config.name] = config
        if tools:
            self._tools_cache[config.name] = tools

    def run_crew(
        self,
        agent_names: List[str],
        task_description: str,
        inputs: Optional[Dict[str, Any]] = None,
        process: str = "sequential",
    ) -> AgentResult:
        """Assemble and run a CrewAI Crew with the specified agents.

        Parameters
        ----------
        agent_names : list[str]
            Names of registered agents to include in the crew.
        task_description : str
            Natural-language description of the task for the crew.
        inputs : dict, optional
            Key-value inputs passed to the crew's kickoff().
        process : str
            'sequential' or 'hierarchical'.

        Returns
        -------
        AgentResult
        """
        started_at = datetime.utcnow().isoformat()
        start_time = time.time()

        if not CREWAI_AVAILABLE:
            return AgentResult(
                agent_name=",".join(agent_names),
                framework="crewai",
                status="error",
                output="",
                error="CrewAI is not installed. Install with: pip install crewai",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
            )

        # Build CrewAI Agent objects
        crew_agents = []
        for name in agent_names:
            config = self._agent_configs.get(name)
            if config is None:
                return AgentResult(
                    agent_name=name,
                    framework="crewai",
                    status="error",
                    output="",
                    error=f"Agent config not found: {name}",
                    started_at=started_at,
                    completed_at=datetime.utcnow().isoformat(),
                )
            tools = self._tools_cache.get(name, [])
            crew_agent = _build_crewai_agent(config, tools)
            if crew_agent is None:
                return AgentResult(
                    agent_name=name,
                    framework="crewai",
                    status="error",
                    output="",
                    error=f"Failed to build CrewAI agent for {name}",
                    started_at=started_at,
                    completed_at=datetime.utcnow().isoformat(),
                )
            crew_agents.append(crew_agent)

        # Build tasks -- one per agent, all with the same description
        # (in a real scenario, you'd pass per-agent task descriptions)
        tasks = []
        for i, crew_agent in enumerate(crew_agents):
            task = CrewTask(
                description=task_description,
                agent=crew_agent,
                expected_output="Detailed analysis results in structured format.",
            )
            tasks.append(task)

        # Select process mode
        if process == "hierarchical" and hasattr(Process, 'hierarchical'):
            crew_process = Process.hierarchical
        else:
            crew_process = Process.sequential

        try:
            crew = Crew(
                agents=crew_agents,
                tasks=tasks,
                process=crew_process,
                verbose=True,
            )

            result = crew.kickoff(inputs=inputs or {})

            duration_ms = int((time.time() - start_time) * 1000)

            # Extract output text
            output_text = str(result) if result else ""

            # Estimate token usage (rough heuristic: 4 chars per token)
            est_input_tokens = len(task_description) // 4
            est_output_tokens = len(output_text) // 4

            # Estimate cost using the first agent's model
            first_model = self._agent_configs[agent_names[0]].model if agent_names else "default"
            est_cost = _estimate_cost(first_model, est_input_tokens, est_output_tokens)

            return AgentResult(
                agent_name=",".join(agent_names),
                framework="crewai",
                status="success",
                output=output_text,
                raw_output=result,
                tokens_input=est_input_tokens,
                tokens_output=est_output_tokens,
                estimated_cost=est_cost,
                duration_ms=duration_ms,
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                metadata={
                    "process": process,
                    "agent_count": len(agent_names),
                    "agents": agent_names,
                },
            )

        except Exception as e:
            logger.error(f"CrewAI execution failed: {e}", exc_info=True)
            return AgentResult(
                agent_name=",".join(agent_names),
                framework="crewai",
                status="error",
                output="",
                error=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
            )

    def list_registered(self) -> List[Dict[str, Any]]:
        """List all registered agent configs."""
        result = []
        for name, config in self._agent_configs.items():
            result.append({
                "name": config.name,
                "role": config.role,
                "model": config.model,
                "provider": config.provider,
                "has_tools": bool(self._tools_cache.get(name)),
            })
        return result
