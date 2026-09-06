"""Virtual load effects, no electrical actuation. Owner M2."""

from dataclasses import dataclass
from .config import DeviceProfile


@dataclass
class Device:
    profile: DeviceProfile
    observed_w: int = 0
    command_version: int = 0
    command_id: str | None = None
    last_desired_w: int | None = None
    transitions: int = 0

    def __post_init__(self):
        self.observed_w = self.profile.baseline_w

    def command(
        self,
        command_id: str,
        version: int,
        desired_w: int,
        deadline_ns: int,
        now_ns: int,
        allowance_w: int,
    ) -> str:
        if now_ns >= deadline_ns:
            return "expired"
        if command_id == self.command_id:
            return (
                "duplicate"
                if (version, desired_w) == (self.command_version, self.last_desired_w)
                else "rejected"
            )
        if version <= self.command_version or type(desired_w) is not int:
            return "rejected"
        if (
            not self.profile.baseline_w
            <= desired_w
            <= min(self.profile.max_w, allowance_w)
        ):
            return "rejected"
        if (
            self.profile.control_policy != "flexible"
            and desired_w != self.profile.max_w
        ):
            return "rejected"
        self.transitions += int(self.observed_w != desired_w)
        self.observed_w = desired_w
        self.command_version, self.command_id = version, command_id
        self.last_desired_w = desired_w
        return "applied"
