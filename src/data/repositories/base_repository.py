


from sqlalchemy import select
from typing import Generic, Type, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession


T = TypeVar('T')

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_by_id(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def update(self, id: int, **kwargs) -> T | None:
        obj = await self.session.get(self.model, id)
        if obj is None:
            return None
        for key, value in kwargs.items():
            setattr(obj, key, value)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, id: int)-> bool:
        obj = await self.session.get(self.model, id)
        if obj is None:
            return False
        await self.session.delete(obj)
        await self.session.commit()
        return True

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())