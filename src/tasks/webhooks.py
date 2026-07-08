import asyncio
import json
from datetime import datetime, timezone

import httpx

from celery_app import celery_app
from core.database import async_session_maker
from data.models.webhook import WebhookDelivery
from data.repositories.webhook_repository import WebhookRepository
from utils.hmac_utils import sign_payload


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_webhook_delivery(self, delivery_id: int):
    return asyncio.run(_send(self, delivery_id))


async def _send(task, delivery_id: int):
    async with async_session_maker() as session:
        repo = WebhookRepository(session)

        delivery = await session.get(WebhookDelivery, delivery_id)
        if delivery is None:
            return {"success": False, "error": "Delivery not found"}

        subscription = await repo.get_by_id(delivery.subscription_id)
        if subscription is None or not subscription.is_active:
            await repo.update_delivery(delivery_id, status="skipped")
            return {"success": False, "error": "Subscription inactive"}

        body = json.dumps(delivery.payload).encode()
        signature = sign_payload(subscription.secret_key, body)

        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Event": delivery.event_type,
        }

        try:
            async with httpx.AsyncClient(timeout=subscription.timeout) as client:
                response = await client.post(subscription.url, content=body, headers=headers)

            success = response.is_success
            await repo.update_delivery(
                delivery_id,
                status="success" if success else "failed",
                attempts=delivery.attempts + 1,
                response_status=response.status_code,
                response_body=response.text[:1000],
                delivered_at=datetime.now(timezone.utc).replace(tzinfo=None) if success else None,
            )

            if not success:
                raise task.retry(
                    exc=Exception(f"HTTP {response.status_code}"),
                    max_retries=subscription.retry_count,
                )

            return {"success": True, "status_code": response.status_code}

        except httpx.RequestError as exc:
            await repo.update_delivery(
                delivery_id,
                status="failed",
                attempts=delivery.attempts + 1,
                error_message=str(exc)[:500],
            )
            raise task.retry(exc=exc, max_retries=subscription.retry_count)
