import asyncio
import fakeredis.aioredis
import pytest
from app.from_scratch.rate_limiter import InMemoryRateLimiter, RedisRateLimiter

@pytest.mark.asyncio
async def test_in_memory_allows_within_limit():
    rl = InMemoryRateLimiter(max_tokens=3, refill_rate=1.0)
    for _ in range(3):
        (ok, headers) = await rl.allow_request('user-1')
        assert ok is True
        assert headers['X-RateLimit-Limit'] == '3'

@pytest.mark.asyncio
async def test_in_memory_denies_when_exhausted():
    rl = InMemoryRateLimiter(max_tokens=2, refill_rate=0.5)
    await rl.allow_request('user-1')
    await rl.allow_request('user-1')
    (ok, headers) = await rl.allow_request('user-1')
    assert ok is False
    assert headers['X-RateLimit-Remaining'] == '0'
    assert 'Retry-After' in headers

@pytest.mark.asyncio
async def test_in_memory_refills_after_wait():
    rl = InMemoryRateLimiter(max_tokens=1, refill_rate=10.0)
    (ok, _) = await rl.allow_request('u')
    assert ok
    (ok, _) = await rl.allow_request('u')
    assert not ok
    await asyncio.sleep(0.15)
    (ok, _) = await rl.allow_request('u')
    assert ok

@pytest.mark.asyncio
async def test_in_memory_isolates_clients():
    rl = InMemoryRateLimiter(max_tokens=1, refill_rate=0.1)
    (a_ok, _) = await rl.allow_request('A')
    (b_ok, _) = await rl.allow_request('B')
    (a_again, _) = await rl.allow_request('A')
    assert a_ok and b_ok and (not a_again)

@pytest.mark.asyncio
async def test_redis_limiter_basic_flow():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    rl = RedisRateLimiter(redis, max_tokens=2, refill_rate=1.0)
    (ok1, _) = await rl.allow_request('u')
    (ok2, _) = await rl.allow_request('u')
    (ok3, headers) = await rl.allow_request('u')
    assert ok1 and ok2
    assert not ok3
    assert headers['X-RateLimit-Limit'] == '2'
    assert 'Retry-After' in headers

@pytest.mark.asyncio
async def test_redis_limiter_refills():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    rl = RedisRateLimiter(redis, max_tokens=1, refill_rate=10.0)
    assert (await rl.allow_request('u'))[0]
    assert not (await rl.allow_request('u'))[0]
    await asyncio.sleep(0.15)
    assert (await rl.allow_request('u'))[0]
