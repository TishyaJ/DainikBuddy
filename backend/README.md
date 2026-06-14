# PocketBuddy Backend

FastAPI + Motor (async MongoDB) backend powering the PocketBuddy AI wellness, finance, and productivity platform.

---

## Architecture Overview

```
server.py                       ← Main FastAPI app, core CRUD endpoints, AI chat streaming (~1200 lines)
├── auth_router.py              ← Authentication endpoints (/api/auth/*)
├── analytics_router.py         ← Trend & anomaly detection (/api/analytics/*)
├── notification_router.py      ← Smart notifications & nudges (/api/notifications/*)
├── social_router.py            ← Study groups & challenges (/api/social/*)
├── gamification_router.py      ← XP, levels, achievements (/api/gamification/*)
│
├── auth_service.py             ← Password hashing, JWT creation/verification, validation
├── analytics_service.py        ← Trend computation, anomaly detection, recovery plans
├── notification_service.py     ← Nudge generation, rate limiting, dismissal adaptation
├── social_service.py           ← Group CRUD, invite codes, shared goals, challenges
├── gamification_service.py     ← XP awards, level calculation, streak tracking, achievements
├── categorization_service.py   ← Expense auto-categorization (user rules → keywords → misc)
├── context_engine.py           ← Cross-domain AI context assembly (7-day data fusion)
├── conversation_memory.py      ← Chat message persistence, summarization, topic search
├── insights_service.py         ← AI-powered weekly review, daily insights, command center
├── discover_food_service.py    ← AI food recommendations (Groq LLM + user context)
├── discover_travel_service.py  ← AI route comparison (LLM + deterministic fallback)
│
├── jwt_middleware.py           ← FastAPI Depends() for JWT token verification
├── emergentintegrations/       ← Multi-provider LLM engine
│   └── llm/
│       ├── chat.py             ← LlmChat class (main streaming interface)
│       ├── _adapters.py        ← Provider adapters (OpenAI, Anthropic, Gemini, Groq)
│       ├── _fallback.py        ← Automatic provider fallback chain
│       ├── _safety.py          ← Content safety filtering
│       ├── _cache.py           ← Response caching layer
│       └── _models.py          ← Shared types, config, routing
│
└── tests/                      ← pytest test suite (15 files, 200+ tests)
    ├── test_auth.py
    ├── test_auth_properties.py
    ├── test_ai_adapters.py
    ├── test_ai_cache.py
    ├── test_ai_engine_properties.py
    ├── test_ai_fallback.py
    ├── test_ai_integration.py
    ├── test_ai_safety.py
    ├── test_categorization_service.py
    ├── test_chat_personality.py
    ├── test_context_engine.py
    ├── test_conversation_memory.py
    ├── test_food_service.py
    ├── test_life_balance.py
    └── test_travel_service.py
```

---

## API Endpoint Catalog

### Authentication (`auth_router.py` → `/api/auth/*`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account (email + password). Returns access + refresh tokens |
| POST | `/api/auth/login` | Login with email + password. Returns access + refresh tokens |
| POST | `/api/auth/refresh` | Exchange refresh token for new access token |
| POST | `/api/auth/forgot-password` | Request password reset (always returns success — anti-enumeration) |
| POST | `/api/auth/reset-password` | Reset password using token from email link |
| DELETE | `/api/auth/delete-account` | Permanently delete user account and all data |
| GET | `/api/auth/export-data` | GDPR data export — returns all user data as JSON |

