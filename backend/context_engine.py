"""
Context Engine for PocketBuddy AI Enhancement.

Assembles 7-day user data (mood, expenses, sleep, goals, burnout score) into a
unified context object for AI buddy conversations and cross-domain correlation.

Requirements: 1.1, 1.4, 1.6, 1.7
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Domain identifiers
DOMAINS = ["mood", "expenses", "sleep", "goals", "tasks"]

# Quality mapping for sleep entries (string -> numeric)
SLEEP_QUALITY_MAP = {"good": 5, "ok": 3, "poor": 1}

# Mood mapping (string -> numeric 1-5)
MOOD_MAP = {"great": 5, "good": 4, "okay": 3, "bad": 2, "terrible": 1}

# Minimum days required for cross-domain correlations
MIN_DAYS_FOR_CORRELATIONS = 3


async def _fetch_domain_data(
    db, user_id: str, collection: str, date_field: str, since: str, limit: int = 500
) -> List[Dict[str, Any]]:
    """Fetch documents from a collection for a given user since a date."""
    cursor = db[collection].find(
        {"user_id": user_id, date_field: {"$gte": since}},
        {"_id": 0},
    ).sort(date_field, -1).limit(limit)
    return await cursor.to_list(limit)


async def _safe_fetch(
    db, user_id: str, collection: str, date_field: str, since: str
) -> tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Fetch domain data with graceful degradation.
    Returns (data, None) on success or (None, error_message) on failure.
    """
    try:
        data = await _fetch_domain_data(db, user_id, collection, date_field, since)
        return data, None
    except Exception as e:
        logger.warning(
            f"Failed to fetch {collection} for user {user_id}: {e}"
        )
        return None, str(e)


def _compute_financial_health_score(
    expenses: List[Dict[str, Any]],
    budget_categories: List[Dict[str, Any]],
) -> int:
    """
    Compute financial health score (0-100) based on budget adherence.
    
    Score logic:
    - 100 = spending exactly at or under budget
    - Decreases as spending exceeds allocated budget
    - If no budget data, use a neutral score of 50
    """
    if not budget_categories:
        return 50

    total_allocated = sum(cat.get("allocated", 0) for cat in budget_categories)
    total_spent = sum(cat.get("spent", 0) for cat in budget_categories)

    if total_allocated <= 0:
        return 50

    # Ratio of spent to allocated (1.0 = exactly at budget)
    spend_ratio = total_spent / total_allocated

    if spend_ratio <= 0.7:
        # Under 70% spending = excellent
        score = 100
    elif spend_ratio <= 1.0:
        # 70%-100% = good to moderate (100 -> 60)
        score = 100 - int((spend_ratio - 0.7) / 0.3 * 40)
    elif spend_ratio <= 1.5:
        # 100%-150% = moderate to poor (60 -> 20)
        score = 60 - int((spend_ratio - 1.0) / 0.5 * 40)
    else:
        # Over 150% = very poor
        score = max(0, 20 - int((spend_ratio - 1.5) * 40))

    return max(0, min(100, score))


