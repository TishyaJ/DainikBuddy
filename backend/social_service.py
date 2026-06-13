"""
Social Service for PocketBuddy.
Handles study group creation, invite codes, join/leave logic,
shared goals with leaderboards, community challenges, and milestone notifications.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import os
import uuid
import string
import random
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

GROUPS_COLLECTION = "study_groups"
SHARED_GOALS_COLLECTION = "shared_goals"
CHALLENGES_COLLECTION = "community_challenges"
NOTIFICATIONS_COLLECTION = "notifications"
GAMIFICATION_COLLECTION = "gamification"

MAX_MEMBERS_PER_GROUP = 20
CHALLENGE_XP_REWARD = 50
MILESTONE_THRESHOLDS = [25, 50, 75, 100]


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def _generate_invite_code() -> str:
    """Generate a 6-character alphanumeric invite code."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


async def _get_user_display_name(user_id: str) -> str:
    """Get display name from user_profiles collection."""
    profile = await db.user_profiles.find_one({"user_id": user_id})
    if profile:
        return profile.get("name", "User")
    return "User"


async def _get_user_level(user_id: str) -> int:
    """Get user's gamification level."""
    doc = await db[GAMIFICATION_COLLECTION].find_one({"user_id": user_id})
    if doc:
        import math
        return math.floor(doc.get("total_xp", 0) / 100) + 1
    return 1


async def _create_notification(user_id: str, title: str, body: str,
                                notif_type: str = "social_update",
                                metadata: dict = None) -> dict:
    """Create a notification for a user."""
    notification = {
        "id": _generate_id(),
        "user_id": user_id,
        "type": notif_type,
        "title": title,
        "body": body,
        "category": "social",
        "read": False,
        "dismissed": False,
        "created_at": now_iso(),
        "metadata": metadata or {},
    }
    await db[NOTIFICATIONS_COLLECTION].insert_one(notification)
    return notification


# ============ STUDY GROUPS ============

async def create_group(user_id: str, name: str) -> dict:
    """Create a new study group with a unique invite code."""
    display_name = await _get_user_display_name(user_id)
    level = await _get_user_level(user_id)

    # Generate a unique invite code
    invite_code = _generate_invite_code()
    while await db[GROUPS_COLLECTION].find_one({"invite_code": invite_code}):
        invite_code = _generate_invite_code()

    group = {
        "id": _generate_id(),
        "name": name,
        "invite_code": invite_code,
        "creator_id": user_id,
        "members": [
            {
                "user_id": user_id,
                "display_name": display_name,
                "level": level,
                "joined_at": now_iso(),
            }
        ],
        "created_at": now_iso(),
        "max_members": MAX_MEMBERS_PER_GROUP,
    }
    await db[GROUPS_COLLECTION].insert_one(group)
    group.pop("_id", None)
    return group


async def get_group(group_id: str, user_id: str) -> dict | None:
    """
    Get group details. Only members can view.
    Privacy: only display_name, level, and shared goal progress visible.
    """
    group = await db[GROUPS_COLLECTION].find_one({"id": group_id})
    if not group:
        return None

    # Check if user is a member
    member_ids = [m["user_id"] for m in group.get("members", [])]
    if user_id not in member_ids:
        return None

    group.pop("_id", None)

    # Privacy enforcement: only show display_name, level for members
    safe_members = [
        {
            "user_id": m["user_id"],
            "display_name": m["display_name"],
            "level": m["level"],
            "joined_at": m["joined_at"],
        }
        for m in group.get("members", [])
    ]
    group["members"] = safe_members

    # Get shared goals progress
    goals = await get_group_goals(group_id)
    group["shared_goals"] = goals

    # Activity feed (20 recent items)
    activity = await _get_activity_feed(group_id, limit=20)
    group["activity_feed"] = activity

    return group


async def get_user_groups(user_id: str) -> list:
    """Get all groups the user is a member of."""
    cursor = db[GROUPS_COLLECTION].find(
        {"members.user_id": user_id}
    )
    groups = []
    async for doc in cursor:
        doc.pop("_id", None)
        # Privacy: only show display_name and level
        doc["members"] = [
            {
                "user_id": m["user_id"],
                "display_name": m["display_name"],
                "level": m["level"],
                "joined_at": m["joined_at"],
            }
            for m in doc.get("members", [])
        ]
        groups.append(doc)
    return groups


