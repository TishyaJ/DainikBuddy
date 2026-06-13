"""
Notification Router for PocketBuddy.
Provides endpoints for notification management, preferences, and push subscriptions.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from jwt_middleware import get_current_user
import notification_service

notification_router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class DismissRequest(BaseModel):
    """Request body for dismissing a notification (optional, ID is in path)."""
    pass


class PreferencesUpdate(BaseModel):
    """Request body for updating notification preferences."""
    budget_alerts: Optional[bool] = None
    wellness_reminders: Optional[bool] = None
    streak_celebrations: Optional[bool] = None
    social_updates: Optional[bool] = None


class PushSubscription(BaseModel):
    """Push notification subscription data from the browser."""
    endpoint: str
    keys: Dict[str, Any]


@notification_router.get("")
async def get_notifications(user_id: str = Depends(get_current_user)):
    """Get the user's recent notifications (limit 20)."""
    notifications = await notification_service.get_notifications(user_id)
    return {"notifications": notifications, "count": len(notifications)}


@notification_router.post("/{notification_id}/dismiss")
async def dismiss_notification(notification_id: str, user_id: str = Depends(get_current_user)):
    """
    Dismiss a notification.
    Applies frequency adaptation:
    - Single dismissal: 50% reduction for 7 days
    - 3+ dismissals of same type in 7 days: suppress for 14 days
    """
    result = await notification_service.dismiss_notification(user_id, notification_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "dismissed", "notification": result}


@notification_router.get("/preferences")
async def get_preferences(user_id: str = Depends(get_current_user)):
    """Get notification preferences for the current user."""
    prefs = await notification_service.get_preferences(user_id)
    return prefs


@notification_router.patch("/preferences")
async def update_preferences(
    updates: PreferencesUpdate,
    user_id: str = Depends(get_current_user),
):
    """Update notification preferences (enable/disable per category)."""
    update_dict = updates.model_dump(exclude_none=True)
    prefs = await notification_service.update_preferences(user_id, update_dict)
    return prefs


@notification_router.post("/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    user_id: str = Depends(get_current_user),
):
    """
    Register a push notification subscription.
    Stores the browser push subscription for delivering nudges
    when the app is not in the foreground.
    """
    sub_data = subscription.model_dump()
    result = await notification_service.save_push_subscription(user_id, sub_data)
    return result


@notification_router.post("/evaluate")
async def evaluate_nudges(user_id: str = Depends(get_current_user)):
    """
    Evaluate all nudge conditions for the current user.
    Triggers checks for budget warnings, wellness nudges, and check-in reminders.
    Returns any newly generated notifications.
    """
    generated = await notification_service.evaluate_nudges(user_id)
    return {"generated": generated, "count": len(generated)}
