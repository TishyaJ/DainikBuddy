"""
Fallback handler: retry logic with exponential backoff + provider fallback chain.
Handles transient errors, rate limits, and graceful degradation.
"""

import asyncio
import logging
from typing import AsyncIterator, Callable, Optional, Any

logger = logging.getLogger(__name__)

# ============ FALLBACK CHAIN ============
# Maps primary provider → (fallback_provider, fallback_model)
FALLBACK_CHAIN: dict[str, tuple[str, str]] = {
    "openai": ("groq", "llama-3.3-70b-versatile"),
    "anthropic": ("openai", "gpt-4o-mini"),
    "gemini": ("groq", "llama-3.3-70b-versatile"),
    "groq": ("openai", "gpt-4o-mini"),
}


class FallbackHandler:
    """
    Handles retry-with-backoff and provider fallback for LLM streaming calls.

    Retry strategy:
    - Transient errors (429, 500, 502, 503, network timeout): retry up to 2 times
    - 429 with Retry-After header: honor that header's wait duration
    - 429 without Retry-After: exponential backoff starting at 2s
    - Other transient: exponential backoff starting at 1s
    - Non-transient (400, 401, 403): immediate yield of user-friendly error, no retry
    - After all retries exhausted: try fallback provider
    - If fallback also fails: yield domain-appropriate message from FALLBACK_MESSAGES
    """

    TRANSIENT_CODES = {429, 500, 502, 503}
    NON_TRANSIENT_CODES = {400, 401, 403}
    MAX_RETRIES = 2
    INITIAL_BACKOFF = 1.0   # seconds, for non-429 transient errors
    RATE_LIMIT_BACKOFF = 2.0  # seconds, for 429 without Retry-After

    async def execute_with_retry(
        self,
        adapter,
        messages: list[dict[str, Any]],
        params: dict[str, Any],
        fallback_adapter_factory: Optional[Callable] = None,
        buddy_type: str = "helper",
    ) -> AsyncIterator[tuple[str, Optional[dict]]]:
        """
        Execute a streaming completion with retry and fallback logic.

        Yields (text_chunk, usage_or_None) tuples.
        On total failure, yields a single fallback message chunk + ("", None).
        """
        from ._models import FALLBACK_MESSAGES

        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                # Attempt the actual streaming call
                async for chunk_tuple in adapter.stream_completion(
                    messages,
                    params.get("temperature", 0.7),
                    params.get("top_p"),
                    params.get("max_tokens", 1024),
                ):
                    yield chunk_tuple
                return  # Success - done

            except Exception as e:
                last_error = e
                status_code = self._extract_status_code(e)
                error_str = str(e)

                # Non-transient: don't retry, yield immediately
                if status_code in self.NON_TRANSIENT_CODES:
                    logger.warning(
                        f"Non-transient error {status_code} from provider, "
                        f"not retrying: {error_str}"
                    )
                    yield (f"I'm unable to process that request right now (error {status_code}). "
                           f"Please try again later.", None)
                    return

                # Transient: decide on wait time
                if status_code in self.TRANSIENT_CODES or self._is_network_error(e):
                    if attempt < self.MAX_RETRIES:
                        wait = self._compute_wait(e, status_code, attempt)
                        logger.warning(
                            f"Transient error (attempt {attempt + 1}/{self.MAX_RETRIES + 1}), "
                            f"retrying in {wait:.1f}s: {error_str}"
                        )
                        await asyncio.sleep(wait)
                        continue  # retry
                    else:
                        logger.warning(
                            f"All {self.MAX_RETRIES + 1} attempts exhausted for primary provider: {error_str}"
                        )
                else:
                    # Unknown error type — treat as transient for safety
                    if attempt < self.MAX_RETRIES:
                        wait = self.INITIAL_BACKOFF * (2 ** attempt)
                        logger.warning(
                            f"Unknown error (attempt {attempt + 1}/{self.MAX_RETRIES + 1}), "
                            f"retrying in {wait:.1f}s: {error_str}"
                        )
                        await asyncio.sleep(wait)
                        continue
                    else:
                        logger.warning(f"All attempts exhausted, unknown error: {error_str}")

                break  # Exit retry loop, attempt fallback

        # All retries exhausted — try fallback provider
        if fallback_adapter_factory is not None:
            try:
                logger.warning(f"Activating fallback provider for buddy '{buddy_type}'")
                fallback_adapter = fallback_adapter_factory()
                if fallback_adapter is not None:
                    async for chunk_tuple in fallback_adapter.stream_completion(
                        messages,
                        params.get("temperature", 0.7),
                        params.get("top_p"),
                        params.get("max_tokens", 1024),
                    ):
                        yield chunk_tuple
                    return
            except Exception as fb_error:
                logger.warning(f"Fallback provider also failed: {fb_error}")

        # Total failure — yield domain-appropriate message
        fallback_msg = FALLBACK_MESSAGES.get(buddy_type, FALLBACK_MESSAGES["helper"])
        logger.warning(f"All providers failed, yielding fallback message for buddy '{buddy_type}'")
        yield (fallback_msg, None)

    def _extract_status_code(self, error: Exception) -> Optional[int]:
        """Extract HTTP status code from SDK exceptions."""
        # OpenAI / Groq style
        if hasattr(error, "status_code"):
            return error.status_code
        # Anthropic style
        if hasattr(error, "status"):
            return error.status
        # httpx-based errors
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            return error.response.status_code
        # Try to parse from string (last resort)
        error_str = str(error)
        for code in [429, 500, 502, 503, 400, 401, 403]:
            if str(code) in error_str:
                return code
        return None

    def _is_network_error(self, error: Exception) -> bool:
        """Check if the error is a network/timeout error (treated as transient)."""
        import asyncio
        network_error_types = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
        if isinstance(error, network_error_types):
            return True
        error_name = type(error).__name__.lower()
        return any(kw in error_name for kw in ["timeout", "connection", "network"])

    def _compute_wait(self, error: Exception, status_code: Optional[int], attempt: int) -> float:
        """Compute how long to wait before the next retry."""
        # 429 with Retry-After header
        if status_code == 429:
            retry_after = self._extract_retry_after(error)
            if retry_after is not None:
                logger.warning(f"Rate limited. Retry-After: {retry_after}s")
                return retry_after
            # 429 without Retry-After: exponential starting at 2s
            return self.RATE_LIMIT_BACKOFF * (2 ** attempt)
        # Other transient: exponential starting at 1s
        return self.INITIAL_BACKOFF * (2 ** attempt)

    def _extract_retry_after(self, error: Exception) -> Optional[float]:
        """Extract Retry-After header value from rate limit errors."""
        # Check response headers
        response = getattr(error, "response", None)
        if response:
            headers = getattr(response, "headers", {}) or {}
            retry_after = headers.get("retry-after") or headers.get("Retry-After")
            if retry_after:
                try:
                    return float(retry_after)
                except (ValueError, TypeError):
                    pass
        # Check if the exception has a retry_after attribute (some SDKs)
        retry_after_attr = getattr(error, "retry_after", None)
        if retry_after_attr is not None:
            try:
                return float(retry_after_attr)
            except (ValueError, TypeError):
                pass
        return None
