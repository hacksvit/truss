"""Pure O(n log n) weighted-surplus filling. Owner M1; no I/O or clocks."""

from dataclasses import dataclass
from fractions import Fraction
from collections.abc import Sequence


@dataclass(frozen=True)
class Demand:
    member_id: str
    floor_w: int
    useful_w: int
    weight: Fraction = Fraction(1)

    def __post_init__(self):
        if not isinstance(self.weight, Fraction):
            raise ValueError("weight must be an exact Fraction")
        if type(self.floor_w) is not int or type(self.useful_w) is not int:
            raise ValueError("watts must be integers")
        if not 0 <= self.floor_w <= self.useful_w or not 1 <= self.weight <= 2:
            raise ValueError("invalid demand envelope/weight")


@dataclass(frozen=True)
class Proposal:
    feasible: bool
    budgets: dict[str, int]
    continuous: dict[str, Fraction]
    deficit_w: int
    remainder_w: Fraction


def allocate(offers: Sequence[Demand], cap_w: int, reserve_w: int = 0) -> Proposal:
    if (
        type(cap_w) is not int
        or type(reserve_w) is not int
        or min(cap_w, reserve_w) < 0
    ):
        raise ValueError("cap/reserve must be nonnegative integer watts")
    if len({o.member_id for o in offers}) != len(offers):
        raise ValueError("duplicate member")
    available = cap_w - reserve_w - sum(o.floor_w for o in offers)
    if available < 0:
        return Proposal(False, {}, {}, -available, Fraction(0))
    active = sorted(
        (Fraction(o.useful_w - o.floor_w) / o.weight, o.member_id, o.weight)
        for o in offers
        if o.useful_w > o.floor_w
    )
    pool, level = Fraction(available), Fraction(0)
    total_weight = sum((item[2] for item in active), Fraction(0))
    for threshold, _, weight in active:
        cost = (threshold - level) * total_weight
        if cost > pool:
            level += pool / total_weight
            pool = Fraction(0)
            break
        pool -= cost
        level = threshold
        total_weight -= weight
    continuous = {
        o.member_id: Fraction(o.floor_w)
        + min(Fraction(o.useful_w - o.floor_w), o.weight * level)
        for o in sorted(offers, key=lambda o: o.member_id)
    }
    budgets = {
        key: value.numerator // value.denominator for key, value in continuous.items()
    }
    rounding = sum(continuous.values(), Fraction(0)) - sum(budgets.values())
    return Proposal(True, budgets, continuous, 0, rounding)
