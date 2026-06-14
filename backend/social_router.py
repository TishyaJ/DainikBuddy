"""
Social Router for PocketBuddy.
Provides endpoints for study groups, shared goals, and community challenges.
"""

from fastapi import APIRouter, Depends, HTTPException
from jwt_middleware import get_current_user
from pydantic import BaseModel
from typing import Optional
import social_service

social_router = APIRouter(prefix="/api/social", tags=["social"])


# ============ REQUEST MODELS ============

class CreateGroupRequest(BaseModel):
    name: str


class JoinByInviteRequest(BaseModel):
    invite_code: str


class CreateGoalRequest(BaseModel):
    title: str
    target: float


class UpdateProgressRequest(BaseModel):
    current: float


class CreateChallengeRequest(BaseModel):
    title: str
    description: str
    type: str  # finance | wellness | productivity
    criteria: dict = {}
    badge_id: str = ""


class UpdateChallengeProgressRequest(BaseModel):
    progress: float


class CompleteChallengeRequest(BaseModel):
    mood: Optional[int] = None  # 1-5 emotion scale
    reflection: Optional[str] = None  # max 200 chars


# ============ STUDY GROUPS ============

@social_router.get("/groups")
async def list_groups(user_id: str = Depends(get_current_user)):
    """Get all groups the current user is a member of."""
    return await social_service.get_user_groups(user_id)


@social_router.post("/groups")
async def create_group(req: CreateGroupRequest, user_id: str = Depends(get_current_user)):
    """Create a new study group with a unique 6-char invite code."""
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Group name is required")
    group = await social_service.create_group(user_id, req.name.strip())
    return group


@social_router.get("/groups/{group_id}")
async def get_group(group_id: str, user_id: str = Depends(get_current_user)):
    """
    Get group details including members, shared goals, and activity feed.
    Only accessible to group members. Privacy enforced.
    """
    group = await social_service.get_group(group_id, user_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found or you are not a member")
    return group


@social_router.post("/groups/join")
async def join_group_by_invite(req: JoinByInviteRequest, user_id: str = Depends(get_current_user)):
    """Join a group using a 6-character invite code."""
    result = await social_service.join_group_by_invite(user_id, req.invite_code.strip())
    if result and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@social_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user_id: str = Depends(get_current_user)):
    """Join a group by its ID."""
    result = await social_service.join_group_by_id(user_id, group_id)
    if result and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@social_router.post("/groups/{group_id}/leave")
async def leave_group(group_id: str, user_id: str = Depends(get_current_user)):
    """
    Leave a group. Removes from member list and leaderboards.
    Personal XP and badges are retained.
    """
    result = await social_service.leave_group(user_id, group_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============ SHARED GOALS ============

@social_router.get("/groups/{group_id}/goals")
async def get_group_goals(group_id: str, user_id: str = Depends(get_current_user)):
    """Get shared goals with leaderboard sorted by completion percentage descending."""
    # Verify membership
    group = await social_service.get_group(group_id, user_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found or you are not a member")
    return await social_service.get_group_goals(group_id)


@social_router.post("/groups/{group_id}/goals")
async def create_shared_goal(group_id: str, req: CreateGoalRequest,
                             user_id: str = Depends(get_current_user)):
    """Create a shared goal for the group."""
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Goal title is required")
    if req.target <= 0:
        raise HTTPException(status_code=400, detail="Target must be positive")

    goal = await social_service.create_shared_goal(user_id, group_id, req.title.strip(), req.target)
    if not goal:
        raise HTTPException(status_code=404, detail="Group not found or you are not a member")
    return goal


@social_router.patch("/groups/{group_id}/goals/{goal_id}")
async def update_goal_progress(group_id: str, goal_id: str, req: UpdateProgressRequest,
                               user_id: str = Depends(get_current_user)):
    """
    Update progress on a shared goal. Triggers milestone notifications
    (25%, 50%, 75%, 100%) broadcast to all other group members.
    """
    result = await social_service.update_goal_progress(user_id, goal_id, req.current)
    if not result:
        raise HTTPException(status_code=404, detail="Goal not found or you are not a member")
    return result


# ============ COMMUNITY CHALLENGES ============

@social_router.get("/challenges")
async def list_challenges(user_id: str = Depends(get_current_user)):
    """Get current week's active community challenges with user participation info."""
    challenges = await social_service.get_active_challenges()
    # Add 'joined' flag for the current user
    for c in challenges:
        participants = c.get("participants", [])
        participant = next((p for p in participants if p.get("user_id") == user_id), None)
        c["joined"] = participant is not None
        c["completed"] = participant.get("completed", False) if participant else False
    return challenges


@social_router.post("/challenges")
async def create_challenge(req: CreateChallengeRequest, user_id: str = Depends(get_current_user)):
    """Create a new weekly community challenge."""
    if req.type not in ("finance", "wellness", "productivity"):
        raise HTTPException(status_code=400, detail="Type must be finance, wellness, or productivity")
    challenge = await social_service.create_challenge(
        title=req.title,
        description=req.description,
        challenge_type=req.type,
        criteria=req.criteria,
        badge_id=req.badge_id,
        creator_id=user_id,
    )
    return challenge


@social_router.post("/challenges/{challenge_id}/join")
async def join_challenge(challenge_id: str, user_id: str = Depends(get_current_user)):
    """Join a community challenge."""
    result = await social_service.join_challenge(user_id, challenge_id)
    if result and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@social_router.patch("/challenges/{challenge_id}/progress")
async def update_challenge_progress(challenge_id: str, req: UpdateChallengeProgressRequest,
                                    user_id: str = Depends(get_current_user)):
    """Update progress on a challenge. Auto-completes at 100% and awards 50 XP + badge."""
    result = await social_service.update_challenge_progress(user_id, challenge_id, req.progress)
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found or not joined")
    return result


@social_router.post("/challenges/{challenge_id}/complete")
async def complete_challenge(challenge_id: str, req: CompleteChallengeRequest,
                             user_id: str = Depends(get_current_user)):
    """Mark a challenge as completed. Optionally accepts mood (1-5) and reflection text."""
    if req.mood is not None and not (1 <= req.mood <= 5):
        raise HTTPException(status_code=400, detail="Mood must be between 1 and 5")
    if req.reflection and len(req.reflection) > 200:
        raise HTTPException(status_code=400, detail="Reflection must be 200 characters or less")
    result = await social_service.complete_challenge_with_reflection(
        user_id, challenge_id, mood=req.mood, reflection=req.reflection
    )
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found or not joined")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@social_router.post("/challenges/{challenge_id}/close")
async def close_challenge(challenge_id: str, user_id: str = Depends(get_current_user)):
    """Close a challenge early. Only the creator can close."""
    result = await social_service.close_challenge(user_id, challenge_id)
    if not result:
        raise HTTPException(status_code=404, detail="Challenge not found")
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result
