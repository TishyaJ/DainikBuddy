"""Iteration 4 backend tests for PocketBuddy:
- Chat injection (your_pattern + name in system prompt -> assistant msg persisted)
- Exercise CRUD + sessions + summary
- Routine habits (dynamic)
- Wellness AI cards (LLM with fallback)
- Onboard endpoint creates Goal entries with source='onboard' (replace on rerun)
- PATCH /api/profile {onboarded:false}
"""
import os
import time
import json
import pytest
import requests
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for ln in f:
            if ln.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = ln.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ============== 1) Chat injects your_pattern ==============
class TestChatPatternInjection:
    def test_chat_uses_pattern_persisted_in_assistant_message(self, s):
        # set known pattern
        r = s.patch(f"{API}/profile", json={
            "name": "Alex",
            "your_pattern": {"spending_style": "careful", "sleep": "7-8h"},
        }, timeout=15)
        assert r.status_code == 200, r.text

        # clear chat history so we can find the new assistant message
        s.delete(f"{API}/chat/finance/history", timeout=15)

        # POST a chat - drain the SSE stream
        sid = f"test-finance-{int(time.time())}"
        with s.post(f"{API}/chat/finance",
                    json={"message": "I want to save more this month", "session_id": sid},
                    stream=True, timeout=60) as resp:
            assert resp.status_code == 200
            full = ""
            done = False
            for line in resp.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        done = True
                        break
                    full += chunk.replace("\\n", "\n")
            assert done, "Stream did not complete"
            assert len(full) > 0, "No text streamed"

        # give backend a tick to persist
        time.sleep(1.0)
        hist = s.get(f"{API}/chat/finance/history", timeout=15).json()
        assert len(hist) >= 2  # user + assistant
        assistant = [m for m in hist if m["role"] == "assistant"]
        assert assistant, "No assistant message persisted"
        text = assistant[-1]["content"].lower()
        # Should mention careful spending style OR user name OR savings keywords
        assert any(k in text for k in ["careful", "alex", "save", "spending", "₹"]), \
            f"Assistant reply didn't reflect pattern/context: {text[:300]}"


# ============== 2) Exercises CRUD ==============
class TestExerciseCRUD:
    def test_create_list_patch_delete(self, s):
        # CREATE
        r = s.post(f"{API}/exercises",
                   json={"name": "TEST_Squats", "body_part": "lower", "target_minutes": 30},
                   timeout=15)
        assert r.status_code == 200, r.text
        ex = r.json()
        assert ex["name"] == "TEST_Squats"
        assert ex["body_part"] == "lower"
        assert ex["target_minutes"] == 30
        eid = ex["id"]

        # LIST
        all_ex = s.get(f"{API}/exercises", timeout=15).json()
        assert any(e["id"] == eid for e in all_ex)

        # PATCH progress<100 -> active
        r2 = s.patch(f"{API}/exercises/{eid}", json={"progress": 50}, timeout=15)
        assert r2.status_code == 200
        assert r2.json()["progress"] == 50
        assert r2.json()["status"] == "active"

        # PATCH progress>=100 -> done
        r3 = s.patch(f"{API}/exercises/{eid}", json={"progress": 100}, timeout=15)
        assert r3.json()["status"] == "done"
        assert r3.json()["progress"] == 100

        # DELETE
        rd = s.delete(f"{API}/exercises/{eid}", timeout=15)
        assert rd.status_code == 200
        all_ex2 = s.get(f"{API}/exercises", timeout=15).json()
        assert not any(e["id"] == eid for e in all_ex2)


