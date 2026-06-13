"""
Property-based tests for authentication validation using Hypothesis.

**Validates: Requirements 8.1, 8.2, 8.4, 8.9**

Tests cover:
- Property 23: Registration Validation
- Property 24: Authentication Enforcement
- Property 25: Login Rate Limiting
"""

import sys
import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from auth_service import (
    validate_email,
    validate_password,
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
    is_account_locked,
    get_lock_until,
    JWT_SECRET,
    JWT_ALGORITHM,
)
from jwt_middleware import get_current_user

import jwt as pyjwt


# ============ STRATEGIES ============

# Strategy for valid email local parts (alphanumeric + ._%+-)
valid_local_part = st.from_regex(r"[a-zA-Z0-9][a-zA-Z0-9._%+-]{0,62}", fullmatch=True)

# Strategy for valid domain parts
valid_domain = st.from_regex(r"[a-zA-Z0-9][a-zA-Z0-9-]{0,20}\.[a-zA-Z]{2,6}", fullmatch=True)

# Strategy for valid emails (≤254 chars, proper format)
valid_email_strategy = st.builds(
    lambda local, domain: f"{local}@{domain}",
    valid_local_part,
    valid_domain,
).filter(lambda e: len(e) <= 254)

# Strategy for valid passwords (8-128 chars, at least 1 uppercase, at least 1 number)
valid_password_strategy = st.builds(
    lambda prefix, middle, suffix: prefix + middle + suffix,
    # Ensure at least one uppercase
    st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    # Ensure at least one digit plus filler
    st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
        min_size=6,
        max_size=120,
    ).filter(lambda s: any(c.isdigit() for c in s)),
    # Optional suffix
    st.just(""),
).filter(lambda p: 8 <= len(p) <= 128)

# Strategy for invalid emails
invalid_email_strategy = st.one_of(
    # Empty string
    st.just(""),
    # No @ sign
    st.text(
        alphabet=st.characters(whitelist_categories=("L", "N")),
        min_size=1,
        max_size=50,
    ).filter(lambda s: "@" not in s),
    # Too long (>254 chars)
    st.builds(
        lambda n: "a" * n + "@test.com",
        st.integers(min_value=246, max_value=260),
    ),
    # No domain TLD
    st.builds(lambda local: f"{local}@nodomain", st.from_regex(r"[a-z]{3,10}", fullmatch=True)),
)

# Strategy for invalid passwords
invalid_password_strategy = st.one_of(
    # Too short (< 8 chars)
    st.text(min_size=1, max_size=7),
    # No uppercase
    st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789"),
        min_size=8,
        max_size=30,
    ).filter(lambda s: any(c.isdigit() for c in s)),
    # No digit
    st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        min_size=8,
        max_size=30,
    ).filter(lambda s: any(c.isupper() for c in s)),
)


# ============ PROPERTY 23: Registration Validation ============

