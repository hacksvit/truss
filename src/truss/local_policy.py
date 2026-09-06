"""Household-local assignment; only flexible output can yield. Owner M3."""

from .config import MemberProfile


def assign(profile: MemberProfile, budget_w: int) -> dict[str, int]:
    baseline = sum(d.baseline_w for d in profile.devices)
    if budget_w < baseline:
        raise ValueError("budget cannot preserve registered device baselines")
    result = {d.device_id: d.baseline_w for d in profile.devices}
    remaining = budget_w - baseline
    for device in sorted(profile.devices, key=lambda d: (-d.priority, d.device_id)):
        if device.control_policy != "flexible":
            continue
        step = device.max_w - device.baseline_w
        if device.actuation == "binary":
            # A button, not a dial: it runs at its maximum or not at all. Taking
            # a partial step is not physically available, so an unaffordable
            # device is skipped and a lower-priority one may still fit.
            extra = step if step <= remaining else 0
        else:
            extra = min(remaining, step)
        result[device.device_id] += extra
        remaining -= extra
    return result


def unusable_w(profile: MemberProfile, budget_w: int) -> int:
    """Watts the household is allowed to draw but cannot reach.

    Always zero while every flexible device modulates. Binary devices leave a
    remainder too small for their whole step; that stranded capacity is real
    and is reported rather than hidden.
    """
    return budget_w - sum(assign(profile, budget_w).values())