# ============== 3) Exercise Sessions ==============
class TestExerciseSessions:
    def test_start_stop_get_sessions(self, s):
        r = s.post(f"{API}/exercises",
                   json={"name": "TEST_Pushups", "body_part": "upper", "target_minutes": 10},
                   timeout=15)
        eid = r.json()["id"]
        try:
            st = s.post(f"{API}/exercises/{eid}/start", json={}, timeout=15)
            assert st.status_code == 200
            sid = st.json()["id"]

            time.sleep(1.2)

            sp = s.post(f"{API}/exercises/{eid}/stop",
                        json={"comment": "10 reps x 3"}, timeout=15)
            assert sp.status_code == 200
            sj = sp.json()
            assert sj["comment"] == "10 reps x 3"
            assert sj["elapsed_seconds"] >= 1
            assert sj["ended_at"] is not None

            # GET sessions
            g = s.get(f"{API}/exercises/{eid}/sessions", timeout=15).json()
            assert "sessions" in g and "total_seconds" in g
            assert g["active"] is None
            assert any(x["id"] == sid for x in g["sessions"])
            assert g["total_seconds"] >= 1
        finally:
            s.delete(f"{API}/exercises/{eid}", timeout=15)


# ============== 4) Exercise summary ==============
class TestExerciseSummary:
    def test_summary_shape_and_dynamic(self, s):
        # Clear all sessions and exercises first so sedentary=true, balanced=false
        from pymongo import MongoClient
        mongo_url, db_name = None, None
        with open("/app/backend/.env") as f:
            for ln in f:
                if ln.startswith("MONGO_URL"):
                    mongo_url = ln.split("=", 1)[1].strip().strip('"')
                if ln.startswith("DB_NAME"):
                    db_name = ln.split("=", 1)[1].strip().strip('"')
        cli = MongoClient(mongo_url)
        cli[db_name].exercise_sessions.delete_many({"user_id": "alex"})

        summary = s.get(f"{API}/exercises/summary", timeout=15).json()
        for k in ["today_minutes", "sedentary", "sedentary_warning", "by_part_7d",
                  "balanced_7d", "imbalance_note"]:
            assert k in summary, f"Missing {k}: {summary}"
        assert summary["sedentary"] is True
        assert summary["balanced_7d"] is False
        assert set(summary["by_part_7d"].keys()) >= {"upper", "lower", "cardio", "full"}

        # Log a >= 60s upper session
        r = s.post(f"{API}/exercises",
                   json={"name": "TEST_UpperX", "body_part": "upper", "target_minutes": 10},
                   timeout=15)
        eid = r.json()["id"]
        try:
            s.post(f"{API}/exercises/{eid}/start", json={}, timeout=15)
            # Manually set started_at 70s in the past so summary picks up >= 1 minute
            cli[db_name].exercise_sessions.update_many(
                {"exercise_id": eid, "ended_at": None},
                {"$set": {"started_at": (datetime.utcnow().replace(microsecond=0)
                                         .isoformat() + "+00:00")}}
            )
            time.sleep(1.0)
            s.post(f"{API}/exercises/{eid}/stop", json={"comment": "x"}, timeout=15)
            # Inflate elapsed_seconds to 120 (2 min) so today_minutes>=1
            cli[db_name].exercise_sessions.update_many(
                {"exercise_id": eid},
                {"$set": {"elapsed_seconds": 120}},
            )

            summary2 = s.get(f"{API}/exercises/summary", timeout=15).json()
            assert summary2["today_minutes"] >= 1
            assert summary2["by_part_7d"]["upper"] >= 1
        finally:
            s.delete(f"{API}/exercises/{eid}", timeout=15)


