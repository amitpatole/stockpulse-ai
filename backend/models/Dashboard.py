```python
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Dashboard(Base):
    __tablename__ = 'dashboard'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    widgets = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```