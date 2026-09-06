from truss.config import DeviceProfile
from truss.devices import Device
from hypothesis import given, strategies as st


@given(st.integers(0, 500))
def test_duplicate_command_has_one_effect(watts):
    d = Device(
        DeviceProfile(
            device_id="heater",
            label="Virtual",
            kind="heater",
            max_w=500,
            baseline_w=0,
            control_policy="flexible",
            priority=1,
        )
    )
    assert d.command("cmd", 1, watts, 100, 0, 500) == "applied"
    transitions = d.transitions
    assert d.command("cmd", 1, watts, 100, 50, 500) == "duplicate"
    assert d.transitions == transitions
    assert d.command("late", 2, 500, 100, 100, 500) == "expired"
