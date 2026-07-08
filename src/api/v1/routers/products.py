from fastapi import APIRouter

from api.v1.schemas.product import AggregateRequest, ProductCreate, ProductResponse
from core.dependencies import CurrentUser, ProductServiceDep, WebhookServiceDep

router = APIRouter(tags=["products"])


@router.post("/products", status_code=201, response_model=ProductResponse)
async def add_product(
    data: ProductCreate,
    service: ProductServiceDep,
    _: CurrentUser,
):
    return await service.add_product(batch_id=data.batch_id, unique_code=data.unique_code)


@router.post("/batches/{batch_id}/aggregate", response_model=ProductResponse)
async def aggregate_product(
    batch_id: int,
    data: AggregateRequest,
    service: ProductServiceDep,
    webhook_service: WebhookServiceDep,
    _: CurrentUser,
):
    product = await service.aggregate_product(batch_id=batch_id, unique_code=data.unique_code)
    await webhook_service.dispatch("product_aggregated", {
        "unique_code": product.unique_code,
        "batch_id": batch_id,
        "aggregated_at": product.aggregated_at.isoformat() if product.aggregated_at else None,
    })
    return product
