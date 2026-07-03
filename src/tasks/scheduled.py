import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from data.models.webhook import WebhookDelivery, WebhookSubscription
from tasks.webhooks import send_webhook_delivery

from celery_app import celery_app
from core.cache import invalidate, set_cached
from core.database import async_session_maker
from data.repositories.batch_repository import BatchRepository
from data.repositories.webhook_repository import WebhookRepository
from domain.services.analytics_service import AnalyticsService
from domain.services.webhook_service import WebhookService
from storage.minio_service import minio_service


@celery_app.task
def auto_close_expired_batches():
    return asyncio.run(_auto_close())


@celery_app.task
def cleanup_old_files():
    return asyncio.run(_cleanup())


@celery_app.task
def update_cached_statistics():
    return asyncio.run(_update_stats())


@celery_app.task
def retry_failed_webhooks():
    return asyncio.run(_retry_webhooks())


async def _auto_close():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with async_session_maker() as session:
        repo = BatchRepository(session)
        webhook_service = WebhookService(repo=WebhookRepository(session))
        batches = await repo.get_many(is_closed=False)

        closed = 0
        for batch in batches:
            if batch.shift_end < now:
                await repo.update(batch.id, is_closed=True, closed_at=now)
                await invalidate(f"batch_detail:{batch.id}")
                await invalidate(f"batch_statistics:{batch.id}")
                await webhook_service.dispatch("batch_closed", {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "closed_at": now.isoformat(),
                })
                closed += 1

        await invalidate("dashboard_stats")

    return {"closed": closed}


async def _cleanup():
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    deleted = 0

    for bucket in ["reports", "exports", "imports"]:
        try:
            objects = minio_service.client.list_objects(bucket, recursive=True)
            for obj in objects:
                if (
                    obj.object_name is not None
                    and obj.last_modified is not None
                    and obj.last_modified.replace(tzinfo=None) < cutoff.replace(tzinfo=None)
                ):
                    minio_service.delete_file(bucket, obj.object_name)
                    deleted += 1
        except Exception:
            continue

    return {"deleted_files": deleted}


async def _update_stats():
    async with async_session_maker() as session:
        service = AnalyticsService(session)
        stats = await service.get_dashboard_stats()

    import json
    await set_cached("dashboard_stats", json.dumps(stats), ttl=300)
    return {"updated": True}


async def _retry_webhooks():
    async with async_session_maker() as session:
        result = await session.execute(
            select(WebhookDelivery)
            .join(WebhookSubscription)
            .where(
                WebhookDelivery.status == "failed",
                WebhookDelivery.attempts < WebhookSubscription.retry_count,
                WebhookSubscription.is_active == True,
            )
        )
        failed = result.scalars().all()

    retried = 0
    for delivery in failed:
        send_webhook_delivery.delay(delivery.id)
        retried += 1

    return {"retried": retried}