def _compute_wellness_composite_score(
    moods: List[Dict[str, Any]],
    sleeps: List[Dict[str, Any]],
) -> int:
    """
    Compute wellness composite score (0-100) from mood averages, sleep quality,
    and stress levels.
    
    Components:
    - Mood score (0-100): average mood mapped to percentage
    - Sleep quality (0-100): average sleep quality mapped to percentage
    - Stress inversion (0-100): 100 - average stress (lower stress = higher score)
    """
    components = []

    if moods:
        # Mood component: map mood string to 1-5 then scale to 0-100
        mood_values = [MOOD_MAP.get(m.get("mood", "okay"), 3) for m in moods]
        avg_mood = sum(mood_values) / len(mood_values)
        mood_score = int((avg_mood / 5.0) * 100)
        components.append(mood_score)

        # Stress component: invert stress (0-100 where 100 = no stress)
        stress_values = [m.get("stress", 50) for m in moods]
        avg_stress = sum(stress_values) / len(stress_values)
        stress_score = int(100 - avg_stress)
        components.append(max(0, min(100, stress_score)))

        # Energy component
        energy_values = [m.get("energy", 50) for m in moods]
        avg_energy = sum(energy_values) / len(energy_values)
        components.append(max(0, min(100, int(avg_energy))))

    if sleeps:
        # Sleep quality component
        quality_values = [
            SLEEP_QUALITY_MAP.get(s.get("quality", "ok"), 3) for s in sleeps
        ]
        avg_quality = sum(quality_values) / len(quality_values)
        sleep_score = int((avg_quality / 5.0) * 100)
        components.append(sleep_score)

        # Sleep hours component (8h = 100%)
        hours_values = [s.get("hours", 7) for s in sleeps]
        avg_hours = sum(hours_values) / len(hours_values)
        hours_score = int(min(100, (avg_hours / 8.0) * 100))
        components.append(max(0, hours_score))

    if not components:
        return 50  # Neutral if no data

    return max(0, min(100, int(sum(components) / len(components))))


def _compute_habit_consistency(
    moods: List[Dict[str, Any]],
    sleeps: List[Dict[str, Any]],
    days_in_range: int,
) -> int:
    """
    Compute habit consistency percentage (0-100) based on how many days
    had check-ins (mood entries, sleep entries).
    
    A day counts as consistent if it has at least one mood or sleep entry.
    """
    if days_in_range <= 0:
        return 0

    # Collect unique dates with activity
    active_dates = set()

    for m in moods:
        try:
            dt = datetime.fromisoformat(m.get("created_at", ""))
            active_dates.add(dt.date())
        except (ValueError, TypeError):
            pass

    for s in sleeps:
        try:
            date_str = s.get("date", s.get("created_at", ""))
            dt = datetime.fromisoformat(date_str)
            active_dates.add(dt.date())
        except (ValueError, TypeError):
            pass

    consistency = int((len(active_dates) / days_in_range) * 100)
    return max(0, min(100, consistency))


def _identify_active_stressors(
    moods: List[Dict[str, Any]],
    expenses: List[Dict[str, Any]],
    sleeps: List[Dict[str, Any]],
    goals: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    budget_categories: List[Dict[str, Any]],
) -> List[str]:
    """
    Identify current stress factors (max 10 items).
    
    Checks for:
    - High stress levels in mood entries
    - Poor sleep quality or low hours
    - Overspent budget categories
    - Missed or behind goals
    - Low task completion rates
    """
    stressors = []

    # Check high stress from mood entries
    if moods:
        avg_stress = sum(m.get("stress", 50) for m in moods) / len(moods)
        if avg_stress > 70:
            stressors.append(f"High average stress level ({int(avg_stress)}/100)")
        
        # Check low energy
        avg_energy = sum(m.get("energy", 50) for m in moods) / len(moods)
        if avg_energy < 40:
            stressors.append(f"Low energy levels ({int(avg_energy)}/100)")

        # Check low motivation
        avg_motivation = sum(m.get("motivation", 50) for m in moods) / len(moods)
        if avg_motivation < 40:
            stressors.append(f"Low motivation ({int(avg_motivation)}/100)")

    # Check poor sleep
    if sleeps:
        avg_hours = sum(s.get("hours", 7) for s in sleeps) / len(sleeps)
        if avg_hours < 6:
            stressors.append(f"Insufficient sleep (avg {avg_hours:.1f}h/night)")

        poor_nights = sum(
            1 for s in sleeps if SLEEP_QUALITY_MAP.get(s.get("quality", "ok"), 3) <= 1
        )
        if poor_nights >= 3:
            stressors.append(f"Poor sleep quality ({poor_nights} bad nights in 7 days)")

    # Check overspent budget categories
    if budget_categories:
        for cat in budget_categories:
            allocated = cat.get("allocated", 0)
            spent = cat.get("spent", 0)
            if allocated > 0 and spent > allocated:
                overspend_pct = int(((spent - allocated) / allocated) * 100)
                stressors.append(
                    f"Over budget in {cat.get('name', 'Unknown')} (+{overspend_pct}%)"
                )

    # Check high spending categories (top expense categories)
    if expenses:
        category_totals: Dict[str, float] = {}
        for e in expenses:
            cat = e.get("category", "misc")
            category_totals[cat] = category_totals.get(cat, 0) + e.get("amount", 0)
        
        # Flag categories with unusually high spending (>40% of total)
        total_spending = sum(category_totals.values())
        if total_spending > 0:
            for cat, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
                if amount / total_spending > 0.4:
                    stressors.append(
                        f"High spending on {cat} ({int(amount / total_spending * 100)}% of total)"
                    )
                    break

    # Check missed goals
    if goals:
        for goal in goals:
            target = goal.get("target", 0)
            current = goal.get("current", 0)
            if target > 0 and current / target < 0.3:
                stressors.append(f"Behind on goal: {goal.get('title', 'Unknown')}")

    # Check incomplete tasks
    if tasks:
        completed = sum(1 for t in tasks if t.get("status") == "done")
        total = len(tasks)
        if total > 0:
            completion_rate = completed / total
            if completion_rate < 0.5:
                stressors.append(
                    f"Low task completion ({int(completion_rate * 100)}%)"
                )

    # Cap at 10 items
    return stressors[:10]


