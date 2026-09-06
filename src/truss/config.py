"""Immutable run and private device configuration. Owner M1."""

from pathlib import Path
from pydantic import Field, model_validator
from .schemas import Model, ID, UUID, W, Pos, ControlPolicy


class Registration(Model):
    member_id: ID
    floor_w: W
    max_w: W
    host_id: ID
    baseline_revision: Pos

    @model_validator(mode="after")
    def bounds(self):
        if self.floor_w > self.max_w:
            raise ValueError("floor exceeds maximum")
        return self


class RunPolicy(Model):
    site_id: ID
    run_id: UUID
    registry_revision: Pos
    cap_w: W
    measurement_reserve_w: W
    external_bound_w: W
    members: list[Registration]
    ttl_ms: int = Field(default=6000, ge=6000, le=6000)
    renew_ms: int = Field(default=2000, ge=2000, le=2000)
    hold_ms: int = Field(default=6400, ge=6400, le=6400)

    @model_validator(mode="after")
    def initial_feasibility(self):
        if len({m.member_id for m in self.members}) != len(self.members):
            raise ValueError("duplicate registered member")
        if self.reserve_w + sum(m.floor_w for m in self.members) > self.cap_w:
            raise ValueError("initial baselines do not fit cap")
        return self

    @property
    def reserve_w(self):
        return self.measurement_reserve_w + self.external_bound_w


class DeviceProfile(Model):
    device_id: ID
    label: str
    kind: str
    max_w: W
    baseline_w: W
    control_policy: ControlPolicy
    priority: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def protected_maximum(self):
        if self.baseline_w > self.max_w:
            raise ValueError("baseline exceeds maximum")
        if self.control_policy != "flexible" and self.baseline_w != self.max_w:
            raise ValueError("protected/unclassified device must be fully reserved")
        return self


class MemberProfile(Model):
    member_id: ID
    devices: list[DeviceProfile]

    @model_validator(mode="after")
    def unique(self):
        if len({d.device_id for d in self.devices}) != len(self.devices):
            raise ValueError("duplicate device ID")
        return self


def load_run(path: str | Path) -> RunPolicy:
    return RunPolicy.model_validate_json(Path(path).read_bytes())


def load_member(path: str | Path, registration: Registration) -> MemberProfile:
    profile = MemberProfile.model_validate_json(Path(path).read_bytes())
    if profile.member_id != registration.member_id:
        raise ValueError("wrong household profile")
    if sum(d.baseline_w for d in profile.devices) > registration.floor_w:
        raise ValueError("device baselines exceed registered floor")
    if sum(d.max_w for d in profile.devices) > registration.max_w:
        raise ValueError("device envelope exceeds registration")
    return profile
