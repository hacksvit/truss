"""M3: private household process; aggregate offers out, bounded plant commands in."""

import time
from pathlib import Path
from uuid import uuid4
from .runtime_common import ProcessContext
from .clock import domain_id
from .config import load_member
from .member import MemberReceiver
from .local_policy import assign
from .schemas import (
    Status,
    PlantBind,
    PlantCeiling,
    PlantAck,
    Offer,
    LeaseRequest,
    Lease,
    LeaseAck,
    DeviceCommand,
    LocalDecision,
)


def run(manifest, member_id):
    c = ProcessContext(manifest, "member", member_id)
    reg = next(m for m in c.policy.members if m.member_id == member_id)
    profile = load_member(Path(c.manifest["config_dir"]) / f"{member_id}.json", reg)
    receiver = MemberReceiver(
        reg, c.boot, c.policy.site_id, c.policy.run_id, c.policy.registry_revision
    )
    root = f"{c.root}/member/{member_id}"
    c.start(
        [root + "/lease", root + "/plant/status", root + "/plant/ack", root + "/meter"]
    )
    binding = None
    bound = False
    request = None
    request_seq = 0
    command_version = 0
    retired_plants = set()
    next_status = next_request = next_bind = next_retry = 0
    latest_offer = None

    def acknowledge(lease, result, reason, now, confirmed=False):
        left = (
            max(0, (receiver.accepted.deadline_ns - now) // 1_000_000)
            if receiver.accepted
            else 0
        )
        c.publish(
            LeaseAck.model_validate(
                c.envelope(
                    "truss.lease_ack.v1",
                    ref=lease.ref,
                    result=result,
                    reason=reason,
                    accepted_budget_w=receiver.budget(now),
                    lease_ms_remaining=min(6000, left),
                    plant_confirmed=confirmed,
                    observed_w=None,
                    observation_quality="unknown",
                    plant_boot_id=binding.plant_boot_id if binding else None,
                )
            )
        )

    try:
        while c.running:
            now = time.monotonic_ns()
            for message in c.drain():
                now = time.monotonic_ns()
                if (
                    isinstance(message, Status)
                    and message.component == "plant"
                    and message.member_id == member_id
                    and message.state in ("online", "at_floor")
                ):
                    if message.publisher_boot_id in retired_plants:
                        continue
                    if (
                        binding is None
                        or message.publisher_boot_id != binding.plant_boot_id
                    ):
                        if binding:
                            retired_plants.add(binding.plant_boot_id)
                        binding = PlantBind.model_validate(
                            c.envelope(
                                "truss.plant_bind.v1",
                                member_id=member_id,
                                member_boot_id=c.boot,
                                plant_boot_id=message.publisher_boot_id,
                                binding_id=str(uuid4()),
                                clock_domain_id=domain_id(),
                                registry_revision=c.policy.registry_revision,
                            )
                        )
                        bound = False
                        receiver.accepted = None
                        receiver.pending = None
                        request = None
                elif (
                    isinstance(message, PlantAck)
                    and binding
                    and message.binding_id == binding.binding_id
                    and message.plant_boot_id == binding.plant_boot_id
                ):
                    if message.kind == "bind" and message.result in (
                        "applied",
                        "duplicate",
                    ):
                        bound = True
                    elif (
                        message.kind == "ceiling"
                        and message.result in ("applied", "duplicate")
                        and receiver.accepted
                        and message.ref == receiver.accepted.lease.ref
                    ):
                        accepted = receiver.accepted
                        if now >= accepted.deadline_ns:
                            continue
                        assigned = assign(profile, accepted.lease.budget_w)
                        higher = 0
                        for device in sorted(
                            profile.devices, key=lambda d: (-d.priority, d.device_id)
                        ):
                            command_version += 1
                            amount = assigned[device.device_id]
                            reason = (
                                "baseline_only"
                                if device.control_policy != "flexible"
                                else "manual_priority"
                            )
                            decision = LocalDecision(
                                decision_id=str(uuid4()),
                                member_id=member_id,
                                device_id=device.device_id,
                                ref=accepted.lease.ref,
                                offer_seq=latest_offer.seq if latest_offer else 0,
                                requested_w=device.max_w,
                                assigned_w=amount,
                                member_budget_w=accepted.lease.budget_w,
                                reserved_local_baseline_w=sum(
                                    d.baseline_w for d in profile.devices
                                ),
                                higher_priority_assigned_w=higher,
                                reason=reason,
                                deadline_status="none",
                                deadline_in_ms=None,
                            )
                            command = DeviceCommand.model_validate(
                                c.envelope(
                                    "truss.command.v1",
                                    member_id=member_id,
                                    member_boot_id=c.boot,
                                    plant_boot_id=binding.plant_boot_id,
                                    binding_id=binding.binding_id,
                                    device_id=device.device_id,
                                    command_id=str(uuid4()),
                                    command_version=command_version,
                                    ref=accepted.lease.ref,
                                    desired_state="running" if amount else "deferred",
                                    desired_w=amount,
                                    clock_domain_id=binding.clock_domain_id,
                                    expires_mono_ns=str(accepted.deadline_ns),
                                    reason=reason,
                                    decision=decision,
                                )
                            )
                            c.publish(command)
                            higher += amount - device.baseline_w
                        acknowledge(accepted.lease, "applied", None, now, True)
                elif isinstance(message, Lease):
                    result = receiver.accept(message, now)
                    if result == "applied" and binding and bound:
                        accepted = receiver.accepted
                        ceiling = PlantCeiling.model_validate(
                            c.envelope(
                                "truss.plant_ceiling.v1",
                                member_id=member_id,
                                member_boot_id=c.boot,
                                plant_boot_id=binding.plant_boot_id,
                                binding_id=binding.binding_id,
                                clock_domain_id=binding.clock_domain_id,
                                registry_revision=c.policy.registry_revision,
                                ref=message.ref,
                                budget_w=message.budget_w,
                                expires_mono_ns=str(accepted.deadline_ns),
                            )
                        )
                        c.publish(ceiling)
                        acknowledge(message, "applied", None, now)
                    elif result == "duplicate":
                        acknowledge(message, "duplicate", None, now)
                    else:
                        acknowledge(
                            message,
                            "expired" if result == "expired" else "rejected",
                            result if result != "applied" else "wrong_boot",
                            now,
                        )
            now = time.monotonic_ns()
            if binding and not bound and now >= next_bind:
                c.publish(binding)
                next_bind = now + 500_000_000
            if now >= next_status:
                c.publish(
                    c.status_message(
                        "online" if receiver.budget(now) > reg.floor_w else "at_floor"
                    ),
                    retain=True,
                )
                next_status = now + 1_000_000_000
            if bound and now >= next_request:
                latest_offer = Offer.model_validate(
                    c.envelope(
                        "truss.offer.v1",
                        member_id=member_id,
                        member_boot_id=c.boot,
                        registry_revision=c.policy.registry_revision,
                        floor_w=reg.floor_w,
                        firm_w=reg.floor_w,
                        useful_w=min(reg.max_w, sum(d.max_w for d in profile.devices)),
                        deadline_energy_wh=0.0,
                        deadline_in_ms=None,
                        debt_wh=0.0,
                        debt_revision=0,
                        reported_curtailment_wh=0.0,
                    )
                )
                c.publish(latest_offer)
                request_seq += 1
                request_id = str(uuid4())
                receiver.open_request(request_id, now)
                request = LeaseRequest.model_validate(
                    c.envelope(
                        "truss.lease_request.v1",
                        member_id=member_id,
                        member_boot_id=c.boot,
                        request_id=request_id,
                        request_seq=request_seq,
                        offer_seq=latest_offer.seq,
                        registry_revision=c.policy.registry_revision,
                        ttl_ms=6000,
                    )
                )
                c.publish(request)
                next_request = now + 2_000_000_000
                next_retry = now + 500_000_000
            elif request and receiver.pending and now >= next_retry:
                c.publish(request)
                next_retry = now + 500_000_000
            time.sleep(0.02)
    finally:
        c.close()
