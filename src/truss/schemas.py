"""Strict wire models for plan 20. Owner M1; receivers still enforce authority."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    model_validator,
)

ID = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")]
UUID = Annotated[
    str,
    StringConstraints(
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    ),
]
Nat = Annotated[int, Field(ge=0, le=9007199254740991)]
Pos = Annotated[int, Field(ge=1, le=9007199254740991)]
W = Annotated[int, Field(ge=0, le=100000)]
Wh = Annotated[float, Field(ge=0, le=1000000)]
Ms = Nat
Remaining = Annotated[int, Field(ge=0, le=6000)]
DayMs = Annotated[int, Field(ge=0, le=86400000)]
Mono = Annotated[str, StringConstraints(pattern=r"^[0-9]{1,20}$")]
Hash = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Text = Annotated[str, StringConstraints(min_length=1, max_length=500)]
Weight = Annotated[float, Field(ge=1, le=2)]
Quality = Literal["fresh", "stale", "unknown"]
Rule = Literal["equal_surplus", "debt_weighted_surplus"]
Result = Literal["applied", "rejected", "duplicate", "expired"]
DeviceState = Literal["idle", "requested", "running", "deferred", "completing", "fault"]
ControlPolicy = Literal["protected", "flexible", "unclassified"]
Actuation = Literal["modulating", "binary"]
Reason = Literal[
    "initial",
    "renewal",
    "cap_change",
    "capacity_exhausted",
    "baseline_only",
    "stale_offer",
    "policy_conflict",
    "recovery",
    "member_budget_exceeded",
    "min_run",
    "deadline_missed",
    "old_version",
    "wrong_identity",
    "wrong_boot",
    "wrong_request",
    "wrong_registry",
    "expired",
    "duplicate",
    "invalid_amount",
    "enforcer_fault",
    "manual_priority",
    "simulated_fault",
    "validator_veto",
]


class Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        allow_inf_nan=False,
        populate_by_name=True,
    )


class Envelope(Model):
    schema_id: str = Field(alias="schema")
    site_id: ID
    run_id: UUID
    publisher_id: ID
    publisher_boot_id: UUID
    seq: Nat
    ts: str
    correlation_id: UUID | None

    @model_validator(mode="after")
    def timestamp(self):
        if not self.ts.endswith("Z"):
            raise ValueError("ts must be UTC RFC3339 ending in Z")
        datetime.fromisoformat(self.ts.replace("Z", "+00:00"))
        return self


class Status(Envelope):
    schema_id: Literal["truss.status.v1"] = Field(alias="schema")
    component: Literal["coordinator", "member", "plant"]
    component_id: ID
    connection_id: UUID
    source: Literal["heartbeat", "will", "graceful"]
    state: Literal["starting", "recovering", "online", "offline", "at_floor", "fault"]
    member_id: ID | None
    epoch: Pos | None
    recovery_ms_remaining: Annotated[int, Field(ge=0, le=6400)] | None
    registry_revision: Pos
    reason: Reason | None

    @model_validator(mode="after")
    def consistency(self):
        if (self.component == "coordinator") != (
            self.member_id is None and self.epoch is not None
        ):
            raise ValueError("coordinator requires epoch and no member ID")
        if self.component != "coordinator" and (
            self.member_id is None or self.epoch is not None
        ):
            raise ValueError("member/plant requires member ID and null epoch")
        if (self.state == "recovering") != (self.recovery_ms_remaining is not None):
            raise ValueError("recovery countdown/state mismatch")
        if self.source == "will" and (self.state != "offline" or self.seq != 0):
            raise ValueError("Will must be offline with sequence zero")
        return self


class Offer(Envelope):
    schema_id: Literal["truss.offer.v1"] = Field(alias="schema")
    member_id: ID
    member_boot_id: UUID
    registry_revision: Pos
    floor_w: W
    firm_w: W
    useful_w: W
    deadline_energy_wh: Wh
    deadline_in_ms: DayMs | None
    debt_wh: Wh
    debt_revision: Nat
    reported_curtailment_wh: Wh

    @model_validator(mode="after")
    def envelope_valid(self):
        if not self.floor_w <= self.firm_w <= self.useful_w:
            raise ValueError("floor <= firm <= useful required")
        if self.member_boot_id != self.publisher_boot_id:
            raise ValueError("offer boot mismatch")
        if (self.deadline_energy_wh > 0) != (self.deadline_in_ms is not None):
            raise ValueError("deadline energy/remaining mismatch")
        return self


class LeaseRequest(Envelope):
    schema_id: Literal["truss.lease_request.v1"] = Field(alias="schema")
    member_id: ID
    member_boot_id: UUID
    request_id: UUID
    request_seq: Pos
    offer_seq: Nat
    registry_revision: Pos
    ttl_ms: Annotated[int, Field(strict=True, ge=6000, le=6000)]


class LeaseRef(Model):
    member_id: ID
    member_boot_id: UUID
    request_id: UUID
    epoch: Pos
    version: Pos
    lease_id: UUID
    plan_id: ID


class Basis(Model):
    snapshot_id: Hash
    policy_hash: Hash
    registry_revision: Pos
    cap_revision: Pos
    cap_w: W
    measurement_reserve_w: W
    external_bound_w: W
    baseline_sum_w: Nat
    surplus_pool_w: W
    rule: Rule
    debt_scale_wh: Annotated[float, Field(gt=0, le=1000000)]
    weight_cap: Annotated[float, Field(ge=2, le=2)]
    member_floor_w: W
    member_useful_w: W
    member_debt_wh: Wh
    member_weight: Weight
    proposed_budget_w: W
    issued_budget_w: W
    reservation_before_w: W
    reservation_after_w: W
    total_exposure_after_w: Nat
    reason: Reason


class Lease(Envelope):
    schema_id: Literal["truss.lease.v1"] = Field(alias="schema")
    ref: LeaseRef
    registry_revision: Pos
    budget_w: W
    ttl_ms: Annotated[int, Field(strict=True, ge=6000, le=6000)]
    reason: Reason
    basis: Basis

    @model_validator(mode="after")
    def matches_basis(self):
        if (
            self.budget_w != self.basis.issued_budget_w
            or self.registry_revision != self.basis.registry_revision
        ):
            raise ValueError("lease/basis mismatch")
        if not self.basis.member_floor_w <= self.budget_w <= self.basis.member_useful_w:
            raise ValueError("lease outside member envelope")
        return self


class LeaseAck(Envelope):
    schema_id: Literal["truss.lease_ack.v1"] = Field(alias="schema")
    ref: LeaseRef
    result: Result
    reason: Reason | None
    accepted_budget_w: W
    lease_ms_remaining: Remaining
    plant_confirmed: bool
    observed_w: W | None
    observation_quality: Quality
    plant_boot_id: UUID | None


class PlantBind(Envelope):
    schema_id: Literal["truss.plant_bind.v1"] = Field(alias="schema")
    member_id: ID
    member_boot_id: UUID
    plant_boot_id: UUID
    binding_id: UUID
    clock_domain_id: ID
    registry_revision: Pos


class PlantCeiling(PlantBind):
    schema_id: Literal["truss.plant_ceiling.v1"] = Field(alias="schema")
    ref: LeaseRef
    budget_w: W
    expires_mono_ns: Mono


class PlantAck(Envelope):
    schema_id: Literal["truss.plant_ack.v1"] = Field(alias="schema")
    member_id: ID
    plant_boot_id: UUID
    binding_id: UUID
    kind: Literal["bind", "ceiling"]
    ref: LeaseRef | None
    result: Result
    reason: Reason | None
    active_budget_w: W
    remaining_ms: Remaining
    observed_w: W

    @model_validator(mode="after")
    def ref_kind(self):
        if (self.kind == "ceiling") != (self.ref is not None):
            raise ValueError("ceiling ack requires ref; bind ack forbids it")
        return self


class MemberMeter(Envelope):
    schema_id: Literal["truss.member_meter.v1"] = Field(alias="schema")
    member_id: ID
    plant_boot_id: UUID
    clock_domain_id: ID
    sampled_mono_ns: Mono
    observed_w: W
    active_budget_w: W
    floor_w: W
    active_ref: LeaseRef | None
    lease_ms_remaining: Remaining
    at_floor: bool
    enforcement_state: Literal["healthy", "fault"]
    sample_seq: Nat

    @model_validator(mode="after")
    def floor_observation(self):
        if self.plant_boot_id != self.publisher_boot_id:
            raise ValueError("meter boot mismatch")
        if self.at_floor and (
            self.observed_w > self.floor_w
            or self.active_ref is not None
            or self.lease_ms_remaining
        ):
            raise ValueError("inconsistent at-floor report")
        return self


class DeviceDiscovery(Envelope):
    schema_id: Literal["truss.device_discovery.v1"] = Field(alias="schema")
    member_id: ID
    device_id: ID
    plant_boot_id: UUID
    registry_revision: Pos
    kind: Literal["light", "router", "heater", "charger", "washer", "generic"]
    label: Text
    max_w: W
    baseline_w: W
    flexibility: Literal["protected", "firm", "deferrable", "deadline"]
    control_policy: ControlPolicy
    priority: Annotated[int, Field(ge=0, le=100)]
    interruptible: bool
    min_run_ms: DayMs
    min_off_ms: DayMs

    @model_validator(mode="after")
    def baseline(self):
        if self.baseline_w > self.max_w:
            raise ValueError("baseline exceeds maximum")
        if self.control_policy != "flexible" and self.baseline_w != self.max_w:
            raise ValueError("protected/unclassified maximum must be fully reserved")
        return self


class DeviceTelemetry(Envelope):
    schema_id: Literal["truss.telemetry.v1"] = Field(alias="schema")
    member_id: ID
    device_id: ID
    plant_boot_id: UUID
    clock_domain_id: ID
    sampled_mono_ns: Mono
    state: DeviceState
    observed_w: W
    requested_w: W
    remaining_energy_wh: Wh
    deadline_in_ms: DayMs | None
    min_run_remaining_ms: DayMs
    min_off_remaining_ms: DayMs
    last_command_id: UUID | None
    last_command_version: Nat
    active_ref: LeaseRef | None


class LocalDecision(Model):
    decision_id: UUID
    member_id: ID
    device_id: ID
    ref: LeaseRef | None
    offer_seq: Nat
    requested_w: W
    assigned_w: W
    member_budget_w: W
    reserved_local_baseline_w: W
    higher_priority_assigned_w: W
    reason: Reason
    deadline_status: Literal["none", "pending", "missed", "unknown"]
    deadline_in_ms: DayMs | None


class DeviceCommand(Envelope):
    schema_id: Literal["truss.command.v1"] = Field(alias="schema")
    member_id: ID
    member_boot_id: UUID
    device_id: ID
    plant_boot_id: UUID
    binding_id: UUID
    command_id: UUID
    command_version: Pos
    ref: LeaseRef | None
    desired_state: Literal["idle", "running", "deferred"]
    desired_w: W
    clock_domain_id: ID
    expires_mono_ns: Mono
    reason: Reason
    decision: LocalDecision

    @model_validator(mode="after")
    def command_state(self):
        if self.desired_state != "running" and self.desired_w != 0:
            raise ValueError("idle/deferred commands require zero desired watts")
        if (
            self.decision.device_id != self.device_id
            or self.decision.member_id != self.member_id
            or self.decision.ref != self.ref
        ):
            raise ValueError("local decision identity mismatch")
        return self


class DeviceAck(Envelope):
    schema_id: Literal["truss.ack.v1"] = Field(alias="schema")
    member_id: ID
    device_id: ID
    plant_boot_id: UUID
    binding_id: UUID
    command_id: UUID
    command_version: Pos
    ref: LeaseRef | None
    result: Result
    reason: Reason | None
    observed_state: DeviceState
    observed_w: W


class CapacityEvent(Envelope):
    schema_id: Literal["truss.capacity.v1"] = Field(alias="schema")
    event_id: UUID
    operation_id: UUID
    cap_revision: Pos
    expected_previous_revision: Pos
    cap_w: W
    source: Literal["operator", "fixture"]
    reason: Literal["cap_change", "simulated_fault"]


class LocalPolicy(Envelope):
    schema_id: Literal["truss.local_policy.v1"] = Field(alias="schema")
    operation_id: UUID
    member_id: ID
    device_id: ID
    policy_revision: Pos
    protected: bool


class PolicyAck(LocalPolicy):
    schema_id: Literal["truss.policy_ack.v1"] = Field(alias="schema")
    result: Literal["applied", "rejected", "duplicate"]
    reason: Reason | None


class AllocationRow(Model):
    member_id: ID
    floor_w: W
    useful_w: W
    debt_wh: Wh
    weight: Weight
    target_w: W | None
    issued_w: W | None
    reserved_w: W
    latest_ref: LeaseRef | None
    reason: Reason


class ValidationResult(Model):
    valid: bool
    codes: list[Reason]
    exposure_w: Nat
    limit_after_reserves_w: W | None


class StageTiming(Model):
    input_validation_ms: Annotated[float, Field(ge=0)] | None
    allocation_ms: Annotated[float, Field(ge=0)] | None
    plan_validation_ms: Annotated[float, Field(ge=0)] | None
    admission_ms: Annotated[float, Field(ge=0)] | None


class Plan(Envelope):
    schema_id: Literal["truss.plan.v1"] = Field(alias="schema")
    plan_id: ID
    snapshot_id: Hash
    policy_hash: Hash
    registry_revision: Pos
    cap_revision: Pos
    epoch: Pos
    status: Literal["proposed", "admitted", "waiting_release", "infeasible", "vetoed"]
    rule: Rule
    cap_w: W
    measurement_reserve_w: W
    external_bound_w: W
    baseline_sum_w: Nat
    deficit_w: Nat
    affected_members: list[ID]
    allocations: list[AllocationRow]
    validation: ValidationResult
    timing: StageTiming


Message = Annotated[
    Union[
        Status,
        Offer,
        LeaseRequest,
        Lease,
        LeaseAck,
        PlantBind,
        PlantCeiling,
        PlantAck,
        MemberMeter,
        DeviceDiscovery,
        DeviceTelemetry,
        DeviceCommand,
        DeviceAck,
        CapacityEvent,
        LocalPolicy,
        PolicyAck,
        Plan,
    ],
    Field(discriminator="schema_id"),
]
MESSAGE_ADAPTER = TypeAdapter(Message)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(payload: bytes) -> Message:
    """Decode strict JSON; topic/role checks are separately enforced by transport."""
    if len(payload) > 131072:
        raise ValueError("message too large")
    value = json.loads(payload, object_pairs_hook=_unique_pairs)
    message = MESSAGE_ADAPTER.validate_python(value)
    if not isinstance(message, Plan) and len(payload) > 32768:
        raise ValueError("non-plan message too large")
    if (
        getattr(message, "result", None) in ("rejected", "expired")
        and message.reason is None
    ):
        raise ValueError("rejection requires reason")
    return message


def encode(message: Envelope) -> bytes:
    payload = message.model_dump_json(by_alias=True).encode()
    decode(payload)
    return payload
