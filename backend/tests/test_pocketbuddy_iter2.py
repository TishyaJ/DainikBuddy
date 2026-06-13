"""Iteration 2 backend tests for PocketBuddy:
Profile, Tasks CRUD + Sessions, Auto-balance budget, Cashflow, Fitness/today.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- Profile ----------
class TestProfile:
    def test_get_profile_shape(self, s):
        r = s.get(f"{API}/profile")
        assert r.status_code == 200
        d = r.json()
        for k in ("name", "monthly_income", "streak_days", "avatar_initial"):
            assert k in d, f"missing {k}"
        assert isinstance(d["streak_days"], int)
        assert isinstance(d["monthly_income"], (int, float))

    def test_patch_profile_persists(self, s):
        original = s.get(f"{API}/profile").json()
        r = s.patch(f"{API}/profile", json={"name": "Ankit"})
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "Ankit"
        # verify persisted
        g = s.get(f"{API}/profile").json()
        assert g["name"] == "Ankit"
        # restore
        s.patch(f"{API}/profile", json={"name": original.get("name", "Alex")})


# ---------- Tasks CRUD ----------
class TestTasks:
    def test_seeded_tasks(self, s):
        r = s.get(f"{API}/tasks")
        assert r.status_code == 200
        arr = r.json()
        titles = [t["title"] for t in arr]
        for expected in ["Workout", "Read 20 pages", "Study Math chapter 4"]:
            assert expected in titles, f"missing seeded task {expected}"

    def test_create_update_delete_task(self, s):
        # create
        r = s.post(f"{API}/tasks", json={"title": "TEST_Task1", "target_minutes": 45})
        assert r.status_code == 200
        t = r.json()
        assert t["title"] == "TEST_Task1"
        assert t["target_minutes"] == 45
        assert t["progress"] == 0
        assert t["status"] == "active"
        tid = t["id"]

        # update progress -> auto status flip on 100
        r2 = s.patch(f"{API}/tasks/{tid}", json={"progress": 100})
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["progress"] == 100
        assert d2["status"] == "done"
        assert d2["completed_at"] is not None

        # partial progress flips back to active
        r3 = s.patch(f"{API}/tasks/{tid}", json={"progress": 50})
        assert r3.json()["status"] == "active"

        # delete
        r4 = s.delete(f"{API}/tasks/{tid}")
        assert r4.status_code == 200
        # verify gone
        listed = s.get(f"{API}/tasks").json()
        assert not any(t["id"] == tid for t in listed)


# ---------- Task Sessions ----------
class TestTaskSessions:
    def test_start_stop_session(self, s):
        # create task
        t = s.post(f"{API}/tasks", json={"title": "TEST_SessTask"}).json()
        tid = t["id"]

        # start
        r = s.post(f"{API}/tasks/{tid}/start")
        assert r.status_code == 200
        sess = r.json()
        assert sess["task_id"] == tid
        assert sess["ended_at"] is None

        # sessions list shows active
        gs = s.get(f"{API}/tasks/{tid}/sessions").json()
        assert gs["active"] is not None
        assert gs["active"]["ended_at"] is None

        # stop
        r2 = s.post(f"{API}/tasks/{tid}/stop", json={"comment": "completed pomodoro"})
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["ended_at"] is not None
        assert d2["comment"] == "completed pomodoro"
        assert d2["elapsed_seconds"] >= 0

        # post-stop list
        gs2 = s.get(f"{API}/tasks/{tid}/sessions").json()
        assert gs2["active"] is None
        assert len(gs2["sessions"]) >= 1
        assert "total_seconds" in gs2

        # cleanup
        s.delete(f"{API}/tasks/{tid}")

    def test_stop_without_active_session(self, s):
        t = s.post(f"{API}/tasks", json={"title": "TEST_NoSess"}).json()
        r = s.post(f"{API}/tasks/{t['id']}/stop", json={"comment": ""})
        assert r.status_code == 404
        s.delete(f"{API}/tasks/{t['id']}")


# ---------- Auto-balance ----------
class TestAutoBalance:
    def test_invalid_income(self, s):
        r = s.post(f"{API}/budget/auto-balance", json={"income": 0})
        assert r.status_code == 400
        r2 = s.post(f"{API}/budget/auto-balance", json={"income": -100})
        assert r2.status_code == 400

    def test_auto_balance_20000(self, s):
        r = s.post(f"{API}/budget/auto-balance", json={"income": 20000})
        assert r.status_code == 200
        d = r.json()
        assert d.get("ok") is True
        assert d.get("income") == 20000

        # profile income persisted
        prof = s.get(f"{API}/profile").json()
        assert prof["monthly_income"] == 20000

        # check categories
        budget = s.get(f"{API}/budget").json()
        cats = budget["categories"]
        by_name = {c["name"].lower(): c for c in cats}

        # needs: food, transport, education -> total ~10000
        needs_total = sum(
            by_name[n]["allocated"] for n in ("food", "transport", "education") if n in by_name
        )
        assert 9900 <= needs_total <= 10100, f"needs={needs_total}"

        # wants: entertainment + miscellaneous -> ~6000
        wants_total = sum(
            by_name[n]["allocated"] for n in ("entertainment", "miscellaneous") if n in by_name
        )
        assert 5900 <= wants_total <= 6100, f"wants={wants_total}"

        # savings exists ~ 4000
        assert "savings" in by_name, "Savings category not created"
        sav = by_name["savings"]["allocated"]
        assert 3900 <= sav <= 4100, f"savings={sav}"

        # restore monthly_income for downstream tests
        s.patch(f"{API}/profile", json={"monthly_income": 16000})


# ---------- Cashflow ----------
def test_cashflow(s):
    r = s.get(f"{API}/cashflow")
    assert r.status_code == 200
    d = r.json()
    for k in ("forecast_remaining", "overspend", "underspend", "days_left", "trend"):
        assert k in d, f"missing {k}"
    assert isinstance(d["trend"], list)
    assert len(d["trend"]) == 14
    for x in d["trend"]:
        assert "d" in x and "v" in x


# ---------- Fitness today ----------
def test_fitness_today_deterministic(s):
    r1 = s.get(f"{API}/fitness/today")
    assert r1.status_code == 200
    d1 = r1.json()
    for k in ("steps", "active_minutes", "sedentary_hours", "body_balance"):
        assert k in d1, f"missing {k}"
    assert isinstance(d1["body_balance"], list) and len(d1["body_balance"]) == 7
    # same-day determinism
    d2 = s.get(f"{API}/fitness/today").json()
    assert d1 == d2
