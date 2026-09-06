"""Independent plan checks. Owner M1. Deliberately does not import allocator."""

from collections.abc import Mapping, Sequence


def validate_proposal(
    offers: Sequence, budgets: Mapping[str, int], cap_w: int, reserve_w: int = 0
) -> list[str]:
    errors = []
    expected = {o.member_id: o for o in offers}
    if len(expected) != len(offers) or set(budgets) != set(expected):
        errors.append("membership_mismatch")
    for member, budget in budgets.items():
        if type(budget) is not int or member not in expected:
            errors.append("invalid_amount")
        elif not expected[member].floor_w <= budget <= expected[member].useful_w:
            errors.append("outside_envelope")
    if not errors and sum(budgets.values()) + reserve_w > cap_w:
        errors.append("cap_exceeded")
    return errors