async def join_group_by_invite(user_id: str, invite_code: str) -> dict | None:
    """Join a group using an invite code. Returns error dict or group."""
    group = await db[GROUPS_COLLECTION].find_one({"invite_code": invite_code})
    if not group:
        return {"error": "Invalid or expired invite code"}

    # Check if already a member
    member_ids = [m["user_id"] for m in group.get("members", [])]
    if user_id in member_ids:
        return {"error": "Already a member of this group"}

    # Check max members
    if len(group.get("members", [])) >= group.get("max_members", MAX_MEMBERS_PER_GROUP):
        return {"error": "Group is full (maximum 20 members)"}

    display_name = await _get_user_display_name(user_id)
    level = await _get_user_level(user_id)

    new_member = {
        "user_id": user_id,
        "display_name": display_name,
        "level": level,
        "joined_at": now_iso(),
    }

    await db[GROUPS_COLLECTION].update_one(
        {"id": group["id"]},
        {"$push": {"members": new_member}}
    )

    # Log activity
    await _log_activity(group["id"], user_id, "joined", f"{display_name} joined the group")

    group.pop("_id", None)
    group["members"].append(new_member)
    return group


async def join_group_by_id(user_id: str, group_id: str) -> dict | None:
    """Join a group by its ID (for direct join via link)."""
    group = await db[GROUPS_COLLECTION].find_one({"id": group_id})
    if not group:
        return {"error": "Group not found"}

    member_ids = [m["user_id"] for m in group.get("members", [])]
    if user_id in member_ids:
        return {"error": "Already a member of this group"}

    if len(group.get("members", [])) >= group.get("max_members", MAX_MEMBERS_PER_GROUP):
        return {"error": "Group is full (maximum 20 members)"}

    display_name = await _get_user_display_name(user_id)
    level = await _get_user_level(user_id)

    new_member = {
        "user_id": user_id,
        "display_name": display_name,
        "level": level,
        "joined_at": now_iso(),
    }

    await db[GROUPS_COLLECTION].update_one(
        {"id": group_id},
        {"$push": {"members": new_member}}
    )

    await _log_activity(group_id, user_id, "joined", f"{display_name} joined the group")

    group.pop("_id", None)
    group["members"].append(new_member)
    return group


async def leave_group(user_id: str, group_id: str) -> dict:
    """
    Leave a group. Removes user from member list and leaderboards.
    Retains personal XP/badges earned.
    """
    group = await db[GROUPS_COLLECTION].find_one({"id": group_id})
    if not group:
        return {"error": "Group not found"}

    member_ids = [m["user_id"] for m in group.get("members", [])]
    if user_id not in member_ids:
        return {"error": "Not a member of this group"}

    display_name = await _get_user_display_name(user_id)

    # Remove from members list
    await db[GROUPS_COLLECTION].update_one(
        {"id": group_id},
        {"$pull": {"members": {"user_id": user_id}}}
    )

    # Remove from shared goals progress (leaderboards)
    await db[SHARED_GOALS_COLLECTION].update_many(
        {"group_id": group_id},
        {"$pull": {"progress": {"user_id": user_id}}}
    )

    # Log activity
    await _log_activity(group_id, user_id, "left", f"{display_name} left the group")

    return {"status": "left", "group_id": group_id}


# ============ SHARED GOALS ============

async def create_shared_goal(user_id: str, group_id: str, title: str, target: float) -> dict | None:
    """Create a shared goal for a group."""
    group = await db[GROUPS_COLLECTION].find_one({"id": group_id})
    if not group:
        return None

    # Verify user is a member
    member_ids = [m["user_id"] for m in group.get("members", [])]
    if user_id not in member_ids:
        return None

    display_name = await _get_user_display_name(user_id)

    goal = {
        "id": _generate_id(),
        "group_id": group_id,
        "title": title,
        "target": target,
        "created_by": user_id,
        "progress": [
            {
                "user_id": user_id,
                "display_name": display_name,
                "current": 0,
                "updated_at": now_iso(),
            }
        ],
        "created_at": now_iso(),
    }
    await db[SHARED_GOALS_COLLECTION].insert_one(goal)
    goal.pop("_id", None)

    await _log_activity(group_id, user_id, "goal_created", f"{display_name} created goal: {title}")

    return goal


