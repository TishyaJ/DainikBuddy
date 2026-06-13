"""
Unit tests for authentication service and router.
Tests cover password hashing, JWT creation/verification, validation, and rate limiting.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    hash_refresh_token,
    validate_email,
    validate_password,
    is_account_locked,
    get_lock_until,
    generate_reset_token,
    hash_reset_token,
    now_iso,
)


# ============ PASSWORD HASHING TESTS ============

class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_hash(self):
        """Hash should start with $2b$ indicating bcrypt."""
        hashed = hash_password("TestPass123")
        assert hashed.startswith("$2b$")

    def test_hash_password_cost_12(self):
        """Hash should use cost factor 12."""
        hashed = hash_password("TestPass123")
        # bcrypt format: $2b$12$...
        assert hashed.startswith("$2b$12$")

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "MySecurePass1"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        hashed = hash_password("CorrectPass1")
        assert verify_password("WrongPass1", hashed) is False

    def test_verify_password_empty_hash(self):
        """Empty hash should not crash, just return False."""
        assert verify_password("test", "") is False

    def test_different_passwords_different_hashes(self):
        """Two different passwords should produce different hashes."""
        h1 = hash_password("Password1")
        h2 = hash_password("Password2")
        assert h1 != h2

    def test_same_password_different_hashes(self):
        """Same password hashed twice should produce different hashes (salted)."""
        h1 = hash_password("SamePass1")
        h2 = hash_password("SamePass1")
        assert h1 != h2  # Different salts


# ============ JWT TOKEN TESTS ============

class TestJWTTokens:
    def test_create_access_token_returns_string(self):
        token = create_access_token("user-123", "test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token_valid(self):
        token = create_access_token("user-123", "test@example.com")
        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_verify_access_token_invalid(self):
        payload = verify_access_token("invalid.token.here")
        assert payload is None

    def test_verify_access_token_expired(self):
        """Expired token should return None."""
        import jwt as pyjwt
        expired_payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "type": "access",
            "iat": datetime.now(timezone.utc) - timedelta(hours=25),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        from auth_service import JWT_SECRET, JWT_ALGORITHM
        token = pyjwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        assert verify_access_token(token) is None

    def test_create_refresh_token_returns_string(self):
        token = create_refresh_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_refresh_token_valid(self):
        token = create_refresh_token("user-123")
        payload = verify_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_verify_refresh_token_rejects_access_token(self):
        """Access tokens should not be valid as refresh tokens."""
        token = create_access_token("user-123", "test@example.com")
        payload = verify_refresh_token(token)
        assert payload is None

    def test_verify_access_token_rejects_refresh_token(self):
        """Refresh tokens should not be valid as access tokens."""
        token = create_refresh_token("user-123")
        payload = verify_access_token(token)
        assert payload is None

    def test_refresh_token_hash(self):
        """Hash should be deterministic for same token."""
        token = create_refresh_token("user-123")
        h1 = hash_refresh_token(token)
        h2 = hash_refresh_token(token)
        assert h1 == h2

    def test_different_tokens_different_hashes(self):
        t1 = create_refresh_token("user-1")
        t2 = create_refresh_token("user-2")
        assert hash_refresh_token(t1) != hash_refresh_token(t2)


# ============ VALIDATION TESTS ============

class TestEmailValidation:
    def test_valid_email(self):
        valid, error = validate_email("user@example.com")
        assert valid is True
        assert error == ""

    def test_valid_email_with_plus(self):
        valid, error = validate_email("user+tag@example.com")
        assert valid is True

    def test_invalid_email_no_at(self):
        valid, error = validate_email("userexample.com")
        assert valid is False

    def test_invalid_email_no_domain(self):
        valid, error = validate_email("user@")
        assert valid is False

    def test_invalid_email_no_tld(self):
        valid, error = validate_email("user@example")
        assert valid is False

    def test_empty_email(self):
        valid, error = validate_email("")
        assert valid is False

    def test_email_too_long(self):
        long_email = "a" * 246 + "@test.com"  # 246 + 9 = 255, > 254 chars
        valid, error = validate_email(long_email)
        assert valid is False

    def test_email_at_max_length(self):
        # 254 chars total
        local = "a" * 240
        email = f"{local}@example.com"  # 240 + 12 = 252 chars, valid
        valid, error = validate_email(email)
        assert valid is True


class TestPasswordValidation:
    def test_valid_password(self):
        valid, error = validate_password("SecurePass1")
        assert valid is True
        assert error == ""

    def test_too_short(self):
        valid, error = validate_password("Short1")
        assert valid is False
        assert "8 characters" in error

    def test_too_long(self):
        valid, error = validate_password("A1" + "a" * 127)
        assert valid is False
        assert "128 characters" in error

    def test_no_uppercase(self):
        valid, error = validate_password("nouppercase1")
        assert valid is False
        assert "uppercase" in error

    def test_no_number(self):
        valid, error = validate_password("NoNumberHere")
        assert valid is False
        assert "number" in error

    def test_minimum_valid_password(self):
        """Exactly 8 chars with uppercase and number."""
        valid, error = validate_password("Abcdefg1")
        assert valid is True

    def test_maximum_valid_password(self):
        """Exactly 128 chars with uppercase and number."""
        valid, error = validate_password("A1" + "a" * 126)
        assert valid is True

    def test_empty_password(self):
        valid, error = validate_password("")
        assert valid is False


# ============ RATE LIMITING TESTS ============

class TestRateLimiting:
    def test_not_locked_when_no_time(self):
        assert is_account_locked(None) is False

    def test_not_locked_when_empty_string(self):
        assert is_account_locked("") is False

    def test_locked_when_future(self):
        future = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        assert is_account_locked(future) is True

    def test_not_locked_when_past(self):
        past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        assert is_account_locked(past) is False

    def test_get_lock_until_is_15_min_from_now(self):
        lock_time = get_lock_until()
        lock_dt = datetime.fromisoformat(lock_time)
        now = datetime.now(timezone.utc)
        diff = lock_dt - now
        # Should be approximately 15 minutes (allow 2 sec tolerance)
        assert 14 * 60 < diff.total_seconds() < 15 * 60 + 2


# ============ RESET TOKEN TESTS ============

class TestResetToken:
    def test_generate_reset_token_length(self):
        token = generate_reset_token()
        assert len(token) > 20  # url-safe base64 of 32 bytes

    def test_generate_unique_tokens(self):
        t1 = generate_reset_token()
        t2 = generate_reset_token()
        assert t1 != t2

    def test_hash_reset_token_deterministic(self):
        token = "some-reset-token"
        h1 = hash_reset_token(token)
        h2 = hash_reset_token(token)
        assert h1 == h2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
