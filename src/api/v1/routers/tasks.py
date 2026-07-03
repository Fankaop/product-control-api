from celery.result import AsyncResult
from fastapi import APIRouter

from api.v1.schemas.task import TaskStatusResponse
from core.dependencies import CurrentUser

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, _: CurrentUser):
    result = AsyncResult(task_id)
    return TaskStatusResponse(
        task_id=task_id,
        status=result.status,
        result=result.result if result.ready() else result.info,
    )