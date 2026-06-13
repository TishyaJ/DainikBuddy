"""
Unit tests for the context engine service.

Tests cover:
- Financial health score computation
- Wellness composite score computation
- Habit consistency percentage
- Active stressors identification
- Graceful degradation (domain failures)
- Data sufficiency guard (<3 days)
- Full context assembly
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from context_engine import (
    assemble_context,
    _compute_financial_health_score,
    _compute_wellness_composite_score,
    _compute_habit_consistency,
    _identify_active_stressors,
    _count_unique_data_days,
    _compute_cross_domain_correlations,
    SLEEP_QUALITY_MAP,
    MOOD_MAP,
    MIN_DAYS_FOR_CORRELATIONS,
)


def _iso(days_ago: int = 0) -> str:
    """Helper to generate ISO datetime string for N days ago."""
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


# ============ Financial Health Score Tests ============


class TestFinancialHealthScore:
    def test_no_budget_returns_neutral(self):
        score = _compute_financial_health_score([], [])
        assert score == 50

    def test_under_budget_returns_high(self):
        budget = [{"name": "food", "allocated": 5000, "spent": 2000}]
        score = _compute_financial_health_score([], budget)
        assert score == 100  # 40% spend ratio < 70%

    def test_at_budget_returns_moderate(self):
        budget = [{"name": "food", "allocated": 5000, "spent": 5000}]
        score = _compute_financial_health_score([], budget)
        assert score == 60  # exactly at budget

    def test_over_budget_returns_low(self):
        budget = [{"name": "food", "allocated": 5000, "spent": 7500}]
        score = _compute_financial_health_score([], budget)
        assert score < 60
        assert score >= 0

    def test_heavily_over_budget(self):
        budget = [{"name": "food", "allocated": 1000, "spent": 5000}]
        score = _compute_financial_health_score([], budget)
        assert score <= 20

    def test_score_always_0_to_100(self):
        # Extreme overspend
        budget = [{"name": "food", "allocated": 100, "spent": 100000}]
        score = _compute_financial_health_score([], budget)
        assert 0 <= score <= 100

    def test_zero_allocated_returns_neutral(self):
        budget = [{"name": "food", "allocated": 0, "spent": 100}]
        score = _compute_financial_health_score([], budget)
        assert score == 50


# ============ Wellness Composite Score Tests ============


class TestWellnessCompositeScore:
    def test_no_data_returns_neutral(self):
        score = _compute_wellness_composite_score([], [])
        assert score == 50

    def test_good_mood_good_sleep(self):
        moods = [
            {"mood": "great", "stress": 20, "energy": 80},
            {"mood": "good", "stress": 25, "energy": 75},
        ]
        sleeps = [
            {"hours": 8, "quality": "good"},
            {"hours": 7.5, "quality": "good"},
        ]
        score = _compute_wellness_composite_score(moods, sleeps)
        assert score > 70

    def test_bad_mood_poor_sleep(self):
        moods = [
            {"mood": "terrible", "stress": 90, "energy": 20},
            {"mood": "bad", "stress": 85, "energy": 25},
        ]
        sleeps = [
            {"hours": 4, "quality": "poor"},
            {"hours": 3.5, "quality": "poor"},
        ]
        score = _compute_wellness_composite_score(moods, sleeps)
        assert score < 40

    def test_only_mood_data(self):
        moods = [{"mood": "okay", "stress": 50, "energy": 50}]
        score = _compute_wellness_composite_score(moods, [])
        assert 0 <= score <= 100

    def test_only_sleep_data(self):
        sleeps = [{"hours": 7, "quality": "ok"}]
        score = _compute_wellness_composite_score([], sleeps)
        assert 0 <= score <= 100

    def test_score_always_0_to_100(self):
        moods = [{"mood": "great", "stress": 0, "energy": 100}]
        sleeps = [{"hours": 10, "quality": "good"}]
        score = _compute_wellness_composite_score(moods, sleeps)
        assert 0 <= score <= 100


# ============ Habit Consistency Tests ============


class TestHabitConsistency:
    def test_no_data_returns_zero(self):
        assert _compute_habit_consistency([], [], 7) == 0

    def test_all_days_active(self):
        moods = [{"created_at": _iso(i)} for i in range(7)]
        result = _compute_habit_consistency(moods, [], 7)
        assert result == 100

    def test_partial_days(self):
        moods = [{"created_at": _iso(i)} for i in range(3)]
        result = _compute_habit_consistency(moods, [], 7)
        assert result == 42  # 3/7 * 100 = 42

    def test_combined_mood_and_sleep(self):
        # 2 unique days from moods, 2 from sleep (1 overlapping)
        moods = [{"created_at": _iso(0)}, {"created_at": _iso(1)}]
        sleeps = [{"date": _iso(1)}, {"date": _iso(2)}]
        result = _compute_habit_consistency(moods, sleeps, 7)
        assert result == 42  # 3 unique days / 7 = 42%

    def test_zero_days_range(self):
        assert _compute_habit_consistency([], [], 0) == 0


# ============ Active Stressors Tests ============


class TestActiveStressors:
    def test_no_data_no_stressors(self):
        result = _identify_active_stressors([], [], [], [], [], [])
        assert result == []

    def test_high_stress_detected(self):
        moods = [{"stress": 80, "energy": 50, "motivation": 50}] * 5
        result = _identify_active_stressors(moods, [], [], [], [], [])
        assert any("High average stress" in s for s in result)

    def test_low_sleep_detected(self):
        sleeps = [{"hours": 4, "quality": "poor"}] * 5
        result = _identify_active_stressors([], [], sleeps, [], [], [])
        assert any("Insufficient sleep" in s for s in result)

    def test_overspent_budget_detected(self):
        budget = [{"name": "food", "allocated": 2000, "spent": 4000}]
        result = _identify_active_stressors([], [], [], [], [], budget)
        assert any("Over budget" in s for s in result)

    def test_low_task_completion(self):
        tasks = [{"status": "active"}] * 10 + [{"status": "done"}] * 2
        result = _identify_active_stressors([], [], [], [], tasks, [])
        assert any("Low task completion" in s for s in result)

    def test_max_10_stressors(self):
        # Create conditions for many stressors
        moods = [{"stress": 90, "energy": 10, "motivation": 10}] * 5
        sleeps = [{"hours": 3, "quality": "poor"}] * 5
        budget = [
            {"name": f"cat{i}", "allocated": 100, "spent": 500}
            for i in range(15)
        ]
        tasks = [{"status": "active"}] * 20
        goals = [{"title": f"Goal {i}", "target": 100, "current": 5} for i in range(10)]
        
        result = _identify_active_stressors(moods, [], sleeps, goals, tasks, budget)
        assert len(result) <= 10


# ============ Data Days Count Tests ============


class TestCountUniqueDays:
    def test_no_data(self):
        assert _count_unique_data_days([], [], []) == 0

    def test_single_domain(self):
        moods = [{"created_at": _iso(0)}, {"created_at": _iso(1)}]
        assert _count_unique_data_days(moods, [], []) == 2

    def test_overlapping_domains(self):
        moods = [{"created_at": _iso(0)}]
        sleeps = [{"date": _iso(0)}]
        expenses = [{"created_at": _iso(0)}]
        assert _count_unique_data_days(moods, sleeps, expenses) == 1

    def test_multiple_entries_same_day(self):
        moods = [{"created_at": _iso(0)}, {"created_at": _iso(0)}]
        assert _count_unique_data_days(moods, [], []) == 1


# ============ Cross-Domain Correlations Tests ============


class TestCrossDomainCorrelations:
    def test_emotional_eating_detected(self):
        moods = [{"stress": 80}] * 5
        # Food is >40% of total spending
        expenses = [
            {"category": "food", "amount": 500},
            {"category": "transport", "amount": 100},
        ]
        result = _compute_cross_domain_correlations(moods, expenses, [], [], [], [])
        assert any(c["type"] == "emotional_eating" for c in result)

    def test_burnout_risk_detected(self):
        sleeps = [{"hours": 5}] * 5
        tasks = [{"status": "active"}] * 8 + [{"status": "done"}] * 2
        result = _compute_cross_domain_correlations([], [], sleeps, [], tasks, [])
        assert any(c["type"] == "burnout_risk" for c in result)

    def test_financial_stress_detected(self):
        moods = [{"stress": 70}] * 5
        budget = [{"allocated": 5000, "spent": 7000}]
        result = _compute_cross_domain_correlations(moods, [], [], [], [], budget)
        assert any(c["type"] == "financial_stress" for c in result)

    def test_no_correlations_when_data_normal(self):
        moods = [{"stress": 30}] * 5
        sleeps = [{"hours": 8}] * 5
        tasks = [{"status": "done"}] * 8
        budget = [{"allocated": 5000, "spent": 3000}]
        expenses = [{"category": "food", "amount": 100}]
        result = _compute_cross_domain_correlations(
            moods, expenses, sleeps, [], tasks, budget
        )
        assert len(result) == 0


# ============ Full Context Assembly Tests ============


class TestAssembleContext:
    @pytest.fixture
    def mock_db(self):
        """Create a mock Motor database with async cursor support."""
        db = MagicMock()

        def make_collection_mock(data):
            collection = MagicMock()
            cursor = MagicMock()
            cursor.sort = MagicMock(return_value=cursor)
            cursor.limit = MagicMock(return_value=cursor)
            cursor.to_list = AsyncMock(return_value=data)
            collection.find = MagicMock(return_value=cursor)
            return collection

        return db, make_collection_mock

    @pytest.mark.asyncio
    async def test_assembly_with_full_data(self, mock_db):
        db, make_mock = mock_db

        moods = [
            {"mood": "good", "stress": 40, "energy": 70, "motivation": 60, "created_at": _iso(i)}
            for i in range(5)
        ]
        expenses = [
            {"amount": 200, "category": "food", "created_at": _iso(i)}
            for i in range(5)
        ]
        sleeps = [
            {"hours": 7.5, "quality": "good", "date": _iso(i)}
            for i in range(5)
        ]
        goals = [
            {"title": "Save 5000", "target": 5000, "current": 3000, "status": "active", "created_at": _iso(0)}
        ]
        tasks = [
            {"title": "Study", "target_minutes": 60, "progress": 80, "status": "done", "created_at": _iso(i)}
            for i in range(3)
        ]
        budget_cats = [
            {"name": "food", "allocated": 3000, "spent": 1500}
        ]

        db.__getitem__ = MagicMock(side_effect=lambda key: {
            "mood_entries": make_mock(moods),
            "expenses": make_mock(expenses),
            "sleep_entries": make_mock(sleeps),
            "goals": make_mock(goals),
            "tasks": make_mock(tasks),
            "budget_categories": make_mock(budget_cats),
        }[key])

        result = await assemble_context(db, "test_user")

        assert result["user_id"] == "test_user"
        assert 0 <= result["financial_health_score"] <= 100
        assert 0 <= result["wellness_composite_score"] <= 100
        assert 0 <= result["habit_consistency_percentage"] <= 100
        assert len(result["active_stressors"]) <= 10
        assert result["sufficient_data"] is True
        assert result["unavailable_domains"] == []
        assert "assembled_at" in result

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_domain_failure(self, mock_db):
        db, make_mock = mock_db

        # mood_entries will raise an exception
        failing_collection = MagicMock()
        failing_cursor = MagicMock()
        failing_cursor.sort = MagicMock(return_value=failing_cursor)
        failing_cursor.limit = MagicMock(return_value=failing_cursor)
        failing_cursor.to_list = AsyncMock(side_effect=Exception("DB connection lost"))
        failing_collection.find = MagicMock(return_value=failing_cursor)

        expenses = [{"amount": 100, "category": "food", "created_at": _iso(i)} for i in range(4)]
        sleeps = [{"hours": 7, "quality": "good", "date": _iso(i)} for i in range(4)]

        db.__getitem__ = MagicMock(side_effect=lambda key: {
            "mood_entries": failing_collection,
            "expenses": make_mock(expenses),
            "sleep_entries": make_mock(sleeps),
            "goals": make_mock([]),
            "tasks": make_mock([]),
            "budget_categories": make_mock([]),
        }[key])

        result = await assemble_context(db, "test_user")

        # Should still succeed with degraded data
        assert "mood" in result["unavailable_domains"]
        assert 0 <= result["financial_health_score"] <= 100
        assert 0 <= result["wellness_composite_score"] <= 100

    @pytest.mark.asyncio
    async def test_data_sufficiency_guard(self, mock_db):
        db, make_mock = mock_db

        # Only 2 days of data - below the 3-day threshold
        moods = [{"mood": "good", "stress": 40, "energy": 70, "motivation": 60, "created_at": _iso(0)}]
        expenses = [{"amount": 100, "category": "food", "created_at": _iso(0)}]

        db.__getitem__ = MagicMock(side_effect=lambda key: {
            "mood_entries": make_mock(moods),
            "expenses": make_mock(expenses),
            "sleep_entries": make_mock([]),
            "goals": make_mock([]),
            "tasks": make_mock([]),
            "budget_categories": make_mock([]),
        }[key])

        result = await assemble_context(db, "test_user")

        assert result["sufficient_data"] is False
        assert result["correlations"] == []
        assert result["data_days"] < MIN_DAYS_FOR_CORRELATIONS

    @pytest.mark.asyncio
    async def test_empty_user_data(self, mock_db):
        db, make_mock = mock_db

        db.__getitem__ = MagicMock(side_effect=lambda key: make_mock([]))

        result = await assemble_context(db, "new_user")

        assert result["user_id"] == "new_user"
        assert result["financial_health_score"] == 50  # neutral
        assert result["wellness_composite_score"] == 50  # neutral
        assert result["habit_consistency_percentage"] == 0
        assert result["active_stressors"] == []
        assert result["sufficient_data"] is False
        assert result["correlations"] == []
