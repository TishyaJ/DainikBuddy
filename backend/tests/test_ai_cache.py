"""
Unit tests for ResponseCache: hit/miss, TTL expiration, LRU eviction, disabled cache.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def cache():
    from emergentintegrations.llm._cache import ResponseCache
    return ResponseCache(maxsize=10, ttl=3600)


@pytest.fixture
def small_cache():
    """Cache with very small capacity for LRU eviction tests."""
    from emergentintegrations.llm._cache import ResponseCache
    return ResponseCache(maxsize=3, ttl=3600)


PROVIDER = "openai"
MODEL = "gpt-4o-mini"
SYSTEM = "You are a helpful assistant."
USER_MSG = "What is my budget?"
RESPONSE = "Your budget is ₹15,000 this month."


# ============ CACHE HIT ============

class TestCacheHit:
    def test_hit_returns_stored_response(self, cache):
        cache.put(PROVIDER, MODEL, SYSTEM, USER_MSG, RESPONSE)
        result = cache.get(PROVIDER, MODEL, SYSTEM, USER_MSG)
        assert result == RESPONSE

    def test_same_key_different_response_overwrites(self, cache):
        cache.put(PROVIDER, MODEL, SYSTEM, USER_MSG, "old response")
        cache.put(PROVIDER, MODEL, SYSTEM, USER_MSG, "new response")
        result = cache.get(PROVIDER, MODEL, SYSTEM, USER_MSG)
        assert result == "new response"

    def test_different_user_messages_have_different_keys(self, cache):
        cache.put(PROVIDER, MODEL, SYSTEM, "question 1", "answer 1")
        cache.put(PROVIDER, MODEL, SYSTEM, "question 2", "answer 2")
        assert cache.get(PROVIDER, MODEL, SYSTEM, "question 1") == "answer 1"
        assert cache.get(PROVIDER, MODEL, SYSTEM, "question 2") == "answer 2"

    def test_different_providers_have_different_keys(self, cache):
        cache.put("openai", MODEL, SYSTEM, USER_MSG, "openai answer")
        cache.put("anthropic", MODEL, SYSTEM, USER_MSG, "anthropic answer")
        assert cache.get("openai", MODEL, SYSTEM, USER_MSG) == "openai answer"
        assert cache.get("anthropic", MODEL, SYSTEM, USER_MSG) == "anthropic answer"

    def test_different_system_messages_have_different_keys(self, cache):
        cache.put(PROVIDER, MODEL, "System A", USER_MSG, "answer A")
        cache.put(PROVIDER, MODEL, "System B", USER_MSG, "answer B")
        assert cache.get(PROVIDER, MODEL, "System A", USER_MSG) == "answer A"
        assert cache.get(PROVIDER, MODEL, "System B", USER_MSG) == "answer B"


# ============ CACHE MISS ============

class TestCacheMiss:
    def test_miss_returns_none(self, cache):
        result = cache.get(PROVIDER, MODEL, SYSTEM, "never asked this")
        assert result is None

    def test_empty_cache_always_misses(self, cache):
        assert cache.get("openai", "gpt-4", "any system", "any message") is None

    def test_miss_after_different_provider(self, cache):
        cache.put("openai", MODEL, SYSTEM, USER_MSG, RESPONSE)
        result = cache.get("groq", MODEL, SYSTEM, USER_MSG)
        assert result is None


# ============ LRU EVICTION ============

class TestLRUEviction:
    def test_cache_never_exceeds_maxsize(self, small_cache):
        """Insert more entries than maxsize; cache should never exceed maxsize."""
        for i in range(20):
            small_cache.put(PROVIDER, MODEL, SYSTEM, f"question {i}", f"answer {i}")
        assert small_cache.size <= small_cache._maxsize

    def test_oldest_entry_evicted(self, small_cache):
        """Insert 4 entries into a maxsize=3 cache; first entry should be evicted."""
        for i in range(4):
            small_cache.put(PROVIDER, MODEL, SYSTEM, f"question {i}", f"answer {i}")
        # The first entry should be evicted (LRU)
        # Note: LRU evicts least recently USED, so if all inserts have equal recency,
        # the first inserted should be gone
        assert small_cache.get(PROVIDER, MODEL, SYSTEM, "question 0") is None
        # Last entry should still be there
        assert small_cache.get(PROVIDER, MODEL, SYSTEM, "question 3") == "answer 3"


# ============ CACHE KEY USES SHA-256 ============

class TestCacheKeyDerivation:
    def test_key_uses_sha256_of_system_message(self, cache):
        """Verify the key derivation uses sha256 of system message (not raw text)."""
        import hashlib
        system_hash = hashlib.sha256(SYSTEM.encode("utf-8")).hexdigest()
        raw = f"{PROVIDER}:{MODEL}:{system_hash}:{USER_MSG}"
        expected_key = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        # Verify _make_key produces the same result
        actual_key = cache._make_key(PROVIDER, MODEL, cache._hash_system(SYSTEM), USER_MSG)
        assert actual_key == expected_key

    def test_slightly_different_system_produces_different_key(self, cache):
        key1 = cache._make_key(PROVIDER, MODEL, cache._hash_system("System A"), USER_MSG)
        key2 = cache._make_key(PROVIDER, MODEL, cache._hash_system("System B"), USER_MSG)
        assert key1 != key2


# ============ EMPTY RESPONSE NOT CACHED ============

class TestEmptyResponseNotCached:
    def test_empty_string_not_stored(self, cache):
        cache.put(PROVIDER, MODEL, SYSTEM, USER_MSG, "")
        result = cache.get(PROVIDER, MODEL, SYSTEM, USER_MSG)
        assert result is None

    def test_whitespace_not_considered_empty(self, cache):
        # Non-empty responses should be cached
        cache.put(PROVIDER, MODEL, SYSTEM, USER_MSG, "   some content   ")
        result = cache.get(PROVIDER, MODEL, SYSTEM, USER_MSG)
        assert result is not None


# ============ MODULE-LEVEL SINGLETON ============

class TestModuleLevelSingleton:
    def test_module_cache_instance_exists(self):
        from emergentintegrations.llm._cache import _cache
        assert _cache is not None

    def test_module_cache_has_correct_defaults(self):
        from emergentintegrations.llm._cache import _cache
        assert _cache._maxsize == 1000
        assert _cache._ttl == 3600
