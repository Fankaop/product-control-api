import asyncio
from datetime import datetime, timezone
from celery_app import celery_app
from core.database import async_session_maker
from data.repositories import BatchRepository, ProductRepository

@celery_app.task(bind=True, max_retries=3)
def aggregate_products_batch(self, batch_id: int, unique_codes: list[str], user_id: int | None = None):
    return asyncio.run(_aggregate(self, batch_id, unique_codes, user_id))

async def _aggregate(task, batch_id: int, unique_codes: list[str], user_id: int | None = None):
    async with async_session_maker() as session:
        product_repo = ProductRepository(session)
        batch_repo = BatchRepository(session)
        if await batch_repo.get_by_id(batch_id) is None:
            return {'success': False, 'error': 'Batch not found'}
        errors = []
        aggregated = 0
        for i, uniq in enumerate(unique_codes):
            product = await product_repo.get_by_unique_code(uniq)
            if product is None:
                errors.append({'code': uniq, 'reason': 'not found'})
            elif product.is_aggregated:
                errors.append({'code': uniq, 'reason': 'already aggregated'})
            else:
                await product_repo.update(product.id, is_aggregated=True, aggregated_at=datetime.now(timezone.utc).replace(tzinfo=None))
                aggregated += 1

            task.update_state(
                state='PROGRESS',
                meta={
                    'current': i + 1,
                    'total': len(unique_codes),
                    'progress': round((i + 1) / len(unique_codes) * 100, 2),
                }
            )

        await session.commit()
        return {
            "success": True,
            "total": len(unique_codes),
            "aggregated": aggregated,
            "failed": len(errors),
            "errors": errors,
        }