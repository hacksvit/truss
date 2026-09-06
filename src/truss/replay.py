"""Read-only ordered playback of recorded facts. Owner M3."""

import hashlib
import json
from .events import read_events
from .reducer import reduce


def replay(path, through_seq: int | None = None) -> tuple[dict, bool]:
    records, gap = read_events(path)
    state = {}
    for event in records:
        if through_seq is not None and event.event_seq > through_seq:
            break
        state = reduce(state, event)
    return state, gap


def digest(state: dict) -> str:
    return hashlib.sha256(
        json.dumps(state, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
