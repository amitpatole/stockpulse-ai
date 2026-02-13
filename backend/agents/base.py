"""
StockPulse AI v3.0 - Agent Base Layer
Agent registry, base classes, and result tracking.
"""

import time
import json
import sqlite3
import logging
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
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
    """Abstract base class for all StockPulse agents"""

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
            result = self.execute(inputs or {})
            result.started_at = started_at
            result.completed_at = datetime.utcnow().isoformat()
            result.duration_ms = int((time.time() - start_time) * 1000)
            self._status = AgentStatus.SUCCESS if result.status == 'success' else AgentStatus.ERROR
            self._last_result = result
            self._run_count += 1
            return result
        except Exception as e:
            logger.error(f"Agent {self.name} failed: {e}", exc_info=True)
            result = AgentResult(
                agent_name=self.name,
                framework='native',
                status='error',
                output='',
                error=str(e),
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_ms=int((time.time() - start_time) * 1000),
            )
            self._status = AgentStatus.ERROR
            self._last_result = result
            return result

    def get_status_dict(self) -> Dict[str, Any]:
        """Return agent status as a dictionary for API responses"""
        return {
            'name': self.config.name,
            'role': self.config.role,
            'model': self.config.model,
            'status': self._status.value,
            'enabled': self.config.enabled,
            'run_count': self._run_count,
            'last_run': self._last_result.to_dict() if self._last_result else None,
            'tags': self.config.tags,
        }


class AgentRegistry:
    """Registry for all agents with status tracking and run history persistence"""

    def __init__(self, db_path: str = 'stock_news.db'):
        self._agents: Dict[str, BaseAgent] = {}
        self._lock = threading.Lock()
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create agent_runs table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    framework TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    tokens_input INTEGER DEFAULT 0,
                    tokens_output INTEGER DEFAULT 0,
                    estimated_cost REAL DEFAULT 0.0,
                    duration_ms INTEGER DEFAULT 0,
                    error TEXT,
                    metadata TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_agent_runs_name
                ON agent_runs(agent_name)
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_agent_runs_created
                ON agent_runs(created_at)
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to init agent_runs table: {e}")

    def register(self, agent: BaseAgent):
        """Register an agent"""
        with self._lock:
            self._agents[agent.name] = agent
            logger.info(f"Registered agent: {agent.name} ({agent.config.role})")

    def get(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name"""
        return self._agents.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents with their status"""
        return [agent.get_status_dict() for agent in self._agents.values()]

    def run_agent(self, name: str, inputs: Dict[str, Any] = None) -> Optional[AgentResult]:
        """Run an agent by name and persist the result"""
        agent = self._agents.get(name)
        if not agent:
            logger.error(f"Agent not found: {name}")
            return None

        if not agent.config.enabled:
            logger.warning(f"Agent {name} is disabled")
            return AgentResult(
                agent_name=name,
                framework='disabled',
                status='error',
                output='',
                error='Agent is disabled',
            )

        result = agent.run(inputs)
        self._persist_result(result, inputs)
        return result

    def _persist_result(self, result: AgentResult, inputs: Dict[str, Any] = None):
        """Save agent run result to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT INTO agent_runs
                (agent_name, framework, status, input_data, output_data,
                 tokens_input, tokens_output, estimated_cost, duration_ms,
                 error, metadata, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.agent_name,
                result.framework,
                result.status,
                json.dumps(inputs) if inputs else None,
                result.output[:10000] if result.output else None,  # Cap at 10K chars
                result.tokens_input,
                result.tokens_output,
                result.estimated_cost,
                result.duration_ms,
                result.error,
                json.dumps(result.metadata) if result.metadata else None,
                result.started_at,
                result.completed_at,
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to persist agent result: {e}")

    def get_run_history(self, agent_name: str = None, limit: int = 50) -> List[Dict]:
        """Get agent run history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            if agent_name:
                rows = conn.execute(
                    'SELECT * FROM agent_runs WHERE agent_name = ? ORDER BY created_at DESC LIMIT ?',
                    (agent_name, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    'SELECT * FROM agent_runs ORDER BY created_at DESC LIMIT ?',
                    (limit,)
                ).fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get run history: {e}")
            return []

    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get cost summary across all agents"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

            # Total cost
            row = conn.execute('''
                SELECT
                    COALESCE(SUM(estimated_cost), 0) as total_cost,
                    COUNT(*) as total_runs,
                    COALESCE(SUM(tokens_input), 0) as total_tokens_in,
                    COALESCE(SUM(tokens_output), 0) as total_tokens_out
                FROM agent_runs
                WHERE created_at > datetime('now', ? || ' days')
            ''', (f'-{days}',)).fetchone()

            # Per-agent breakdown
            agent_rows = conn.execute('''
                SELECT
                    agent_name,
                    COUNT(*) as runs,
                    COALESCE(SUM(estimated_cost), 0) as cost,
                    COALESCE(SUM(tokens_input + tokens_output), 0) as tokens
                FROM agent_runs
                WHERE created_at > datetime('now', ? || ' days')
                GROUP BY agent_name
                ORDER BY cost DESC
            ''', (f'-{days}',)).fetchall()

            # Daily breakdown
            daily_rows = conn.execute('''
                SELECT
                    DATE(created_at) as date,
                    COALESCE(SUM(estimated_cost), 0) as cost,
                    COUNT(*) as runs
                FROM agent_runs
                WHERE created_at > datetime('now', ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            ''', (f'-{days}',)).fetchall()

            conn.close()

            return {
                'period_days': days,
                'total_cost': round(row['total_cost'], 4),
                'total_runs': row['total_runs'],
                'total_tokens_input': row['total_tokens_in'],
                'total_tokens_output': row['total_tokens_out'],
                'by_agent': [dict(r) for r in agent_rows],
                'by_day': [dict(r) for r in daily_rows],
            }
        except Exception as e:
            logger.error(f"Failed to get cost summary: {e}")
            return {'period_days': days, 'total_cost': 0, 'total_runs': 0,
                    'total_tokens_input': 0, 'total_tokens_output': 0,
                    'by_agent': [], 'by_day': []}