async def update_goal_progress(user_id: str, goal_id: str, current: float) -> dict | None:
    """Update a user's progress on a shared goal. Triggers milestone notifications."""
    goal = await db[SHARED_GOALS_COLLECTION].find_one({"id": goal_id})
    if not goal:
        return None

    group_id = goal["group_id"]
    group = await db[GROUPS_COLLECTION].find_one({"id": group_id})
    if not group:
        return None

    # Verify user is a member of the group
    member_ids = [m["user_id"] for m in group.get("members", [])]
    if user_id not in member_ids:
        return None

    display_name = await _get_user_display_name(user_id)
    target = goal.get("target", 1)

    # Get previous progress
    old_progress_entry = next(
        (p for p in goal.get("progress", []) if p["user_id"] == user_id), None
    )
    old_current = old_progress_entry["current"] if old_progress_entry else 0
    old_pct = (old_current / target * 100) if target > 0 else 0

    # Cap current to target
    current = min(current, target)
    new_pct = (current / target * 100) if target > 0 else 0

    # Update or insert progress entry
    if old_progress_entry:
        await db[SHARED_GOALS_COLLECTION].update_one(
            {"id": goal_id, "progress.user_id": user_id},
            {"$set": {
                "progress.$.current": current,
                "progress.$.display_name": display_name,
                "progress.$.updated_at": now_iso(),
            }}
        )
    else:
        await db[SHARED_GOALS_COLLECTION].update_one(
            {"id": goal_id},
            {"$push": {"progress": {
                "user_id": user_id,
                "display_name": display_name,
                "current": current,
                "updated_at": now_iso(),
            }}}
        )

    # Check milestone notifications (25%, 50%, 75%, 100%)
    for threshold in MILESTONE_THRESHOLDS:
        if old_pct < threshold <= new_pct:
            await _broadcast_milestone(
                group=group,
                user_id=user_id,
                display_name=display_name,
                goal_title=goal["title"],
                milestone=threshold,
            )

    # Refresh the goal
    updated_goal = await db[SHARED_GOALS_COLLECTION].find_one({"id": goal_id})
    updated_goal.pop("_id", None)
    return updated_goal


async def get_group_goals(group_id: str) -> list:
    """
    Get all shared goals for a group with leaderboard.
    Sorted by completion percentage descending.
    """
    goals = await db[SHARED_GOALS_COLLECTION].find(
        {"group_id": group_id}
    ).to_list(100)

    result = []
    for goal in goals:
        goal.pop("_id", None)
        target = goal.get("target", 1)

        # Build leaderboard sorted by completion percentage descending
        progress = goal.get("progress", [])
        leaderboard = []
        for p in progress:
            pct = (p["current"] / target * 100) if target > 0 else 0
            leaderboard.append({
                "user_id": p["user_id"],
                "display_name": p["display_name"],
                "current": p["current"],
                "percentage": round(pct, 1),
                "updated_at": p.get("updated_at"),
            })
        leaderboard.sort(key=lambda x: x["percentage"], reverse=True)
        goal["leaderboard"] = leaderboard
        result.append(goal)

    return result


# ============ COMMUNITY CHALLENGES ============

async def get_active_challenges() -> list:
    """Get current week's active challenges."""
    now = datetime.now(timezone.utc)
    challenges = await db[CHALLENGES_COLLECTION].find(
        {
            "start_date": {"$lte": now.isoformat()},
            "end_date": {"$gte": now.isoformat()},
        }
    ).to_list(50)

    for c in challenges:
        c.pop("_id", None)
    return challenges


async def create_challenge(title: str, description: str, challenge_type: str,
                           criteria: dict, badge_id: str) -> dict:
    """Create a weekly community challenge (Monday 00:00 UTC to Sunday 23:59 UTC)."""
    now = datetime.now(timezone.utc)
    # Find the current week's Monday 00:00 UTC
    days_since_monday = now.weekday()
    monday = now - timedelta(days=days_since_monday)
    start_date = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    # Sunday 23:59 UTC
    end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)

    challenge = {
        "id": _generate_id(),
        "title": title,
        "description": description,
        "type": challenge_type,
        "criteria": criteria,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "participants": [],
        "badge_id": badge_id,
        "xp_reward": CHALLENGE_XP_REWARD,
    }
    await db[CHALLENGES_COLLECTION].insert_one(challenge)
    challenge.pop("_id", None)
    return challenge


