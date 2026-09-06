"""Bounded, isolated synthetic allocation measurement. Owner M5; no MQTT import."""

import platform
import random
import statistics
import time
from .allocator import Demand, allocate


def benchmark(members: int, seed: int = 42, samples: int = 200) -> dict:
    if type(members) is not int or not 1 <= members <= 5000 or not 1 <= samples <= 200:
        raise ValueError("benchmark size/sample bound exceeded")
    rng = random.Random(seed)
    offers = [Demand(f"m{i}", 100, rng.randint(150, 2000)) for i in range(members)]
    cap = members * 500
    for _ in range(20):
        allocate(offers, cap)
    elapsed = []
    deadline = time.monotonic() + 10
    for _ in range(samples):
        if time.monotonic() >= deadline:
            break
        start = time.perf_counter_ns()
        allocate(offers, cap)
        elapsed.append((time.perf_counter_ns() - start) / 1e6)
    ordered = sorted(elapsed)
    return {
        "members": members,
        "seed": seed,
        "samples_ms": elapsed,
        "complete": len(elapsed) == samples,
        "median_ms": statistics.median(elapsed) if elapsed else None,
        "p95_ms": ordered[max(0, int(len(ordered) * 0.95 + 0.999) - 1)]
        if ordered
        else None,
        "python": platform.python_version(),
        "os": platform.platform(),
        "timer": "perf_counter_ns",
        "scope": "synthetic pure allocator, validation/transport excluded",
        "warmups": 20,
    }