### Core CRUD (`server.py` → `/api/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/moods` | List mood entries (last 30) |
| POST | `/api/moods` | Log a mood entry (awards XP) |
| GET | `/api/expenses` | List expenses (last 50) |
| POST | `/api/expenses` | Log expense (auto-categorizes if category="auto") |
| POST | `/api/expenses/{id}/recategorize` | Change expense category + store user rule |
| GET | `/api/journal` | List journal entries (last 30) |
| POST | `/api/journal` | Create journal entry (awards XP) |
| GET | `/api/tasks` | List active tasks (excludes archived) |
| POST | `/api/tasks` | Create a task |
| PATCH | `/api/tasks/{id}` | Update task progress/status |
| GET | `/api/goals` | List active goals (excludes done) |
| POST | `/api/goals` | Create a goal |
| PATCH | `/api/goals/{id}` | Update goal progress |
| DELETE | `/api/goals/{id}` | Delete a goal |
| GET | `/api/sleep` | List sleep entries (last 30) |
| POST | `/api/sleep` | Log sleep data |
| GET | `/api/history` | Archived tasks + completed goals (supports `?range=7d|30d|90d|all`) |

### AI Chat (`server.py` → `/api/chat/*`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat/{buddy}` | Stream AI response. Buddies: `finance`, `wellness`, `discover`, `helper` |
| GET | `/api/chat/{buddy}/history` | Get chat history for a buddy |
| DELETE | `/api/chat/{buddy}/history` | Clear chat history for a buddy |

Each buddy has distinct personality rules, loads conversation history (last 5 messages + summary), injects cross-domain context, and supports "remember when" topic search.

### Insights & Life Balance (`server.py` → `/api/insights/*`, `/api/life-balance`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/life-balance` | 5-domain radar scores (finance, wellness, academics, social, self-care) |
| GET | `/api/insights/daily` | 3 AI-powered insight cards (cached per day, LLM-generated with fallback) |
| GET | `/api/insights/tomorrow-plan` | 3 actionable steps (available after 8 PM) |
| POST | `/api/insights/complete-actions` | Mark plan complete (awards 25 XP) |
| GET | `/api/insights/weekly` | AI-powered weekly review (scorecard, highlights, focus) |
| GET | `/api/insights/briefing` | Command center daily briefing (summary, actions, cross-domain nudge) |

### Analytics (`analytics_router.py` → `/api/analytics/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analytics/trends?period=weekly|monthly` | Spending/mood/sleep/habit trends with % change |
| GET | `/api/analytics/anomalies` | Spending anomalies (daily spend > 2× 30-day avg) |
| GET | `/api/analytics/monthly-report` | Income vs spending, budget adherence, prediction |
| GET | `/api/analytics/recovery-plan` | Habit recovery suggestions (≤3 schedule adjustments) |

### Notifications (`notification_router.py` → `/api/notifications/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/notifications` | List recent notifications (limit 20) |
| POST | `/api/notifications/{id}/dismiss` | Dismiss notification (triggers frequency adaptation) |
| GET | `/api/notifications/preferences` | Get notification category preferences |
| PATCH | `/api/notifications/preferences` | Toggle notification categories on/off |
| POST | `/api/notifications/subscribe` | Store push notification subscription |
| POST | `/api/notifications/evaluate` | Trigger nudge evaluation (budget/wellness/checkin/streak) |

### Social (`social_router.py` → `/api/social/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/social/groups` | List user's study groups |
| POST | `/api/social/groups` | Create a study group (generates 6-char invite code) |
| GET | `/api/social/groups/{id}` | Group detail (members, goals, activity feed) |
| POST | `/api/social/groups/{id}/join` | Join group by ID |
| POST | `/api/social/groups/join` | Join group by invite code |
| POST | `/api/social/groups/{id}/leave` | Leave group |
| GET | `/api/social/groups/{id}/goals` | List shared goals with leaderboard |
| POST | `/api/social/groups/{id}/goals` | Create shared goal |
| PATCH | `/api/social/goals/{id}/progress` | Update goal progress (triggers milestones) |
| GET | `/api/social/challenges` | List active weekly challenges |
| POST | `/api/social/challenges` | Create a community challenge |
| POST | `/api/social/challenges/{id}/join` | Join a challenge |
| PATCH | `/api/social/challenges/{id}/progress` | Update challenge progress |
| POST | `/api/social/challenges/{id}/complete` | Complete challenge (with mood + reflection) |
| POST | `/api/social/challenges/{id}/close` | Close challenge (creator only) |

