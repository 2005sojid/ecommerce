"""Snowflake ID generator (Alex Xu, System Design Vol.1 Ch.7).

A Snowflake ID is a 64-bit integer composed of:

    | 1 bit  | 41 bits     | 10 bits   | 12 bits   |
    | sign=0 | timestamp   | worker_id | sequence  |

- sign       : always 0 -> the integer fits in a signed 64-bit slot.
- timestamp  : milliseconds since a custom epoch (2024-01-01 UTC).
                41 bits gives ~69 years of room.
- worker_id  : identifies the generator instance (0..1023).
- sequence   : per-millisecond counter (0..4095). When it overflows we spin
                until the next millisecond, guaranteeing monotonicity.

Properties:
- Monotonically increasing within a single generator.
- Globally unique across up to 1024 generators (distinct worker_id).
- Roughly time-sortable; can be decoded back into its parts.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone

CUSTOM_EPOCH_MS = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)

WORKER_ID_BITS = 10
SEQUENCE_BITS = 12

MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1

WORKER_ID_SHIFT = SEQUENCE_BITS
TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS


def _now_ms() -> int:
    return int(time.time() * 1000)


class SnowflakeGenerator:
    def __init__(self, worker_id: int | None = None, epoch_ms: int = CUSTOM_EPOCH_MS) -> None:
        if worker_id is None:
            worker_id = int(os.environ.get('INSTANCE_ID', '1'))
        self.worker_id = worker_id & MAX_WORKER_ID
        self.epoch_ms = epoch_ms
        self._sequence = 0
        self._last_ts = -1
        self._lock = threading.Lock()

    def _wait_next_ms(self, last_ts: int) -> int:
        ts = _now_ms()
        while ts <= last_ts:
            ts = _now_ms()
        return ts

    def generate(self) -> int:
        with self._lock:
            ts = _now_ms()
            if ts < self._last_ts:
                raise RuntimeError(
                    f'Clock moved backwards. Refusing to generate id for {self._last_ts - ts} ms.'
                )
            if ts == self._last_ts:
                self._sequence = (self._sequence + 1) & MAX_SEQUENCE
                if self._sequence == 0:
                    ts = self._wait_next_ms(self._last_ts)
            else:
                self._sequence = 0
            self._last_ts = ts
            delta = ts - self.epoch_ms
            return (delta << TIMESTAMP_SHIFT) | (self.worker_id << WORKER_ID_SHIFT) | self._sequence


snowflake = SnowflakeGenerator()


def next_id() -> int:
    return snowflake.generate()
