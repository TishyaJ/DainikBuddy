"""
Shim module replacing the private emergentintegrations.llm.chat package.
Provides LlmChat, UserMessage, TextDelta, and StreamDone with the same interface
so the server can start. AI features will return fallback responses.
"""

from dataclasses import dataclass, field
from typing import Optional, AsyncIterator


@dataclass
class UserMessage:
    text: str


@dataclass
class TextDelta:
    content: str


@dataclass
class StreamDone:
    pass


class LlmChat:
    """Shim LLM chat client. Streams a fallback message instead of calling an external AI."""

    def __init__(self, api_key: str = "", session_id: str = "", system_message: str = ""):
        self.api_key = api_key
        self.session_id = session_id
        self.system_message = system_message
        self._provider = "openai"
        self._model = "gpt-4"

    def with_model(self, provider: str, model: str) -> "LlmChat":
        self._provider = provider
        self._model = model
        return self

    async def stream_message(self, message: UserMessage) -> AsyncIterator:
        """Yield a fallback response since the real AI service is unavailable."""
        fallback = (
            "I'm currently running without the AI backend. "
            "Please ensure the EMERGENT_LLM_KEY is configured and the emergentintegrations "
            "package is installed for full AI functionality. "
            "In the meantime, all other app features work normally!"
        )
        yield TextDelta(content=fallback)
        yield StreamDone()
