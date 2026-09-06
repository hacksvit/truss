"""Independent timed authority oracle, excluding unimplemented MQTT process wiring."""

from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from hypothesis import strategies as st
from truss.config import Registration
from truss.reservations import ReservationLedger


class AuthorityMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.now = 0
        self.sequence = 0
        self.deliverable = []
        self.recovery = 0
        self.gate = ReservationLedger(
            [
                Registration(
                    member_id=m,
                    floor_w=100,
                    max_w=900,
                    host_id="pc",
                    baseline_revision=1,
                )
                for m in ("a", "b")
            ]
        )

    @rule(
        member=st.sampled_from(["a", "b"]),
        watts=st.integers(100, 900),
        delay_ms=st.integers(0, 9000),
    )
    def request(self, member, watts, delay_ms):
        self.sequence += 1
        try:
            self.gate.admit(
                member_id=member,
                boot_id="boot",
                request_id=str(self.sequence),
                request_seq=self.sequence,
                amount_w=watts,
                cap_w=1200,
                reserve_w=100,
                now_ns=self.now,
            )
        except ValueError:
            return
        # Oracle gives grants the full 6 s even if production transport drops them.
        # Delivery after expiry creates no authority. Delay never moves deadline.
        if delay_ms < 6000:
            self.deliverable.append((member, watts, self.now + 6_000_000_000))

    @rule(milliseconds=st.integers(0, 10000))
    def advance(self, milliseconds):
        self.now += milliseconds * 1_000_000

    @rule()
    def restart(self):
        self.gate.begin_recovery(self.now)
        self.recovery = self.now + 6_400_000_000

    @invariant()
    def exposure_covers_all_possible_grants(self):
        oracle = {"a": 100, "b": 100}
        for m, w, end in self.deliverable:
            if self.now < end:
                oracle[m] = max(oracle[m], w)
        exposure = self.gate.exposure(self.now)
        assert all(exposure[m] >= oracle[m] for m in oracle)
        assert sum(oracle.values()) + 100 <= 1200
        if self.now >= self.recovery:
            assert sum(exposure.values()) + 100 <= 1200


TestAuthorityMachine = AuthorityMachine.TestCase
