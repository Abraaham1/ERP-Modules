import json
import time
import uuid

from app.core.logging import get_logger
from app.core.rate_limit import get_redis
from app.schemas.user import UserOut

logger = get_logger("cache.user")

USER_CACHE_TTL_SECONDS = 60
USER_CACHE_PREFIX = "user_cache:"


def _cache_key(user_id: uuid.UUID) -> str:
    return f"{USER_CACHE_PREFIX}{user_id}"


async def get_cached_user(user_id: uuid.UUID) -> dict | None:
    client = get_redis()
    key = _cache_key(user_id)

    start = time.perf_counter()
    raw = await client.get(key)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if raw is None:
        logger.info("CACHE MISS  (%.2fms)", elapsed_ms)
        return None

    logger.info("CACHE HIT   (%.2fms)", elapsed_ms)
    return json.loads(raw)


async def set_cached_user(user_id: uuid.UUID, user_out: UserOut) -> None:
    client = get_redis()
    key = _cache_key(user_id)
    payload = user_out.model_dump(mode="json")

    start = time.perf_counter()
    await client.set(key, json.dumps(payload), ex=USER_CACHE_TTL_SECONDS)
    elapsed_ms = (time.perf_counter() - start) * 1000

    logger.info("CACHE SET   (%.2fms) ttl=%ss", elapsed_ms, USER_CACHE_TTL_SECONDS)


async def invalidate_cached_user(user_id: uuid.UUID) -> None:
    client = get_redis()
    key = _cache_key(user_id)

    start = time.perf_counter()
    deleted = await client.delete(key)
    elapsed_ms = (time.perf_counter() - start) * 1000

    if deleted:
        logger.info("CACHE INVALIDATE (%.2fms)", elapsed_ms)