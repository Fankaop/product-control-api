from data.models.user import User
from data.repositories.user_repository import UserRepository
from core.exceptions import AppException
from utils.password_utils import hash_password, verify_password
from utils.jwt_utils import create_access_token


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def register(self, email: str, password: str) -> User:
        existing = await self.repo.get_by_email(email)
        if existing is not None:
            raise AppException(message="Email already registered", status_code=409)
        return await self.repo.create(email=email, hashed_password=hash_password(password))

    async def login(self, email: str, password: str) -> str:
        user = await self.repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AppException(message="Invalid email or password", status_code=401)
        if not user.is_active:
            raise AppException(message="User is inactive", status_code=403)
        return create_access_token(user.id)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.repo.get_by_id(user_id)
