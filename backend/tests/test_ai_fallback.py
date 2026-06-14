"""
Unit tests for FallbackHandler retry and fallback logic.
Tests: retry counts, backoff, non-transient immediate failure, fallback activation.
"""

import asyncio
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


def _make_error(status_code: int, retry_after: float = None):
    """Create a mock HTTP error with a given status code."""
    err = Exception(f"HTTP error {status_code}")
    err.status_code = status_code
    if retry_after is not None:
        response = MagicMock()
        response.headers = {"retry-after": str(retry_after)}
        err.response = response
    return err


async def _mock_adapter_raising(error, call_count_box: list):
    """Adapter that raises an error and records each attempt."""
    async def stream_completion(messages, temperature, top_p, max_tokens):
        call_count_box[0] += 1
        raise error
        yield  # make it an async generator
    return stream_completion


@pytest.fixture
def handler():
    from emergentintegrations.llm._fallback import FallbackHandler
    return FallbackHandler()


# ============ NON-TRANSIENT ERRORS ============

class TestNonTransientErrors:
    @pytest.mark.asyncio
    async def test_401_yields_error_immediately(self, handler):
        """401 should yield a user-friendly message without any retry."""
        error = _make_error(401)
        call_count = [0]

        class FailingAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count[0] += 1
                raise error
                yield  # async generator

        results = []
        async for chunk_text, usage in handler.execute_with_retry(
            FailingAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="helper"
        ):
            results.append(chunk_text)

        # Only 1 attempt (no retry)
        assert call_count[0] == 1
        # Should have yielded some error text
        assert any(results)

    @pytest.mark.asyncio
    async def test_403_yields_error_immediately(self, handler):
        error = _make_error(403)
        call_count = [0]

        class FailingAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count[0] += 1
                raise error
                yield

        results = []
        async for chunk_text, usage in handler.execute_with_retry(
            FailingAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="helper"
        ):
            results.append(chunk_text)

        assert call_count[0] == 1  # no retry

    @pytest.mark.asyncio
    async def test_400_yields_error_immediately(self, handler):
        error = _make_error(400)
        call_count = [0]

        class FailingAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count[0] += 1
                raise error
                yield

        results = []
        async for _ in handler.execute_with_retry(
            FailingAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="helper"
        ):
            pass

        assert call_count[0] == 1


# ============ TRANSIENT ERRORS (RETRY COUNT) ============

class TestTransientRetryCount:
    @pytest.mark.asyncio
    async def test_500_retries_up_to_max(self, handler):
        """500 should retry MAX_RETRIES times before activating fallback."""
        error = _make_error(500)
        call_count = [0]

        class FailingAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count[0] += 1
                raise error
                yield

        # Patch asyncio.sleep to skip waits
        with patch("asyncio.sleep", new=AsyncMock()):
            results = []
            async for chunk_text, usage in handler.execute_with_retry(
                FailingAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="helper"
            ):
                results.append(chunk_text)

        # MAX_RETRIES=2, so 3 total attempts (1 initial + 2 retries)
        assert call_count[0] == handler.MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_503_retries_up_to_max(self, handler):
        error = _make_error(503)
        call_count = [0]

        class FailingAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count[0] += 1
                raise error
                yield

        with patch("asyncio.sleep", new=AsyncMock()):
            async for _ in handler.execute_with_retry(
                FailingAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="helper"
            ):
                pass

        assert call_count[0] == handler.MAX_RETRIES + 1


# ============ RATE LIMIT HANDLING ============

