"""
Gamification Service for PocketBuddy.
Handles XP awards, streak computation, level calculation, and achievement tracking.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import math
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collection name for gamification data
GAMIFICATION_COLLECTION = "gamification"

# XP award amounts
XP_MOOD_CHECKIN = 10
XP_EXPENSE_LOG = 5
XP_JOURNAL_ENTRY = 10
XP_PLAN_COMPLETE = 25

# Daily caps
MAX_EXPENSE_XP_PER_DAY = 10  # max 2 expense logs worth of XP per day

# Achievement definitions
ACHIEVEMENTS = [
    {"id": "first_week", "name": "First Week", "description": "Maintain a 7-day streak"},
    {"id": "budget_master", "name": "Budget Master", "description": "End a month under budget"},
    {"id": "sleep_champion", "name": "Sleep Champion", "description": "7 consecutive nights with 7+ hours of sleep"},
    {"id": "journal_keeper", "name": "Journal Keeper", "description": "Write 30 journal entries"},
    {"id": "social_butterfly", "name": "Social Butterfly", "description": "Join 3 or more study groups"},
]


def _today_str() -> str:
    """Return today's date as YYYY-MM-DD string in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def compute_streak_bonus(streak_days: int) -> int:
    """Compute streak bonus XP: min(streak_days * 2, 100)."""
    return min(streak_days * 2, 100)


def compute_level(total_xp: int) -> int:
    """Compute level from total XP: floor(total_xp / 100) + 1."""
    return math.floor(total_xp / 100) + 1


async def _get_or_create_gamification(user_id: str) -> dict:
    """Get or create gamification document for a user."""
    doc = await db[GAMIFICATION_COLLECTION].find_one({"user_id": user_id})
    if not doc:
        doc = {
            "user_id": user_id,
            "total_xp": 0,
            "level": 1,
            "streak_days": 0,
            "last_checkin_date": None,
            "achievements": [],
            "daily_xp_log": {
                "mood_checkin": False,
                "journal_entry": False,
                "expense_count": 0,
            },
            "daily_xp_date": _today_str(),
        }
        await db[GAMIFICATION_COLLECTION].insert_one(doc)
    return doc


async def _reset_daily_if_needed(doc: dict) -> dict:
    """Reset daily XP log if the date has changed."""
    today = _today_str()
    if doc.get("daily_xp_date") != today:
        doc["daily_xp_log"] = {
            "mood_checkin": False,
            "journal_entry": False,
            "expense_count": 0,
        }
        doc["daily_xp_date"] = today
        await db[GAMIFICATION_COLLECTION].update_one(
            {"user_id": doc["user_id"]},
            {"$set": {
                "daily_xp_log": doc["daily_xp_log"],
                "daily_xp_date": today,
            }}
        )
    return doc


async def _update_streak(user_id: str, doc: dict) -> dict:
    """Update streak based on mood check-in. Called when mood_checkin action occurs."""
    today = _today_str()
    last_checkin = doc.get("last_checkin_date")

    if last_checkin == today:
        # Already checked in today, no streak change
        return doc

    if last_checkin:
        last_date = datetime.strptime(last_checkin, "%Y-%m-%d").date()
        today_date = datetime.strptime(today, "%Y-%m-%d").date()
        diff = (today_date - last_date).days

        if diff == 1:
            # Consecutive day - increment streak
            doc["streak_days"] = doc.get("streak_days", 0) + 1
        elif diff > 1:
            # Missed day(s) - reset streak
            doc["streak_days"] = 1
        # diff == 0 handled above
    else:
        # First ever check-in
        doc["streak_days"] = 1

    doc["last_checkin_date"] = today

    await db[GAMIFICATION_COLLECTION].update_one(
        {"user_id": user_id},
        {"$set": {
            "streak_days": doc["streak_days"],
            "last_checkin_date": today,
        }}
    )
    return doc


async def award_xp(user_id: str, action: str) -> dict:
    """
    Award XP based on action type with daily caps.

    Actions:
    - "mood_checkin": 10 XP (first check-in only per day)
    - "expense_log": 5 XP (max 10 XP/day = 2 expenses)
    - "journal_entry": 10 XP (first entry only per day)

    Returns updated gamification status.
    """
    doc = await _get_or_create_gamification(user_id)
    doc = await _reset_daily_if_needed(doc)

    xp_earned = 0
    daily_log = doc["daily_xp_log"]

    if action == "mood_checkin":
        if not daily_log.get("mood_checkin", False):
            xp_earned = XP_MOOD_CHECKIN
            daily_log["mood_checkin"] = True
            # Update streak on mood check-in
            doc = await _update_streak(user_id, doc)
            # Award streak bonus
            streak_bonus = compute_streak_bonus(doc.get("streak_days", 0))
            xp_earned += streak_bonus

    elif action == "expense_log":
        current_count = daily_log.get("expense_count", 0)
        if current_count * XP_EXPENSE_LOG < MAX_EXPENSE_XP_PER_DAY:
            xp_earned = XP_EXPENSE_LOG
            daily_log["expense_count"] = current_count + 1

    elif action == "journal_entry":
        if not daily_log.get("journal_entry", False):
            xp_earned = XP_JOURNAL_ENTRY
            daily_log["journal_entry"] = True

    elif action == "plan_complete":
        if not daily_log.get("plan_complete", False):
            xp_earned = XP_PLAN_COMPLETE
            daily_log["plan_complete"] = True

    if xp_earned > 0:
        doc["total_xp"] = doc.get("total_xp", 0) + xp_earned
        doc["level"] = compute_level(doc["total_xp"])
        doc["daily_xp_log"] = daily_log

        await db[GAMIFICATION_COLLECTION].update_one(
            {"user_id": user_id},
            {"$set": {
                "total_xp": doc["total_xp"],
                "level": doc["level"],
                "daily_xp_log": daily_log,
            }}
        )

    # Check achievements after XP award
    await check_achievements(user_id)

    return {
        "xp_earned": xp_earned,
        "total_xp": doc["total_xp"],
        "level": doc["level"],
        "streak_days": doc.get("streak_days", 0),
    }


