```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class Webhook(Base):
    __tablename__ = 'webhooks'

    id = Column(UUID, primary_key=True, server_default=func.uuid())
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    webhook_url = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    last_delivery_status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Webhook(id={self.id}, user_id={self.user_id}, webhook_url={self.webhook_url}, event_type={self.event_type}, status={self.status})>"
```