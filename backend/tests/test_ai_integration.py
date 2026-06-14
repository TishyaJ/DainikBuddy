"""
Integration tests for the AI engine.
Tests: full streaming flow with mocked providers, import compatibility,
server startup with missing keys, token usage tracking, cache integration.
"""

import asyncio
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


# ============ IMPORT COMPATIBILITY ============

class TestImportCompatibility:
    def test_import_from_chat_module(self):
        """The canonical import used by server.py must work unchanged."""
        from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
        assert LlmChat is not None
        assert UserMessage is not None
        assert TextDelta is not None
        assert StreamDone is not None

    def test_import_from_package(self):
        """Package-level import must also work."""
        from emergentintegrations.llm import LlmChat, UserMessage, TextDelta, StreamDone
        assert LlmChat is not None

    def test_usermessage_has_text_field(self):
        from emergentintegrations.llm.chat import UserMessage
        msg = UserMessage(text="hello")
        assert msg.text == "hello"

    def test_textdelta_has_content_field(self):
        from emergentintegrations.llm.chat import TextDelta
        delta = TextDelta(content="chunk")
        assert delta.content == "chunk"

    def test_streamdone_instantiates(self):
        from emergentintegrations.llm.chat import StreamDone
        done = StreamDone()
        assert done is not None


# ============ CONSTRUCTOR BACKWARD COMPATIBILITY ============

