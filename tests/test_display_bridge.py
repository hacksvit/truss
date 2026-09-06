"""M5: screen projection, read-only HTTP boundary and actual native parser regressions."""

import shutil
import subprocess
from pathlib import Path

import httpx
import pytest

from truss.display_bridge import answer_request, display_frame
from truss.mock import MockState

NONCE = "0000000100000001"
POLL = f"TRUSS? {NONCE}\n".encode()


def test_projection_preserves_source_unknown_and_floor():
    snapshot = MockState().snapshot()
    output = display_frame(snapshot, NONCE)
    assert output.startswith(f"TRUSS1 {NONCE} mock ".encode())
    assert b" 900 " in output
    assert b"heater" not in output and b"member-a" not in output
    snapshot = snapshot.model_copy(
        update={
            "site": snapshot.site.model_copy(
                update={
                    "observed_w": 0,
                    "observed_quality": "fresh",
                    "oldest_sample_age_ms": 0,
                }
            )
        }
    )
    assert display_frame(snapshot, NONCE).split()[5] == b"0"
    for quality, age in (
        ("stale", 100),
        ("unknown", 0),
        ("fresh", None),
        ("fresh", 1501),
    ):
        stale = snapshot.model_copy(
            update={
                "site": snapshot.site.model_copy(
                    update={
                        "observed_quality": quality,
                        "oldest_sample_age_ms": age,
                    }
                )
            }
        )
        assert display_frame(stale, NONCE).split()[5] == b"-1"
    with pytest.raises(ValueError):
        display_frame(snapshot, "injected\nnonce")


def test_bridge_reads_new_snapshot_only_for_valid_polls():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "GET" and request.url.path == "/api/v1/state"
        assert request.url.params["source"] == "mock"
        return httpx.Response(
            200, json=MockState().snapshot().model_dump(by_alias=True)
        )

    with httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://local"
    ) as client:
        assert answer_request(b"bootloader chatter\n", client, "mock") is None
        assert answer_request(POLL + b"extra", client, "mock") is None
        assert answer_request(POLL, client, "mock").startswith(b"TRUSS1 ")
        assert answer_request(POLL, client, "mock").startswith(b"TRUSS1 ")
    assert len(calls) == 2


@pytest.mark.parametrize(
    "kind", ["wrong_source", "unavailable", "too_large", "invalid_snapshot"]
)
def test_bridge_does_not_forward_invalid_evidence(kind):
    snapshot = MockState().snapshot().model_dump(by_alias=True)
    responses = {
        "wrong_source": httpx.Response(200, json=snapshot),
        "unavailable": httpx.Response(503),
        "too_large": httpx.Response(200, content=b"x" * 1_048_577),
        "invalid_snapshot": httpx.Response(200, json={"site": {"observed_w": 0}}),
    }
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: responses[kind]),
        base_url="http://local",
    ) as client:
        with pytest.raises((ValueError, httpx.HTTPError)):
            answer_request(POLL, client, "live")


def test_native_display_parser(tmp_path):
    compiler = shutil.which("g++")
    if not compiler:
        pytest.skip("Native display parser regression requires g++")
    firmware = Path(__file__).resolve().parents[1] / "firmware/status-display"
    binary = tmp_path / "protocol-test"
    subprocess.run(
        [
            compiler,
            "-std=c++11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(firmware / "include"),
            str(firmware / "tests/protocol_test.cpp"),
            "-o",
            str(binary),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run([str(binary)], check=True, capture_output=True)
