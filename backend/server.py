from fastapi import FastAPI, APIRouter, HTTPException, Query
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

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


# ============ SEED ============
async def seed_demo_data():
    """Seed demo data once for user 'alex'."""
    if await db.budget_categories.count_documents({"user_id": DEMO_USER}) > 0:
        return
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


@app.on_event("startup")
async def on_startup():
    await seed_demo_data()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# ============ HELPERS ============
async def list_docs(coll, user_id=DEMO_USER, limit=200, sort_field=None):
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
async def create_mood(entry: MoodEntry):
    entry.user_id = DEMO_USER
    await db.mood_entries.insert_one(entry.model_dump())
    return entry


@api_router.get("/mood")
async def get_moods(limit: int = 30):
    return await list_docs("mood_entries", limit=limit, sort_field="created_at")


# ============ EXPENSES ============
@api_router.post("/expenses")
async def create_expense(e: Expense):
    e.user_id = DEMO_USER
    if not e.category or e.category == "auto":
        e.category = detect_category(f"{e.merchant} {e.note}")
    await db.expenses.insert_one(e.model_dump())
    # update budget spent
    await db.budget_categories.update_one(
        {"user_id": DEMO_USER, "name": {"$regex": f"^{e.category}$", "$options": "i"}},
        {"$inc": {"spent": e.amount}},
    )
    return e


@api_router.get("/expenses")
async def get_expenses(limit: int = 50):
    return await list_docs("expenses", limit=limit, sort_field="created_at")


@api_router.post("/expenses/categorize")
async def categorize(payload: Dict[str, str]):
    text = payload.get("text", "")
    return {"category": detect_category(text)}


# ============ JOURNAL ============
@api_router.post("/journal")
async def create_journal(j: JournalEntry):
    j.user_id = DEMO_USER
    sent, score = simple_sentiment(j.text)
    j.sentiment = sent
    j.sentiment_score = score
    await db.journal_entries.insert_one(j.model_dump())
    return j


@api_router.get("/journal")
async def get_journals(limit: int = 30):
    return await list_docs("journal_entries", limit=limit, sort_field="created_at")


@api_router.get("/journal/weekly")
async def journal_weekly():
    entries = await db.journal_entries.find({"user_id": DEMO_USER}, {"_id": 0}).sort("created_at", -1).to_list(50)
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
async def get_goals():
    return await list_docs("goals")


@api_router.post("/goals")
async def create_goal(g: Goal):
    g.user_id = DEMO_USER
    await db.goals.insert_one(g.model_dump())
    return g


@api_router.patch("/goals/{goal_id}")
async def update_goal(goal_id: str, payload: Dict[str, Any]):
    await db.goals.update_one({"id": goal_id, "user_id": DEMO_USER}, {"$set": payload})
    doc = await db.goals.find_one({"id": goal_id}, {"_id": 0})
    return doc


# ============ BUDGET ============
@api_router.get("/budget")
async def get_budget():
    cats = await list_docs("budget_categories")
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
async def update_budget(cat_id: str, payload: Dict[str, Any]):
    await db.budget_categories.update_one({"id": cat_id, "user_id": DEMO_USER}, {"$set": payload})
    return await db.budget_categories.find_one({"id": cat_id}, {"_id": 0})


# ============ SUBSCRIPTIONS / SAVINGS / SPLITS ============
@api_router.get("/subscriptions")
async def get_subs():
    subs = await list_docs("subscriptions")
    total = sum(s["amount"] for s in subs)
    return {"items": subs, "monthly_total": total}


@api_router.get("/savings")
async def get_savings():
    return await list_docs("savings_goals")


@api_router.get("/splits")
async def get_splits():
    items = await list_docs("split_bills")
    net = sum(s["owes_you"] for s in items)
    return {"items": items, "net_balance": net}


# ============ WELLNESS ============
@api_router.get("/wellness/scores")
async def wellness_scores():
    moods = await db.mood_entries.find({"user_id": DEMO_USER}, {"_id": 0}).sort("created_at", -1).to_list(7)
    sleeps = await db.sleep_entries.find({"user_id": DEMO_USER}, {"_id": 0}).sort("date", -1).to_list(7)
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
        "streak_days": 5,
    }


@api_router.get("/sleep/weekly")
async def sleep_weekly():
    sleeps = await db.sleep_entries.find({"user_id": DEMO_USER}, {"_id": 0}).sort("date", 1).to_list(7)
    out = []
    for s in sleeps:
        d = datetime.fromisoformat(s["date"]).strftime("%a")
        out.append({"day": d, "hours": s["hours"], "quality": s["quality"]})
    return out


@api_router.post("/sleep")
async def add_sleep(s: SleepEntry):
    s.user_id = DEMO_USER
    await db.sleep_entries.insert_one(s.model_dump())
    return s


@api_router.get("/mood/weekly")
async def mood_weekly():
    moods = await db.mood_entries.find({"user_id": DEMO_USER}, {"_id": 0}).sort("created_at", 1).to_list(7)
    return [{"day": datetime.fromisoformat(m["created_at"]).strftime("%a"), "mood": m["mood"],
             "stress": m.get("stress", 50)} for m in moods]


