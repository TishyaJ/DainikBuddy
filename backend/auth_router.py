"""
Authentication router for PocketBuddy.
Provides registration, login, token refresh, password reset, account deletion, and data export.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    hash_refresh_token,
    generate_reset_token,
    hash_reset_token,
    validate_email,
    validate_password,
    is_account_locked,
    get_lock_until,
    now_iso,
)

logger = logging.getLogger(__name__)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])


# ============ REQUEST/RESPONSE MODELS ============

class RegisterRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


class DeleteAccountRequest(BaseModel):
    password: str


# ============ DATABASE REFERENCE ============
# This will be set by server.py when including the router
db = None


def set_db(database):
    """Set the database reference. Called from server.py."""
    global db
    db = database


# ============ RATE LIMITING CONSTANTS ============
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15


# ============ ENDPOINTS ============

@auth_router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Register a new user account."""
    # Validate email
    email_valid, email_error = validate_email(req.email)
    if not email_valid:
        raise HTTPException(status_code=400, detail=email_error)

    # Validate password
    pwd_valid, pwd_error = validate_password(req.password)
    if not pwd_valid:
        raise HTTPException(status_code=400, detail=pwd_error)

    # Normalize email
    email = req.email.strip().lower()

    # Check for duplicate email
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    # Create user
    user_id = str(uuid.uuid4())
    password_hash = hash_password(req.password)

    # Generate tokens
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    refresh_token_hashed = hash_refresh_token(refresh_token)

    now = now_iso()
    user_doc = {
        "id": user_id,
        "email": email,
        "password_hash": password_hash,
        "created_at": now,
        "updated_at": now,
        "last_login_at": now,
        "failed_login_attempts": 0,
        "locked_until": None,
        "refresh_token_hash": refresh_token_hashed,
        "push_subscription": None,
    }

    await db.users.insert_one(user_doc)

    logger.info(f"New user registered: {email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Login with email and password."""
    email = req.email.strip().lower()

    # Find user
    user = await db.users.find_one({"email": email})

    if not user:
        # Generic error - don't reveal whether email exists
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if account is locked
    if is_account_locked(user.get("locked_until")):
        raise HTTPException(
            status_code=429,
            detail="Account temporarily locked due to too many failed attempts. Please try again later."
        )

    # Check if we need to reset failed attempts (window expired)
    failed_attempts = user.get("failed_login_attempts", 0)
    if failed_attempts > 0:
        # Check if the lockout window has passed since last failed attempt
        updated_at = user.get("updated_at", "")
        if updated_at:
            try:
                last_update = datetime.fromisoformat(updated_at)
                window_end = last_update + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
                if datetime.now(timezone.utc) > window_end:
                    # Reset failed attempts - window expired
                    failed_attempts = 0
                    await db.users.update_one(
                        {"id": user["id"]},
                        {"$set": {"failed_login_attempts": 0, "updated_at": now_iso()}}
                    )
            except (ValueError, TypeError):
                pass

    # Verify password
    if not verify_password(req.password, user["password_hash"]):
        # Increment failed attempts
        new_attempts = failed_attempts + 1
        update_fields = {
            "failed_login_attempts": new_attempts,
            "updated_at": now_iso(),
        }

        # Lock account if max attempts reached
        if new_attempts >= MAX_FAILED_ATTEMPTS:
            update_fields["locked_until"] = get_lock_until()
            logger.warning(f"Account locked for {email} after {new_attempts} failed attempts")

        await db.users.update_one({"id": user["id"]}, {"$set": update_fields})

        # Generic error message - no field hints
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Successful login - reset failed attempts
    access_token = create_access_token(user["id"], email)
    refresh_token = create_refresh_token(user["id"])
    refresh_token_hashed = hash_refresh_token(refresh_token)

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login_at": now_iso(),
            "updated_at": now_iso(),
            "refresh_token_hash": refresh_token_hashed,
        }}
    )

    logger.info(f"User logged in: {email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest):
    """Refresh access token using a valid refresh token."""
    # Verify the refresh token
    payload = verify_refresh_token(req.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Find user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Verify the refresh token hash matches what's stored
    stored_hash = user.get("refresh_token_hash")
    if not stored_hash or stored_hash != hash_refresh_token(req.refresh_token):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    # Issue new tokens
    access_token = create_access_token(user["id"], user["email"])
    new_refresh_token = create_refresh_token(user["id"])
    new_refresh_hash = hash_refresh_token(new_refresh_token)

    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "refresh_token_hash": new_refresh_hash,
            "updated_at": now_iso(),
        }}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@auth_router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(req: ForgotPasswordRequest):
    """
    Request a password reset link.
    Always returns success message regardless of whether email exists (security).
    """
    email = req.email.strip().lower()

    # Always return same message whether email exists or not
    success_message = "If an account with that email exists, a password reset link has been sent."

    user = await db.users.find_one({"email": email})
    if not user:
        # Don't reveal that email doesn't exist
        return MessageResponse(message=success_message)

    # Generate reset token
    reset_token = generate_reset_token()
    reset_token_hashed = hash_reset_token(reset_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

    # Store reset token in database
    await db.password_resets.insert_one({
        "user_id": user["id"],
        "token_hash": reset_token_hashed,
        "expires_at": expires_at,
        "used": False,
        "created_at": now_iso(),
    })

    # Log the reset link (mock email sending)
    logger.info(f"[MOCK EMAIL] Password reset token for {email}: {reset_token}")
    logger.info(f"[MOCK EMAIL] Reset link: http://localhost:3000/reset-password?token={reset_token}")

    return MessageResponse(message=success_message)


@auth_router.post("/reset-password", response_model=MessageResponse)
async def reset_password(req: ResetPasswordRequest):
    """Reset password using a valid reset token."""
    # Validate new password
    pwd_valid, pwd_error = validate_password(req.new_password)
    if not pwd_valid:
        raise HTTPException(status_code=400, detail=pwd_error)

    # Find the reset token
    token_hash = hash_reset_token(req.token)
    reset_doc = await db.password_resets.find_one({
        "token_hash": token_hash,
        "used": False,
    })

    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Check expiry
    try:
        expires_at = datetime.fromisoformat(reset_doc["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Update password
    new_hash = hash_password(req.new_password)
    await db.users.update_one(
        {"id": reset_doc["user_id"]},
        {"$set": {
            "password_hash": new_hash,
            "updated_at": now_iso(),
            "failed_login_attempts": 0,
            "locked_until": None,
            "refresh_token_hash": None,  # Invalidate existing sessions
        }}
    )

    # Mark token as used
    await db.password_resets.update_one(
        {"_id": reset_doc["_id"]},
        {"$set": {"used": True}}
    )

    logger.info(f"Password reset successful for user_id: {reset_doc['user_id']}")

    return MessageResponse(message="Password has been reset successfully. Please log in with your new password.")


@auth_router.post("/delete-account", response_model=MessageResponse)
async def delete_account(req: DeleteAccountRequest, request: Request):
    """Delete user account. Requires password confirmation."""
    # Get user from token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header.split(" ", 1)[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify password
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # Delete user data from all collections
    email = user["email"]
    await db.users.delete_one({"id": user_id})
    await db.password_resets.delete_many({"user_id": user_id})

    # Delete user data from domain collections
    for collection in [
        "mood_entries", "expenses", "journal_entries", "goals",
        "budget_categories", "subscriptions", "savings_goals",
        "split_bills", "sleep_entries", "chat_messages",
        "user_profiles", "tasks", "task_sessions",
        "exercises", "exercise_sessions",
    ]:
        await db[collection].delete_many({"user_id": user_id})

    logger.info(f"Account deleted: {email}")

    return MessageResponse(message="Account and all associated data have been permanently deleted.")


@auth_router.get("/export-data")
async def export_data(request: Request):
    """Export all user data as JSON."""
    # Get user from token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")

    token = auth_header.split(" ", 1)[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload.get("sub")
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Collect all user data
    export = {
        "account": user,
        "mood_entries": await db.mood_entries.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "expenses": await db.expenses.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "journal_entries": await db.journal_entries.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "goals": await db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "budget_categories": await db.budget_categories.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "subscriptions": await db.subscriptions.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "savings_goals": await db.savings_goals.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "split_bills": await db.split_bills.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "sleep_entries": await db.sleep_entries.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "tasks": await db.tasks.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "exercises": await db.exercises.find({"user_id": user_id}, {"_id": 0}).to_list(None),
        "exported_at": now_iso(),
    }

    return export
