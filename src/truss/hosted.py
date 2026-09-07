"""Single-port demo hosting: website, live runtime, mock API and WebSockets."""

import asyncio
import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.staticfiles import StaticFiles

from .api import create_app
from .mock import MockState
from .observer import LiveState
from .runtime import TrussRun


def create_hosted_app(config_dir=None, dist=None, runtime_root=None, broker_port=None):
    root = Path(__file__).resolve().parents[2]
    config_dir = config_dir or os.getenv("TRUSS_CONFIG_DIR", str(root / "config"))
    dist = Path(dist or os.getenv("TRUSS_WEB_DIST", str(root / "web/dist")))
    runtime_root = runtime_root or os.getenv("TRUSS_RUNTIME_ROOT", "/tmp/truss-runtime")
    broker_port = broker_port or int(os.getenv("TRUSS_BROKER_PORT", "18883"))
    if not (dist / "index.html").is_file():
        raise RuntimeError("Website build missing; run npm --prefix web run build first.")
    website = Starlette(routes=[Mount("/", app=StaticFiles(directory=dist))])
    backends = {}

    @asynccontextmanager
    async def lifespan(app):
        run = TrussRun(config_dir, runtime_root=runtime_root, broker_port=broker_port)
        observer = None
        try:
            await asyncio.to_thread(run.start)
            observer = LiveState(run)
            # Uvicorn owns SIGTERM/SIGINT and invokes this lifespan's cleanup.
            await asyncio.to_thread(observer.start, install_signals=False)
            backends["live"] = create_app(observer)
            backends["mock"] = create_app(MockState(config_dir))
            async with AsyncExitStack() as stack:
                for backend in backends.values():
                    await stack.enter_async_context(backend.router.lifespan_context(backend))
                yield
        finally:
            if observer is not None:
                await asyncio.to_thread(observer.close)
            await asyncio.to_thread(run.close)
            backends.clear()

    lifecycle = Starlette(lifespan=lifespan)

    async def application(scope, receive, send):
        if scope["type"] == "lifespan":
            return await lifecycle(scope, receive, send)
        path = scope["path"]
        for prefix, replacement, source in (
            ("/console-api", "/api", "live"),
            ("/console-ws", "/ws", "live"),
            ("/api", "/api", "mock"),
            ("/ws", "/ws", "mock"),
        ):
            if path == prefix or path.startswith(prefix + "/"):
                rewritten = replacement + path[len(prefix):]
                forwarded = {**scope, "path": rewritten, "raw_path": rewritten.encode()}
                return await backends[source](forwarded, receive, send)
        if scope["type"] == "websocket":
            return await send({"type": "websocket.close", "code": 1008})
        if path in ("/", "/example", "/console", "/lab", "/info", "/credits"):
            scope = {**scope, "path": "/index.html", "raw_path": b"/index.html"}
        await website(scope, receive, send)

    return application


if __name__ == "__main__":
    import uvicorn

    # One worker owns the broker and shared demonstration state.
    uvicorn.run(create_hosted_app(), host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
