"""
AI Insights Service for PocketBuddy.

Provides shared utilities and service classes for generating AI-powered,
data-grounded insights across Weekly Review, Daily Insights, and
Helper Buddy Command Center.

Requirements: 9.4, 9.5, 11.1, 11.2, 11.3, 11.4
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

logger = logging.getLogger(__name__)


# =============================================================================
# Shared Utilities
# =============================================================================


async def _call_llm_with_timeout(
    system_prompt: str,
    user_prompt: str,
    timeout_seconds: float,
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> Optional[str]:
    """
    Call LLM with timeout enforcement. Returns response text or None on failure/timeout.

    Uses asyncio.wait_for to enforce timeout on the LLM streaming collection.
    Strips markdown code blocks from the response if present.

    Requirements: 11.1, 11.2, 11.3, 11.4
    """
    try:
        async def _do_llm():
            api_key = os.getenv("GROQ_API_KEY", "")
            if not api_key:
                logger.warning("GROQ_API_KEY not configured, skipping LLM call")
                return None

            llm = LlmChat(
                api_key=api_key,
                session_id="insights",
                system_message=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                cache_enabled=True,
            ).with_model("groq", "llama-3.3-70b-versatile")

            full_text = ""
            async for event in llm.stream_message(UserMessage(text=user_prompt)):
                if isinstance(event, TextDelta):
                    full_text += event.content
                elif isinstance(event, StreamDone):
                    break

            # Strip markdown code blocks if present
            full_text = full_text.strip()
            if full_text.startswith("```"):
                lines = full_text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                full_text = "\n".join(lines)

            return full_text if full_text else None

        return await asyncio.wait_for(_do_llm(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(
            f"LLM call timed out after {timeout_seconds}s"
        )
        return None
    except Exception as e:
        logger.warning(f"LLM call failed: {e}")
        return None


def _validate_grounding(text: str, context: dict) -> bool:
    """
    Validate that generated text contains at least one numeric value
    that exists in the provided context data.

    Extracts numbers from:
    - context["raw_data"] (all numeric values at any nesting level)
    - context scores (financial_health_score, wellness_composite_score,
      habit_consistency_percentage)
    - context["active_stressors"] descriptions (embedded numbers)

    Returns True if at least one context number appears in the text.

    Requirements: 9.4, 9.5
    """
    if not text or not context:
        return False

    # Collect all numeric values from context
    context_numbers: set[str] = set()

    # Extract from scores
    for key in ("financial_health_score", "wellness_composite_score",
                "habit_consistency_percentage"):
        value = context.get(key)
        if value is not None:
            context_numbers.add(str(int(value)) if isinstance(value, (int, float)) else str(value))

    # Extract numbers from raw_data (recursive)
    raw_data = context.get("raw_data", {})
    _extract_numbers_from_dict(raw_data, context_numbers)

    # Extract numbers from active_stressors descriptions
    stressors = context.get("active_stressors", [])
    for stressor in stressors:
        if isinstance(stressor, str):
            nums = re.findall(r'\d+\.?\d*', stressor)
            context_numbers.update(nums)

    # Check if text contains at least one of these numbers
    if not context_numbers:
        return False

    for num_str in context_numbers:
        if num_str in text:
            return True

    return False


def _extract_numbers_from_dict(data: dict, numbers: set) -> None:
    """Recursively extract all numeric values from a nested dict/list structure."""
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, (int, float)):
                # Add both int and float representations
                numbers.add(str(value))
                if isinstance(value, float):
                    # Also add integer representation if it's a whole number
                    if value == int(value):
                        numbers.add(str(int(value)))
                else:
                    # For ints, also add float representation
                    numbers.add(str(float(value)))
            elif isinstance(value, dict):
                _extract_numbers_from_dict(value, numbers)
            elif isinstance(value, list):
                _extract_numbers_from_list(value, numbers)
    elif isinstance(data, list):
        _extract_numbers_from_list(data, numbers)


def _extract_numbers_from_list(data: list, numbers: set) -> None:
    """Recursively extract all numeric values from a list structure."""
    for item in data:
        if isinstance(item, (int, float)):
            numbers.add(str(item))
            if isinstance(item, float) and item == int(item):
                numbers.add(str(int(item)))
            elif isinstance(item, int):
                numbers.add(str(float(item)))
        elif isinstance(item, dict):
            _extract_numbers_from_dict(item, numbers)
        elif isinstance(item, list):
            _extract_numbers_from_list(item, numbers)


def _get_iso_week(dt: Optional[datetime] = None) -> str:
    """
    Return ISO week string like '2026-W24' for cache keying.

    If no datetime is provided, uses current UTC time.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def _now_iso() -> str:
    """Return current UTC time as ISO format string."""
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# WeeklyReviewService
# =============================================================================


