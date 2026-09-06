"""Independent virtual-plant gate. Owner M2. Its process must outlive the member."""

from .config import MemberProfile, Registration
from .schemas import PlantBind, PlantCeiling
from .devices import Device


class Plant:
    def __init__(
        self,
        registration: Registration,
        profile: MemberProfile,
        boot_id: str,
        domain: str,
        registry_revision: int | None = None,
    ):
        if (
            registration.member_id != profile.member_id
            or sum(d.baseline_w for d in profile.devices) > registration.floor_w
        ):
            raise ValueError("profile does not fit baseline")
        self.registration, self.profile = registration, profile
        self.boot_id, self.domain = boot_id, domain
        self.registry_revision = (
            registry_revision
            if registry_revision is not None
            else registration.baseline_revision
        )
        self.devices = {d.device_id: Device(d) for d in profile.devices}
        self.binding: PlantBind | None = None
        self.ceiling: PlantCeiling | None = None
        self.highwater = (0, 0)
        self.command_deadlines: dict[str, int] = {}

    def budget(self, now_ns: int) -> int:
        if self.ceiling and now_ns < int(self.ceiling.expires_mono_ns):
            return self.ceiling.budget_w
        return self.registration.floor_w

    def bind(self, binding: PlantBind, now_ns: int) -> str:
        self.tick(now_ns)
        if (
            binding.member_id,
            binding.plant_boot_id,
            binding.clock_domain_id,
            binding.registry_revision,
        ) != (
            self.registration.member_id,
            self.boot_id,
            self.domain,
            self.registry_revision,
        ):
            return "rejected"
        if self.binding and binding.binding_id == self.binding.binding_id:
            return "duplicate" if binding == self.binding else "rejected"
        if self.ceiling and now_ns < int(self.ceiling.expires_mono_ns):
            return "rejected"
        self.binding, self.ceiling, self.highwater = binding, None, (0, 0)
        self.command_deadlines.clear()
        for device in self.devices.values():
            device.command_version = 0
            device.command_id = None
            device.last_desired_w = None
        return "applied"

    def apply_ceiling(self, ceiling: PlantCeiling, now_ns: int) -> str:
        if not self.binding:
            return "rejected"
        fields = (
            "site_id",
            "run_id",
            "member_id",
            "member_boot_id",
            "plant_boot_id",
            "binding_id",
            "clock_domain_id",
            "registry_revision",
        )
        if any(getattr(ceiling, f) != getattr(self.binding, f) for f in fields):
            return "rejected"
        if (
            ceiling.ref.member_id != self.registration.member_id
            or ceiling.ref.member_boot_id != self.binding.member_boot_id
        ):
            return "rejected"
        if not self.registration.floor_w <= ceiling.budget_w <= self.registration.max_w:
            return "rejected"
        if now_ns >= int(ceiling.expires_mono_ns):
            return "expired"
        if int(ceiling.expires_mono_ns) > now_ns + 6_000_000_000:
            return "rejected"
        if self.ceiling and ceiling.ref.lease_id == self.ceiling.ref.lease_id:
            return "duplicate" if ceiling == self.ceiling else "rejected"
        if (ceiling.ref.epoch, ceiling.ref.version) <= self.highwater:
            return "rejected"
        self.ceiling = ceiling
        self.highwater = (ceiling.ref.epoch, ceiling.ref.version)
        self.tick(now_ns)
        return "applied"

    def tick(self, now_ns: int):
        """Enforce baseline on expiry; trim flexible loads on ceiling reductions."""
        budget = self.budget(now_ns)
        for key, deadline in list(self.command_deadlines.items()):
            if now_ns >= deadline:
                self.devices[key].observed_w = self.devices[key].profile.baseline_w
                del self.command_deadlines[key]
        if not self.ceiling or now_ns >= int(self.ceiling.expires_mono_ns):
            for device in self.devices.values():
                device.observed_w = device.profile.baseline_w
            return
        excess = max(0, sum(d.observed_w for d in self.devices.values()) - budget)
        for device in sorted(
            self.devices.values(),
            key=lambda d: (d.profile.priority, d.profile.device_id),
        ):
            if device.profile.control_policy == "flexible":
                shed = min(excess, device.observed_w - device.profile.baseline_w)
                device.observed_w -= shed
                excess -= shed

    def command(
        self,
        device_id: str,
        command_id: str,
        version: int,
        watts: int,
        deadline_ns: int,
        now_ns: int,
    ):
        self.tick(now_ns)
        device = self.devices[device_id]
        other = sum(d.observed_w for key, d in self.devices.items() if key != device_id)
        if watts > device.profile.baseline_w:
            if self.ceiling is None or deadline_ns > int(self.ceiling.expires_mono_ns):
                return "rejected"
        result = device.command(
            command_id, version, watts, deadline_ns, now_ns, self.budget(now_ns) - other
        )
        if result == "applied":
            self.command_deadlines[device_id] = deadline_ns
        return result