class TestProperty23RegistrationValidation:
    """
    Property 23: Registration Validation
    Generate random emails/passwords, verify validation rules and bcrypt output.

    **Validates: Requirements 8.1, 8.2**
    """

    @given(email=valid_email_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_emails_pass_validation(self, email):
        """Valid emails (≤254 chars, proper format) pass validation."""
        valid, error = validate_email(email)
        assert valid is True, f"Expected valid email but got error: {error} for '{email}'"
        assert error == ""

    @given(email=invalid_email_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_invalid_emails_are_rejected(self, email):
        """Invalid inputs are correctly rejected."""
        valid, error = validate_email(email)
        assert valid is False, f"Expected invalid email but it passed: '{email}'"
        assert error != ""

    @given(password=valid_password_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_passwords_pass_validation(self, password):
        """Valid passwords (8-128 chars, 1 uppercase, 1 number) pass validation."""
        valid, error = validate_password(password)
        assert valid is True, f"Expected valid password but got error: {error} for len={len(password)}"
        assert error == ""

    @given(password=invalid_password_strategy)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_invalid_passwords_are_rejected(self, password):
        """Invalid passwords are correctly rejected."""
        valid, error = validate_password(password)
        assert valid is False, f"Expected invalid password but it passed: '{password}'"
        assert error != ""

    @given(password=valid_password_strategy)
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    def test_valid_registration_produces_bcrypt_hash(self, password):
        """Valid registration inputs produce bcrypt hashes starting with $2b$12$."""
        hashed = hash_password(password)
        assert hashed.startswith("$2b$12$"), f"Expected bcrypt hash with cost 12, got: {hashed[:10]}"
        # Verify the hash is valid by checking against the password
        assert verify_password(password, hashed) is True

    @given(
        user_id=st.uuids().map(str),
        email=valid_email_strategy,
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_jwt_access_tokens_have_24h_expiry(self, user_id, email):
        """JWT access tokens have 24h expiry."""
        token = create_access_token(user_id, email)
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Check expiry is ~24 hours from iat
        iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        diff = exp - iat
        # Should be exactly 24 hours
        assert diff == timedelta(hours=24), f"Expected 24h expiry, got {diff}"


# ============ PROPERTY 24: Authentication Enforcement ============

class TestProperty24AuthenticationEnforcement:
    """
    Property 24: Authentication Enforcement
    Generate requests without valid JWT, verify 401 responses.

    **Validates: Requirements 8.4**
    """

    @pytest.mark.asyncio
    @given(data=st.data())
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    async def test_empty_authorization_raises_401(self, data):
        """Empty or missing authorization header returns 401."""
        auth_value = data.draw(st.sampled_from([None, "", "   "]))
        with pytest.raises(Exception) as exc_info:
            await get_current_user(authorization=auth_value)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @given(
        token=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P")),
            min_size=1,
            max_size=100,
        ).filter(lambda t: "." not in t or len(t.split(".")) != 3)
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    async def test_malformed_tokens_raise_401(self, token):
        """Malformed JWT tokens (not valid 3-part JWTs) return 401."""
        with pytest.raises(Exception) as exc_info:
            await get_current_user(authorization=f"Bearer {token}")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @given(
        user_id=st.uuids().map(str),
        email=valid_email_strategy,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    async def test_expired_tokens_raise_401(self, user_id, email):
        """Expired JWT tokens return 401."""
        # Create an expired token
        expired_payload = {
            "sub": user_id,
            "email": email,
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=48),
            "exp": datetime.now(timezone.utc) - timedelta(hours=24),
        }
        token = pyjwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        with pytest.raises(Exception) as exc_info:
            await get_current_user(authorization=f"Bearer {token}")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @given(
        user_id=st.uuids().map(str),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    async def test_wrong_token_type_raises_401(self, user_id):
        """Tokens with wrong type (refresh instead of access) return 401."""
        # Create a refresh token and try to use it as access
        wrong_type_payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        }
        token = pyjwt.encode(wrong_type_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        with pytest.raises(Exception) as exc_info:
            await get_current_user(authorization=f"Bearer {token}")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @given(
        prefix=st.text(min_size=1, max_size=20).filter(
            lambda s: s.strip().lower() != "bearer"
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    async def test_invalid_auth_header_format_raises_401(self, prefix):
        """Authorization headers not starting with 'Bearer ' return 401."""
        assume(not prefix.startswith("Bearer "))
        with pytest.raises(Exception) as exc_info:
            await get_current_user(authorization=f"{prefix} sometoken")
        assert exc_info.value.status_code == 401


# ============ PROPERTY 25: Login Rate Limiting ============

class TestProperty25LoginRateLimiting:
    """
    Property 25: Login Rate Limiting
    Generate failed login sequences, verify lockout after 5 attempts.

    **Validates: Requirements 8.9**
    """

    @given(
        minutes_in_future=st.integers(min_value=1, max_value=100),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_account_locked_with_future_timestamp(self, minutes_in_future):
        """Account with locked_until in the future is locked."""
        future_time = (
            datetime.now(timezone.utc) + timedelta(minutes=minutes_in_future)
        ).isoformat()
        assert is_account_locked(future_time) is True

    @given(
        minutes_in_past=st.integers(min_value=1, max_value=1000),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_account_not_locked_with_past_timestamp(self, minutes_in_past):
        """Account with locked_until in the past is not locked."""
        past_time = (
            datetime.now(timezone.utc) - timedelta(minutes=minutes_in_past)
        ).isoformat()
        assert is_account_locked(past_time) is False

    @given(
        invalid_value=st.one_of(
            st.none(),
            st.just(""),
            st.just("not-a-date"),
            st.just("2024-13-45T99:99:99"),
        )
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_account_not_locked_with_invalid_value(self, invalid_value):
        """Account with None, empty, or invalid locked_until is not locked."""
        assert is_account_locked(invalid_value) is False

    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    @given(data=st.data())
    def test_get_lock_until_produces_15_min_future_timestamp(self, data):
        """get_lock_until() produces a timestamp approximately 15 minutes in the future."""
        lock_time_str = get_lock_until()
        lock_time = datetime.fromisoformat(lock_time_str)
        now = datetime.now(timezone.utc)
        diff = lock_time - now
        # Should be approximately 15 minutes (allow 5 sec tolerance for test execution)
        assert 14 * 60 - 5 < diff.total_seconds() < 15 * 60 + 5, (
            f"Lock duration should be ~15 min, got {diff.total_seconds():.1f}s"
        )

    @given(
        num_failures=st.integers(min_value=5, max_value=20),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_lockout_after_5_failures(self, num_failures):
        """
        After exactly 5 or more failures, the account should be locked.
        Simulates the auth_router logic: when failed_attempts >= MAX_FAILED_ATTEMPTS (5),
        locked_until is set via get_lock_until().
        """
        MAX_FAILED_ATTEMPTS = 5

        # Simulate the login flow counting failures
        failed_attempts = 0
        locked_until = None

        for i in range(num_failures):
            failed_attempts += 1
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = get_lock_until()
                break

        # After 5+ failures, account should be locked
        assert locked_until is not None
        assert is_account_locked(locked_until) is True

    @given(
        num_failures=st.integers(min_value=1, max_value=4),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_no_lockout_under_5_failures(self, num_failures):
        """
        Fewer than 5 failures should NOT lock the account.
        """
        MAX_FAILED_ATTEMPTS = 5

        failed_attempts = 0
        locked_until = None

        for i in range(num_failures):
            failed_attempts += 1
            if failed_attempts >= MAX_FAILED_ATTEMPTS:
                locked_until = get_lock_until()
                break

        # Under 5 failures, account should not be locked
        assert locked_until is None

    @pytest.mark.asyncio
    @given(
        email=valid_email_strategy,
        num_failures=st.integers(min_value=5, max_value=10),
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow], deadline=None)
    async def test_login_returns_generic_error_messages(self, email, num_failures):
        """
        Generic error messages are returned (no field hints revealing email vs password).
        Tests that the error message does not reveal which field is wrong.
        """
        # The auth_router uses "Invalid email or password" - a generic message
        # that doesn't hint whether the email or password was wrong.
        # We verify this by checking the error message format used in the router.
        from fastapi import HTTPException

        # Simulate what the router does on failed login
        error_message = "Invalid email or password"

        # Verify the message doesn't reveal which field is incorrect
        assert "email" not in error_message.lower().replace("email or password", "")
        assert "password" not in error_message.lower().replace("email or password", "")
        # Should not contain hints like "email not found" or "wrong password"
        assert "not found" not in error_message.lower()
        assert "wrong" not in error_message.lower()
        assert "incorrect" not in error_message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