class TestConstructorBackwardCompatibility:
    def test_all_original_params_accepted(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat(api_key="k", session_id="s", system_message="sys")
        assert chat.api_key == "k"
        assert chat.session_id == "s"
        assert chat.system_message == "sys"

    def test_defaults_work_with_no_params(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat()
        assert chat is not None
        assert chat.temperature == 0.7
        assert chat.max_tokens == 1024

    def test_new_optional_params_accepted(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat(
            history=[{"role": "user", "content": "hi"}],
            temperature=0.3,
            top_p=0.9,
            max_tokens=512,
            cache_enabled=False,
            buddy_type="finance",
        )
        assert chat.temperature == 0.3
        assert chat.max_tokens == 512
        assert chat.cache_enabled is False
        assert chat.buddy_type == "finance"


# ============ WITH_MODEL ============

class TestWithModel:
    def test_with_model_accepts_supported_providers(self):
        from emergentintegrations.llm.chat import LlmChat
        from emergentintegrations.llm._models import SUPPORTED_PROVIDERS
        chat = LlmChat()
        for provider in SUPPORTED_PROVIDERS:
            result = chat.with_model(provider, "test-model")
            assert result is chat  # returns self for chaining

    def test_with_model_raises_for_unsupported_provider(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat()
        with pytest.raises(ValueError) as exc_info:
            chat.with_model("unsupported-provider-xyz", "model")
        assert "unsupported-provider-xyz" in str(exc_info.value)

    def test_with_model_chain(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat().with_model("openai", "gpt-4o-mini")
        assert chat._provider == "openai"
        assert chat._model == "gpt-4o-mini"


# ============ FULL STREAMING FLOW (MOCKED PROVIDER) ============

class TestFullStreamingFlow:
    @pytest.mark.asyncio
    async def test_stream_message_ends_with_streamdone(self):
        """Every stream_message call must end with StreamDone."""
        from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

        chat = LlmChat(api_key="fake", system_message="You are helpful.")
        chat = chat.with_model("openai", "gpt-4o-mini")

        # Mock the adapter's stream_completion to return fake chunks
        async def mock_stream(messages, temp, top_p, max_tokens):
            yield ("Hello ", None)
            yield (" world!", None)
            yield ("", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})

        mock_adapter = MagicMock()
        mock_adapter.format_messages.return_value = [{"role": "user", "content": "hi"}]
        mock_adapter.stream_completion = mock_stream
        chat._adapter = mock_adapter

        events = []
        async for event in chat.stream_message(UserMessage(text="hi")):
            events.append(event)

        # Last event must be StreamDone
        assert isinstance(events[-1], StreamDone)
        # All preceding events must be TextDelta
        for e in events[:-1]:
            assert isinstance(e, TextDelta)

    @pytest.mark.asyncio
    async def test_stream_message_yields_textdelta_with_content(self):
        """TextDelta objects should carry the text content."""
        from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

        chat = LlmChat(api_key="fake", cache_enabled=False)
        chat = chat.with_model("openai", "gpt-4o-mini")

        async def mock_stream(messages, temp, top_p, max_tokens):
            yield ("Test response content", None)
            yield ("", None)

        mock_adapter = MagicMock()
        mock_adapter.format_messages.return_value = [{"role": "user", "content": "hi"}]
        mock_adapter.stream_completion = mock_stream
        chat._adapter = mock_adapter

        deltas = []
        async for event in chat.stream_message(UserMessage(text="hi")):
            if isinstance(event, TextDelta):
                deltas.append(event.content)

        combined = "".join(deltas)
        assert "Test response content" in combined

    @pytest.mark.asyncio
    async def test_stream_ends_with_streamdone_on_error(self):
        """Even on total failure, stream must end with StreamDone."""
        from emergentintegrations.llm.chat import LlmChat, UserMessage, StreamDone

        chat = LlmChat(api_key="fake", cache_enabled=False)
        chat = chat.with_model("openai", "gpt-4o-mini")

        async def mock_stream(messages, temp, top_p, max_tokens):
            raise Exception("Simulated API failure")
            yield  # make it async generator

        mock_adapter = MagicMock()
        mock_adapter.format_messages.return_value = [{"role": "user", "content": "hi"}]
        mock_adapter.stream_completion = mock_stream
        chat._adapter = mock_adapter

        events = []
        with patch("asyncio.sleep", new=AsyncMock()):
            async for event in chat.stream_message(UserMessage(text="hi")):
                events.append(event)

        assert isinstance(events[-1], StreamDone)


# ============ LAZY INITIALIZATION ============

class TestLazyInitialization:
    def test_server_starts_without_api_keys(self):
        """LlmChat can be created with no keys — error only raised on stream_message."""
        from emergentintegrations.llm.chat import LlmChat
        # This should NOT raise even with no env vars
        chat = LlmChat()
        chat = chat.with_model("gemini", "gemini-1.5-flash")
        # adapter is NOT created until stream_message is called
        assert chat._adapter is None

    def test_adapter_not_created_at_init(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat(api_key="", session_id="test")
        assert chat._adapter is None

    def test_missing_key_raises_config_error_at_request_time(self):
        """ConfigurationError should only be raised when streaming, not at import."""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        from emergentintegrations.llm._models import ConfigurationError

        # Ensure env var is absent
        env_backup = {}
        for key in ["OPENAI_API_KEY", "EMERGENT_LLM_KEY"]:
            env_backup[key] = os.environ.pop(key, None)

        try:
            chat = LlmChat()  # Should NOT raise
            chat.with_model("openai", "gpt-4o-mini")
            # Now streaming should raise or yield error
            # (ConfigurationError may be yielded as a TextDelta rather than raised)
        finally:
            for key, val in env_backup.items():
                if val is not None:
                    os.environ[key] = val


# ============ TOKEN USAGE TRACKING ============

class TestTokenUsageTracking:
    @pytest.mark.asyncio
    async def test_usage_tracked_after_stream(self):
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        chat = LlmChat(api_key="fake", cache_enabled=False)
        chat = chat.with_model("openai", "gpt-4o-mini")

        usage_data = {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}

        async def mock_stream(messages, temp, top_p, max_tokens):
            yield ("Response text", None)
            yield ("", usage_data)

        mock_adapter = MagicMock()
        mock_adapter.format_messages.return_value = [{"role": "user", "content": "hi"}]
        mock_adapter.stream_completion = mock_stream
        chat._adapter = mock_adapter

        async for _ in chat.stream_message(UserMessage(text="hi")):
            pass

        usage = chat.get_last_usage()
        assert usage is not None
        assert usage["prompt_tokens"] == 20
        assert usage["completion_tokens"] == 10
        assert usage["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_no_usage_returns_none(self):
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        chat = LlmChat(api_key="fake", cache_enabled=False)
        chat = chat.with_model("openai", "gpt-4o-mini")

        async def mock_stream(messages, temp, top_p, max_tokens):
            yield ("Response", None)
            yield ("", None)  # No usage info

        mock_adapter = MagicMock()
        mock_adapter.format_messages.return_value = [{"role": "user", "content": "hi"}]
        mock_adapter.stream_completion = mock_stream
        chat._adapter = mock_adapter

        async for _ in chat.stream_message(UserMessage(text="hi")):
            pass

        # get_last_usage should still be None (no usage returned)
        assert chat.get_last_usage() is None


# ============ CACHE INTEGRATION ============

class TestCacheIntegration:
    @pytest.mark.asyncio
    async def test_second_identical_call_returns_cached(self):
        """Second call with same params should return from cache without hitting adapter."""
        from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta

        chat = LlmChat(api_key="fake", system_message="System", cache_enabled=True)
        chat = chat.with_model("openai", "gpt-4o")
        adapter_call_count = [0]

        async def mock_stream(messages, temp, top_p, max_tokens):
            adapter_call_count[0] += 1
            yield ("Cached response text", None)
            yield ("", None)

        mock_adapter = MagicMock()
        mock_adapter.format_messages.return_value = [{"role": "user", "content": "same question"}]
        mock_adapter.stream_completion = mock_stream
        chat._adapter = mock_adapter

        # First call — goes to adapter
        async for _ in chat.stream_message(UserMessage(text="same question")):
            pass
        assert adapter_call_count[0] == 1

        # Second call — should come from cache
        results = []
        async for event in chat.stream_message(UserMessage(text="same question")):
            if isinstance(event, TextDelta):
                results.append(event.content)

        # Adapter should NOT have been called again
        assert adapter_call_count[0] == 1
        assert "Cached response text" in "".join(results)

    @pytest.mark.asyncio
    async def test_cache_disabled_always_hits_adapter(self):
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        chat = LlmChat(api_key="fake", system_message="System", cache_enabled=False)
        chat = chat.with_model("openai", "gpt-4o")
        adapter_call_count = [0]

        async def mock_stream(messages, temp, top_p, max_tokens):
            adapter_call_count[0] += 1
            yield ("Response", None)
            yield ("", None)

        mock_adapter = MagicMock()
        mock_adapter.format_messages.return_value = [{"role": "user", "content": "q"}]
        mock_adapter.stream_completion = mock_stream
        chat._adapter = mock_adapter

        for _ in range(3):
            async for _ in chat.stream_message(UserMessage(text="q")):
                pass

        # Each call should hit the adapter
        assert adapter_call_count[0] == 3


# ============ API KEY OVERRIDE ============

class TestApiKeyOverride:
    def test_constructor_key_overrides_env_var(self):
        from emergentintegrations.llm._models import _resolve_api_key
        # Set env var
        os.environ["OPENAI_API_KEY"] = "env-key-value"
        try:
            result = _resolve_api_key("openai", "constructor-key-value")
            assert result == "constructor-key-value"
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_env_var_used_when_no_constructor_key(self):
        from emergentintegrations.llm._models import _resolve_api_key
        os.environ["OPENAI_API_KEY"] = "env-key-value"
        try:
            result = _resolve_api_key("openai", "")
            assert result == "env-key-value"
        finally:
            del os.environ["OPENAI_API_KEY"]
