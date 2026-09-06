import pytest
from truss.config import Registration
from truss.reservations import ReservationLedger


def admit(g, member="a", request="r1", seq=1, watts=800, now=0, cap=1000):
    return g.admit(
        member_id=member,
        boot_id="boot",
        request_id=request,
        request_seq=seq,
        amount_w=watts,
        cap_w=cap,
        reserve_w=0,
        now_ns=now,
    )


def ledger():
    return ReservationLedger(
        [
            Registration(
                member_id=m, floor_w=100, max_w=900, host_id="pc", baseline_revision=1
            )
            for m in ("a", "b")
        ]
    )


def test_lower_lease_does_not_reclaim_old_exposure():
    g = ledger()
    admit(g)
    admit(g, request="r2", seq=2, watts=100, now=1)
    with pytest.raises(ValueError, match="capacity"):
        admit(g, member="b", watts=800, now=2)
    assert g.exposure(2) == {"a": 800, "b": 100}
    admit(g, member="b", watts=800, now=6_400_000_001)


def test_duplicate_does_not_extend_hold():
    g = ledger()
    first = admit(g)
    assert admit(g, now=5_000_000_000) == first
    assert g.exposure(6_400_000_000) == {"a": 100, "b": 100}
    with pytest.raises(ValueError, match="old request"):
        admit(g, now=7_000_000_000)


def test_second_restart_restarts_full_recovery():
    g = ledger()
    g.begin_recovery(0)
    g.begin_recovery(3_000_000_000)
    with pytest.raises(ValueError, match="recovering"):
        admit(g, now=7_000_000_000)
    assert g.exposure(9_399_999_999) == {"a": 900, "b": 900}
    admit(g, now=9_400_000_000)


def test_cap_drop_never_erases_authority():
    g = ledger()
    admit(g)
    with pytest.raises(ValueError):
        admit(g, member="b", watts=100, cap=500, now=1)
    assert sum(g.exposure(1).values()) == 900


def test_drift_and_enforcement_bound_fit_hold():
    # Real-time worst case: fastest coordinator releases earliest; slowest
    # member expires latest. Delay before admission only adds safety margin.
    earliest_release = 6.4 / 1.001
    latest_enforcement = 6.0 / 0.999 + 0.250
    assert earliest_release > latest_enforcement
