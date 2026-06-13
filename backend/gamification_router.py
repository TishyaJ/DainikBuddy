"""
Gamification Router for PocketBuddy.
Provides endpoints for gamification status and achievements.
"""

from fastapi import APIRouter, Depends
from jwt_middleware import get_current_user
import gamification_service

gamification_router = APIRouter(prefix="/api/gamification", tags=["gamification"])


@gamification_router.get("/status")
async def gamification_status(user_id: str = Depends(get_current_user)):
    """Get the current user's gamification status (XP, level, streak, achievements)."""
    return await gamification_service.get_status(user_id)


@gamification_router.get("/achievements")
async def gamification_achievements(user_id: str = Depends(get_current_user)):
    """Get all achievements (earned and available) for the current user."""
    return await gamification_service.get_achievements(user_id)
