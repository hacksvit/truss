"""Pure evidence projection. Owner M5. Replay cannot call an allocator or publisher."""

from copy import deepcopy
from .events import EventRecord


def reduce(state: dict, event: EventRecord) -> dict:
    if state and (
        state["run_id"] != event.run_id or event.event_seq <= state["event_cursor"]
    ):
        raise ValueError("wrong run or non-increasing event")
    next_state = deepcopy(state)
    next_state.update(run_id=event.run_id, event_cursor=event.event_seq)
    if event.payload_schema == "truss.ui_snapshot.v1":
        next_state["snapshot"] = deepcopy(event.payload)
    elif event.kind == "mqtt" and event.topic:
        next_state.setdefault("messages", {})[event.topic] = deepcopy(event.payload)
    next_state.setdefault("events", []).append(event.model_dump())
    next_state["events"] = next_state["events"][-50:]
    return next_state
