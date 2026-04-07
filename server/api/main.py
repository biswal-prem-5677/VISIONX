"""
VisionX — FastAPI Application Entry
=======================================
Main FastAPI application with all routes, middleware, and lifecycle.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

from loguru import logger

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    logger.warning("FastAPI not installed. Install with: pip install fastapi uvicorn")
    raise

from server.api.middleware.cors import get_cors_config
from server.api.middleware.rate_limiter import RateLimiter
from server.api.middleware.abuse_detector import AbuseDetector

# ============================================
# Application Lifecycle
# ============================================

rate_limiter = RateLimiter()
abuse_detector = AbuseDetector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    logger.info("=== VisionX Platform Starting ===")

    # Startup: connect databases, initialize services
    # (connections will be lazy in dev mode)
    logger.info("Platform services ready")

    yield

    # Shutdown: cleanup
    logger.info("=== VisionX Platform Shutting Down ===")


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="VisionX Platform API",
    description="Detect. Understand. Decide. Act.",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
cors_config = get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)


# ============================================
# Middleware: Rate Limiting & Abuse
# ============================================

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    client_ip = request.client.host if request.client else "unknown"

    # Check abuse block
    if abuse_detector.is_blocked(client_ip):
        return Response(
            content='{"error": "Too many requests. Access temporarily blocked."}',
            status_code=429,
            media_type="application/json",
        )

    # Check rate limit
    allowed, headers = rate_limiter.check(client_ip)
    if not allowed:
        return Response(
            content='{"error": "Rate limit exceeded"}',
            status_code=429,
            media_type="application/json",
            headers={k: str(v) for k, v in headers.items()},
        )

    # Process request
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000

    # Add rate limit headers
    for k, v in headers.items():
        response.headers[k] = str(v)

    response.headers["X-Response-Time-Ms"] = f"{duration:.1f}"

    return response


# ============================================
# Routes
# ============================================

@app.get("/", tags=["System"])
async def root():
    """API root — health check."""
    return {
        "name": "VisionX Platform API",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "up",
            "rate_limiter": "active",
            "abuse_detector": "active",
        },
    }


# ============================================
# Import and register route modules
# ============================================

from server.api.routes.auth import router as auth_router
from server.api.routes.vision import router as vision_router
from server.api.routes.events import router as events_router
from server.api.routes.devices import router as devices_router
from server.api.routes.analytics import router as analytics_router
from server.api.routes.admin import router as admin_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(vision_router, prefix="/api/v1/vision", tags=["Vision"])
app.include_router(events_router, prefix="/api/v1/events", tags=["Events"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])


# ============================================
# Run
# ============================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "platform.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
