"""PocketBuddy backend API tests covering all domains: health, mood, expenses,
journal, goals, budget, subscriptions/savings/splits, wellness, discover,
helper/insights, and chat streaming (SSE) + chat history.
"""
import os
import json
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://discover-buddy.preview.emergentagent.com').rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Health ----------
def test_health(s):
    r = s.get(f"{API}/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["user"] == "alex"


# ---------- Mood ----------
class TestMood:
    def test_create_mood(self, s):
        r = s.post(f"{API}/mood", json={"mood": "good", "energy": 60, "stress": 40, "motivation": 70})
        assert r.status_code == 200
        d = r.json()
        assert d["mood"] == "good"
        assert d["energy"] == 60
        assert d["stress"] == 40
        assert d["motivation"] == 70
        assert "id" in d

    def test_get_moods_includes_created(self, s):
        r = s.get(f"{API}/mood")
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list)
        assert len(arr) >= 1
        assert any(m["mood"] == "good" for m in arr)


# ---------- Expenses ----------
class TestExpenses:
    def test_create_expense(self, s):
        r = s.post(f"{API}/expenses", json={"amount": 50, "category": "food", "merchant": "Mess"})
        assert r.status_code == 200
        d = r.json()
        assert d["amount"] == 50
        assert d["category"] == "food"
        assert d["merchant"] == "Mess"

    def test_list_expenses_persisted(self, s):
        r = s.get(f"{API}/expenses")
        assert r.status_code == 200
        arr = r.json()
        assert any(e["merchant"] == "Mess" and e["amount"] == 50 for e in arr)

    def test_categorize_transport(self, s):
        r = s.post(f"{API}/expenses/categorize", json={"text": "uber to college"})
        assert r.status_code == 200
        assert r.json()["category"] == "transport"


# ---------- Journal ----------
class TestJournal:
    def test_journal_positive(self, s):
        r = s.post(f"{API}/journal", json={"text": "I feel happy and grateful today"})
        assert r.status_code == 200
        d = r.json()
        assert d["sentiment"] == "positive"
        assert d["text"].startswith("I feel happy")

    def test_journal_weekly_buckets(self, s):
        r = s.get(f"{API}/journal/weekly")
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list)
        assert len(arr) == 7
        for x in arr:
            assert "day" in x and "score" in x and "count" in x


# ---------- Goals ----------
class TestGoals:
    def test_get_goals_seeded(self, s):
        r = s.get(f"{API}/goals")
        assert r.status_code == 200
        arr = r.json()
        assert len(arr) >= 4

    def test_patch_goal(self, s):
        arr = s.get(f"{API}/goals").json()
        gid = arr[0]["id"]
        r = s.patch(f"{API}/goals/{gid}", json={"current": 90})
        assert r.status_code == 200
        d = r.json()
        assert d["current"] == 90


# ---------- Budget ----------
def test_budget(s):
    r = s.get(f"{API}/budget")
    assert r.status_code == 200
    d = r.json()
    assert "categories" in d and isinstance(d["categories"], list) and len(d["categories"]) >= 4
    assert "total_allocated" in d and d["total_allocated"] > 0
    assert "total_spent" in d
    assert "percent_used" in d


# ---------- Subscriptions/Savings/Splits ----------
def test_subscriptions(s):
    r = s.get(f"{API}/subscriptions")
    assert r.status_code == 200
    d = r.json()
    assert len(d["items"]) >= 3
    assert d["monthly_total"] > 0


def test_savings(s):
    r = s.get(f"{API}/savings")
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) >= 3


def test_splits(s):
    r = s.get(f"{API}/splits")
    assert r.status_code == 200
    d = r.json()
    assert "items" in d and len(d["items"]) >= 2
    assert "net_balance" in d


# ---------- Wellness ----------
def test_wellness_scores(s):
    r = s.get(f"{API}/wellness/scores")
    assert r.status_code == 200
    d = r.json()
    for k in ("sleep_score", "stress_score", "burnout_score"):
        assert k in d
        assert 0 <= d[k] <= 100


def test_sleep_weekly(s):
    r = s.get(f"{API}/sleep/weekly")
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) == 7
    for x in arr:
        assert "day" in x and "hours" in x


# ---------- Discover ----------
@pytest.mark.parametrize("path", ["food", "travel", "snacks", "activities", "campus"])
def test_discover(s, path):
    r = s.get(f"{API}/discover/{path}")
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list) and len(arr) >= 1


# ---------- Helper / Insights ----------
def test_life_balance(s):
    r = s.get(f"{API}/life-balance")
    assert r.status_code == 200
    d = r.json()
    assert "overall" in d
    assert len(d["domains"]) == 4


def test_insights_daily(s):
    r = s.get(f"{API}/insights/daily")
    assert r.status_code == 200
    arr = r.json()
    assert len(arr) == 4


def test_insights_weekly(s):
    r = s.get(f"{API}/insights/weekly")
    assert r.status_code == 200
    d = r.json()
    assert "scorecard" in d and len(d["scorecard"]) == 4
    assert "highlights" in d
    assert "next_week_focus" in d


# ---------- Chat Streaming (SSE) ----------
@pytest.mark.parametrize("buddy,prompt", [
    ("finance", "How can I save more on food?"),
    ("wellness", "I feel a bit anxious about exams"),
    ("discover", "Cheap dinner ideas near campus?"),
    ("helper", "Give me a quick daily summary"),
])
def test_chat_stream(s, buddy, prompt):
    url = f"{API}/chat/{buddy}"
    with requests.post(url, json={"message": prompt}, stream=True, timeout=60) as r:
        assert r.status_code == 200, f"{buddy} status {r.status_code}"
        assert "text/event-stream" in r.headers.get("content-type", "")
        data_events = 0
        got_done = False
        full = ""
        for raw in r.iter_lines(decode_unicode=True):
            if raw is None:
                continue
            if raw.startswith("data:"):
                payload = raw[5:].strip()
                if payload == "[DONE]":
                    got_done = True
                    break
                if payload.startswith("[error]"):
                    pytest.fail(f"{buddy} stream error: {payload}")
                data_events += 1
                full += payload
        assert got_done, f"{buddy} did not emit [DONE]"
        assert data_events >= 1, f"{buddy} produced no data events"
        assert len(full.strip()) > 0, f"{buddy} produced empty response"


# ---------- Chat History ----------
def test_chat_history_then_clear(s):
    # ensure history exists from previous test
    r = s.get(f"{API}/chat/finance/history")
    assert r.status_code == 200
    msgs = r.json()
    assert len(msgs) >= 2
    roles = {m["role"] for m in msgs}
    assert "user" in roles
    assert "assistant" in roles

    # clear
    r2 = s.delete(f"{API}/chat/finance/history")
    assert r2.status_code == 200
    assert r2.json().get("ok") is True

    # confirm cleared
    r3 = s.get(f"{API}/chat/finance/history")
    assert r3.status_code == 200
    assert r3.json() == []
