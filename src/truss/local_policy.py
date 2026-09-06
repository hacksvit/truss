"""Household-local assignment; only flexible output can yield. Owner M3."""

from .config import MemberProfile


def assign(profile: MemberProfile, budget_w: int) -> dict[str, int]:
    baseline = sum(d.baseline_w for d in profile.devices)
    if budget_w < baseline:
        raise ValueError("budget cannot preserve registered device baselines")
    result = {d.device_id: d.baseline_w for d in profile.devices}
    remaining = budget_w - baseline
    for device in sorted(profile.devices, key=lambda d: (-d.priority, d.device_id)):
        if device.control_policy == "flexible":
            extra = min(remaining, device.max_w - device.baseline_w)
            result[device.device_id] += extra
            remaining -= extra
    return result
