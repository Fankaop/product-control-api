from data.models.product import Product
from data.repositories import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product)

    async def get_by_unique_code(self, unique_code:str) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.unique_code==unique_code)
        )
        return result.scalar_one_or_none()
    
    async def get_by_batch_id(self, batch_id: int) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(Product.batch_id==batch_id)
        )
        return list(result.scalars().all())