### Gamification (`gamification_router.py` → `/api/gamification/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/gamification/status` | User's XP, level, streak, daily progress |
| GET | `/api/gamification/achievements` | All earned achievement badges |

### Finance (`server.py` → `/api/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/budget` | Budget categories with allocated/spent amounts |
| POST | `/api/budget` | Set/update budget category |
| GET | `/api/subscriptions` | List tracked subscriptions |
| POST | `/api/subscriptions` | Add subscription |
| GET | `/api/savings` | List savings goals |
| POST | `/api/savings` | Create savings goal |
| GET | `/api/splits` | List bill splits |
| POST | `/api/splits` | Create bill split |

### Wellness (`server.py` → `/api/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/wellness/phq2` | PHQ-2 mental health screening |
| POST | `/api/wellness/phq2` | Submit PHQ-2 responses |
| GET | `/api/wellness/cards` | AI-generated wellness action cards (Anthropic Claude) |
| GET | `/api/wellness/bedtime-goal` | Bedtime goal status |
| POST | `/api/wellness/bedtime-goal` | Set bedtime goal |
| GET | `/api/routine/habits` | Dynamic habit tracking (sleep, exercise, journal, check-in) |

### Discover (`server.py` → `/api/discover/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/discover/food` | AI-powered food recommendations (context-aware, cached 6h) |
| POST | `/api/discover/routes` | AI-powered travel route comparison (cached 24h) |
| GET | `/api/discover/travel` | Legacy travel data (static fallback) |
| GET | `/api/discover/snacks` | Brain food suggestions |
| GET | `/api/discover/activities` | Stress-break activities |
| GET | `/api/discover/campus` | Campus resources |

### Profile & Exercises (`server.py` → `/api/*`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/profile` | User profile (auto-creates on first access) |
| PATCH | `/api/profile` | Update profile fields |
| POST | `/api/profile/onboard` | Onboarding data (name, goals, pattern) |
| GET | `/api/exercises` | List exercises |
| POST | `/api/exercises` | Create exercise entry |
| PATCH | `/api/exercises/{id}` | Update exercise |

---

## File Descriptions

### Core Server
| File | Purpose |
|------|---------|
| `server.py` | FastAPI app initialization, CORS config, MongoDB connection, all core CRUD endpoints, AI chat streaming, life-balance computation, daily insights, onboarding, discover endpoints, wellness AI cards, routine habits. Main entry point (~1200 lines). |
| `jwt_middleware.py` | `get_current_user` FastAPI dependency — extracts `user_id` from Bearer JWT, returns 401 for invalid/expired tokens. Applied to ALL endpoints via `Depends(get_current_user)`. |

### Service Modules (business logic, no HTTP concerns)
| File | Purpose |
|------|---------|
| `auth_service.py` | Password hashing (bcrypt, cost 12), JWT access/refresh token creation, email validation, password strength validation, rate limiting helpers, reset token generation |
| `gamification_service.py` | XP award logic (per action, with daily caps), level computation (100×level XP per level), streak tracking (consecutive days with activity), achievement unlocks |
| `categorization_service.py` | Three-tier expense categorization: user rules → keyword matching → default "misc". Stores user corrections for learning. 500-rule cap per user. |
| `context_engine.py` | Assembles 7-day cross-domain user data into unified context. Computes financial_health_score, wellness_composite_score, habit_consistency. Detects correlations (emotional eating, burnout risk, financial stress). |
| `conversation_memory.py` | Stores/retrieves chat messages per buddy. Last 5 messages for session context. Auto-summarizes older messages (>50) into ≤500 char summaries. Topic keyword search for "remember when" queries. |
| `notification_service.py` | Generates proactive nudges (budget 80% warning, wellness, check-in reminders, streak celebrations). Rate limiting under high stress (max 3/day). Dismissal adaptation (50% reduction → full suppression). |
| `social_service.py` | Study group lifecycle (create, join by 6-char code, leave). Shared goals with leaderboard (sorted by completion %). Milestone notifications (25/50/75/100%). Community challenges with XP rewards. |
| `analytics_service.py` | Trend computation (weekly/monthly). Spending anomaly detection (2× threshold). Monthly financial report with prediction. Habit recovery plans (≤3 suggestions). |
| `insights_service.py` | **NEW** — AI-powered insights engine with three service classes: `WeeklyReviewService` (scorecard + trends + LLM highlights + focus), `DailyInsightsService` (3 personalized insight cards), `CommandCenterService` (daily briefing + cross-domain nudge). Shared utilities: `_call_llm_with_timeout`, `_validate_grounding`, `_get_iso_week`. |
| `discover_food_service.py` | **NEW** — AI food recommendations via Groq LLM. Considers dietary preferences, budget per meal, location/college, time of day. Cached per user+meal-time with 6h TTL. No hardcoded fallback — empty list on failure. |
| `discover_travel_service.py` | **NEW** — AI route comparison for Indian locations. LLM estimates transport costs (Auto, Metro, Bus, Ola/Uber, Rickshaw, Walk). Deterministic fare formula fallback. Cached 24h in MongoDB. |

