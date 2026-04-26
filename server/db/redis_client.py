"""
VisionX — Redis Client
==========================
Redis for real-time caching, rate limiting, and pub/sub.
"""

from __future__ import annotations

import os
from typing import Optional

from loguru import logger


class RedisClient:
    """
    Redis client for caching, rate limiting, and pub/sub.

    Used for:
    - Session caching
    - Rate limiting counters
    - Real-time event pub/sub
    - Temporary data storage
    """

    def __init__(
        self,
        host: str = "",
        port: int = 6379,
        db: int = 0,
        password: str = "",
    ):
        self._host = host or os.getenv("REDIS_HOST", "localhost")
        self._port = port or int(os.getenv("REDIS_PORT", "6379"))
        self._db = db
        self._password = password or os.getenv("REDIS_PASSWORD", "")
        self._client = None
        self._is_connected = False

        logger.info(f"Redis client initialized ({self._host}:{self._port})")

    async def connect(self) -> bool:
        """Connect to Redis."""
        try:
            import redis.asyncio as aioredis

            self._client = aioredis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password or None,
                decode_responses=True,
            )

            await self._client.ping()
            self._is_connected = True
            logger.info("Redis connected")
            return True

        except ImportError:
            logger.warning("redis not installed. Install with: pip install redis")
            return False
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
            self._is_connected = False
            logger.info("Redis disconnected")

    async def get(self, key: str) -> Optional[str]:
        """Get a value."""
        if not self._client:
            return None
        return await self._client.get(key)

    async def set(
        self, key: str, value: str, expire_seconds: int = 0
    ) -> bool:
        """Set a value with optional TTL."""
        if not self._client:
            return False
        if expire_seconds > 0:
            await self._client.setex(key, expire_seconds, value)
        else:
            await self._client.set(key, value)
        return True

    async def delete(self, key: str) -> bool:
        """Delete a key."""
        if not self._client:
            return False
        await self._client.delete(key)
        return True

    async def incr(self, key: str) -> int:
        """Increment a counter."""
        if not self._client:
            return 0
        return await self._client.incr(key)

    async def expire(self, key: str, seconds: int) -> None:
        """Set expiry on a key."""
        if self._client:
            await self._client.expire(key, seconds)

    async def publish(self, channel: str, message: str) -> None:
        """Publish a message to a channel."""
        if self._client:
            await self._client.publish(channel, message)

    @property
    def is_connected(self) -> bool:
        return self._is_connected
