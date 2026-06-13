"""Iteration 3 backend tests for PocketBuddy:
- Live streak_days computation in /api/profile (driven by mood_entries)
- /api/profile/onboard endpoint (name + avatar_initial + your_pattern)
- /api/profile PATCH (name -> avatar_initial, onboarded toggle, drops streak_days)
"""
import os
import pytest
import requests
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to frontend .env if not exported
    try:
        with open("/app/frontend/.env") as f:
            for ln in f:
                if ln.startswith("REACT_APP_BACKEND_URL"):
                    BASE_URL = ln.split("=", 1)[1].strip().rstrip("/")
                    break
    except Exception:
        pass

API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- helpers ----------
def _get_profile(s):
    r = s.get(f"{API}/profile", timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


def _patch_profile(s, payload):
    r = s.patch(f"{API}/profile", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()


# ---------- 1) Live streak ----------
class TestLiveStreak:
    def test_streak_starts_positive_after_seed(self, session):
        # The app seeds 7 consecutive mood entries on startup; depending on tz
        # we may compute 6 or 7 (boundary). It must be > 0 and an int.
        prof = _get_profile(session)
        assert "streak_days" in prof
        assert isinstance(prof["streak_days"], int)
        assert prof["streak_days"] >= 1, f"Expected positive seed streak, got {prof['streak_days']}"

    def test_streak_is_derived_not_client_settable(self, session):
        # Try to set a bogus value via PATCH; GET must still return the computed value
        before = _get_profile(session)["streak_days"]
        _patch_profile(session, {"streak_days": 999})
        after = _get_profile(session)["streak_days"]
        assert after == before, f"streak_days must be computed; before={before} after={after}"
        assert after != 999

    def test_streak_zero_when_no_mood_entries(self, session):
        # Delete all mood entries directly via DB (no public delete-all endpoint).
        from pymongo import MongoClient
        mongo_url = os.environ.get("MONGO_URL")
        db_name = os.environ.get("DB_NAME")
        if not mongo_url or not db_name:
            # Read from backend/.env
            with open("/app/backend/.env") as f:
                for ln in f:
                    if ln.startswith("MONGO_URL"):
                        mongo_url = ln.split("=", 1)[1].strip().strip('"')
                    if ln.startswith("DB_NAME"):
                        db_name = ln.split("=", 1)[1].strip().strip('"')
        cli = MongoClient(mongo_url)
        backup = list(cli[db_name].mood_entries.find({"user_id": "alex"}))
        try:
            cli[db_name].mood_entries.delete_many({"user_id": "alex"})
            prof = _get_profile(session)
            assert prof["streak_days"] == 0
        finally:
            # Restore
            if backup:
                # remove _id collisions
                for d in backup:
                    d.pop("_id", None)
                cli[db_name].mood_entries.insert_many(backup)

    def test_streak_recomputes_after_restore(self, session):
        prof = _get_profile(session)
        assert prof["streak_days"] >= 1


# ---------- 2) Onboard endpoint ----------
class TestOnboard:
    def test_onboard_persists_name_avatar_pattern(self, session):
        payload = {
            "name": "Riya",
            "your_pattern": {
                "spending_style": "careful",
                "sleep": "7-8h",
                "stress_baseline": 7,
            },
        }
        r = session.post(f"{API}/profile/onboard", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["name"] == "Riya"
        assert data["avatar_initial"] == "R"
        assert data["onboarded"] is True
        assert data["your_pattern"]["spending_style"] == "careful"
        assert data["your_pattern"]["sleep"] == "7-8h"
        assert data["your_pattern"]["stress_baseline"] == 7

        # GET again -> persistence
        prof = _get_profile(session)
        assert prof["name"] == "Riya"
        assert prof["avatar_initial"] == "R"
        assert prof["onboarded"] is True
        assert prof["your_pattern"]["spending_style"] == "careful"


# ---------- 3) PATCH profile ----------
class TestProfilePatch:
    def test_patch_name_updates_avatar_initial(self, session):
        data = _patch_profile(session, {"name": "Maya"})
        assert data["name"] == "Maya"
        assert data["avatar_initial"] == "M"

    def test_patch_can_set_onboarded_false(self, session):
        data = _patch_profile(session, {"onboarded": False})
        assert data["onboarded"] is False
        # restore for downstream UI tests
        data2 = _patch_profile(session, {"onboarded": True, "name": "Alex"})
        assert data2["onboarded"] is True
        assert data2["avatar_initial"] == "A"

    def test_patch_income(self, session):
        data = _patch_profile(session, {"monthly_income": 16000})
        assert data["monthly_income"] == 16000
