from fastapi import APIRouter

from api.v1.schemas.webhook import (
    DeliveryListResponse,
    WebhookCreate,
    WebhookListResponse,
    WebhookResponse,
    WebhookUpdate,
)
from core.dependencies import CurrentUser, WebhookServiceDep

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", status_code=201, response_model=WebhookResponse)
async def create_webhook(data: WebhookCreate, service: WebhookServiceDep, _: CurrentUser):
    return await service.create_subscription(
        url=data.url,
        events=data.events,
        secret_key=data.secret_key,
        retry_count=data.retry_count,
        timeout=data.timeout,
    )


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(service: WebhookServiceDep, _: CurrentUser):
    items = await service.list_subscriptions()
    return WebhookListResponse(items=items, total=len(items))


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(webhook_id: int, data: WebhookUpdate, service: WebhookServiceDep, _: CurrentUser):
    webhook = await service.get_subscription(webhook_id)
    update_kwargs = data.model_dump(exclude_none=True)
    if not update_kwargs:
        return webhook
    updated = await service.repo.update(webhook_id, **update_kwargs)
    return updated


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(webhook_id: int, service: WebhookServiceDep, _: CurrentUser):
    await service.delete_subscription(webhook_id)


@router.get("/{webhook_id}/deliveries", response_model=DeliveryListResponse)
async def get_deliveries(webhook_id: int, service: WebhookServiceDep, _: CurrentUser, limit: int = 50):
    items = await service.get_deliveries(webhook_id, limit=limit)
    return DeliveryListResponse(items=items, total=len(items))
