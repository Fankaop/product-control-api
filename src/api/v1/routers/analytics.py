from fastapi import APIRouter

from api.v1.schemas.analytics import (
    BatchStats,
    CompareBatchesRequest,
    CompareBatchesResponse,
    DashboardStats,
    WorkCenterStats,
)
from core.dependencies import AnalyticsServiceDep, CurrentUser

router = APIRouter(prefix='/analytics', tags=['analytics'])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(service: AnalyticsServiceDep, _: CurrentUser):
    return await service.get_dashboard_stats()


@router.get("/batches/{batch_id}", response_model=BatchStats)
async def get_batch_stats(batch_id: int, service: AnalyticsServiceDep, _: CurrentUser):
    return await service.get_batch_stats(batch_id)


@router.get("/work-centers/{work_center_id}", response_model=WorkCenterStats)
async def get_work_center_stats(work_center_id: int, service: AnalyticsServiceDep, _: CurrentUser):
    return await service.get_work_center_stats(work_center_id)


@router.post("/compare-batches", response_model=CompareBatchesResponse)
async def compare_batches(data: CompareBatchesRequest, service: AnalyticsServiceDep, _: CurrentUser):
    return await service.compare_batches(data.batch_ids)
