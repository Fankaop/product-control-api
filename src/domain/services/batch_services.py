import json
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from api.v1.schemas.batch import BatchCreate, BatchUpdate, BatchResponse
from data.models.batch import Batch
from data.repositories.batch_repository import BatchRepository
from domain.exceptions import BatchNotFound, DuplicateBatch
from core.cache import get_cached, set_cached, invalidate, invalidate_pattern


class BatchService:
    def __init__(self, repo: BatchRepository) -> None:
        self.repo = repo

    async def create_batches(self, batches: list[BatchCreate]) -> list[Batch]:
        result = []
        for batch_data in batches:
            work_center = await self.repo.get_or_create_work_center(
                identifier=batch_data.work_center_identifier,
                name=batch_data.work_center_name,
            )
            try:
                batch = await self.repo.create(
                    is_closed=batch_data.is_closed,
                    task_description=batch_data.task_description,
                    work_center_id=work_center.id,
                    shift=batch_data.shift,
                    team=batch_data.team,
                    batch_number=batch_data.batch_number,
                    batch_date=batch_data.batch_date,
                    nomenclature=batch_data.nomenclature,
                    ekn_code=batch_data.ekn_code,
                    shift_start=batch_data.shift_start.replace(tzinfo=None),
                    shift_end=batch_data.shift_end.replace(tzinfo=None),
                )
                result.append(batch)
            except IntegrityError:
                await self.repo.session.rollback()
                raise DuplicateBatch(
                    batch_number=batch_data.batch_number,
                    batch_date=str(batch_data.batch_date),
                )
        await invalidate("dashboard_stats")
        await invalidate_pattern("batches_list:*")
        return result

    async def get_batch_with_products(self, batch_id: int) -> BatchResponse:
        cached = await get_cached(f"batch_detail:{batch_id}")
        if cached:
            return BatchResponse.model_validate_json(cached)
        batch = await self.repo.get_with_products(batch_id)
        if batch is None:
            raise BatchNotFound(batch_id)
        response = BatchResponse.model_validate(batch)
        await set_cached(f"batch_detail:{batch_id}", response.model_dump_json(), ttl=600)
        return response

    async def get_batch(self, batch_id: int) -> Batch:
        res = await self.repo.get_by_id(batch_id)
        if res is None:
            raise BatchNotFound(batch_id)
        return res

    async def update_batch(self, batch_id: int, data: BatchUpdate) -> Batch:
        batch = await self.repo.get_by_id(batch_id)
        if batch is None:
            raise BatchNotFound(batch_id)

        update_data = data.model_dump(exclude_none=True)

        if "is_closed" in update_data:
            if update_data["is_closed"] is True:
                update_data["closed_at"] = datetime.utcnow()
            else:
                update_data["closed_at"] = None

        updated = await self.repo.update(batch_id, **update_data)
        if updated is None:
            raise RuntimeError(f"Batch {batch_id} disappeared during update")
        await invalidate(f"batch_detail:{batch_id}")
        await invalidate(f"batch_statistics:{batch_id}")
        await invalidate("dashboard_stats")
        await invalidate_pattern("batches_list:*")
        return updated

    async def get_batches(self, **filters) -> list[BatchResponse]:
        cache_key = f"batches_list:{json.dumps(filters, default=str, sort_keys=True)}"
        cached = await get_cached(cache_key)
        if cached:
            data = json.loads(cached)
            return [BatchResponse.model_validate(item) for item in data]

        batches = await self.repo.get_many(**filters)
        responses = [BatchResponse.model_validate(b) for b in batches]
        await set_cached(cache_key, json.dumps([r.model_dump(mode="json") for r in responses]), ttl=60)
        return responses
