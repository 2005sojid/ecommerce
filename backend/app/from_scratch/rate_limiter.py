import time
from dataclasses import dataclass
from typing import Protocol
import redis.asyncio as aioredis

class RateLimiter(Protocol):

    async def allow_request(self, client_id: str) -> tuple[bool, dict[str, str]]:
        ...

@dataclass
class _Bucket:
    tokens: float
    last_refill: float

class InMemoryRateLimiter:

    def __init__(self, max_tokens: int=60, refill_rate: float=1.0) -> None:
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self._buckets: dict[str, _Bucket] = {}

    def _refill(self, b: _Bucket) -> None:
        now = time.monotonic()
        elapsed = now - b.last_refill
        b.tokens = min(self.max_tokens, b.tokens + elapsed * self.refill_rate)
        b.last_refill = now

    async def allow_request(self, client_id: str) -> tuple[bool, dict[str, str]]:
        b = self._buckets.get(client_id)
        if b is None:
            b = _Bucket(tokens=float(self.max_tokens), last_refill=time.monotonic())
            self._buckets[client_id] = b
        else:
            self._refill(b)
        if b.tokens >= 1:
            b.tokens -= 1
            return (True, {'X-RateLimit-Limit': str(self.max_tokens), 'X-RateLimit-Remaining': str(int(b.tokens))})
        return (False, {'X-RateLimit-Limit': str(self.max_tokens), 'X-RateLimit-Remaining': '0', 'Retry-After': str(max(1, int(1 / self.refill_rate)))})
_LUA_SCRIPT = "\nlocal key = KEYS[1]\nlocal max_tokens   = tonumber(ARGV[1])\nlocal refill_rate  = tonumber(ARGV[2])\nlocal now          = tonumber(ARGV[3])\n\nlocal data = redis.call('HMGET', key, 'tokens', 'last_refill')\nlocal tokens      = tonumber(data[1]) or max_tokens\nlocal last_refill = tonumber(data[2]) or now\n\nlocal elapsed = now - last_refill\nif elapsed < 0 then elapsed = 0 end\ntokens = math.min(max_tokens, tokens + elapsed * refill_rate)\n\nlocal allowed = 0\nif tokens >= 1 then\n    tokens = tokens - 1\n    allowed = 1\nend\n\nredis.call('HSET', key, 'tokens', tokens, 'last_refill', now)\nredis.call('EXPIRE', key, math.ceil(max_tokens / refill_rate) + 10)\n\nreturn {allowed, tostring(tokens)}\n"

class RedisRateLimiter:

    def __init__(self, redis_client: aioredis.Redis, max_tokens: int=60, refill_rate: float=1.0, prefix: str='ratelimit') -> None:
        self.redis = redis_client
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.prefix = prefix

    async def allow_request(self, client_id: str) -> tuple[bool, dict[str, str]]:
        key = f'{self.prefix}:{client_id}'
        now = time.time()
        result = await self.redis.eval(_LUA_SCRIPT, 1, key, self.max_tokens, self.refill_rate, now)
        allowed = bool(int(result[0]))
        remaining = int(float(result[1]))
        headers = {'X-RateLimit-Limit': str(self.max_tokens), 'X-RateLimit-Remaining': str(max(remaining, 0))}
        if not allowed:
            headers['Retry-After'] = str(max(1, int(1 / self.refill_rate)))
        return (allowed, headers)
