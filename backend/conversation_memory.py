"""
Conversation Memory Service for PocketBuddy AI Enhancement.

Manages conversation history persistence, context loading for new sessions,
and summarization when message count exceeds thresholds.

Requirements: 9.1, 9.2, 9.5, 9.6, 9.7
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Configuration constants
MAX_MESSAGES_PER_BUDDY = 50
RECENT_MESSAGES_TO_RETAIN = 20
CONTEXT_MESSAGES_COUNT = 5
MAX_SUMMARY_LENGTH = 500


async def store_message(
    db, user_id: str, buddy: str, role: str, content: str
) -> Optional[str]:
    """
    Store a chat message and trigger trim/summarize if history exceeds threshold.

    Args:
        db: Motor database instance
        user_id: The authenticated user's ID
        buddy: Buddy identifier (finance/wellness/discover/helper)
        role: Message role (user/assistant)
        content: Message content text

    Returns:
        The message ID if stored successfully, None on failure.
    """
    try:
        import uuid

        message = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "buddy": buddy,
            "role": role,
            "content": content,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.chat_messages.insert_one(message)

        # Check if trim/summarize is needed
        count = await db.chat_messages.count_documents(
            {"user_id": user_id, "buddy": buddy}
        )
        if count > MAX_MESSAGES_PER_BUDDY:
            await trim_and_summarize(db, user_id, buddy)

        return message["id"]
    except Exception as e:
        logger.warning(f"Failed to store message for {user_id}/{buddy}: {e}")
        return None


async def get_conversation_context(
    db, user_id: str, buddy: str
) -> List[Dict[str, Any]]:
    """
    Retrieve the last 5 messages for context when a user sends a message in a new session.

    Returns messages ordered chronologically (oldest first) so the AI model
    sees the conversation flow naturally.

    Graceful fallback: returns empty list if DB retrieval fails.

    Args:
        db: Motor database instance
        user_id: The authenticated user's ID
        buddy: Buddy identifier (finance/wellness/discover/helper)

    Returns:
        List of up to 5 most recent messages ordered chronologically, or empty list on failure.
    """
    try:
        # Fetch last 5 messages sorted by created_at descending, then reverse for chronological order
        cursor = db.chat_messages.find(
            {"user_id": user_id, "buddy": buddy},
            {"_id": 0, "role": 1, "content": 1, "created_at": 1},
        ).sort("created_at", -1).limit(CONTEXT_MESSAGES_COUNT)

        messages = await cursor.to_list(CONTEXT_MESSAGES_COUNT)
        # Reverse to get chronological order (oldest first)
        messages.reverse()
        return messages
    except Exception as e:
        logger.warning(
            f"Failed to retrieve conversation context for {user_id}/{buddy}: {e}"
        )
        return []


async def get_summary(db, user_id: str, buddy: str) -> Optional[str]:
    """
    Retrieve the existing conversation summary for a user/buddy pair.

    Graceful fallback: returns None if DB retrieval fails.

    Args:
        db: Motor database instance
        user_id: The authenticated user's ID
        buddy: Buddy identifier (finance/wellness/discover/helper)

    Returns:
        The summary string if it exists, or None.
    """
    try:
        doc = await db.conversation_summaries.find_one(
            {"user_id": user_id, "buddy": buddy},
            {"_id": 0, "summary": 1},
        )
        if doc:
            return doc.get("summary")
        return None
    except Exception as e:
        logger.warning(
            f"Failed to retrieve conversation summary for {user_id}/{buddy}: {e}"
        )
        return None


async def trim_and_summarize(db, user_id: str, buddy: str) -> bool:
    """
    When message count exceeds 50, summarize messages older than the most recent 20
    into a ≤500 character summary, then delete those older messages.

    The summary is stored/updated in the `conversation_summaries` collection.

    Args:
        db: Motor database instance
        user_id: The authenticated user's ID
        buddy: Buddy identifier (finance/wellness/discover/helper)

    Returns:
        True if summarization completed successfully, False on failure.
    """
    try:
        # Count total messages for this user/buddy
        total_count = await db.chat_messages.count_documents(
            {"user_id": user_id, "buddy": buddy}
        )

        if total_count <= MAX_MESSAGES_PER_BUDDY:
            return True  # No trimming needed

        # Get all messages sorted chronologically
        all_messages = await db.chat_messages.find(
            {"user_id": user_id, "buddy": buddy},
            {"_id": 0, "id": 1, "role": 1, "content": 1, "created_at": 1},
        ).sort("created_at", 1).to_list(total_count)

        # Separate into messages to summarize and messages to retain
        messages_to_retain = all_messages[-RECENT_MESSAGES_TO_RETAIN:]
        messages_to_summarize = all_messages[:-RECENT_MESSAGES_TO_RETAIN]

        if not messages_to_summarize:
            return True  # Nothing to summarize

        # Generate summary from older messages
        summary = _generate_summary(messages_to_summarize)

        # Store or update the summary in conversation_summaries collection
        await db.conversation_summaries.update_one(
            {"user_id": user_id, "buddy": buddy},
            {
                "$set": {
                    "user_id": user_id,
                    "buddy": buddy,
                    "summary": summary,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            },
            upsert=True,
        )

        # Delete the older messages that have been summarized
        ids_to_delete = [msg["id"] for msg in messages_to_summarize]
        await db.chat_messages.delete_many(
            {"user_id": user_id, "buddy": buddy, "id": {"$in": ids_to_delete}}
        )

        return True
    except Exception as e:
        logger.warning(
            f"Failed to trim and summarize for {user_id}/{buddy}: {e}"
        )
        return False


def _generate_summary(messages: List[Dict[str, Any]]) -> str:
    """
    Generate a concise summary (≤500 chars) from a list of messages.

    This uses a simple extractive approach: takes key topics from user messages
    and condenses them into a brief narrative. For production, this could be
    replaced with an LLM-based summarization call.

    Args:
        messages: List of message dicts with role and content fields.

    Returns:
        A summary string of at most 500 characters.
    """
    # Collect user messages for topic extraction (they represent the user's concerns)
    user_contents = []
    assistant_topics = []

    for msg in messages:
        if msg.get("role") == "user":
            user_contents.append(msg.get("content", ""))
        elif msg.get("role") == "assistant":
            # Take first sentence of assistant replies as topic indicators
            content = msg.get("content", "")
            first_sentence = content.split(".")[0] if content else ""
            if first_sentence:
                assistant_topics.append(first_sentence.strip())

    # Build summary from user queries and assistant topic indicators
    summary_parts = []

    if user_contents:
        # Take key user messages (first, middle, last for coverage)
        key_indices = _select_representative_indices(len(user_contents), max_count=5)
        user_highlights = [user_contents[i] for i in key_indices]
        topics = "; ".join(
            _truncate_text(t, 60) for t in user_highlights
        )
        summary_parts.append(f"User discussed: {topics}")

    if assistant_topics:
        # Take a few assistant topic indicators
        key_indices = _select_representative_indices(len(assistant_topics), max_count=3)
        asst_highlights = [assistant_topics[i] for i in key_indices]
        topics = "; ".join(
            _truncate_text(t, 50) for t in asst_highlights
        )
        summary_parts.append(f"Buddy covered: {topics}")

    summary = ". ".join(summary_parts)

    # Enforce max length
    if len(summary) > MAX_SUMMARY_LENGTH:
        summary = summary[: MAX_SUMMARY_LENGTH - 3] + "..."

    return summary


def _select_representative_indices(total: int, max_count: int) -> List[int]:
    """Select evenly spaced indices to represent a range."""
    if total <= max_count:
        return list(range(total))
    step = total / max_count
    return [int(i * step) for i in range(max_count)]


def _truncate_text(text: str, max_len: int) -> str:
    """Truncate text to max_len characters, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


async def get_full_context_for_chat(
    db, user_id: str, buddy: str
) -> Dict[str, Any]:
    """
    High-level function that assembles full conversation context for a chat request.

    Returns a dict with:
        - "history": list of last 5 messages (chronological) for context injection
        - "summary": existing conversation summary (or None)
        - "has_history": whether any prior conversation exists

    Graceful fallback: returns empty context if anything fails.

    Args:
        db: Motor database instance
        user_id: The authenticated user's ID
        buddy: Buddy identifier (finance/wellness/discover/helper)

    Returns:
        Dict with history, summary, and has_history fields.
    """
    try:
        history = await get_conversation_context(db, user_id, buddy)
        summary = await get_summary(db, user_id, buddy)

        return {
            "history": history,
            "summary": summary,
            "has_history": len(history) > 0 or summary is not None,
        }
    except Exception as e:
        logger.warning(
            f"Failed to assemble full context for {user_id}/{buddy}: {e}"
        )
        return {
            "history": [],
            "summary": None,
            "has_history": False,
        }
