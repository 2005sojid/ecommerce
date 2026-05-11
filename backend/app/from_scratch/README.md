# Token-Bucket Rate Limiter (R11)

The from-scratch component of the project.

## What and why
- **What**: a rate limiter built on the "token bucket" algorithm.
- **Why**:
  - Protects `/api/flash-sales/*/claim` from bots and abuse during a sale rush.
  - Protects `/api/auth/login` from brute-force password guessing.

## Algorithm
Bucket of capacity `max_tokens`. Tokens are refilled at the rate `refill_rate` per second.
Each request takes 1 token; if the bucket is empty -- `429 Too Many Requests` with the `Retry-After` header.

Refill is **lazy**: it is recomputed in place at consume time -- no background tasks, no timers.

```
tokens_now = min(max_tokens, tokens_prev + (now - last_refill) * refill_rate)
if tokens_now >= 1: allow,  tokens_now -= 1
else:               deny,   Retry-After = 1 / refill_rate
```

## Trade-offs
| Algorithm | Burst-friendly | Accuracy | Complexity | Memory |
|---|---|---|---|---|
| **Token bucket** | yes (accumulates up to `max_tokens`) | high | low | O(1) per client |
| Leaky bucket | no (uniform outflow) | high | medium (FIFO) | O(N) queue |
| Fixed window | no | low (2x boundary effect) | minimal | O(1) |
| Sliding window log | yes | maximum | medium | O(N) timestamps |
| Sliding window counter | yes | medium | medium | O(1) |

Token bucket was chosen as the minimally complex one that gives "honest" bursts (which matters for the flash-sale UX: the user can press the button 30 times in a row, not "once every 2 seconds").

## Integration
- **Middleware** `app/middleware/rate_limit.py` -- `BaseHTTPMiddleware`, applied only to the listed path prefixes.
- Client identification: when a valid JWT is present -- by `user_id`, otherwise by `request.client.host`.
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After` (only on 429).

## Distributed mode
`RedisRateLimiter` keeps state in Redis (`HSET ratelimit:<client> tokens=... last_refill=...`).
Atomicity of the check-and-update is ensured by a **Lua script** on the Redis side -- a single network round-trip, guaranteed atomic (`EVAL` is executed single-threaded, with no race conditions between backend replicas).

EXPIRE is set on the key automatically (`max_tokens / refill_rate + 10` seconds) -- inactive clients drop out on their own.

## Limitations
- Clock skew between Redis and backend has minimal impact (we use `time.time()` on the backend side, passed into the Lua) -- but with a large skew a mini-burst is possible after reconnect.
- Redis is a single point of failure; for HA you need Redis Sentinel/Cluster.
- It does not differentiate "cheap" vs "heavy" endpoints -- exactly 1 token per request. If desired, add a `cost` parameter to `allow_request`.

---

# Snowflake ID Generator

A second from-scratch component: a 64-bit Snowflake unique ID generator (Alex Xu, *System Design Interview Vol.1*, Ch.7). Lives in `app/from_scratch/snowflake_id.py`.

## Why
- UUIDv4 is 128 bits and not time-sortable -- bad for B-tree index locality.
- Auto-increment integers require a single source of truth -- bad for horizontally scaled write paths.
- Snowflake gives **64-bit, roughly time-sortable, globally unique** IDs without a coordinator: each generator instance has its own `worker_id` and never collides with peers.

## Bit layout

```
| 1 bit  | 41 bits     | 10 bits   | 12 bits   |
| sign=0 | timestamp   | worker_id | sequence  |
```

- **sign (1 bit)**: always 0 so the int fits in a signed 64-bit slot.
- **timestamp (41 bits)**: ms since a custom epoch (`2024-01-01 UTC`). ~69 years of range.
- **worker_id (10 bits)**: up to 1024 generator instances. Sourced from `INSTANCE_ID` env var.
- **sequence (12 bits)**: per-millisecond counter (0..4095). On overflow within the same ms we spin until the next ms -> monotonicity preserved.

## Concurrency
A single `threading.Lock` protects `(last_ts, sequence)`. Async callers are safe too because `generate()` does no I/O and returns immediately.

## Clock skew
- **Clock moves backwards**: `generate()` raises `RuntimeError`. We refuse to mint IDs that could collide with already-issued ones.
- **NTP smear (forward jumps)**: harmless -- IDs just jump ahead a few ms.

## Usage

```python
from app.from_scratch.snowflake_id import next_id, snowflake

order_id = next_id()             # module-level singleton
order_id = snowflake.generate()  # equivalent
```

## Tests
See `tests/test_snowflake.py`: monotonicity, uniqueness (single- and multi-threaded), worker_id isolation, clock-backwards behaviour, layout constants.
