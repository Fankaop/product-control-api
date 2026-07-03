from data.models.webhook import WebhookDelivery, WebhookSubscription
from data.repositories.webhook_repository import WebhookRepository
from domain.exceptions.webhook import WebhookAlreadyInactive, WebhookNotFound


class WebhookService:
    def __init__(self, repo: WebhookRepository) -> None:
        self.repo = repo

    async def create_subscription(
        self,
        url: str,
        events: list[str],
        secret_key: str,
        retry_count: int = 3,
        timeout: int = 10,
    ) -> WebhookSubscription:
        return await self.repo.create(
            url=url,
            events=events,
            secret_key=secret_key,
            retry_count=retry_count,
            timeout=timeout,
        )

    async def get_subscription(self, webhook_id: int) -> WebhookSubscription:
        webhook = await self.repo.get_by_id(webhook_id)
        if webhook is None:
            raise WebhookNotFound(webhook_id)
        return webhook

    async def list_subscriptions(self, limit: int = 100, offset: int = 0) -> list[WebhookSubscription]:
        return await self.repo.get_all(limit=limit, offset=offset)

    async def deactivate_subscription(self, webhook_id: int) -> WebhookSubscription:
        webhook = await self.repo.get_by_id(webhook_id)
        if webhook is None:
            raise WebhookNotFound(webhook_id)
        if not webhook.is_active:
            raise WebhookAlreadyInactive(webhook_id)
        updated = await self.repo.update(webhook_id, is_active=False)
        return updated  # type: ignore[return-value]

    async def delete_subscription(self, webhook_id: int) -> None:
        deleted = await self.repo.delete(webhook_id)
        if not deleted:
            raise WebhookNotFound(webhook_id)

    async def get_deliveries(self, webhook_id: int, limit: int = 50) -> list[WebhookDelivery]:
        webhook = await self.repo.get_by_id(webhook_id)
        if webhook is None:
            raise WebhookNotFound(webhook_id)
        return await self.repo.get_deliveries_by_subscription(webhook_id, limit=limit)

    async def dispatch(self, event: str, payload: dict) -> list[str]:
        from tasks.webhooks import send_webhook_delivery

        subscriptions = await self.repo.get_active_by_event(event)
        task_ids = []
        for subscription in subscriptions:
            delivery = await self.repo.create_delivery(
                subscription_id=subscription.id,
                event_type=event,
                payload=payload,
            )
            task = send_webhook_delivery.delay(delivery.id)
            task_ids.append(task.id)
        return task_ids
