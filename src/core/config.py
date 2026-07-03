from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = 'Product Control API'
    environment: Literal["development", "staging", "production"]
    database_url: PostgresDsn
    redis_url: RedisDsn
    celery_broker_url: str
    celery_result_backend: str
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_pool_size: int = 20
    debug: bool = True
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False


    model_config = SettingsConfigDict(
        env_file='.env',
        case_sensitive=False
    )
    @property
    def is_production(self) -> bool:
        return self.environment == 'production'

@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore

settings = get_settings()
