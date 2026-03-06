```python
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.dependencies import get_async_session
from app.db.models import RateLimit, Provider
from app.db.crud import get_rate_limits, get_provider_by_id
from app.schemas import RateLimitSchema, RateLimitCreateSchema, ProviderSchema

router = APIRouter()

@router.get("/rate_limits", response_model=List[RateLimitSchema])
async def get_rate_limits_data(
    provider_id: int = None,
    session: AsyncSession = Depends(get_async_session),
) -> List[RateLimit]:
    query = select(RateLimit)
    if provider_id:
        query = query.join(Provider).where(Provider.id == provider_id)
    result = await session.execute(query)
    return result.scalars().all()

@router.post("/rate_limits", response_model=RateLimitSchema)
async def create_rate_limit(
    rate_limit: RateLimitCreateSchema,
    session: AsyncSession = Depends(get_async_session),
) -> RateLimit:
    provider = await get_provider_by_id(rate_limit.provider_id, session)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    new_rate_limit = RateLimit(**rate_limit.dict())
    session.add(new_rate_limit)
    await session.commit()
    await session.refresh(new_rate_limit)
    return new_rate_limit

@router.get("/providers", response_model=List[ProviderSchema])
async def get_providers(session: AsyncSession = Depends(get_async_session)) -> List[Provider]:
    result = await session.execute(select(Provider))
    return result.scalars().all()
```