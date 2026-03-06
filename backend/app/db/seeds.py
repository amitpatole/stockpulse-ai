```python
from app.models import Provider, RateLimit

def seed_data(db):
    providers = [
        Provider(name="Provider A", description="Provider A description"),
        Provider(name="Provider B", description="Provider B description"),
    ]
    db.add_all(providers)
    db.commit()

    rate_limits = [
        RateLimit(provider_id=1, usage=100, limit=500, quota=1000),
        RateLimit(provider_id=2, usage=200, limit=600, quota=1200),
    ]
    db.add_all(rate_limits)
    db.commit()
```