class WeeklyReviewService:
    """
    Service for computing and delivering AI-powered weekly reviews.

    Computes real domain scores from assembled context, calculates
    week-over-week trends by comparing with stored previous-week scores,
    and generates LLM-powered highlights and focus recommendations.

    Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4
    """

    def __init__(self, db):
        self.db = db

    def _compute_scores(self, context: dict) -> list:
        """
        Map assembled context scores to domain scorecard entries.

        Mapping:
        - financial_health_score → "Finance"
        - wellness_composite_score → "Wellness"
        - habit_consistency_percentage → "Productivity"

        Returns a list of dicts with domain and score (or None with status
        "insufficient_data" if the domain is unavailable).

        Requirements: 1.2, 1.3, 1.4
        """
        unavailable = context.get("unavailable_domains", [])

        scores = []

        # Finance: unavailable if "expenses" OR "budget" in unavailable_domains
        if "expenses" in unavailable or "budget" in unavailable:
            scores.append({"domain": "Finance", "score": None, "status": "insufficient_data"})
        else:
            scores.append({"domain": "Finance", "score": int(context.get("financial_health_score", 0))})

        # Wellness: unavailable if "mood" AND "sleep" in unavailable_domains
        if "mood" in unavailable and "sleep" in unavailable:
            scores.append({"domain": "Wellness", "score": None, "status": "insufficient_data"})
        else:
            scores.append({"domain": "Wellness", "score": int(context.get("wellness_composite_score", 0))})

        # Productivity: unavailable if "tasks" in unavailable_domains
        if "tasks" in unavailable:
            scores.append({"domain": "Productivity", "score": None, "status": "insufficient_data"})
        else:
            scores.append({"domain": "Productivity", "score": int(context.get("habit_consistency_percentage", 0))})

        return scores

    async def _compute_trends(self, user_id: str, current_scores: list) -> dict:
        """
        Compute week-over-week trends by looking up the previous week's
        stored scores from the `weekly_scores` collection.

        Returns a dict mapping domain name to signed integer difference
        (current - previous), or None if previous data is unavailable
        or had fewer than 3 data_days.

        Requirements: 2.1, 2.2, 2.3, 2.4
        """
        from datetime import timedelta

        # Compute previous ISO week
        prev_week_dt = datetime.now(timezone.utc) - timedelta(weeks=1)
        prev_iso_week = _get_iso_week(prev_week_dt)

        # Look up previous week's stored scores
        prev_record = await self.db["weekly_scores"].find_one(
            {"user_id": user_id, "iso_week": prev_iso_week}
        )

        # If no previous record or insufficient data_days, return null trends
        if prev_record is None or prev_record.get("data_days", 0) < 3:
            return {
                "Finance": None,
                "Wellness": None,
                "Productivity": None,
            }

        # Map stored field names to domain names
        prev_scores_map = {
            "Finance": prev_record.get("finance_score"),
            "Wellness": prev_record.get("wellness_score"),
            "Productivity": prev_record.get("productivity_score"),
        }

        # Compute signed differences for each domain
        trends = {}
        for score_entry in current_scores:
            domain = score_entry["domain"]
            current_val = score_entry.get("score")
            prev_val = prev_scores_map.get(domain)

            if current_val is not None and prev_val is not None:
                trends[domain] = current_val - prev_val
            else:
                trends[domain] = None

        return trends

    async def _store_weekly_scores(self, user_id: str, iso_week: str, scores: list, data_days: int = 0):
        """
        Persist current week's scores into the `weekly_scores` collection
        for future trend computation.

        Upserts using user_id + iso_week as the composite key.
        Stores: finance_score, wellness_score, productivity_score, data_days, computed_at.

        Requirements: 2.1
        """
        # Build the score fields from the scores list
        score_fields = {}
        for entry in scores:
            domain = entry["domain"]
            value = entry.get("score")
            if domain == "Finance":
                score_fields["finance_score"] = value
            elif domain == "Wellness":
                score_fields["wellness_score"] = value
            elif domain == "Productivity":
                score_fields["productivity_score"] = value

        await self.db["weekly_scores"].update_one(
            {"user_id": user_id, "iso_week": iso_week},
            {
                "$set": {
                    **score_fields,
                    "data_days": data_days,
                    "computed_at": _now_iso(),
                }
            },
            upsert=True,
        )

    # -------------------------------------------------------------------------
    # LLM Highlights & Focus (Task 1.3)
    # -------------------------------------------------------------------------

    WEEKLY_HIGHLIGHTS_SYSTEM = """You are an insight generator for a student life-tracking app.
Given the user's 7-day data summary, generate exactly 3 concise highlight statements.
Each highlight MUST:
- Reference at least one specific number from the data (₹ amounts, hours, counts, percentages)
- Be ≤80 characters
- Be in third person (e.g., "Spent ₹2,100 on food this week")
- Focus on achievements or notable patterns

Return ONLY a JSON array of exactly 3 strings. No markdown, no explanation."""

    WEEKLY_HIGHLIGHTS_USER = """User data for the past 7 days:
- Finance score: {finance_score}/100
- Wellness score: {wellness_score}/100
- Productivity score: {productivity_score}/100
- Expenses: {expense_summary}
- Sleep: {sleep_summary}
- Tasks: {task_summary}
- Mood: {mood_summary}

Generate 3 highlight statements."""

    WEEKLY_FOCUS_SYSTEM = """You are a life coach for college students.
Given the user's weakest area, generate exactly 1 actionable focus recommendation for next week.
The focus MUST:
- Name the specific domain
- Reference at least one number from the data
- Be specific and measurable
- Be ≤120 characters

Return ONLY the single focus statement string. No quotes, no JSON, no explanation."""

    WEEKLY_FOCUS_USER = """Lowest-scoring domain: {focus_domain} ({focus_score}/100, trend: {focus_trend})
Data: {focus_data}
Generate one focus recommendation for next week."""

    async def _generate_highlights(self, context: dict) -> list:
        """
        Call LLM with 5s timeout for 3 concise highlights referencing specific data.
        Validates grounding before returning. Falls back to rule-based on failure.

        Requirements: 3.1, 3.2, 3.3, 3.4, 11.1
        """
        raw_data = context.get("raw_data", {})

        # Build summary strings for the prompt
        expense_data = raw_data.get("expenses", {})
        expense_summary = (
            f"₹{expense_data.get('total_spent', 0)} total across {expense_data.get('count', 0)} expenses"
            if expense_data else "No expenses logged"
        )

        sleep_data = raw_data.get("sleep", {})
        sleep_summary = (
            f"{sleep_data.get('avg_hours', 0)}h avg across {sleep_data.get('count', 0)} nights"
            if sleep_data else "No sleep data logged"
        )

        task_data = raw_data.get("tasks", {})
        task_summary = (
            f"{task_data.get('completed', 0)}/{task_data.get('count', 0)} completed ({task_data.get('completion_rate', 0)}%)"
            if task_data else "No tasks logged"
        )

        mood_data = raw_data.get("mood", {})
        mood_summary = (
            f"avg mood {mood_data.get('avg_mood', 0)}/5, stress {mood_data.get('avg_stress', 0)}%"
            if mood_data else "No mood data logged"
        )

        user_prompt = self.WEEKLY_HIGHLIGHTS_USER.format(
            finance_score=context.get("financial_health_score", 0),
            wellness_score=context.get("wellness_composite_score", 0),
            productivity_score=context.get("habit_consistency_percentage", 0),
            expense_summary=expense_summary,
            sleep_summary=sleep_summary,
            task_summary=task_summary,
            mood_summary=mood_summary,
        )

        response = await _call_llm_with_timeout(
            system_prompt=self.WEEKLY_HIGHLIGHTS_SYSTEM,
            user_prompt=user_prompt,
            timeout_seconds=5.0,
            temperature=0.7,
            max_tokens=256,
        )

        if response:
            try:
                highlights = json.loads(response)
                if (
                    isinstance(highlights, list)
                    and len(highlights) == 3
                    and all(isinstance(h, str) and len(h) <= 80 for h in highlights)
                ):
                    # Validate grounding: at least the overall response should be grounded
                    combined_text = " ".join(highlights)
                    if _validate_grounding(combined_text, context):
                        return highlights
                    else:
                        logger.warning("Highlights failed grounding validation, using fallback")
                else:
                    logger.warning("LLM highlights response had invalid structure, using fallback")
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse LLM highlights response: {e}")

        return self._fallback_highlights(context)

    def _fallback_highlights(self, context: dict) -> list:
        """
        Produce exactly 3 rule-based highlight strings ≤80 chars each
        with numeric references from raw_data.

        Requirements: 3.3
        """
        raw_data = context.get("raw_data", {})
        highlights = []

        # Finance highlight
        expense_data = raw_data.get("expenses", {})
        if expense_data and expense_data.get("count", 0) > 0:
            total = expense_data.get("total_spent", 0)
            count = expense_data.get("count", 0)
            text = f"Spent \u20b9{int(total)} across {count} expenses this week"
            highlights.append(text[:80])
        else:
            highlights.append("No expenses logged this week")

        # Wellness highlight
        sleep_data = raw_data.get("sleep", {})
        if sleep_data and sleep_data.get("count", 0) > 0:
            avg_hours = sleep_data.get("avg_hours", 0)
            count = sleep_data.get("count", 0)
            text = f"Slept {avg_hours}h avg over {count} nights"
            highlights.append(text[:80])
        else:
            highlights.append("No sleep data logged")

        # Productivity highlight
        task_data = raw_data.get("tasks", {})
        if task_data and task_data.get("count", 0) > 0:
            completed = task_data.get("completed", 0)
            total = task_data.get("count", 0)
            rate = task_data.get("completion_rate", 0)
            text = f"Completed {completed}/{total} tasks ({rate}%)"
            highlights.append(text[:80])
        else:
            highlights.append("No tasks logged")

        return highlights

    async def _generate_focus(self, scores: list, trends: dict, context: dict) -> str:
        """
        Call LLM with 5s timeout for 1 actionable focus statement ≤120 chars.
        Falls back to template-based focus on failure.

        Requirements: 4.1, 4.2, 4.3, 4.4, 11.1
        """
        # Find the domain with the lowest score (among non-null scores)
        focus_domain, focus_score, focus_trend = self._select_focus_domain(scores, trends)

        if focus_domain is None:
            return self._fallback_focus(scores, trends)

        # Gather domain-specific data for the prompt
        raw_data = context.get("raw_data", {})
        domain_key_map = {
            "Finance": "expenses",
            "Wellness": "sleep",
            "Productivity": "tasks",
        }
        domain_raw = raw_data.get(domain_key_map.get(focus_domain, ""), {})
        focus_data = json.dumps(domain_raw) if domain_raw else "No detailed data available"

        trend_str = f"{focus_trend:+d}" if focus_trend is not None else "no previous data"

        user_prompt = self.WEEKLY_FOCUS_USER.format(
            focus_domain=focus_domain,
            focus_score=focus_score,
            focus_trend=trend_str,
            focus_data=focus_data,
        )

        response = await _call_llm_with_timeout(
            system_prompt=self.WEEKLY_FOCUS_SYSTEM,
            user_prompt=user_prompt,
            timeout_seconds=5.0,
            temperature=0.7,
            max_tokens=128,
        )

        if response:
            # Clean up response - remove quotes if wrapped
            focus = response.strip().strip('"').strip("'")
            if len(focus) <= 120 and _validate_grounding(focus, context):
                return focus
            elif len(focus) <= 120:
                logger.warning("Focus failed grounding validation, using fallback")
            else:
                logger.warning("Focus exceeded 120 chars, using fallback")

        return self._fallback_focus(scores, trends)

    def _select_focus_domain(self, scores: list, trends: dict) -> tuple:
        """
        Select the domain with the lowest score. On tie, pick the one with
        the most negative trend.

        Returns (domain_name, score, trend) or (None, None, None) if no valid scores.
        """
        valid_scores = [
            (s["domain"], s["score"], trends.get(s["domain"]))
            for s in scores
            if s.get("score") is not None
        ]

        if not valid_scores:
            return (None, None, None)

        # Sort by score ascending, then by trend ascending (most negative first) for ties
        valid_scores.sort(key=lambda x: (x[1], x[2] if x[2] is not None else 0))
        return valid_scores[0]

    def _fallback_focus(self, scores: list, trends: dict) -> str:
        """
        Use lowest-scoring domain template to produce a focus statement ≤120 chars.

        Requirements: 4.3, 4.4
        """
        focus_domain, focus_score, _ = self._select_focus_domain(scores, trends)

        if focus_domain is None:
            return "Focus on logging more data to get personalized recommendations."

        text = f"Focus on {focus_domain}: your score is {focus_score}/100. Set a specific daily goal."
        return text[:120]

    # -------------------------------------------------------------------------
    # Caching (Task 1.3)
    # -------------------------------------------------------------------------

    async def _get_cached_review(self, user_id: str, iso_week: str) -> Optional[dict]:
        """
        Check weekly_insights cache by user_id + ISO week.
        Returns the cached review dict if found, else None.

        Requirements: 6.1, 6.2
        """
        try:
            cached = await self.db["weekly_insights"].find_one(
                {"user_id": user_id, "iso_week": iso_week},
                {"_id": 0},
            )
            return cached if cached else None
        except Exception as e:
            logger.warning(f"Cache read failed for user {user_id}, week {iso_week}: {e}")
            return None

    async def _cache_review(self, user_id: str, iso_week: str, review: dict):
        """
        Store completed review in weekly_insights collection.
        Upserts using user_id + iso_week as the composite key.

        Requirements: 6.1
        """
        try:
            await self.db["weekly_insights"].update_one(
                {"user_id": user_id, "iso_week": iso_week},
                {
                    "$set": {
                        **review,
                        "user_id": user_id,
                        "iso_week": iso_week,
                        "created_at": _now_iso(),
                    }
                },
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Cache write failed for user {user_id}, week {iso_week}: {e}")

    async def invalidate_cache(self, user_id: str):
        """
        Delete cached weekly review for current ISO week.
        Called when user data changes (new expense, mood entry, task completion).

        Requirements: 6.4
        """
        iso_week = _get_iso_week()
        try:
            await self.db["weekly_insights"].delete_one(
                {"user_id": user_id, "iso_week": iso_week}
            )
        except Exception as e:
            logger.warning(f"Cache invalidation failed for user {user_id}: {e}")

    # -------------------------------------------------------------------------
    # Main Entry Point (Task 1.3)
    # -------------------------------------------------------------------------

    async def get_weekly_review(self, user_id: str) -> dict:
        """
        Main entry point for the weekly review. Orchestrates:
        1. Cache check → return if hit
        2. Assemble context
        3. If data_days < 3: return insufficient response
        4. Compute scores from context
        5. Compute trends (look up previous week)
        6. Store current week's scores for future trend use
        7. Generate highlights (LLM with fallback)
        8. Generate focus (LLM with fallback)
        9. Build response with data_sufficiency field
        10. Cache the response
        11. Return

        Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.4, 10.1, 10.4, 11.1
        """
        from context_engine import assemble_context

        iso_week = _get_iso_week()

        # 1. Check cache
        cached = await self._get_cached_review(user_id, iso_week)
        if cached:
            logger.info(f"Returning cached weekly review for user {user_id}, week {iso_week}")
            return cached

        # 2. Assemble context
        try:
            context = await assemble_context(self.db, user_id)
        except Exception as e:
            logger.error(f"Context assembly failed for user {user_id}: {e}")
            return {
                "error": "Failed to assemble user context",
                "data_sufficiency": "insufficient",
                "generated_at": _now_iso(),
            }

        data_days = context.get("data_days", 0)

        # 3. If data_days < 1: return insufficient response (need at least 1 day of data)
        if data_days < 1:
            return {
                "scorecard": [],
                "highlights": [],
                "next_week_focus": "Start logging data to unlock your weekly review.",
                "data_sufficiency": "insufficient",
                "generated_at": _now_iso(),
            }

        # 4. Compute scores
        scores = self._compute_scores(context)

        # 5. Compute trends
        trends = await self._compute_trends(user_id, scores)

        # 6. Store current week's scores for future trend use
        await self._store_weekly_scores(user_id, iso_week, scores, data_days=data_days)

        # 7. Generate highlights (LLM with fallback)
        highlights = await self._generate_highlights(context)

        # 8. Generate focus (LLM with fallback)
        next_week_focus = await self._generate_focus(scores, trends, context)

        # 9. Build response with data_sufficiency field
        # Determine data_sufficiency: "full" if all domains have data, "partial" otherwise
        unavailable = context.get("unavailable_domains", [])
        if len(unavailable) == 0 and data_days >= 5:
            data_sufficiency = "full"
        elif data_days >= 3:
            data_sufficiency = "partial"
        else:
            data_sufficiency = "insufficient"

        # Build scorecard with trends
        scorecard = []
        for entry in scores:
            domain = entry["domain"]
            score_val = entry.get("score")
            trend_val = trends.get(domain)
            scorecard.append({
                "domain": domain,
                "score": score_val,
                "trend": trend_val,
            })

        review = {
            "scorecard": scorecard,
            "highlights": highlights,
            "next_week_focus": next_week_focus,
            "data_sufficiency": data_sufficiency,
            "generated_at": _now_iso(),
        }

        # 10. Cache the response
        await self._cache_review(user_id, iso_week, review)

        # 11. Return
        return review


# =============================================================================
# DailyInsightsService
# =============================================================================


class DailyInsightsService:
    """
    Service for generating AI-powered daily insight cards.

    Produces exactly 3 personalized Insight_Cards (finance, wellness, productivity)
    using LLM-enhanced text grounded in actual user data, with rule-based fallback
    and onboarding support for new users.

    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.3, 9.2, 10.2, 10.4, 11.2
    """

    DAILY_INSIGHTS_SYSTEM = """You are a personal insights generator for a college student.
Given their recent data, generate exactly 3 short insight cards (finance, wellness, productivity).

Each card must be a JSON object with:
- "domain": one of "finance", "wellness", "productivity"
- "title": 5-10 word catchy title referencing a specific number
- "detail": 1-2 sentence actionable insight referencing specific data (₹ amounts, hours, percentages)
- "icon": one of "trending-up", "trending-down", "wallet", "heart", "moon", "zap", "target", "check-circle", "smile"
- "data_reference": the raw metric value used (e.g., "₹2100 food / ₹5000 total")

Return ONLY a JSON array of exactly 3 objects. No markdown, no explanation."""

    DAILY_INSIGHTS_USER = """User data (7-day summary):
Finance: {finance_summary}
Wellness: {wellness_summary}
Productivity: {productivity_summary}
Scores: Finance {finance_score}/100, Wellness {wellness_score}/100, Productivity {productivity_score}/100

Generate 3 personalized insight cards."""

    def __init__(self, db):
        self.db = db

    async def _generate_llm_insights(self, context: dict) -> list:
        """
        Call LLM with 3s timeout for conversational title + detail per domain
        referencing specific data points (₹ amounts, percentages, hours).
        Validates grounding on each card.

        Returns a list of 3 InsightCard dicts, or an empty list if LLM fails
        or grounding validation fails.

        Requirements: 5.1, 5.2, 9.2, 11.2
        """
        raw_data = context.get("raw_data", {})

        # Build summary strings for the prompt
        expense_data = raw_data.get("expenses", {})
        if expense_data and expense_data.get("total_spent", 0) > 0:
            total_spent = expense_data.get("total_spent", 0)
            by_category = expense_data.get("by_category", {})
            top_cat = max(by_category, key=by_category.get) if by_category else "misc"
            top_amount = by_category.get(top_cat, 0) if by_category else 0
            finance_summary = (
                f"₹{int(total_spent)} total spent, top category: {top_cat} (₹{int(top_amount)}), "
                f"{expense_data.get('count', 0)} transactions"
            )
        else:
            finance_summary = "No expenses logged this week"

        mood_data = raw_data.get("mood", {})
        sleep_data = raw_data.get("sleep", {})
        wellness_parts = []
        if mood_data:
            wellness_parts.append(
                f"stress {mood_data.get('avg_stress', 50)}/100, energy {mood_data.get('avg_energy', 50)}/100"
            )
        if sleep_data:
            wellness_parts.append(f"sleep avg {sleep_data.get('avg_hours', 7)}h/night")
        wellness_summary = ", ".join(wellness_parts) if wellness_parts else "No mood/sleep data logged"

        task_data = raw_data.get("tasks", {})
        if task_data and task_data.get("count", 0) > 0:
            productivity_summary = (
                f"{task_data.get('completed', 0)}/{task_data.get('count', 0)} tasks completed "
                f"({task_data.get('completion_rate', 0)}% completion rate)"
            )
        else:
            productivity_summary = "No tasks logged this week"

        user_prompt = self.DAILY_INSIGHTS_USER.format(
            finance_summary=finance_summary,
            wellness_summary=wellness_summary,
            productivity_summary=productivity_summary,
            finance_score=context.get("financial_health_score", 0),
            wellness_score=context.get("wellness_composite_score", 0),
            productivity_score=context.get("habit_consistency_percentage", 0),
        )

        response = await _call_llm_with_timeout(
            system_prompt=self.DAILY_INSIGHTS_SYSTEM,
            user_prompt=user_prompt,
            timeout_seconds=3.0,
            temperature=0.7,
            max_tokens=512,
        )

        if not response:
            return []

        try:
            cards = json.loads(response)
            if not isinstance(cards, list) or len(cards) != 3:
                logger.warning("LLM daily insights response had invalid structure (not 3 cards)")
                return []

            # Validate each card structure and grounding
            valid_domains = {"finance", "wellness", "productivity"}
            valid_icons = {
                "trending-up", "trending-down", "wallet", "heart",
                "moon", "zap", "target", "check-circle", "smile",
            }
            validated_cards = []

            for card in cards:
                if not isinstance(card, dict):
                    logger.warning("LLM daily insight card is not a dict")
                    return []
                if card.get("domain") not in valid_domains:
                    logger.warning(f"LLM daily insight card has invalid domain: {card.get('domain')}")
                    return []
                if not card.get("title") or not card.get("detail"):
                    logger.warning("LLM daily insight card missing title or detail")
                    return []
                if card.get("icon") not in valid_icons:
                    # Default to a safe icon if invalid
                    card["icon"] = "zap"
                if not card.get("data_reference"):
                    card["data_reference"] = ""

                # Validate grounding: the card's text should reference context data
                card_text = f"{card['title']} {card['detail']} {card.get('data_reference', '')}"
                if not _validate_grounding(card_text, context):
                    logger.warning(
                        f"LLM daily insight card for {card['domain']} failed grounding validation"
                    )
                    return []

                validated_cards.append({
                    "domain": card["domain"],
                    "title": card["title"],
                    "detail": card["detail"],
                    "icon": card["icon"],
                    "data_reference": card["data_reference"],
                })

            # Ensure all 3 domains are covered
            card_domains = {c["domain"] for c in validated_cards}
            if card_domains != valid_domains:
                logger.warning("LLM daily insights don't cover all 3 domains")
                return []

            return validated_cards

        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse LLM daily insights response: {e}")
            return []

    def _fallback_insights(self, context: dict) -> list:
        """
        Preserve the existing rule-based logic from _generate_daily_insights in server.py.
        Produces exactly 3 InsightCards using if/else chains based on the data.

        Requirements: 5.5, 5.3, 5.4
        """
        raw = context.get("raw_data", {})
        insights = []

        # 1. Financial tip — always present
        expense_data = raw.get("expenses", {})
        if expense_data:
            total_spent = expense_data.get("total_spent", 0)
            by_category = expense_data.get("by_category", {})
            top_cat = max(by_category, key=by_category.get) if by_category else "misc"
            top_amount = by_category.get(top_cat, 0) if by_category else 0
            if total_spent > 0:
                pct = int(top_amount / total_spent * 100)
                insights.append({
                    "domain": "finance",
                    "title": f"{top_cat.capitalize()} spending is {pct}% of total",
                    "detail": f"You spent ₹{int(top_amount)} on {top_cat} this week ({pct}% of ₹{int(total_spent)} total). Consider a daily cap.",
                    "icon": "trending-up",
                    "data_reference": f"₹{int(top_amount)} on {top_cat} (7-day total: ₹{int(total_spent)})",
                })
            else:
                insights.append({
                    "domain": "finance",
                    "title": "No spending recorded",
                    "detail": "Start logging expenses to get personalized finance tips.",
                    "icon": "wallet",
                    "data_reference": "No expense data available",
                })
        else:
            insights.append({
                "domain": "finance",
                "title": "Track your expenses",
                "detail": "Start logging expenses to get personalized finance tips.",
                "icon": "wallet",
                "data_reference": "No expense data available",
            })

        # 2. Wellness suggestion — always present
        mood_data = raw.get("mood", {})
        sleep_data = raw.get("sleep", {})
        if mood_data or sleep_data:
            avg_stress = mood_data.get("avg_stress", 50) if mood_data else 50
            avg_energy = mood_data.get("avg_energy", 50) if mood_data else 50
            avg_sleep = sleep_data.get("avg_hours", 7) if sleep_data else 7
            if avg_stress > 60:
                insights.append({
                    "domain": "wellness",
                    "title": f"Stress at {int(avg_stress)}/100 this week",
                    "detail": f"Your 7-day stress avg is {int(avg_stress)}/100. Try a 5-min breathing exercise or short walk.",
                    "icon": "heart",
                    "data_reference": f"7-day avg stress: {int(avg_stress)}/100",
                })
            elif avg_sleep < 7:
                insights.append({
                    "domain": "wellness",
                    "title": f"Sleep averaging {avg_sleep:.1f}h/night",
                    "detail": f"You averaged {avg_sleep:.1f}h sleep this week (target: 7-8h). Try a consistent bedtime tonight.",
                    "icon": "moon",
                    "data_reference": f"7-day avg sleep: {avg_sleep:.1f}h",
                })
            elif avg_energy < 50:
                insights.append({
                    "domain": "wellness",
                    "title": f"Energy at {int(avg_energy)}/100",
                    "detail": f"Your energy averaged {int(avg_energy)}/100 this week. A short walk or stretch can boost it.",
                    "icon": "zap",
                    "data_reference": f"7-day avg energy: {int(avg_energy)}/100",
                })
            else:
                insights.append({
                    "domain": "wellness",
                    "title": "Wellness on track",
                    "detail": f"Sleep ({avg_sleep:.1f}h avg) and stress ({int(avg_stress)}/100) look healthy. Keep it up!",
                    "icon": "smile",
                    "data_reference": f"Sleep: {avg_sleep:.1f}h, Stress: {int(avg_stress)}/100",
                })
        else:
            insights.append({
                "domain": "wellness",
                "title": "Check in with your mood",
                "detail": "Log your mood and sleep daily to get wellness insights.",
                "icon": "heart",
                "data_reference": "No mood/sleep data available",
            })

        # 3. Productivity recommendation — always present
        task_data = raw.get("tasks", {})
        if task_data:
            completion_rate = task_data.get("completion_rate", 0)
            total_tasks = task_data.get("count", 0)
            completed = task_data.get("completed", 0)
            if completion_rate < 50:
                insights.append({
                    "domain": "productivity",
                    "title": f"Tasks {int(completion_rate)}% complete ({completed}/{total_tasks})",
                    "detail": f"You've completed {completed} of {total_tasks} tasks this week. Pick one priority task for today.",
                    "icon": "target",
                    "data_reference": f"Task completion: {completed}/{total_tasks} ({int(completion_rate)}%)",
                })
            elif completion_rate < 80:
                insights.append({
                    "domain": "productivity",
                    "title": f"Tasks {int(completion_rate)}% complete",
                    "detail": f"Good progress — {completed}/{total_tasks} tasks done. Focus on your top priority to finish strong.",
                    "icon": "target",
                    "data_reference": f"Task completion: {completed}/{total_tasks} ({int(completion_rate)}%)",
                })
            else:
                insights.append({
                    "domain": "productivity",
                    "title": f"Excellent: {int(completion_rate)}% tasks complete",
                    "detail": f"You completed {completed}/{total_tasks} tasks this week. Great momentum — keep it going!",
                    "icon": "check-circle",
                    "data_reference": f"Task completion: {completed}/{total_tasks} ({int(completion_rate)}%)",
                })
        else:
            insights.append({
                "domain": "productivity",
                "title": "Set your goals",
                "detail": "Add tasks to track your productivity this week.",
                "icon": "target",
                "data_reference": "No task data available",
            })

        return insights

    def _onboarding_insights(self) -> list:
        """
        Return 3 generic cards prompting user to log data when data_days < 1.

        Requirements: 10.2
        """
        return [
            {
                "domain": "finance",
                "title": "Track your spending",
                "detail": "Start logging expenses to get personalized finance tips.",
                "icon": "wallet",
                "data_reference": "No expense data available",
            },
            {
                "domain": "wellness",
                "title": "Check in today",
                "detail": "Log your mood and sleep for wellness insights.",
                "icon": "heart",
                "data_reference": "No mood/sleep data available",
            },
            {
                "domain": "productivity",
                "title": "Set your goals",
                "detail": "Add tasks to track your productivity this week.",
                "icon": "target",
                "data_reference": "No task data available",
            },
        ]

    async def get_daily_insights(self, user_id: str) -> dict:
        """
        Main entry point for daily insights. Orchestrates:
        1. Check existing daily cache → return if hit
        2. Assemble context via context_engine
        3. Determine data sufficiency (onboarding / partial / full)
        4. If onboarding: return onboarding cards
        5. LLM generation attempt (with 3s timeout)
        6. On LLM failure: use rule-based fallback
        7. Cache store (upsert into daily_insights collection)
        8. Return response with data_sufficiency field

        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.3, 9.2, 10.2, 10.4, 11.2
        """
        from context_engine import assemble_context

        # Determine today's date string for cache key
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 1. Check cache
        try:
            cached = await self.db["daily_insights"].find_one(
                {"user_id": user_id, "date": today_str}, {"_id": 0}
            )
            if cached and cached.get("insights"):
                logger.info(f"Returning cached daily insights for user {user_id}, date {today_str}")
                return {
                    "insights": cached["insights"],
                    "data_sufficiency": cached.get("data_sufficiency", "full"),
                    "generated_at": cached.get("generated_at", ""),
                    "date": today_str,
                }
        except Exception as e:
            logger.warning(f"Daily insights cache read failed for user {user_id}: {e}")

        # 2. Assemble context
        try:
            context = await assemble_context(self.db, user_id)
        except Exception as e:
            logger.error(f"Context assembly failed for user {user_id}: {e}")
            return {
                "insights": self._onboarding_insights(),
                "data_sufficiency": "onboarding",
                "generated_at": _now_iso(),
                "date": today_str,
            }

        data_days = context.get("data_days", 0)

        # 3. Determine data sufficiency
        if data_days < 1:
            # Onboarding: user has no data
            data_sufficiency = "onboarding"
            insights = self._onboarding_insights()
        else:
            # We have some data — try LLM then fallback
            unavailable = context.get("unavailable_domains", [])
            if len(unavailable) == 0 and data_days >= 5:
                data_sufficiency = "full"
            else:
                data_sufficiency = "partial"

            # 5. Try LLM generation
            insights = await self._generate_llm_insights(context)

            # 6. Fallback if LLM failed
            if not insights:
                insights = self._fallback_insights(context)

        # 7. Cache the result
        try:
            await self.db["daily_insights"].update_one(
                {"user_id": user_id, "date": today_str},
                {"$set": {
                    "user_id": user_id,
                    "date": today_str,
                    "insights": insights,
                    "data_sufficiency": data_sufficiency,
                    "generated_at": _now_iso(),
                }},
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Daily insights cache write failed for user {user_id}: {e}")

        # 8. Return
        return {
            "insights": insights,
            "data_sufficiency": data_sufficiency,
            "generated_at": _now_iso(),
            "date": today_str,
        }


# =============================================================================
# CommandCenterService
# =============================================================================


class CommandCenterService:
    """
    Service for generating proactive daily briefings for the Helper Buddy
    Command Center.

    Produces a cross-domain briefing with summary, up to 3 action suggestions
    spanning at least 2 domains, and a cross-domain nudge connecting patterns.

    Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 9.3, 10.3, 10.4, 11.3
    """

    BRIEFING_SYSTEM = """You are a cross-domain life coach for college students.
Given the user's current state across Finance, Wellness, and Productivity, generate a daily briefing.

Return a JSON object with exactly these fields:
- "summary": 1-sentence state overview connecting 2+ domains (reference numbers), ≤150 chars
- "actions": array of up to 3 objects, each with "domain" (finance/wellness/productivity) and "suggestion" (specific actionable step, ≤80 chars). Actions MUST span at least 2 different domains.
- "nudge": 1 cross-domain insight connecting a pattern between 2 domains using a specific number (≤150 chars). Set to null if no clear pattern.

Rules:
- Every text field MUST reference at least one number from the user's data
- Be specific, not generic
- Focus on TODAY's actions

Return ONLY valid JSON. No markdown, no explanation."""

    BRIEFING_USER = """User state:
- Finance score: {finance_score}/100 (expenses: {expense_summary})
- Wellness score: {wellness_score}/100 (sleep: {sleep_summary}, stress: {stress_level})
- Productivity score: {productivity_score}/100 (tasks: {task_summary})
- Active stressors: {stressors}
- Cross-domain correlations: {correlations}

Generate today's briefing."""

    # Domain keyword groups for nudge validation
    _DOMAIN_KEYWORDS = {
        "finance": {"finance", "spending", "money", "budget"},
        "wellness": {"wellness", "sleep", "stress", "mood"},
        "productivity": {"productivity", "task", "goal", "focus"},
    }

    def __init__(self, db):
        self.db = db

    async def _generate_llm_briefing(self, context: dict) -> Optional[dict]:
        """
        Call LLM with 5s timeout for a structured briefing.

        Parses the LLM JSON response into a dict with summary, actions, and nudge.
        Returns None on failure/timeout/parse error.

        Requirements: 7.2, 7.3, 9.3, 11.3
        """
        raw_data = context.get("raw_data", {})

        # Build summary strings for the prompt
        expense_data = raw_data.get("expenses", {})
        expense_summary = (
            f"₹{expense_data.get('total_spent', 0)} total across {expense_data.get('count', 0)} expenses"
            if expense_data else "No expenses logged"
        )

        sleep_data = raw_data.get("sleep", {})
        sleep_summary = (
            f"{sleep_data.get('avg_hours', 0)}h avg across {sleep_data.get('count', 0)} nights"
            if sleep_data else "No sleep data logged"
        )

        mood_data = raw_data.get("mood", {})
        stress_level = (
            f"{mood_data.get('avg_stress', 0)}% avg"
            if mood_data else "No mood data logged"
        )

        task_data = raw_data.get("tasks", {})
        task_summary = (
            f"{task_data.get('completed', 0)}/{task_data.get('count', 0)} completed ({task_data.get('completion_rate', 0)}%)"
            if task_data else "No tasks logged"
        )

        stressors = context.get("active_stressors", [])
        stressor_text = ", ".join(stressors[:5]) if stressors else "None detected"

        correlations = context.get("correlations", [])
        correlation_text = (
            "; ".join(
                c.get("description", str(c)) if isinstance(c, dict) else str(c)
                for c in correlations[:3]
            )
            if correlations else "Insufficient data for correlations"
        )

        user_prompt = self.BRIEFING_USER.format(
            finance_score=context.get("financial_health_score", 0),
            wellness_score=context.get("wellness_composite_score", 0),
            productivity_score=context.get("habit_consistency_percentage", 0),
            expense_summary=expense_summary,
            sleep_summary=sleep_summary,
            stress_level=stress_level,
            task_summary=task_summary,
            stressors=stressor_text,
            correlations=correlation_text,
        )

        response = await _call_llm_with_timeout(
            system_prompt=self.BRIEFING_SYSTEM,
            user_prompt=user_prompt,
            timeout_seconds=5.0,
            temperature=0.7,
            max_tokens=512,
        )

        if not response:
            return None

        try:
            briefing = json.loads(response)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse LLM briefing response: {e}")
            return None

        # Validate structure
        if not isinstance(briefing, dict):
            logger.warning("LLM briefing response is not a dict")
            return None

        summary = briefing.get("summary")
        actions = briefing.get("actions")
        nudge = briefing.get("nudge")

        # Validate summary
        if not isinstance(summary, str) or len(summary) > 150:
            logger.warning("Briefing summary missing or exceeds 150 chars")
            return None

        # Validate actions
        if not isinstance(actions, list) or len(actions) == 0 or len(actions) > 3:
            logger.warning("Briefing actions invalid count")
            return None

        for action in actions:
            if not isinstance(action, dict):
                return None
            if "domain" not in action or "suggestion" not in action:
                return None
            if not isinstance(action["suggestion"], str) or len(action["suggestion"]) > 80:
                return None

        # Validate actions span at least 2 domains
        action_domains = set(a.get("domain", "") for a in actions)
        if len(action_domains) < 2:
            logger.warning("Briefing actions don't span at least 2 domains")
            return None

        # Validate grounding on summary
        if not _validate_grounding(summary, context):
            logger.warning("Briefing summary failed grounding validation")
            return None

        return {
            "summary": summary,
            "actions": actions,
            "nudge": nudge,
        }

    def _fallback_briefing(self, context: dict) -> dict:
        """
        Construct a fallback briefing from the lowest-scoring domain and
        active stressors when LLM fails or times out.

        Logic:
        1. Find lowest-scoring domain
        2. Summary: "Your {lowest_domain} score is {score}/100. Focus on small wins today."
        3. Actions: one per available domain using templates
        4. Nudge: null (can't generate without LLM)

        Requirements: 7.5, 10.3
        """
        # Determine domain scores
        finance_score = context.get("financial_health_score", 0)
        wellness_score = context.get("wellness_composite_score", 0)
        productivity_score = context.get("habit_consistency_percentage", 0)
        unavailable = context.get("unavailable_domains", [])

        # Build available domain scores
        domain_scores = {}
        if "expenses" not in unavailable and "budget" not in unavailable:
            domain_scores["finance"] = int(finance_score)
        if not ("mood" in unavailable and "sleep" in unavailable):
            domain_scores["wellness"] = int(wellness_score)
        if "tasks" not in unavailable:
            domain_scores["productivity"] = int(productivity_score)

        # Find lowest-scoring domain
        if domain_scores:
            lowest_domain = min(domain_scores, key=domain_scores.get)
            lowest_score = domain_scores[lowest_domain]
        else:
            lowest_domain = "wellness"
            lowest_score = 0

        # Build summary
        summary = f"Your {lowest_domain} score is {lowest_score}/100. Focus on small wins today."

        # Build actions - one per available domain using templates
        action_templates = {
            "finance": "Review your top expense category this week",
            "wellness": "Take a 5-min break if stress is above 60",
            "productivity": "Complete your highest-priority task before lunch",
        }

        actions = []
        for domain in ("finance", "wellness", "productivity"):
            if domain in domain_scores:
                actions.append({
                    "domain": domain,
                    "suggestion": action_templates[domain],
                })

        # If no actions available (all domains unavailable), provide at least one
        if not actions:
            actions.append({
                "domain": "wellness",
                "suggestion": "Take a 5-min break if stress is above 60",
            })

        # Nudge is null for fallback (can't generate without LLM)
        return {
            "summary": summary,
            "actions": actions,
            "nudge": None,
        }

    def _validate_nudge(self, nudge: str, context: dict) -> bool:
        """
        Validate that a nudge string meets the cross-domain constraints:
        - Length ≤ 150 characters
        - Names at least 2 distinct domains (using keyword matching)
        - Contains at least one numeric value from context

        Requirements: 8.2, 8.3
        """
        if not nudge or not isinstance(nudge, str):
            return False

        # Check length constraint
        if len(nudge) > 150:
            return False

        # Check that at least 2 domain keyword groups are represented
        nudge_lower = nudge.lower()
        domains_found = 0
        for domain, keywords in self._DOMAIN_KEYWORDS.items():
            if any(kw in nudge_lower for kw in keywords):
                domains_found += 1

        if domains_found < 2:
            return False

        # Check that at least one numeric value from context appears in nudge
        if not _validate_grounding(nudge, context):
            return False

        return True

    async def get_briefing(self, user_id: str) -> dict:
        """
        Main entry point for the Command Center briefing. Orchestrates:
        1. Cache check (daily_briefings collection, keyed by user_id + today's date)
        2. Context assembly
        3. LLM generation (with fallback)
        4. Nudge validation (omit when sufficient_data is false)
        5. Cache store
        6. Return structured response

        Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 9.3, 10.3, 10.4, 11.3
        """
        from context_engine import assemble_context

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 1. Cache check
        try:
            cached = await self.db["daily_briefings"].find_one(
                {"user_id": user_id, "date": today_str},
                {"_id": 0},
            )
            if cached:
                logger.info(f"Returning cached briefing for user {user_id}, date {today_str}")
                return cached
        except Exception as e:
            logger.warning(f"Briefing cache read failed for user {user_id}: {e}")

        # 2. Context assembly
        try:
            context = await assemble_context(self.db, user_id)
        except Exception as e:
            logger.error(f"Context assembly failed for user {user_id}: {e}")
            return {
                "summary": "Unable to generate briefing due to a data error.",
                "actions": [],
                "nudge": None,
                "data_sufficiency": "insufficient",
                "generated_at": _now_iso(),
            }

        # Determine data sufficiency
        data_days = context.get("data_days", 0)
        sufficient_data = context.get("sufficient_data", False)
        unavailable = context.get("unavailable_domains", [])

        if data_days < 1:
            data_sufficiency = "insufficient"
        elif len(unavailable) == 0 and data_days >= 5 and sufficient_data:
            data_sufficiency = "full"
        else:
            data_sufficiency = "partial"

        # 3. LLM generation with fallback
        briefing = await self._generate_llm_briefing(context)

        if briefing is None:
            briefing = self._fallback_briefing(context)

        # 4. Nudge validation - omit nudge when sufficient_data is false
        if not sufficient_data:
            briefing["nudge"] = None
        elif briefing.get("nudge") is not None:
            if not self._validate_nudge(briefing["nudge"], context):
                logger.warning("Nudge failed validation, setting to null")
                briefing["nudge"] = None

        # Build final response
        response = {
            "summary": briefing["summary"],
            "actions": briefing["actions"],
            "nudge": briefing["nudge"],
            "data_sufficiency": data_sufficiency,
            "generated_at": _now_iso(),
        }

        # 5. Cache store
        try:
            await self.db["daily_briefings"].update_one(
                {"user_id": user_id, "date": today_str},
                {
                    "$set": {
                        **response,
                        "user_id": user_id,
                        "date": today_str,
                    }
                },
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Briefing cache write failed for user {user_id}: {e}")

        # 6. Return
        return response
