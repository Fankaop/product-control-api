from fastapi import APIRouter, Depends
from typing import Annotated

from api.v1.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from core.dependencies import CurrentUser, get_auth_service
from domain.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, service: AuthServiceDep):
    user = await service.register(email=data.email, password=data.password)
    return UserResponse(id=user.id, email=user.email, is_active=user.is_active)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, service: AuthServiceDep):
    token = await service.login(email=data.email, password=data.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return UserResponse(id=current_user.id, email=current_user.email, is_active=current_user.is_active)
