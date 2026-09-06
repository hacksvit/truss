"""M5: regenerate labelled development fixtures and exact schema artifacts."""

import json
from pathlib import Path
from truss import schemas as s
from truss.api import create_app
from truss.api_models import Snapshot
from truss.mock import MockState

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures"
U = "00000000-0000-4000-8000-000000000001"
V = "00000000-0000-4000-8000-000000000002"
BASE = dict(
    site_id="hostel-demo",
    run_id=U,
    publisher_id="member-a",
    publisher_boot_id=U,
    seq=1,
    ts="2026-09-06T00:00:00Z",
    correlation_id=None,
)
REF = dict(
    member_id="member-a",
    member_boot_id=U,
    request_id=V,
    epoch=1,
    version=1,
    lease_id=U,
    plan_id="plan-1",
)
BIND = dict(
    member_id="member-a",
    member_boot_id=U,
    plant_boot_id=U,
    binding_id=V,
    clock_domain_id="test-domain",
    registry_revision=1,
)
BASIS = dict(
    snapshot_id="0" * 64,
    policy_hash="0" * 64,
    registry_revision=1,
    cap_revision=1,
    cap_w=1000,
    measurement_reserve_w=100,
    external_bound_w=0,
    baseline_sum_w=100,
    surplus_pool_w=800,
    rule="equal_surplus",
    debt_scale_wh=100.0,
    weight_cap=2.0,
    member_floor_w=100,
    member_useful_w=500,
    member_debt_wh=0.0,
    member_weight=1.0,
    proposed_budget_w=500,
    issued_budget_w=500,
    reservation_before_w=100,
    reservation_after_w=500,
    total_exposure_after_w=600,
    reason="initial",
)
DECISION = dict(
    decision_id=V,
    member_id="member-a",
    device_id="heater",
    ref=REF,
    offer_seq=1,
    requested_w=300,
    assigned_w=300,
    member_budget_w=500,
    reserved_local_baseline_w=100,
    higher_priority_assigned_w=0,
    reason="manual_priority",
    deadline_status="none",
    deadline_in_ms=None,
)


