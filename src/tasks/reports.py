import asyncio
import os
from datetime import datetime, timezone

from celery_app import celery_app
from core.database import async_session_maker
from data.repositories.batch_repository import BatchRepository
from data.repositories.product_repository import ProductRepository
from data.repositories.webhook_repository import WebhookRepository
from domain.services.webhook_service import WebhookService
from storage.minio_service import minio_service
from utils.excel_generator import generate_batch_excel
from utils.pdf_generator import generate_batch_pdf


@celery_app.task(bind=True, max_retries=3)
def generate_batch_report(
    self,
    batch_id: int,
    format: str = "excel",
    user_email: str | None = None,
):
    return asyncio.run(_generate(self, batch_id, format, user_email))


async def _generate(task, batch_id: int, format: str, user_email: str | None):
    async with async_session_maker() as session:
        batch_repo = BatchRepository(session)
        product_repo = ProductRepository(session)

        batch = await batch_repo.get_by_id(batch_id)
        if batch is None:
            return {"success": False, "error": "Batch not found"}

        products = await product_repo.get_by_batch_id(batch_id)

    try:
        if format == "excel":
            file_path = generate_batch_excel(batch, products)
            ext = "xlsx"
        elif format == "pdf":
            file_path = generate_batch_pdf(batch, products)
            ext = "pdf"
        else:
            return {"success": False, "error": f"Format '{format}' not supported"}

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        object_name = f"batch_{batch_id}_report_{timestamp}.{ext}"

        minio_service.ensure_buckets()
        file_url = minio_service.upload_file(
            bucket="reports",
            file_path=file_path,
            object_name=object_name,
            expires_days=7,
        )

        file_size = os.path.getsize(file_path)
        os.remove(file_path)

        expires_at = datetime.now(timezone.utc).isoformat()
        result = {
            "success": True,
            "file_url": file_url,
            "file_name": object_name,
            "file_size": file_size,
            "expires_at": expires_at,
        }

        async with async_session_maker() as session:
            webhook_service = WebhookService(repo=WebhookRepository(session))
            await webhook_service.dispatch("report_generated", {
                "batch_id": batch_id,
                "report_type": format,
                "file_url": file_url,
                "expires_at": expires_at,
            })

        return result

    except Exception as exc:
        raise task.retry(exc=exc)
