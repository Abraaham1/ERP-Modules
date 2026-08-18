import redis.asyncio as redis

from app.core.config import settings

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def check_login_rate_limit(identifier: str) -> bool:

    client = get_redis()
    key = f"login_attempts:{identifier}"

    attempts = await client.incr(key)
    if attempts == 1:
        await client.expire(key, settings.login_rate_limit_window_seconds)

    return attempts <= settings.login_rate_limit_attempts


async def reset_login_rate_limit(identifier: str) -> None:
    client = get_redis()
    await client.delete(f"login_attempts:{identifier}")
