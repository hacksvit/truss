"""M1: reject inflated self-declared floors and omitted registered households."""

import pytest
from truss.config import load_run
from truss.coordinator import Coordinator
from truss.allocator import Demand


def test_self_declared_floor_does_not_change_entitlement():
    policy = load_run("config/run.json")
    c = Coordinator(policy, 0)
    offers = [Demand(m.member_id, m.floor_w, m.max_w) for m in policy.members]
    assert c.propose(offers, 5000).feasible
    offers[0] = Demand(offers[0].member_id, offers[0].floor_w + 10, offers[0].useful_w)
    with pytest.raises(ValueError, match="unapproved floor"):
        c.propose(offers, 5000)


def test_absent_offer_cannot_erase_registered_member():
    policy = load_run("config/run.json")
    c = Coordinator(policy, 0)
    with pytest.raises(ValueError, match="all registered baselines"):
        c.propose(
            [Demand(m.member_id, m.floor_w, m.max_w) for m in policy.members[1:]], 5000
        )
