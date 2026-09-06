"""M1: serialized, durable, sole grant issuer. No private device config is read."""

import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4
from .runtime_common import ProcessContext
from .authority_store import AuthorityStore
from .coordinator import Coordinator
from .allocator import Demand
from .fairness import ServiceDeficit
from .schemas import (
    Offer,
    Status,
    LeaseRequest,
    Lease,
    LeaseRef,
    Basis,
    Plan,
    AllocationRow,
    ValidationResult,
    StageTiming,
)


def canonical_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def run(manifest):
    config = json.loads(Path(manifest).read_text())
    store = AuthorityStore(config["authority_path"])
    epoch = store.claim_epoch(Path(config["runtime_dir"]) / "coordinator.lock")
    c = ProcessContext(manifest, "coordinator", epoch=epoch)
    core = Coordinator(c.policy, time.monotonic_ns())
    registrations = {m.member_id: m for m in c.policy.members}
    c.start(
        [
            c.root + "/member/+/offer",
            c.root + "/member/+/status",
            c.root + "/member/+/lease/request",
            c.root + "/event/capacity",
        ]
    )
    offers = {}
    statuses = {}
    try:
        saved_debt = store.get("debt")
    except ValueError:
        saved_debt = {}
    debt = ServiceDeficit(c.policy.members, time.monotonic_ns(), saved_debt)
    retired = {m: set() for m in registrations}
    grants = {}
    version = 0
    plan_version = 0
    next_status = next_plan = 0
    policy_hash = canonical_hash(c.policy.model_dump())
    try:
        while c.running:
            now = time.monotonic_ns()
            debt.advance(now)
            control = store.get("control", {"revision": 1, "cap_w": c.policy.cap_w})
            cap = control["cap_w"]
            cap_revision = control["revision"]
            rule = (
                control.get("rule", "equal_surplus")
                if debt.enabled
                else "equal_surplus"
            )

            def capture():
                debt.capture(
                    now,
                    offers,
                    statuses,
                    core.ledger,
                    cap,
                    c.policy.reserve_w,
                    c.transport.connected.is_set(),
                )

            capture()

            def demands():
                return [
                    Demand(
                        m.member_id,
                        m.floor_w,
                        offers[m.member_id][0].useful_w
                        if m.member_id in offers
                        and now - offers[m.member_id][1] < 3_000_000_000
                        else m.floor_w,
                        debt.weight(m.member_id, rule),
                    )
                    for m in c.policy.members
                ]

            for message in c.drain():
                now = time.monotonic_ns()
                debt.advance(now)
                if isinstance(message, Status):
                    previous = statuses.get(message.publisher_id)
                    if (
                        previous
                        and previous[0].publisher_boot_id == message.publisher_boot_id
                    ):
                        if message.source == "will":
                            if previous[0].connection_id != message.connection_id:
                                continue
                        elif message.seq <= previous[0].seq:
                            continue
                    if message.publisher_boot_id in retired.get(
                        message.publisher_id, set()
                    ):
                        continue
                    statuses[message.publisher_id] = (message, now)
                    capture()
                elif isinstance(message, Offer):
                    reg = registrations.get(message.member_id)
                    if (
                        not reg
                        or message.registry_revision != c.policy.registry_revision
                        or message.floor_w != reg.floor_w
                        or message.useful_w > reg.max_w
                    ):
                        if reg:
                            offers.pop(message.member_id, None)
                            capture()
                        continue
                    if message.member_boot_id in retired[message.member_id]:
                        continue
                    previous = offers.get(message.member_id)
                    if previous:
                        if (
                            previous[0].member_boot_id == message.member_boot_id
                            and message.seq <= previous[0].seq
                        ):
                            continue
                        if previous[0].member_boot_id != message.member_boot_id:
                            retired[message.member_id].add(previous[0].member_boot_id)
                    offers[message.member_id] = (message, now)
                    capture()
                elif isinstance(message, LeaseRequest):
                    offered = offers.get(message.member_id)
                    if (
                        not offered
                        or message.registry_revision != c.policy.registry_revision
                        or message.member_boot_id != offered[0].member_boot_id
                    ):
                        continue
                    key = (
                        message.member_id,
                        message.member_boot_id,
                        message.request_id,
                    )
                    if key in grants:
                        original, expiry = grants[key]
                        if now < expiry:
                            c.publish(original)
                        continue
                    if (
                        message.offer_seq != offered[0].seq
                        or now - offered[1] >= 3_000_000_000
                    ):
                        continue
                    # Read the committed cap again immediately before admission.
                    store.db.execute("BEGIN IMMEDIATE")
                    control = store.get(
                        "control", {"revision": 1, "cap_w": c.policy.cap_w}
                    )
                    cap = control["cap_w"]
                    cap_revision = control["revision"]
                    rule = (
                        control.get("rule", "equal_surplus")
                        if debt.enabled
                        else "equal_surplus"
                    )
                    capture()
                    frozen = demands()
                    proposal = core.propose(frozen, cap)
                    if not proposal.feasible:
                        store.db.rollback()
                        continue
                    amount = proposal.budgets[message.member_id]
                    before = core.ledger.exposure(now)[message.member_id]
                    admission_started = time.perf_counter_ns()
                    try:
                        reservation = core.ledger.admit(
                            member_id=message.member_id,
                            boot_id=message.member_boot_id,
                            request_id=message.request_id,
                            request_seq=message.request_seq,
                            amount_w=amount,
                            cap_w=cap,
                            reserve_w=c.policy.reserve_w,
                            now_ns=now,
                        )
                    except ValueError:
                        store.db.rollback()
                        continue
                    admission_ms = (time.perf_counter_ns() - admission_started) / 1e6
                    capture()
                    version += 1
                    plan_version += 1
                    plan_id = f"p{epoch}-{plan_version}"
                    exposure = core.ledger.exposure(now)
                    reg = registrations[message.member_id]
                    ref = LeaseRef(
                        member_id=message.member_id,
                        member_boot_id=message.member_boot_id,
                        request_id=message.request_id,
                        epoch=epoch,
                        version=version,
                        lease_id=str(uuid4()),
                        plan_id=plan_id,
                    )
                    snapshot_hash = canonical_hash(
                        {
                            "demands": [
                                d.__dict__ | {"weight": str(d.weight)} for d in frozen
                            ],
                            "cap_w": cap,
                            "cap_revision": cap_revision,
                            "policy_hash": policy_hash,
                            "rule": rule,
                            "debt": debt.dump(),
                        }
                    )
                    basis = Basis(
                        snapshot_id=snapshot_hash,
                        policy_hash=policy_hash,
                        registry_revision=c.policy.registry_revision,
                        cap_revision=cap_revision,
                        cap_w=cap,
                        measurement_reserve_w=c.policy.measurement_reserve_w,
                        external_bound_w=c.policy.external_bound_w,
                        baseline_sum_w=sum(m.floor_w for m in c.policy.members),
                        surplus_pool_w=max(
                            0,
                            cap
                            - c.policy.reserve_w
                            - sum(m.floor_w for m in c.policy.members),
                        ),
                        rule=rule,
                        debt_scale_wh=float(debt.scale),
                        weight_cap=2.0,
                        member_floor_w=reg.floor_w,
                        member_useful_w=offered[0].useful_w,
                        member_debt_wh=float(debt.values[message.member_id]),
                        member_weight=float(debt.weight(message.member_id, rule)),
                        proposed_budget_w=amount,
                        issued_budget_w=amount,
                        reservation_before_w=before,
                        reservation_after_w=exposure[message.member_id],
                        total_exposure_after_w=sum(exposure.values())
                        + c.policy.reserve_w,
                        reason="renewal",
                    )
                    lease = Lease.model_validate(
                        c.envelope(
                            "truss.lease.v1",
                            ref=ref,
                            registry_revision=c.policy.registry_revision,
                            budget_w=amount,
                            ttl_ms=6000,
                            reason="renewal",
                            basis=basis,
                        )
                    )
                    grants[key] = (lease, reservation.release_ns)
                    debt.persist(store)
                    store.db.commit()
                    # Emit the actual plan referenced by this grant, not a later
                    # periodic summary carrying an unrelated plan identifier.
                    rows = []
                    for demand in frozen:
                        current = max(
                            (
                                g[0]
                                for g in grants.values()
                                if g[0].ref.member_id == demand.member_id
                            ),
                            key=lambda g: (g.ref.epoch, g.ref.version),
                            default=None,
                        )
                        rows.append(
                            AllocationRow(
                                member_id=demand.member_id,
                                floor_w=demand.floor_w,
                                useful_w=demand.useful_w,
                                debt_wh=float(debt.values[demand.member_id]),
                                weight=float(demand.weight),
                                target_w=proposal.budgets[demand.member_id],
                                issued_w=current.budget_w if current else None,
                                reserved_w=exposure[demand.member_id],
                                latest_ref=current.ref if current else None,
                                reason="renewal",
                            )
                        )
                    c.publish(
                        Plan.model_validate(
                            c.envelope(
                                "truss.plan.v1",
                                plan_id=plan_id,
                                snapshot_id=snapshot_hash,
                                policy_hash=policy_hash,
                                registry_revision=c.policy.registry_revision,
                                cap_revision=cap_revision,
                                epoch=epoch,
                                status="admitted",
                                rule=rule,
                                cap_w=cap,
                                measurement_reserve_w=c.policy.measurement_reserve_w,
                                external_bound_w=c.policy.external_bound_w,
                                baseline_sum_w=sum(d.floor_w for d in frozen),
                                deficit_w=0,
                                affected_members=[],
                                allocations=rows,
                                validation=ValidationResult(
                                    valid=True,
                                    codes=[],
                                    exposure_w=sum(exposure.values())
                                    + c.policy.reserve_w,
                                    limit_after_reserves_w=cap - c.policy.reserve_w,
                                ),
                                timing=StageTiming(
                                    **(core.timing | {"admission_ms": admission_ms}),
                                ),
                            )
                        )
                    )
                    # This publish may fail; the reservation remains until its hold ends.
                    c.publish(lease)
            now = time.monotonic_ns()
            debt.advance(now)
            capture()
            grants = {key: value for key, value in grants.items() if now < value[1]}
            if now >= next_status:
                recovering = now < core.ledger.recover_until_ns
                c.publish(
                    c.status_message(
                        "recovering" if recovering else "online",
                        recovery=max(
                            0, (core.ledger.recover_until_ns - now) // 1_000_000
                        )
                        if recovering
                        else None,
                    ),
                    retain=True,
                )
                next_status = now + 500_000_000
            if now >= next_plan:
                frozen = demands()
                proposal = core.propose(frozen, cap)
                exposure = core.ledger.exposure(now)
                plan_version += 1
                recovering = now < core.ledger.recover_until_ns
                rows = []
                for m in c.policy.members:
                    latest = next(
                        (
                            g[0]
                            for g in reversed(list(grants.values()))
                            if g[0].ref.member_id == m.member_id
                        ),
                        None,
                    )
                    rows.append(
                        AllocationRow(
                            member_id=m.member_id,
                            floor_w=m.floor_w,
                            useful_w=next(
                                d.useful_w for d in frozen if d.member_id == m.member_id
                            ),
                            debt_wh=float(debt.values[m.member_id]),
                            weight=float(debt.weight(m.member_id, rule)),
                            target_w=proposal.budgets.get(m.member_id),
                            issued_w=latest.budget_w if latest else None,
                            reserved_w=exposure[m.member_id],
                            latest_ref=latest.ref if latest else None,
                            reason="recovery" if recovering else "renewal",
                        )
                    )
                total = sum(exposure.values()) + c.policy.reserve_w
                snapshot_hash = canonical_hash(
                    {
                        "demands": [
                            d.__dict__ | {"weight": str(d.weight)} for d in frozen
                        ],
                        "cap_w": cap,
                        "cap_revision": cap_revision,
                        "policy_hash": policy_hash,
                        "rule": rule,
                        "debt": debt.dump(),
                    }
                )
                c.publish(
                    Plan.model_validate(
                        c.envelope(
                            "truss.plan.v1",
                            plan_id=f"p{epoch}-{plan_version}",
                            snapshot_id=snapshot_hash,
                            policy_hash=policy_hash,
                            registry_revision=c.policy.registry_revision,
                            cap_revision=cap_revision,
                            epoch=epoch,
                            status="infeasible"
                            if not proposal.feasible
                            else "waiting_release"
                            if recovering or total > cap
                            else "admitted",
                            rule=rule,
                            cap_w=cap,
                            measurement_reserve_w=c.policy.measurement_reserve_w,
                            external_bound_w=c.policy.external_bound_w,
                            baseline_sum_w=sum(m.floor_w for m in c.policy.members),
                            deficit_w=proposal.deficit_w,
                            affected_members=list(registrations)
                            if not proposal.feasible
                            else [],
                            allocations=rows,
                            validation=ValidationResult(
                                valid=proposal.feasible
                                and not recovering
                                and total <= cap,
                                codes=[],
                                exposure_w=total,
                                limit_after_reserves_w=max(0, cap - c.policy.reserve_w),
                            ),
                            timing=StageTiming(
                                **core.timing,
                            ),
                        )
                    ),
                    retain=True,
                )
                with store.db:
                    debt.persist(store)
                next_plan = now + 500_000_000
            time.sleep(0.02)
    finally:
        c.close()
        store.close()
