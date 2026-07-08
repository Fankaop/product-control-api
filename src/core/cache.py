import redis.asyncio as redis
from core.config import settings

redis_client = redis.from_url(str(settings.redis_url), decode_responses=True)

async def get_cached(key:str) -> str | None:
    return await redis_client.get(key)

async def set_cached(key: str, value: str, ttl: int)-> None:
    await redis_client.set(key, value, ex=ttl)

async def invalidate(key: str) -> None:
    await redis_client.delete(key)


async def invalidate_pattern(pattern: str) -> None:
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)