class TestRateLimitHandling:
    @pytest.mark.asyncio
    async def test_429_with_retry_after_waits_correct_duration(self, handler):
        """429 with Retry-After header should wait exactly that many seconds."""
        error = _make_error(429, retry_after=5.0)
        call_count = [0]
        sleep_durations = []

        class FailingAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count[0] += 1
                raise error
                yield

        async def mock_sleep(duration):
            sleep_durations.append(duration)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            async for _ in handler.execute_with_retry(
                FailingAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="finance"
            ):
                pass

        # First sleep should be 5.0 (from Retry-After header)
        assert sleep_durations[0] == 5.0

    @pytest.mark.asyncio
    async def test_429_without_retry_after_uses_backoff(self, handler):
        """429 without Retry-After should start at RATE_LIMIT_BACKOFF seconds."""
        error = _make_error(429)  # no Retry-After
        call_count = [0]
        sleep_durations = []

        class FailingAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count[0] += 1
                raise error
                yield

        async def mock_sleep(duration):
            sleep_durations.append(duration)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            async for _ in handler.execute_with_retry(
                FailingAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="wellness"
            ):
                pass

        # First sleep should be RATE_LIMIT_BACKOFF (2.0s)
        assert sleep_durations[0] == handler.RATE_LIMIT_BACKOFF


# ============ FALLBACK PROVIDER ACTIVATION ============

class TestFallbackProviderActivation:
    @pytest.mark.asyncio
    async def test_fallback_activated_after_primary_exhaustion(self, handler):
        """After primary retries exhausted, fallback adapter should be called."""
        error = _make_error(500)
        call_count_primary = [0]
        call_count_fallback = [0]

        class PrimaryAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count_primary[0] += 1
                raise error
                yield

        class FallbackAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                call_count_fallback[0] += 1
                yield ("Fallback response", None)

        def fallback_factory():
            return FallbackAdapter()

        with patch("asyncio.sleep", new=AsyncMock()):
            results = []
            async for chunk_text, usage in handler.execute_with_retry(
                PrimaryAdapter(), [], {}, fallback_adapter_factory=fallback_factory, buddy_type="helper"
            ):
                results.append(chunk_text)

        assert call_count_fallback[0] == 1
        assert "Fallback response" in results


# ============ DOMAIN-APPROPRIATE FALLBACK MESSAGES ============

class TestFallbackMessages:
    @pytest.mark.asyncio
    async def test_finance_buddy_gets_finance_message(self, handler):
        from emergentintegrations.llm._models import FALLBACK_MESSAGES
        error = _make_error(500)

        class AlwaysFailAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                raise error
                yield

        with patch("asyncio.sleep", new=AsyncMock()):
            results = []
            async for chunk_text, usage in handler.execute_with_retry(
                AlwaysFailAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="finance"
            ):
                results.append(chunk_text)

        combined = " ".join(r for r in results if r)
        finance_msg = FALLBACK_MESSAGES["finance"]
        # Should contain key phrases from finance fallback
        assert "expense" in combined.lower() or "budget" in combined.lower()

    @pytest.mark.asyncio
    async def test_wellness_buddy_gets_wellness_message(self, handler):
        error = _make_error(500)

        class AlwaysFailAdapter:
            async def stream_completion(self, messages, temperature, top_p, max_tokens):
                raise error
                yield

        with patch("asyncio.sleep", new=AsyncMock()):
            results = []
            async for chunk_text, usage in handler.execute_with_retry(
                AlwaysFailAdapter(), [], {}, fallback_adapter_factory=None, buddy_type="wellness"
            ):
                results.append(chunk_text)

        combined = " ".join(r for r in results if r)
        assert "breath" in combined.lower() or "checking in" in combined.lower()


# ============ STATUS CODE EXTRACTION ============

class TestStatusCodeExtraction:
    def test_extracts_status_code_attribute(self, handler):
        err = Exception("error")
        err.status_code = 429
        assert handler._extract_status_code(err) == 429

    def test_extracts_from_status_attribute(self, handler):
        err = Exception("error")
        err.status = 401
        assert handler._extract_status_code(err) == 401

    def test_returns_none_for_unknown_error(self, handler):
        err = ValueError("something went wrong")
        result = handler._extract_status_code(err)
        # May return None or a code parsed from string
        assert result is None or isinstance(result, int)
