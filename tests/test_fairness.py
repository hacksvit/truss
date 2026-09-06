"""M1: exact service-credit integration, frozen unknown intervals and durable restart behavior."""

from fractions import Fraction
from types import SimpleNamespace as NS
from hypothesis import given, strategies as st

from truss.config import Registration
from truss.reservations import ReservationLedger, Reservation
from truss.fairness import ServiceDeficit, NS_PER_HOUR
from truss.authority_store import AuthorityStore


def setup():
    members = [
        Registration(
            member_id=m, floor_w=100, max_w=1000, host_id="pc", baseline_revision=1
        )
        for m in ("a", "b")
    ]
    ledger = ReservationLedger(members)
    offers = {m: (NS(useful_w=1000, member_boot_id="boot"), 0) for m in ("a", "b")}
    statuses = {
        m: (NS(publisher_boot_id="boot", state="online"), 0) for m in ("a", "b")
    }
    debt = ServiceDeficit(members, 0)
    return debt, ledger, offers, statuses, members


@given(st.lists(st.integers(min_value=1, max_value=999999999), min_size=1, max_size=8))
def test_credit_invariant_under_interval_splitting(cuts):
    a, ledger, offers, statuses, _ = setup()
    b, *_ = setup()
    a.capture(0, offers, statuses, ledger, 1000, 0)
    b.capture(0, offers, statuses, ledger, 1000, 0)
    for t in sorted(set(cuts)):
        a.advance(t)
    a.advance(1_000_000_000)
    b.advance(1_000_000_000)
    assert a.values == b.values == {m: Fraction(400, 3600) for m in ("a", "b")}


def test_split_exactly_at_reservation_expiry_and_reference_change():
    debt, ledger, offers, statuses, _ = setup()
    ledger.records[("a", "boot", "r")] = Reservation(
        "a", "r", "boot", 1, 800, 500_000_000
    )
    debt.values["a"] = Fraction(1)
    debt.capture(0, offers, statuses, ledger, 1000, 0)
    debt.advance(1_000_000_000)
    assert debt.values["a"] == 1 + Fraction((-300 + 400) * 500_000_000, NS_PER_HOUR)
    assert debt.values["b"] == Fraction(400, 3600)
    # Status expires at 1.5 s: no new credit after that exact boundary.
    debt.advance(2_000_000_000)
    assert debt.values["b"] == Fraction(400 * 1_500_000_000, NS_PER_HOUR)


def test_no_offline_recovery_infeasible_or_unknown_interval_credit():
    for reason in ("offline", "recovery", "infeasible", "partition", "gap"):
        debt, ledger, offers, statuses, _ = setup()
        if reason == "offline":
            for status, _ in statuses.values():
                status.state = "offline"
        if reason == "recovery":
            ledger.begin_recovery(0)
        debt.capture(
            0,
            offers,
            statuses,
            ledger,
            100 if reason == "infeasible" else 1000,
            0,
            reason != "partition",
        )
        debt.advance(2_000_000_000 if reason == "gap" else 1_000_000_000)
        assert all(v == 0 for v in debt.values.values())
    assert debt.frozen_gap_ns == 2_000_000_000


def test_bounds_weight_cap_durable_restart_and_corrupt_state(tmp_path):
    debt, ledger, offers, statuses, members = setup()
    debt.values["a"] = Fraction(20)
    debt.capture(0, offers, statuses, ledger, 1000, 0)
    debt.advance(1_000_000_000)
    assert debt.values["a"] == 20
    assert debt.weight("a", "debt_weighted_surplus") == 2
    assert debt.weight("a", "equal_surplus") == 1
    store = AuthorityStore(tmp_path / "authority.sqlite")
    with store.db:
        debt.persist(store)
    restored = ServiceDeficit(members, 8_000_000_000, store.get("debt"))
    restored.advance(9_000_000_000)
    assert restored.values == debt.values  # No backfilling unobserved downtime.
    corrupted = debt.dump()
    corrupted["values"]["a"] = [1, 0]
    bad = ServiceDeficit(members, 0, corrupted)
    assert not bad.enabled and bad.error
    assert all(bad.weight(m, "debt_weighted_surplus") == 1 for m in ("a", "b"))
    store.close()
