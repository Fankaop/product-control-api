from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from core.config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(str(settings.database_url),
                            pool_size=settings.database_pool_size,
                            echo = settings.debug)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_= AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

            
async def dispose_engine() -> None:
    """Закрыть все соединения с БД."""
    await engine.dispose()