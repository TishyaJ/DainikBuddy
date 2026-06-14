import pytest
import asyncio
from hypothesis import given, strategies as st
from unittest.mock import patch, MagicMock, AsyncMock

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
from emergentintegrations.llm._models import SUPPORTED_PROVIDERS, FALLBACK_MESSAGES, ConfigurationError
from emergentintegrations.llm._adapters import OpenAIAdapter, AnthropicAdapter, GeminiAdapter, GroqAdapter
from emergentintegrations.llm._safety import SafetyFilter
from emergentintegrations.llm._cache import ResponseCache

# Feature: ai-engine-enhancement, Property 1: Provider Routing Correctness
@given(provider=st.sampled_from(list(SUPPORTED_PROVIDERS)), model=st.text(min_size=1))
def test_property_1_provider_routing(provider, model):
    chat = LlmChat(api_key="test_key").with_model(provider, model)
    adapter = chat._adapter
    
    if provider == "openai":
        assert isinstance(adapter, OpenAIAdapter)
    elif provider == "anthropic":
        assert isinstance(adapter, AnthropicAdapter)
    elif provider == "gemini":
        assert isinstance(adapter, GeminiAdapter)
    elif provider == "groq":
        assert isinstance(adapter, GroqAdapter)

# Feature: ai-engine-enhancement, Property 2: Unsupported Provider Rejection
@given(provider=st.text().filter(lambda x: x not in SUPPORTED_PROVIDERS), model=st.text())
def test_property_2_unsupported_provider(provider, model):
    with pytest.raises(ValueError) as excinfo:
        LlmChat(api_key="test_key").with_model(provider, model)
    assert provider in str(excinfo.value)

# Feature: ai-engine-enhancement, Property 3: Stream Termination Invariant
@pytest.mark.asyncio
async def test_property_3_stream_termination():
    chat = LlmChat(api_key="test_key", cache_enabled=False).with_model("groq", "test-model")
    
    # Mock adapter to yield some chunks
    mock_adapter = AsyncMock()
    async def mock_stream(*args, **kwargs):
        yield ("chunk 1", None)
        yield (" chunk 2", None)
    mock_adapter.stream_completion = mock_stream
    chat._adapter = mock_adapter

    results = []
    async for chunk in chat.stream_message(UserMessage("hello")):
        results.append(chunk)

    assert len(results) > 0
    assert isinstance(results[-1], StreamDone)
    for res in results[:-1]:
        assert isinstance(res, TextDelta)

# Feature: ai-engine-enhancement, Property 4: Missing API Key Detection
@given(provider=st.sampled_from(list(SUPPORTED_PROVIDERS)))
@pytest.mark.asyncio
async def test_property_4_missing_api_key(provider):
    with patch.dict('os.environ', clear=True):
        chat = LlmChat(api_key="").with_model(provider, "test-model")
        with pytest.raises(ConfigurationError):
            async for _ in chat.stream_message(UserMessage("hello")):
                pass

# Feature: ai-engine-enhancement, Property 8: Safety Filter Correctness
@given(text=st.text(min_size=1))
def test_property_8_safety_filter(text):
    safety = SafetyFilter()
    is_safe, replacement, reason = safety.check(text)
    
    if is_safe:
        assert replacement == text
        assert reason is None
    else:
        assert replacement != text
        assert reason is not None
        assert "professional" in replacement.lower() or "icall" in replacement.lower()

# Feature: ai-engine-enhancement, Property 9: Cache Round-Trip with Interface Consistency
@given(provider=st.sampled_from(["openai", "groq"]),
       model=st.text(min_size=1),
       sys_msg=st.text(),
       user_msg=st.text(min_size=1),
       response=st.text(min_size=1))
@pytest.mark.asyncio
async def test_property_9_cache_round_trip(provider, model, sys_msg, user_msg, response):
    cache = ResponseCache()
    cache.put(provider, model, sys_msg, user_msg, response)
    
    retrieved = cache.get(provider, model, sys_msg, user_msg)
    assert retrieved == response

# Feature: ai-engine-enhancement, Property 10: Cache LRU Eviction at Capacity
def test_property_10_cache_lru():
    cache = ResponseCache(max_size=10)
    for i in range(15):
        cache.put("openai", f"model-{i}", "sys", "user", f"resp-{i}")
    
    # Size should be 10 (or less if cachetools behaves slightly differently, but max 10)
    assert len(cache._cache) <= 10
    
    # Earliest items should be evicted
    assert cache.get("openai", "model-0", "sys", "user") is None
    # Most recent should still be there
    assert cache.get("openai", "model-14", "sys", "user") == "resp-14"

# Feature: ai-engine-enhancement, Property 11: Domain-Appropriate Fallback Messages
@given(buddy_type=st.sampled_from(["finance", "wellness", "discover", "helper"]))
@pytest.mark.asyncio
async def test_property_11_fallback_messages(buddy_type):
    chat = LlmChat(api_key="test_key", buddy_type=buddy_type, cache_enabled=False).with_model("groq", "test-model")
    
    # Mock adapter to always fail
    mock_adapter = AsyncMock()
    mock_adapter.stream_completion.side_effect = Exception("Simulated total failure")
    chat._adapter = mock_adapter

    results = []
    async for chunk in chat.stream_message(UserMessage("hello")):
        results.append(chunk)

    assert len(results) >= 2
    assert isinstance(results[-1], StreamDone)
    
    # Check that one of the TextDeltas contains the fallback message for this domain
    fallback_msg = FALLBACK_MESSAGES.get(buddy_type, FALLBACK_MESSAGES["helper"])
    
    combined_text = "".join(c.content for c in results[:-1] if isinstance(c, TextDelta))
    # It might have [error] text from the exception handling in chat_stream if we used that, 
    # but in LlmChat.stream_message, it yields the fallback message directly.
    assert fallback_msg in combined_text
