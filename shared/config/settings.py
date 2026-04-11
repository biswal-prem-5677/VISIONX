"""
VisionX — Shared Configuration Settings
===========================================
Central configuration loaded from environment + defaults.
"""

from __future__ import annotations

import os
from typing import Optional
from pydantic import BaseModel, Field


class EdgeConfig(BaseModel):
    """Edge pipeline settings."""
    camera_source: str | int = 0
    camera_width: int = 1280
    camera_height: int = 720
    camera_fps: int = 30
    confidence_threshold: float = 0.5
    model_path: str = "yolov8n.pt"
    performance_mode: str = "balanced"  # lite, balanced, max


class ServerConfig(BaseModel):
    """FastAPI server settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    jwt_secret: str = Field(default_factory=lambda: os.getenv("JWT_SECRET", "visionx-dev-secret"))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30


class DatabaseConfig(BaseModel):
    """Database connection settings."""
    postgres_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./visionx.db"))
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    pinecone_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("PINECONE_API_KEY"))
    pinecone_index: str = "visionx-embeddings"


class BillingConfig(BaseModel):
    """Stripe billing settings."""
    stripe_secret_key: Optional[str] = Field(default_factory=lambda: os.getenv("STRIPE_SECRET_KEY"))
    stripe_webhook_secret: Optional[str] = Field(default_factory=lambda: os.getenv("STRIPE_WEBHOOK_SECRET"))
    free_camera_limit: int = 1
    pro_camera_limit: int = 5
    enterprise_camera_limit: int = 999


class AppSettings(BaseModel):
    """Root application settings."""
    app_name: str = "VisionX"
    app_version: str = "1.0.0"
    environment: str = Field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    edge: EdgeConfig = Field(default_factory=EdgeConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    billing: BillingConfig = Field(default_factory=BillingConfig)


# Singleton settings instance
settings = AppSettings()