### AI Engine (`emergentintegrations/llm/`)
| File | Purpose |
|------|---------|
| `chat.py` | `LlmChat` class — main interface for AI streaming. `.with_model(provider, model)` configures the adapter. Supports system messages, conversation history, temperature/max_tokens control. |
| `_adapters.py` | Provider-specific adapters implementing the `ProviderAdapter` protocol. Each handles message formatting and async streaming for their SDK: OpenAI (AsyncOpenAI), Anthropic (AsyncAnthropic), Gemini (GenerativeModel), Groq (AsyncGroq). |
| `_fallback.py` | Automatic fallback chain — if primary provider fails (timeout, rate limit, API error), tries next provider in chain. Domain-appropriate fallback messages when all providers fail. |
| `_safety.py` | Content safety filtering applied before sending prompts to LLM. Prevents injection and ensures safe outputs. |
| `_cache.py` | Response caching layer to reduce API costs for repeated/similar queries. |
| `_models.py` | Shared data models (`AdapterConfig`, `UsageInfo`, `StreamEvent`), provider routing (`PROVIDER_ENV_KEYS`, `SUPPORTED_PROVIDERS`), API key resolution (`_resolve_api_key`), custom exceptions. |

### Routers (HTTP layer, thin wrappers around services)
| File | Purpose |
|------|---------|
| `auth_router.py` | Routes for `/api/auth/*`. Handles request parsing, calls auth_service, returns responses. |
| `analytics_router.py` | Routes for `/api/analytics/*`. JWT-protected. |
| `notification_router.py` | Routes for `/api/notifications/*`. JWT-protected. |
| `social_router.py` | Routes for `/api/social/*`. JWT-protected. Challenge completion with reflection + close. |
| `gamification_router.py` | Routes for `/api/gamification/*`. JWT-protected. |

### Other
| File | Purpose |
|------|---------|
| `fix_auth.py` | Diagnostic script for auth issues — list/delete/reset users in MongoDB. Run with `python fix_auth.py --list`. |
| `pytest.ini` | Pytest configuration (paths, markers, warnings). |

---

## Setup Instructions

### Prerequisites
- Python 3.10+ (3.11 or 3.12 recommended)
- pip (comes with Python)
- MongoDB Atlas account OR local MongoDB instance
- At least ONE LLM API key (OpenAI, Anthropic, Gemini, or Groq)

### Step-by-Step

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows (CMD):
venv\Scripts\activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file (copy from .env.example, fill in values)
copy .env.example .env

