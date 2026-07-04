import uuid

from fastapi import APIRouter, UploadFile, File

from api.v1.schemas.batch import AggregateAsyncRequest, BatchCreate, BatchResponse, BatchUpdate, ExportRequest, ReportRequest
from api.v1.schemas.analytics import BatchStats
from api.v1.schemas.task import TaskResponse
from core.dependencies import BatchServiceDep, CurrentUser, WebhookServiceDep, AnalyticsServiceDep
from tasks.aggregation import aggregate_products_batch
from tasks.exports import export_batches_to_file
from tasks.imports import import_batches_from_file
from tasks.reports import generate_batch_report
from storage.minio_service import minio_service

router = APIRouter(prefix='/batches', tags=['batches'])


@router.post("", status_code=201, response_model=list[BatchResponse])
async def create_batches(
    data: list[BatchCreate],
    service: BatchServiceDep,
    webhook_service: WebhookServiceDep,
    current_user: CurrentUser,
):
    batches = await service.create_batches(data)
    for batch in batches:
        await webhook_service.dispatch("batch_created", {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "batch_date": str(batch.batch_date),
            "nomenclature": batch.nomenclature,
            "work_center_id": batch.work_center_id,
        })
    return batches


@router.post("/export", status_code=202, response_model=TaskResponse)
async def export_batches(
    data: ExportRequest,
    _: CurrentUser,
):
    task = export_batches_to_file.delay(data.filters, data.format)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Export started",
    )


@router.post("/import", status_code=202, response_model=TaskResponse)
async def import_batches(
    current_user: CurrentUser,
    file: UploadFile = File(...),
):
    object_name = f"{uuid.uuid4()}_{file.filename}"
    tmp_path = f"/tmp/{object_name}"

    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    minio_service.ensure_buckets()
    minio_service.upload_file(bucket="imports", file_path=tmp_path, object_name=object_name)

    task = import_batches_from_file.delay(
        file_url=object_name,
        object_name=object_name,
        user_id=current_user.id,
    )
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="File uploaded, import started",
    )


@router.get("", response_model=list[BatchResponse])
async def get_batches(
    service: BatchServiceDep,
    _: CurrentUser,
    is_closed: bool | None = None,
    batch_number: int | None = None,
    batch_date: str | None = None,
    work_center_id: int | None = None,
    shift: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    return await service.get_batches(
        is_closed=is_closed,
        batch_number=batch_number,
        batch_date=batch_date,
        work_center_id=work_center_id,
        shift=shift,
        limit=limit,
        offset=offset,
    )


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: int,
    service: BatchServiceDep,
    _: CurrentUser,
):
    return await service.get_batch_with_products(batch_id)


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    data: BatchUpdate,
    service: BatchServiceDep,
    webhook_service: WebhookServiceDep,
    _: CurrentUser,
):
    batch = await service.update_batch(batch_id, data)
    if data.is_closed is True:
        await webhook_service.dispatch("batch_closed", {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "closed_at": batch.closed_at.isoformat() if batch.closed_at else None,
        })
    else:
        changes = data.model_dump(exclude_none=True)
        if changes:
            await webhook_service.dispatch("batch_updated", {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "changes": changes,
            })
    return batch


@router.get("/{batch_id}/statistics", response_model=BatchStats)
async def get_batch_statistics(
    batch_id: int,
    service: AnalyticsServiceDep,
    _: CurrentUser,
):
    return await service.get_batch_stats(batch_id)


@router.post("/{batch_id}/aggregate-async", status_code=202, response_model=TaskResponse)
async def aggregate_async(
    batch_id: int,
    data: AggregateAsyncRequest,
    current_user: CurrentUser,
):
    task = aggregate_products_batch.delay(batch_id, data.unique_codes, current_user.id)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Aggregation task started",
    )


@router.post("/{batch_id}/reports", status_code=202, response_model=TaskResponse)
async def create_report(
    batch_id: int,
    data: ReportRequest,
    _: CurrentUser,
):
    task = generate_batch_report.delay(batch_id, data.format, data.email)
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Report generation started",
    )
