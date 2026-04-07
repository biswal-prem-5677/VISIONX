"""
VisionX — CORS Middleware Configuration
==========================================
Cross-Origin Resource Sharing configuration.
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger


# Default allowed origins
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


def get_cors_config() -> dict[str, Any]:
    """
    Get CORS configuration for FastAPI.

    Reads additional origins from CORS_ORIGINS env var (comma-separated).
    """
    extra = os.getenv("CORS_ORIGINS", "")
    origins = list(DEFAULT_ORIGINS)

    if extra:
        origins.extend([o.strip() for o in extra.split(",") if o.strip()])

    config = {
        "allow_origins": origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "expose_headers": [
            "X-RateLimit-Limit-Minute",
            "X-RateLimit-Remaining-Minute",
            "X-RateLimit-Limit-Hour",
            "X-RateLimit-Remaining-Hour",
        ],
    }

    logger.info(f"CORS configured (origins: {len(origins)})")
    return config
