"""Possible authority, not last measured draw. Owner M1. Caller serialises access."""

from dataclasses import dataclass
from .config import Registration


@dataclass(frozen=True)
class Reservation:
    member_id: str
    request_id: str
    boot_id: str
    request_seq: int
    amount_w: int
    release_ns: int


class ReservationLedger:
    def __init__(self, members: list[Registration], hold_ms: int = 6400):
        self.members = {m.member_id: m for m in members}
        if len(self.members) != len(members) or hold_ms < 6400:
            raise ValueError("invalid registry/hold")
        self.hold_ns = hold_ms * 1_000_000
        self.records: dict[tuple[str, str, str], Reservation] = {}
        self.highwater: dict[tuple[str, str], int] = {}
        self.recover_until_ns = 0

    def begin_recovery(self, now_ns: int):
        self.records.clear()
        self.highwater.clear()
        self.recover_until_ns = now_ns + self.hold_ns

    def expire(self, now_ns: int):
        self.records = {
            key: r for key, r in self.records.items() if r.release_ns > now_ns
        }

    def exposure(self, now_ns: int) -> dict[str, int]:
        self.expire(now_ns)
        if now_ns < self.recover_until_ns:
            return {m.member_id: m.max_w for m in self.members.values()}
        result = {m.member_id: m.floor_w for m in self.members.values()}
        for r in self.records.values():
            result[r.member_id] = max(result[r.member_id], r.amount_w)
        return result

    def admit(
        self,
        *,
        member_id: str,
        boot_id: str,
        request_id: str,
        request_seq: int,
        amount_w: int,
        cap_w: int,
        reserve_w: int,
        now_ns: int,
    ) -> Reservation:
        if now_ns < self.recover_until_ns:
            raise ValueError("recovering")
        if member_id not in self.members:
            raise ValueError("unknown member")
        if (
            type(amount_w) is not int
            or type(cap_w) is not int
            or type(reserve_w) is not int
            or min(cap_w, reserve_w) < 0
        ):
            raise ValueError("invalid amount")
        registration = self.members[member_id]
        if not registration.floor_w <= amount_w <= registration.max_w:
            raise ValueError("outside registered envelope")
        self.expire(now_ns)
        key = (member_id, boot_id, request_id)
        if key in self.records:
            old = self.records[key]
            if (amount_w, request_seq) != (old.amount_w, old.request_seq):
                raise ValueError("immutable request conflict")
            return old  # No timer reset. Caller must replay the same immutable grant.
        stream = (member_id, boot_id)
        if request_seq <= self.highwater.get(stream, 0):
            raise ValueError("old request")
        current = self.exposure(now_ns)
        current[member_id] = max(current[member_id], amount_w)
        if sum(current.values()) + reserve_w > cap_w:
            raise ValueError("capacity exhausted")
        record = Reservation(
            member_id, request_id, boot_id, request_seq, amount_w, now_ns + self.hold_ns
        )
        self.records[key] = record
        self.highwater[stream] = request_seq
        return record
