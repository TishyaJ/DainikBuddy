"""
Analytics Service for PocketBuddy.
Handles trend computation (weekly/monthly), spending anomaly detection,
monthly financial health report generation, and habit recovery plan generation.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional


def _today_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


def _days_ago(days: int) -> datetime:
    """Return datetime N days ago from now in UTC."""
    return _today_utc() - timedelta(days=days)


async def compute_trends(db, user_id: str, period: str = "weekly") -> dict:
    """
    Compute trend lines for spending, mood, sleep, and habit consistency.

    Property 18: Weekly trends require ≥7 days of data; monthly require ≥28 days.
    When fewer than 30 days exist, use all available data and indicate actual days used.

    Validates: Requirements 6.1, 6.2
    """
    min_days = 7 if period == "weekly" else 28
    lookback_days = 7 if period == "weekly" else 30

    # Determine how many days of data exist
    since = _days_ago(lookback_days)
    since_iso = since.isoformat()

    # Gather expenses
    expenses = await db.expenses.find(
        {"user_id": user_id, "created_at": {"$gte": since_iso}}
    ).to_list(1000)

    # Gather mood entries
    mood_entries = await db.mood_entries.find(
        {"user_id": user_id, "created_at": {"$gte": since_iso}}
    ).to_list(500)

    # Gather sleep entries
    sleep_entries = await db.sleep_entries.find(
        {"user_id": user_id, "date": {"$gte": since.strftime("%Y-%m-%d")}}
    ).to_list(100)

    # Gather tasks for habit consistency
    tasks = await db.tasks.find(
        {"user_id": user_id}
    ).to_list(200)

    # Determine actual days with data
    expense_dates = set()
    for e in expenses:
        try:
            d = datetime.fromisoformat(e["created_at"]).date()
            expense_dates.add(d)
        except (ValueError, KeyError):
            pass

    mood_dates = set()
    for m in mood_entries:
        try:
            d = datetime.fromisoformat(m["created_at"]).date()
            mood_dates.add(d)
        except (ValueError, KeyError):
            pass

    sleep_dates = set()
    for s in sleep_entries:
        try:
            d_str = s.get("date", "")
            if d_str:
                sleep_dates.add(datetime.strptime(d_str, "%Y-%m-%d").date() if isinstance(d_str, str) else d_str)
        except (ValueError, KeyError):
            pass

    all_dates = expense_dates | mood_dates | sleep_dates
    actual_days = len(all_dates)

    # Check data sufficiency
    if actual_days < min_days:
        return {
            "status": "insufficient_data",
            "required_days": min_days,
            "actual_days": actual_days,
            "period": period,
            "message": f"Need at least {min_days} days of data for {period} trends. Currently have {actual_days} days.",
        }

    # Compute spending by category
    spending_by_category = {}
    daily_spending = {}
    for e in expenses:
        cat = e.get("category", "misc")
        amount = e.get("amount", 0)
        spending_by_category[cat] = spending_by_category.get(cat, 0) + amount
        try:
            d = datetime.fromisoformat(e["created_at"]).date().isoformat()
            daily_spending[d] = daily_spending.get(d, 0) + amount
        except (ValueError, KeyError):
            pass

    total_spending = sum(spending_by_category.values())

    # Compute average mood score
    mood_scores = []
    for m in mood_entries:
        # Map mood text to numeric: great=5, good=4, okay=3, bad=2, terrible=1
        mood_map = {"great": 5, "good": 4, "okay": 3, "bad": 2, "terrible": 1}
        mood_val = mood_map.get(m.get("mood", "okay"), 3)
        mood_scores.append(mood_val)
    avg_mood = round(sum(mood_scores) / len(mood_scores), 2) if mood_scores else None

    # Compute average sleep
    sleep_hours = [s.get("hours", 0) for s in sleep_entries if s.get("hours")]
    avg_sleep = round(sum(sleep_hours) / len(sleep_hours), 2) if sleep_hours else None

    # Compute habit consistency (% of days with at least one check-in activity)
    today = _today_utc().date()
    habit_days = 0
    for i in range(lookback_days):
        check_date = today - timedelta(days=i)
        has_activity = (
            check_date in expense_dates or
            check_date in mood_dates or
            check_date in sleep_dates
        )
        if has_activity:
            habit_days += 1
    habit_consistency = round((habit_days / lookback_days) * 100, 1)

    # Compute comparison with prior period if enough data
    comparison = None
    prior_since = _days_ago(lookback_days * 2)
    prior_until = _days_ago(lookback_days)
    prior_expenses = await db.expenses.find(
        {"user_id": user_id, "created_at": {
            "$gte": prior_since.isoformat(),
            "$lt": prior_until.isoformat()
        }}
    ).to_list(1000)

    if prior_expenses:
        prior_total = sum(e.get("amount", 0) for e in prior_expenses)
        if prior_total > 0:
            spending_change = round(((total_spending - prior_total) / prior_total) * 100, 1)
        else:
            spending_change = None
        comparison = {
            "spending_change_pct": spending_change,
            "prior_period_total": prior_total,
            "current_period_total": total_spending,
        }

    return {
        "status": "ok",
        "period": period,
        "actual_days": actual_days,
        "spending": {
            "total": total_spending,
            "by_category": spending_by_category,
            "daily": daily_spending,
        },
        "mood": {
            "average_score": avg_mood,
            "entries_count": len(mood_scores),
        },
        "sleep": {
            "average_hours": avg_sleep,
            "entries_count": len(sleep_hours),
        },
        "habit_consistency_pct": habit_consistency,
        "comparison": comparison,
    }


async def detect_anomalies(db, user_id: str) -> list:
    """
    Detect spending anomalies: flag when daily spend > 2× 30-day daily average.

    Property 19: For any daily expense total that exceeds 2× the user's 30-day daily average,
    an anomaly SHALL be flagged containing the anomalous amount, the 30-day daily average,
    and the percentage deviation.

    Validates: Requirements 6.3
    """
    since_30d = _days_ago(30)
    expenses = await db.expenses.find(
        {"user_id": user_id, "created_at": {"$gte": since_30d.isoformat()}}
    ).to_list(2000)

    if not expenses:
        return []

    # Compute daily totals
    daily_totals = {}
    for e in expenses:
        try:
            d = datetime.fromisoformat(e["created_at"]).date().isoformat()
            daily_totals[d] = daily_totals.get(d, 0) + e.get("amount", 0)
        except (ValueError, KeyError):
            pass

    if not daily_totals:
        return []

    # Compute 30-day daily average
    total_spent = sum(daily_totals.values())
    num_days = len(daily_totals)
    daily_average = total_spent / num_days if num_days > 0 else 0

    if daily_average <= 0:
        return []

    # Threshold is 2× daily average
    threshold = daily_average * 2

    # Find anomalies
    anomalies = []
    for date_str, amount in sorted(daily_totals.items(), reverse=True):
        if amount > threshold:
            deviation_pct = round(((amount - daily_average) / daily_average) * 100, 1)
            anomalies.append({
                "date": date_str,
                "amount": round(amount, 2),
                "daily_average": round(daily_average, 2),
                "threshold": round(threshold, 2),
                "deviation_pct": deviation_pct,
                "message": f"Spent ₹{amount:.0f} on {date_str} — {deviation_pct}% above your 30-day daily average of ₹{daily_average:.0f}.",
            })

    return anomalies


async def generate_monthly_report(db, user_id: str) -> dict:
    """
    Generate monthly financial health report.
    Includes: total income vs spending, category budget adherence,
    savings progress, and predicted month-end balance.

    Validates: Requirements 6.4
    """
    today = _today_utc()
    # Current month start
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_iso = month_start.isoformat()

    # Get user's monthly income
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    monthly_income = (profile or {}).get("monthly_income", 0)

    # Get this month's expenses
    expenses = await db.expenses.find(
        {"user_id": user_id, "created_at": {"$gte": month_start_iso}}
    ).to_list(2000)

    total_spending = sum(e.get("amount", 0) for e in expenses)

    # Category-wise spending
    category_spending = {}
    for e in expenses:
        cat = e.get("category", "misc")
        category_spending[cat] = category_spending.get(cat, 0) + e.get("amount", 0)

    # Get budget categories for adherence computation
    budget_cats = await db.budget_categories.find({"user_id": user_id}).to_list(100)

    category_adherence = []
    for bc in budget_cats:
        name = bc.get("name", bc.get("category", "Unknown"))
        allocated = bc.get("allocated", 0)
        spent = bc.get("spent", 0)
        adherence_pct = round((spent / allocated) * 100, 1) if allocated > 0 else 0
        category_adherence.append({
            "category": name,
            "allocated": allocated,
            "spent": spent,
            "adherence_pct": adherence_pct,
            "within_budget": spent <= allocated,
        })

    # Savings progress
    goals = await db.goals.find(
        {"user_id": user_id, "status": {"$ne": "done"}}
    ).to_list(50)
    savings_goals = []
    for g in goals:
        savings_goals.append({
            "title": g.get("title", "Untitled"),
            "target": g.get("target", 0),
            "current": g.get("current", 0),
            "progress_pct": round((g.get("current", 0) / g.get("target", 1)) * 100, 1) if g.get("target", 0) > 0 else 0,
        })

    # Predicted month-end balance based on current spending trajectory
    days_elapsed = max(1, today.day)
    last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    days_in_month = last_day.day
    daily_spend_rate = total_spending / days_elapsed
    predicted_total_spending = round(daily_spend_rate * days_in_month, 2)
    predicted_month_end_balance = round(monthly_income - predicted_total_spending, 2)

    return {
        "month": today.strftime("%B %Y"),
        "monthly_income": monthly_income,
        "total_spending": round(total_spending, 2),
        "net_balance": round(monthly_income - total_spending, 2),
        "category_adherence": category_adherence,
        "savings_goals": savings_goals,
        "prediction": {
            "daily_spend_rate": round(daily_spend_rate, 2),
            "predicted_total_spending": predicted_total_spending,
            "predicted_month_end_balance": predicted_month_end_balance,
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
        },
    }


async def generate_recovery_plan(db, user_id: str) -> dict:
    """
    Generate personalized habit recovery plan.
    Triggered when habit consistency < 40% for 14 consecutive days.
    Suggests ≤3 schedule adjustments.

    Property 20: For any tracked habit whose consistency drops below 40% for 2 consecutive
    weeks (14 days), a personalized recovery plan SHALL be generated containing at most 3
    specific schedule adjustments.

    Validates: Requirements 6.5
    """
    today = _today_utc().date()
    since_14d = _days_ago(14)
    since_14d_iso = since_14d.isoformat()

    # Gather 14-day activity data
    mood_entries = await db.mood_entries.find(
        {"user_id": user_id, "created_at": {"$gte": since_14d_iso}}
    ).to_list(200)

    sleep_entries = await db.sleep_entries.find(
        {"user_id": user_id, "date": {"$gte": since_14d.strftime("%Y-%m-%d")}}
    ).to_list(50)

    journal_entries = await db.journal_entries.find(
        {"user_id": user_id, "created_at": {"$gte": since_14d_iso}}
    ).to_list(100)

    exercise_sessions = await db.exercise_sessions.find(
        {"user_id": user_id, "started_at": {"$gte": since_14d_iso}}
    ).to_list(200)

    # Calculate per-habit consistency over 14 days
    habits = {}

    # Mood check-in consistency
    mood_dates = set()
    for m in mood_entries:
        try:
            mood_dates.add(datetime.fromisoformat(m["created_at"]).date())
        except (ValueError, KeyError):
            pass
    mood_consistency = round((len(mood_dates) / 14) * 100, 1)
    habits["mood_checkin"] = {
        "name": "Daily mood check-in",
        "consistency_pct": mood_consistency,
        "days_completed": len(mood_dates),
    }

    # Sleep logging consistency
    sleep_dates = set()
    for s in sleep_entries:
        try:
            d_str = s.get("date", "")
            if d_str:
                sleep_dates.add(datetime.strptime(d_str, "%Y-%m-%d").date() if isinstance(d_str, str) else d_str)
        except (ValueError, KeyError):
            pass
    sleep_consistency = round((len(sleep_dates) / 14) * 100, 1)
    habits["sleep_logging"] = {
        "name": "Sleep logging",
        "consistency_pct": sleep_consistency,
        "days_completed": len(sleep_dates),
    }

    # Journal consistency
    journal_dates = set()
    for j in journal_entries:
        try:
            journal_dates.add(datetime.fromisoformat(j["created_at"]).date())
        except (ValueError, KeyError):
            pass
    journal_consistency = round((len(journal_dates) / 14) * 100, 1)
    habits["journaling"] = {
        "name": "Daily journaling",
        "consistency_pct": journal_consistency,
        "days_completed": len(journal_dates),
    }

    # Exercise consistency
    exercise_dates = set()
    for ex in exercise_sessions:
        try:
            exercise_dates.add(datetime.fromisoformat(ex["started_at"]).date())
        except (ValueError, KeyError):
            pass
    exercise_consistency = round((len(exercise_dates) / 14) * 100, 1)
    habits["exercise"] = {
        "name": "Exercise",
        "consistency_pct": exercise_consistency,
        "days_completed": len(exercise_dates),
    }

    # Identify habits below 40% threshold
    declining_habits = {k: v for k, v in habits.items() if v["consistency_pct"] < 40}

    if not declining_habits:
        return {
            "status": "no_recovery_needed",
            "habits": habits,
            "message": "All habits are above 40% consistency. Keep it up!",
            "adjustments": [],
        }

    # Get user's energy pattern and preferences from profile
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0}) or {}
    your_pattern = profile.get("your_pattern", {})
    energy_peak = your_pattern.get("energy_peak", "morning")

    # Generate ≤3 schedule adjustments
    adjustments = []

    # Define recovery suggestions per habit based on energy pattern
    suggestion_map = {
        "mood_checkin": {
            "morning": "Set a morning alarm reminder to check in with your mood right after waking up — takes just 30 seconds.",
            "afternoon": "Link your mood check-in to lunch time — check in right before or after eating.",
            "evening": "Add a mood check-in to your bedtime routine — reflect on the day before sleep.",
        },
        "sleep_logging": {
            "morning": "Log last night's sleep as your first action each morning — it's fresh in your mind.",
            "afternoon": "Set a midday reminder to log yesterday's sleep if you missed it in the morning.",
            "evening": "Log your sleep right when you get into bed — set a nightly phone reminder.",
        },
        "journaling": {
            "morning": "Write 2-3 lines in your journal with morning coffee — keep it short and consistent.",
            "afternoon": "Use a lunch break to jot down one highlight and one challenge from the morning.",
            "evening": "Spend 5 minutes journaling before bed — it helps process the day and wind down.",
        },
        "exercise": {
            "morning": "Try a 10-minute stretch or walk right after waking — lower the bar to build consistency.",
            "afternoon": "Block 15 minutes after lunch for a short walk — movement aids digestion and focus.",
            "evening": "Add a 10-minute bodyweight routine before dinner — no equipment needed.",
        },
    }

    for habit_key, habit_data in list(declining_habits.items())[:3]:
        time_slot = energy_peak if energy_peak in ("morning", "afternoon", "evening") else "morning"
        suggestion = suggestion_map.get(habit_key, {}).get(
            time_slot,
            f"Try to do {habit_data['name'].lower()} at a consistent time each day."
        )
        adjustments.append({
            "habit": habit_data["name"],
            "current_consistency": habit_data["consistency_pct"],
            "suggestion": suggestion,
            "target_time": time_slot,
        })

    return {
        "status": "recovery_needed",
        "habits": habits,
        "declining_habits": list(declining_habits.keys()),
        "adjustments": adjustments,
        "message": f"Found {len(declining_habits)} habit(s) below 40% consistency over the past 14 days.",
    }