async def join_challenge(user_id: str, challenge_id: str) -> dict | None:
    """Join a community challenge."""
    challenge = await db[CHALLENGES_COLLECTION].find_one({"id": challenge_id})
    if not challenge:
        return {"error": "Challenge not found"}

    # Check if challenge is still active
    now = datetime.now(timezone.utc)
    end_date = datetime.fromisoformat(challenge["end_date"])
    if now > end_date:
        return {"error": "Challenge has ended"}

    # Check if already joined
    participants = challenge.get("participants", [])
    if any(p["user_id"] == user_id for p in participants):
        return {"error": "Already joined this challenge"}

    participant = {
        "user_id": user_id,
        "completed": False,
        "progress": 0,
    }

    await db[CHALLENGES_COLLECTION].update_one(
        {"id": challenge_id},
        {"$push": {"participants": participant}}
    )

    challenge.pop("_id", None)
    challenge["participants"].append(participant)
    return challenge


async def complete_challenge(user_id: str, challenge_id: str) -> dict | None:
    """
    Mark a challenge as completed for a user.
    Awards 50 XP + challenge-specific badge.
    """
    challenge = await db[CHALLENGES_COLLECTION].find_one({"id": challenge_id})
    if not challenge:
        return None

    # Check user is a participant
    participants = challenge.get("participants", [])
    participant = next((p for p in participants if p["user_id"] == user_id), None)
    if not participant:
        return None

    if participant.get("completed"):
        return {"status": "already_completed"}

    # Mark as completed
    await db[CHALLENGES_COLLECTION].update_one(
        {"id": challenge_id, "participants.user_id": user_id},
        {"$set": {
            "participants.$.completed": True,
            "participants.$.progress": 100,
        }}
    )

    # Award 50 XP directly to gamification doc
    await db[GAMIFICATION_COLLECTION].update_one(
        {"user_id": user_id},
        {"$inc": {"total_xp": CHALLENGE_XP_REWARD}},
        upsert=True,
    )

    # Award badge
    badge_id = challenge.get("badge_id")
    if badge_id:
        badge = {
            "id": badge_id,
            "name": f"Challenge: {challenge['title']}",
            "earned_at": now_iso(),
        }
        await db[GAMIFICATION_COLLECTION].update_one(
            {"user_id": user_id},
            {"$push": {"achievements": badge}},
            upsert=True,
        )

    return {
        "status": "completed",
        "xp_awarded": CHALLENGE_XP_REWARD,
        "badge_id": badge_id,
        "challenge_title": challenge["title"],
    }


async def update_challenge_progress(user_id: str, challenge_id: str, progress: float) -> dict | None:
    """Update user's progress on a challenge. Auto-completes at 100%."""
    challenge = await db[CHALLENGES_COLLECTION].find_one({"id": challenge_id})
    if not challenge:
        return None

    participant = next(
        (p for p in challenge.get("participants", []) if p["user_id"] == user_id), None
    )
    if not participant:
        return None

    progress = min(progress, 100)

    await db[CHALLENGES_COLLECTION].update_one(
        {"id": challenge_id, "participants.user_id": user_id},
        {"$set": {"participants.$.progress": progress}}
    )

    # Auto-complete at 100%
    if progress >= 100 and not participant.get("completed"):
        return await complete_challenge(user_id, challenge_id)

    challenge.pop("_id", None)
    return challenge


# ============ INTERNAL HELPERS ============

async def _broadcast_milestone(group: dict, user_id: str, display_name: str,
                                goal_title: str, milestone: int):
    """Broadcast milestone notification to all OTHER group members."""
    members = group.get("members", [])
    for member in members:
        if member["user_id"] != user_id:
            title = f"🎯 Goal Milestone!"
            body = (
                f"{display_name} reached {milestone}% on \"{goal_title}\"!"
            )
            await _create_notification(
                user_id=member["user_id"],
                title=title,
                body=body,
                notif_type="social_update",
                metadata={
                    "milestone": milestone,
                    "goal_title": goal_title,
                    "achieved_by": display_name,
                    "group_id": group["id"],
                },
            )


async def _log_activity(group_id: str, user_id: str, action: str, description: str):
    """Log an activity event for the group feed."""
    activity = {
        "id": _generate_id(),
        "group_id": group_id,
        "user_id": user_id,
        "action": action,
        "description": description,
        "created_at": now_iso(),
    }
    await db["group_activities"].insert_one(activity)


async def _get_activity_feed(group_id: str, limit: int = 20) -> list:
    """Get recent activity feed for a group."""
    cursor = db["group_activities"].find(
        {"group_id": group_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit)

    activities = []
    async for doc in cursor:
        activities.append(doc)
    return activities
