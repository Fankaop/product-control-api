from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from api.v1.schemas.product import ProductResponse


class BatchCreate(BaseModel):
    is_closed: bool = False
    task_description: str
    work_center_name: str
    work_center_identifier: str
    shift: str
    team: str
    batch_number: int
    batch_date: date
    nomenclature: str
    ekn_code: str
    shift_start: datetime
    shift_end: datetime


class AggregateAsyncRequest(BaseModel):
    unique_codes: list[str]


class ReportRequest(BaseModel):
    format: str = "excel"
    email: str | None = None


class ExportRequest(BaseModel):
    format: str = "excel"
    filters: dict = {}


class BatchUpdate(BaseModel):
    is_closed: bool | None = None
    task_description: str | None = None
    shift: str | None = None
    team: str | None = None


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_closed: bool
    closed_at: datetime | None
    batch_number: int
    batch_date: date
    task_description: str
    nomenclature: str
    ekn_code: str
    shift: str
    team: str
    shift_start: datetime
    shift_end: datetime
    created_at: datetime
    products: list[ProductResponse] = []
