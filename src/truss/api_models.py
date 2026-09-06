"""Operator-plane views. Owner M5. Constructors fill explicit output defaults only."""

from typing import Literal, Annotated
from pydantic import Field, model_validator
from .schemas import (
    Model,
    ID,
    UUID,
    Nat,
    W,
    Wh,
    Ms,
    Quality,
    Rule,
    Basis,
    LocalDecision,
    LeaseRef,
    StageTiming,
    ControlPolicy,
)

Source = Literal["live", "mock", "replay"]


class Capabilities(Model):
    protect: bool = False
    debt_weighting: bool = False
    chaos: bool = False
    replay: bool = False
    lab: bool = False
    max_live_members: int = 5
    max_lab_members: int = 5000
    cpsat: Literal[False] = False
    hardware: Literal[False] = False


class Operation(Model):
    operation_id: UUID
    run_id: UUID
    kind: Literal["cap", "protect", "chaos", "fault", "rule", "replay", "lab"]
    status: Literal["queued", "running", "applied", "rejected", "failed"]
    control_revision: Nat
    created_at: str
    finished_at: str | None = None
    error: str | None = None
    message: str | None = None
    result_id: UUID | None = None


class LeaseView(Model):
    ref: LeaseRef | None = None
    remaining_ms: Ms | None = None
    sample_age_ms: Ms | None = None
    quality: Quality = "unknown"
    plant_confirmed: bool = False


class DeviceView(Model):
    id: ID
    kind: str
    label: str
    w: W | None
    requested_w: W
    state: str
    quality: Quality
    sample_age_ms: Ms | None
    ack: Literal["pending", "applied", "verified", "rejected", "stale", "none"]
    protected: bool
    control_policy: ControlPolicy
    curtailment_eligible: bool
    deadline_in_ms: Ms | None = None
    deadline_status: Literal["none", "pending", "missed", "unknown"] = "none"
    command_id: UUID | None = None
    decision: LocalDecision | None = None


class MemberView(Model):
    id: ID
    boot_id: UUID | None = None
    plant_boot_id: UUID | None = None
    floor_w: W
    max_w: W
    firm_w: W
    useful_w: W
    target_w: W | None
    issued_w: W | None
    reserved_w: W
    observed_w: W | None
    observed_quality: Quality
    sample_age_ms: Ms | None
    debt_wh: Wh = 0.0
    reported_curtailment_wh: Wh | None = None
    weight: float = 1.0
    lease: LeaseView
    status: Literal["joining", "ok", "stale", "offline", "at_floor", "fault"]
    devices: list[DeviceView]
    device_visibility: Literal["demo_observer", "hidden"] = "demo_observer"
    basis: Basis | None = None


class SiteView(Model):
    id: ID
    cap_w: W
    cap_revision: Nat
    measurement_reserve_w: W
    external_bound_w: W
    baseline_sum_w: Nat
    reserved_member_w: Nat
    unverified_member_reservation_w: Nat
    available_for_new_grants_w: W
    exposure_w: Nat
    observed_w: Nat | None
    observed_quality: Quality
    oldest_sample_age_ms: Ms | None
    state: Literal[
        "starting", "recovering", "leased", "cap_transition", "infeasible", "unverified"
    ]
    coordinator_status: Literal["online", "recovering", "offline", "unknown"]
    recovering_ms_remaining: Ms | None
    compliance: Literal["within_cap", "over_cap", "unknown"]
    deficit_w: Nat
    affected_members: list[ID]
    rule: Rule
    plan_id: ID | None
    timing: StageTiming


class EventView(Model):
    seq: Nat
    at: str
    kind: str
    code: str
    text: str
    member_id: ID | None = None
    device_id: ID | None = None
    plan_id: ID | None = None
    correlation_id: UUID | None = None


class MetricsView(Model):
    observation_window_ms: Ms = 0
    eligible_samples: Nat = 0
    within_cap_samples: Nat = 0
    unknown_samples: Nat = 0
    cap_compliance_pct: float | None = None
    time_to_safe_ms: Ms | None = None
    time_to_safe_status: Literal[
        "pending", "observed", "timeout", "infeasible", "unknown"
    ] = "unknown"
    lease_model_violations: Nat | None = None
    issued_commands: Nat = 0
    applied_commands: Nat = 0
    ack_success_pct: float | None = None
    jain_service_ratio: float | None = None
    fairness_sample_count: Nat = 0
    max_enforcement_lateness_ms: float | None = None
    replay_gaps: Nat = 0