def _count_unique_data_days(
    moods: List[Dict[str, Any]],
    sleeps: List[Dict[str, Any]],
    expenses: List[Dict[str, Any]],
) -> int:
    """Count the number of unique days with data across all domains."""
    dates = set()

    for m in moods:
        try:
            dt = datetime.fromisoformat(m.get("created_at", ""))
            dates.add(dt.date())
        except (ValueError, TypeError):
            pass

    for s in sleeps:
        try:
            date_str = s.get("date", s.get("created_at", ""))
            dt = datetime.fromisoformat(date_str)
            dates.add(dt.date())
        except (ValueError, TypeError):
            pass

    for e in expenses:
        try:
            dt = datetime.fromisoformat(e.get("created_at", ""))
            dates.add(dt.date())
        except (ValueError, TypeError):
            pass

    return len(dates)


async def assemble_context(db, user_id: str) -> Dict[str, Any]:
    """
    Assemble unified context object from 7 days of user data.
    
    This is the main entry point for the context engine. It queries all domains,
    computes scores, and returns a unified context dict.
    
    Implements:
    - Graceful degradation: proceeds with available data if a domain fails
    - Data sufficiency guard: skips cross-domain correlations if <3 days of data
    - Context assembly targets completion within 2 seconds
    
    Args:
        db: Motor async MongoDB database instance
        user_id: The authenticated user's ID
        
    Returns:
        Dict containing:
        - financial_health_score (int 0-100)
        - wellness_composite_score (int 0-100)
        - habit_consistency_percentage (int 0-100)
        - active_stressors (list, max 10 items)
        - raw_data: summaries of each domain's data
        - unavailable_domains: list of domains that failed to load
        - sufficient_data: bool indicating if enough data exists for correlations
        - data_days: number of unique days with data
        - assembled_at: ISO timestamp of assembly
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    days_in_range = 7

    unavailable_domains: List[str] = []

    # Fetch all domains concurrently with graceful degradation
    mood_result, expense_result, sleep_result, goal_result, task_result = (
        await asyncio.gather(
            _safe_fetch(db, user_id, "mood_entries", "created_at", seven_days_ago),
            _safe_fetch(db, user_id, "expenses", "created_at", seven_days_ago),
            _safe_fetch(db, user_id, "sleep_entries", "date", seven_days_ago),
            _safe_fetch(db, user_id, "goals", "created_at", seven_days_ago),
            _safe_fetch(db, user_id, "tasks", "created_at", seven_days_ago),
        )
    )

    # Unpack results, tracking unavailable domains
    moods: List[Dict[str, Any]] = []
    if mood_result[0] is not None:
        moods = mood_result[0]
    else:
        unavailable_domains.append("mood")

    expenses: List[Dict[str, Any]] = []
    if expense_result[0] is not None:
        expenses = expense_result[0]
    else:
        unavailable_domains.append("expenses")

    sleeps: List[Dict[str, Any]] = []
    if sleep_result[0] is not None:
        sleeps = sleep_result[0]
    else:
        unavailable_domains.append("sleep")

    goals: List[Dict[str, Any]] = []
    if goal_result[0] is not None:
        goals = goal_result[0]
    else:
        unavailable_domains.append("goals")

    tasks: List[Dict[str, Any]] = []
    if task_result[0] is not None:
        tasks = task_result[0]
    else:
        unavailable_domains.append("tasks")

    # Fetch budget categories (not time-bounded, represents current state)
    budget_categories: List[Dict[str, Any]] = []
    try:
        cursor = db["budget_categories"].find(
            {"user_id": user_id}, {"_id": 0}
        )
        budget_categories = await cursor.to_list(100)
    except Exception as e:
        logger.warning(f"Failed to fetch budget_categories for user {user_id}: {e}")
        # Budget failure contributes to expenses domain being partially unavailable
        if "expenses" not in unavailable_domains:
            unavailable_domains.append("budget")

    # Determine data sufficiency
    data_days = _count_unique_data_days(moods, sleeps, expenses)
    sufficient_data = data_days >= MIN_DAYS_FOR_CORRELATIONS

    # Compute scores
    financial_health_score = _compute_financial_health_score(expenses, budget_categories)
    wellness_composite_score = _compute_wellness_composite_score(moods, sleeps)
    habit_consistency_percentage = _compute_habit_consistency(moods, sleeps, days_in_range)

    # Identify active stressors
    active_stressors = _identify_active_stressors(
        moods, expenses, sleeps, goals, tasks, budget_categories
    )

    # Build raw data summaries
    raw_data = {}

    if moods:
        mood_values = [MOOD_MAP.get(m.get("mood", "okay"), 3) for m in moods]
        raw_data["mood"] = {
            "count": len(moods),
            "avg_mood": round(sum(mood_values) / len(mood_values), 2),
            "avg_stress": round(
                sum(m.get("stress", 50) for m in moods) / len(moods), 1
            ),
            "avg_energy": round(
                sum(m.get("energy", 50) for m in moods) / len(moods), 1
            ),
            "avg_motivation": round(
                sum(m.get("motivation", 50) for m in moods) / len(moods), 1
            ),
        }

    if expenses:
        category_totals: Dict[str, float] = {}
        for e in expenses:
            cat = e.get("category", "misc")
            category_totals[cat] = category_totals.get(cat, 0) + e.get("amount", 0)
        raw_data["expenses"] = {
            "count": len(expenses),
            "total_spent": round(sum(e.get("amount", 0) for e in expenses), 2),
            "by_category": {k: round(v, 2) for k, v in category_totals.items()},
        }

    if sleeps:
        raw_data["sleep"] = {
            "count": len(sleeps),
            "avg_hours": round(
                sum(s.get("hours", 7) for s in sleeps) / len(sleeps), 1
            ),
            "avg_quality": round(
                sum(
                    SLEEP_QUALITY_MAP.get(s.get("quality", "ok"), 3) for s in sleeps
                )
                / len(sleeps),
                1,
            ),
        }

    if goals:
        raw_data["goals"] = {
            "count": len(goals),
            "active": sum(1 for g in goals if g.get("status") == "active"),
            "completed": sum(1 for g in goals if g.get("status") == "done"),
        }

    if tasks:
        raw_data["tasks"] = {
            "count": len(tasks),
            "completed": sum(1 for t in tasks if t.get("status") == "done"),
            "completion_rate": round(
                sum(1 for t in tasks if t.get("status") == "done") / len(tasks) * 100,
                1,
            ),
        }

    # Build cross-domain correlations only if sufficient data
    correlations = []
    if sufficient_data and len(unavailable_domains) == 0:
        correlations = _compute_cross_domain_correlations(
            moods, expenses, sleeps, goals, tasks, budget_categories
        )

    context = {
        "user_id": user_id,
        "financial_health_score": financial_health_score,
        "wellness_composite_score": wellness_composite_score,
        "habit_consistency_percentage": habit_consistency_percentage,
        "active_stressors": active_stressors,
        "raw_data": raw_data,
        "correlations": correlations,
        "unavailable_domains": unavailable_domains,
        "sufficient_data": sufficient_data,
        "data_days": data_days,
        "assembled_at": now.isoformat(),
    }

    logger.info(
        f"Context assembled for user {user_id}: "
        f"financial={financial_health_score}, wellness={wellness_composite_score}, "
        f"consistency={habit_consistency_percentage}%, "
        f"stressors={len(active_stressors)}, "
        f"unavailable={unavailable_domains}, sufficient={sufficient_data}"
    )

    return context


def _compute_cross_domain_correlations(
    moods: List[Dict[str, Any]],
    expenses: List[Dict[str, Any]],
    sleeps: List[Dict[str, Any]],
    goals: List[Dict[str, Any]],
    tasks: List[Dict[str, Any]],
    budget_categories: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    """
    Compute cross-domain correlations when sufficient data exists.
    
    Detects patterns like:
    - High stress + increased food spending (emotional eating)
    - Poor sleep + low task completion (burnout risk)
    - Budget overspend + stress correlation
    """
    correlations = []

    # Emotional eating: stress > 70 and high food spending
    if moods and expenses:
        avg_stress = sum(m.get("stress", 50) for m in moods) / len(moods)
        food_spending = sum(
            e.get("amount", 0) for e in expenses if e.get("category") == "food"
        )
        total_spending = sum(e.get("amount", 0) for e in expenses)

        if avg_stress > 70 and total_spending > 0 and food_spending / total_spending > 0.4:
            correlations.append({
                "type": "emotional_eating",
                "description": (
                    f"High stress ({int(avg_stress)}/100) correlates with elevated food spending "
                    f"({int(food_spending / total_spending * 100)}% of total expenses)"
                ),
                "domains": ["mood", "expenses"],
            })

    # Burnout risk: poor sleep + low task completion
    if sleeps and tasks:
        avg_sleep = sum(s.get("hours", 7) for s in sleeps) / len(sleeps)
        completed_tasks = sum(1 for t in tasks if t.get("status") == "done")
        total_tasks = len(tasks)
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 1.0

        if avg_sleep < 6 and completion_rate < 0.5:
            correlations.append({
                "type": "burnout_risk",
                "description": (
                    f"Low sleep ({avg_sleep:.1f}h avg) combined with low task completion "
                    f"({int(completion_rate * 100)}%) suggests burnout risk"
                ),
                "domains": ["sleep", "tasks"],
            })

    # Financial stress: overspending + high stress
    if moods and budget_categories:
        avg_stress = sum(m.get("stress", 50) for m in moods) / len(moods)
        total_allocated = sum(cat.get("allocated", 0) for cat in budget_categories)
        total_spent = sum(cat.get("spent", 0) for cat in budget_categories)

        if total_allocated > 0 and total_spent > total_allocated and avg_stress > 60:
            correlations.append({
                "type": "financial_stress",
                "description": (
                    f"Budget overspend ({int(total_spent / total_allocated * 100)}% of allocated) "
                    f"may be contributing to elevated stress ({int(avg_stress)}/100)"
                ),
                "domains": ["expenses", "mood"],
            })

    return correlations


def _has_consecutive_poor_sleep(sleeps: List[Dict[str, Any]], threshold: float = 6.0, consecutive_days: int = 3) -> bool:
    """
    Check if there are N consecutive days with sleep < threshold hours.
    
    Sleeps should be sorted by date. We group by date and check for consecutive
    days meeting the condition.
    """
    if len(sleeps) < consecutive_days:
        return False

    # Group sleep hours by date
    daily_hours: Dict[str, float] = {}
    for s in sleeps:
        date_str = s.get("date", s.get("created_at", ""))
        try:
            dt = datetime.fromisoformat(date_str)
            day_key = dt.strftime("%Y-%m-%d")
            # If multiple entries per day, use the max (most sleep)
            if day_key in daily_hours:
                daily_hours[day_key] = max(daily_hours[day_key], s.get("hours", 7))
            else:
                daily_hours[day_key] = s.get("hours", 7)
        except (ValueError, TypeError):
            continue

    if len(daily_hours) < consecutive_days:
        return False

    # Sort dates and check for consecutive poor sleep days
    sorted_dates = sorted(daily_hours.keys())
    consecutive_count = 0

    for i, date_key in enumerate(sorted_dates):
        if daily_hours[date_key] < threshold:
            consecutive_count += 1
            if consecutive_count >= consecutive_days:
                return True
        else:
            consecutive_count = 0

        # Also verify the dates are actually consecutive (no gaps)
        if i > 0 and consecutive_count > 1:
            prev_date = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d").date()
            curr_date = datetime.strptime(date_key, "%Y-%m-%d").date()
            if (curr_date - prev_date).days != 1:
                consecutive_count = 1 if daily_hours[date_key] < threshold else 0

    return False


async def detect_correlations(db, user_id: str) -> List[Dict[str, Any]]:
    """
    Detect cross-domain correlations with enhanced logic.
    
    Requirements 1.2, 1.3, 1.5:
    - Emotional eating: stress > 70 AND food spending +30% vs prior 7 days
    - Burnout risk: sleep < 6h for 3 CONSECUTIVE days AND task completion < 50%
    - Returns list of correlation insight dicts with type, title, detail, icon
    
    This function fetches data from both the current 7 days AND the prior 7 days
    (days 8-14 ago) to perform period-over-period comparisons.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).isoformat()
    fourteen_days_ago = (now - timedelta(days=14)).isoformat()

    correlations: List[Dict[str, Any]] = []

    # Fetch current period data (last 7 days)
    current_moods, current_expenses, current_sleeps, current_tasks = await asyncio.gather(
        _fetch_domain_data(db, user_id, "mood_entries", "created_at", seven_days_ago),
        _fetch_domain_data(db, user_id, "expenses", "created_at", seven_days_ago),
        _fetch_domain_data(db, user_id, "sleep_entries", "date", seven_days_ago),
        _fetch_domain_data(db, user_id, "tasks", "created_at", seven_days_ago),
    )

    # Fetch prior period data (days 8-14) for comparison
    prior_expenses_all = await _fetch_domain_data(
        db, user_id, "expenses", "created_at", fourteen_days_ago, limit=1000
    )
    # Filter to only the prior period (between 14 and 7 days ago)
    prior_expenses = [
        e for e in prior_expenses_all
        if e.get("created_at", "") < seven_days_ago
    ]

    # Check data sufficiency
    data_days = _count_unique_data_days(current_moods, current_sleeps, current_expenses)
    if data_days < MIN_DAYS_FOR_CORRELATIONS:
        return []

    # --- Emotional Eating Detection ---
    # Stress > 70 AND food spending +30% vs prior 7 days
    if current_moods and current_expenses:
        avg_stress = sum(m.get("stress", 50) for m in current_moods) / len(current_moods)

        if avg_stress > 70:
            # Calculate current period food spending
            current_food_spending = sum(
                e.get("amount", 0) for e in current_expenses
                if e.get("category") == "food"
            )
            # Calculate prior period food spending
            prior_food_spending = sum(
                e.get("amount", 0) for e in prior_expenses
                if e.get("category") == "food"
            )

            # Check for +30% increase (only if prior period has data)
            if prior_food_spending > 0:
                increase_pct = ((current_food_spending - prior_food_spending) / prior_food_spending) * 100
                if increase_pct > 30:
                    correlations.append({
                        "type": "emotional_eating",
                        "domain": "correlation",
                        "title": "Emotional Eating Pattern Detected",
                        "detail": (
                            f"Your stress is high ({int(avg_stress)}/100) and food spending "
                            f"increased {int(increase_pct)}% vs last week. Consider mindful "
                            f"eating or a stress-relief activity instead."
                        ),
                        "icon": "alert-triangle",
                    })

    # --- Burnout Risk Detection ---
    # Sleep < 6h for 3 CONSECUTIVE days AND task completion < 50%
    if current_sleeps and current_tasks:
        has_consecutive_poor_sleep = _has_consecutive_poor_sleep(
            current_sleeps, threshold=6.0, consecutive_days=3
        )

        if has_consecutive_poor_sleep:
            completed_tasks = sum(1 for t in current_tasks if t.get("status") == "done")
            total_tasks = len(current_tasks)
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 1.0

            if completion_rate < 0.5:
                avg_sleep = sum(s.get("hours", 7) for s in current_sleeps) / len(current_sleeps)
                correlations.append({
                    "type": "burnout_risk",
                    "domain": "correlation",
                    "title": "Burnout Risk Alert",
                    "detail": (
                        f"You've slept under 6h for 3+ consecutive days (avg {avg_sleep:.1f}h) "
                        f"and task completion is at {int(completion_rate * 100)}%. "
                        f"Consider taking a recovery day."
                    ),
                    "icon": "alert-circle",
                })

    # --- Financial Stress (retained from original) ---
    if current_moods:
        avg_stress = sum(m.get("stress", 50) for m in current_moods) / len(current_moods)
        try:
            budget_categories = await db["budget_categories"].find(
                {"user_id": user_id}, {"_id": 0}
            ).to_list(100)
        except Exception:
            budget_categories = []

        if budget_categories:
            total_allocated = sum(cat.get("allocated", 0) for cat in budget_categories)
            total_spent = sum(cat.get("spent", 0) for cat in budget_categories)

            if total_allocated > 0 and total_spent > total_allocated and avg_stress > 60:
                correlations.append({
                    "type": "financial_stress",
                    "domain": "correlation",
                    "title": "Financial Stress Detected",
                    "detail": (
                        f"You've overspent your budget ({int(total_spent / total_allocated * 100)}% used) "
                        f"and stress is elevated ({int(avg_stress)}/100). "
                        f"Review non-essential spending this week."
                    ),
                    "icon": "trending-down",
                })

    return correlations


