"""
Unit tests for the categorization service.
Tests the cascading categorization strategy:
  1. User-specific rules (case-insensitive exact match)
  2. Keyword-based detection
  3. Default to "misc"
Also tests rule storage, capacity limits, and overwrite behavior.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

import categorization_service
from categorization_service import (
    _keyword_detect_category,
    get_user_rule,
    categorize_expense,
    store_category_rule,
    MAX_RULES_PER_USER,
)


# ============ Keyword Detection Tests ============

class TestKeywordDetectCategory:
    def test_food_keywords(self):
        assert _keyword_detect_category("pizza place") == "food"
        assert _keyword_detect_category("Mess Express lunch") == "food"
        assert _keyword_detect_category("Coffee shop") == "food"
        assert _keyword_detect_category("Thali House") == "food"

    def test_transport_keywords(self):
        assert _keyword_detect_category("Uber ride") == "transport"
        assert _keyword_detect_category("Metro card") == "transport"
        assert _keyword_detect_category("Auto fare") == "transport"

    def test_entertainment_keywords(self):
        assert _keyword_detect_category("Netflix subscription") == "entertainment"
        assert _keyword_detect_category("Movie tickets") == "entertainment"

    def test_education_keywords(self):
        assert _keyword_detect_category("Udemy course") == "education"
        assert _keyword_detect_category("Book store") == "education"
        assert _keyword_detect_category("stationery shop") == "education"

    def test_no_match_returns_none(self):
        assert _keyword_detect_category("random merchant") is None
        assert _keyword_detect_category("") is None
        assert _keyword_detect_category("gym membership") is None

    def test_case_insensitive(self):
        assert _keyword_detect_category("PIZZA") == "food"
        assert _keyword_detect_category("UBER") == "transport"


# ============ get_user_rule Tests ============

class TestGetUserRule:
    @pytest.mark.asyncio
    async def test_returns_category_when_rule_exists(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(
            return_value={"user_id": "user1", "merchant_lower": "starbucks", "category": "food"}
        )
        result = await get_user_rule(db, "user1", "Starbucks")
        assert result == "food"
        db.user_category_rules.find_one.assert_called_once_with(
            {"user_id": "user1", "merchant_lower": "starbucks"},
            {"_id": 0}
        )

    @pytest.mark.asyncio
    async def test_returns_none_when_no_rule(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(return_value=None)
        result = await get_user_rule(db, "user1", "Unknown Shop")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_merchant(self):
        db = MagicMock()
        result = await get_user_rule(db, "user1", "")
        assert result is None
        result = await get_user_rule(db, "user1", "  ")
        assert result is None

    @pytest.mark.asyncio
    async def test_case_insensitive_lookup(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(
            return_value={"user_id": "user1", "merchant_lower": "starbucks", "category": "food"}
        )
        result = await get_user_rule(db, "user1", "STARBUCKS")
        assert result == "food"
        db.user_category_rules.find_one.assert_called_once_with(
            {"user_id": "user1", "merchant_lower": "starbucks"},
            {"_id": 0}
        )


# ============ categorize_expense Tests ============

class TestCategorizeExpense:
    @pytest.mark.asyncio
    async def test_user_rule_takes_priority(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(
            return_value={"user_id": "user1", "merchant_lower": "gym place", "category": "health"}
        )
        category, is_misc = await categorize_expense(db, "user1", "Gym Place", "workout")
        assert category == "health"
        assert is_misc is False

    @pytest.mark.asyncio
    async def test_keyword_fallback_when_no_user_rule(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(return_value=None)
        category, is_misc = await categorize_expense(db, "user1", "Pizza Hut", "lunch")
        assert category == "food"
        assert is_misc is False

    @pytest.mark.asyncio
    async def test_defaults_to_misc_when_no_match(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(return_value=None)
        category, is_misc = await categorize_expense(db, "user1", "Random Shop", "stuff")
        assert category == "misc"
        assert is_misc is True

    @pytest.mark.asyncio
    async def test_empty_merchant_uses_keyword_detection(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(return_value=None)
        category, is_misc = await categorize_expense(db, "user1", "", "uber to college")
        assert category == "transport"
        assert is_misc is False


# ============ store_category_rule Tests ============

class TestStoreCategoryRule:
    @pytest.mark.asyncio
    async def test_creates_new_rule(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(return_value=None)
        db.user_category_rules.count_documents = AsyncMock(return_value=10)
        db.user_category_rules.insert_one = AsyncMock()

        result = await store_category_rule(db, "user1", "Starbucks", "food")
        assert result == {"success": True, "action": "created"}
        db.user_category_rules.insert_one.assert_called_once()
        call_arg = db.user_category_rules.insert_one.call_args[0][0]
        assert call_arg["user_id"] == "user1"
        assert call_arg["merchant_lower"] == "starbucks"
        assert call_arg["category"] == "food"

    @pytest.mark.asyncio
    async def test_overwrites_existing_rule(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(
            return_value={"user_id": "user1", "merchant_lower": "starbucks", "category": "entertainment"}
        )
        db.user_category_rules.update_one = AsyncMock()

        result = await store_category_rule(db, "user1", "Starbucks", "food")
        assert result == {"success": True, "action": "updated"}
        db.user_category_rules.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_at_capacity(self):
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(return_value=None)
        db.user_category_rules.count_documents = AsyncMock(return_value=MAX_RULES_PER_USER)

        result = await store_category_rule(db, "user1", "New Merchant", "food")
        assert result["success"] is False
        assert "500" in result["reason"]

    @pytest.mark.asyncio
    async def test_overwrite_at_capacity_allowed(self):
        """Overwriting an existing rule should work even at capacity."""
        db = MagicMock()
        db.user_category_rules.find_one = AsyncMock(
            return_value={"user_id": "user1", "merchant_lower": "starbucks", "category": "entertainment"}
        )
        db.user_category_rules.update_one = AsyncMock()

        result = await store_category_rule(db, "user1", "Starbucks", "food")
        assert result == {"success": True, "action": "updated"}

    @pytest.mark.asyncio
    async def test_rejects_empty_merchant(self):
        db = MagicMock()
        result = await store_category_rule(db, "user1", "", "food")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_rejects_empty_category(self):
        db = MagicMock()
        result = await store_category_rule(db, "user1", "Starbucks", "")
        assert result["success"] is False
