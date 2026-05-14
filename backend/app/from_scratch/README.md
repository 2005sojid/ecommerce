# Token-Bucket Rate Limiter

This is our first from-scratch (easy one) component of the project

## Explanation
We needed a way to protect two endpoints that are particularly vulnerable to abuse: `/api/flash-sales/*/claim`, which gets abused by bots the moment a sale goes live, and `/api/auth/login`, which is a brute-force target
To deal with these problem, we need a rate limiter. The token bucket algorithm fit our needs best

## Algorithm
Bucket of capacity `max_tokens`. Tokens are refilled at the rate `refill_rate` per second.
Each request takes 1 token. If the bucket is empty, then it gives `429 Too Many Requests` with the `Retry-After` header

Refill is **lazy**: it is recalculated in place at consume time, without background tasks and timers.

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
- **Middleware** `app/middleware/rate_limit.py`. `BaseHTTPMiddleware`, applied only to the listed path prefixes.
- Client identification: when a valid JWT is present by `user_id`, otherwise by `request.client.host`.
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

## Limitations
- Clock skew between Redis and backend has minimal impact
- Redis is a single point of failure
- It does not differentiate "cheap" vs "heavy" endpoints -- exactly 1 token per request

---

# Snowflake ID Generator

A second  (harder one) from-scratch component: a 64-bit Snowflake unique ID generator (Alex Xu, System Design Interview Vol.1, Ch.7). Located in `app/from_scratch/snowflake_id.py`

## Why
There are two alternatives: UUIDv4 and Auto-Increment. Both of them have real problems at scale. UUIDv4 is 128 bits and completely random, which means every insert lands somewhere unpredictable, fragmenting the index over time in B-tree. Auto-increment integers are fine until you have more than one write node, at which point you need a single coordinator handing out IDs, and that coordinator becomes our bottleneck

Snowflake IDs solve these problems: they're 64-bit, roughly time-sortable, and globally unique with no coordinator. Each generator instance knows its own `worker_id` and never needs to talk to anyone else

## Bit layout

```
| 1 bit  | 41 bits     | 10 bits   | 12 bits   |
| sign=0 | timestamp   | worker_id | sequence  |
```

- **sign (1 bit)**: always 0 so the int fits in a signed 64-bit slot.
- **timestamp (41 bits)**: ms since a custom epoch (`2024-01-01 UTC`)
- **worker_id (10 bits)**: up to 1024 generator instances
- **sequence (12 bits)**: per-millisecond counter (0..4095).

## Concurrency
A single `threading.Lock` protects `(last_ts, sequence)`. Async callers are safe too because `generate()` does no I/O and returns immediately

## Clock skew
- **Clock moves backwards**: `generate()` raises `RuntimeError`. We refuse to mint IDs that could collide with already-issued ones.
- **NTP smear (forward jumps)**: If harmless, IDs just jump ahead a few ms

## Usage

```python
from app.from_scratch.snowflake_id import next_id, snowflake

order_id = next_id()             
order_id = snowflake.generate() 
```
