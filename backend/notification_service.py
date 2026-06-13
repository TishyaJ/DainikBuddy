"""
Notification Service for PocketBuddy.
Handles nudge generation logic for budget warnings, wellness nudges,
check-in reminders, streak celebrations, and notification management.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
import uuid
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

NOTIFICATIONS_COLLECTION = "notifications"
PREFERENCES_COLLECTION = "notification_preferences"

# Streak milestone thresholds
STREAK_MILESTONES = [7, 14, 30, 60, 90]

# XP earned per milestone
MILESTONE_XP = {7: 50, 14: 100, 30: 200, 60: 500, 90: 1000}

# High-stress rate limit
HIGH_STRESS_MAX_NUDGES_PER_DAY = 3
HIGH_STRESS_THRESHOLD = 70
HIGH_STRESS_CONSECUTIVE_DAYS = 2

# Budget warning threshold
BUDGET_WARNING_THRESHOLD = 0.80

# Burnout score threshold for wellness nudge
BURNOUT_THRESHOLD = 40

# Recovery action suggestions
RECOVERY_ACTIONS = [
    "Take a 10-minute breathing break",
    "Go for a short walk outside",
    "Try a 5-minute guided meditation",
    "Take a 20-minute power nap",
    "Do some light stretching exercises",
    "Listen to calming music for 10 minutes",
]


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    """Generate a unique notification ID."""
    return str(uuid.uuid4())


async def get_preferences(user_id: str) -> dict:
    """Get notification preferences for a user, creating defaults if not found."""
    prefs = await db[PREFERENCES_COLLECTION].find_one({"user_id": user_id})
    if not prefs:
        prefs = {
            "user_id": user_id,
            "budget_alerts": True,
            "wellness_reminders": True,
            "streak_celebrations": True,
            "social_updates": True,
            "suppressed_types": [],
        }
        await db[PREFERENCES_COLLECTION].insert_one(prefs)
    # Remove MongoDB _id for response
    prefs.pop("_id", None)
    return prefs


async def update_preferences(user_id: str, updates: dict) -> dict:
    """Update notification preferences for a user."""
    allowed_fields = {"budget_alerts", "wellness_reminders", "streak_celebrations", "social_updates"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields and isinstance(v, bool)}

    if not filtered:
        return await get_preferences(user_id)

    await db[PREFERENCES_COLLECTION].update_one(
        {"user_id": user_id},
        {"$set": filtered},
        upsert=True,
    )
    return await get_preferences(user_id)


async def _is_category_enabled(user_id: str, category: str) -> bool:
    """Check if a notification category is enabled for the user."""
    prefs = await get_preferences(user_id)

    category_map = {
        "budget_warning": "budget_alerts",
        "wellness_nudge": "wellness_reminders",
        "streak_celebration": "streak_celebrations",
        "social_update": "social_updates",
        "reminder": "wellness_reminders",
    }

    pref_key = category_map.get(category, "wellness_reminders")
    return prefs.get(pref_key, True)


async def _is_type_suppressed(user_id: str, nudge_type: str) -> bool:
    """Check if a nudge type is currently suppressed due to dismissals."""
    prefs = await get_preferences(user_id)
    suppressed = prefs.get("suppressed_types", [])
    now = datetime.now(timezone.utc)

    for entry in suppressed:
        if entry.get("type") == nudge_type:
            until_str = entry.get("until", "")
            try:
                until_dt = datetime.fromisoformat(until_str)
                if now < until_dt:
                    return True
            except (ValueError, TypeError):
                continue
    return False


async def _check_high_stress_rate_limit(user_id: str) -> bool:
    """
    Check if user is under high-stress rate limit.
    Returns True if rate-limited (should NOT send more nudges).
    Req 3.5: max 3 nudges/day when stress > 70 for 2 consecutive days.
    """
    # Check if stress > 70 for 2 consecutive days
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
    mood_entries = await db.mood_entries.find(
        {"user_id": user_id, "created_at": {"$gte": two_days_ago.isoformat()}}
    ).sort("created_at", -1).to_list(100)

    if len(mood_entries) < 2:
        return False

    # Group by day and check stress scores
    days_with_high_stress = set()
    for entry in mood_entries:
        stress = entry.get("stress", entry.get("stress_level", 50))
        if stress > HIGH_STRESS_THRESHOLD:
            entry_date = entry.get("created_at", "")[:10]
            days_with_high_stress.add(entry_date)

    # Need at least 2 consecutive days with high stress
    if len(days_with_high_stress) < HIGH_STRESS_CONSECUTIVE_DAYS:
        return False

    # Check today's nudge count
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await db[NOTIFICATIONS_COLLECTION].count_documents({
        "user_id": user_id,
        "created_at": {"$gte": today_start.isoformat()},
    })

    return today_count >= HIGH_STRESS_MAX_NUDGES_PER_DAY


async def _should_reduce_frequency(user_id: str, nudge_type: str) -> bool:
    """
    Check if frequency should be reduced (50% reduction for 7 days after single dismissal).
    Returns True if we should skip this nudge (50% chance effectively).
    """
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    dismissal_count = await db[NOTIFICATIONS_COLLECTION].count_documents({
        "user_id": user_id,
        "type": nudge_type,
        "dismissed": True,
        "created_at": {"$gte": seven_days_ago.isoformat()},
    })

    # If 1-2 dismissals in past 7 days, reduce frequency by 50%
    if 1 <= dismissal_count < 3:
        import random
        return random.random() < 0.5

    return False


async def _create_notification(user_id: str, notif_type: str, title: str, body: str,
                                category: str, metadata: dict = None) -> dict | None:
    """Create and store a notification, respecting preferences and rate limits."""
    # Check if category is enabled
    if not await _is_category_enabled(user_id, notif_type):
        return None

    # Check if type is suppressed
    if await _is_type_suppressed(user_id, notif_type):
        return None

    # Check high-stress rate limit
    if await _check_high_stress_rate_limit(user_id):
        return None

    # Check frequency reduction
    if await _should_reduce_frequency(user_id, notif_type):
        return None

    notification = {
        "id": _generate_id(),
        "user_id": user_id,
        "type": notif_type,
        "title": title,
        "body": body,
        "category": category,
        "read": False,
        "dismissed": False,
        "created_at": now_iso(),
        "metadata": metadata or {},
    }

    await db[NOTIFICATIONS_COLLECTION].insert_one(notification)
    notification.pop("_id", None)
    return notification


async def generate_budget_warning(user_id: str, category_name: str,
                                   allocated: float, spent: float) -> dict | None:
    """
    Req 3.1: Generate budget warning when category reaches 80% of allocated amount.
    """
    if allocated <= 0:
        return None

    spent_pct = spent / allocated
    if spent_pct < BUDGET_WARNING_THRESHOLD:
        return None

    remaining = allocated - spent
    pct_display = round(spent_pct * 100)

    title = f"Budget Alert: {category_name}"
    body = (
        f"You've spent {pct_display}% of your {category_name} budget. "
        f"₹{remaining:.0f} remaining."
    )

    metadata = {
        "category_name": category_name,
        "spent_pct": pct_display,
        "remaining": remaining,
    }

    return await _create_notification(
        user_id, "budget_warning", title, body, "budget", metadata
    )


async def generate_wellness_nudge(user_id: str, burnout_score: float) -> dict | None:
    """
    Req 3.2: Generate wellness nudge when burnout score < 40.
    Suggests a specific recovery action.
    """
    if burnout_score >= BURNOUT_THRESHOLD:
        return None

    import random
    action = random.choice(RECOVERY_ACTIONS)

    title = "Wellness Check"
    body = f"Your wellness score is low ({burnout_score:.0f}/100). Suggested action: {action}"

    metadata = {
        "burnout_score": burnout_score,
        "suggested_action": action,
    }

    return await _create_notification(
        user_id, "wellness_nudge", title, body, "wellness", metadata
    )


async def generate_checkin_reminder(user_id: str) -> dict | None:
    """
    Req 3.3: Generate check-in reminder if no mood entry by 10 PM local time.
    """
    title = "Daily Check-in Reminder"
    body = "Don't forget to complete your daily mood check-in!"

    return await _create_notification(
        user_id, "reminder", title, body, "reminder", {}
    )


async def generate_streak_celebration(user_id: str, streak_count: int,
                                       xp_earned: int) -> dict | None:
    """
    Req 3.4: Generate streak celebration at milestones (7, 14, 30, 60, 90 days).
    """
    if streak_count not in STREAK_MILESTONES:
        return None

    title = f"🎉 {streak_count}-Day Streak!"
    body = f"Amazing! You've maintained a {streak_count}-day streak and earned {xp_earned} XP!"

    metadata = {
        "streak_count": streak_count,
        "xp_earned": xp_earned,
    }

    return await _create_notification(
        user_id, "streak_celebration", title, body, "streak", metadata
    )


async def check_budget_warnings(user_id: str) -> list:
    """Check all budget categories for the user and generate warnings as needed."""
    budget_cats = await db.budget_categories.find({"user_id": user_id}).to_list(100)
    warnings = []

    for cat in budget_cats:
        allocated = cat.get("allocated", 0)
        spent = cat.get("spent", 0)
        name = cat.get("name", cat.get("category", "Unknown"))

        result = await generate_budget_warning(user_id, name, allocated, spent)
        if result:
            warnings.append(result)

    return warnings


async def check_wellness_nudge(user_id: str) -> dict | None:
    """Check burnout score and generate wellness nudge if needed."""
    # Get latest wellness/mood data to compute burnout score
    latest_mood = await db.mood_entries.find_one(
        {"user_id": user_id},
        sort=[("created_at", -1)]
    )

    if not latest_mood:
        return None

    # Compute burnout score from available data
    # Use stress as inverse indicator: burnout_score = 100 - stress
    stress = latest_mood.get("stress", latest_mood.get("stress_level", 50))
    energy = latest_mood.get("energy", latest_mood.get("energy_level", 50))

    # Simple burnout score: average of (100-stress) and energy
    burnout_score = (100 - stress + energy) / 2

    return await generate_wellness_nudge(user_id, burnout_score)


async def check_checkin_reminder(user_id: str, user_timezone: str = "UTC") -> dict | None:
    """
    Check if user has logged mood today. If not, generate reminder.
    Should be called around 10 PM user's local time.
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    today_mood = await db.mood_entries.find_one({
        "user_id": user_id,
        "created_at": {"$gte": today_start.isoformat()},
    })

    if today_mood:
        return None  # Already checked in today

    return await generate_checkin_reminder(user_id)


