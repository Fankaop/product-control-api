from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.webhook import WebhookDelivery, WebhookSubscription
from data.repositories.base_repository import BaseRepository


class WebhookRepository(BaseRepository[WebhookSubscription]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WebhookSubscription)

    async def get_active_by_event(self, event: str) -> list[WebhookSubscription]:
        result = await self.session.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.is_active == True,
                WebhookSubscription.events.contains([event]),
            )
        )
        return list(result.scalars().all())

    async def create_delivery(
        self,
        subscription_id: int,
        event_type: str,
        payload: dict,
    ) -> WebhookDelivery:
        delivery = WebhookDelivery(
            subscription_id=subscription_id,
            event_type=event_type,
            payload=payload,
        )
        self.session.add(delivery)
        await self.session.commit()
        await self.session.refresh(delivery)
        return delivery

    async def update_delivery(self, delivery_id: int, **kwargs) -> WebhookDelivery | None:
        delivery = await self.session.get(WebhookDelivery, delivery_id)
        if delivery is None:
            return None
        for key, value in kwargs.items():
            setattr(delivery, key, value)
        await self.session.commit()
        await self.session.refresh(delivery)
        return delivery

    async def get_deliveries_by_subscription(
        self,
        subscription_id: int,
        limit: int = 50,
    ) -> list[WebhookDelivery]:
        result = await self.session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
