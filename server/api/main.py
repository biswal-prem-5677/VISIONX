"""
VisionX — FastAPI Application Entry
=======================================
Main FastAPI application: middleware, routers, WebSocket transport, lifecycle.

Run locally:
    uvicorn server.api.main:app --reload
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import asynccontextmanager

from loguru import logger

try:
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
except ImportError:
    logger.warning("FastAPI not installed. Install with: pip install fastapi uvicorn")
    raise

from server.api.middleware.abuse_detector import AbuseDetector
from server.api.middleware.cors import get_cors_config
from server.api.middleware.rate_limiter import RateLimiter
from server.api.websockets.live_feed import ws_manager

# Importing this resolves DATABASE_URL, which in production raises rather than
# guessing at a local file (server/db/session.py). A misconfigured deployment
# therefore fails at import — before it can accept a request it cannot serve.
from server.db.session import database

API_VERSION = "0.3.0"

# NOTE: both are per-process, in-memory. They are correct for a single replica
# and become ineffective the moment the API is horizontally scaled. Externalize
# to Redis before adding a second replica (ENGINEERING_REVIEW.md §5, R15).
rate_limiter = RateLimiter()
abuse_detector = AbuseDetector()

#: Paths exempt from rate limiting — probes must never be throttled, or an
#: orchestrator will kill a healthy pod during a traffic spike.
_RATE_LIMIT_EXEMPT = frozenset({"/health", "/", "/docs", "/redoc", "/openapi.json"})


# ============================================
# Application Lifecycle
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown.

    The database engine is created here rather than lazily on first use, so the
    connection pool is warm before the first request and disposed of on the way
    out instead of being abandoned to the garbage collector.

    ``connect()`` does not dial the server — SQLAlchemy engines connect lazily —
    so an unreachable database does not prevent startup. It surfaces at
    ``/health``, which pings for real and reports ``degraded``. Refusing to boot
    would be the wrong trade: the process still serves every route that needs no
    row, and a crash loop during a database outage removes capacity without
    fixing anything.
    """
    logger.info(f"=== VisionX Platform Starting (v{API_VERSION}) ===")

    await database.connect()
    logger.info("Platform services ready")

    yield

    logger.info("=== VisionX Platform Shutting Down ===")
    await ws_manager.shutdown()
    await database.disconnect()


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="VisionX Platform API",
    description="Detect. Understand. Decide. Act.",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, **get_cors_config())


# ============================================
# Middleware: request ID, rate limiting, abuse
# ============================================

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """
    Attach a request ID, enforce rate limits, and record timing.

    The request ID is echoed on every response and every error body so a user
    report can be correlated to a log line.
    """
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
    request.state.request_id = request_id

    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path

    if path not in _RATE_LIMIT_EXEMPT:
        if abuse_detector.is_blocked(client_ip):
            return _error_response(
                429, "rate_limited",
                "Too many requests. Access temporarily blocked.", request_id,
            )

        allowed, limit_headers = rate_limiter.check(client_ip)
        if not allowed:
            resp = _error_response(
                429, "rate_limited", "Rate limit exceeded", request_id,
            )
            for k, v in limit_headers.items():
                resp.headers[k] = str(v)
            return resp
    else:
        limit_headers = {}

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    for k, v in limit_headers.items():
        response.headers[k] = str(v)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.1f}"

    return response


