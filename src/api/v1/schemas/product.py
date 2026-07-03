from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    unique_code: str
    batch_id: int


class AggregateRequest(BaseModel):
    unique_code: str


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    unique_code: str
    is_aggregated: bool
    aggregated_at: datetime | None
