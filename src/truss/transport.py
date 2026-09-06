"""MQTT 5 adapter and topic mapping. Owner M3. ProcessContext owns bounded delivery."""

from collections.abc import Callable
from threading import Event
from paho.mqtt import client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
from .schemas import Envelope, Status, decode, encode


def topic_for(message: Envelope) -> str:
    root = f"truss/v1/site/{message.site_id}"
    member = getattr(message, "member_id", None) or getattr(
        getattr(message, "ref", None), "member_id", None
    )
    kind = message.schema_id
    if isinstance(message, Status):
        suffix = (
            "coordinator/status"
            if message.component == "coordinator"
            else f"member/{member}/"
            + ("plant/status" if message.component == "plant" else "status")
        )
    elif kind == "truss.capacity.v1":
        suffix = "event/capacity"
    elif kind == "truss.plan.v1":
        suffix = "plan"
    else:
        suffixes = {
            "offer": "offer",
            "lease_request": "lease/request",
            "lease": "lease",
            "lease_ack": "lease/ack",
            "member_meter": "meter",
            "plant_bind": "plant/bind",
            "plant_ceiling": "plant/ceiling",
            "plant_ack": "plant/ack",
            "local_policy": "policy",
            "policy_ack": "policy/ack",
            "device_discovery": "discovery",
            "telemetry": "telemetry",
            "command": "command",
            "ack": "ack",
        }
        leaf = suffixes[kind.split(".")[1]]
        if hasattr(message, "device_id") and kind not in (
            "truss.local_policy.v1",
            "truss.policy_ack.v1",
        ):
            suffix = f"member/{member}/device/{message.device_id}/{leaf}"
        else:
            suffix = f"member/{member}/{leaf}"
    return f"{root}/{suffix}"


def validate_delivery(topic: str, payload: bytes, role: str) -> Envelope:
    message = decode(payload)
    if topic != topic_for(message):
        raise ValueError("topic/payload identity mismatch")
    kind = message.schema_id.split(".")[1]
    member = getattr(message, "member_id", None) or getattr(
        getattr(message, "ref", None), "member_id", None
    )
    plant_kinds = {"plant_ack", "member_meter", "device_discovery", "telemetry", "ack"}
    expected = (
        "coordinator"
        if kind in ("lease", "plan")
        else "api-control"
        if kind in ("capacity", "local_policy")
        else "plant-" + member.removeprefix("member-")
        if kind in plant_kinds
        else member
    )
    if isinstance(message, Status):
        expected = message.component_id
    if message.publisher_id != expected:
        raise ValueError("publisher/topic role mismatch")
    field = "plant_boot_id" if kind in plant_kinds else "member_boot_id"
    if hasattr(message, field) and getattr(message, field) != message.publisher_boot_id:
        raise ValueError("publisher boot mismatch")
    if role == "coordinator" and ("/device/" in topic or "/plant/" in topic):
        raise ValueError("coordinator cannot consume private device/plant topics")
    return message


class MQTTTransport:
    """Callbacks run on paho thread; process owner must enqueue into its own loop."""

    def __init__(self, client_id: str, role: str, username: str, password: str):
        self.role = role
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, protocol=mqtt.MQTTv5
        )
        self.client.username_pw_set(username, password)
        self.errors: list[str] = []
        self.connected = Event()
        self.client.max_queued_messages_set(1024)
        self.client.max_inflight_messages_set(20)

    def set_will(self, message: Status):
        self.client.will_set(topic_for(message), encode(message), qos=1, retain=True)

    def start(
        self,
        host: str,
        port: int,
        subscriptions: list[str],
        callback: Callable[[Envelope], None],
    ):
        if self.role == "coordinator" and any(
            "/device/" in t or t.endswith("/#") for t in subscriptions
        ):
            raise ValueError(
                "coordinator subscriptions must be explicitly aggregate-only"
            )

        def connected(client, userdata, flags, reason, properties):
            if not reason.is_failure:
                for topic in subscriptions:
                    client.subscribe(topic, qos=1)
                self.connected.set()

        def disconnected(client, userdata, flags, reason, properties):
            self.connected.clear()

        def received(client, userdata, message):
            try:
                if message.retain and not message.topic.endswith(
                    ("/status", "/plan", "/discovery")
                ):
                    raise ValueError("retained authority/control rejected")
                callback(validate_delivery(message.topic, message.payload, self.role))
            except ValueError as error:
                self.errors = (self.errors + [str(error)])[-100:]

        self.client.on_connect, self.client.on_message = connected, received
        self.client.on_disconnect = disconnected
        self.client.reconnect_delay_set(1, 2)
        props = Properties(PacketTypes.CONNECT)
        props.SessionExpiryInterval = 0
        self.client.connect(host, port, keepalive=2, clean_start=True, properties=props)
        self.client.loop_start()

    def publish(self, message: Envelope, *, retain: bool = False):
        topic = topic_for(message)
        if message.schema_id == "truss.lease.v1" and self.role != "coordinator":
            raise ValueError("only coordinator can publish leases")
        if retain and message.schema_id not in (
            "truss.status.v1",
            "truss.plan.v1",
            "truss.device_discovery.v1",
        ):
            raise ValueError("authority/control cannot be retained")
        props = Properties(PacketTypes.PUBLISH)
        props.MessageExpiryInterval = 6
        return self.client.publish(
            topic, encode(message), qos=1, retain=retain, properties=props
        )

    def close(self):
        self.client.disconnect()
        self.client.loop_stop()
