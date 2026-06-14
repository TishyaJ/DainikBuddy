"""
LlmChat orchestrator — public AI engine interface.

This module is the drop-in replacement for the original shim.
server.py continues to import exactly:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

The orchestrator composes:
- Provider adapters (_adapters.py)
- Fallback handler (_fallback.py)
- Safety filter (_safety.py)
- Response cache (_cache.py)
- Shared models (_models.py)
"""

import logging
from dataclasses import dataclass
from typing import Optional, AsyncIterator

logger = logging.getLogger(__name__)


# ============ PUBLIC INTERFACE TYPES ============

@dataclass
class UserMessage:
    """Wraps the user's text input sent to the LLM."""
    text: str


@dataclass
class TextDelta:
    """Wraps an incremental chunk of text streamed back from the LLM."""
    content: str


@dataclass
class StreamDone:
    """Signals that the LLM has finished streaming its response."""
    pass


# ============ ORCHESTRATOR ============

class LlmChat:
    """
    Production-ready multi-provider LLM chat client.

    Drop-in replacement for the previous shim:
    - Same constructor signature (api_key, session_id, system_message)
    - Same with_model(provider, model) → LlmChat chain
    - Same async generator stream_message(UserMessage)
    - Added: history, temperature, top_p, max_tokens, cache_enabled, buddy_type

    Lazy initialization: provider clients are created on first stream_message call,
    not at import or construction time. The server starts fine even with no API keys.
    """

    def __init__(
        self,
        api_key: str = "",
        session_id: str = "",
        system_message: str = "",
        history: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        cache_enabled: bool = True,
        buddy_type: Optional[str] = None,
    ):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self.history: list[dict] = history or []
        self.temperature = temperature if temperature is not None else 0.7
        self.top_p = top_p
        self.max_tokens = max_tokens if max_tokens is not None else 1024
        self.cache_enabled = cache_enabled
        self.buddy_type = buddy_type or "helper"

        self._provider: str = "openai"
        self._model: str = "gpt-4o-mini"
        self._adapter = None          # lazy — created on first stream_message
        self._last_usage: Optional[dict] = None

    def with_model(self, provider: str, model: str) -> "LlmChat":
        """
        Configure which provider and model to use.

        Raises ValueError for unsupported providers (requirement 1.6).
        """
        from ._models import SUPPORTED_PROVIDERS
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(
                f"Unsupported provider '{provider}'. "
                f"Supported providers: {sorted(SUPPORTED_PROVIDERS)}"
            )
        self._provider = provider
        self._model = model
        self._adapter = None  # reset so it's recreated with new provider/model
        return self

    def get_last_usage(self) -> Optional[dict]:
        """
        Return token usage from the last completed stream_message call.

        Returns a dict with prompt_tokens, completion_tokens, total_tokens,
        or None if the provider didn't return usage data.
        """
        return self._last_usage

    def _create_adapter(self):
        """Lazy-initialize the provider adapter on first use."""
        from ._models import _resolve_api_key
        from ._adapters import ADAPTER_CLASSES

        api_key = _resolve_api_key(self._provider, self.api_key)
        adapter_class = ADAPTER_CLASSES[self._provider]
        return adapter_class(api_key=api_key, model=self._model)

    def _create_fallback_adapter(self):
        """Create a fallback adapter using the FALLBACK_CHAIN."""
        from ._fallback import FALLBACK_CHAIN
        from ._models import _resolve_api_key, SUPPORTED_PROVIDERS
        from ._adapters import ADAPTER_CLASSES

        fallback = FALLBACK_CHAIN.get(self._provider)
        if not fallback:
            return None

        fb_provider, fb_model = fallback
        if fb_provider not in SUPPORTED_PROVIDERS:
            return None

        try:
            fb_key = _resolve_api_key(fb_provider, "")
            fb_class = ADAPTER_CLASSES[fb_provider]
            return fb_class(api_key=fb_key, model=fb_model)
        except Exception as e:
            logger.warning(f"Could not create fallback adapter ({fb_provider}): {e}")
            return None

    async def stream_message(self, message: UserMessage) -> AsyncIterator:
        """
        Stream a response from the configured LLM provider.

        Orchestration flow:
        1. Check response cache (skip if cache_enabled=False)
        2. Lazy-init adapter
        3. Format messages for the provider
        4. Call adapter via fallback handler (with retry + fallback)
        5. Collect full response text
        6. Apply safety filter to complete response
        7. Yield TextDelta chunks + StreamDone
        8. Store result in cache
        9. Track token usage
        """
        from ._cache import _cache
        from ._fallback import FallbackHandler
        from ._safety import check_safety
        from ._models import FALLBACK_MESSAGES

        # 1. Cache check
        if self.cache_enabled:
            cached = _cache.get(
                self._provider,
                self._model,
                self.system_message,
                message.text,
            )
            if cached:
                logger.info(f"Serving cached response for session={self.session_id}")
                # Yield cached text as a single TextDelta + StreamDone
                yield TextDelta(content=cached)
                yield StreamDone()
                return

        # 2. Lazy-init adapter
        if self._adapter is None:
            try:
                self._adapter = self._create_adapter()
            except Exception as e:
                logger.error(f"Failed to create adapter: {e}")
                fallback_msg = FALLBACK_MESSAGES.get(self.buddy_type, FALLBACK_MESSAGES["helper"])
                yield TextDelta(content=str(e) if "ConfigurationError" in type(e).__name__ else fallback_msg)
                yield StreamDone()
                return

        # 3. Format messages for the provider
        try:
            messages = self._adapter.format_messages(
                self.system_message,
                self.history,
                message.text,
            )
        except Exception as e:
            logger.error(f"Message formatting failed: {e}")
            yield TextDelta(content=FALLBACK_MESSAGES.get(self.buddy_type, FALLBACK_MESSAGES["helper"]))
            yield StreamDone()
            return

        # 4. Stream via fallback handler (retry + fallback chain)
        handler = FallbackHandler()
        params = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }

        def fallback_factory():
            return self._create_fallback_adapter()

        # 5. Collect full response text for safety check + caching
        full_text = ""
        usage_data = None

        try:
            async for chunk_text, usage in handler.execute_with_retry(
                self._adapter,
                messages,
                params,
                fallback_adapter_factory=fallback_factory,
                buddy_type=self.buddy_type,
            ):
                if chunk_text:
                    full_text += chunk_text
                if usage:
                    usage_data = usage

        except Exception as e:
            logger.error(f"Unexpected error during streaming: {e}")
            full_text = FALLBACK_MESSAGES.get(self.buddy_type, FALLBACK_MESSAGES["helper"])

        # 6. Safety filter on complete response
        is_safe, replacement, reason = check_safety(full_text)
        if not is_safe and replacement:
            logger.warning(f"Safety filter replaced response. Reason: {reason}")
            full_text = replacement

        # 7. Yield the response
        if full_text:
            yield TextDelta(content=full_text)

        # 8. Store in cache
        if self.cache_enabled and full_text:
            _cache.put(
                self._provider,
                self._model,
                self.system_message,
                message.text,
                full_text,
            )

        # 9. Track usage
        if usage_data:
            self._last_usage = usage_data

        yield StreamDone()
