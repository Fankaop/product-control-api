from pydantic import BaseModel


class DashboardStats(BaseModel):
    summary: dict
    today: dict
    by_shift: dict
    top_work_centers: list
    cached_at: str


class BatchStats(BaseModel):
    batch_info: dict
    production_stats: dict
    timeline: dict
    team_performance: dict


class WorkCenterStats(BaseModel):
    work_center_id: int
    total_batches: int
    closed_batches: int
    open_batches: int
    total_products: int


class CompareBatchesRequest(BaseModel):
    batch_ids: list[int]


class CompareBatchesResponse(BaseModel):
    comparison: list
    average: dict
