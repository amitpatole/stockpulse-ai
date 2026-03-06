```python
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .config import get_db_url, get_db_type

db = SQLAlchemy()

class HealthStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False)
    latency_ms = db.Column(db.Float, nullable=False)
    error_rate = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<HealthStatus {self.id} {self.status} {self.timestamp}>"
```