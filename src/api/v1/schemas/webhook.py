from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WebhookCreate(BaseModel):
    url: str
    events: list[str]
    secret_key: str
    retry_count: int = 3
    timeout: int = 10


class WebhookUpdate(BaseModel):
    is_active: bool | None = None
    events: list[str] | None = None


class WebhookResponse(BaseModel):
    id: int
    url: str
    events: list[str]
    is_active: bool
    retry_count: int
    timeout: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WebhookListResponse(BaseModel):
    items: list[WebhookResponse]
    total: int


class DeliveryResponse(BaseModel):
    id: int
    event_type: str
    status: str
    attempts: int
    response_status: int | None
    response_body: str | None
    error_message: str | None
    created_at: datetime
    delivered_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class DeliveryListResponse(BaseModel):
    items: list[DeliveryResponse]
    total: int
