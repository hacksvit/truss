"""Exercise the hosted entry point with a real private MQTT runtime."""

import socket

import pytest
from starlette.testclient import TestClient

from truss.hosted import create_hosted_app
from truss.runtime import broker_binary


def test_hosted_pages_assets_and_independent_backends(tmp_path):
    try:
        broker_binary()
    except RuntimeError:
        pytest.skip("Mosquitto is required for the hosted integration test")
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>Truss hosted</html>")
    (dist / "clouds").mkdir()
    (dist / "clouds/cloud.png").write_bytes(b"cloud-asset")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        broker_port = reservation.getsockname()[1]
    app = create_hosted_app(
        config_dir="config", dist=dist, runtime_root=tmp_path / "runtime",
        broker_port=broker_port,
    )
    with TestClient(app) as client:
        for route in ("/", "/example", "/console", "/lab", "/info", "/credits"):
            response = client.get(route)
            assert response.status_code == 200
            assert "Truss hosted" in response.text
        assert client.get("/clouds/cloud.png").content == b"cloud-asset"
        assert client.get("/missing.png").status_code == 404
        assert client.get("/api/v1/health").json()["mode"] == "mock"
        assert client.get("/console-api/v1/health").json()["mode"] == "live"
        for prefix, source in (("/ws", "mock"), ("/console-ws", "live")):
            with client.websocket_connect(
                f"{prefix}/v1/state?source={source}", subprotocols=["truss.ui.v1"]
            ) as stream:
                hello = stream.receive_json()
                assert hello["type"] == "hello"
                assert hello["source"] == source


def test_hosted_requires_website_build(tmp_path):
    with pytest.raises(RuntimeError, match="Website build missing"):
        create_hosted_app(dist=tmp_path)
