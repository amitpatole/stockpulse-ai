```python
import time
import json
import sqlite3
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class AgentStatus(str, Enum):
    IDLE = 'idle'
    RUNNING = 'running'
    SUCCESS = 'success'
    ERROR = 'error'


class AgentFramework(str, Enum):
    CREWAI = 'crewai'
    OPENCLAW = 'openclaw'


@dataclass
class AgentConfig:
    """Configuration for a single agent"""
    name: str
    role: str
    goal: str
    backstory: str
    model: str = 'claude-haiku-4-5-20251001'
    provider: str = 'anthropic'
    max_tokens: int = 4096
    temperature: float = 0.7
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    """Result from an agent run"""
    agent_name: str
    framework: str
    status: str  # 'success' or 'error'
    output: str
    raw_output: Any = None
    tokens_input: int = 0
    tokens_output: int = 0
    estimated_cost: float = 0.0
    duration_ms: int = 0
    started_at: str = ''
    completed_at: str = ''
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop('raw_output', None)
        return d


class BaseAgent(ABC):
    """Abstract base class for all TickerPulse agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self._status = AgentStatus.IDLE
        self._last_result: Optional[AgentResult] = None
        self._run_count = 0

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def last_result(self) -> Optional[AgentResult]:
        return self._last_result

    @abstractmethod
    def execute(self, inputs: Dict[str, Any] = None) -> AgentResult:
        """Execute the agent's task. Must be implemented by subclasses."""
        pass

    def run(self, inputs: Dict[str, Any] = None) -> AgentResult:
        """Run the agent with timing, error handling, and status tracking"""
        self._status = AgentStatus.RUNNING
        start_time = time.time()
        started_at = datetime.utcnow().isoformat()

        try:
            result = self.execute(inputs)
            self._last_result = result
            self._status = AgentStatus.SUCCESS
            self._run_count += 1
            return result
        except Exception as e:
            self._last_result = AgentResult(
                agent_name=self.name,
                framework=self.config.provider,
                status=AgentStatus.ERROR,
                output=str(e),
                tokens_input=0,
                tokens_output=0,
                estimated_cost=0.0,
                duration_ms=0,
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                error=e
            )
            return self._last_result
```