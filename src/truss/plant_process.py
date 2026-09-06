"""M2: independent virtual enforcer process. No coordinator or allocator imports."""

import time
import json
import os
from pathlib import Path
from .runtime_common import ProcessContext
from .config import load_member
from .clock import domain_id
from .plant import Plant
from .schemas import (
    PlantBind,
    PlantCeiling,
    DeviceCommand,
    PlantAck,
    DeviceAck,
    MemberMeter,
    DeviceTelemetry,
    DeviceDiscovery,
)


def run(manifest, member_id):
    c = ProcessContext(manifest, "plant", member_id)
    reg = next(m for m in c.policy.members if m.member_id == member_id)
    profile = load_member(Path(c.manifest["config_dir"]) / f"{member_id}.json", reg)
    p = Plant(reg, profile, c.boot, domain_id(), c.policy.registry_revision)
    root = f"{c.root}/member/{member_id}"
    c.start([root + "/plant/bind", root + "/plant/ceiling", root + "/device/+/command"])
    retired = set()
    last_tick = time.monotonic_ns()
    next_meter = next_status = 0
    sample = 0
    fault = False
    max_expiry_lateness_ns = 0
    try:
        while c.running:
            now = time.monotonic_ns()
            if now - last_tick > 250_000_000:
                fault = True
            if p.ceiling and last_tick < int(p.ceiling.expires_mono_ns) <= now:
                max_expiry_lateness_ns = max(
                    max_expiry_lateness_ns, now - int(p.ceiling.expires_mono_ns)
                )
            last_tick = now
            p.tick(now)
            for message in c.drain():
                now = time.monotonic_ns()
                p.tick(now)
                if isinstance(message, PlantBind) and not isinstance(
                    message, PlantCeiling
                ):
                    result = "rejected"
                    if message.member_boot_id not in retired:
                        old = p.binding
                        result = p.bind(message, now)
                        if (
                            result == "applied"
                            and old
                            and old.member_boot_id != message.member_boot_id
                        ):
                            retired.add(old.member_boot_id)
                    ack = PlantAck.model_validate(
                        c.envelope(
                            "truss.plant_ack.v1",
                            member_id=member_id,
                            plant_boot_id=c.boot,
                            binding_id=message.binding_id,
                            kind="bind",
                            ref=None,
                            result=result,
                            reason=None
                            if result in ("applied", "duplicate")
                            else "wrong_boot",
                            active_budget_w=p.budget(now),
                            remaining_ms=0,
                            observed_w=sum(d.observed_w for d in p.devices.values()),
                        )
                    )
                    c.publish(ack)
                elif isinstance(message, PlantCeiling):
                    result = p.apply_ceiling(message, now) if not fault else "rejected"
                    c.publish(
                        PlantAck.model_validate(
                            c.envelope(
                                "truss.plant_ack.v1",
                                member_id=member_id,
                                plant_boot_id=c.boot,
                                binding_id=message.binding_id,
                                kind="ceiling",
                                ref=message.ref,
                                result=result,
                                reason=None
                                if result in ("applied", "duplicate")
                                else "expired"
                                if result == "expired"
                                else "wrong_boot",
                                active_budget_w=p.budget(now),
                                remaining_ms=max(
                                    0,
                                    min(
                                        6000,
                                        (int(message.expires_mono_ns) - now)
                                        // 1_000_000,
                                    ),
                                ),
                                observed_w=sum(
                                    d.observed_w for d in p.devices.values()
                                ),
                            )
                        )
                    )
                elif isinstance(message, DeviceCommand):
                    binding = p.binding
                    fields = (
                        "site_id",
                        "run_id",
                        "member_id",
                        "member_boot_id",
                        "plant_boot_id",
                        "binding_id",
                        "clock_domain_id",
                    )
                    valid = binding and all(
                        getattr(message, f) == getattr(binding, f) for f in fields
                    )
                    valid = (
                        valid
                        and message.device_id in p.devices
                        and p.ceiling
                        and message.ref == p.ceiling.ref
                    )
                    valid = (
                        valid
                        and message.decision.assigned_w == message.desired_w
                        and message.decision.member_budget_w == p.budget(now)
                    )
                    result = (
                        p.command(
                            message.device_id,
                            message.command_id,
                            message.command_version,
                            message.desired_w,
                            int(message.expires_mono_ns),
                            now,
                        )
                        if valid and not fault
                        else "rejected"
                    )
                    d = p.devices.get(message.device_id)
                    c.publish(
                        DeviceAck.model_validate(
                            c.envelope(
                                "truss.ack.v1",
                                member_id=member_id,
                                device_id=message.device_id,
                                plant_boot_id=c.boot,
                                binding_id=message.binding_id,
                                command_id=message.command_id,
                                command_version=message.command_version,
                                ref=message.ref,
                                result=result,
                                reason=None
                                if result in ("applied", "duplicate")
                                else "expired"
                                if result == "expired"
                                else "policy_conflict",
                                observed_state="running"
                                if d and d.observed_w
                                else "idle",
                                observed_w=d.observed_w if d else 0,
                            )
                        )
                    )
            now = time.monotonic_ns()
            p.tick(now)
            if fault:
                p.ceiling = None
                p.tick(now)
            if now >= next_status:
                c.publish(c.status_message("fault" if fault else "online"), retain=True)
                for d in profile.devices:
                    c.publish(
                        DeviceDiscovery.model_validate(
                            c.envelope(
                                "truss.device_discovery.v1",
                                member_id=member_id,
                                device_id=d.device_id,
                                plant_boot_id=c.boot,
                                registry_revision=c.policy.registry_revision,
                                kind=d.kind,
                                label=d.label,
                                max_w=d.max_w,
                                baseline_w=d.baseline_w,
                                flexibility="protected"
                                if d.control_policy != "flexible"
                                else "deferrable",
                                control_policy=d.control_policy,
                                priority=d.priority,
                                interruptible=d.control_policy == "flexible",
                                min_run_ms=0,
                                min_off_ms=0,
                            )
                        ),
                        retain=True,
                    )
                next_status = now + 1_000_000_000
            if now >= next_meter:
                sample += 1
                active = (
                    p.ceiling
                    if p.ceiling and now < int(p.ceiling.expires_mono_ns)
                    else None
                )
                remaining = (
                    max(0, (int(active.expires_mono_ns) - now) // 1_000_000)
                    if active
                    else 0
                )
                common = dict(
                    member_id=member_id,
                    plant_boot_id=c.boot,
                    clock_domain_id=p.domain,
                    sampled_mono_ns=str(now),
                )
                c.publish(
                    MemberMeter.model_validate(
                        c.envelope(
                            "truss.member_meter.v1",
                            **common,
                            observed_w=sum(d.observed_w for d in p.devices.values()),
                            active_budget_w=p.budget(now),
                            floor_w=reg.floor_w,
                            active_ref=active.ref if active else None,
                            lease_ms_remaining=remaining,
                            at_floor=active is None,
                            enforcement_state="fault" if fault else "healthy",
                            sample_seq=sample,
                        )
                    )
                )
                for d in p.devices.values():
                    c.publish(
                        DeviceTelemetry.model_validate(
                            c.envelope(
                                "truss.telemetry.v1",
                                **common,
                                device_id=d.profile.device_id,
                                state="running" if d.observed_w else "deferred",
                                observed_w=d.observed_w,
                                requested_w=d.profile.max_w,
                                remaining_energy_wh=0.0,
                                deadline_in_ms=None,
                                min_run_remaining_ms=0,
                                min_off_remaining_ms=0,
                                last_command_id=d.command_id,
                                last_command_version=d.command_version,
                                active_ref=active.ref if active else None,
                            )
                        )
                    )
                state_path = (
                    Path(c.manifest["runtime_dir"]) / f"{c.publisher_id}-state.json"
                )
                temporary = state_path.with_suffix(".tmp")
                temporary.write_text(
                    json.dumps(
                        dict(
                            source="virtual-plant",
                            run_id=c.policy.run_id,
                            member_id=member_id,
                            plant_boot_id=c.boot,
                            sampled_mono_ns=str(now),
                            floor_w=reg.floor_w,
                            observed_w=sum(d.observed_w for d in p.devices.values()),
                            active_budget_w=p.budget(now),
                            enforcement_state="fault" if fault else "healthy",
                            max_expiry_lateness_ms=max_expiry_lateness_ns / 1_000_000,
                            devices={key: d.observed_w for key, d in p.devices.items()},
                        )
                    )
                )
                os.replace(temporary, state_path)
                next_meter = now + 500_000_000
            time.sleep(0.02)
    finally:
        c.close()