# 6. Start the server
uvicorn server:app --reload --port 8000
```

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# === REQUIRED ===
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?appName=pocketbuddy&tls=true&tlsAllowInvalidCertificates=true
DB_NAME=pocketbuddy
JWT_SECRET=any-random-string-at-least-32-chars-long
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# === AI KEYS (at least one required for chat to work) ===
EMERGENT_LLM_KEY=your-openai-key-here
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
GROQ_API_KEY=gsk_...
```

#### ⚠️ CRITICAL: MongoDB URL Encoding

If your MongoDB password contains special characters (`@`, `#`, `%`, `/`, `:`), you MUST URL-encode them:

| Character | Encoded |
|-----------|---------|
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |
| `/` | `%2F` |
| `:` | `%3A` |

Example: Password `MyP@ss#1` becomes `MyP%40ss%231` in the connection string.

**DO NOT** wrap the password in `<>` angle brackets. MongoDB Atlas UI sometimes shows `<password>` as a placeholder — replace the ENTIRE `<password>` including the brackets.

---

## Running Tests

```bash
# Activate venv first!
venv\Scripts\activate

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=term-missing

# Run only AI engine tests
python -m pytest tests/test_ai_*.py -v
```

**Important:** Tests must be run from within the activated virtual environment. Running `pytest` directly without venv activation will fail with `ModuleNotFoundError`.

Current test suite: **15 test files, 200+ tests**.

---

## Development Guidelines

### Adding a New Endpoint

1. If it's a simple CRUD endpoint → add it to `server.py` directly
2. If it's a feature domain with multiple endpoints → create a new router file:
   ```python
   # my_router.py
   from fastapi import APIRouter, Depends
   from jwt_middleware import get_current_user
   
   my_router = APIRouter(prefix="/api/myfeature", tags=["MyFeature"])
   
   @my_router.get("/items")
   async def get_items(user_id: str = Depends(get_current_user)):
       # ... your logic
       return {"items": []}
   ```
3. Register the router in `server.py`:
   ```python
   from my_router import my_router
   app.include_router(my_router)  # BEFORE app.include_router(api_router)
   ```

### Adding a New Service

- Accept `db` as a parameter (not as a module-level import from server.py)
- This enables unit testing with mocked Motor instances
- Wrap DB calls in try/except for graceful degradation
- Follow the pattern in `context_engine.py` or `insights_service.py`

### Using the AI Engine

```python
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

llm = LlmChat(
    api_key=os.getenv("GROQ_API_KEY"),
    session_id="my-feature",
    system_message="You are a helpful assistant.",
    temperature=0.7,
    max_tokens=512,
    cache_enabled=True,
).with_model("groq", "llama-3.3-70b-versatile")

full_text = ""
async for event in llm.stream_message(UserMessage(text="Hello")):
    if isinstance(event, TextDelta):
        full_text += event.content
    elif isinstance(event, StreamDone):
        break
```

Supported providers: `openai`, `anthropic`, `gemini`, `groq`

### Common Pitfalls

1. **Motor version**: Must be compatible with your pymongo version. If you see `_QUERY_OPTIONS` errors, upgrade motor to 3.7.1+.
2. **Index conflicts**: Don't call `create_index()` with different options on the same field from multiple places. All indexes are managed in `server.py`'s `on_startup`.
3. **Circular imports**: Service modules should NEVER import from `server.py`. Pass `db` as a function parameter instead.
4. **Streaming responses**: The chat endpoint returns `StreamingResponse` (not JSON). Don't try to parse it as JSON in tests.
5. **UTC timestamps**: Always use `datetime.now(timezone.utc)` — never naive datetimes.
6. **load_dotenv placement**: Must be at the very top of `server.py` before any imports that read env vars. A misplaced `load_dotenv` caused a zombie server bug (see diary.md).
7. **.env BOM**: If `python-dotenv` can't read the first variable, check for UTF-8 BOM in the `.env` file. Recreate without BOM.
8. **LLM timeout**: Always wrap LLM calls in `asyncio.wait_for()` with a reasonable timeout (3-8s). LLMs can hang indefinitely.

---

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These are auto-generated from the FastAPI route definitions and Pydantic models.
