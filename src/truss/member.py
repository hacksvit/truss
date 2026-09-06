"""Request-anchored receiver core. Owner M3. MQTT lifecycle is in member_process.py."""

from dataclasses import dataclass
from .config import Registration
from .schemas import Lease


@dataclass(frozen=True)
class AcceptedLease:
    lease: Lease
    deadline_ns: int


class MemberReceiver:
    def __init__(
        self,
        registration: Registration,
        boot_id: str,
        site_id: str,
        run_id: str,
        registry_revision: int,
    ):
        self.registration = registration
        self.boot_id, self.site_id, self.run_id = boot_id, site_id, run_id
        self.registry_revision = registry_revision
        self.pending: tuple[str, int] | None = None
        self.accepted: AcceptedLease | None = None
        self.highwater = (0, 0)

    def open_request(self, request_id: str, now_ns: int):
        self.pending = (request_id, now_ns + 6_000_000_000)

    def accept(self, lease: Lease, now_ns: int) -> str:
        if (
            lease.site_id != self.site_id
            or lease.run_id != self.run_id
            or lease.publisher_id != "coordinator"
        ):
            return "wrong_identity"
        if (
            lease.ref.member_id != self.registration.member_id
            or lease.ref.member_boot_id != self.boot_id
        ):
            return "wrong_boot"
        if lease.registry_revision != self.registry_revision:
            return "wrong_registry"
        if not self.registration.floor_w <= lease.budget_w <= self.registration.max_w:
            return "invalid_amount"
        if self.accepted and lease.ref.lease_id == self.accepted.lease.ref.lease_id:
            if lease != self.accepted.lease:
                return "invalid_amount"
            return "duplicate" if now_ns < self.accepted.deadline_ns else "expired"
        if (lease.ref.epoch, lease.ref.version) <= self.highwater:
            return "old_version"
        if self.pending is None or lease.ref.request_id != self.pending[0]:
            return "wrong_request"
        if now_ns >= self.pending[1]:
            return "expired"
        self.accepted = AcceptedLease(lease, self.pending[1])
        self.highwater = (lease.ref.epoch, lease.ref.version)
        self.pending = None
        return "applied"

    def budget(self, now_ns: int) -> int:
        if self.accepted and now_ns < self.accepted.deadline_ns:
            return self.accepted.lease.budget_w
        return self.registration.floor_w
