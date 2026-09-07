"""M3: bounded per-process MQTT inbox, identity and signal lifecycle."""

import json
import queue
import signal
import time
from random import Random
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .config import load_run
from .transport import MQTTTransport
from .schemas import Status
from .faults import DeliveryFault, delivery_decision
from .transport import topic_for


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ProcessContext:
    def __init__(self, manifest_path, role, member_id=None, epoch=None):
        self.manifest_path = Path(manifest_path)
        self.manifest = json.loads(self.manifest_path.read_text())
        self.policy = load_run(self.manifest["policy_path"])
        self.role, self.member_id, self.epoch = role, member_id, epoch
        self.publisher_id = (
            role
            if member_id is None
            else member_id
            if role == "member"
            else "plant-" + member_id.removeprefix("member-")
        )
        self.boot = str(uuid4())
        self.connection = str(uuid4())
        self.sequence = 0
        self.queue = queue.Queue(maxsize=1024)
        self.dropped = 0
        self.running = True
        self.delayed = queue.Queue(maxsize=1024)
        self.pending_delayed = []
        self.rng = Random(42)
        credentials = json.loads(Path(self.manifest["credentials_path"]).read_text())
        self.transport = MQTTTransport(
            f"{self.publisher_id}-{self.boot}",
            role,
            self.publisher_id,
            credentials[self.publisher_id],
        )
        if role in ("coordinator", "member", "plant"):
            self.transport.set_will(self.status_message("offline", source="will"))

            def prepare_connection(*_):
                self.connection = str(uuid4())
                self.transport.set_will(self.status_message("offline", source="will"))

            self.transport.client.on_pre_connect = prepare_connection

    def envelope(self, schema, **fields):
        self.sequence += 1
        return dict(
            schema=schema,
            site_id=self.policy.site_id,
            run_id=self.policy.run_id,
            publisher_id=self.publisher_id,
            publisher_boot_id=self.boot,
            seq=self.sequence,
            ts=utc_now(),
            correlation_id=None,
            **fields,
        )

    def status_message(self, state, source="heartbeat", recovery=None):
        body = self.envelope(
            "truss.status.v1",
            component=self.role,
            component_id=self.publisher_id,
            connection_id=self.connection,
            source=source,
            state=state,
            member_id=self.member_id,
            epoch=self.epoch,
            registry_revision=self.policy.registry_revision,
            recovery_ms_remaining=recovery,
            reason="recovery" if recovery is not None else None,
        )
        if source == "will":
            body["seq"] = 0
        return Status.model_validate(body)

    def enqueue(self, message):
        if (
            message.site_id != self.policy.site_id
            or message.run_id != self.policy.run_id
        ):
            return
        decision, delay = delivery_decision(
            self.fault(), topic_for(message), time.monotonic_ns(), self.rng
        )
        if decision == "drop":
            return
        try:
            if decision == "delay":
                self.delayed.put_nowait(
                    (time.monotonic_ns() + delay * 1_000_000, message)
                )
            else:
                self.queue.put_nowait(message)
        except queue.Full:
            self.dropped += 1

    def fault(self):
        path = Path(self.manifest["runtime_dir"]) / "faults.json"
        try:
            data = json.loads(path.read_text())
            target = self.role + ":" + self.member_id if self.member_id else self.role
            if data.pop("target") != target:
                return None
            return DeliveryFault(**data)
        except FileNotFoundError:
            return None

    def start(self, subscriptions, *, install_signals=True):
        self.transport.start(
            "127.0.0.1", self.manifest["broker_port"], subscriptions, self.enqueue
        )
        if not self.transport.connected.wait(5):
            raise RuntimeError("broker connection unavailable")
        if install_signals:
            signal.signal(signal.SIGTERM, lambda *_: setattr(self, "running", False))
            signal.signal(signal.SIGINT, lambda *_: setattr(self, "running", False))

    def drain(self, limit=64):
        while len(self.pending_delayed) < 1024:
            try:
                self.pending_delayed.append(self.delayed.get_nowait())
            except queue.Empty:
                break
        now = time.monotonic_ns()
        waiting = []
        ready = []
        for deadline, message in self.pending_delayed:
            (ready if deadline <= now else waiting).append(
                message if deadline <= now else (deadline, message)
            )
        self.pending_delayed = waiting
        for message in ready[:limit]:
            yield message
        self.pending_delayed.extend((now, message) for message in ready[limit:])
        for _ in range(max(0, limit - len(ready))):
            try:
                yield self.queue.get_nowait()
            except queue.Empty:
                return

    def publish(self, message, retain=False):
        decision, _ = delivery_decision(
            self.fault(), topic_for(message), time.monotonic_ns(), self.rng
        )
        if decision == "drop":
            return False
        result = self.transport.publish(message, retain=retain)
        return result.rc == 0

    def close(self):
        if (
            self.role in ("coordinator", "member", "plant")
            and self.transport.connected.is_set()
        ):
            self.publish(self.status_message("offline", source="graceful"), retain=True)
        self.transport.close()

    @property
    def root(self):
        return f"truss/v1/site/{self.policy.site_id}"
