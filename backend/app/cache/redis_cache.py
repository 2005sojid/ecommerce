import json
import logging
from functools import wraps
from typing import Any, Callable
import redis.asyncio as redis
from app.config import settings
logger = logging.getLogger(__name__)
redis_client: redis.Redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_redis() -> redis.Redis:
    return redis_client

def _key_pattern(key: str) -> str:
    return key.split(':', 1)[0]

async def cache_get(key: str) -> Any | None:
    try:
        raw = await redis_client.get(key)
    except Exception as exc:
        logger.warning('cache_get(%s) failed: %s', key, exc)
        return None
    from app.metrics import cache_ops
    if raw is None:
        cache_ops.labels(op='miss', key_pattern=_key_pattern(key)).inc()
        return None
    cache_ops.labels(op='hit', key_pattern=_key_pattern(key)).inc()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

async def cache_set(key: str, value: Any, ttl: int=300) -> None:
    try:
        await redis_client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as exc:
        logger.warning('cache_set(%s) failed: %s', key, exc)

async def cache_delete(*keys: str) -> None:
    if not keys:
        return
    try:
        await redis_client.delete(*keys)
        from app.metrics import cache_ops
        for k in keys:
            cache_ops.labels(op='invalidate', key_pattern=_key_pattern(k)).inc()
    except Exception as exc:
        logger.warning('cache_delete(%s) failed: %s', keys, exc)

def cached(key_template: str, ttl: int=300) -> Callable:

    def decorator(func: Callable) -> Callable:

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                key = key_template.format(**kwargs)
            except KeyError:
                return await func(*args, **kwargs)
            hit = await cache_get(key)
            if hit is not None:
                return hit
            result = await func(*args, **kwargs)
            await cache_set(key, result, ttl)
            return result
        return wrapper
    return decorator
