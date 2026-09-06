import json
from pathlib import Path
import pytest
from hypothesis import given, strategies as st
from truss.schemas import decode, encode


def test_all_variants_roundtrip(wire):
    assert len(wire) == 17
    for value in wire.values():
        parsed = decode(json.dumps(value).encode())
        assert decode(encode(parsed)) == parsed


def test_invalid_fixtures():
    for case in json.loads(Path("fixtures/wire-invalid.json").read_text()):
        with pytest.raises(ValueError):
            decode(json.dumps(case["message"]).encode())


@given(st.sampled_from(["NaN", "Infinity", "-Infinity", "true", '"500"']))
def test_non_numeric_watts_rejected(value):
    message = next(
        m
        for m in json.loads(Path("fixtures/wire-valid.json").read_text())
        if m["schema"] == "truss.lease.v1"
    )
    raw = json.dumps(message).replace('"budget_w": 500', f'"budget_w": {value}')
    with pytest.raises(ValueError):
        decode(raw.encode())


def test_duplicate_keys_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        decode(b'{"schema":"a","schema":"b"}')
