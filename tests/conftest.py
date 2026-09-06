import json
from pathlib import Path
import pytest
from truss.config import Registration
from truss.schemas import decode

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def registration():
    return Registration(
        member_id="member-a", floor_w=100, max_w=1000, host_id="pc", baseline_revision=1
    )


@pytest.fixture
def wire():
    return {
        m["schema"]: m
        for m in json.loads((ROOT / "fixtures/wire-valid.json").read_text())
    }


@pytest.fixture
def lease(wire):
    return decode(json.dumps(wire["truss.lease.v1"]).encode())


@pytest.fixture(scope="session")
def live_stack(tmp_path_factory):
    import socket
    from truss.runtime import TrussRun, broker_binary
    from truss.observer import LiveState

    try:
        broker_binary()
    except RuntimeError as exc:
        pytest.skip(str(exc))
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    run = TrussRun(runtime_root=tmp_path_factory.mktemp("live"), broker_port=port)
    observer = None
    try:
        run.start()
        observer = LiveState(run)
        observer.start()
        yield run, observer
    finally:
        if observer:
            observer.close()
        run.close()
