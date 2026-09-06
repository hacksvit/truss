"""M1: durable service-deficit accounting against equal-surplus authority, never meter use."""

from fractions import Fraction
from .allocator import Demand, allocate

NS_PER_HOUR = 3_600_000_000_000


class ServiceDeficit:
    def __init__(self, members, now_ns, saved=None, scale_wh=10):
        self.members = {m.member_id: m for m in members}
        self.scale = Fraction(scale_wh)
        self.maximum = 2 * self.scale
        self.values = {m: Fraction(0) for m in self.members}
        self.revision = 0
        self.enabled = True
        self.error = None
        self.frozen_gap_ns = 0
        self.at = now_ns
        self.context = None
        if saved is not None:
            try:
                if saved["schema"] != 1 or set(saved["values"]) != set(self.members):
                    raise ValueError("wrong debt registry/schema")
                for member, pair in saved["values"].items():
                    if (
                        len(pair) != 2
                        or any(type(x) is not int for x in pair)
                        or pair[1] <= 0
                    ):
                        raise ValueError("invalid rational debt")
                    value = Fraction(*pair)
                    if not 0 <= value <= self.maximum:
                        raise ValueError("invalid debt bound")
                    self.values[member] = value
                if type(saved["revision"]) is not int or saved["revision"] < 0:
                    raise ValueError("invalid debt revision")
                if type(saved["enabled"]) is not bool:
                    raise ValueError("invalid debt health")
                self.enabled = saved["enabled"]
                self.error = saved.get("error")
                self.revision = saved["revision"]
                self.frozen_gap_ns = saved.get("frozen_gap_ns", 0)
                if type(self.frozen_gap_ns) is not int or self.frozen_gap_ns < 0:
                    raise ValueError("invalid gap counter")
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                self.values = {m: Fraction(0) for m in self.members}
                self.enabled = False
                self.error = "corrupt_debt_state_weighting_disabled"

    def capture(
        self, now_ns, offers, statuses, ledger, cap_w, reserve_w, connected=True
    ):
        """Freeze the next interval's inputs; call advance BEFORE any input/ledger mutation."""
        if now_ns != self.at:
            raise ValueError("advance accounting before replacing its inputs")
        valid = {}
        for member, (offer, received) in offers.items():
            status = statuses.get(member)
            if (
                status
                and status[0].publisher_boot_id == offer.member_boot_id
                and status[0].state in ("online", "at_floor")
            ):
                valid[member] = (
                    offer.useful_w,
                    min(received + 3_000_000_000, status[1] + 1_500_000_000),
                )
        self.context = (
            valid,
            tuple(ledger.records.values()),
            ledger.recover_until_ns,
            cap_w,
            reserve_w,
            connected,
        )

    def advance(self, now_ns):
        if now_ns < self.at:
            raise ValueError("backward accounting clock")
        if now_ns == self.at:
            return
        start, self.at = self.at, now_ns
        if not self.enabled or self.context is None:
            return
        # A stalled coordinator cannot invent a history of valid offers. Freeze
        # rather than extrapolating across suspend/long scheduling gaps.
        if now_ns - start > 1_500_000_000:
            self.frozen_gap_ns += now_ns - start
            return
        valid, records, recovery, cap, reserve, connected = self.context
        if not connected:
            return
        cuts = sorted(
            {start, now_ns}
            | {
                t
                for t in [
                    recovery,
                    *(v[1] for v in valid.values()),
                    *(r.release_ns for r in records),
                ]
                if start < t < now_ns
            }
        )
        changed = False
        for left, right in zip(cuts, cuts[1:]):
            if left < recovery:
                continue
            demands = [
                Demand(
                    m,
                    reg.floor_w,
                    valid[m][0] if m in valid and left < valid[m][1] else reg.floor_w,
                )
                for m, reg in self.members.items()
            ]
            reference = allocate(demands, cap, reserve)
            if not reference.feasible:
                continue
            exposure = {m: reg.floor_w for m, reg in self.members.items()}
            for record in records:
                if left < record.release_ns:
                    exposure[record.member_id] = max(
                        exposure[record.member_id], record.amount_w
                    )
            for member in self.members:
                if member not in valid or left >= valid[member][1]:
                    continue
                delta = (reference.continuous[member] - exposure[member]) * Fraction(
                    right - left, NS_PER_HOUR
                )
                self.values[member] = min(
                    self.maximum, max(Fraction(0), self.values[member] + delta)
                )
                changed = True
        if changed:
            self.revision += 1

    def weight(self, member, rule):
        return (
            Fraction(1) + min(self.values[member] / self.scale, Fraction(1))
            if self.enabled and rule == "debt_weighted_surplus"
            else Fraction(1)
        )

    def dump(self):
        return {
            "schema": 1,
            "values": {m: [v.numerator, v.denominator] for m, v in self.values.items()},
            "revision": self.revision,
            "enabled": self.enabled,
            "error": self.error,
            "frozen_gap_ns": self.frozen_gap_ns,
        }

    def persist(self, store):
        # Never commit a caller's admission transaction prematurely.
        import json

        store.db.execute(
            "INSERT INTO kv VALUES ('debt',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (json.dumps(self.dump()),),
        )
