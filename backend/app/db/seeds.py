```python
from app.db.models import Provider, RateLimit
from app.db.dependencies import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

async def seed_data(session: AsyncSession):
    providers = [
        Provider(name="Provider1"),
        Provider(name="Provider2")
    ]
    await asyncio.gather(*[session.add(provider) for provider in providers])
    await session.commit()

    rate_limits = [
        RateLimit(provider_id=1, quota=100, remaining=50, reset_time=3600),
        RateLimit(provider_id=2, quota=200, remaining=100, reset_time=7200)
    ]
    await asyncio.gather(*[session.add(rate_limit) for rate_limit in rate_limits])
    await session.commit()

def seed():
    session = next(get_async_session())
    asyncio.run(seed_data(session))
```