async def get_status(user_id: str) -> dict:
    """Return current gamification status for a user."""
    doc = await _get_or_create_gamification(user_id)
    doc = await _reset_daily_if_needed(doc)

    return {
        "total_xp": doc.get("total_xp", 0),
        "level": compute_level(doc.get("total_xp", 0)),
        "streak_days": doc.get("streak_days", 0),
        "last_checkin_date": doc.get("last_checkin_date"),
        "achievements": doc.get("achievements", []),
        "daily_xp_log": doc.get("daily_xp_log", {}),
        "xp_to_next_level": 100 - (doc.get("total_xp", 0) % 100),
    }


async def get_achievements(user_id: str) -> dict:
    """Return all achievements (earned and available) for a user."""
    doc = await _get_or_create_gamification(user_id)
    earned_ids = {a["id"] for a in doc.get("achievements", [])}

    earned = []
    available = []

    for ach in ACHIEVEMENTS:
        if ach["id"] in earned_ids:
            # Find the earned record to get earned_at
            earned_record = next(
                (a for a in doc["achievements"] if a["id"] == ach["id"]), None
            )
            earned.append({
                **ach,
                "earned": True,
                "earned_at": earned_record.get("earned_at") if earned_record else None,
            })
        else:
            available.append({
                **ach,
                "earned": False,
                "earned_at": None,
            })

    return {
        "earned": earned,
        "available": available,
        "total_earned": len(earned),
        "total_available": len(ACHIEVEMENTS),
    }


async def check_achievements(user_id: str) -> list:
    """Check and award any newly earned achievements. Returns list of newly earned."""
    doc = await _get_or_create_gamification(user_id)
    earned_ids = {a["id"] for a in doc.get("achievements", [])}
    newly_earned = []

    # "First Week": streak_days >= 7
    if "first_week" not in earned_ids:
        if doc.get("streak_days", 0) >= 7:
            newly_earned.append({
                "id": "first_week",
                "name": "First Week",
                "earned_at": datetime.now(timezone.utc).isoformat(),
            })

    # "Journal Keeper": total journal entries >= 30
    if "journal_keeper" not in earned_ids:
        journal_count = await db.journal_entries.count_documents({"user_id": user_id})
        if journal_count >= 30:
            newly_earned.append({
                "id": "journal_keeper",
                "name": "Journal Keeper",
                "earned_at": datetime.now(timezone.utc).isoformat(),
            })

    # "Budget Master": user ended a month under budget
    # Placeholder - checks if current total spent < total allocated
    if "budget_master" not in earned_ids:
        budget_cats = await db.budget_categories.find({"user_id": user_id}).to_list(100)
        if budget_cats:
            total_allocated = sum(c.get("allocated", 0) for c in budget_cats)
            total_spent = sum(c.get("spent", 0) for c in budget_cats)
            if total_allocated > 0 and total_spent <= total_allocated:
                # Check if we're at month end (day >= 28)
                today = datetime.now(timezone.utc)
                if today.day >= 28:
                    newly_earned.append({
                        "id": "budget_master",
                        "name": "Budget Master",
                        "earned_at": today.isoformat(),
                    })

    # "Sleep Champion": 7 consecutive nights with sleep hours >= 7
    if "sleep_champion" not in earned_ids:
        sleep_entries = await db.sleep_entries.find(
            {"user_id": user_id}
        ).sort("date", -1).to_list(7)
        if len(sleep_entries) >= 7:
            all_good = all(s.get("hours", 0) >= 7 for s in sleep_entries)
            if all_good:
                newly_earned.append({
                    "id": "sleep_champion",
                    "name": "Sleep Champion",
                    "earned_at": datetime.now(timezone.utc).isoformat(),
                })

    # "Social Butterfly": joined >= 3 study groups
    # Placeholder - checks study_groups collection
    if "social_butterfly" not in earned_ids:
        group_count = await db.study_groups.count_documents(
            {"members": {"$in": [user_id]}}
        )
        if group_count >= 3:
            newly_earned.append({
                "id": "social_butterfly",
                "name": "Social Butterfly",
                "earned_at": datetime.now(timezone.utc).isoformat(),
            })

    # Persist newly earned achievements
    if newly_earned:
        await db[GAMIFICATION_COLLECTION].update_one(
            {"user_id": user_id},
            {"$push": {"achievements": {"$each": newly_earned}}}
        )

    return newly_earned
