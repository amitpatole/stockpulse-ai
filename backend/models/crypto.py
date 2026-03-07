```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from ticker_pulse.database import Base

class CryptoCurrency(Base):
    __tablename__ = 'cryptocurrencies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    price_usd = Column(Float, nullable=False)
    market_cap_usd = Column(Float, nullable=False)
    volume_usd_24h = Column(Float, nullable=False)
    percent_change_1h = Column(Float, nullable=False)
    percent_change_24h = Column(Float, nullable=False)
    percent_change_7d = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
```