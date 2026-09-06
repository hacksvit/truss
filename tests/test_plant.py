import json
from truss.config import MemberProfile, DeviceProfile
from truss.plant import Plant
from truss.schemas import decode


def test_expiry_independent_of_member_and_protected_floor(registration, wire):
    profile = MemberProfile(
        member_id="member-a",
        devices=[
            DeviceProfile(
                device_id="essential",
                label="Fictional essential",
                kind="generic",
                max_w=100,
                baseline_w=100,
                control_policy="protected",
                priority=100,
            ),
            DeviceProfile(
                device_id="heater",
                label="Heater",
                kind="heater",
                max_w=500,
                baseline_w=0,
                control_policy="flexible",
                priority=20,
            ),
        ],
    )
    binding = decode(json.dumps(wire["truss.plant_bind.v1"]).encode())
    ceiling = decode(json.dumps(wire["truss.plant_ceiling.v1"]).encode())
    p = Plant(registration, profile, binding.plant_boot_id, binding.clock_domain_id)
    assert p.bind(binding, 0) == "applied"
    assert p.apply_ceiling(ceiling, 0) == "applied"
    assert p.command("heater", "cmd", 1, 400, 6_000_000_000, 0) == "applied"
    assert p.command("essential", "bad", 1, 0, 6_000_000_000, 1) == "rejected"
    assert p.command("heater", "over", 2, 500, 6_000_000_000, 1) == "rejected"
    p.tick(6_000_000_000)  # Member has never run again.
    assert p.devices["heater"].observed_w == 0
    assert p.devices["essential"].observed_w == 100
    assert p.apply_ceiling(ceiling, 6_000_000_001) == "expired"
