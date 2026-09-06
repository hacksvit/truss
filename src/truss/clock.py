"""Injectable monotonic time. Owner M3. Wall time is never control authority."""

import time
from pathlib import Path
from typing import Protocol


class Clock(Protocol):
    def now_ns(self) -> int: ...


class SystemClock:
    def now_ns(self) -> int:
        return time.monotonic_ns()


class FakeClock:
    def __init__(self, now_ns: int = 0):
        self.value = now_ns

    def now_ns(self) -> int:
        return self.value

    def advance_ms(self, ms: int):
        if ms < 0:
            raise ValueError("monotonic time cannot go backward")
        self.value += ms * 1_000_000


def domain_id() -> str:
    """Linux host boot ID; fail closed instead of inventing a shared domain."""
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
