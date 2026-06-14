"""
LRU + TTL response cache for LLM responses.
Reduces API costs and latency for repeated similar queries.
"""

import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    LRU + TTL cache for LLM responses.

    Key = SHA-256 of (provider:model:sha256(system_message):user_message)
    TTL = 3600 seconds (1 hour) by default
    Max size = 1000 entries (LRU eviction when full)
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        try:
            from cachetools import TTLCache
            self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
            self._available = True
        except ImportError:
            logger.warning("cachetools not installed; response caching disabled")
            self._cache = {}
            self._available = False
        self._maxsize = maxsize
        self._ttl = ttl

    def _make_key(
        self,
        provider: str,
        model: str,
        system_hash: str,
        user_message: str,
    ) -> str:
        """Generate a deterministic cache key from request parameters."""
        raw = f"{provider}:{model}:{system_hash}:{user_message}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _hash_system(self, system_message: str) -> str:
        return hashlib.sha256(system_message.encode("utf-8")).hexdigest()

    def get(
        self,
        provider: str,
        model: str,
        system_message: str,
        user_message: str,
    ) -> Optional[str]:
        """
        Return cached response string if present and not expired.
        Returns None on cache miss.
        """
        if not self._available:
            return None
        key = self._make_key(provider, model, self._hash_system(system_message), user_message)
        result = self._cache.get(key)
        if result is not None:
            logger.info(f"Cache HIT for provider={provider} model={model}")
        return result

    def put(
        self,
        provider: str,
        model: str,
        system_message: str,
        user_message: str,
        response: str,
    ) -> None:
        """Store a response in the cache."""
        if not self._available or not response:
            return
        key = self._make_key(provider, model, self._hash_system(system_message), user_message)
        self._cache[key] = response
        logger.info(f"Cache STORE for provider={provider} model={model} ({len(response)} chars)")

    @property
    def size(self) -> int:
        return len(self._cache)


# Module-level singleton (shared across all LlmChat instances)
_cache = ResponseCache()
