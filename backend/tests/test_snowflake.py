import os
import threading
from unittest import mock

import pytest

from app.from_scratch.snowflake_id import (
    MAX_SEQUENCE,
    MAX_WORKER_ID,
    SEQUENCE_BITS,
    WORKER_ID_BITS,
    SnowflakeGenerator,
)


def test_monotonic_increase():
    gen = SnowflakeGenerator(worker_id=1)
    prev = -1
    for _ in range(10_000):
        cur = gen.generate()
        assert cur > prev, f'IDs are not monotonically increasing: {cur} <= {prev}'
        prev = cur


def test_uniqueness():
    gen = SnowflakeGenerator(worker_id=2)
    ids = {gen.generate() for _ in range(10_000)}
    assert len(ids) == 10_000


def test_uniqueness_multithreaded():
    gen = SnowflakeGenerator(worker_id=3)
    ids: list[int] = []
    lock = threading.Lock()

    def worker():
        local: list[int] = []
        for _ in range(1000):
            local.append(gen.generate())
        with lock:
            ids.extend(local)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(set(ids)) == 10_000


def test_different_workers_dont_overlap():
    with mock.patch.dict(os.environ, {'INSTANCE_ID': '7'}):
        g7 = SnowflakeGenerator()
    with mock.patch.dict(os.environ, {'INSTANCE_ID': '42'}):
        g42 = SnowflakeGenerator()
    assert g7.worker_id == 7
    assert g42.worker_id == 42

    ids_7 = {g7.generate() for _ in range(10_000)}
    ids_42 = {g42.generate() for _ in range(10_000)}
    assert ids_7.isdisjoint(ids_42)

    worker_mask = MAX_WORKER_ID
    for x in ids_7:
        assert (x >> SEQUENCE_BITS) & worker_mask == 7
    for x in ids_42:
        assert (x >> SEQUENCE_BITS) & worker_mask == 42


def test_worker_id_masked():
    g = SnowflakeGenerator(worker_id=MAX_WORKER_ID + 5)
    assert g.worker_id == (MAX_WORKER_ID + 5) & MAX_WORKER_ID


def test_layout_constants():
    assert WORKER_ID_BITS == 10
    assert SEQUENCE_BITS == 12
    assert MAX_SEQUENCE == 4095
    assert MAX_WORKER_ID == 1023


def test_clock_backwards_raises():
    gen = SnowflakeGenerator(worker_id=1)
    gen.generate()
    gen._last_ts += 10_000  # simulate prior generation far in the future
    with pytest.raises(RuntimeError):
        gen.generate()
