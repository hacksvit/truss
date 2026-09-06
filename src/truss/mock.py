"""Honest interactive UI mock. Owner M5. Never imports MQTT or live processes."""

import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .allocator import Demand, allocate
from .config import load_run, load_member
from .local_policy import assign, unusable_w
from .api_models import (
    Snapshot,
    SiteView,
    MemberView,
    DeviceView,
    LeaseView,
    MetricsView,
    Capabilities,
    EventView,
)
from .schemas import StageTiming


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MockState:
    source = "mock"

    def __init__(self, config_dir: str | Path = "config"):
        config_dir = Path(config_dir)
        self.policy = load_run(config_dir / "run.json")
        self.profiles = {
            m.member_id: load_member(config_dir / f"{m.member_id}.json", m)
            for m in self.policy.members
        }
        self.stream_id, self.run_id = str(uuid4()), self.policy.run_id
        self.revision = self.control_revision = 0
        self.cap_w = self.policy.cap_w
        self.coordinator_status = "online"
        self.last_renewal = time.monotonic()
        self.recover_until = 0.0
        self.old_budgets = {m.member_id: m.floor_w for m in self.policy.members}
        self.active_budgets = dict(self.old_budgets)
        self.transition_until = 0.0
        self.stale_member = None
        self.events: list[EventView] = []
        self.operations = []
        self.add_event(
            "initial",
            "Interactive mock ready. These are synthetic observations, not a live distributed run.",
        )

    def add_event(self, code, text):
        self.events.append(
            EventView(
                seq=len(self.events) + 1,
                at=utc_now(),
                kind="operation",
                code=code,
                text=text,
            )
        )

    def set_cap(self, watts: int):
        self.old_budgets = dict(self.active_budgets)
        self.cap_w = watts
        self.transition_until = time.monotonic() + 6.4
        self.control_revision += 1
        self.add_event(
            "cap_change",
            f"Mock cap requested: {watts} W. Previous authority retained during transition.",
        )

    def chaos(self, action: str, member_id: str | None):
        if action not in (
            "kill_coordinator",
            "restart_coordinator",
            "stale_member",
            "clear_faults",
        ):
            raise ValueError(
                "This mock does not implement the requested process action"
            )
        if action == "kill_coordinator":
            self.coordinator_status = "offline"
            self.add_event(
                "simulated_fault",
                "Mock coordinator stopped; the illustrated leases will expire.",
            )
        elif action == "restart_coordinator":
            self.coordinator_status = "recovering"
            self.recover_until = time.monotonic() + 6.4
            self.add_event(
                "recovery", "Mock coordinator recovering: 6.4-second authority wait."
            )
        elif action == "stale_member":
            if member_id not in self.profiles:
                raise ValueError("unknown member")
            self.stale_member = member_id
            self.add_event(
                "stale_offer",
                f"Mock observations for {member_id} are stale. Unknown is not zero.",
            )
        elif action == "clear_faults":
            self.stale_member = None
        self.control_revision += 1

    def snapshot(self) -> Snapshot:
        now = time.monotonic()
        self.revision += 1
        demands = [Demand(m.member_id, m.floor_w, m.max_w) for m in self.policy.members]
        proposal = allocate(demands, self.cap_w, self.policy.reserve_w)
        if self.coordinator_status == "recovering" and now >= self.recover_until:
            self.coordinator_status = "online"
            self.add_event("recovery", "Mock recovery wait completed.")
        transition = now < self.transition_until
        if (
            self.coordinator_status == "online"
            and not transition
            and proposal.feasible
            and now - self.last_renewal >= 2
        ):
            self.last_renewal = now
            self.active_budgets = dict(proposal.budgets)
        remaining = max(0, int(6000 - (now - self.last_renewal) * 1000))
        if remaining == 0:
            self.active_budgets = {m.member_id: m.floor_w for m in self.policy.members}
        members = []
        for registration in self.policy.members:
            member = registration.member_id
            budget = self.active_budgets[member]
            assigned = assign(self.profiles[member], budget)
            stale = member == self.stale_member
            quality = "stale" if stale else "fresh"
            reserved = max(budget, self.old_budgets[member]) if transition else budget
            devices = [
                DeviceView(
                    id=d.device_id,
                    kind=d.kind,
                    label=d.label,
                    w=assigned[d.device_id],
                    requested_w=d.max_w,
                    state="running" if assigned[d.device_id] else "deferred",
                    quality=quality,
                    sample_age_ms=3000 if stale else 0,
                    ack="stale" if stale else "verified",
                    protected=d.control_policy != "flexible",
                    control_policy=d.control_policy,
                    curtailment_eligible=d.control_policy == "flexible",
                )
                for d in self.profiles[member].devices
            ]
            members.append(
                MemberView(
                    id=member,
                    floor_w=registration.floor_w,
                    max_w=registration.max_w,
                    firm_w=registration.floor_w,
                    useful_w=registration.max_w,
                    target_w=proposal.budgets.get(member),
                    issued_w=budget,
                    reserved_w=reserved,
                    unusable_w=unusable_w(self.profiles[member], budget),
                    observed_w=sum(assigned.values()),
                    observed_quality=quality,
                    sample_age_ms=3000 if stale else 0,
                    lease=LeaseView(
                        remaining_ms=remaining,
                        sample_age_ms=0,
                        quality=quality,
                        plant_confirmed=not stale,
                    ),
                    status="stale" if stale else "at_floor" if remaining == 0 else "ok",
                    devices=devices,
                )
            )
        reserved_total = sum(m.reserved_w for m in members)
        exposure = reserved_total + self.policy.reserve_w
        observed = None if self.stale_member else sum(m.observed_w for m in members)
        state = (
            "infeasible"
            if not proposal.feasible
            else "recovering"
            if self.coordinator_status == "recovering"
            else "cap_transition"
            if transition
            else "unverified"
            if observed is None
            else "leased"
        )
        site = SiteView(
            id=self.policy.site_id,
            cap_w=self.cap_w,
            cap_revision=self.control_revision + 1,
            measurement_reserve_w=self.policy.measurement_reserve_w,
            external_bound_w=self.policy.external_bound_w,
            baseline_sum_w=sum(m.floor_w for m in members),
            reserved_member_w=reserved_total,
            unverified_member_reservation_w=sum(
                m.reserved_w for m in members if m.status == "stale"
            ),
            available_for_new_grants_w=max(0, self.cap_w - exposure),
            unusable_w=sum(m.unusable_w for m in members),
            exposure_w=exposure,
            observed_w=observed,
            observed_quality="unknown" if observed is None else "fresh",
            oldest_sample_age_ms=3000 if observed is None else 0,
            state=state,
            coordinator_status=self.coordinator_status,
            recovering_ms_remaining=max(0, int((self.recover_until - now) * 1000))
            if self.coordinator_status == "recovering"
            else None,
            compliance="unknown"
            if observed is None
            else "within_cap"
            if observed <= self.cap_w
            else "over_cap",
            deficit_w=proposal.deficit_w,
            affected_members=[m.id for m in members] if not proposal.feasible else [],
            rule="equal_surplus",
            plan_id=None,
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
            control_revision=self.control_revision,
            source="mock",
            generated_at=utc_now(),
            event_cursor=len(self.events),
            site=site,
            members=members,
            events=self.events[-50:],
            operations=self.operations[-20:],
            metrics=MetricsView(),
            capabilities=Capabilities(chaos=True, lab=True),
        )
