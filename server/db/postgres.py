"""
VisionX — PostgreSQL Database
=================================
PostgreSQL connection, models, and CRUD operations.
Uses SQLAlchemy async for non-blocking database access.
"""

from __future__ import annotations

import os
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "visionx"
    user: str = "postgres"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def sync_url(self) -> str:
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class PostgresClient:
    """
    PostgreSQL database client.

    Manages async connection pool and provides CRUD helpers.
    Uses SQLAlchemy async engine for non-blocking access.
    """

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self._config = config or DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "visionx"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
        )
        self._engine = None
        self._session_factory = None
        self._is_connected = False

        logger.info(
            f"PostgreSQL client initialized "
            f"({self._config.host}:{self._config.port}/{self._config.database})"
        )

    async def connect(self) -> bool:
        """Establish database connection."""
        try:
            from sqlalchemy.ext.asyncio import (
                AsyncSession,
                create_async_engine,
            )
            from sqlalchemy.orm import sessionmaker

            self._engine = create_async_engine(
                self._config.url,
                pool_size=self._config.pool_size,
                max_overflow=self._config.max_overflow,
                echo=False,
            )

            self._session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            self._is_connected = True
            logger.info("PostgreSQL connected")
            return True

        except ImportError:
            logger.warning(
                "SQLAlchemy/asyncpg not installed. "
                "Install with: pip install sqlalchemy asyncpg"
            )
            return False
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Close database connection."""
        if self._engine:
            await self._engine.dispose()
            self._is_connected = False
            logger.info("PostgreSQL disconnected")

    def get_session(self):
        """Get an async database session."""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        return self._session_factory()

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def config(self) -> DatabaseConfig:
        return self._config