class Snapshot(Model):
    schema_id: Literal["truss.ui_snapshot.v1"] = Field(
        default="truss.ui_snapshot.v1", alias="schema"
    )
    run_id: UUID
    stream_id: UUID
    revision: Nat
    control_revision: Nat
    source: Source
    replay_id: UUID | None = None
    generated_at: str
    event_cursor: Nat
    site: SiteView
    members: list[MemberView]
    events: list[EventView]
    operations: list[Operation]
    metrics: MetricsView
    capabilities: Capabilities


class ControlRequest(Model):
    run_id: UUID
    expected_control_revision: Nat
    source: Source


class CapRequest(ControlRequest):
    watts: W


class RuleRequest(ControlRequest):
    rule: Rule


class FaultRequest(ControlRequest):
    target: str
    action: Literal["partition", "drop_acks", "delay_telemetry", "delay_grants"]
    duration_ms: Annotated[int, Field(ge=1, le=30000)] = 8000
    delay_ms: Annotated[int, Field(ge=0, le=10000)] = 0
    rate: Annotated[float, Field(ge=0, le=1)] = 1.0

    @model_validator(mode="after")
    def meaningful(self):
        if self.action.startswith("delay_") != (self.delay_ms > 0):
            raise ValueError("A positive delay is required only for delay actions")
        return self


class ChaosRequest(ControlRequest):
    action: Literal[
        "kill_coordinator",
        "restart_coordinator",
        "stale_member",
        "clear_faults",
        "kill_member",
        "restart_member",
        "kill_broker",
        "restart_broker",
    ]
    member_id: ID | None


class LabRequest(Model):
    members: Annotated[int, Field(ge=1, le=5000)]
    seed: Nat
    samples: Annotated[int, Field(ge=1, le=200)] = 200
    distribution: Literal["uniform", "saturated", "skewed"] = "uniform"
    rule: Rule = "equal_surplus"
    cap_ratio: Annotated[float, Field(ge=0, le=1)] = 0.5


class BenchmarkResult(Model):
    members: int
    seed: Nat
    samples_ms: list[float]
    complete: bool
    median_ms: float | None
    p95_ms: float | None
    python: str
    os: str
    timer: str
    scope: str
    warmups: int
    distribution: str = "uniform"
    rule: Rule = "equal_surplus"
    cap_ratio: float = 0.5
    validation_samples_ms: list[float] = Field(default_factory=list)
    total_samples_ms: list[float] = Field(default_factory=list)
    requested_samples: int = 200


class LabJob(Model):
    job_id: UUID
    status: Literal["running", "complete", "failed"]
    request: LabRequest
    created_at: str
    finished_at: str | None = None
    result: BenchmarkResult | None = None
    error: str | None = None


class ReplayRequest(Model):
    recorded_run_id: UUID
    from_seq: Nat = 0
    speed: Literal[1] = 1


class ReplaySeek(Model):
    from_seq: Nat


class ReplayPlayback(Model):
    action: Literal["play", "pause"]


class FairnessMember(Model):
    member_id: ID
    debt_wh: Wh
    weight: Annotated[float, Field(ge=1, le=2)]


class FairnessView(Model):
    run_id: UUID
    desired_rule: Rule
    effective_rule: Rule
    available: bool
    revision: Nat
    error: str | None
    scale_wh: float
    maximum_wh: float
    frozen_gap_ms: Nat
    meaning: str
    members: list[FairnessMember]


class RecordingSummary(Model):
    recorded_run_id: UUID
    bytes: Nat
    replayable: bool


class RecordingCatalog(Model):
    items: list[RecordingSummary]
    max_bytes: Nat
    max_frames: Nat


class ReplayView(Model):
    replay_id: UUID
    recorded_run_id: UUID
    sha256: str
    gap: bool
    frame_seq: Nat
    first_seq: Nat
    last_seq: Nat
    frame_count: Nat
    playing: bool
    position_ms: Nat
    duration_ms: Nat
    snapshot: Snapshot


class ProcessView(Model):
    name: str
    pid: int
    running: bool
    exit_code: int | None


class RuntimeView(Model):
    run_id: UUID
    processes: list[ProcessView]
    evidence_error: str | None
    recording_full: bool
