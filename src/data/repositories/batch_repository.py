from sqlalchemy import select
from sqlalchemy.orm import joinedload

from core.database import AsyncSession
from data.models.batch import Batch
from data.models.work_center import WorkCenter
from data.repositories import BaseRepository


class BatchRepository(BaseRepository[Batch]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Batch)
    
    async def get_with_products(self, batch_id: int) -> Batch | None:
        result = await self.session.execute(
            select(Batch).options(joinedload(Batch.products)).where(Batch.id == batch_id)
        )
        return result.unique().scalars().first()

    async def get_many(
        self,
        is_closed: bool | None = None,
        batch_number: int | None = None,
        batch_date: str | None = None,
        work_center_id: int | None = None,
        shift: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Batch]:
        query = select(Batch)
        if is_closed is not None:
            query = query.where(Batch.is_closed == is_closed)
        if batch_number is not None:
            query = query.where(Batch.batch_number == batch_number)
        if batch_date is not None:
            query = query.where(Batch.batch_date == batch_date)
        if work_center_id is not None:
            query = query.where(Batch.work_center_id == work_center_id)
        if shift is not None:
            query = query.where(Batch.shift == shift)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_or_create_work_center(self, identifier: str, name: str) -> WorkCenter:
        result = await self.session.execute(
            select(WorkCenter).where(WorkCenter.identifier == identifier)
        )
        work_center = result.scalar_one_or_none()
        if work_center is None:
            work_center = WorkCenter(name=name, identifier=identifier)
            self.session.add(work_center)
            await self.session.flush()
        return work_center
