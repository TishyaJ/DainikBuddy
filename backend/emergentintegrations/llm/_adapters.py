"""
Provider adapter protocol + implementations for all supported LLM providers.
Each adapter handles SDK-specific message formatting and streaming.
"""

import logging
from typing import Protocol, AsyncIterator, Any, Optional

logger = logging.getLogger(__name__)


# ============ PROTOCOL ============

class ProviderAdapter(Protocol):
    """Protocol all provider adapters must satisfy."""

    async def stream_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        top_p: Optional[float],
        max_tokens: int,
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        """
        Yield (text_chunk, usage_info_or_None) tuples.
        The last yield MAY include usage info from the provider's response.
        """
        ...

    def format_messages(
        self,
        system_message: str,
        history: list[dict[str, str]],
        current_message: str,
    ) -> list[dict[str, Any]]:
        """Format messages according to provider-specific schema."""
        ...


# ============ OPENAI ADAPTER ============

class OpenAIAdapter:
    """
    Adapter for OpenAI Chat Completions API.
    Format: [{role, content}] list with system as first message.
    """

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = None  # lazy init

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    def format_messages(
        self,
        system_message: str,
        history: list[dict[str, str]],
        current_message: str,
    ) -> list[dict[str, Any]]:
        msgs = []
        if system_message:
            msgs.append({"role": "system", "content": system_message})
        for h in history:
            msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": current_message})
        return msgs

    async def stream_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        top_p: Optional[float],
        max_tokens: int,
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if top_p is not None:
            kwargs["top_p"] = top_p

        usage_info = None
        async with await client.chat.completions.create(**kwargs) as stream:
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield (chunk.choices[0].delta.content, None)
                # Extract usage from the final chunk
                if hasattr(chunk, "usage") and chunk.usage:
                    usage_info = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }

        # Yield final empty string with usage info
        yield ("", usage_info)


# ============ ANTHROPIC ADAPTER ============

class AnthropicAdapter:
    """
    Adapter for Anthropic Messages API.
    Format: system as top-level param, user/assistant messages in array.
    """

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = None  # lazy init
        self._system_message = ""

    def _get_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self._api_key)
        return self._client

    def format_messages(
        self,
        system_message: str,
        history: list[dict[str, str]],
        current_message: str,
    ) -> list[dict[str, Any]]:
        # Store system message for use in stream_completion
        self._system_message = system_message
        msgs = []
        for h in history:
            msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": current_message})
        return msgs

    async def stream_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        top_p: Optional[float],
        max_tokens: int,
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if self._system_message:
            kwargs["system"] = self._system_message
        if top_p is not None:
            kwargs["top_p"] = top_p

        prompt_tokens = 0
        completion_tokens = 0

        async with client.messages.stream(**kwargs) as stream:
            async for event in stream:
                event_type = getattr(event, "type", None)
                if event_type == "message_start":
                    usage = getattr(event.message, "usage", None)
                    if usage:
                        prompt_tokens = getattr(usage, "input_tokens", 0)
                elif event_type == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    if delta and getattr(delta, "type", None) == "text_delta":
                        yield (delta.text, None)
                elif event_type == "message_delta":
                    usage = getattr(event, "usage", None)
                    if usage:
                        completion_tokens = getattr(usage, "output_tokens", 0)

        usage_info = None
        if prompt_tokens or completion_tokens:
            usage_info = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
        yield ("", usage_info)


# ============ GEMINI ADAPTER ============

class GeminiAdapter:
    """
    Adapter for Google Gemini GenerateContent API.
    Format: contents array with role/parts structure; system_instruction separate.
    """

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = None  # lazy init
        self._system_message = ""

    def _get_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            system_instr = self._system_message if self._system_message else None
            self._client = genai.GenerativeModel(
                model_name=self._model,
                system_instruction=system_instr,
            )
        return self._client

    def format_messages(
        self,
        system_message: str,
        history: list[dict[str, str]],
        current_message: str,
    ) -> list[dict[str, Any]]:
        self._system_message = system_message
        # Reset client so system_instruction is picked up fresh
        self._client = None
        contents = []
        for h in history:
            # Gemini uses "model" instead of "assistant"
            role = "model" if h["role"] == "assistant" else h["role"]
            contents.append({"role": role, "parts": [{"text": h["content"]}]})
        contents.append({"role": "user", "parts": [{"text": current_message}]})
        return contents

    async def stream_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        top_p: Optional[float],
        max_tokens: int,
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        client = self._get_client()

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if top_p is not None:
            generation_config["top_p"] = top_p

        usage_info = None
        async for chunk in await client.generate_content_async(
            messages,
            generation_config=generation_config,
            stream=True,
        ):
            if chunk.text:
                yield (chunk.text, None)
            # Capture usage metadata
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                um = chunk.usage_metadata
                usage_info = {
                    "prompt_tokens": getattr(um, "prompt_token_count", 0) or 0,
                    "completion_tokens": getattr(um, "candidates_token_count", 0) or 0,
                    "total_tokens": getattr(um, "total_token_count", 0) or 0,
                }

        yield ("", usage_info)


# ============ GROQ ADAPTER ============

class GroqAdapter:
    """
    Adapter for Groq Chat Completions API (OpenAI-compatible interface).
    Format: same OpenAI role/content objects, directed at api.groq.com.
    """

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client = None  # lazy init

    def _get_client(self):
        if self._client is None:
            from groq import AsyncGroq
            self._client = AsyncGroq(api_key=self._api_key)
        return self._client

    def format_messages(
        self,
        system_message: str,
        history: list[dict[str, str]],
        current_message: str,
    ) -> list[dict[str, Any]]:
        # Same as OpenAI format
        msgs = []
        if system_message:
            msgs.append({"role": "system", "content": system_message})
        for h in history:
            msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": current_message})
        return msgs

    async def stream_completion(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        top_p: Optional[float],
        max_tokens: int,
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if top_p is not None:
            kwargs["top_p"] = top_p

        usage_info = None
        async for chunk in await client.chat.completions.create(**kwargs):
            if chunk.choices and chunk.choices[0].delta.content:
                yield (chunk.choices[0].delta.content, None)
            if hasattr(chunk, "x_groq") and chunk.x_groq:
                # Groq includes usage in x_groq.usage on the final chunk
                groq_usage = getattr(chunk.x_groq, "usage", None)
                if groq_usage:
                    usage_info = {
                        "prompt_tokens": getattr(groq_usage, "prompt_tokens", 0),
                        "completion_tokens": getattr(groq_usage, "completion_tokens", 0),
                        "total_tokens": getattr(groq_usage, "total_tokens", 0),
                    }

        yield ("", usage_info)


# ============ ADAPTER REGISTRY ============

ADAPTER_CLASSES = {
    "openai": OpenAIAdapter,
    "anthropic": AnthropicAdapter,
    "gemini": GeminiAdapter,
    "groq": GroqAdapter,
}
