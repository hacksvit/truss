"""Real Mosquitto and eleven owned control processes; independent virtual meters."""

from random import Random
import json
import time
from uuid import uuid4
from fastapi.testclient import TestClient
from truss.api import create_app
from truss.faults import DeliveryFault, delivery_decision


def test_partition_has_bounded_lifetime():
    f = DeliveryFault("partition", 100)
    assert delivery_decision(f, "x", 99, Random(1))[0] == "drop"
    assert delivery_decision(f, "x", 100, Random(1))[0] == "pass"


def until(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError("Timed out waiting for independently observed condition")


def ready(observer):
    s = observer.snapshot()
    assert observer.failure is None, observer.failure
    return (
        s
        if all(m.status == "ok" and m.observed_w > m.floor_w for m in s.members)
        else None
    )


def floors(observer):
    s = observer.snapshot()
    return (
        s
        if all(
            m.status == "at_floor"
            and m.observed_quality == "fresh"
            and m.observed_w == m.floor_w
            for m in s.members
        )
        else None
    )


def post(client, path, **fields):
    s = client.get("/api/v1/state?source=live").json()
    body = dict(
        run_id=s["run_id"],
        source="live",
        expected_control_revision=s["control_revision"],
        **fields,
    )
    key = str(uuid4())
    r = client.post("/api/v1/" + path, json=body, headers={"Idempotency-Key": key})
    assert r.status_code == 202, r.text
    assert (
        client.post(
            "/api/v1/" + path, json=body, headers={"Idempotency-Key": key}
        ).json()
        == r.json()
    )
    return r.json()


def test_real_process_kill_and_restart(live_stack):
    run, observer = live_stack
    start = until(lambda: ready(observer), 25)
    assert start.site.observed_w == 4900
    from truss.events import read_events

    with observer.lock:
        records, gap = read_events(observer.log.path)
    assert not gap
    plans = {
        e.payload["plan_id"]: e.payload
        for e in records
        if e.payload_schema == "truss.plan.v1"
    }
    leases = [e.payload for e in records if e.payload_schema == "truss.lease.v1"]
    assert leases
    for lease in leases:
        assert (
            plans[lease["ref"]["plan_id"]]["snapshot_id"]
            == lease["basis"]["snapshot_id"]
        )
    plants = {
        name: p.pid
        for name, p in run.supervisor.children.items()
        if name.startswith("plant:")
    }
    c = TestClient(create_app(observer))
    post(c, "chaos", action="kill_coordinator", member_id=None)
    safe = until(lambda: floors(observer), 7)
    assert safe.site.observed_w == 900
    for m in safe.members:
        protected = [d for d in m.devices if d.protected]
        assert protected and all(d.w == d.requested_w for d in protected)
    assert plants == {
        name: p.pid
        for name, p in run.supervisor.children.items()
        if name.startswith("plant:")
    }
    post(c, "chaos", action="restart_coordinator", member_id=None)
    time.sleep(0.7)
    post(c, "chaos", action="restart_coordinator", member_id=None)
    deadline = time.monotonic() + 6.4
    while time.monotonic() < deadline:
        assert observer.snapshot().site.observed_w == 900
        time.sleep(0.1)
    until(lambda: ready(observer), 12)


def test_cap_transition_and_impossible_baselines(live_stack):
    run, o = live_stack
    until(lambda: ready(o), 20)
    c = TestClient(create_app(o))
    post(c, "cap", watts=3000)
    first = o.snapshot()
    assert first.site.state == "cap_transition" and first.site.exposure_w >= 5000
    until(
        lambda: (
            (s := o.snapshot()).site.observed_w is not None
            and s.site.observed_w <= 2900
        ),
        8,
    )
    post(c, "cap", watts=500)
    assert o.snapshot().site.state == "infeasible"
    s = until(lambda: floors(o), 7)
    assert s.site.deficit_w == 500 and s.site.compliance == "over_cap"
    post(c, "cap", watts=5000)
    until(lambda: ready(o), 20)


def test_member_and_broker_death_leave_plant_alive(live_stack):
    run, o = live_stack
    until(lambda: ready(o), 20)
    plant = run.supervisor.children["plant:member-a"]
    pid = plant.pid
    run.act("kill_member", "member-a")
    until(
        lambda: (
            next(m for m in o.snapshot().members if m.id == "member-a").status
            == "at_floor"
        ),
        7,
    )
    assert plant.poll() is None and plant.pid == pid
    run.act("restart_member", "member-a")
    until(lambda: ready(o), 20)
    gaps_before = o.gaps
    run.act("kill_broker")
    killed = time.monotonic_ns()

    def isolated_plants_at_floor():
        records = [
            json.loads((run.directory / f"plant-{letter}-state.json").read_text())
            for letter in "abcde"
        ]
        return all(
            int(r["sampled_mono_ns"]) > killed + 6_000_000_000
            and r["observed_w"] == r["floor_w"]
            and r["enforcement_state"] == "healthy"
            for r in records
        )

    until(isolated_plants_at_floor, 8)
    assert (
        o.snapshot().site.observed_w is None
    )  # Broker outage means no fresh observer evidence.
    assert o.gaps > gaps_before
    assert TestClient(create_app(o)).get("/api/v1/events").json()["gap"] is True
    run.act("restart_broker")
    until(lambda: ready(o), 20)


def test_partition_healing_and_delayed_expired_grants(live_stack):
    run, o = live_stack
    until(lambda: ready(o), 20)
    gaps_before = o.gaps
    run.set_fault("member:member-a", "partition", duration_ms=8500)
    until(
        lambda: (
            next(m for m in o.snapshot().members if m.id == "member-a").status
            == "at_floor"
        ),
        7,
    )
    until(lambda: ready(o), 15)
    run.set_fault("member:member-a", "delay_grants", duration_ms=10000, delay_ms=7000)
    until(
        lambda: (
            next(m for m in o.snapshot().members if m.id == "member-a").status
            == "at_floor"
        ),
        7,
    )
    until(lambda: ready(o), 20)
    assert o.failure is None and o.gaps == gaps_before
