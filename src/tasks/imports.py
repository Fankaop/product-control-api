import asyncio
import os

from celery_app import celery_app
from core.database import async_session_maker
from data.repositories.batch_repository import BatchRepository
from data.repositories.webhook_repository import WebhookRepository
from domain.services.webhook_service import WebhookService
from storage.minio_service import minio_service
from utils.excel_parser import parse_csv, parse_excel


@celery_app.task(bind=True, max_retries=1)
def import_batches_from_file(self, file_url: str, object_name: str, user_id: int | None = None):
    return asyncio.run(_import(self, file_url, object_name, user_id))


async def _import(task, file_url: str, object_name: str, user_id: int | None):
    local_path = f"/tmp/{object_name}"

    try:
        minio_service.download_file(bucket="imports", object_name=object_name, file_path=local_path)
    except Exception as exc:
        return {"success": False, "error": f"Failed to download file: {exc}"}

    try:
        if object_name.endswith(".csv"):
            records, parse_errors = parse_csv(local_path)
        else:
            records, parse_errors = parse_excel(local_path)
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

    total = len(records) + len(parse_errors)
    created = 0
    skipped = 0
    errors = list(parse_errors)

    async with async_session_maker() as session:
        repo = BatchRepository(session)

        for i, record in enumerate(records):
            try:
                work_center = await repo.get_or_create_work_center(
                    identifier=record.get("work_center_identifier", ""),
                    name=record.get("work_center_name", ""),
                )
                await repo.create(
                    batch_number=record["batch_number"],
                    batch_date=record["batch_date"],
                    nomenclature=record["nomenclature"],
                    ekn_code=record.get("ekn_code", ""),
                    task_description=record.get("task_description", ""),
                    shift=record.get("shift", ""),
                    team=record.get("team", ""),
                    shift_start=record["shift_start"],
                    shift_end=record["shift_end"],
                    work_center_id=work_center.id,
                )
                created += 1

            except Exception as exc:
                skipped += 1
                errors.append({"row": i + 2, "error": str(exc)})

            task.update_state(
                state="PROGRESS",
                meta={
                    "current": i + 1,
                    "total": len(records),
                    "created": created,
                    "skipped": skipped,
                },
            )

    result = {
        "success": True,
        "total_rows": total,
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }

    async with async_session_maker() as session:
        webhook_service = WebhookService(repo=WebhookRepository(session))
        await webhook_service.dispatch("import_completed", {
            "total_rows": total,
            "created": created,
            "skipped": skipped,
            "errors": errors[:10],
        })

    return result
