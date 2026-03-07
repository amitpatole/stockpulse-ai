```python
from app import db
from app.models import Cryptocurrency
from app.services import get_cryptocurrency_data
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

class CryptocurrencyAgent(BaseAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.symbol = config.tags[0]

    def execute(self, inputs: Dict[str, Any] = None) -> AgentResult:
        try:
            data = get_cryptocurrency_data(self.symbol)
            price = data['usd']
            result = AgentResult(
                agent_name=self.name,
                framework=self.config.provider,
                status=AgentStatus.SUCCESS,
                output=f'Current price of {self.symbol} is ${price}',
                tokens_input=0,
                tokens_output=0,
                estimated_cost=0.0,
                duration_ms=int(time.time() * 1000) - int(inputs.get('started_at', time.time()) * 1000),
                started_at=inputs.get('started_at', ''),
                completed_at=inputs.get('completed_at', ''),
                error=None,
                metadata={'price': price}
            )
            db.session.add(Cryptocurrency(symbol=self.symbol, price_usd=price, last_updated=datetime.utcnow()))
            db.session.commit()
            return result
        except Exception as e:
            result = AgentResult(
                agent_name=self.name,
                framework=self.config.provider,
                status=AgentStatus.ERROR,
                output='Error fetching cryptocurrency data',
                tokens_input=0,
                tokens_output=0,
                estimated_cost=0.0,
                duration_ms=int(time.time() * 1000) - int(inputs.get('started_at', time.time()) * 1000),
                started_at=inputs.get('started_at', ''),
                completed_at=inputs.get('completed_at', ''),
                error=str(e),
                metadata={}
            )
            return result
```