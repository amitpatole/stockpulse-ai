```python
from sqlalchemy import Column, Integer, String, Float, DateTime
from app import db

class Cryptocurrency(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    price_usd = Column(Float, nullable=False)
    last_updated = Column(DateTime, nullable=False)
```