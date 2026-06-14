"""
Unit tests for provider adapter message formatting and structure.
Tests: format_messages() output schema per provider, default params.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============ OPENAI ADAPTER ============

class TestOpenAIAdapterFormatMessages:
    def _make(self):
        from emergentintegrations.llm._adapters import OpenAIAdapter
        return OpenAIAdapter(api_key="test-key", model="gpt-4o-mini")

    def test_system_message_first(self):
        adapter = self._make()
        msgs = adapter.format_messages("You are helpful.", [], "Hello")
        assert msgs[0]["role"] == "system"
        assert msgs[0]["content"] == "You are helpful."

    def test_current_user_message_last(self):
        adapter = self._make()
        msgs = adapter.format_messages("System", [], "My message")
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"] == "My message"

    def test_history_in_order(self):
        adapter = self._make()
        history = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "response"},
        ]
        msgs = adapter.format_messages("System", history, "current")
        # system, user(first), assistant(response), user(current)
        assert len(msgs) == 4
        assert msgs[1]["role"] == "user"
        assert msgs[1]["content"] == "first"
        assert msgs[2]["role"] == "assistant"
        assert msgs[2]["content"] == "response"
        assert msgs[3]["content"] == "current"

    def test_empty_history(self):
        adapter = self._make()
        msgs = adapter.format_messages("Sys", [], "hi")
        assert len(msgs) == 2  # system + user
        assert msgs[-1]["role"] == "user"

    def test_no_system_message(self):
        adapter = self._make()
        msgs = adapter.format_messages("", [], "hi")
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"

    def test_all_messages_have_role_and_content(self):
        adapter = self._make()
        history = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]
        msgs = adapter.format_messages("sys", history, "current")
        for m in msgs:
            assert "role" in m
            assert "content" in m


# ============ ANTHROPIC ADAPTER ============

class TestAnthropicAdapterFormatMessages:
    def _make(self):
        from emergentintegrations.llm._adapters import AnthropicAdapter
        return AnthropicAdapter(api_key="test-key", model="claude-3-haiku-20240307")

    def test_system_stored_separately(self):
        adapter = self._make()
        msgs = adapter.format_messages("You are a helper.", [], "Hello")
        # System message should NOT be in the messages array
        for m in msgs:
            assert m.get("role") != "system"
        # Should be stored on the adapter for use in stream_completion
        assert adapter._system_message == "You are a helper."

    def test_current_user_message_last(self):
        adapter = self._make()
        msgs = adapter.format_messages("Sys", [], "My message")
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"] == "My message"

    def test_history_in_order_no_system(self):
        adapter = self._make()
        history = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "response"},
        ]
        msgs = adapter.format_messages("Sys", history, "current")
        # No system in array; user, assistant, user(current)
        assert len(msgs) == 3
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"
        assert msgs[2]["content"] == "current"

    def test_all_messages_have_role_and_content(self):
        adapter = self._make()
        history = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]
        msgs = adapter.format_messages("sys", history, "curr")
        for m in msgs:
            assert "role" in m
            assert "content" in m


# ============ GEMINI ADAPTER ============

class TestGeminiAdapterFormatMessages:
    def _make(self):
        from emergentintegrations.llm._adapters import GeminiAdapter
        return GeminiAdapter(api_key="test-key", model="gemini-1.5-flash")

    def test_system_instruction_stored(self):
        adapter = self._make()
        adapter.format_messages("You are Gemini.", [], "Hi")
        assert adapter._system_message == "You are Gemini."

    def test_contents_array_with_parts(self):
        adapter = self._make()
        contents = adapter.format_messages("Sys", [], "Hello world")
        assert isinstance(contents, list)
        assert contents[-1]["role"] == "user"
        assert "parts" in contents[-1]
        assert contents[-1]["parts"][0]["text"] == "Hello world"

    def test_assistant_mapped_to_model(self):
        adapter = self._make()
        history = [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "answer"},
        ]
        contents = adapter.format_messages("Sys", history, "followup")
        # "assistant" should become "model"
        assert contents[1]["role"] == "model"

    def test_user_role_preserved(self):
        adapter = self._make()
        history = [{"role": "user", "content": "q"}]
        contents = adapter.format_messages("Sys", history, "curr")
        assert contents[0]["role"] == "user"

    def test_all_entries_have_role_and_parts(self):
        adapter = self._make()
        history = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]
        contents = adapter.format_messages("sys", history, "curr")
        for c in contents:
            assert "role" in c
            assert "parts" in c
            assert "text" in c["parts"][0]


# ============ GROQ ADAPTER ============

class TestGroqAdapterFormatMessages:
    def _make(self):
        from emergentintegrations.llm._adapters import GroqAdapter
        return GroqAdapter(api_key="test-key", model="llama-3.3-70b-versatile")

    def test_same_format_as_openai(self):
        from emergentintegrations.llm._adapters import OpenAIAdapter, GroqAdapter
        openai_adapter = OpenAIAdapter(api_key="k", model="gpt-4o-mini")
        groq_adapter = GroqAdapter(api_key="k", model="llama-3.3-70b-versatile")
        history = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]
        openai_msgs = openai_adapter.format_messages("Sys", history, "curr")
        groq_msgs = groq_adapter.format_messages("Sys", history, "curr")
        assert openai_msgs == groq_msgs

    def test_system_first_user_last(self):
        adapter = self._make()
        msgs = adapter.format_messages("System", [], "Question")
        assert msgs[0]["role"] == "system"
        assert msgs[-1]["role"] == "user"


# ============ ADAPTER REGISTRY ============

class TestAdapterRegistry:
    def test_all_four_providers_registered(self):
        from emergentintegrations.llm._adapters import ADAPTER_CLASSES
        assert "openai" in ADAPTER_CLASSES
        assert "anthropic" in ADAPTER_CLASSES
        assert "gemini" in ADAPTER_CLASSES
        assert "groq" in ADAPTER_CLASSES

    def test_adapter_classes_instantiable(self):
        from emergentintegrations.llm._adapters import ADAPTER_CLASSES
        for provider, cls in ADAPTER_CLASSES.items():
            adapter = cls(api_key="test", model="test-model")
            assert adapter is not None


# ============ DEFAULT PARAMETERS ============

class TestDefaultParameters:
    def test_llmchat_default_temperature(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat()
        assert chat.temperature == 0.7

    def test_llmchat_default_max_tokens(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat()
        assert chat.max_tokens == 1024

    def test_llmchat_custom_temperature(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat(temperature=0.3)
        assert chat.temperature == 0.3

    def test_llmchat_custom_max_tokens(self):
        from emergentintegrations.llm.chat import LlmChat
        chat = LlmChat(max_tokens=512)
        assert chat.max_tokens == 512
