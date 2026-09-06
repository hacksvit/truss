from pathlib import Path
import pytest
from truss.events import read_events, EventLog
from truss.replay import replay, digest


def test_replay_is_deterministic_and_read_only():
    path = Path("fixtures/demo-events.jsonl")
    before = path.read_bytes()
    a, gap = replay(path)
    b, _ = replay(path)
    assert not gap and digest(a) == digest(b) and path.read_bytes() == before


def test_truncated_tail_is_reported(tmp_path):
    p = tmp_path / "events.jsonl"
    p.write_bytes(Path("fixtures/demo-events.jsonl").read_bytes() + b'{"partial":')
    records, gap = read_events(p)
    assert records and gap
    with pytest.raises(ValueError, match="gap"):
        EventLog(p)


def test_missing_prefix_and_corrupt_record_are_gaps(tmp_path):
    lines = Path("fixtures/demo-events.jsonl").read_bytes().splitlines(keepends=True)
    path = tmp_path / "events.jsonl"
    path.write_bytes(b"".join(lines[1:]))
    assert read_events(path)[1]
    path.write_bytes(lines[0] + b"not-json\n")
    records, gap = read_events(path)
    assert len(records) == 1 and gap
