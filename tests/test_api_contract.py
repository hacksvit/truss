from uuid import uuid4
from fastapi.testclient import TestClient
from truss.api import create_app
from truss.api_models import Snapshot
from truss.mock import MockState


def test_live_unavailable_and_mock_source_isolation():
    assert TestClient(create_app()).get("/api/v1/state").status_code == 503
    c = TestClient(create_app(MockState()))
    assert c.get("/api/v1/state?source=live").status_code == 403
    s = Snapshot.model_validate(c.get("/api/v1/state?source=mock").json())
    assert s.source == "mock" and not s.capabilities.protect


def test_control_idempotency_and_revision_conflict():
    c = TestClient(create_app(MockState()))
    s = c.get("/api/v1/state?source=mock").json()
    body = dict(
        source="mock",
        run_id=s["run_id"],
        expected_control_revision=s["control_revision"],
        watts=3000,
    )
    headers = {"Idempotency-Key": str(uuid4())}
    a = c.post("/api/v1/cap", json=body, headers=headers)
    b = c.post("/api/v1/cap", json=body, headers=headers)
    assert a.status_code == b.status_code == 202 and a.json() == b.json()
    assert (
        c.post("/api/v1/cap", json={**body, "watts": 2000}, headers=headers).status_code
        == 409
    )
    assert (
        c.post(
            "/api/v1/cap", json=body, headers={"Idempotency-Key": str(uuid4())}
        ).status_code
        == 409
    )


def test_websocket_snapshot_and_ping():
    with TestClient(create_app(MockState())) as c:
        with c.websocket_connect(
            "/ws/v1/state?source=mock", subprotocols=["truss.ui.v1"]
        ) as ws:
            assert ws.receive_json()["type"] == "hello"
            ping = ws.receive_json()
            assert ping["type"] == "ping"
            ws.send_json({"type": "pong", "id": ping["id"]})
            frame = ws.receive_json()
            assert frame["type"] == "snapshot"
            assert Snapshot.model_validate(frame["data"]).source == "mock"
