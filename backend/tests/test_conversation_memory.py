"""
Unit tests for the conversation memory service.

Tests cover:
- store_message: message persistence and auto-trim trigger
- get_conversation_context: returns last 5 messages in chronological order
- get_summary: retrieves stored summary
- trim_and_summarize: summarizes older messages when count > 50
- get_full_context_for_chat: assembles full context
- Graceful fallback: returns defaults when DB fails
- _generate_summary: stays within 500 char limit
- _select_representative_indices: selects evenly spaced indices

Requirements: 9.1, 9.2, 9.5, 9.6, 9.7
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from conversation_memory import (
    store_message,
    get_conversation_context,
    get_summary,
    trim_and_summarize,
    get_full_context_for_chat,
    _generate_summary,
    _select_representative_indices,
    _truncate_text,
    MAX_MESSAGES_PER_BUDDY,
    RECENT_MESSAGES_TO_RETAIN,
    CONTEXT_MESSAGES_COUNT,
    MAX_SUMMARY_LENGTH,
)


def _iso(days_ago: int = 0, hours_ago: int = 0) -> str:
    """Helper to generate ISO datetime string for N days/hours ago."""
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)
    return dt.isoformat()


def _make_message(role: str, content: str, hours_ago: int = 0) -> dict:
    """Helper to create a message dict."""
    return {
        "id": f"msg-{hours_ago}",
        "user_id": "user1",
        "buddy": "finance",
        "role": role,
        "content": content,
        "created_at": _iso(hours_ago=hours_ago),
    }


def _mock_cursor(messages):
    """Create a mock async cursor that supports sort, limit, and to_list."""
    cursor = MagicMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=messages)
    return cursor


# ============ Constants Tests ============


class TestConstants:
    def test_max_messages_is_50(self):
        assert MAX_MESSAGES_PER_BUDDY == 50

    def test_recent_retain_is_20(self):
        assert RECENT_MESSAGES_TO_RETAIN == 20

    def test_context_count_is_5(self):
        assert CONTEXT_MESSAGES_COUNT == 5

    def test_max_summary_is_500(self):
        assert MAX_SUMMARY_LENGTH == 500


# ============ get_conversation_context Tests ============


class TestGetConversationContext:
    @pytest.mark.asyncio
    async def test_returns_last_5_messages_chronologically(self):
        """Req 9.2: Include last 5 messages ordered chronologically."""
        messages = [
            {"role": "assistant", "content": "Reply 3", "created_at": _iso(hours_ago=1)},
            {"role": "user", "content": "Msg 3", "created_at": _iso(hours_ago=2)},
            {"role": "assistant", "content": "Reply 2", "created_at": _iso(hours_ago=3)},
            {"role": "user", "content": "Msg 2", "created_at": _iso(hours_ago=4)},
            {"role": "user", "content": "Msg 1", "created_at": _iso(hours_ago=5)},
        ]

        db = MagicMock()
        db.chat_messages.find = MagicMock(return_value=_mock_cursor(messages))

        result = await get_conversation_context(db, "user1", "finance")

        assert len(result) == 5
        # Should be reversed to chronological order
        assert result[0]["content"] == "Msg 1"
        assert result[-1]["content"] == "Reply 3"

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_no_history(self):
        """Req 9.7: First-ever message with no prior history."""
        db = MagicMock()
        db.chat_messages.find = MagicMock(return_value=_mock_cursor([]))

        result = await get_conversation_context(db, "user1", "finance")
        assert result == []

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_db_error(self):
        """Req 9.6: Proceed without history if DB fails."""
        db = MagicMock()
        db.chat_messages.find = MagicMock(side_effect=Exception("DB connection failed"))

        result = await get_conversation_context(db, "user1", "finance")
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_fewer_than_5_if_less_exist(self):
        """When fewer than 5 messages exist, return all available."""
        messages = [
            {"role": "user", "content": "Hello", "created_at": _iso(hours_ago=2)},
            {"role": "assistant", "content": "Hi!", "created_at": _iso(hours_ago=1)},
        ]

        db = MagicMock()
        db.chat_messages.find = MagicMock(return_value=_mock_cursor(messages))

        result = await get_conversation_context(db, "user1", "finance")
        assert len(result) == 2


# ============ get_summary Tests ============


class TestGetSummary:
    @pytest.mark.asyncio
    async def test_returns_summary_when_exists(self):
        db = MagicMock()
        db.conversation_summaries.find_one = AsyncMock(
            return_value={"summary": "User discussed budget concerns."}
        )

        result = await get_summary(db, "user1", "finance")
        assert result == "User discussed budget concerns."

    @pytest.mark.asyncio
    async def test_returns_none_when_no_summary(self):
        db = MagicMock()
        db.conversation_summaries.find_one = AsyncMock(return_value=None)

        result = await get_summary(db, "user1", "finance")
        assert result is None

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_db_error(self):
        """Req 9.6: Graceful fallback."""
        db = MagicMock()
        db.conversation_summaries.find_one = AsyncMock(
            side_effect=Exception("DB timeout")
        )

        result = await get_summary(db, "user1", "finance")
        assert result is None


# ============ store_message Tests ============


class TestStoreMessage:
    @pytest.mark.asyncio
    async def test_stores_message_and_returns_id(self):
        db = MagicMock()
        db.chat_messages.insert_one = AsyncMock()
        db.chat_messages.count_documents = AsyncMock(return_value=10)

        result = await store_message(db, "user1", "finance", "user", "Hello!")
        assert result is not None
        db.chat_messages.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_triggers_trim_when_over_50(self):
        """Req 9.5: Triggers summarization when >50 messages."""
        db = MagicMock()
        db.chat_messages.insert_one = AsyncMock()
        db.chat_messages.count_documents = AsyncMock(return_value=55)

        # Mock trim_and_summarize dependencies
        messages = [_make_message("user", f"Msg {i}", hours_ago=60 - i) for i in range(55)]
        db.chat_messages.find = MagicMock(return_value=_mock_cursor(messages))
        db.conversation_summaries.update_one = AsyncMock()
        db.chat_messages.delete_many = AsyncMock()

        result = await store_message(db, "user1", "finance", "user", "New message")
        assert result is not None

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_insert_error(self):
        """Req 9.6: Returns None on failure."""
        db = MagicMock()
        db.chat_messages.insert_one = AsyncMock(side_effect=Exception("Write failed"))

        result = await store_message(db, "user1", "finance", "user", "Hello!")
        assert result is None


# ============ trim_and_summarize Tests ============


class TestTrimAndSummarize:
    @pytest.mark.asyncio
    async def test_no_trim_when_under_threshold(self):
        """No action needed when count <= 50."""
        db = MagicMock()
        db.chat_messages.count_documents = AsyncMock(return_value=30)

        result = await trim_and_summarize(db, "user1", "finance")
        assert result is True

    @pytest.mark.asyncio
    async def test_summarizes_and_deletes_older_messages(self):
        """Req 9.5: Summarize older than recent 20, retain only 20 + summary."""
        # Create 55 messages
        messages = [
            _make_message("user" if i % 2 == 0 else "assistant", f"Content {i}", hours_ago=55 - i)
            for i in range(55)
        ]

        db = MagicMock()
        db.chat_messages.count_documents = AsyncMock(return_value=55)
        db.chat_messages.find = MagicMock(return_value=_mock_cursor(messages))
        db.conversation_summaries.update_one = AsyncMock()
        db.chat_messages.delete_many = AsyncMock()

        result = await trim_and_summarize(db, "user1", "finance")

        assert result is True
        # Should upsert a summary
        db.conversation_summaries.update_one.assert_called_once()
        # Should delete older messages
        db.chat_messages.delete_many.assert_called_once()

        # Verify the delete call targets the correct messages (first 35)
        delete_call = db.chat_messages.delete_many.call_args
        filter_arg = delete_call[0][0]
        assert filter_arg["user_id"] == "user1"
        assert filter_arg["buddy"] == "finance"
        assert len(filter_arg["id"]["$in"]) == 35  # 55 - 20 = 35 messages to delete

    @pytest.mark.asyncio
    async def test_summary_stored_with_correct_schema(self):
        """Verify conversation_summaries document has correct fields."""
        messages = [
            _make_message("user", f"Topic {i}", hours_ago=60 - i)
            for i in range(55)
        ]

        db = MagicMock()
        db.chat_messages.count_documents = AsyncMock(return_value=55)
        db.chat_messages.find = MagicMock(return_value=_mock_cursor(messages))
        db.conversation_summaries.update_one = AsyncMock()
        db.chat_messages.delete_many = AsyncMock()

        await trim_and_summarize(db, "user1", "finance")

        # Check the upsert call
        update_call = db.conversation_summaries.update_one.call_args
        filter_doc = update_call[0][0]
        update_doc = update_call[0][1]["$set"]

        assert filter_doc == {"user_id": "user1", "buddy": "finance"}
        assert update_doc["user_id"] == "user1"
        assert update_doc["buddy"] == "finance"
        assert "summary" in update_doc
        assert len(update_doc["summary"]) <= MAX_SUMMARY_LENGTH
        assert "updated_at" in update_doc

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_error(self):
        """Req 9.6: Returns False on failure."""
        db = MagicMock()
        db.chat_messages.count_documents = AsyncMock(side_effect=Exception("DB error"))

        result = await trim_and_summarize(db, "user1", "finance")
        assert result is False


# ============ _generate_summary Tests ============


class TestGenerateSummary:
    def test_summary_within_500_chars(self):
        """Req 9.5: Summary must be ≤500 characters."""
        messages = [
            {"role": "user", "content": f"Long message about topic number {i} " * 10}
            for i in range(40)
        ]

        summary = _generate_summary(messages)
        assert len(summary) <= MAX_SUMMARY_LENGTH

    def test_summary_captures_user_topics(self):
        """Summary should reference user-discussed topics."""
        messages = [
            {"role": "user", "content": "How do I save money on food?"},
            {"role": "assistant", "content": "Here are some tips for saving on food costs."},
            {"role": "user", "content": "What about my rent budget?"},
            {"role": "assistant", "content": "Let's look at your rent allocation."},
        ]

        summary = _generate_summary(messages)
        assert "User discussed" in summary
        assert len(summary) > 0

    def test_empty_messages_returns_empty(self):
        """Empty message list produces empty summary."""
        summary = _generate_summary([])
        assert summary == ""

    def test_only_assistant_messages(self):
        """Handle case with only assistant messages."""
        messages = [
            {"role": "assistant", "content": "I can help with budgeting."},
            {"role": "assistant", "content": "Let me check your spending."},
        ]

        summary = _generate_summary(messages)
        assert "Buddy covered" in summary


# ============ _select_representative_indices Tests ============


class TestSelectRepresentativeIndices:
    def test_returns_all_when_total_less_than_max(self):
        result = _select_representative_indices(3, 5)
        assert result == [0, 1, 2]

    def test_returns_exact_when_total_equals_max(self):
        result = _select_representative_indices(5, 5)
        assert result == [0, 1, 2, 3, 4]

    def test_selects_evenly_spaced(self):
        result = _select_representative_indices(10, 5)
        assert len(result) == 5
        assert result[0] == 0  # First element always included


# ============ _truncate_text Tests ============


class TestTruncateText:
    def test_short_text_unchanged(self):
        assert _truncate_text("hello", 10) == "hello"

    def test_long_text_truncated_with_ellipsis(self):
        result = _truncate_text("a long piece of text here", 10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_exact_length_unchanged(self):
        assert _truncate_text("hello", 5) == "hello"


# ============ get_full_context_for_chat Tests ============


class TestGetFullContextForChat:
    @pytest.mark.asyncio
    async def test_assembles_history_and_summary(self):
        """Should return both history and summary."""
        messages = [
            {"role": "user", "content": "Hello", "created_at": _iso(hours_ago=2)},
            {"role": "assistant", "content": "Hi!", "created_at": _iso(hours_ago=1)},
        ]

        db = MagicMock()
        db.chat_messages.find = MagicMock(return_value=_mock_cursor(messages))
        db.conversation_summaries.find_one = AsyncMock(
            return_value={"summary": "Prior conversation about budgets."}
        )

        result = await get_full_context_for_chat(db, "user1", "finance")

        assert result["has_history"] is True
        assert len(result["history"]) == 2
        assert result["summary"] == "Prior conversation about budgets."

    @pytest.mark.asyncio
    async def test_no_history_returns_empty(self):
        """Req 9.7: First-ever message returns no context."""
        db = MagicMock()
        db.chat_messages.find = MagicMock(return_value=_mock_cursor([]))
        db.conversation_summaries.find_one = AsyncMock(return_value=None)

        result = await get_full_context_for_chat(db, "user1", "finance")

        assert result["has_history"] is False
        assert result["history"] == []
        assert result["summary"] is None

    @pytest.mark.asyncio
    async def test_graceful_fallback_on_error(self):
        """Req 9.6: Returns empty context on failure."""
        db = MagicMock()
        db.chat_messages.find = MagicMock(side_effect=Exception("Connection lost"))

        result = await get_full_context_for_chat(db, "user1", "finance")

        assert result["has_history"] is False
        assert result["history"] == []
        assert result["summary"] is None
