```python
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

Base = declarative_base()

class StockData(Base):
    __tablename__ = 'stock_data'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    data = Column(JSON)

class TechnicalIndicators(Base):
    __tablename__ = 'technical_indicators'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    date = Column(DateTime, index=True)
    close = Column(Float)
    rsi = Column(Float)
    macd = Column(Float)
    signal = Column(Float)
    upper_band = Column(Float)
    lower_band = Column(Float)
    sma = Column(Float)
    ema = Column(Float)
```