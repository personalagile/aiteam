"""Short-term memory storage using Redis or in-memory fallback.

This module provides a minimal wrapper that appends text items per agent and
retrieves recent history. Redis is used when available via ``REDIS_URL``; the
fallback is an in-memory dictionary suitable for tests and local dev.
"""

from __future__ import annotations

import os
from collections import defaultdict

try:  # Optional dependency; keep imports local and typed
    import redis as _redis  # type: ignore
    from redis.exceptions import RedisError as _RedisError  # type: ignore
except ImportError:  # pragma: no cover - optional dependency fallback
    _redis = None  # type: ignore

    class _RedisError(Exception):  # type: ignore
        """Fallback Redis error type when redis is not installed."""


_STORE: defaultdict[str, list[str]] = defaultdict(list)


class ShortTermMemory:
    """Short-term memory backed by Redis if available, else in-memory."""

    def __init__(self) -> None:
        self._client = None
        url = os.getenv("REDIS_URL")
        if _redis and url:
            try:
                self._client = _redis.Redis.from_url(url, decode_responses=True)
                # quick ping
                self._client.ping()
            except _RedisError:  # pragma: no cover - fallback path
                self._client = None
        if self._client is None:
            # Use a shared in-memory store across instances for dev/tests
            self._store = _STORE

    def append(self, agent: str, item: str) -> None:
        """Append an item to the agent's short-term memory."""
        if self._client is not None:
            self._client.rpush(f"stm:{agent}", item)
        else:
            self._store[agent].append(item)

    def history(self, agent: str, limit: int = 20) -> list[str]:
        """Return up to ``limit`` most recent items for ``agent``."""
        if self._client is not None:
            data = self._client.lrange(f"stm:{agent}", -limit, -1)
            return list(data)
        return self._store[agent][-limit:]