async def dismiss_notification(user_id: str, notification_id: str) -> dict | None:
    """
    Req 3.7: Dismiss a notification and apply frequency adaptation.
    - Single dismissal: 50% reduction for 7 days
    - 3+ dismissals of same type in 7 days: suppress for 14 days
    """
    # Find and dismiss the notification
    notif = await db[NOTIFICATIONS_COLLECTION].find_one({
        "id": notification_id,
        "user_id": user_id,
    })

    if not notif:
        return None

    await db[NOTIFICATIONS_COLLECTION].update_one(
        {"id": notification_id, "user_id": user_id},
        {"$set": {"dismissed": True}},
    )

    # Check dismissal count for this type in the last 7 days
    nudge_type = notif.get("type")
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    dismissal_count = await db[NOTIFICATIONS_COLLECTION].count_documents({
        "user_id": user_id,
        "type": nudge_type,
        "dismissed": True,
        "created_at": {"$gte": seven_days_ago.isoformat()},
    })

    # If 3+ dismissals of same type, suppress for 14 days
    if dismissal_count >= 3:
        suppress_until = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        await db[PREFERENCES_COLLECTION].update_one(
            {"user_id": user_id},
            {
                "$pull": {"suppressed_types": {"type": nudge_type}},
            },
        )
        await db[PREFERENCES_COLLECTION].update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "suppressed_types": {
                        "type": nudge_type,
                        "until": suppress_until,
                    }
                }
            },
            upsert=True,
        )

    notif["dismissed"] = True
    notif.pop("_id", None)
    return notif


async def get_notifications(user_id: str, limit: int = 20) -> list:
    """Get recent notifications for a user."""
    cursor = db[NOTIFICATIONS_COLLECTION].find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit)

    notifications = []
    async for doc in cursor:
        doc.pop("_id", None)
        notifications.append(doc)

    return notifications


async def save_push_subscription(user_id: str, subscription: dict) -> dict:
    """
    Req 3.8: Save push notification subscription for a user.
    """
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"push_subscription": subscription}},
    )
    return {"status": "subscribed", "user_id": user_id}


async def evaluate_nudges(user_id: str) -> list:
    """
    Evaluate all nudge conditions for a user and generate applicable notifications.
    Called periodically or on relevant data changes.
    """
    generated = []

    # Check budget warnings
    budget_warnings = await check_budget_warnings(user_id)
    generated.extend(budget_warnings)

    # Check wellness nudge
    wellness = await check_wellness_nudge(user_id)
    if wellness:
        generated.append(wellness)

    # Check check-in reminder
    reminder = await check_checkin_reminder(user_id)
    if reminder:
        generated.append(reminder)

    return generated
