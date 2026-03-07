```python
from pydantic import BaseModel

class WebhookCreate(BaseModel):
    user_id: str
    webhook_url: str
    event_type: str

class WebhookUpdate(BaseModel):
    user_id: Optional[str] = None
    webhook_url: Optional[str] = None
    event_type: Optional[str] = None

class WebhookStatus(BaseModel):
    status: str

class WebhookDelivery(BaseModel):
    status: str
    message: Optional[str] = None
```