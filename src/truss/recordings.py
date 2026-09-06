"""M5: bounded, immutable replay sessions over recorded operator snapshots; no controls."""

from bisect import bisect_right
import hashlib
from pathlib import Path
import threading
import time
from uuid import UUID, uuid4
from .api_models import Snapshot, Capabilities

MAX_RECORDING_BYTES = 32 * 1024 * 1024
MAX_FRAMES = 10000


class Recordings:
    def __init__(self, root=None):
        self.root = Path(root).resolve() if root else None
        self.sessions = {}
        self.lock = threading.Lock()

    def _path(self, run_id):
        if str(UUID(run_id)) != run_id:
            raise ValueError("recording_not_found")
        if not self.root:
            raise ValueError("recording_not_found")
        path = self.root / run_id / "snapshots.jsonl"
        if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
            raise ValueError("recording_not_found")
        return path

    def catalog(self):
        items = []
        if self.root and self.root.exists():
            for folder in sorted(self.root.iterdir()):
                try:
                    path = self._path(folder.name)
                except (ValueError, OSError):
                    continue
                items.append(
                    {
                        "recorded_run_id": folder.name,
                        "bytes": path.stat().st_size,
                        "replayable": path.stat().st_size <= MAX_RECORDING_BYTES,
                    }
                )
        return {
            "items": items,
            "max_bytes": MAX_RECORDING_BYTES,
            "max_frames": MAX_FRAMES,
        }

    def create(self, run_id, from_seq=0):
        path = self._path(run_id)
        # Freeze a bounded prefix at creation. A writer may append afterwards;
        # any partial final line is reported as a gap, never filled with guesses.
        with path.open("rb") as stream:
            raw = stream.read(MAX_RECORDING_BYTES + 1)
        if len(raw) > MAX_RECORDING_BYTES:
            raise ValueError("recording_too_large")
        from .events import EventRecord

        frames, times, gap, previous_seq, previous_time = [], [], False, 0, -1
        for line in raw.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                gap = True
                break
            try:
                event = EventRecord.model_validate_json(line)
                if (
                    event.kind != "snapshot"
                    or event.payload_schema != "truss.ui_snapshot.v1"
                    or event.topic is not None
                ):
                    raise ValueError("wrong recording envelope")
                if (
                    event.run_id != run_id
                    or event.event_seq <= previous_seq
                    or int(event.received_mono_ns) < previous_time
                ):
                    gap = True
                    break
                if event.event_seq != previous_seq + 1:
                    gap = True
                snapshot = Snapshot.model_validate(event.payload)
                if snapshot.run_id != run_id or snapshot.source not in ("live", "mock"):
                    raise ValueError("wrong snapshot source/run")
                gap |= snapshot.metrics.replay_gaps > 0
                frames.append((event.event_seq, snapshot))
                times.append(int(event.received_mono_ns))
                previous_seq = event.event_seq
                previous_time = int(event.received_mono_ns)
                if len(frames) > MAX_FRAMES:
                    raise ValueError("recording_too_many_frames")
            except ValueError as exc:
                if str(exc) == "recording_too_many_frames":
                    raise
                gap = True
                break
        if not frames:
            raise ValueError("recording_empty")
        with self.lock:
            if len(self.sessions) >= 4:
                raise ValueError("replay_session_limit")
            replay_id = str(uuid4())
            session = {
                "replay_id": replay_id,
                "recorded_run_id": run_id,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "gap": gap,
                "frames": frames,
                "times": [t - times[0] for t in times],
                "playing": False,
                "play_started": 0,
                "play_offset": 0,
                "cursor": 0,
                "view_revision": 0,
                "stream_id": str(uuid4()),
            }
            self._seek(session, from_seq)
            self.sessions[replay_id] = session
            return self._view(session)

    def _seek(self, session, from_seq):
        if from_seq < 0 or from_seq > session["frames"][-1][0]:
            raise ValueError("replay_cursor_out_of_range")
        index = bisect_right([seq for seq, _ in session["frames"]], from_seq) - 1
        if from_seq and (index < 0 or session["frames"][index][0] != from_seq):
            raise ValueError("replay_cursor_in_gap")
        session["cursor"] = max(0, index)
        session["playing"] = False
        session["play_offset"] = session["times"][session["cursor"]]
        session["view_revision"] += 1

    def _view(self, session):
        if session["playing"]:
            position = (
                session["play_offset"] + time.monotonic_ns() - session["play_started"]
            )
            index = min(
                len(session["frames"]) - 1, bisect_right(session["times"], position) - 1
            )
            if index != session["cursor"]:
                session["cursor"] = index
                session["view_revision"] += 1
            if position >= session["times"][-1]:
                session["playing"] = False
                session["play_offset"] = session["times"][-1]
        seq, original = session["frames"][session["cursor"]]
        snapshot = original.model_copy(
            update={
                "source": "replay",
                "replay_id": session["replay_id"],
                "stream_id": session["stream_id"],
                "revision": session["view_revision"],
                "operations": [],
                "capabilities": Capabilities(replay=True),
            }
        )
        return {
            "replay_id": session["replay_id"],
            "recorded_run_id": session["recorded_run_id"],
            "sha256": session["sha256"],
            "gap": session["gap"],
            "frame_seq": seq,
            "first_seq": session["frames"][0][0],
            "last_seq": session["frames"][-1][0],
            "frame_count": len(session["frames"]),
            "playing": session["playing"],
            "position_ms": session["times"][session["cursor"]] // 1_000_000,
            "duration_ms": session["times"][-1] // 1_000_000,
            "snapshot": snapshot.model_dump(by_alias=True),
        }

    def get(self, replay_id, from_seq=None):
        with self.lock:
            if replay_id not in self.sessions:
                raise ValueError("replay_not_found")
            session = self.sessions[replay_id]
            if from_seq is not None:
                self._seek(session, from_seq)
            return self._view(session)

    def delete(self, replay_id):
        with self.lock:
            if self.sessions.pop(replay_id, None) is None:
                raise ValueError("replay_not_found")

    def playback(self, replay_id, action):
        with self.lock:
            if replay_id not in self.sessions:
                raise ValueError("replay_not_found")
            session = self.sessions[replay_id]
            self._view(session)
            if action == "pause":
                if session["playing"]:
                    session["play_offset"] += (
                        time.monotonic_ns() - session["play_started"]
                    )
                session["playing"] = False
            elif action == "play":
                if (
                    not session["playing"]
                    and session["cursor"] < len(session["frames"]) - 1
                ):
                    session["play_started"] = time.monotonic_ns()
                    session["playing"] = True
            else:
                raise ValueError("unsupported_playback_action")
            return self._view(session)