# ============ DISCOVER (static seed) ============
@api_router.get("/discover/food")
async def discover_food():
    return [
        {"name": "Mess Express", "price": 50, "rating": 4.3, "distance": "0.2 km", "tag": "Full meal", "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400"},
        {"name": "Roll Zone", "price": 40, "rating": 4.5, "distance": "0.4 km", "tag": "Rolls", "image": "https://images.unsplash.com/photo-1565299507177-b0ac66763828?w=400"},
        {"name": "Student Thali", "price": 60, "rating": 4.2, "distance": "0.6 km", "tag": "Thali", "image": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400"},
        {"name": "Coffee Cart", "price": 25, "rating": 4.1, "distance": "0.1 km", "tag": "Drinks", "image": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400"},
    ]


@api_router.get("/discover/travel")
async def discover_travel():
    return [
        {"mode": "Metro", "cost": 30, "time": "25 min", "icon": "train", "safe": True},
        {"mode": "Cycle", "cost": 0, "time": "40 min", "icon": "bike", "safe": True},
        {"mode": "Rideshare", "cost": 120, "time": "18 min", "icon": "car", "safe": True},
        {"mode": "Walk", "cost": 0, "time": "55 min", "icon": "footprints", "safe": False},
    ]


@api_router.get("/discover/snacks")
async def discover_snacks():
    return [
        {"name": "Almonds + Banana", "nutrition": 9, "budget": 8, "tag": "Brain food"},
        {"name": "Roasted Chana", "nutrition": 8, "budget": 10, "tag": "Protein"},
        {"name": "Dark Chocolate", "nutrition": 7, "budget": 6, "tag": "Focus"},
        {"name": "Greek Yogurt", "nutrition": 9, "budget": 5, "tag": "Calm"},
    ]


@api_router.get("/discover/activities")
async def discover_activities():
    return [
        {"name": "5-min stretch", "duration": "5 min", "type": "movement"},
        {"name": "Box breathing", "duration": "3 min", "type": "calm"},
        {"name": "Quick sketch", "duration": "10 min", "type": "creative"},
        {"name": "Walk outdoors", "duration": "15 min", "type": "movement"},
    ]


@api_router.get("/discover/campus")
async def discover_campus():
    return [
        {"name": "Counseling Center", "type": "wellness", "available": True},
        {"name": "Peer Tutoring", "type": "study", "available": True},
        {"name": "Food Pantry", "type": "aid", "available": True},
        {"name": "Financial Aid Office", "type": "aid", "available": False},
    ]


# ============ HELPER (life balance + insights) ============
@api_router.get("/life-balance")
async def life_balance():
    cats = await list_docs("budget_categories")
    spent_pct = sum(c["spent"] for c in cats) / max(sum(c["allocated"] for c in cats), 1) * 100
    finance = max(0, 100 - (spent_pct - 70))  # less spend = better
    finance = round(min(100, max(0, finance)))
    w = await wellness_scores()
    wellness = w["burnout_score"]
    goals = await list_docs("goals")
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
async def daily_insights():
    return [
        {"domain": "finance", "title": "Snacks spending up 22%", "detail": "Try hostel mess twice this week to save ~₹250.", "icon": "trending-up"},
        {"domain": "wellness", "title": "Sleep dropped 45 min", "detail": "Aim for a 11:30pm bedtime tonight.", "icon": "moon"},
        {"domain": "productivity", "title": "Goals 71% on track", "detail": "Sleep goal needs attention this week.", "icon": "target"},
        {"domain": "discover", "title": "New deal nearby", "detail": "Flat 20% off at Mess Express today only.", "icon": "compass"},
    ]


@api_router.get("/insights/weekly")
async def weekly_insights():
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
BUDDY_MODELS = {
    "finance": ("openai", "gpt-5.2", "You are Finance Buddy, a wise owl 🦉 helping a student named Alex manage money in Indian rupees (₹). Be concise, friendly, use bullet points, give concrete numbers. Topics: budgeting, expenses, savings goals, splitting bills, subscriptions, cash flow. End with one actionable tip."),
    "wellness": ("anthropic", "claude-sonnet-4-5-20250929", "You are Wellness Buddy, a calm and empathetic cloud ☁️ supporting student Alex's mental wellbeing. Validate feelings first, then offer a small, doable step. Topics: stress, sleep, burnout, focus, mood, breathing. If crisis is detected, gently suggest reaching out to campus counseling. Keep replies warm and under 120 words."),
    "discover": ("gemini", "gemini-3-flash-preview", "You are Discover Buddy, an upbeat compass 🧭 helping student Alex find cheap food, safe transport, student deals, and campus resources in India. Be punchy, list 2-3 concrete options with prices in ₹ when possible. End with a question to keep the convo going."),
    "helper": ("openai", "gpt-5.4", "You are Helper Buddy, the orchestrator of Alex's super-app PocketBuddy. You synthesize insights across Finance, Wellness, Discover and Productivity. Always reason briefly across domains (e.g., 'finance + sleep + goals') and end with a single 'Tomorrow do this:' line."),
}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@api_router.post("/chat/{buddy}")
async def chat_stream(buddy: str, req: ChatRequest):
    if buddy not in BUDDY_MODELS:
        raise HTTPException(404, "Unknown buddy")
    provider, model, system = BUDDY_MODELS[buddy]
    session_id = req.session_id or f"{DEMO_USER}-{buddy}"

    # store user message
    await db.chat_messages.insert_one(ChatMessage(buddy=buddy, role="user", content=req.message).model_dump())

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
            await db.chat_messages.insert_one(ChatMessage(buddy=buddy, role="assistant", content=full).model_dump())
        except Exception:
            pass
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api_router.get("/chat/{buddy}/history")
async def chat_history(buddy: str, limit: int = 50):
    msgs = await db.chat_messages.find({"user_id": DEMO_USER, "buddy": buddy}, {"_id": 0}).sort("created_at", 1).to_list(limit)
    return msgs


@api_router.delete("/chat/{buddy}/history")
async def clear_chat(buddy: str):
    await db.chat_messages.delete_many({"user_id": DEMO_USER, "buddy": buddy})
    return {"ok": True}


# ============ HEALTH ============
@api_router.get("/")
async def root():
    return {"app": "PocketBuddy", "status": "ok", "user": DEMO_USER}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
