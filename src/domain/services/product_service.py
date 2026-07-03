from datetime import datetime

from data.models.product import Product
from data.repositories import BatchRepository, ProductRepository
from domain.exceptions import BatchNotFound, ProductAlreadyAggregated
from domain.exceptions.product import ProductNotFound


class ProductService:
    def __init__(self, repo: ProductRepository, batch_repo: BatchRepository) -> None:
        self.repo = repo
        self.batch_repo = batch_repo

    async def add_product(self, batch_id: int, unique_code: str) -> Product:
        batch = await self.batch_repo.get_by_id(batch_id)
        if batch is None:
            raise BatchNotFound(batch_id)
        return await self.repo.create(
            batch_id=batch_id,
            unique_code=unique_code
        )
    async def aggregate_product(self, batch_id: int, unique_code: str) -> Product:
        product = await self.repo.get_by_unique_code(unique_code)
        if product is None:
            raise ProductNotFound(unique_code)
        if product.batch_id != batch_id:
            raise ProductNotFound(unique_code)
        if product.is_aggregated:
            raise ProductAlreadyAggregated(unique_code)
        updated = await self.repo.update(
            product.id,
            is_aggregated=True,
            aggregated_at=datetime.utcnow(),
        )
        if updated is None:
            raise RuntimeError(f"Product {unique_code} disappeared during aggregation")
        return updated
        