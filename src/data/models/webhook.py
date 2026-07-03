from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class WebhookSubscription(Base):
    __tablename__ = 'webhook_subscriptions'

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]
    events: Mapped[list[str]] = mapped_column(ARRAY(String))
    secret_key: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    retry_count: Mapped[int] = mapped_column(default=3)
    timeout: Mapped[int] = mapped_column(default=10)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    deliveries: Mapped[list['WebhookDelivery']] = relationship(back_populates='subscription')


class WebhookDelivery(Base):
    __tablename__ = 'webhook_deliveries'

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey('webhook_subscriptions.id'))
    event_type: Mapped[str]
    payload: Mapped[Any] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(default='pending')
    attempts: Mapped[int] = mapped_column(default=0)
    response_status: Mapped[int | None]
    response_body: Mapped[str | None]
    error_message: Mapped[str | None]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    delivered_at: Mapped[datetime | None]

    subscription: Mapped['WebhookSubscription'] = relationship(back_populates='deliveries')
