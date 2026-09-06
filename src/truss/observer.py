"""M5: live MQTT evidence and operator projection; has no grant publisher."""

import json
import sqlite3
import threading
import time
from pathlib import Path
from uuid import uuid4
from .runtime_common import ProcessContext, utc_now
from .authority_store import AuthorityStore
from .events import EventLog
from .clock import domain_id
from .config import load_member
from .transport import topic_for
from .schemas import (
    Status,
    Lease,
    MemberMeter,
    DeviceTelemetry,
    DeviceAck,
    DeviceCommand,
    Plan,
    StageTiming,
    CapacityEvent,
)
from .api_models import (
    Snapshot,
    SiteView,
    MemberView,
    DeviceView,
    LeaseView,
    Capabilities,
    EventView,
    MetricsView,
    Operation,
)


class LiveState:
    source = "live"

    def __init__(self, run):
        self.run = run
        self.c = ProcessContext(run.manifest_path, "evidence")
        self.policy = self.c.policy
        self.publisher = ProcessContext(run.manifest_path, "api-control")
        self.publish_lock = threading.Lock()
        self.run_id = self.policy.run_id
        self.stream_id = str(uuid4())
        self.revision = 0
        self.profiles = {
            m.member_id: load_member(
                Path(self.c.manifest["config_dir"]) / f"{m.member_id}.json", m
            )
            for m in self.policy.members
        }
        self.domain = domain_id()
        self.lock = threading.RLock()
        self.running = False
        self.thread = None
        self.events = []
        self.events_cutoff_seq = 0
        self.latest = {}
        self.leases = {}
        self.seen = {}
        self.boots = {}
        self.retired = {}
        self.initial_hold = time.monotonic_ns() + 6_400_000_000
        self.gaps = 0
        self.failure = None
        self.log = EventLog(run.directory / "events.jsonl")
        self.sample_key = None
        self.eligible = 0
        self.within = 0
        self.unknown = 0
        self.started = time.monotonic_ns()
        self.cap_changed = None
        self.last_cap = self.policy.cap_w
        self.time_to_safe = None

    def start(self):
        self.c.start([self.c.root + "/#"])
        self.publisher.start([])
        self.running = True
        self.thread = threading.Thread(
            target=self._consume, daemon=True, name="truss-evidence"
        )
        self.thread.start()

    def close(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.c.close()
        self.publisher.close()

    def _consume(self):
        dropped = 0
        next_sample = 0
        connected = True
        while self.running:
            try:
                with self.lock:
                    is_connected = self.c.transport.connected.is_set()
                    if connected and not is_connected:
                        self.record_gap("broker_disconnected")
                    if not connected and is_connected:
                        self.initial_hold = time.monotonic_ns() + 6_400_000_000
                    connected = is_connected
                    if self.c.dropped != dropped:
                        self.record_gap(
                            "observer_queue_overflow", self.c.dropped - dropped
                        )
                        dropped = self.c.dropped
                        self.initial_hold = time.monotonic_ns() + 6_400_000_000
                    for m in self.c.drain(256):
                        self.ingest(m, time.monotonic_ns())
                    now = time.monotonic_ns()
                    if now >= next_sample:
                        self._snapshot(now)
                        next_sample = now + 500_000_000
                time.sleep(0.025)
            except Exception as exc:
                self.failure = type(exc).__name__ + ": " + str(exc)
                self.gaps += 1
                self.running = False

    def append_event(self, event):
        self.events.append(event)
        if len(self.events) > 500:
            self.events_cutoff_seq = self.events[-501].seq
            self.events = self.events[-500:]

    def record_gap(self, reason, lost_messages=None):
        self.gaps += 1
        record = self.log.append(
            run_id=self.run_id,
            received_at=utc_now(),
            received_mono_ns=str(time.monotonic_ns()),
            kind="observation_gap",
            topic=None,
            payload_schema="truss.observation_gap.v1",
            payload={"reason": reason, "lost_messages": lost_messages},
            correlation_id=None,
        )
        self.append_event(
            EventView(
                seq=record.event_seq,
                at=record.received_at,
                kind="observation_gap",
                code=reason,
                text=f"Observation gap: {reason}. Missing samples are unknown.",
            )
        )

    def ingest(self, m, now):
        topic = topic_for(m)
        # Persist all validated delivered facts, including duplicates; state dedups separately.
        record = self.log.append(
            run_id=self.run_id,
            received_at=utc_now(),
            received_mono_ns=str(now),
            kind="mqtt",
            topic=topic,
            payload_schema=m.schema_id,
            payload=m.model_dump(by_alias=True),
            correlation_id=m.correlation_id,
        )
        key = (m.publisher_id, m.publisher_boot_id, topic)
        will = isinstance(m, Status) and m.source == "will"
        old_status = self.latest.get(topic)
        if (
            will
            and old_status
            and isinstance(old_status[0], Status)
            and old_status[0].connection_id != m.connection_id
        ):
            return
        if m.publisher_boot_id in self.retired.get(m.publisher_id, set()):
            return
        previous_boot = self.boots.get(m.publisher_id)
        if previous_boot and previous_boot != m.publisher_boot_id:
            self.retired.setdefault(m.publisher_id, set()).add(previous_boot)
        self.boots[m.publisher_id] = m.publisher_boot_id
        if not will and m.seq <= self.seen.get(key, -1):
            return
        if not will:
            self.seen[key] = m.seq
        self.latest[topic] = (m, now)
        if isinstance(m, Lease):
            self.leases.setdefault(m.ref.lease_id, (m, now + 6_400_000_000))
        if isinstance(m, (Status, Lease, DeviceAck, CapacityEvent)):
            code = (
                m.state
                if isinstance(m, Status)
                else m.result
                if isinstance(m, DeviceAck)
                else "cap_change"
                if isinstance(m, CapacityEvent)
                else "grant"
            )
            # Heartbeats do not flood the visible event tail.
            if not isinstance(m, Status) or m.state not in ("online", "at_floor"):
                self.append_event(
                    EventView(
                        seq=record.event_seq,
                        at=record.received_at,
                        kind=m.schema_id,
                        code=code,
                        text=f"{m.publisher_id}: {code}",
                        member_id=getattr(m, "member_id", None),
                    )
                )

    def control_state(self):
        store = AuthorityStore(self.c.manifest["authority_path"])
        try:
            return store.get("control")
        finally:
            store.close()

    @property
    def control_revision(self):
        return self.control_state()["revision"]

    @property
    def operations(self):
        db = sqlite3.connect(self.c.manifest["authority_path"])
        try:
            return [
                Operation.model_validate(json.loads(row[0]))
                for row in db.execute(
                    "SELECT result FROM operations ORDER BY rowid DESC LIMIT 20"
                ).fetchall()
            ][::-1]
        finally:
            db.close()

    def control(self, body, key, kind):
        encoded = json.dumps(
            {"kind": kind, **body.model_dump()}, sort_keys=True, separators=(",", ":")
        )
        store = AuthorityStore(self.c.manifest["authority_path"])
        try:
            store.db.execute("BEGIN IMMEDIATE")
            old = store.db.execute(
                "SELECT body,result FROM operations WHERE key=?", (key,)
            ).fetchone()
            if old:
                store.db.rollback()
                if old[0] != encoded:
                    raise ValueError("idempotency_conflict")
                return Operation.model_validate(json.loads(old[1]))
            current = store.get("control")
            if (
                body.run_id != self.run_id
                or body.source != "live"
                or body.expected_control_revision != current["revision"]
            ):
                store.db.rollback()
                raise ValueError("revision_conflict")
            if kind == "chaos" and body.action not in (
                "kill_coordinator",
                "restart_coordinator",
                "kill_member",
                "restart_member",
                "kill_broker",
                "restart_broker",
            ):
                store.db.rollback()
                raise ValueError("unsupported")
            if (
                kind == "chaos"
                and "member" in body.action
                and body.member_id not in self.profiles
            ):
                store.db.rollback()
                raise ValueError("unknown_member")
            current["revision"] += 1
            if kind == "cap":
                current["cap_w"] = body.watts
            operation = Operation(
                operation_id=str(uuid4()),
                run_id=self.run_id,
                kind=kind,
                status="applied" if kind == "cap" else "queued",
                control_revision=current["revision"],
                created_at=utc_now(),
                finished_at=utc_now() if kind == "cap" else None,
                message="Desired cap committed; old authority must expire before compliance is claimed."
                if kind == "cap"
                else "Owned process action queued.",
            )
            store.db.execute(
                "UPDATE kv SET value=? WHERE key=?", (json.dumps(current), "control")
            )
            store.db.execute(
                "INSERT INTO operations VALUES (?,?,?)",
                (key, encoded, operation.model_dump_json()),
            )
            store.db.commit()
            if kind == "cap":
                with self.publish_lock:
                    event = CapacityEvent.model_validate(
                        self.publisher.envelope(
                            "truss.capacity.v1",
                            event_id=str(uuid4()),
                            operation_id=operation.operation_id,
                            cap_revision=current["revision"],
                            expected_previous_revision=current["revision"] - 1,
                            cap_w=body.watts,
                            source="operator",
                            reason="cap_change",
                        )
                    )
                    # Notification is best effort. SQLite commit remains authoritative
                    # even when broker loss prevents the event from being delivered.
                    self.publisher.publish(event)
            if kind == "chaos":
                try:
                    self.run.act(body.action, body.member_id)
                    operation = operation.model_copy(
                        update={
                            "status": "applied",
                            "finished_at": utc_now(),
                            "message": f"Actual owned process action completed: {body.action}",
                        }
                    )
                except Exception as exc:
                    operation = operation.model_copy(
                        update={
                            "status": "failed",
                            "finished_at": utc_now(),
                            "error": str(exc),
                        }
                    )
                with store.db:
                    store.db.execute(
                        "UPDATE operations SET result=? WHERE key=?",
                        (operation.model_dump_json(), key),
                    )
            return operation
        finally:
            store.close()

    def snapshot(self):
        with self.lock:
            return self._snapshot(time.monotonic_ns())

    def _snapshot(self, now):
        control = self.control_state()
        cap = control["cap_w"]
        self.revision += 1
        if cap != self.last_cap:
            self.cap_changed = now
            self.last_cap = cap
            self.time_to_safe = None

        def latest(suffix, cls):
            item = self.latest.get(self.c.root + "/" + suffix)
            return (
                item
                if item
                and isinstance(item[0], cls)
                and self.boots.get(item[0].publisher_id) == item[0].publisher_boot_id
                else (None, None)
            )

        def age(message, received):
            if not message:
                return None
            if hasattr(message, "sampled_mono_ns"):
                if message.clock_domain_id != self.domain:
                    return None
                nanos = now - int(message.sampled_mono_ns)
                return nanos // 1_000_000 if nanos >= 0 else None
            return (now - received) // 1_000_000

        status, received = latest("coordinator/status", Status)
        coordinator = (
            "unknown"
            if not status or age(status, received) > 1500
            else status.state
            if status.state in ("online", "recovering", "offline")
            else "unknown"
        )
        plan, plan_received = latest("plan", Plan)
        rows = (
            {r.member_id: r for r in plan.allocations}
            if plan and now - plan_received < 1_500_000_000
            else {}
        )
        self.leases = {k: v for k, v in self.leases.items() if v[1] > now}
        members = []
        sample_keys = []
        all_current = True
        for reg in self.policy.members:
            prefix = f"member/{reg.member_id}"
            meter, meter_received = latest(prefix + "/meter", MemberMeter)
            meter_age = age(meter, meter_received)
            quality = (
                "unknown"
                if meter is None or meter_age is None
                else "fresh"
                if meter_age <= 1500
                and meter.enforcement_state == "healthy"
                and not self.failure
                else "stale"
            )
            if quality != "fresh":
                all_current = False
            active_lease = max(
                (
                    item[0]
                    for item in self.leases.values()
                    if item[0].ref.member_id == reg.member_id
                ),
                key=lambda lease: (lease.ref.epoch, lease.ref.version),
                default=None,
            )
            reserved = max(
                [reg.floor_w]
                + [
                    g.budget_w
                    for g, end in self.leases.values()
                    if g.ref.member_id == reg.member_id
                ]
            )
            if now < self.initial_hold or self.failure:
                reserved = reg.max_w
            if reg.member_id in rows:
                reserved = max(reserved, rows[reg.member_id].reserved_w)
            devices = []
            for profile in self.profiles[reg.member_id].devices:
                leaf = prefix + "/device/" + profile.device_id
                telemetry, tr = latest(leaf + "/telemetry", DeviceTelemetry)
                a = age(telemetry, tr)
                q = (
                    "unknown"
                    if telemetry is None or a is None
                    else "fresh"
                    if a <= 1500 and quality == "fresh"
                    else "stale"
                )
                ack, _ = latest(leaf + "/ack", DeviceAck)
                command, _ = latest(leaf + "/command", DeviceCommand)
                matched = (
                    ack
                    and telemetry
                    and command
                    and ack.command_id
                    == telemetry.last_command_id
                    == command.command_id
                    and ack.ref == command.ref == telemetry.active_ref
                    and ack.observed_w == telemetry.observed_w
                )
                ack_state = (
                    "verified"
                    if matched
                    and ack.result in ("applied", "duplicate")
                    and q == "fresh"
                    else "rejected"
                    if ack and ack.result == "rejected"
                    else "stale"
                    if q != "fresh"
                    else "pending"
                    if command
                    else "none"
                )
                devices.append(
                    DeviceView(
                        id=profile.device_id,
                        kind=profile.kind,
                        label=profile.label,
                        w=telemetry.observed_w if telemetry else None,
                        requested_w=telemetry.requested_w
                        if telemetry
                        else profile.max_w,
                        state=telemetry.state if telemetry else "unknown",
                        quality=q,
                        sample_age_ms=a,
                        ack=ack_state,
                        protected=profile.control_policy != "flexible",
                        control_policy=profile.control_policy,
                        curtailment_eligible=profile.control_policy == "flexible",
                        command_id=command.command_id if command else None,
                        decision=command.decision if command and matched else None,
                    )
                )
            row = rows.get(reg.member_id)
            remaining = (
                max(0, meter.lease_ms_remaining - meter_age)
                if meter and meter_age is not None
                else None
            )
            lease_view = LeaseView(
                ref=meter.active_ref if meter else None,
                remaining_ms=remaining,
                sample_age_ms=meter_age,
                quality=quality,
                plant_confirmed=quality == "fresh" and meter.active_ref is not None,
            )
            members.append(
                MemberView(
                    id=reg.member_id,
                    boot_id=meter.active_ref.member_boot_id
                    if meter and meter.active_ref
                    else None,
                    plant_boot_id=meter.plant_boot_id if meter else None,
                    floor_w=reg.floor_w,
                    max_w=reg.max_w,
                    firm_w=reg.floor_w,
                    useful_w=row.useful_w if row else reg.max_w,
                    target_w=row.target_w if row else None,
                    issued_w=active_lease.budget_w if active_lease else None,
                    reserved_w=reserved,
                    observed_w=meter.observed_w if meter else None,
                    observed_quality=quality,
                    sample_age_ms=meter_age,
                    lease=lease_view,
                    status="fault"
                    if meter and meter.enforcement_state == "fault"
                    else "stale"
                    if quality != "fresh"
                    else "at_floor"
                    if meter.at_floor
                    else "ok",
                    devices=devices,
                    basis=active_lease.basis
                    if active_lease and meter and active_lease.ref == meter.active_ref
                    else None,
                )
            )
            sample_keys.append(
                (meter.plant_boot_id, meter.sample_seq) if meter else None
            )
        observed = sum(m.observed_w for m in members) if all_current else None
        total = sum(m.reserved_w for m in members) + self.policy.reserve_w
        floor = sum(m.floor_w for m in members)
        deficit = max(0, floor + self.policy.reserve_w - cap)
        state = (
            "infeasible"
            if deficit
            else "recovering"
            if coordinator == "recovering" or now < self.initial_hold
            else "cap_transition"
            if total > cap
            else "unverified"
            if observed is None
            else "leased"
        )
        compliance = (
            "unknown"
            if observed is None
            else "within_cap"
            if observed + self.policy.external_bound_w <= cap
            else "over_cap"
        )
        if tuple(sample_keys) != self.sample_key:
            self.sample_key = tuple(sample_keys)
            if observed is None:
                self.unknown += 1
            else:
                self.eligible += 1
                self.within += int(compliance == "within_cap")
                if (
                    self.cap_changed is not None
                    and not deficit
                    and observed + self.policy.reserve_w <= cap
                    and all(
                        m.sample_age_ms is not None
                        and now - m.sample_age_ms * 1_000_000 >= self.cap_changed
                        for m in members
                    )
                    and self.time_to_safe is None
                ):
                    self.time_to_safe = (now - self.cap_changed) // 1_000_000
        site = SiteView(
            id=self.policy.site_id,
            cap_w=cap,
            cap_revision=control["revision"],
            measurement_reserve_w=self.policy.measurement_reserve_w,
            external_bound_w=self.policy.external_bound_w,
            baseline_sum_w=floor,
            reserved_member_w=sum(m.reserved_w for m in members),
            unverified_member_reservation_w=sum(
                m.reserved_w for m in members if m.observed_quality != "fresh"
            ),
            available_for_new_grants_w=max(0, cap - total),
            exposure_w=total,
            observed_w=observed,
            observed_quality="fresh" if all_current else "unknown",
            oldest_sample_age_ms=max((m.sample_age_ms or 0 for m in members), default=0)
            if all_current
            else None,
            state=state,
            coordinator_status=coordinator,
            recovering_ms_remaining=max(
                0, status.recovery_ms_remaining - age(status, received)
            )
            if status and coordinator == "recovering"
            else None,
            compliance=compliance,
            deficit_w=deficit,
            affected_members=[m.id for m in members] if deficit else [],
            rule="equal_surplus",
            plan_id=plan.plan_id if plan else None,
            timing=StageTiming(
                input_validation_ms=None,
                allocation_ms=None,
                plan_validation_ms=None,
                admission_ms=None,
            ),
        )
        return Snapshot(
            run_id=self.run_id,
            stream_id=self.stream_id,
            revision=self.revision,
            control_revision=control["revision"],
            source="live",
            generated_at=utc_now(),
            event_cursor=self.log.seq,
            site=site,
            members=members,
            events=self.events[-50:],
            operations=self.operations,
            metrics=MetricsView(
                observation_window_ms=(now - self.started) // 1_000_000,
                eligible_samples=self.eligible,
                within_cap_samples=self.within,
                unknown_samples=self.unknown,
                cap_compliance_pct=100 * self.within / self.eligible
                if self.eligible
                else None,
                time_to_safe_ms=self.time_to_safe,
                time_to_safe_status="infeasible"
                if deficit
                else "observed"
                if self.time_to_safe is not None
                else "unknown"
                if observed is None
                else "pending",
                replay_gaps=self.gaps,
            ),
            capabilities=Capabilities(chaos=True),
        )
