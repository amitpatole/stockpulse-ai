```python
from app.db.base_class import Base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Provider(Base):
    __tablename__ = "provider"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    rate_limit = relationship("RateLimit", back_populates="provider")

class RateLimit(Base):
    __tablename__ = "rate_limit"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("provider.id"), nullable=False)
    usage = Column(Integer, default=0)
    limit = Column(Integer, default=0)
    quota = Column(Integer, default=0)
```