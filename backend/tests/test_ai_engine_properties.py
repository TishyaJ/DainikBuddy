import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock, AsyncMock

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
from emergentintegrations.llm._models import SUPPORTED_PROVIDERS, FALLBACK_MESSAGES, ConfigurationError
from emergentintegrations.llm._adapters import OpenAIAdapter, AnthropicAdapter, GeminiAdapter, GroqAdapter, ADAPTER_CLASSES
from emergentintegrations.llm._safety import SafetyFilter, check_safety
from emergentintegrations.llm._cache import ResponseCache

# Feature: ai-engine-enhancement, Property 1: Provider Routing Correctness
# with_model uses lazy adapter creation; we verify by forcing adapter creation via _create_adapter
@given(provider=st.sampled_from(list(SUPPORTED_PROVIDERS)), model=st.text(min_size=1))
def test_property_1_provider_routing(provider, model):
    chat = LlmChat(api_key="test_key").with_model(provider, model)
    # Adapter is lazily created; force creation to test routing
    adapter = chat._create_adapter()
    
    expected_class = ADAPTER_CLASSES[provider]
    assert isinstance(adapter, expected_class)

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
# When no API key is available, _resolve_api_key raises ConfigurationError.
# With lazy init in LlmChat, this surfaces during _create_adapter.
@given(provider=st.sampled_from(list(SUPPORTED_PROVIDERS)))
def test_property_4_missing_api_key(provider):
    with patch.dict('os.environ', {}, clear=True):
        chat = LlmChat(api_key="").with_model(provider, "test-model")
        with pytest.raises(ConfigurationError):
            chat._create_adapter()

# Feature: ai-engine-enhancement, Property 8: Safety Filter Correctness
@given(text=st.text(min_size=1))
def test_property_8_safety_filter(text):
    safety = SafetyFilter()
    is_safe, replacement, reason = safety.check(text)
    
    if is_safe:
        # When safe, replacement and reason are None
        assert replacement is None
        assert reason is None
    else:
        # When unsafe, replacement contains a safe alternative and reason explains why
        assert replacement is not None
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
    cache = ResponseCache(maxsize=10)
    for i in range(15):
        cache.put("openai", f"model-{i}", "sys", "user", f"resp-{i}")
    
    # Size should be at most 10 (TTLCache may expire items, but at most maxsize)
    assert cache.size <= 10
    
    # Earliest items should be evicted
    assert cache.get("openai", "model-0", "sys", "user") is None
    # Most recent should still be there
    assert cache.get("openai", "model-14", "sys", "user") == "resp-14"

# Feature: ai-engine-enhancement, Property 11: Domain-Appropriate Fallback Messages
# The FallbackHandler retries + tries a fallback provider before yielding the domain message.
# We mock _create_adapter AND _create_fallback_adapter to force total failure path.
@settings(deadline=None)
@given(buddy_type=st.sampled_from(["finance", "wellness", "discover", "helper"]))
@pytest.mark.asyncio
async def test_property_11_fallback_messages(buddy_type):
    chat = LlmChat(api_key="test_key", buddy_type=buddy_type, cache_enabled=False).with_model("groq", "test-model")
    
    # Mock adapter that always raises on stream_completion
    mock_adapter = MagicMock()
    
    async def failing_stream(*args, **kwargs):
        raise Exception("Simulated total failure")
        # Make it an async generator by using yield (never reached)
        yield  # noqa: this makes it an async generator
    
    mock_adapter.stream_completion = failing_stream
    mock_adapter.format_messages = MagicMock(return_value=[{"role": "user", "content": "hello"}])
    chat._adapter = mock_adapter

    # Also make fallback adapter fail
    with patch.object(chat, '_create_fallback_adapter', return_value=None):
        results = []
        async for chunk in chat.stream_message(UserMessage(text="hello")):
            results.append(chunk)

    assert len(results) >= 2
    assert isinstance(results[-1], StreamDone)
    
    # Check that one of the TextDeltas contains the fallback message for this domain
    fallback_msg = FALLBACK_MESSAGES.get(buddy_type, FALLBACK_MESSAGES["helper"])
    
    combined_text = "".join(c.content for c in results[:-1] if isinstance(c, TextDelta))
    assert fallback_msg in combined_text
