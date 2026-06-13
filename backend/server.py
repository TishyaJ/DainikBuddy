from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
from jwt_middleware import get_current_user
import gamification_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# Legacy demo user ID - only used for seeding initial demo data
DEMO_USER = "alex"

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============ MODELS ============
class MoodEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    mood: str  # great/good/okay/bad/terrible
    energy: int = 50
    stress: int = 50
    motivation: int = 50
    note: Optional[str] = ""
    created_at: str = Field(default_factory=now_iso)


class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    amount: float
    category: str  # food/transport/entertainment/education/misc
    merchant: Optional[str] = ""
    note: Optional[str] = ""
    created_at: str = Field(default_factory=now_iso)


class JournalEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    text: str
    sentiment: Optional[str] = None  # positive/neutral/negative
    sentiment_score: Optional[float] = None
    created_at: str = Field(default_factory=now_iso)


class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    title: str
    target: float
    current: float = 0
    unit: str = "%"
    deadline: Optional[str] = None
    status: str = "active"  # active/missed/done
    created_at: str = Field(default_factory=now_iso)


class BudgetCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    name: str
    allocated: float
    spent: float = 0


class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    name: str
    amount: float
    renews_on: str
    icon: str = "credit-card"


class SavingsGoal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    name: str
    target: float
    saved: float = 0
    emoji: str = "🎯"


