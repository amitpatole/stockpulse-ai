```python
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db_session
from backend.models import Event
from backend.schemas import EventCreate, EventUpdate, EventStatus
from backend.utils import handle_event_delivery

router = APIRouter()

@router.post("/events", response_model=EventCreate)
async def create_event(event: EventCreate, session: AsyncSession = Depends(get_db_session)):
    new_event = Event(**event.dict())
    session.add(new_event)
    await session.commit()
    await session.refresh(new_event)
    return new_event

@router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str = Path(..., title="Event ID"), session: AsyncSession = Depends(get_db_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.put("/events/{event_id}", response_model=Event)
async def update_event(event_id: str = Path(..., title="Event ID"), event: EventUpdate, session: AsyncSession = Depends(get_db_session)):
    existing_event = await session.get(Event, event_id)
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event.dict(exclude_unset=True).items():
        setattr(existing_event, key, value)
    await session.commit()
    await session.refresh(existing_event)
    return existing_event

@router.delete("/events/{event_id}", response_model=EventStatus)
async def delete_event(event_id: str = Path(..., title="Event ID"), session: AsyncSession = Depends(get_db_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await session.delete(event)
    await session.commit()
    return {"status": "success"}

@router.post("/events/{event_id}/deliver", response_model=EventDelivery)
async def deliver_event(event_id: str = Path(..., title="Event ID"), session: AsyncSession = Depends(get_db_session)):
    event = await session.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    delivery_status = await handle_event_delivery(event)
    return delivery_status
```