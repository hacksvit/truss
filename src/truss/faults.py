"""Bounded deterministic delivery faults. Owner M2. Does not alter authority clocks."""

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class DeliveryFault:
    action: str
    until_ns: int
    rate: float = 0.0
    delay_ms: int = 0

    def __post_init__(self):
        if (
            self.action
            not in ("partition", "drop_acks", "delay_telemetry", "delay_grants")
            or not 0 <= self.rate <= 1
            or not 0 <= self.delay_ms <= 10000
        ):
            raise ValueError("invalid delivery fault")


def delivery_decision(
    fault: DeliveryFault | None, topic: str, now_ns: int, rng: Random
) -> tuple[str, int]:
    if not fault or now_ns >= fault.until_ns:
        return "pass", 0
    if fault.action == "partition" or (
        fault.action == "drop_acks"
        and topic.endswith("/ack")
        and rng.random() < fault.rate
    ):
        return "drop", 0
    if fault.action == "delay_telemetry" and topic.endswith(("/telemetry", "/meter")):
        return "delay", fault.delay_ms
    if fault.action == "delay_grants" and topic.endswith("/lease"):
        return "delay", fault.delay_ms
    return "pass", 0
