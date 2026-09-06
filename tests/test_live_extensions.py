"""M5: actual rule persistence, weighted grants, read-only replay and concurrent lab/fault API."""

import time
from uuid import uuid4
from fastapi.testclient import TestClient
from truss.api import create_app
from truss.authority_store import AuthorityStore
from test_fault_integration import until, ready, post


def test_live_rule_credit_restart_and_persistent_operation_lookup(live_stack):
    run, observer = live_stack
    until(lambda: ready(observer), 25)
    with TestClient(create_app(observer)) as client:
        operation = post(client, "rule", rule="debt_weighted_surplus")

        def weighted():
            snapshot = observer.snapshot()
            return (
                snapshot
                if snapshot.site.rule == "debt_weighted_surplus"
                and any(
                    m.basis and m.basis.rule == "debt_weighted_surplus"
                    for m in snapshot.members
                )
                else None
            )

        snapshot = until(weighted, 12)
        assert all(1 <= m.weight <= 2 and m.debt_wh >= 0 for m in snapshot.members)
        assert snapshot.site.timing.allocation_ms is not None
        assert snapshot.site.timing.plan_validation_ms is not None
        assert client.get("/api/v1/fairness").json()["available"]
        run.act("kill_coordinator")
        store = AuthorityStore(run.directory / "authority.sqlite")
        before = store.get("debt")
        run.act("restart_coordinator")
        time.sleep(1)
        after = store.get("debt")
        assert before["values"] == after["values"]
        assert store.get("control")["rule"] == "debt_weighted_surplus"
        store.close()
        until(weighted, 15)
        post(client, "rule", rule="equal_surplus")
        # More than the 20-item snapshot tail must not lose durable operation lookup.
        for _ in range(21):
            post(client, "cap", watts=5000)
        assert (
            client.get("/api/v1/operations/" + operation["operation_id"]).json()
            == operation
        )
        until(lambda: ready(observer), 20)


def test_live_isolated_lab_recording_and_bounded_fault_api(live_stack):
    run, observer = live_stack
    until(lambda: ready(observer), 25)
    with TestClient(create_app(observer)) as client:
        job = client.post(
            "/api/v1/lab/runs",
            json={"members": 5000, "seed": 42, "samples": 20},
            headers={"Idempotency-Key": str(uuid4())},
        )
        assert job.status_code == 202, job.text
        deadline = time.monotonic() + 16
        while time.monotonic() < deadline:
            assert observer.snapshot().site.observed_w is not None
            status = client.get(job.headers["Location"]).json()
            if status["status"] != "running":
                break
            time.sleep(0.1)
        assert status["status"] == "complete", status
        assert client.get("/api/v1/recordings").json()["items"]
        replay = client.post(
            "/api/v1/replays", json={"recorded_run_id": run.policy.run_id}
        )
        assert replay.status_code == 201, replay.text
        view = replay.json()
        assert view["snapshot"]["source"] == "replay" and view["frame_count"] > 1
        assert (
            client.post(
                "/api/v1/replays/" + view["replay_id"] + "/seek",
                json={"from_seq": view["last_seq"]},
            ).json()["snapshot"]["site"]["observed_w"]
            is not None
        )
        operation = post(
            client,
            "faults",
            target="member:member-a",
            action="delay_grants",
            duration_ms=1000,
            delay_ms=7000,
            rate=1.0,
        )
        assert operation["status"] == "applied"
        body = {
            "source": "live",
            "run_id": observer.run_id,
            "expected_control_revision": observer.control_revision,
            "target": "broker",
            "action": "partition",
            "duration_ms": 1000,
        }
        assert (
            client.post(
                "/api/v1/faults", json=body, headers={"Idempotency-Key": str(uuid4())}
            ).status_code
            == 422
        )
        assert client.get("/api/v1/runtime").json()["processes"]
        until(lambda: ready(observer), 20)
