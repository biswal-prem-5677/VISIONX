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
    """Application startup and shutdown."""
    logger.info(f"=== VisionX Platform Starting (v{API_VERSION}) ===")
    logger.info("Platform services ready")

    yield

    logger.info("=== VisionX Platform Shutting Down ===")
    await ws_manager.shutdown()


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
    Liveness/readiness probe.

    Reports only what this process can actually verify. Downstream dependency
    checks (Postgres, Redis) belong here once those connections exist — a health
    check that reports "healthy" without checking dependencies is worse than none.
    """
    return {
        "status": "healthy",
        "version": API_VERSION,
        "timestamp": time.time(),
        "services": {
            "api": "up",
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