class SplitBill(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    title: str
    total: float
    with_person: str
    you_paid: float
    owes_you: float


class SleepEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    hours: float
    quality: str = "good"  # good/ok/poor
    date: str = Field(default_factory=now_iso)


class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    buddy: str  # finance/wellness/discover/helper
    role: str  # user/assistant
    content: str
    created_at: str = Field(default_factory=now_iso)


class UserProfile(BaseModel):
    user_id: str = DEMO_USER
    name: str = "Alex"
    monthly_income: float = 16000
    streak_days: int = 0  # computed on read from mood entries
    avatar_initial: str = "A"
    onboarded: bool = False
    your_pattern: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    title: str
    target_minutes: int = 60
    progress: int = 0  # 0..100
    status: str = "active"  # active/done
    created_at: str = Field(default_factory=now_iso)
    completed_at: Optional[str] = None


class TaskSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    user_id: str = DEMO_USER
    started_at: str = Field(default_factory=now_iso)
    ended_at: Optional[str] = None
    elapsed_seconds: int = 0
    comment: str = ""


class Exercise(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = DEMO_USER
    name: str
    body_part: str = "full"  # upper / lower / full / cardio
    target_minutes: int = 30
    progress: int = 0  # 0..100
    status: str = "active"
    created_at: str = Field(default_factory=now_iso)


class ExerciseSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exercise_id: str
    user_id: str = DEMO_USER
    started_at: str = Field(default_factory=now_iso)
    ended_at: Optional[str] = None
    elapsed_seconds: int = 0
    comment: str = ""


# ============ SEED ============
async def seed_demo_data():
    """Seed demo data once for user 'alex' (idempotent for profile & tasks)."""
    if await db.budget_categories.count_documents({"user_id": DEMO_USER}) == 0:
        await _seed_main()
    if not await db.user_profiles.find_one({"user_id": DEMO_USER}):
        await db.user_profiles.insert_one(UserProfile().model_dump())
    if await db.tasks.count_documents({"user_id": DEMO_USER}) == 0:
        defaults = [
            {"title": "Study Math chapter 4", "target_minutes": 90, "progress": 40},
            {"title": "Read 20 pages", "target_minutes": 30, "progress": 70},
            {"title": "Workout", "target_minutes": 45, "progress": 0},
        ]
        for t in defaults:
            await db.tasks.insert_one(Task(user_id=DEMO_USER, **t).model_dump())


async def _seed_main():
    cats = [
        {"name": "Food", "allocated": 6000, "spent": 4230},
        {"name": "Transport", "allocated": 3000, "spent": 1650},
        {"name": "Entertainment", "allocated": 2000, "spent": 1200},
        {"name": "Education", "allocated": 4000, "spent": 2800},
        {"name": "Miscellaneous", "allocated": 1000, "spent": 520},
    ]
    for c in cats:
        await db.budget_categories.insert_one(BudgetCategory(user_id=DEMO_USER, **c).model_dump())

    subs = [
        {"name": "Spotify Student", "amount": 59, "renews_on": "2026-02-15", "icon": "music"},
        {"name": "Netflix (shared)", "amount": 199, "renews_on": "2026-02-22", "icon": "tv"},
        {"name": "ChatGPT Plus", "amount": 1650, "renews_on": "2026-03-01", "icon": "sparkles"},
        {"name": "Notion AI", "amount": 800, "renews_on": "2026-02-28", "icon": "book"},
    ]
    for s in subs:
        await db.subscriptions.insert_one(Subscription(user_id=DEMO_USER, **s).model_dump())

    sg = [
        {"name": "New Laptop", "target": 65000, "saved": 18500, "emoji": "💻"},
        {"name": "Study Abroad", "target": 200000, "saved": 42000, "emoji": "✈️"},
        {"name": "Emergency Fund", "target": 30000, "saved": 21000, "emoji": "🛡️"},
    ]
    for s in sg:
        await db.savings_goals.insert_one(SavingsGoal(user_id=DEMO_USER, **s).model_dump())

    splits = [
        {"title": "Pizza night", "total": 800, "with_person": "Rohan", "you_paid": 800, "owes_you": 400},
        {"title": "Uber to college", "total": 220, "with_person": "Priya", "you_paid": 0, "owes_you": -110},
        {"title": "Library prints", "total": 60, "with_person": "Aman", "you_paid": 60, "owes_you": 30},
    ]
    for s in splits:
        await db.split_bills.insert_one(SplitBill(user_id=DEMO_USER, **s).model_dump())

    goals = [
        {"title": "Study 4 hrs/day", "target": 100, "current": 75, "unit": "%"},
        {"title": "Sleep before 12am", "target": 100, "current": 40, "unit": "%", "status": "missed"},
        {"title": "Gym 3x/week", "target": 100, "current": 66, "unit": "%"},
        {"title": "Save ₹500/week", "target": 100, "current": 85, "unit": "%"},
    ]
    for g in goals:
        await db.goals.insert_one(Goal(user_id=DEMO_USER, **g).model_dump())

    # Sleep history for last 7 days
    for i in range(7):
        h = [7.5, 6.2, 5.5, 8.0, 6.5, 7.2, 6.8][i]
        q = "good" if h >= 7 else ("ok" if h >= 6 else "poor")
        d = (datetime.now(timezone.utc) - timedelta(days=6 - i)).isoformat()
        await db.sleep_entries.insert_one(SleepEntry(user_id=DEMO_USER, hours=h, quality=q, date=d).model_dump())

    # mood history
    moods = ["good", "okay", "great", "good", "bad", "good", "great"]
    for i, m in enumerate(moods):
        await db.mood_entries.insert_one(MoodEntry(
            user_id=DEMO_USER, mood=m, energy=60 + i, stress=70 - i * 5,
            motivation=60 + i, note="",
            created_at=(datetime.now(timezone.utc) - timedelta(days=6 - i)).isoformat()
        ).model_dump())

    # expenses
    today_exp = [
        {"amount": 60, "category": "food", "merchant": "Mess Express", "note": "lunch"},
        {"amount": 40, "category": "transport", "merchant": "Metro", "note": "to college"},
        {"amount": 80, "category": "food", "merchant": "Roll Zone", "note": "snack"},
    ]
    for e in today_exp:
        await db.expenses.insert_one(Expense(user_id=DEMO_USER, **e).model_dump())

    # profile (only if missing)
    if not await db.user_profiles.find_one({"user_id": DEMO_USER}):
        await db.user_profiles.insert_one(UserProfile().model_dump())

    # default daily tasks
    if await db.tasks.count_documents({"user_id": DEMO_USER}) == 0:
        defaults = [
            {"title": "Study Math chapter 4", "target_minutes": 90, "progress": 40},
            {"title": "Read 20 pages", "target_minutes": 30, "progress": 70},
            {"title": "Workout", "target_minutes": 45, "progress": 0},
        ]
        for t in defaults:
            await db.tasks.insert_one(Task(user_id=DEMO_USER, **t).model_dump())

    # profile (only if missing)
    if not await db.user_profiles.find_one({"user_id": DEMO_USER}):
        await db.user_profiles.insert_one(UserProfile().model_dump())

    # default daily tasks
    if await db.tasks.count_documents({"user_id": DEMO_USER}) == 0:
        defaults = [
            {"title": "Study Math chapter 4", "target_minutes": 90, "progress": 40},
            {"title": "Read 20 pages", "target_minutes": 30, "progress": 70},
            {"title": "Workout", "target_minutes": 45, "progress": 0},
        ]
        for t in defaults:
            await db.tasks.insert_one(Task(user_id=DEMO_USER, **t).model_dump())


@app.on_event("startup")
async def on_startup():
    # Ensure unique index on users.email for auth
    await db.users.create_index("email", unique=True, sparse=True)
    await seed_demo_data()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# ============ HELPERS ============
async def list_docs(coll, user_id, limit=200, sort_field=None):
    cursor = db[coll].find({"user_id": user_id}, {"_id": 0})
    if sort_field:
        cursor = cursor.sort(sort_field, -1)
    return await cursor.to_list(limit)


def detect_category(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["pizza", "burger", "mess", "food", "lunch", "dinner", "snack", "coffee", "tea", "thali"]):
        return "food"
    if any(k in t for k in ["uber", "ola", "metro", "bus", "auto", "taxi", "fuel", "petrol", "ride"]):
        return "transport"
    if any(k in t for k in ["movie", "netflix", "game", "concert", "ticket"]):
        return "entertainment"
    if any(k in t for k in ["book", "course", "udemy", "stationery", "tuition", "print"]):
        return "education"
    return "misc"


def simple_sentiment(text: str) -> tuple[str, float]:
    t = (text or "").lower()
    pos = sum(1 for w in ["happy", "great", "good", "love", "calm", "excited", "grateful", "proud", "joy"] if w in t)
    neg = sum(1 for w in ["sad", "stress", "tired", "anxious", "angry", "overwhelm", "bad", "hate", "lonely", "burnout"] if w in t)
    score = (pos - neg) / max(pos + neg, 1)
    if score > 0.2:
        return "positive", score
    if score < -0.2:
        return "negative", score
    return "neutral", score


# ============ MOOD ============
@api_router.post("/mood")
async def create_mood(entry: MoodEntry, user_id: str = Depends(get_current_user)):
    entry.user_id = user_id
    await db.mood_entries.insert_one(entry.model_dump())
    # Award gamification XP for mood check-in
    await gamification_service.award_xp(user_id, "mood_checkin")
    return entry


@api_router.get("/mood")
async def get_moods(limit: int = 30, user_id: str = Depends(get_current_user)):
    return await list_docs("mood_entries", user_id=user_id, limit=limit, sort_field="created_at")


# ============ EXPENSES ============
@api_router.post("/expenses")
async def create_expense(e: Expense, user_id: str = Depends(get_current_user)):
    e.user_id = user_id
    if not e.category or e.category == "auto":
        e.category = detect_category(f"{e.merchant} {e.note}")
    await db.expenses.insert_one(e.model_dump())
    # update budget spent
    await db.budget_categories.update_one(
        {"user_id": user_id, "name": {"$regex": f"^{e.category}$", "$options": "i"}},
        {"$inc": {"spent": e.amount}},
    )
    # Award gamification XP for expense log
    await gamification_service.award_xp(user_id, "expense_log")
    return e


@api_router.get("/expenses")
async def get_expenses(limit: int = 50, user_id: str = Depends(get_current_user)):
    return await list_docs("expenses", user_id=user_id, limit=limit, sort_field="created_at")


@api_router.post("/expenses/categorize")
async def categorize(payload: Dict[str, str], user_id: str = Depends(get_current_user)):
    text = payload.get("text", "")
    return {"category": detect_category(text)}


# ============ JOURNAL ============
@api_router.post("/journal")
async def create_journal(j: JournalEntry, user_id: str = Depends(get_current_user)):
    j.user_id = user_id
    sent, score = simple_sentiment(j.text)
    j.sentiment = sent
    j.sentiment_score = score
    await db.journal_entries.insert_one(j.model_dump())
    # Award gamification XP for journal entry
    await gamification_service.award_xp(user_id, "journal_entry")
    return j


@api_router.get("/journal")
async def get_journals(limit: int = 30, user_id: str = Depends(get_current_user)):
    return await list_docs("journal_entries", user_id=user_id, limit=limit, sort_field="created_at")


@api_router.get("/journal/weekly")
async def journal_weekly(user_id: str = Depends(get_current_user)):
    entries = await db.journal_entries.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    # bucket last 7 days
    today = datetime.now(timezone.utc).date()
    out = []
    for i in range(7):
        d = today - timedelta(days=6 - i)
        day_entries = [e for e in entries if datetime.fromisoformat(e["created_at"]).date() == d]
        avg = sum(e.get("sentiment_score") or 0 for e in day_entries) / max(len(day_entries), 1) if day_entries else 0
        out.append({"day": d.strftime("%a"), "score": round(avg, 2), "count": len(day_entries)})
    return out


# ============ GOALS ============
@api_router.get("/goals")
async def get_goals(user_id: str = Depends(get_current_user)):
    return await list_docs("goals", user_id=user_id)


@api_router.post("/goals")
async def create_goal(g: Goal, user_id: str = Depends(get_current_user)):
    g.user_id = user_id
    await db.goals.insert_one(g.model_dump())
    return g


@api_router.patch("/goals/{goal_id}")
async def update_goal(goal_id: str, payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    await db.goals.update_one({"id": goal_id, "user_id": user_id}, {"$set": payload})
    doc = await db.goals.find_one({"id": goal_id}, {"_id": 0})
    return doc


# ============ BUDGET ============
@api_router.get("/budget")
async def get_budget(user_id: str = Depends(get_current_user)):
    cats = await list_docs("budget_categories", user_id=user_id)
    total_alloc = sum(c["allocated"] for c in cats)
    total_spent = sum(c["spent"] for c in cats)
    return {
        "categories": cats,
        "total_allocated": total_alloc,
        "total_spent": total_spent,
        "remaining": total_alloc - total_spent,
        "percent_used": round(total_spent / total_alloc * 100, 1) if total_alloc else 0,
    }


@api_router.patch("/budget/{cat_id}")
async def update_budget(cat_id: str, payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    payload.pop("id", None); payload.pop("user_id", None)
    await db.budget_categories.update_one({"id": cat_id, "user_id": user_id}, {"$set": payload})
    return await db.budget_categories.find_one({"id": cat_id}, {"_id": 0})


@api_router.post("/budget")
async def create_budget_category(payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Name required")
    allocated = float(payload.get("allocated") or 0)
    cat = BudgetCategory(user_id=user_id, name=name, allocated=allocated, spent=0)
    await db.budget_categories.insert_one(cat.model_dump())
    return cat


@api_router.delete("/budget/{cat_id}")
async def delete_budget_category(cat_id: str, user_id: str = Depends(get_current_user)):
    res = await db.budget_categories.delete_one({"id": cat_id, "user_id": user_id})
    return {"deleted": res.deleted_count}


# ============ SUBSCRIPTIONS / SAVINGS / SPLITS ============
@api_router.get("/subscriptions")
async def get_subs(user_id: str = Depends(get_current_user)):
    subs = await list_docs("subscriptions", user_id=user_id)
    total = sum(s["amount"] for s in subs)
    return {"items": subs, "monthly_total": total}


@api_router.get("/savings")
async def get_savings(user_id: str = Depends(get_current_user)):
    return await list_docs("savings_goals", user_id=user_id)


@api_router.get("/splits")
async def get_splits(user_id: str = Depends(get_current_user)):
    items = await list_docs("split_bills", user_id=user_id)
    net = sum(s["owes_you"] for s in items)
    return {"items": items, "net_balance": net}


# ============ WELLNESS ============
@api_router.get("/wellness/scores")
async def wellness_scores(user_id: str = Depends(get_current_user)):
    moods = await db.mood_entries.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(7)
    sleeps = await db.sleep_entries.find({"user_id": user_id}, {"_id": 0}).sort("date", -1).to_list(7)
    avg_sleep = sum(s["hours"] for s in sleeps) / max(len(sleeps), 1) if sleeps else 7
    avg_stress = sum(m.get("stress", 50) for m in moods) / max(len(moods), 1) if moods else 50
    sleep_score = round(min(100, (avg_sleep / 8) * 100))
    stress_score = round(100 - avg_stress)
    burnout_score = round((sleep_score + stress_score) / 2)
    return {
        "sleep_score": sleep_score,
        "stress_score": stress_score,
        "burnout_score": burnout_score,
        "avg_sleep_hours": round(avg_sleep, 1),
        "streak_days": await compute_streak(user_id),
    }


@api_router.get("/sleep/weekly")
async def sleep_weekly(user_id: str = Depends(get_current_user)):
    sleeps = await db.sleep_entries.find({"user_id": user_id}, {"_id": 0}).sort("date", 1).to_list(7)
    out = []
    for s in sleeps:
        d = datetime.fromisoformat(s["date"]).strftime("%a")
        out.append({"day": d, "hours": s["hours"], "quality": s["quality"]})
    return out


@api_router.post("/sleep")
async def add_sleep(s: SleepEntry, user_id: str = Depends(get_current_user)):
    s.user_id = user_id
    await db.sleep_entries.insert_one(s.model_dump())
    return s


@api_router.get("/mood/weekly")
async def mood_weekly(user_id: str = Depends(get_current_user)):
    moods = await db.mood_entries.find({"user_id": user_id}, {"_id": 0}).sort("created_at", 1).to_list(7)
    return [{"day": datetime.fromisoformat(m["created_at"]).strftime("%a"), "mood": m["mood"],
             "stress": m.get("stress", 50)} for m in moods]


# ============ EXERCISES (physical wellbeing) ============
@api_router.get("/exercises")
async def get_exercises(user_id: str = Depends(get_current_user)):
    return await db.exercises.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.post("/exercises")
async def create_exercise(payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Name required")
    e = Exercise(
        user_id=user_id, name=name,
        body_part=payload.get("body_part") or "full",
        target_minutes=int(payload.get("target_minutes") or 30),
    )
    await db.exercises.insert_one(e.model_dump())
    return e


@api_router.patch("/exercises/{eid}")
async def update_exercise(eid: str, payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    payload.pop("id", None); payload.pop("user_id", None)
    if "progress" in payload:
        payload["progress"] = max(0, min(100, int(payload["progress"])))
        payload["status"] = "done" if payload["progress"] >= 100 else "active"
    await db.exercises.update_one({"id": eid, "user_id": user_id}, {"$set": payload})
    return await db.exercises.find_one({"id": eid}, {"_id": 0})


@api_router.delete("/exercises/{eid}")
async def delete_exercise(eid: str, user_id: str = Depends(get_current_user)):
    await db.exercises.delete_one({"id": eid, "user_id": user_id})
    await db.exercise_sessions.delete_many({"exercise_id": eid, "user_id": user_id})
    return {"deleted": 1}


@api_router.post("/exercises/{eid}/start")
async def start_exercise_session(eid: str, user_id: str = Depends(get_current_user)):
    await db.exercise_sessions.update_many(
        {"exercise_id": eid, "user_id": user_id, "ended_at": None},
        {"$set": {"ended_at": now_iso()}},
    )
    s = ExerciseSession(exercise_id=eid, user_id=user_id)
    await db.exercise_sessions.insert_one(s.model_dump())
    return s


@api_router.post("/exercises/{eid}/stop")
async def stop_exercise_session(eid: str, payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    open_s = await db.exercise_sessions.find_one(
        {"exercise_id": eid, "user_id": user_id, "ended_at": None},
        {"_id": 0}, sort=[("started_at", -1)],
    )
    if not open_s:
        raise HTTPException(404, "No active session")
    ended = now_iso()
    started_dt = datetime.fromisoformat(open_s["started_at"])
    elapsed = int((datetime.fromisoformat(ended) - started_dt).total_seconds())
    comment = (payload.get("comment") or "").strip()
    await db.exercise_sessions.update_one(
        {"id": open_s["id"]},
        {"$set": {"ended_at": ended, "elapsed_seconds": elapsed, "comment": comment}},
    )
    return {**open_s, "ended_at": ended, "elapsed_seconds": elapsed, "comment": comment}


@api_router.get("/exercises/{eid}/sessions")
async def get_exercise_sessions(eid: str, user_id: str = Depends(get_current_user)):
    sessions = await db.exercise_sessions.find(
        {"exercise_id": eid, "user_id": user_id}, {"_id": 0}
    ).sort("started_at", -1).to_list(100)
    total = sum(s.get("elapsed_seconds", 0) for s in sessions)
    active = next((s for s in sessions if not s.get("ended_at")), None)
    return {"sessions": sessions, "total_seconds": total, "active": active}


@api_router.get("/exercises/summary")
async def exercises_summary(user_id: str = Depends(get_current_user)):
    """Today's snapshot: total active minutes, sedentary warning, upper/lower split (last 7d)."""
    today = datetime.now(timezone.utc)
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    sessions = await db.exercise_sessions.find(
        {"user_id": user_id, "started_at": {"$gte": today_start}, "ended_at": {"$ne": None}}, {"_id": 0},
    ).to_list(200)
    today_minutes = sum(s.get("elapsed_seconds", 0) for s in sessions) // 60

    # last 7 days upper vs lower vs full
    since = (today - timedelta(days=7)).isoformat()
    last7 = await db.exercise_sessions.find(
        {"user_id": user_id, "started_at": {"$gte": since}, "ended_at": {"$ne": None}}, {"_id": 0},
    ).to_list(500)
    ex_ids = {s["exercise_id"] for s in last7}
    exs = await db.exercises.find({"id": {"$in": list(ex_ids)}, "user_id": user_id}, {"_id": 0}).to_list(100)
    bp = {e["id"]: e.get("body_part", "full") for e in exs}
    by_part = {"upper": 0, "lower": 0, "cardio": 0, "full": 0}
    for s in last7:
        part = bp.get(s["exercise_id"], "full")
        by_part[part] = by_part.get(part, 0) + s.get("elapsed_seconds", 0) // 60

    # sedentary: less than 20 minutes today is "sedentary warning"
    sedentary = today_minutes < 20
    balanced = by_part["upper"] > 0 and by_part["lower"] > 0
    return {
        "today_minutes": today_minutes,
        "sedentary": sedentary,
        "sedentary_warning": "You've been sedentary today — try a quick 10-min walk." if sedentary else "Great — you've moved enough today.",
        "by_part_7d": by_part,
        "balanced_7d": balanced,
        "imbalance_note": None if balanced else "You haven't covered both upper and lower body this week. Add the missing group tomorrow.",
    }


# ============ ROUTINE (dynamic habits) ============
@api_router.get("/routine/habits")
async def routine_habits(user_id: str = Depends(get_current_user)):
    """Compute habit consistency from real data for last 7 days."""
    today = datetime.now(timezone.utc)
    since = today - timedelta(days=7)
    since_iso = since.isoformat()

    sleeps = await db.sleep_entries.find({"user_id": user_id}, {"_id": 0}).sort("date", -1).to_list(7)
    journals = await db.journal_entries.find(
        {"user_id": user_id, "created_at": {"$gte": since_iso}}, {"_id": 0},
    ).to_list(100)
    exercises = await db.exercise_sessions.find(
        {"user_id": user_id, "started_at": {"$gte": since_iso}, "ended_at": {"$ne": None}}, {"_id": 0},
    ).to_list(200)
    moods = await db.mood_entries.find(
        {"user_id": user_id, "created_at": {"$gte": since_iso}}, {"_id": 0},
    ).to_list(50)

    days_with_sleep_7h = len([s for s in sleeps if s.get("hours", 0) >= 7])
    exercise_days = len({datetime.fromisoformat(s["started_at"]).date() for s in exercises})
    journal_days = len({datetime.fromisoformat(j["created_at"]).date() for j in journals})
    checkin_days = len({datetime.fromisoformat(m["created_at"]).date() for m in moods})

    return [
        {"habit": "7+ hour sleep", "value": round(days_with_sleep_7h / 7 * 100)},
        {"habit": "Exercise", "value": round(exercise_days / 7 * 100)},
        {"habit": "Daily journal", "value": round(journal_days / 7 * 100)},
        {"habit": "Daily check-in", "value": round(checkin_days / 7 * 100)},
    ]


# ============ WELLNESS AI CARDS ============
async def _generate_wellness_cards(card_kind: str, user_id: str) -> List[Dict[str, str]]:
    """Use Wellness Buddy (Claude) to produce 2 short personalized cards.

    Falls back to safe defaults on any error so the UI never blocks.
    """
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0}) or {}
    pattern = profile.get("your_pattern", {}) or {}
    moods = await db.mood_entries.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(7)
    tasks = await db.tasks.find({"user_id": user_id}, {"_id": 0}).to_list(20)
    goals = await db.goals.find({"user_id": user_id}, {"_id": 0}).to_list(20)
    sleeps = await db.sleep_entries.find({"user_id": user_id}, {"_id": 0}).sort("date", -1).to_list(7)

    user_name = profile.get("name", "User")
    context = {
        "pattern": pattern,
        "recent_moods": [{"mood": m["mood"], "stress": m.get("stress", 50)} for m in moods[:5]],
        "active_tasks": [{"title": t["title"], "progress": t["progress"]} for t in tasks if t.get("status") != "done"][:5],
        "goals": [{"title": g["title"], "current": g["current"], "status": g["status"]} for g in goals][:5],
        "avg_sleep": round(sum(s["hours"] for s in sleeps) / max(len(sleeps), 1), 1) if sleeps else 7,
    }
    kind_hint = {
        "stress": "two short cards: one MOTIVATIONAL (encouragement), one PRACTICAL (a doable 5-min plan).",
        "routine": "two short cards: one habit insight, one tiny next-step plan.",
    }.get(card_kind, "two helpful cards.")
    sys = (
        "You are Wellness Buddy. Respond with EXACTLY this JSON shape and nothing else: "
        '[{"kind":"motivational","title":"...","text":"..."},{"kind":"plan","title":"...","text":"..."}]. '
        f"Each text <= 30 words. Speak warmly to {user_name}. Use the user's saved pattern and recent data."
    )
    user_msg = f"Context: {context}\nWrite {kind_hint}"
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"{user_id}-wellness-cards-{card_kind}",
            system_message=sys,
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        full = ""
        async for ev in chat.stream_message(UserMessage(text=user_msg)):
            if isinstance(ev, TextDelta):
                full += ev.content
            elif isinstance(ev, StreamDone):
                break
        import json as _json, re as _re
        # extract JSON array
        m = _re.search(r"\[.*\]", full, _re.DOTALL)
        if m:
            data = _json.loads(m.group(0))
            if isinstance(data, list) and len(data) >= 1:
                return data[:2]
    except Exception as e:
        logger.warning(f"wellness cards generation failed: {e}")
    # fallback
    return [
        {"kind": "motivational", "title": "You're doing better than you think",
         "text": "Tiny wins compound. One small step in the next hour beats a perfect plan tomorrow."},
        {"kind": "plan", "title": "5-min reset",
         "text": "Stand up, drink water, 10 slow breaths, write one line in your journal. Then resume."},
    ]


@api_router.get("/wellness/cards")
async def wellness_cards(kind: str = "stress", user_id: str = Depends(get_current_user)):
    return await _generate_wellness_cards(kind, user_id)


# ============ DISCOVER (static seed) ============
@api_router.get("/discover/food")
async def discover_food(user_id: str = Depends(get_current_user)):
    return [
        {"name": "Mess Express", "price": 50, "rating": 4.3, "distance": "0.2 km", "tag": "Full meal", "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400"},
        {"name": "Roll Zone", "price": 40, "rating": 4.5, "distance": "0.4 km", "tag": "Rolls", "image": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=400"},
        {"name": "Student Thali", "price": 60, "rating": 4.2, "distance": "0.6 km", "tag": "Thali", "image": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400"},
        {"name": "Coffee Cart", "price": 25, "rating": 4.1, "distance": "0.1 km", "tag": "Drinks", "image": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400"},
    ]


@api_router.get("/discover/travel")
async def discover_travel(user_id: str = Depends(get_current_user)):
    return [
        {"mode": "Metro", "cost": 30, "time": "25 min", "icon": "train", "safe": True},
        {"mode": "Cycle", "cost": 0, "time": "40 min", "icon": "bike", "safe": True},
        {"mode": "Rideshare", "cost": 120, "time": "18 min", "icon": "car", "safe": True},
        {"mode": "Walk", "cost": 0, "time": "55 min", "icon": "footprints", "safe": False},
    ]


@api_router.get("/discover/snacks")
async def discover_snacks(user_id: str = Depends(get_current_user)):
    return [
        {"name": "Almonds + Banana", "nutrition": 9, "budget": 8, "tag": "Brain food"},
        {"name": "Roasted Chana", "nutrition": 8, "budget": 10, "tag": "Protein"},
        {"name": "Dark Chocolate", "nutrition": 7, "budget": 6, "tag": "Focus"},
        {"name": "Greek Yogurt", "nutrition": 9, "budget": 5, "tag": "Calm"},
    ]


@api_router.get("/discover/activities")
async def discover_activities(user_id: str = Depends(get_current_user)):
    return [
        {"name": "5-min stretch", "duration": "5 min", "type": "movement"},
        {"name": "Box breathing", "duration": "3 min", "type": "calm"},
        {"name": "Quick sketch", "duration": "10 min", "type": "creative"},
        {"name": "Walk outdoors", "duration": "15 min", "type": "movement"},
    ]


@api_router.get("/discover/campus")
async def discover_campus(user_id: str = Depends(get_current_user)):
    return [
        {"name": "Counseling Center", "type": "wellness", "available": True},
        {"name": "Peer Tutoring", "type": "study", "available": True},
        {"name": "Food Pantry", "type": "aid", "available": True},
        {"name": "Financial Aid Office", "type": "aid", "available": False},
    ]


# ============ PROFILE ============
async def compute_streak(user_id: str) -> int:
    """Count consecutive days ending today or yesterday with at least one mood entry."""
    moods = await db.mood_entries.find(
        {"user_id": user_id}, {"_id": 0, "created_at": 1}
    ).sort("created_at", -1).to_list(400)
    if not moods:
        return 0
    dates = sorted({datetime.fromisoformat(m["created_at"]).date() for m in moods}, reverse=True)
    today = datetime.now(timezone.utc).date()
    if (today - dates[0]).days > 1:
        return 0
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak


@api_router.get("/profile")
async def get_profile(user_id: str = Depends(get_current_user)):
    p = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0})
    if not p:
        p = UserProfile(user_id=user_id).model_dump()
        await db.user_profiles.insert_one(p)
    # ensure new keys exist for older docs
    p.setdefault("onboarded", False)
    p.setdefault("your_pattern", {})
    # compute live streak
    p["streak_days"] = await compute_streak(user_id)
    return p


@api_router.patch("/profile")
async def update_profile(payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    payload.pop("user_id", None)
    payload.pop("streak_days", None)  # streak is always computed
    # avatar initial follows first letter of name
    if "name" in payload and payload["name"]:
        payload["avatar_initial"] = payload["name"].strip()[:1].upper()
    await db.user_profiles.update_one({"user_id": user_id}, {"$set": payload}, upsert=True)
    return await get_profile(user_id)


@api_router.post("/profile/onboard")
async def onboard(payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    """Persist Your-Pattern, mark onboarded=true, optionally create Goal entries.

    Accepts {name, your_pattern, goals: [str | {title, target, current?}]}.
    Each goal becomes a row in /api/goals so the home Goals tab is driven from onboarding.
    """
    update = {"onboarded": True}
    if payload.get("name"):
        update["name"] = payload["name"].strip()
        update["avatar_initial"] = update["name"][:1].upper()
    if isinstance(payload.get("your_pattern"), dict):
        update["your_pattern"] = payload["your_pattern"]
    await db.user_profiles.update_one({"user_id": user_id}, {"$set": update}, upsert=True)

    goals_in = payload.get("goals") or []
    if goals_in:
        # replace any previously onboarding-created goals so re-running stays clean
        await db.goals.delete_many({"user_id": user_id, "source": "onboard"})
        for g in goals_in:
            if isinstance(g, str):
                title = g.strip()
                if not title:
                    continue
                goal = Goal(user_id=user_id, title=title, target=100, current=0)
            elif isinstance(g, dict) and g.get("title"):
                goal = Goal(
                    user_id=user_id, title=g["title"].strip(),
                    target=float(g.get("target") or 100),
                    current=float(g.get("current") or 0),
                )
            else:
                continue
            doc = goal.model_dump()
            doc["source"] = "onboard"
            await db.goals.insert_one(doc)
    return await get_profile(user_id)


# ============ TASKS ============
@api_router.get("/tasks")
async def get_tasks(user_id: str = Depends(get_current_user)):
    return await db.tasks.find({"user_id": user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)


@api_router.post("/tasks")
async def create_task(payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    title = (payload.get("title") or "").strip()
    if not title:
        raise HTTPException(400, "Title required")
    t = Task(user_id=user_id, title=title,
             target_minutes=int(payload.get("target_minutes") or 60),
             progress=int(payload.get("progress") or 0))
    await db.tasks.insert_one(t.model_dump())
    return t


@api_router.patch("/tasks/{task_id}")
async def update_task(task_id: str, payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    payload.pop("id", None); payload.pop("user_id", None)
    if "progress" in payload:
        payload["progress"] = max(0, min(100, int(payload["progress"])))
        if payload["progress"] >= 100:
            payload["status"] = "done"
            payload["completed_at"] = now_iso()
        else:
            payload["status"] = "active"
            payload["completed_at"] = None
    await db.tasks.update_one({"id": task_id, "user_id": user_id}, {"$set": payload})
    return await db.tasks.find_one({"id": task_id}, {"_id": 0})


@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, user_id: str = Depends(get_current_user)):
    await db.tasks.delete_one({"id": task_id, "user_id": user_id})
    await db.task_sessions.delete_many({"task_id": task_id, "user_id": user_id})
    return {"deleted": 1}


@api_router.post("/tasks/{task_id}/start")
async def start_task_session(task_id: str, user_id: str = Depends(get_current_user)):
    # close any open session for this task first
    await db.task_sessions.update_many(
        {"task_id": task_id, "user_id": user_id, "ended_at": None},
        {"$set": {"ended_at": now_iso()}},
    )
    s = TaskSession(task_id=task_id, user_id=user_id)
    await db.task_sessions.insert_one(s.model_dump())
    return s


@api_router.post("/tasks/{task_id}/stop")
async def stop_task_session(task_id: str, payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    open_s = await db.task_sessions.find_one(
        {"task_id": task_id, "user_id": user_id, "ended_at": None},
        {"_id": 0}, sort=[("started_at", -1)],
    )
    if not open_s:
        raise HTTPException(404, "No active session")
    ended = now_iso()
    started_dt = datetime.fromisoformat(open_s["started_at"])
    elapsed = int((datetime.fromisoformat(ended) - started_dt).total_seconds())
    comment = (payload.get("comment") or "").strip()
    await db.task_sessions.update_one(
        {"id": open_s["id"]},
        {"$set": {"ended_at": ended, "elapsed_seconds": elapsed, "comment": comment}},
    )
    return {**open_s, "ended_at": ended, "elapsed_seconds": elapsed, "comment": comment}


@api_router.get("/tasks/{task_id}/sessions")
async def get_task_sessions(task_id: str, user_id: str = Depends(get_current_user)):
    sessions = await db.task_sessions.find(
        {"task_id": task_id, "user_id": user_id}, {"_id": 0}
    ).sort("started_at", -1).to_list(100)
    total = sum(s.get("elapsed_seconds", 0) for s in sessions)
    active = next((s for s in sessions if not s.get("ended_at")), None)
    return {"sessions": sessions, "total_seconds": total, "active": active}


# ============ AUTO-BALANCE BUDGET ============
@api_router.post("/budget/auto-balance")
async def auto_balance(payload: Dict[str, Any], user_id: str = Depends(get_current_user)):
    """Distribute income using 50/30/20 rule across user categories.

    needs (50%): Food, Transport, Education, Housing/Rent
    wants (30%): Entertainment, Misc, Subscriptions
    savings (20%): Savings (single bucket, ensures category exists)
    """
    income = float(payload.get("income") or 0)
    if income <= 0:
        raise HTTPException(400, "Income must be > 0")
    # persist on profile
    await db.user_profiles.update_one(
        {"user_id": user_id}, {"$set": {"monthly_income": income}}, upsert=True,
    )
    NEEDS = {"food", "transport", "education", "rent", "housing", "groceries"}
    WANTS = {"entertainment", "miscellaneous", "misc", "subscriptions", "shopping"}
    cats = await list_docs("budget_categories", user_id=user_id)
    needs = [c for c in cats if c["name"].lower() in NEEDS]
    wants = [c for c in cats if c["name"].lower() in WANTS]
    savings = [c for c in cats if c["name"].lower() in {"savings", "save", "savings goal"}]

    def split(pool, total):
        if not pool:
            return
        per = round(total / len(pool))
        # assign rounding remainder to last entry so total == budget exactly
        last = round(total - per * (len(pool) - 1))
        for i, c in enumerate(pool):
            asyncio_updates.append((c["id"], last if i == len(pool) - 1 else per))

    asyncio_updates = []
    split(needs, income * 0.5)
    split(wants, income * 0.3)
    split(savings, income * 0.2)

    if not savings:
        # ensure a Savings category exists
        new_save = BudgetCategory(user_id=user_id, name="Savings", allocated=round(income * 0.2))
        await db.budget_categories.insert_one(new_save.model_dump())

    for cid, amount in asyncio_updates:
        await db.budget_categories.update_one(
            {"id": cid, "user_id": user_id}, {"$set": {"allocated": amount}},
        )
    return {"ok": True, "income": income, "rule": "50/30/20"}


# ============ CASHFLOW (dynamic) ============
@api_router.get("/cashflow")
async def cashflow(user_id: str = Depends(get_current_user)):
    cats = await list_docs("budget_categories", user_id=user_id)
    total_alloc = sum(c["allocated"] for c in cats) or 0
    total_spent = sum(c["spent"] for c in cats) or 0
    today = datetime.now(timezone.utc)
    last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    days_left = max(1, (last_day - today).days)
    days_elapsed = max(1, today.day)
    daily_avg = total_spent / days_elapsed
    forecast_total = total_spent + daily_avg * days_left
    forecast_remaining = round(total_alloc - forecast_total)
    overspend = sum(max(0, c["spent"] - c["allocated"] * 0.9) for c in cats)
    underspend = sum(max(0, c["allocated"] * 0.5 - c["spent"]) for c in cats)
    # 14-day spending trend (last 14 days)
    since = (today - timedelta(days=14)).isoformat()
    expenses = await db.expenses.find(
        {"user_id": user_id, "created_at": {"$gte": since}}, {"_id": 0},
    ).to_list(500)
    trend = []
    for i in range(14):
        d = (today - timedelta(days=13 - i)).date()
        day_total = sum(
            e["amount"] for e in expenses
            if datetime.fromisoformat(e["created_at"]).date() == d
        )
        trend.append({"d": d.strftime("%d"), "v": round(day_total)})
    return {
        "forecast_remaining": forecast_remaining,
        "overspend": round(overspend),
        "underspend": round(underspend),
        "days_left": days_left,
        "trend": trend,
    }


# ============ FITNESS (dynamic) ============
@api_router.get("/fitness/today")
async def fitness_today(user_id: str = Depends(get_current_user)):
    # Deterministic per-day mock so values feel "live" but are stable
    today = datetime.now(timezone.utc).date()
    seed = today.toordinal()
    steps = 5000 + (seed * 137) % 6000
    active = 20 + (seed * 11) % 50
    sedentary = round(8 - active / 30, 1)
    body = [(seed * (i + 3)) % 90 + 10 for i in range(7)]
    return {"steps": steps, "active_minutes": active, "sedentary_hours": sedentary, "body_balance": body}


# ============ HELPER (life balance + insights) ============
@api_router.get("/life-balance")
async def life_balance(user_id: str = Depends(get_current_user)):
    cats = await list_docs("budget_categories", user_id=user_id)
    spent_pct = sum(c["spent"] for c in cats) / max(sum(c["allocated"] for c in cats), 1) * 100
    finance = max(0, 100 - (spent_pct - 70))  # less spend = better
    finance = round(min(100, max(0, finance)))
    w = await wellness_scores(user_id)
    wellness = w["burnout_score"]
    goals = await list_docs("goals", user_id=user_id)
    productivity = round(sum(g["current"] for g in goals) / max(len(goals), 1)) if goals else 60
    discover = 78
    overall = round((finance + wellness + productivity + discover) / 4)
    return {
        "overall": overall,
        "domains": [
            {"name": "Finance", "score": finance},
            {"name": "Wellness", "score": wellness},
            {"name": "Productivity", "score": productivity},
            {"name": "Discover", "score": discover},
        ],
    }


@api_router.get("/insights/daily")
async def daily_insights(user_id: str = Depends(get_current_user)):
    from context_engine import assemble_context, detect_correlations

    try:
        # Assemble user context for generating insights
        ctx = await assemble_context(db, user_id)
        raw = ctx.get("raw_data", {})

        # Generate base insight cards from real user data
        insights = []

        # Financial tip
        expense_data = raw.get("expenses", {})
        if expense_data:
            total_spent = expense_data.get("total_spent", 0)
            by_category = expense_data.get("by_category", {})
            top_cat = max(by_category, key=by_category.get) if by_category else "misc"
            top_amount = by_category.get(top_cat, 0) if by_category else 0
            if total_spent > 0:
                pct = int(top_amount / total_spent * 100)
                insights.append({
                    "domain": "finance",
                    "title": f"{top_cat.capitalize()} spending is {pct}% of total",
                    "detail": f"You spent ₹{int(top_amount)} on {top_cat} this week. Consider setting a budget limit.",
                    "icon": "trending-up",
                })
            else:
                insights.append({
                    "domain": "finance",
                    "title": "Track your expenses",
                    "detail": "Start logging expenses to get personalized finance tips.",
                    "icon": "wallet",
                })
        else:
            insights.append({
                "domain": "finance",
                "title": "Track your expenses",
                "detail": "Start logging expenses to get personalized finance tips.",
                "icon": "wallet",
            })

        # Wellness suggestion
        mood_data = raw.get("mood", {})
        sleep_data = raw.get("sleep", {})
        if mood_data or sleep_data:
            avg_stress = mood_data.get("avg_stress", 50) if mood_data else 50
            avg_sleep = sleep_data.get("avg_hours", 7) if sleep_data else 7
            if avg_stress > 60:
                insights.append({
                    "domain": "wellness",
                    "title": f"Stress level at {int(avg_stress)}/100",
                    "detail": "Try a 5-min breathing exercise or a short walk today.",
                    "icon": "heart",
                })
            elif avg_sleep < 7:
                insights.append({
                    "domain": "wellness",
                    "title": f"Sleep averaging {avg_sleep:.1f}h",
                    "detail": "Aim for a consistent bedtime tonight to improve rest.",
                    "icon": "moon",
                })
            else:
                insights.append({
                    "domain": "wellness",
                    "title": "Wellness on track",
                    "detail": "Keep up the good sleep and stress management!",
                    "icon": "smile",
                })
        else:
            insights.append({
                "domain": "wellness",
                "title": "Check in with your mood",
                "detail": "Log your mood daily to get wellness insights.",
                "icon": "heart",
            })

        # Productivity recommendation
        task_data = raw.get("tasks", {})
        if task_data:
            completion_rate = task_data.get("completion_rate", 0)
            insights.append({
                "domain": "productivity",
                "title": f"Tasks {int(completion_rate)}% complete",
                "detail": "Focus on your top priority task first thing tomorrow." if completion_rate < 70 else "Great progress! Keep the momentum going.",
                "icon": "target",
            })
        else:
            insights.append({
                "domain": "productivity",
                "title": "Set your goals",
                "detail": "Add tasks to track your productivity this week.",
                "icon": "target",
            })

        # Detect and append correlation insights
        correlation_insights = await detect_correlations(db, user_id)
        for corr in correlation_insights:
            insights.append({
                "domain": corr.get("domain", "correlation"),
                "title": corr["title"],
                "detail": corr["detail"],
                "icon": corr.get("icon", "alert-circle"),
            })

        return insights

    except Exception as e:
        logger.error(f"Error generating daily insights for {user_id}: {e}")
        # Fallback to basic insights on error
        return [
            {"domain": "finance", "title": "Track your spending", "detail": "Log expenses to get personalized tips.", "icon": "wallet"},
            {"domain": "wellness", "title": "Check in today", "detail": "Log your mood for wellness insights.", "icon": "heart"},
            {"domain": "productivity", "title": "Stay on track", "detail": "Review your goals for the week.", "icon": "target"},
        ]


@api_router.get("/insights/weekly")
async def weekly_insights(user_id: str = Depends(get_current_user)):
    return {
        "scorecard": [
            {"domain": "Finance", "score": 78, "trend": "+4"},
            {"domain": "Wellness", "score": 71, "trend": "-3"},
            {"domain": "Productivity", "score": 66, "trend": "+8"},
            {"domain": "Discover", "score": 82, "trend": "+1"},
        ],
        "highlights": [
            "Saved ₹420 by cooking 3 meals at home",
            "Slept 7+ hours on 4 nights",
            "Completed 18 of 25 Pomodoro sessions",
        ],
        "next_week_focus": "Protect bedtime: lights out by 11:30pm on weekdays.",
    }


# ============ CHATBOT (SSE streaming) ============

# Distinct system prompts per buddy with explicit personality requirements (Req 9.3)
BUDDY_MODELS = {
    "finance": (
        "openai",
        "gpt-5.2",
        "You are Finance Buddy, a wise owl 🦉 helping a student manage money in Indian rupees (₹). "
        "Be concise, friendly, use bullet points, give concrete numbers. "
        "Topics: budgeting, expenses, savings goals, splitting bills, subscriptions, cash flow.\n\n"
        "CRITICAL PERSONALITY RULES:\n"
        "- You MUST include at least one specific numeric value (₹ amount, percentage, or budget figure) in EVERY response.\n"
        "- You MUST reference a budget category, savings target, or spending figure in every reply.\n"
        "- End with one actionable tip that includes a number (e.g., 'Save ₹200 this week by...').\n"
        "- If the user asks about non-financial topics, still tie your answer back to a financial angle with a number."
    ),
    "wellness": (
        "anthropic",
        "claude-sonnet-4-5-20250929",
        "You are Wellness Buddy, a calm and empathetic cloud ☁️ supporting a student's mental wellbeing. "
        "Topics: stress, sleep, burnout, focus, mood, breathing. "
        "If crisis is detected, gently suggest reaching out to campus counseling. Keep replies warm and under 120 words.\n\n"
        "CRITICAL PERSONALITY RULES:\n"
        "- You MUST ALWAYS validate and acknowledge the user's feelings BEFORE offering any suggestion or advice.\n"
        "- Start every response with empathetic, validating language (e.g., 'I hear you...', 'That sounds really tough...', "
        "'It makes sense that you feel...', 'Your feelings are completely valid...').\n"
        "- Only AFTER validating, offer a small, doable step or suggestion.\n"
        "- Never jump straight to advice without first acknowledging the user's emotional state."
    ),
    "discover": (
        "gemini",
        "gemini-3-flash-preview",
        "You are Discover Buddy, an upbeat compass 🧭 helping a student find cheap food, safe transport, "
        "student deals, and campus resources in India. Be punchy and enthusiastic.\n\n"
        "CRITICAL PERSONALITY RULES:\n"
        "- You MUST include at least one concrete recommendation with a specific price in ₹ OR a specific location/place name in EVERY response.\n"
        "- List 2-3 concrete options whenever possible, each with prices in ₹ or specific addresses/landmarks.\n"
        "- Format recommendations clearly (e.g., '🍕 Dominos student deal: ₹199 for medium pizza at MG Road outlet').\n"
        "- End with a question to keep the conversation going.\n"
        "- Never give vague suggestions without at least one price or location."
    ),
    "helper": (
        "openai",
        "gpt-5.2",
        "You are Helper Buddy, the orchestrator of the super-app PocketBuddy. "
        "You synthesize insights across Finance, Wellness, Discover and Productivity.\n\n"
        "CRITICAL PERSONALITY RULES:\n"
        "- You MUST reference at least TWO different life domains (finance, wellness, productivity, discovery) in EVERY response.\n"
        "- Always reason briefly across domains (e.g., 'Looking at your finances + sleep patterns...', "
        "'Connecting your spending habits with your wellness goals...').\n"
        "- Show how different areas of the user's life connect and affect each other.\n"
        "- End with a single 'Tomorrow do this:' line that incorporates multiple domains.\n"
        "- Never respond about only one domain in isolation."
    ),
}


# ---- Conversation memory topic search for "remember when" references (Req 9.4) ----
MEMORY_TRIGGER_PHRASES = [
    "remember when",
    "last time",
    "we talked about",
    "you said",
    "i mentioned",
    "you told me",
    "we discussed",
    "earlier you",
    "previously",
    "before you said",
    "you recommended",
    "you suggested",
]


def _detect_memory_reference(message: str) -> bool:
    """Check if the user's message references a previous conversation."""
    msg_lower = message.lower()
    return any(phrase in msg_lower for phrase in MEMORY_TRIGGER_PHRASES)


def _extract_search_keywords(message: str) -> list:
    """Extract meaningful keywords from the user's message for topic search."""
    # Remove common trigger phrases to get the actual topic
    msg_lower = message.lower()
    for phrase in MEMORY_TRIGGER_PHRASES:
        msg_lower = msg_lower.replace(phrase, "")

    # Remove common stop words and short words
    stop_words = {
        "i", "me", "my", "we", "you", "the", "a", "an", "is", "was", "are",
        "were", "been", "be", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "shall", "can",
        "about", "that", "this", "what", "when", "where", "how", "who",
        "which", "there", "here", "just", "also", "very", "really", "so",
        "but", "and", "or", "if", "then", "than", "too", "not", "no", "yes",
        "it", "its", "to", "of", "in", "on", "at", "for", "with", "from",
    }
    words = [w.strip("?.!,;:'\"") for w in msg_lower.split()]
    keywords = [w for w in words if w and len(w) > 2 and w not in stop_words]
    return keywords


async def _search_conversation_history(db, user_id: str, buddy: str, message: str) -> str:
    """
    Search the last 50 messages for content matching the user's reference.
    Returns formatted context string with matching messages, or empty string.
    """
    try:
        keywords = _extract_search_keywords(message)
        if not keywords:
            return ""

        # Fetch the last 50 messages for this user/buddy
        cursor = db.chat_messages.find(
            {"user_id": user_id, "buddy": buddy},
            {"_id": 0, "role": 1, "content": 1, "created_at": 1},
        ).sort("created_at", -1).limit(50)
        messages = await cursor.to_list(50)

        if not messages:
            return ""

        # Score each message by keyword match count
        matching_messages = []
        for msg in messages:
            content_lower = msg.get("content", "").lower()
            match_count = sum(1 for kw in keywords if kw in content_lower)
            if match_count > 0:
                matching_messages.append((match_count, msg))

        if not matching_messages:
            return ""

        # Sort by relevance (most matches first) and take top 3
        matching_messages.sort(key=lambda x: x[0], reverse=True)
        top_matches = matching_messages[:3]

        # Format as context block
        context_lines = []
        for _, msg in top_matches:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            content_preview = msg["content"][:200]  # Limit length
            context_lines.append(f"  {role_label}: {content_preview}")

        return (
            "\n\n[Relevant prior conversation the user is referencing:\n"
            + "\n".join(context_lines)
            + "\n]\n"
            "Use this context to acknowledge and build upon what was previously discussed."
        )
    except Exception as e:
        logger.warning(f"Failed to search conversation history: {e}")
        return ""


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@api_router.post("/chat/{buddy}")
async def chat_stream(buddy: str, req: ChatRequest, user_id: str = Depends(get_current_user)):
    if buddy not in BUDDY_MODELS:
        raise HTTPException(404, "Unknown buddy")
    provider, model, base_system = BUDDY_MODELS[buddy]
    session_id = req.session_id or f"{user_id}-{buddy}"

    # inject user's "Your Pattern" + name so chat replies stay consistent
    profile = await db.user_profiles.find_one({"user_id": user_id}, {"_id": 0}) or {}
    pattern = profile.get("your_pattern") or {}
    user_name = profile.get("name", "User")
    pattern_block = ""
    if pattern:
        # human-readable pairs
        pairs = ", ".join(f"{k}={v}" for k, v in pattern.items() if v not in (None, ""))
        pattern_block = f"\n\nThe user is named {user_name}. Their saved Your-Pattern: {pairs}. Stay consistent with this style; reference it when relevant."
    else:
        pattern_block = f"\n\nThe user is named {user_name}."
    system = base_system + pattern_block

    # ---- Conversation Memory Integration (Req 9.1, 9.2, 9.5, 9.7) ----
    try:
        from conversation_memory import get_full_context_for_chat

        memory_context = await get_full_context_for_chat(db, user_id, buddy)

        # If summary exists, include it in system prompt
        if memory_context.get("summary"):
            system += f"\n\n[Prior conversation summary: {memory_context['summary']}]"

        # If history exists, include last 5 messages as context
        if memory_context.get("history"):
            history_lines = []
            for msg in memory_context["history"]:
                role_label = "User" if msg["role"] == "user" else "You"
                history_lines.append(f"  {role_label}: {msg['content'][:300]}")
            system += (
                "\n\n[Recent conversation history (continue naturally from here):\n"
                + "\n".join(history_lines)
                + "\n]"
            )
    except Exception as e:
        logger.warning(f"Failed to load conversation memory for chat: {e}")
        # Graceful fallback: proceed without memory context (Req 9.6)

    # ---- "Remember when" topic search (Req 9.4) ----
    try:
        if _detect_memory_reference(req.message):
            memory_ref_context = await _search_conversation_history(db, user_id, buddy, req.message)
            if memory_ref_context:
                system += memory_ref_context
    except Exception as e:
        logger.warning(f"Failed topic search for memory reference: {e}")

    # Include cross-domain context for richer responses
    try:
        from context_engine import assemble_context, get_wellness_context_for_finance

        ctx = await assemble_context(db, user_id)
        raw = ctx.get("raw_data", {})

        # Build a brief context summary for all buddies
        context_parts = []
        if raw.get("mood"):
            context_parts.append(
                f"Mood: avg stress {raw['mood'].get('avg_stress', 50)}/100, "
                f"energy {raw['mood'].get('avg_energy', 50)}/100"
            )
        if raw.get("sleep"):
            context_parts.append(f"Sleep: avg {raw['sleep'].get('avg_hours', 7)}h/night")
        if raw.get("expenses"):
            context_parts.append(f"Spending: ₹{int(raw['expenses'].get('total_spent', 0))} this week")
        if raw.get("tasks"):
            context_parts.append(f"Tasks: {raw['tasks'].get('completion_rate', 0):.0f}% done")

        if context_parts:
            system += f"\n\n[User's 7-day context: {'; '.join(context_parts)}]"

        # Finance buddy: include wellness context when stress > 60 or sleep < 6.5h
        if buddy == "finance":
            wellness_ctx = await get_wellness_context_for_finance(db, user_id)
            if wellness_ctx:
                system += wellness_ctx

    except Exception as e:
        logger.warning(f"Failed to assemble context for chat: {e}")
        # Proceed without context - graceful degradation

    # store user message
    await db.chat_messages.insert_one(ChatMessage(user_id=user_id, buddy=buddy, role="user", content=req.message).model_dump())

    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id, system_message=system).with_model(provider, model)

    async def event_gen():
        full = ""
        try:
            async for ev in chat.stream_message(UserMessage(text=req.message)):
                if isinstance(ev, TextDelta):
                    full += ev.content
                    # SSE format: data: <text>\n\n   (escape newlines)
                    safe = ev.content.replace("\n", "\\n")
                    yield f"data: {safe}\n\n"
                elif isinstance(ev, StreamDone):
                    break
        except Exception as e:
            logger.error(f"chat error: {e}")
            yield f"data: [error] {str(e)}\n\n"
        # persist assistant message
        try:
            await db.chat_messages.insert_one(ChatMessage(user_id=user_id, buddy=buddy, role="assistant", content=full).model_dump())
        except Exception:
            pass
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api_router.get("/chat/{buddy}/history")
async def chat_history(buddy: str, limit: int = 50, user_id: str = Depends(get_current_user)):
    msgs = await db.chat_messages.find({"user_id": user_id, "buddy": buddy}, {"_id": 0}).sort("created_at", 1).to_list(limit)
    return msgs


@api_router.delete("/chat/{buddy}/history")
async def clear_chat(buddy: str, user_id: str = Depends(get_current_user)):
    await db.chat_messages.delete_many({"user_id": user_id, "buddy": buddy})
    return {"ok": True}


# ============ HEALTH ============
@api_router.get("/")
async def root():
    return {"app": "PocketBuddy", "status": "ok"}


# ============ AUTH ROUTER ============
from auth_router import auth_router, set_db as auth_set_db
auth_set_db(db)
app.include_router(auth_router)

# ============ GAMIFICATION ROUTER ============
from gamification_router import gamification_router
app.include_router(gamification_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
