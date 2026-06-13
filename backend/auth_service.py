"""
Authentication service module for PocketBuddy.
Handles password hashing, JWT creation/verification, and token management.
"""

import bcrypt
import jwt
import uuid
import os
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any


# Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "pocketbuddy-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRY_HOURS = 24
REFRESH_TOKEN_EXPIRY_DAYS = 30
BCRYPT_COST = 12
PASSWORD_RESET_EXPIRY_MINUTES = 15


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


# ============ PASSWORD HASHING ============

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=BCRYPT_COST)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


# ============ JWT TOKENS ============

def create_access_token(user_id: str, email: str) -> str:
    """Create a JWT access token with 24-hour expiry."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token with 30-day expiry."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode an access token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a refresh token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ============ REFRESH TOKEN HASH ============

def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for storage (using SHA-256)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ============ PASSWORD RESET TOKEN ============

def generate_reset_token() -> str:
    """Generate a secure random token for password reset."""
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    """Hash a reset token for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ============ VALIDATION ============

def validate_email(email: str) -> tuple[bool, str]:
    """
    Validate email format and length.
    Returns (is_valid, error_message).
    """
    if not email or len(email) > 254:
        return False, "Email must be between 1 and 254 characters"

    # Basic email format check
    import re
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    if not email_pattern.match(email):
        return False, "Invalid email format"

    return True, ""


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password requirements:
    - 8-128 characters
    - At least 1 uppercase letter
    - At least 1 number
    Returns (is_valid, error_message).
    """
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"

    if len(password) > 128:
        return False, "Password must be at most 128 characters"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    return True, ""


# ============ RATE LIMITING ============

def is_account_locked(locked_until: Optional[str]) -> bool:
    """Check if an account is currently locked."""
    if not locked_until:
        return False
    try:
        lock_time = datetime.fromisoformat(locked_until)
        return datetime.now(timezone.utc) < lock_time
    except (ValueError, TypeError):
        return False


def get_lock_until() -> str:
    """Get the ISO timestamp for 15 minutes from now (lock duration)."""
    return (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