def _error_response(
    status_code: int, code: str, message: str, request_id: str
) -> JSONResponse:
    """Single error envelope shared by middleware and exception handlers."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
    )


# ============================================
# System Routes
# ============================================

@app.get("/", tags=["System"])
async def root():
    """API root — service identity."""
    return {
        "name": "VisionX Platform API",
        "version": API_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
async def health_check():
    """
    Liveness probe.

    Reports only what this process can actually verify. The database entry is a
    real ``SELECT 1`` — not a guess from the fact that an engine object exists —
    because a health check that reports "healthy" without touching its
    dependencies is worse than no health check at all.

    **Why an unreachable database is still HTTP 200.** This endpoint is wired as
    the container healthcheck in ``docker/Dockerfile.server`` and
    ``docker/docker-compose.yml``, where a non-200 means *restart this process*.
    Restarting the API does not repair Postgres; it removes serving capacity in
    the middle of an outage and drops every live WebSocket with it. So the status
    code answers "is this process alive", while ``status`` and ``services`` in
    the body answer "can it do its job" — and the body never claims ``healthy``
    when it cannot. A caller that needs readiness semantics reads ``status``.

    Redis is still absent from this list on purpose: no part of the application
    connects to it yet, so any value here would be invented (tracker DEF-024).
    """
    database_up = await database.ping()

    return {
        "status": "healthy" if database_up else "degraded",
        "version": API_VERSION,
        "timestamp": time.time(),
        "services": {
            "api": "up",
            "database": "up" if database_up else "down",
            "rate_limiter": "active",
            "abuse_detector": "active",
            "websocket": "active",
        },
        "websocket_connections": ws_manager.connection_count,
    }


# ============================================
# WebSocket: live detection feed
# ============================================

@app.websocket("/ws/vision")
async def vision_websocket(websocket: WebSocket):
    """
    Real-time detection/event stream consumed by the dashboard.

    Client → server messages (JSON):
        {"type": "subscribe",   "channel": "live:cam-1"}
        {"type": "unsubscribe", "channel": "live:cam-1"}
        {"type": "ping"}

    Server → client messages are emitted by ``ws_manager`` broadcasts and carry
    a ``type`` of ``detection``, ``event``, ``status``, ``pong``, or ``error``.

    Clients are subscribed to ``events`` on connect so alerts are never missed
    while a viewer is deciding which camera to watch.
    """
    connection_id = uuid.uuid4().hex[:16]

    await ws_manager.connect(connection_id, websocket)
    ws_manager.subscribe(connection_id, "events")

    try:
        await ws_manager.send_to(connection_id, {
            "type": "status",
            "connection_id": connection_id,
            "is_processing": False,
            "subscribed": ["events"],
        })

        while True:
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await ws_manager.send_to(connection_id, {
                    "type": "error", "message": "Invalid JSON",
                })
                continue

            if not isinstance(message, dict):
                await ws_manager.send_to(connection_id, {
                    "type": "error", "message": "Expected a JSON object",
                })
                continue

            msg_type = message.get("type")

            if msg_type == "ping":
                await ws_manager.send_to(connection_id, {"type": "pong"})

            elif msg_type == "subscribe":
                channel = message.get("channel")
                if isinstance(channel, str) and channel:
                    ws_manager.subscribe(connection_id, channel)
                    await ws_manager.send_to(connection_id, {
                        "type": "subscribed", "channel": channel,
                    })
                else:
                    await ws_manager.send_to(connection_id, {
                        "type": "error", "message": "subscribe requires a 'channel' string",
                    })

            elif msg_type == "unsubscribe":
                channel = message.get("channel")
                if isinstance(channel, str) and channel:
                    ws_manager.unsubscribe(connection_id, channel)
                    await ws_manager.send_to(connection_id, {
                        "type": "unsubscribed", "channel": channel,
                    })

            else:
                await ws_manager.send_to(connection_id, {
                    "type": "error", "message": f"Unknown message type: {msg_type!r}",
                })

    except WebSocketDisconnect:
        logger.debug(f"WebSocket client disconnected: {connection_id}")
    except Exception as e:  # noqa: BLE001 - one bad socket must not kill the server
        logger.warning(f"WebSocket error ({connection_id}): {type(e).__name__}: {e}")
    finally:
        ws_manager.disconnect(connection_id)


# ============================================
# Routers
# ============================================

from server.api.routes.admin import router as admin_router  # noqa: E402
from server.api.routes.analytics import router as analytics_router  # noqa: E402
from server.api.routes.auth import router as auth_router  # noqa: E402
from server.api.routes.billing import router as billing_router  # noqa: E402
from server.api.routes.config import router as config_router  # noqa: E402
from server.api.routes.devices import router as devices_router  # noqa: E402
from server.api.routes.events import router as events_router  # noqa: E402
from server.api.routes.gdpr import router as gdpr_router  # noqa: E402
from server.api.routes.help import router as help_router  # noqa: E402
from server.api.routes.notifications import router as notifications_router  # noqa: E402
from server.api.routes.usage_tracking import router as usage_router  # noqa: E402
from server.api.routes.vision import router as vision_router  # noqa: E402

_V1 = "/api/v1"

# Routers that declare their own `prefix=` on APIRouter are mounted at the
# version root; the rest get an explicit prefix here.
app.include_router(auth_router, prefix=f"{_V1}/auth", tags=["Authentication"])
app.include_router(vision_router, prefix=f"{_V1}/vision", tags=["Vision"])
app.include_router(events_router, prefix=f"{_V1}/events", tags=["Events"])
app.include_router(devices_router, prefix=f"{_V1}/devices", tags=["Devices"])
app.include_router(analytics_router, prefix=f"{_V1}/analytics", tags=["Analytics"])
app.include_router(admin_router, prefix=f"{_V1}/admin", tags=["Admin"])
app.include_router(gdpr_router, prefix=_V1, tags=["GDPR"])

# Previously defined but never mounted — their endpoints were unreachable.
app.include_router(billing_router, prefix=_V1)
app.include_router(config_router, prefix=_V1)
app.include_router(help_router, prefix=_V1)
app.include_router(notifications_router, prefix=_V1)
app.include_router(usage_router, prefix=_V1)


# ============================================
# Run
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
