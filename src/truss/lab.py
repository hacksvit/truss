"""Bounded, isolated synthetic allocation measurement. Owner M5; no MQTT import."""

import platform
import random
import statistics
import time
from .allocator import Demand, allocate
from .validator import validate_proposal
from fractions import Fraction


def benchmark(
    members: int,
    seed: int = 42,
    samples: int = 200,
    distribution="uniform",
    rule="equal_surplus",
    cap_ratio=0.5,
) -> dict:
    if type(members) is not int or not 1 <= members <= 5000 or not 1 <= samples <= 200:
        raise ValueError("benchmark size/sample bound exceeded")
    if (
        distribution not in ("uniform", "saturated", "skewed")
        or rule not in ("equal_surplus", "debt_weighted_surplus")
        or not 0 <= cap_ratio <= 1
    ):
        raise ValueError("invalid benchmark scenario")
    rng = random.Random(seed)
    offers = []
    for i in range(members):
        useful = (
            rng.randint(150, 2000)
            if distribution == "uniform"
            else 150
            if distribution == "saturated"
            else 10000
            if i % 10 == 0
            else 150
        )
        weight = (
            Fraction(rng.randint(100, 200), 100)
            if rule == "debt_weighted_surplus"
            else Fraction(1)
        )
        offers.append(Demand(f"m{i}", 100, useful, weight))
    cap = members * 100 + int(sum(d.useful_w - d.floor_w for d in offers) * cap_ratio)
    for _ in range(20):
        allocate(offers, cap)
    elapsed = []
    validation, totals = [], []
    deadline = time.monotonic() + 10
    for _ in range(samples):
        if time.monotonic() >= deadline:
            break
        start = time.perf_counter_ns()
        proposal = allocate(offers, cap)
        allocated = time.perf_counter_ns()
        if not proposal.feasible or validate_proposal(offers, proposal.budgets, cap, 0):
            raise ValueError("benchmark proposal validation failed")
        finished = time.perf_counter_ns()
        elapsed.append((allocated - start) / 1e6)
        validation.append((finished - allocated) / 1e6)
        totals.append((finished - start) / 1e6)
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
        "distribution": distribution,
        "rule": rule,
        "cap_ratio": cap_ratio,
        "validation_samples_ms": validation,
        "total_samples_ms": totals,
        "requested_samples": samples,
    }
