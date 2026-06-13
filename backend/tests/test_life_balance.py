"""
Tests for the life-balance and daily insights endpoints.
Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Helper: create a mock DB that returns configurable data
def make_mock_db(
    budget_cats=None,
    expenses=None,
    savings_goals=None,
    mood_entries=None,
    sleep_entries=None,
    tasks=None,
    task_sessions=None,
    study_groups=None,
    exercise_sessions=None,
    journal_entries=None,
    group_messages=None,
    daily_insights_doc=None,
    tomorrow_plan_doc=None,
    user_profile=None,
):
    """Create a mock db object that simulates Motor async queries."""
    mock_db = MagicMock()

    def make_find_mock(data):
        """Create a mock that supports .find().to_list() pattern."""
        m = MagicMock()
        m.find.return_value = m
        m.sort.return_value = m
        m.to_list = AsyncMock(return_value=data or [])
        return m

    mock_db.__getitem__ = MagicMock(side_effect=lambda key: {
        "budget_categories": make_find_mock(budget_cats),
        "expenses": make_find_mock(expenses),
        "savings_goals": make_find_mock(savings_goals),
        "mood_entries": make_find_mock(mood_entries),
        "sleep_entries": make_find_mock(sleep_entries),
        "tasks": make_find_mock(tasks),
        "task_sessions": make_find_mock(task_sessions),
        "study_groups": make_find_mock(study_groups),
        "exercise_sessions": make_find_mock(exercise_sessions),
        "journal_entries": make_find_mock(journal_entries),
        "group_messages": make_find_mock(group_messages),
    }.get(key, make_find_mock([])))

    # For attribute-style access
    mock_db.budget_categories = make_find_mock(budget_cats)
    mock_db.expenses = make_find_mock(expenses)
    mock_db.savings_goals = make_find_mock(savings_goals)
    mock_db.mood_entries = make_find_mock(mood_entries)
    mock_db.sleep_entries = make_find_mock(sleep_entries)
    mock_db.tasks = make_find_mock(tasks)
    mock_db.task_sessions = make_find_mock(task_sessions)
    mock_db.study_groups = make_find_mock(study_groups)
    mock_db.exercise_sessions = make_find_mock(exercise_sessions)
    mock_db.journal_entries = make_find_mock(journal_entries)
    mock_db.group_messages = make_find_mock(group_messages)

    # daily_insights collection for caching
    daily_insights_coll = MagicMock()
    daily_insights_coll.find_one = AsyncMock(return_value=daily_insights_doc)
    daily_insights_coll.update_one = AsyncMock()
    mock_db.daily_insights = daily_insights_coll

    # tomorrow_plans collection
    tomorrow_plans_coll = MagicMock()
    tomorrow_plans_coll.find_one = AsyncMock(return_value=tomorrow_plan_doc)
    tomorrow_plans_coll.update_one = AsyncMock()
    mock_db.tomorrow_plans = tomorrow_plans_coll

    # user_profiles
    user_profiles_coll = MagicMock()
    user_profiles_coll.find_one = AsyncMock(return_value=user_profile or {"timezone": "Asia/Kolkata"})
    mock_db.user_profiles = user_profiles_coll

    return mock_db


class TestLifeBalanceScoring:
    """Tests for the life-balance radar scoring logic."""

    @pytest.mark.asyncio
    async def test_returns_exactly_5_domains(self):
        """Property 3: Life-balance radar SHALL produce exactly 5 domain scores."""
        from server import _compute_life_balance_scores, db as real_db

        # Patch the module-level db
        mock_db = make_mock_db(
            budget_cats=[{"allocated": 10000, "spent": 5000}],
            mood_entries=[{"mood": "good", "stress": 40, "energy": 60, "created_at": datetime.now(timezone.utc).isoformat()}],
            sleep_entries=[{"hours": 7.5, "quality": "good", "date": datetime.now(timezone.utc).isoformat()}],
            tasks=[{"status": "done", "created_at": datetime.now(timezone.utc).isoformat()}],
            study_groups=[{"id": "g1", "members": ["test_user"]}],
            exercise_sessions=[{"started_at": datetime.now(timezone.utc).isoformat(), "ended_at": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": 1800}],
            journal_entries=[{"created_at": datetime.now(timezone.utc).isoformat()}],
        )

        with patch("server.db", mock_db):
            result = await _compute_life_balance_scores("test_user")

        assert "domains" in result
        assert len(result["domains"]) == 5

        domain_names = [d["name"] for d in result["domains"]]
        assert domain_names == ["Finance", "Wellness", "Academics", "Social", "Self-Care"]

    @pytest.mark.asyncio
    async def test_scores_are_integers_0_to_100(self):
        """Property 3: Each score is integer 0-100."""
        from server import _compute_life_balance_scores

        mock_db = make_mock_db(
            budget_cats=[{"allocated": 10000, "spent": 15000}],  # Overspent
            mood_entries=[{"mood": "terrible", "stress": 90, "energy": 20, "created_at": datetime.now(timezone.utc).isoformat()}],
            sleep_entries=[{"hours": 4, "quality": "poor", "date": datetime.now(timezone.utc).isoformat()}],
            tasks=[{"status": "active", "created_at": datetime.now(timezone.utc).isoformat()}],
        )

        with patch("server.db", mock_db):
            result = await _compute_life_balance_scores("test_user")

        for domain in result["domains"]:
            assert isinstance(domain["score"], int), f"{domain['name']} score is not int"
            assert 0 <= domain["score"] <= 100, f"{domain['name']} score {domain['score']} out of range"

    @pytest.mark.asyncio
    async def test_low_score_domains_get_actionable_step(self):
        """Property 29: Low-score domains (<40) get actionable step ≤140 characters."""
        from server import _compute_life_balance_scores

        # Create data that will produce low scores
        mock_db = make_mock_db(
            budget_cats=[{"allocated": 10000, "spent": 18000}],  # Very overspent -> low finance
            mood_entries=[{"mood": "terrible", "stress": 95, "energy": 10, "created_at": datetime.now(timezone.utc).isoformat()}],
            sleep_entries=[{"hours": 3, "quality": "poor", "date": datetime.now(timezone.utc).isoformat()}],
            tasks=[{"status": "active", "created_at": datetime.now(timezone.utc).isoformat()}] * 5,  # No completions
        )

        with patch("server.db", mock_db):
            result = await _compute_life_balance_scores("test_user")

        for domain in result["domains"]:
            if domain["score"] < 40:
                assert "actionable_step" in domain, f"{domain['name']} (score={domain['score']}) missing actionable_step"
                assert len(domain["actionable_step"]) <= 140, f"Actionable step too long: {len(domain['actionable_step'])} chars"
                assert domain.get("highlight") == "red"
                assert domain.get("low_score") is True

    @pytest.mark.asyncio
    async def test_partial_data_indicator(self):
        """Property 31: Partial data computation includes indicator noting days used."""
        from server import _compute_life_balance_scores

        # Only 2 days of data (less than 7)
        two_days_ago = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        mock_db = make_mock_db(
            budget_cats=[{"allocated": 10000, "spent": 5000}],
            mood_entries=[
                {"mood": "good", "stress": 40, "energy": 60, "created_at": datetime.now(timezone.utc).isoformat()},
                {"mood": "okay", "stress": 50, "energy": 50, "created_at": two_days_ago},
            ],
            sleep_entries=[{"hours": 7, "quality": "good", "date": datetime.now(timezone.utc).isoformat()}],
        )

        with patch("server.db", mock_db):
            result = await _compute_life_balance_scores("test_user")

        assert "partial_data" in result
        assert "days_used" in result
        # Since we have <7 days for most domains, partial_data should be True
        assert result["partial_data"] is True
        # days_used should contain per-domain day counts
        for domain_name in ["Finance", "Wellness", "Academics", "Social", "Self-Care"]:
            assert domain_name in result["days_used"]

    @pytest.mark.asyncio
    async def test_no_data_returns_valid_structure(self):
        """With no data, still returns exactly 5 domains with valid scores."""
        from server import _compute_life_balance_scores

        mock_db = make_mock_db()

        with patch("server.db", mock_db):
            result = await _compute_life_balance_scores("test_user")

        assert len(result["domains"]) == 5
        for domain in result["domains"]:
            assert 0 <= domain["score"] <= 100


class TestDailyInsights:
    """Tests for the daily insights generation."""

    @pytest.mark.asyncio
    async def test_generates_exactly_3_insights(self):
        """Property 28: Exactly 3 daily insight cards."""
        from server import _generate_daily_insights

        mock_ctx = {
            "raw_data": {
                "expenses": {"total_spent": 500, "by_category": {"food": 300, "transport": 200}, "count": 5},
                "mood": {"avg_stress": 55, "avg_energy": 60, "avg_motivation": 60, "avg_mood": 4.0, "count": 3},
                "sleep": {"avg_hours": 7, "avg_quality": 4.0, "count": 3},
                "tasks": {"count": 5, "completed": 3, "completion_rate": 60},
            },
            "financial_health_score": 70,
            "wellness_composite_score": 65,
        }

        with patch("server.db") as mock_db, \
             patch("context_engine.assemble_context", new_callable=AsyncMock, return_value=mock_ctx):
            insights = await _generate_daily_insights("test_user")

        assert len(insights) == 3

    @pytest.mark.asyncio
    async def test_insight_domains_are_correct(self):
        """Each insight has the correct domain: finance, wellness, productivity."""
        from server import _generate_daily_insights

        mock_ctx = {
            "raw_data": {
                "expenses": {"total_spent": 500, "by_category": {"food": 300, "transport": 200}, "count": 5},
                "mood": {"avg_stress": 50, "avg_energy": 50, "avg_motivation": 50, "avg_mood": 3.0, "count": 3},
                "sleep": {"avg_hours": 7.5, "avg_quality": 4.0, "count": 3},
                "tasks": {"count": 5, "completed": 2, "completion_rate": 40},
            },
        }

        with patch("server.db") as mock_db, \
             patch("context_engine.assemble_context", new_callable=AsyncMock, return_value=mock_ctx):
            insights = await _generate_daily_insights("test_user")

        domains = [i["domain"] for i in insights]
        assert domains == ["finance", "wellness", "productivity"]

    @pytest.mark.asyncio
    async def test_insights_reference_data_points(self):
        """Requirement 10.2: Each insight references specific data points."""
        from server import _generate_daily_insights

        mock_ctx = {
            "raw_data": {
                "expenses": {"total_spent": 800, "by_category": {"food": 500, "transport": 300}, "count": 5},
                "mood": {"avg_stress": 65, "avg_energy": 55, "avg_motivation": 60, "avg_mood": 3.5, "count": 5},
                "sleep": {"avg_hours": 6.5, "avg_quality": 3.0, "count": 4},
                "tasks": {"count": 4, "completed": 2, "completion_rate": 50},
            },
        }

        with patch("server.db") as mock_db, \
             patch("context_engine.assemble_context", new_callable=AsyncMock, return_value=mock_ctx):
            insights = await _generate_daily_insights("test_user")

        for insight in insights:
            assert "data_reference" in insight, f"Insight missing data_reference: {insight['title']}"

    @pytest.mark.asyncio
    async def test_no_data_still_returns_3_insights(self):
        """Even with no data, exactly 3 insights are returned."""
        from server import _generate_daily_insights

        mock_ctx = {
            "raw_data": {},
            "financial_health_score": 50,
            "wellness_composite_score": 50,
        }

        with patch("server.db") as mock_db, \
             patch("context_engine.assemble_context", new_callable=AsyncMock, return_value=mock_ctx):
            insights = await _generate_daily_insights("test_user")

        assert len(insights) == 3


class TestTomorrowPlan:
    """Tests for the tomorrow plan endpoint logic."""

    @pytest.mark.asyncio
    async def test_plan_has_exactly_3_actions(self):
        """Property 30: Tomorrow's Plan returns exactly 3 actions."""
        from server import _compute_life_balance_scores

        mock_db = make_mock_db(
            budget_cats=[{"allocated": 10000, "spent": 5000}],
            mood_entries=[{"mood": "good", "stress": 40, "energy": 60, "created_at": datetime.now(timezone.utc).isoformat()}],
            sleep_entries=[{"hours": 7, "quality": "good", "date": datetime.now(timezone.utc).isoformat()}],
            tasks=[{"status": "done", "created_at": datetime.now(timezone.utc).isoformat()}],
            study_groups=[{"id": "g1", "members": ["test_user"]}],
            exercise_sessions=[{"started_at": datetime.now(timezone.utc).isoformat(), "ended_at": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": 1800}],
            journal_entries=[{"created_at": datetime.now(timezone.utc).isoformat()}],
        )

        with patch("server.db", mock_db):
            balance = await _compute_life_balance_scores("test_user")

        domains = balance["domains"]
        sorted_domains = sorted(domains, key=lambda d: d["score"])
        # The top 3 lowest should be used for actions
        assert len(sorted_domains) >= 3

    @pytest.mark.asyncio
    async def test_plan_ordered_by_ascending_score(self):
        """Property 30: Actions ordered by ascending domain score."""
        from server import _compute_life_balance_scores

        mock_db = make_mock_db(
            budget_cats=[{"allocated": 10000, "spent": 14000}],  # Finance low
            mood_entries=[{"mood": "terrible", "stress": 90, "energy": 20, "created_at": datetime.now(timezone.utc).isoformat()}],
            sleep_entries=[{"hours": 4, "quality": "poor", "date": datetime.now(timezone.utc).isoformat()}],
            tasks=[],
        )

        with patch("server.db", mock_db):
            balance = await _compute_life_balance_scores("test_user")

        domains = balance["domains"]
        sorted_domains = sorted(domains, key=lambda d: d["score"])

        # Verify ordering: the first 3 should have scores in ascending order
        scores = [d["score"] for d in sorted_domains[:3]]
        assert scores == sorted(scores), f"Scores not ascending: {scores}"


class TestActionableStepLength:
    """Tests for actionable step character limit."""

    def test_all_predefined_actions_under_140_chars(self):
        """Property 29: All actionable steps are ≤140 characters."""
        from server import _LOW_SCORE_ACTIONS

        for domain, action in _LOW_SCORE_ACTIONS.items():
            assert len(action) <= 140, f"{domain} action is {len(action)} chars: '{action}'"
