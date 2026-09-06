"""M3: household assignment under modulating and binary actuation."""

import pytest
from hypothesis import given, strategies as st
from truss.config import DeviceProfile, MemberProfile
from truss.local_policy import assign, unusable_w


def device(device_id, priority, baseline, maximum, policy="flexible", act="modulating"):
    return DeviceProfile(
        device_id=device_id,
        label=device_id,
        kind="generic",
        max_w=maximum,
        baseline_w=baseline,
        control_policy=policy,
        priority=priority,
        actuation=act,
    )


def household(heater_actuation):
    return MemberProfile(
        member_id="member-a",
        devices=[
            device("protected-load", 100, 120, 120, "protected"),
            device("router", 90, 40, 40, "protected"),
            device("charger", 60, 0, 180),
            device("heater", 20, 0, 650, act=heater_actuation),
        ],
    )


def test_modulating_heater_absorbs_the_remainder():
    assigned = assign(household("modulating"), 960)
    assert assigned == {
        "protected-load": 120,
        "router": 40,
        "charger": 180,
        "heater": 620,
    }
    assert unusable_w(household("modulating"), 960) == 0


def test_binary_heater_is_skipped_when_its_whole_step_does_not_fit():
    profile = household("binary")
    assigned = assign(profile, 960)
    assert assigned["heater"] == 0
    assert assigned["charger"] == 180
    assert sum(assigned.values()) == 340
    assert unusable_w(profile, 960) == 620


def test_binary_heater_runs_whole_once_it_fits():
    profile = household("binary")
    assigned = assign(profile, 990)
    assert assigned["heater"] == 650
    assert assigned["charger"] == 180
    assert unusable_w(profile, 990) == 0


def test_binary_device_never_takes_a_partial_step():
    profile = household("binary")
    for budget in range(160, 1000):
        assert assign(profile, budget)["heater"] in (0, 650)


def test_lower_priority_device_still_fits_after_an_unaffordable_one():
    profile = MemberProfile(
        member_id="member-a",
        devices=[
            device("router", 90, 40, 40, "protected"),
            device("heater", 60, 0, 650, act="binary"),
            device("lamp", 20, 0, 100),
        ],
    )
    assigned = assign(profile, 100)
    assert assigned["heater"] == 0
    assert assigned["lamp"] == 60


def test_budget_below_baselines_is_refused_not_shaved():
    with pytest.raises(ValueError):
        assign(household("binary"), 159)


def test_binary_device_must_have_a_real_step():
    with pytest.raises(ValueError):
        device("pinned", 50, 40, 40, "protected", act="binary")


profiles = st.builds(
    MemberProfile,
    member_id=st.just("member-a"),
    devices=st.lists(
        st.builds(
            device,
            device_id=st.text("abcdef", min_size=1, max_size=4),
            priority=st.integers(0, 100),
            baseline=st.just(0),
            maximum=st.integers(1, 900),
            policy=st.just("flexible"),
            act=st.sampled_from(["modulating", "binary"]),
        ),
        min_size=1,
        max_size=5,
        unique_by=lambda d: d.device_id,
    ),
)


@given(profiles, st.integers(0, 5000))
def test_assignment_never_exceeds_its_budget(profile, budget):
    baseline = sum(d.baseline_w for d in profile.devices)
    assigned = assign(profile, baseline + budget)
    total = sum(assigned.values())
    assert total <= baseline + budget
    assert total >= baseline
    for d in profile.devices:
        assert d.baseline_w <= assigned[d.device_id] <= d.max_w
        if d.actuation == "binary":
            assert assigned[d.device_id] in (d.baseline_w, d.max_w)
    assert unusable_w(profile, baseline + budget) == baseline + budget - total


@given(profiles, st.integers(0, 5000))
def test_only_binary_devices_can_strand_capacity(profile, budget):
    baseline = sum(d.baseline_w for d in profile.devices)
    stranded = unusable_w(profile, baseline + budget)
    if all(d.actuation == "modulating" for d in profile.devices):
        headroom = sum(d.max_w - d.baseline_w for d in profile.devices)
        assert stranded == max(0, budget - headroom)
    assert stranded >= 0
