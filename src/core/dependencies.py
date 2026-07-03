from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from data.models.user import User
from data.repositories import BatchRepository, ProductRepository
from data.repositories.user_repository import UserRepository
from data.repositories.webhook_repository import WebhookRepository
from domain.services.analytics_service import AnalyticsService
from domain.services.auth_service import AuthService
from domain.services.batch_services import BatchService
from domain.services.product_service import ProductService
from domain.services.webhook_service import WebhookService
from utils.jwt_utils import decode_access_token

DBSession = Annotated[AsyncSession, Depends(get_db)]
_bearer = HTTPBearer()


async def get_current_user(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def get_auth_service(db: DBSession) -> AuthService:
    return AuthService(repo=UserRepository(db))

def get_batch_service(db: DBSession) -> BatchService:
    return BatchService(repo=BatchRepository(db))

def get_product_service(db: DBSession) -> ProductService:
    return ProductService(repo=ProductRepository(db), batch_repo=BatchRepository(db))

def get_analytics_service(db: DBSession) -> AnalyticsService:
    return AnalyticsService(session=db)

def get_webhook_service(db: DBSession) -> WebhookService:
    return WebhookService(repo=WebhookRepository(db))


CurrentUser = Annotated[User, Depends(get_current_user)]
BatchServiceDep = Annotated[BatchService, Depends(get_batch_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
WebhookServiceDep = Annotated[WebhookService, Depends(get_webhook_service)]
