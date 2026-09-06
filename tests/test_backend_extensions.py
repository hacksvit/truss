"""M5: isolated benchmark API, immutable replay and hardened request boundaries."""

import time
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from truss.api import create_app
from truss.api_models import Snapshot
from truss.mock import MockState
from truss.events import EventLog
from truss.recordings import Recordings


def test_api_rejects_duplicate_json_chunked_large_body_and_bad_ws():
    with TestClient(create_app(MockState())) as client:
        assert (
            client.post(
                "/api/v1/cap",
                content=b'{"watts":1,"watts":2}',
                headers={"Content-Type": "application/json"},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/cap", content=iter([b"x" * 9000, b"x" * 9000])
            ).status_code
            == 413
        )
        assert client.get("/api/v1/events?after_seq=-1").status_code == 422
        with client.websocket_connect(
            "/ws/v1/state?source=mock", subprotocols=["truss.ui.v1"]
        ) as ws:
            ws.receive_json()
            ws.receive_json()
            ws.send_json(["invalid"])
            from starlette.websockets import WebSocketDisconnect

            with pytest.raises(WebSocketDisconnect):
                for _ in range(4):
                    ws.receive_json()


def test_real_disposable_benchmark_job_and_idempotency():
    with TestClient(create_app(MockState())) as client:
        key = str(uuid4())
        body = dict(
            members=50,
            seed=7,
            samples=10,
            distribution="skewed",
            rule="debt_weighted_surplus",
            cap_ratio=0.3,
        )
        response = client.post(
            "/api/v1/lab/runs", json=body, headers={"Idempotency-Key": key}
        )
        assert response.status_code == 202, response.text
        job = response.json()
        assert (
            client.post(
                "/api/v1/lab/runs",
                json={**body, "members": 60},
                headers={"Idempotency-Key": key},
            ).status_code
            == 409
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            job = client.get(response.headers["Location"]).json()
            assert client.get("/api/v1/health").status_code == 200
            if job["status"] != "running":
                break
            time.sleep(0.05)
        assert job["status"] == "complete", job
        result = job["result"]
        assert result["complete"] and len(result["samples_ms"]) == 10
        assert (
            len(result["validation_samples_ms"])
            == len(result["total_samples_ms"])
            == 10
        )
        assert all(
            t >= a for t, a in zip(result["total_samples_ms"], result["samples_ms"])
        )
        repeated = client.post(
            "/api/v1/lab/runs", json=body, headers={"Idempotency-Key": key}
        ).json()
        assert repeated == job
        legacy = client.post(
            "/api/v1/lab/benchmark", json={"members": 10, "seed": 1, "samples": 2}
        )
        assert legacy.status_code == 200, legacy.text
        assert legacy.json()["complete"]


def recording(tmp_path):
    state = MockState()
    path = tmp_path / state.run_id / "snapshots.jsonl"
    log = EventLog(path)
    for i in range(3):
        snapshot = state.snapshot()
        log.append(
            run_id=state.run_id,
            received_at=snapshot.generated_at,
            received_mono_ns=str(i * 500000000),
            kind="snapshot",
            topic=None,
            payload_schema="truss.ui_snapshot.v1",
            payload=snapshot.model_dump(by_alias=True),
            correlation_id=None,
        )
    return state, path


def test_replay_seeks_frozen_recording_with_source_and_gap(tmp_path):
    state, path = recording(tmp_path)
    before = path.read_bytes()
    archive = Recordings(tmp_path)
    assert archive.catalog()["items"][0]["recorded_run_id"] == state.run_id
    view = archive.create(state.run_id)
    assert view["frame_seq"] == 1 and not view["gap"]
    snapshot = Snapshot.model_validate(view["snapshot"])
    assert snapshot.source == "replay" and not snapshot.capabilities.chaos
    assert not snapshot.operations
    end = archive.get(view["replay_id"], 3)
    assert end["frame_seq"] == 3 and end["sha256"] == view["sha256"]
    with pytest.raises(ValueError, match="out_of_range"):
        archive.get(view["replay_id"], 4)
    assert path.read_bytes() == before
    path.write_bytes(before + b'{"partial":')
    assert not archive.get(view["replay_id"])["gap"]  # Immutable session.
    assert archive.create(state.run_id)["gap"]
    archive.delete(view["replay_id"])
    with pytest.raises(ValueError, match="not_found"):
        archive.get(view["replay_id"])


def test_replay_api_has_no_path_upload_or_live_controls(tmp_path):
    state, path = recording(tmp_path)
    app = create_app(MockState())
    # Explicit test archive registration. Production only discovers its run root.
    app.state.recordings.root = tmp_path
    with TestClient(app) as client:
        view = client.post(
            "/api/v1/replays", json={"recorded_run_id": state.run_id}
        ).json()
        assert view["snapshot"]["source"] == "replay"
        uri = "/api/v1/replays/" + view["replay_id"]
        assert client.post(uri + "/seek", json={"from_seq": 2}).json()["frame_seq"] == 2
        assert client.get(uri).status_code == 200
        assert (
            client.post(
                "/api/v1/replays", json={"recorded_run_id": "../../etc/passwd"}
            ).status_code
            == 422
        )
        snap = view["snapshot"]
        assert (
            client.post(
                "/api/v1/cap",
                json={
                    "run_id": snap["run_id"],
                    "source": "replay",
                    "expected_control_revision": snap["control_revision"],
                    "watts": 1000,
                },
                headers={"Idempotency-Key": str(uuid4())},
            ).status_code
            == 403
        )
        assert client.delete(uri).json() == {"deleted": True}


def test_replay_play_pause_uses_recorded_time_and_seek_is_exact(tmp_path, monkeypatch):
    state, path = recording(tmp_path)
    archive = Recordings(tmp_path)
    now = [0]
    monkeypatch.setattr("truss.recordings.time.monotonic_ns", lambda: now[0])
    view = archive.create(state.run_id)
    replay_id = view["replay_id"]
    assert archive.playback(replay_id, "play")["playing"]
    now[0] = 600_000_000
    assert archive.get(replay_id)["frame_seq"] == 2
    archive.playback(replay_id, "pause")
    now[0] = 4_000_000_000
    assert archive.get(replay_id)["frame_seq"] == 2
    archive.playback(replay_id, "play")
    now[0] += 400_000_000
    end = archive.get(replay_id)
    assert end["frame_seq"] == 3 and not end["playing"]
    assert archive.get(replay_id, 1)["frame_seq"] == 1
    lines = path.read_bytes().splitlines(keepends=True)
    path.write_bytes(lines[0] + lines[2])
    missing = archive.create(state.run_id)
    assert missing["gap"]
    with pytest.raises(ValueError, match="in_gap"):
        archive.get(missing["replay_id"], 2)
