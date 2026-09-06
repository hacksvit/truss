"""Live/mock operator API. Owner M5. No provider means explicitly unavailable."""

import asyncio
import json
import time
from pathlib import Path
from uuid import uuid4, UUID
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, Request, WebSocket, WebSocketDisconnect, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .api_models import (
    CapRequest,
    ChaosRequest,
    LabRequest,
    Operation,
    Snapshot,
    BenchmarkResult,
    RuleRequest,
    FaultRequest,
    ReplayRequest,
    ReplaySeek,
    ReplayPlayback,
    LabJob,
    FairnessView,
    RuntimeView,
    RecordingCatalog,
    ReplayView,
)
from .lab_jobs import LabJobs
from .recordings import Recordings
from .mock import utc_now


def create_app(provider=None) -> FastAPI:
    jobs = LabJobs()
    recordings = Recordings(
        provider.run.directory.parent
        if provider and provider.source == "live"
        else None
    )

    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            await asyncio.to_thread(jobs.close)

    app = FastAPI(
        title="Truss operator API",
        version="0.2.0",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.provider = provider
    app.state.requests = {}
    app.state.lab_busy = False
    app.state.lab_jobs = jobs
    app.state.recordings = recordings

    def error(status, code, message):
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "fields": [],
                    "request_id": str(uuid4()),
                    "retryable": status in (429, 503),
                }
            },
        )

    @app.middleware("http")
    async def no_cache(request: Request, call_next):
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return error(400, "invalid_request", "Invalid Content-Length")
        if length < 0:
            return error(400, "invalid_request", "Invalid Content-Length")
        if length > 16384:
            return error(413, "invalid_request", "Request exceeds 16 KiB")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 16384:
                return error(413, "invalid_request", "Request exceeds 16 KiB")
        request._body = bytes(body)
        if body and "application/json" in request.headers.get("content-type", ""):

            def unique(pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        raise ValueError("Duplicate JSON key")
                    result[key] = value
                return result

            try:
                json.loads(
                    body,
                    object_pairs_hook=unique,
                    parse_constant=lambda _: (_ for _ in ()).throw(
                        ValueError("Nonfinite JSON")
                    ),
                )
            except (ValueError, UnicodeDecodeError):
                return error(
                    422, "invalid_request", "Malformed, duplicate-key or nonfinite JSON"
                )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return error(422, "invalid_request", "Invalid request fields")

    @app.get("/api/v1/health")
    async def health():
        if provider and provider.source == "live":
            snap = provider.snapshot()
            return {
                "api": "ok",
                "broker": "connected"
                if provider.c.transport.connected.is_set()
                else "disconnected",
                "coordinator": snap.site.coordinator_status,
                "mode": "live",
                "run_id": provider.run_id,
                "evidence": "ok"
                if not provider.failure and not provider.gaps
                else "unavailable",
                "capabilities": snap.capabilities.model_dump(),
            }
        return {
            "api": "ok",
            "broker": "disconnected",
            "coordinator": "unknown",
            "mode": "mock" if provider else "unwired",
            "run_id": provider.run_id if provider else None,
            "evidence": "unavailable",
            "capabilities": provider.snapshot().capabilities.model_dump()
            if provider
            else {},
        }

    @app.get("/api/v1/state", response_model=Snapshot)
    async def state(source: str = "live"):
        if not provider:
            return error(
                503,
                "dependency_unavailable",
                "This server has no state provider. Start truss live for MQTT state or truss mock for synthetic state.",
            )
        if source != provider.source:
            return error(
                403,
                "read_only",
                "Requested source does not match this server. Mock cannot masquerade as live.",
            )
        return provider.snapshot().model_dump(by_alias=True)

    def control(body, key, kind, effect):
        if not provider or body.source != provider.source:
            return error(403, "read_only", "Wrong source or live runtime unavailable")
        try:
            UUID(key)
        except (ValueError, TypeError):
            return error(422, "invalid_request", "Idempotency-Key must be a UUID")
        encoded = json.dumps({"kind": kind, **body.model_dump()}, sort_keys=True)
        previous = app.state.requests.get(key)
        if previous:
            return (
                JSONResponse(previous[1], status_code=202)
                if previous[0] == encoded
                else error(
                    409, "idempotency_conflict", "Key was used for different input"
                )
            )
        if (
            body.run_id != provider.run_id
            or body.expected_control_revision != provider.control_revision
        ):
            return error(
                409, "revision_conflict", "Refresh state before changing controls"
            )
        try:
            effect()
        except ValueError as exc:
            return error(422, "invalid_request", str(exc))
        operation = Operation(
            operation_id=str(uuid4()),
            run_id=provider.run_id,
            kind=kind,
            status="applied",
            control_revision=provider.control_revision,
            created_at=utc_now(),
            finished_at=utc_now(),
            message="Applied to mock state only",
        )
        provider.operations.append(operation)
        output = operation.model_dump()
        app.state.requests[key] = (encoded, output)
        return JSONResponse(
            output,
            status_code=202,
            headers={"Location": f"/api/v1/operations/{operation.operation_id}"},
        )

    @app.post("/api/v1/cap", response_model=Operation, status_code=202)
    async def cap(body: CapRequest, idempotency_key: str = Header()):
        if provider and provider.source == "live":
            return await live_control(body, idempotency_key, "cap")
        return control(
            body, idempotency_key, "cap", lambda: provider.set_cap(body.watts)
        )

    @app.post("/api/v1/chaos", response_model=Operation, status_code=202)
    async def chaos(body: ChaosRequest, idempotency_key: str = Header()):
        if provider and provider.source == "live":
            return await live_control(body, idempotency_key, "chaos")
        return control(
            body,
            idempotency_key,
            "chaos",
            lambda: provider.chaos(body.action, body.member_id),
        )

    @app.post("/api/v1/rule", response_model=Operation, status_code=202)
    async def rule(body: RuleRequest, idempotency_key: str = Header()):
        if not provider or provider.source != "live":
            return error(
                409,
                "unsupported",
                "Authoritative debt controls require the live backend",
            )
        return await live_control(body, idempotency_key, "rule")

    @app.post("/api/v1/faults", response_model=Operation, status_code=202)
    async def faults(body: FaultRequest, idempotency_key: str = Header()):
        if not provider or provider.source != "live":
            return error(409, "unsupported", "Delivery faults require the live runtime")
        return await live_control(body, idempotency_key, "fault")

    @app.get("/api/v1/fairness", response_model=FairnessView)
    async def fairness():
        if not provider or provider.source != "live":
            return error(
                409, "unsupported", "Mock does not invent authoritative service history"
            )
        return await asyncio.to_thread(provider.fairness_state)

    @app.get("/api/v1/runtime", response_model=RuntimeView)
    async def runtime():
        if not provider or provider.source != "live":
            return error(409, "unsupported", "No live process supervisor")
        return {
            "run_id": provider.run_id,
            "processes": [
                {
                    "name": name,
                    "pid": process.pid,
                    "running": process.poll() is None,
                    "exit_code": process.poll(),
                }
                for name, process in provider.run.supervisor.children.items()
            ],
            "evidence_error": provider.failure,
            "recording_full": provider.recording_full,
        }

    async def live_control(body, key, kind):
        if body.source != "live":
            return error(403, "read_only", "Live server requires live source")
        try:
            UUID(key)
        except (ValueError, TypeError):
            return error(422, "invalid_request", "Idempotency-Key must be a UUID")
        try:
            operation = await asyncio.to_thread(provider.control, body, key, kind)
            return JSONResponse(
                operation.model_dump(),
                status_code=202,
                headers={"Location": f"/api/v1/operations/{operation.operation_id}"},
            )
        except ValueError as exc:
            code = str(exc)
            return error(
                409
                if code
                in (
                    "revision_conflict",
                    "idempotency_conflict",
                    "unsupported",
                    "debt_unavailable",
                )
                else 422,
                code,
                code,
            )

    @app.get("/api/v1/operations/{operation_id}", response_model=Operation)
    async def operation(operation_id: str):
        if provider and provider.source == "live":
            op = await asyncio.to_thread(provider.get_operation, operation_id)
            return (
                op.model_dump() if op else error(404, "not_found", "Unknown operation")
            )
        for op in provider.operations if provider else []:
            if op.operation_id == operation_id:
                return op.model_dump()
        return error(404, "not_found", "Unknown operation")

    @app.get("/api/v1/events")
    async def events(after_seq: int = Query(default=0, ge=0)):
        selected = (
            [e.model_dump() for e in provider.events if e.seq > after_seq]
            if provider
            else []
        )
        return {
            "items": selected[-500:],
            "gap": len(selected) > 500
            or bool(getattr(provider, "gaps", 0))
            or after_seq < getattr(provider, "events_cutoff_seq", 0),
        }

    @app.post("/api/v1/lab/benchmark", response_model=BenchmarkResult)
    async def lab(body: LabRequest):
        if not provider:
            return error(503, "dependency_unavailable", "No active backend")
        try:
            job = jobs.submit(body, str(uuid4()))
        except ValueError as exc:
            return error(429, str(exc), "One benchmark at a time")
        while job.status == "running":
            await asyncio.sleep(0.05)
            job = jobs.get(job.job_id)
        return (
            job.result
            if job.status == "complete"
            else error(503, "benchmark_failed", job.error)
        )

    @app.post("/api/v1/lab/runs", response_model=LabJob, status_code=202)
    async def lab_run(body: LabRequest, idempotency_key: str = Header()):
        if not provider:
            return error(503, "dependency_unavailable", "No active backend")
        try:
            UUID(idempotency_key)
        except ValueError:
            return error(422, "invalid_request", "Idempotency-Key must be a UUID")
        try:
            job = jobs.submit(body, idempotency_key)
        except ValueError as exc:
            return error(429 if str(exc) == "busy" else 409, str(exc), str(exc))
        return JSONResponse(
            job.model_dump(),
            status_code=202,
            headers={"Location": f"/api/v1/lab/runs/{job.job_id}"},
        )

    @app.get("/api/v1/lab/runs/{job_id}", response_model=LabJob)
    async def lab_result(job_id: str):
        return jobs.get(job_id) or error(404, "not_found", "Unknown benchmark job")

    @app.get("/api/v1/recordings", response_model=RecordingCatalog)
    async def recording_list():
        return await asyncio.to_thread(recordings.catalog)

    def replay_error(exc):
        code = str(exc)
        return error(
            404
            if code.endswith("not_found")
            else 413
            if code in ("recording_too_large", "recording_too_many_frames")
            else 409,
            code,
            code,
        )

    @app.post("/api/v1/replays", status_code=201, response_model=ReplayView)
    async def replay_create(body: ReplayRequest):
        try:
            return await asyncio.to_thread(
                recordings.create, body.recorded_run_id, body.from_seq
            )
        except (ValueError, OSError) as exc:
            return replay_error(exc)

    @app.get("/api/v1/replays/{replay_id}", response_model=ReplayView)
    async def replay_state(replay_id: str):
        try:
            return recordings.get(replay_id)
        except ValueError as exc:
            return replay_error(exc)

    @app.post("/api/v1/replays/{replay_id}/seek", response_model=ReplayView)
    async def replay_seek(replay_id: str, body: ReplaySeek):
        try:
            return recordings.get(replay_id, body.from_seq)
        except ValueError as exc:
            return replay_error(exc)

    @app.delete("/api/v1/replays/{replay_id}")
    async def replay_close(replay_id: str):
        try:
            recordings.delete(replay_id)
            return {"deleted": True}
        except ValueError as exc:
            return replay_error(exc)

    @app.post("/api/v1/replays/{replay_id}/playback", response_model=ReplayView)
    async def replay_playback(replay_id: str, body: ReplayPlayback):
        try:
            return recordings.playback(replay_id, body.action)
        except ValueError as exc:
            return replay_error(exc)

    @app.post("/api/v1/{unimplemented:path}")
    def unsupported(unimplemented: str):
        return error(
            409,
            "unsupported",
            f"{unimplemented} is specified but not integrated; see implementation-status.md",
        )

    @app.websocket("/ws/v1/state")
    async def stream(socket: WebSocket):
        if (
            not provider
            or socket.query_params.get("source") != provider.source
            or "truss.ui.v1" not in socket.scope.get("subprotocols", [])
        ):
            await socket.close(code=1008)
            return
        await socket.accept(subprotocol="truss.ui.v1")
        await socket.send_json(
            {
                "type": "hello",
                "schema": "truss.ws.v1",
                "stream_id": provider.stream_id,
                "run_id": provider.run_id,
                "source": provider.source,
                "heartbeat_ms": 1000,
                "snapshot_hz": 4,
            }
        )
        pending, last_pong = set(), time.monotonic()

        async def receive():
            nonlocal last_pong
            while True:
                raw = await socket.receive_text()
                try:
                    frame = json.loads(raw) if len(raw) <= 4096 else None
                except ValueError:
                    frame = None
                if (
                    not isinstance(frame, dict)
                    or frame.get("type") != "pong"
                    or not isinstance(frame.get("id"), str)
                    or frame["id"] not in pending
                ):
                    await socket.close(code=1008)
                    return
                pending.discard(frame["id"])
                last_pong = time.monotonic()

        receiver = asyncio.create_task(receive())
        try:
            tick = 0
            while not receiver.done():
                if time.monotonic() - last_pong > 5:
                    await socket.close(code=1008)
                    break
                if tick % 4 == 0:
                    token = str(uuid4())
                    pending.add(token)
                    await asyncio.wait_for(
                        socket.send_json({"type": "ping", "id": token}), timeout=2
                    )
                await asyncio.wait_for(
                    socket.send_json(
                        {
                            "type": "snapshot",
                            "data": provider.snapshot().model_dump(by_alias=True),
                        }
                    ),
                    timeout=2,
                )
                tick += 1
                await asyncio.sleep(0.25)
        except (WebSocketDisconnect, RuntimeError, asyncio.TimeoutError):
            pass
        finally:
            receiver.cancel()
            await asyncio.gather(receiver, return_exceptions=True)

    dist = Path(__file__).resolve().parents[2] / "web" / "dist"
    if dist.exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{route:path}")
        def frontend(route: str):
            if route not in ("", "console", "lab"):
                return error(404, "not_found", "Unknown route")
            return FileResponse(dist / "index.html")

    return app