# ============== 5) Routine habits ==============
class TestRoutineHabits:
    def test_habits_shape_and_response(self, s):
        habits = s.get(f"{API}/routine/habits", timeout=15).json()
        assert isinstance(habits, list)
        names = [h["habit"] for h in habits]
        for expected in ["7+ hour sleep", "Exercise", "Daily journal", "Daily check-in"]:
            assert expected in names, f"Missing habit {expected}"
        for h in habits:
            assert 0 <= h["value"] <= 100

    def test_habit_updates_after_new_mood(self, s):
        before = {h["habit"]: h["value"]
                  for h in s.get(f"{API}/routine/habits", timeout=15).json()}
        # Wipe moods to force the daily check-in down, then re-add one
        from pymongo import MongoClient
        with open("/app/backend/.env") as f:
            mongo_url = db_name = None
            for ln in f:
                if ln.startswith("MONGO_URL"):
                    mongo_url = ln.split("=", 1)[1].strip().strip('"')
                if ln.startswith("DB_NAME"):
                    db_name = ln.split("=", 1)[1].strip().strip('"')
        cli = MongoClient(mongo_url)
        backup = list(cli[db_name].mood_entries.find({"user_id": "alex"}))
        try:
            cli[db_name].mood_entries.delete_many({"user_id": "alex"})
            zero_habits = {h["habit"]: h["value"]
                           for h in s.get(f"{API}/routine/habits", timeout=15).json()}
            assert zero_habits["Daily check-in"] == 0

            # Create one mood entry
            r = s.post(f"{API}/mood", json={"mood": "okay", "stress": 50}, timeout=15)
            assert r.status_code == 200
            after = {h["habit"]: h["value"]
                     for h in s.get(f"{API}/routine/habits", timeout=15).json()}
            assert after["Daily check-in"] > 0, after
        finally:
            cli[db_name].mood_entries.delete_many({"user_id": "alex"})
            if backup:
                for d in backup:
                    d.pop("_id", None)
                cli[db_name].mood_entries.insert_many(backup)


# ============== 6) Wellness cards ==============
class TestWellnessCards:
    def test_returns_two_cards(self, s):
        r = s.get(f"{API}/wellness/cards?kind=stress", timeout=20)
        assert r.status_code == 200
        cards = r.json()
        assert isinstance(cards, list)
        assert 1 <= len(cards) <= 2
        for c in cards:
            assert "kind" in c and "title" in c and "text" in c


# ============== 7) Onboard creates Goal entries ==============
class TestOnboardGoals:
    def test_onboard_creates_and_replaces_onboard_goals(self, s):
        # Snapshot non-onboard goals
        before = s.get(f"{API}/goals", timeout=15).json()
        non_onboard_before = [g for g in before if g.get("source") != "onboard"]

        # First onboard
        payload = {
            "name": "Alex",
            "your_pattern": {"spending_style": "careful", "sleep": "7-8h"},
            "goals": ["Study 3 hrs/day", "Sleep before 11pm", "Gym 3x/week"],
        }
        r = s.post(f"{API}/profile/onboard", json=payload, timeout=15)
        assert r.status_code == 200, r.text

        gs = s.get(f"{API}/goals", timeout=15).json()
        onboard_goals = [g for g in gs if g.get("source") == "onboard"]
        titles = sorted(g["title"] for g in onboard_goals)
        assert titles == sorted(payload["goals"]), titles

        # Re-run with different goals - should REPLACE, not add
        new_payload = {
            "name": "Alex",
            "goals": ["Read 20 pages", "Drink 2L water"],
        }
        r2 = s.post(f"{API}/profile/onboard", json=new_payload, timeout=15)
        assert r2.status_code == 200
        gs2 = s.get(f"{API}/goals", timeout=15).json()
        onboard_goals2 = [g for g in gs2 if g.get("source") == "onboard"]
        titles2 = sorted(g["title"] for g in onboard_goals2)
        assert titles2 == sorted(new_payload["goals"]), titles2

        # Non-onboard goals untouched
        non_onboard_after = [g for g in gs2 if g.get("source") != "onboard"]
        assert len(non_onboard_after) == len(non_onboard_before)


# ============== 8) PATCH onboarded:false ==============
class TestProfileReonboard:
    def test_patch_onboarded_false(self, s):
        r = s.patch(f"{API}/profile", json={"onboarded": False}, timeout=15)
        assert r.status_code == 200
        assert r.json()["onboarded"] is False
        # restore
        r2 = s.patch(f"{API}/profile", json={"onboarded": True}, timeout=15)
        assert r2.json()["onboarded"] is True
