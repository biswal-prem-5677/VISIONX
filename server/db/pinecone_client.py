"""
VisionX — Pinecone Vector Database Client
=============================================
Pinecone for storing and querying vector embeddings.
Used for face recognition, image search, and similarity.
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger


class PineconeClient:
    """
    Pinecone vector database client.

    Stores and queries vector embeddings for:
    - Face recognition embeddings
    - Image similarity search
    - Semantic search over detection history
    """

    def __init__(
        self,
        api_key: str = "",
        index_name: str = "visionx-embeddings",
        dimension: int = 128,
    ):
        self._api_key = api_key or os.getenv("PINECONE_API_KEY", "")
        self._index_name = index_name
        self._dimension = dimension
        self._index = None
        self._is_connected = False

        logger.info(f"Pinecone client initialized (index: {index_name})")

    def connect(self) -> bool:
        """Connect to Pinecone."""
        if not self._api_key:
            logger.warning("Pinecone API key not configured")
            return False

        try:
            from pinecone import Pinecone

            pc = Pinecone(api_key=self._api_key)

            # Check if index exists
            existing = pc.list_indexes().names()
            if self._index_name not in existing:
                pc.create_index(
                    name=self._index_name,
                    dimension=self._dimension,
                    metric="cosine",
                )

            self._index = pc.Index(self._index_name)
            self._is_connected = True
            logger.info(f"Pinecone connected (index: {self._index_name})")
            return True

        except ImportError:
            logger.warning(
                "pinecone not installed. "
                "Install with: pip install pinecone-client"
            )
            return False
        except Exception as e:
            logger.error(f"Pinecone connection failed: {e}")
            return False

    def upsert(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Insert or update a vector."""
        if not self._index:
            return False

        try:
            self._index.upsert(
                vectors=[(id, vector, metadata or {})]
            )
            return True
        except Exception as e:
            logger.error(f"Pinecone upsert error: {e}")
            return False

    def query(
        self,
        vector: list[float],
        top_k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Query similar vectors."""
        if not self._index:
            return []

        try:
            result = self._index.query(
                vector=vector,
                top_k=top_k,
                filter=filter,
                include_metadata=True,
            )

            return [
                {
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata,
                }
                for match in result.matches
            ]
        except Exception as e:
            logger.error(f"Pinecone query error: {e}")
            return []

    def delete(self, ids: list[str]) -> bool:
        """Delete vectors by IDs."""
        if not self._index:
            return False

        try:
            self._index.delete(ids=ids)
            return True
        except Exception as e:
            logger.error(f"Pinecone delete error: {e}")
            return False

    @property
    def is_connected(self) -> bool:
        return self._is_connected