async def get_wellness_context_for_finance(db, user_id: str) -> Optional[str]:
    """
    Get wellness context string to prepend to Finance Buddy's system prompt.
    
    Requirement 1.5: When stress > 60 or sleep avg < 6.5h, include wellness data.
    
    Returns a context string if thresholds are crossed, None otherwise.
    """
    now = datetime.now(timezone.utc)
    seven_days_ago = (now - timedelta(days=7)).isoformat()

    moods, sleeps = await asyncio.gather(
        _fetch_domain_data(db, user_id, "mood_entries", "created_at", seven_days_ago),
        _fetch_domain_data(db, user_id, "sleep_entries", "date", seven_days_ago),
    )

    wellness_notes = []

    if moods:
        avg_stress = sum(m.get("stress", 50) for m in moods) / len(moods)
        if avg_stress > 60:
            wellness_notes.append(
                f"The user's stress level is elevated ({int(avg_stress)}/100 over the past week). "
                f"Consider how financial decisions may be affected by stress."
            )

    if sleeps:
        avg_sleep = sum(s.get("hours", 7) for s in sleeps) / len(sleeps)
        if avg_sleep < 6.5:
            wellness_notes.append(
                f"The user is sleep-deprived (avg {avg_sleep:.1f}h/night over 7 days). "
                f"Fatigue can impair financial decision-making."
            )

    if wellness_notes:
        return (
            "\n\n[WELLNESS CONTEXT - The user's wellbeing may affect financial decisions]\n"
            + "\n".join(wellness_notes)
            + "\nPlease gently acknowledge how their wellbeing relates to the financial topic "
            "and suggest small, supportive steps."
        )

    return None
