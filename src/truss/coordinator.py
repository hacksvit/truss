"""Coordinator core. Owner M1. The MQTT lifecycle lives in coordinator_process.py."""

from .allocator import Demand, Proposal, allocate
from .validator import validate_proposal
from .reservations import ReservationLedger
from .config import RunPolicy


class Coordinator:
    def __init__(self, policy: RunPolicy, now_ns: int):
        self.policy = policy
        self.ledger = ReservationLedger(policy.members, policy.hold_ms)
        self.ledger.begin_recovery(now_ns)

    def propose(self, demands: list[Demand], cap_w: int) -> Proposal:
        registrations = {m.member_id: m for m in self.policy.members}
        if set(registrations) != {d.member_id for d in demands}:
            raise ValueError("proposal must include all registered baselines")
        for demand in demands:
            registered = registrations[demand.member_id]
            if (
                demand.floor_w != registered.floor_w
                or demand.useful_w > registered.max_w
            ):
                raise ValueError("unapproved floor or maximum")
        proposal = allocate(demands, cap_w, self.policy.reserve_w)
        if proposal.feasible and validate_proposal(
            demands, proposal.budgets, cap_w, self.policy.reserve_w
        ):
            raise ValueError("independent validator veto")
        return proposal
