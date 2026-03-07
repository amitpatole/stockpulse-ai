```python
from typing import List, Dict, Optional
import sqlite3
from backend.config import Config
from backend.database import get_db_connection
from backend.agents.base import BaseAgent, AgentConfig, AgentResult, AgentStatus, AgentFramework

class EconomicEventsAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._db_connection = get_db_connection()

    def execute(self, inputs: Dict[str, Any] = None) -> AgentResult:
        try:
            # Fetch economic events from API
            cursor = self._db_connection.cursor()
            cursor.execute("SELECT * FROM economic_events")
            economic_events = cursor.fetchall()
            
            # Process and return the data
            output = "\n".join([f"{event['name']} - {event['event_date']}" for event in economic_events])
            return AgentResult(
                agent_name=self.name,
                framework=self.config.provider,
                status=AgentStatus.SUCCESS,
                output=output,
                tokens_input=0,
                tokens_output=0,
                estimated_cost=0.0,
                duration_ms=0,
                started_at=datetime.utcnow().isoformat(),
                completed_at=datetime.utcnow().isoformat(),
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                framework=self.config.provider,
                status=AgentStatus.ERROR,
                output=str(e),
                tokens_input=0,
                tokens_output=0,
                estimated_cost=0.0,
                duration_ms=0,
                error=str(e),
            )

    def run(self, inputs: Dict[str, Any] = None) -> AgentResult:
        return self.execute(inputs)
```