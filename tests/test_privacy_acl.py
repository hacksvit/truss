import json
from pathlib import Path
import pytest
from truss.transport import topic_for, validate_delivery
from truss.schemas import decode


def test_topic_identity_and_private_delivery(wire):
    raw = json.dumps(wire["truss.telemetry.v1"]).encode()
    m = decode(raw)
    with pytest.raises(ValueError, match="private"):
        validate_delivery(topic_for(m), raw, "coordinator")
    with pytest.raises(ValueError, match="identity"):
        validate_delivery(topic_for(m).replace("member-a", "member-b"), raw, "observer")


def test_coordinator_acl_has_no_private_subscription():
    text = (
        Path("config/acl")
        .read_text()
        .split("user coordinator\n")[1]
        .split("\nuser ")[0]
    )
    assert "/device/" not in text and "/plant/" not in text and "/#" not in text


def test_broker_enforces_privacy(live_stack):
    import threading, time
    from paho.mqtt import client as mqtt

    run, _ = live_stack
    manifest = json.loads(run.manifest_path.read_text())
    credentials = json.loads(Path(manifest["credentials_path"]).read_text())
    root = f"truss/v1/site/{run.policy.site_id}"
    clients = []

    def connect(username, password):
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv5)
        clients.append(c)
        event = threading.Event()
        codes = []
        c.username_pw_set(username, password)

        def connected(client, userdata, flags, reason, properties):
            codes.append(reason)
            event.set()

        c.on_connect = connected
        c.connect("127.0.0.1", run.port)
        c.loop_start()
        assert event.wait(5)
        return c, codes[0]

    try:
        _, reason = connect("member-a", "deliberately-wrong-password")
        assert reason.is_failure
        coordinator, reason = connect("coordinator", credentials["coordinator"])
        assert not reason.is_failure
        received = []
        coordinator.on_message = lambda c, u, m: received.append(m.topic)
        allowed = root + "/member/member-a/offer"
        coordinator.subscribe(allowed, qos=1)
        coordinator.subscribe(root + "/member/member-a/device/+/telemetry", qos=1)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and allowed not in received:
            time.sleep(0.05)
        assert allowed in received
        time.sleep(0.7)
        assert not any("/device/" in t for t in received)
        member, reason = connect("member-a", credentials["member-a"])
        assert not reason.is_failure
        published = threading.Event()
        reasons = []

        def on_publish(c, u, mid, reason, properties):
            reasons.append(reason)
            published.set()

        member.on_publish = on_publish
        member.publish(root + "/member/member-a/lease", b"{}", qos=1)
        assert published.wait(3) and reasons[0].is_failure
    finally:
        for c in clients:
            c.disconnect()
            c.loop_stop()
