"""Append-only ordered JSONL evidence. Owner M3. Not an authority database."""

import os
from pathlib import Path
from .schemas import Model, UUID, Pos, Mono


class EventRecord(Model):
    run_id: UUID
    event_seq: Pos
    received_at: str
    received_mono_ns: Mono
    kind: str
    topic: str | None
    payload_schema: str
    payload: dict
    correlation_id: UUID | None


def read_events(path: str | Path) -> tuple[list[EventRecord], bool]:
    raw = Path(path).read_bytes() if Path(path).exists() else b""
    lines = raw.splitlines(keepends=True)
    result, gap = [], False
    for line in lines:
        if not line.endswith(b"\n"):
            gap = True
            break
        try:
            record = EventRecord.model_validate_json(line)
        except ValueError:
            gap = True
            break
        if not result and record.event_seq != 1:
            gap = True
        if result and (
            record.event_seq != result[-1].event_seq + 1
            or record.run_id != result[-1].run_id
        ):
            gap = True
        result.append(record)
    return result, gap


class EventLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records, gap = read_events(path)
        if gap:
            raise ValueError(
                "existing log has a gap; preserve it and start a new segment"
            )
        self.seq = records[-1].event_seq if records else 0
        self.run_id = records[-1].run_id if records else None

    def append(self, **fields) -> EventRecord:
        if self.run_id is not None and fields.get("run_id") != self.run_id:
            raise ValueError("run identity changed inside event log")
        record = EventRecord(event_seq=self.seq + 1, **fields)
        with self.path.open("ab") as output:
            output.write(record.model_dump_json().encode() + b"\n")
            output.flush()
            os.fsync(output.fileno())
        self.seq += 1
        self.run_id = record.run_id
        return record