def examples():
    messages = []

    def add(cls, **fields):
        name = cls.model_fields["schema_id"].annotation.__args__[0]
        messages.append(
            cls.model_validate({**BASE, "schema": name, **fields}).model_dump(
                by_alias=True
            )
        )

    add(
        s.Status,
        component="member",
        component_id="member-a",
        connection_id=U,
        source="heartbeat",
        state="online",
        member_id="member-a",
        epoch=None,
        recovery_ms_remaining=None,
        registry_revision=1,
        reason=None,
    )
    add(
        s.Offer,
        member_id="member-a",
        member_boot_id=U,
        registry_revision=1,
        floor_w=100,
        firm_w=200,
        useful_w=500,
        deadline_energy_wh=0.0,
        deadline_in_ms=None,
        debt_wh=0.0,
        debt_revision=0,
        reported_curtailment_wh=0.0,
    )
    add(
        s.LeaseRequest,
        member_id="member-a",
        member_boot_id=U,
        request_id=V,
        request_seq=1,
        offer_seq=1,
        registry_revision=1,
        ttl_ms=6000,
    )
    add(
        s.Lease,
        publisher_id="coordinator",
        ref=REF,
        registry_revision=1,
        budget_w=500,
        ttl_ms=6000,
        reason="initial",
        basis=BASIS,
    )
    add(
        s.LeaseAck,
        ref=REF,
        result="applied",
        reason=None,
        accepted_budget_w=500,
        lease_ms_remaining=5000,
        plant_confirmed=False,
        observed_w=None,
        observation_quality="unknown",
        plant_boot_id=None,
    )
    add(s.PlantBind, **BIND)
    add(s.PlantCeiling, **BIND, ref=REF, budget_w=500, expires_mono_ns="6000000000")
    add(
        s.PlantAck,
        publisher_id="plant-a",
        member_id="member-a",
        plant_boot_id=U,
        binding_id=V,
        kind="ceiling",
        ref=REF,
        result="applied",
        reason=None,
        active_budget_w=500,
        remaining_ms=5000,
        observed_w=400,
    )
    add(
        s.MemberMeter,
        publisher_id="plant-a",
        member_id="member-a",
        plant_boot_id=U,
        clock_domain_id="test-domain",
        sampled_mono_ns="1000000000",
        observed_w=400,
        active_budget_w=500,
        floor_w=100,
        active_ref=REF,
        lease_ms_remaining=5000,
        at_floor=False,
        enforcement_state="healthy",
        sample_seq=1,
    )
    add(
        s.DeviceDiscovery,
        publisher_id="plant-a",
        member_id="member-a",
        device_id="heater",
        plant_boot_id=U,
        registry_revision=1,
        kind="heater",
        label="Virtual heater",
        max_w=500,
        baseline_w=0,
        flexibility="deferrable",
        control_policy="flexible",
        priority=20,
        interruptible=True,
        min_run_ms=0,
        min_off_ms=0,
    )
    add(
        s.DeviceTelemetry,
        publisher_id="plant-a",
        member_id="member-a",
        device_id="heater",
        plant_boot_id=U,
        clock_domain_id="test-domain",
        sampled_mono_ns="1000000000",
        state="running",
        observed_w=300,
        requested_w=300,
        remaining_energy_wh=0.0,
        deadline_in_ms=None,
        min_run_remaining_ms=0,
        min_off_remaining_ms=0,
        last_command_id=V,
        last_command_version=1,
        active_ref=REF,
    )
    add(
        s.DeviceCommand,
        **{k: v for k, v in BIND.items() if k != "registry_revision"},
        device_id="heater",
        command_id=V,
        command_version=1,
        ref=REF,
        desired_state="running",
        desired_w=300,
        expires_mono_ns="6000000000",
        reason="manual_priority",
        decision=DECISION,
    )
    add(
        s.DeviceAck,
        publisher_id="plant-a",
        member_id="member-a",
        device_id="heater",
        plant_boot_id=U,
        binding_id=V,
        command_id=V,
        command_version=1,
        ref=REF,
        result="applied",
        reason=None,
        observed_state="running",
        observed_w=300,
    )
    add(
        s.CapacityEvent,
        publisher_id="api-control",
        event_id=U,
        operation_id=V,
        cap_revision=2,
        expected_previous_revision=1,
        cap_w=1000,
        source="operator",
        reason="cap_change",
    )
    policy = dict(
        operation_id=U,
        member_id="member-a",
        device_id="heater",
        policy_revision=1,
        protected=True,
    )
    add(s.LocalPolicy, publisher_id="api-control", **policy)
    add(s.PolicyAck, **policy, result="rejected", reason="policy_conflict")
    add(
        s.Plan,
        publisher_id="coordinator",
        plan_id="plan-1",
        snapshot_id="0" * 64,
        policy_hash="0" * 64,
        registry_revision=1,
        cap_revision=1,
        epoch=1,
        status="proposed",
        rule="equal_surplus",
        cap_w=1000,
        measurement_reserve_w=100,
        external_bound_w=0,
        baseline_sum_w=100,
        deficit_w=0,
        affected_members=[],
        allocations=[],
        validation=dict(
            valid=True, codes=[], exposure_w=600, limit_after_reserves_w=900
        ),
        timing=dict(
            input_validation_ms=None,
            allocation_ms=None,
            plan_validation_ms=None,
            admission_ms=None,
        ),
    )
    for value in messages:
        s.decode(json.dumps(value).encode())
    return messages


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    messages = examples()
    write("wire-valid.json", messages)
    invalid = []
    for name, patch in [
        ("negative_budget", {"budget_w": -1}),
        ("receipt_ttl", {"ttl_ms": 7000}),
        ("unknown_field", {"devices": []}),
        ("bool_watts", {"budget_w": True}),
    ]:
        invalid.append(
            dict(
                name=name, message={**messages[3], **patch}, expected="validation_error"
            )
        )
    write("wire-invalid.json", invalid)
    write("mqtt.schema.json", s.MESSAGE_ADAPTER.json_schema(by_alias=True))
    write("snapshot.schema.json", Snapshot.model_json_schema(by_alias=True))
    write("openapi.json", create_app().openapi())
    mock = MockState(ROOT / "config")
    snapshots = [dict(case="starting", data=mock.snapshot().model_dump(by_alias=True))]
    mock.last_renewal -= 3
    snapshots.append(
        dict(case="leased", data=mock.snapshot().model_dump(by_alias=True))
    )
    mock.chaos("stale_member", "member-c")
    snapshots.append(
        dict(case="stale_member", data=mock.snapshot().model_dump(by_alias=True))
    )
    mock.chaos("kill_coordinator", None)
    snapshots.append(
        dict(case="coordinator_offline", data=mock.snapshot().model_dump(by_alias=True))
    )
    mock.chaos("restart_coordinator", None)
    snapshots.append(
        dict(case="recovering", data=mock.snapshot().model_dump(by_alias=True))
    )
    mock.set_cap(500)
    snapshots.append(
        dict(case="infeasible", data=mock.snapshot().model_dump(by_alias=True))
    )
    write("snapshots.json", snapshots)
    events = [
        dict(
            run_id=mock.run_id,
            event_seq=i + 1,
            received_at=x["data"]["generated_at"],
            received_mono_ns=str(i * 1000000000),
            kind="mock_fixture",
            topic=None,
            payload_schema="truss.ui_snapshot.v1",
            payload=x["data"],
            correlation_id=None,
        )
        for i, x in enumerate(snapshots)
    ]
    (OUT / "demo-events.jsonl").write_text(
        "".join(json.dumps(x) + "\n" for x in events)
    )
    write(
        "allocator-cases.json",
        [
            dict(
                name="equal",
                floors=[100, 100],
                useful=[500, 500],
                weights=[1, 1],
                cap=600,
                expected=[300, 300],
            ),
            dict(
                name="weighted_surplus",
                floors=[100, 100],
                useful=[500, 500],
                weights=[1, 2],
                cap=500,
                expected=[200, 300],
            ),
            dict(
                name="round_down",
                floors=[0, 0],
                useful=[5, 5],
                weights=[1, 1],
                cap=3,
                expected=[1, 1],
            ),
            dict(
                name="floor_deficit",
                floors=[100, 100],
                useful=[500, 500],
                weights=[1, 1],
                cap=150,
                expected=None,
            ),
        ],
    )
    write(
        "race-traces.json",
        [
            dict(
                name="delayed_grant",
                steps=["request at 0", "grant delivered at 6001 ms"],
                expected="expired; baseline",
            ),
            dict(
                name="duplicate",
                steps=["request at 0", "grant at 1 s", "same grant at 5 s"],
                expected="deadline remains 6 s",
            ),
            dict(
                name="twice_restart",
                steps=["restart at 0", "restart at 3 s"],
                expected="no grant before 9.4 s",
            ),
            dict(
                name="lower_then_reallocate",
                steps=["A holds 800", "A gets 100", "B asks for reclaimed 700"],
                expected="deny until A old hold expires",
            ),
        ],
    )
    write(
        "lab-cases.json",
        dict(
            source="synthetic",
            sizes=[5, 50, 500, 5000],
            seed=7,
            warmups=20,
            samples=200,
            scope="allocator only; no flat latency claim",
        ),
    )


if __name__ == "__main__":
    main()
