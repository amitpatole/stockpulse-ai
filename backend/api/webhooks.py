```python
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db_session
from backend.models import Webhook
from backend.schemas import WebhookCreate, WebhookUpdate, WebhookStatus, WebhookDelivery
from backend.utils import handle_webhook_delivery

router = APIRouter()

@router.post("/webhooks", response_model=WebhookCreate)
async def create_webhook(webhook: WebhookCreate, session: AsyncSession = Depends(get_db_session)):
    new_webhook = Webhook(**webhook.dict())
    session.add(new_webhook)
    await session.commit()
    await session.refresh(new_webhook)
    return new_webhook

@router.get("/webhooks/{webhook_id}", response_model=Webhook)
async def get_webhook(webhook_id: str = Path(..., title="Webhook ID"), session: AsyncSession = Depends(get_db_session)):
    webhook = await session.get(Webhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook

@router.put("/webhooks/{webhook_id}", response_model=Webhook)
async def update_webhook(webhook_id: str = Path(..., title="Webhook ID"), webhook: WebhookUpdate, session: AsyncSession = Depends(get_db_session)):
    existing_webhook = await session.get(Webhook, webhook_id)
    if not existing_webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    for key, value in webhook.dict(exclude_unset=True).items():
        setattr(existing_webhook, key, value)
    await session.commit()
    await session.refresh(existing_webhook)
    return existing_webhook

@router.delete("/webhooks/{webhook_id}", response_model=WebhookStatus)
async def delete_webhook(webhook_id: str = Path(..., title="Webhook ID"), session: AsyncSession = Depends(get_db_session)):
    webhook = await session.get(Webhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await session.delete(webhook)
    await session.commit()
    return {"status": "success"}

@router.post("/webhooks/{webhook_id}/deliver", response_model=WebhookDelivery)
async def deliver_webhook(webhook_id: str = Path(..., title="Webhook ID"), session: AsyncSession = Depends(get_db_session)):
    webhook = await session.get(Webhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    delivery_status = await handle_webhook_delivery(webhook)
    return delivery_status
```