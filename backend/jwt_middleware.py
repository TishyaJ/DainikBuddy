"""
JWT Authentication Middleware for PocketBuddy.
Provides a FastAPI dependency to extract and verify user identity from JWT tokens.
"""

from fastapi import Depends, HTTPException, Header
from typing import Optional

from auth_service import verify_access_token


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency that extracts user_id from a valid JWT access token.

    Reads the Authorization header, expects 'Bearer <token>' format.
    Returns the user_id (from payload['sub']) if valid.
    Raises HTTPException(401) if missing, malformed, or invalid/expired.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]

    payload = verify_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id
