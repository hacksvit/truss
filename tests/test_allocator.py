import json
from pathlib import Path
from fractions import Fraction
from hypothesis import given, strategies as st
from truss.allocator import Demand, allocate
import pytest


def test_float_weight_is_not_silently_approximate():
    with pytest.raises(ValueError, match="exact Fraction"):
        Demand("a", 0, 100, 1.5)


def test_calculated_cases():
    for c in json.loads(Path("fixtures/allocator-cases.json").read_text()):
        offers = [
            Demand(str(i), f, u, Fraction(w))
            for i, (f, u, w) in enumerate(zip(c["floors"], c["useful"], c["weights"]))
        ]
        p = allocate(offers, c["cap"])
        assert p.feasible == (c["expected"] is not None)
        if p.feasible:
            assert list(p.budgets.values()) == c["expected"]


@given(
    st.lists(
        st.tuples(st.integers(0, 200), st.integers(0, 1000), st.integers(1, 2)),
        min_size=1,
        max_size=20,
    ),
    st.integers(0, 20000),
)
def test_envelope_and_continuous_weighted_fairness(rows, extra):
    offers = [
        Demand(f"m{i:02}", f, f + x, Fraction(w)) for i, (f, x, w) in enumerate(rows)
    ]
    cap = sum(o.floor_w for o in offers) + extra
    result = allocate(offers, cap)
    assert result.feasible and sum(result.budgets.values()) <= cap
    assert allocate(list(reversed(offers)), cap) == result
    unsaturated = []
    for o in offers:
        b = result.budgets[o.member_id]
        c = result.continuous[o.member_id]
        assert o.floor_w <= b <= o.useful_w and 0 <= c - b < 1
        if c < o.useful_w:
            unsaturated.append((c - o.floor_w) / o.weight)
    assert len(set(unsaturated)) <= 1
    assert sum(result.continuous.values()) == min(cap, sum(o.useful_w for o in offers))
