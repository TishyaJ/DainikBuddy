# PocketBuddy

AI-powered wellness, finance, and productivity companion for students. Track moods, manage expenses, set goals, chat with AI buddies, join study groups, and build healthy habits — all in one gamified mobile-first app.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Tailwind CSS, Radix UI, Framer Motion, Recharts, Axios |
| **Backend** | Python 3.10+, FastAPI, Motor (async MongoDB), PyJWT, bcrypt |
| **Database** | MongoDB Atlas (cloud) or local MongoDB |
| **AI Engine** | Multi-provider LLM (OpenAI GPT-5.2, Anthropic Claude Sonnet 4.5, Google Gemini 3 Flash, Groq Llama 3.3 70B) with automatic fallback, safety filtering, and response caching |
| **PWA** | Workbox service worker, IndexedDB offline sync, Web Push |

---

## Project Structure

```
PocketBuddy/
├── backend/                    ← FastAPI server (Python)
│   ├── server.py               ← Main app + core endpoints (~1200 lines)
│   ├── *_router.py             ← Feature routers (auth, social, analytics, gamification, notification)
│   ├── *_service.py            ← Business logic modules
│   ├── insights_service.py     ← AI-powered weekly/daily insights generation
│   ├── discover_food_service.py   ← AI food recommendations for students
│   ├── discover_travel_service.py ← AI-powered route comparison
│   ├── emergentintegrations/   ← Multi-provider LLM engine (adapters, fallback, safety, cache)
│   ├── tests/                  ← pytest test suite (15 test files, 200+ tests)
│   └── README.md               ← Detailed backend documentation
│
├── frontend/                   ← React app (PWA)
│   ├── src/pages/              ← 15 page components
│   ├── src/components/         ← 26 reusable UI components + ui/ base layer
│   ├── src/context/            ← 5 React context providers
│   ├── src/lib/                ← Utilities (API client, offline sync, voice input)
│   └── README.md               ← Detailed frontend documentation
│
├── Guides/                     ← Research & planning documents
│   ├── deep-research-report.md ← Student behavior research & evidence-based features
│   ├── discover-domain-tasks.md← Discover module improvement plan
│   └── *.pdf / *.html          ← UI mockups & feature PDFs
│
├── memory/                     ← Project memory & PRD
│   └── PRD.md                  ← Original product requirements doc
│
├── test_reports/               ← Integration test results (JSON iterations)
│
├── .kiro/specs/                ← Feature specifications (requirements → design → tasks)
│   ├── pocketbuddy-ai-enhancement/   ← Core feature spec (completed)
│   ├── ai-engine-enhancement/        ← Multi-provider LLM engine (completed)
│   ├── ai-insights-enhancement/      ← AI-powered insights upgrade (in progress)
│   └── intelligent-discover-module/   ← Smart discover features (in progress)
│
├── REPRODUCIBILITY.md          ← ⭐ Complete setup guide for new team members
├── change_log.md               ← Session-by-session development log
├── diary.md                    ← Implementation decisions and architecture reasoning
└── design_guidelines.json      ← UI/UX design system reference
```

---

## Quick Start

> **New to the project?** Read [REPRODUCIBILITY.md](./REPRODUCIBILITY.md) for the full step-by-step guide with troubleshooting.

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
# Create .env with your MongoDB URL + API keys (see backend/.env.example)
uvicorn server:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install --legacy-peer-deps
# Create .env with: REACT_APP_BACKEND_URL=http://localhost:8000
npm start
```

App opens at http://localhost:3000. Backend API docs at http://localhost:8000/docs.

---

## Key Features

### AI Intelligence Layer
- **4 AI Buddies** — Finance (GPT-5.2), Wellness (Claude Sonnet 4.5), Discover (Gemini 3 Flash), Helper (GPT-5.2 orchestrator) — each with distinct personality + conversation memory
- **Cross-Domain Intelligence** — AI detects correlations between spending, sleep, stress, and habits
- **AI-Powered Insights** — LLM-generated weekly highlights, daily insights, and proactive briefings grounded in real user data
- **Smart Food Recommendations** — AI-powered restaurant suggestions based on dietary preferences, budget, location, and time of day
- **Intelligent Route Comparison** — AI-powered travel cost estimation with Indian transport pricing (Auto, Metro, Bus, Ola/Uber)

### Core Features
- **Gamification** — XP, levels, streaks, achievements, daily challenges
- **Study Groups** — Invite codes, shared goals with leaderboards, community challenges
- **Smart Notifications** — Budget warnings, wellness nudges, streak celebrations (rate-limited with dismissal adaptation)
- **Analytics** — Trend charts, spending anomalies, monthly reports, recovery plans
- **Life-Balance Radar** — 5-domain scoring (finance, wellness, academics, social, self-care)
- **Voice Input** — Web Speech API for journal entries (3s pause auto-stop)
- **Offline Support** — PWA with IndexedDB queue (500-entry cap), sync on reconnect, conflict resolution
- **Auto-Categorization** — Learns from user corrections to categorize future expenses (3-tier cascading)

---

## AI Engine Architecture

PocketBuddy uses a custom multi-provider LLM engine (`emergentintegrations/llm/`):

| Component | Purpose |
|-----------|---------|
| `chat.py` | Main `LlmChat` class — streaming interface with `.with_model(provider, model)` |
| `_adapters.py` | Provider adapters: OpenAI, Anthropic, Gemini, Groq (all async streaming) |
| `_fallback.py` | Automatic fallback chain when primary provider fails |
| `_safety.py` | Content safety filtering before sending to LLM |
| `_cache.py` | Response caching to reduce API costs |
| `_models.py` | Shared types, config, and provider routing |

**Model assignments:**
- Finance Buddy → OpenAI `gpt-5.2`
- Wellness Buddy → Anthropic `claude-sonnet-4-5-20250929`
- Discover Buddy → Google `gemini-3-flash-preview`
- Helper Buddy → OpenAI `gpt-5.2` (orchestrator)
- Insights/Food/Travel → Groq `llama-3.3-70b-versatile` (fast + cheap)

---

## Documentation

| Document | Purpose |
|----------|---------|
| [REPRODUCIBILITY.md](./REPRODUCIBILITY.md) | **Start here** — Full setup guide for new team members |
| [backend/README.md](./backend/README.md) | Backend architecture, all 60+ endpoints, service descriptions |
| [frontend/README.md](./frontend/README.md) | Frontend architecture, components, styling system |
| [Guides/deep-research-report.md](./Guides/deep-research-report.md) | Student behavior research & evidence-based feature design |
| [memory/PRD.md](./memory/PRD.md) | Original product requirements document |
| [change_log.md](./change_log.md) | What changed in each development session |
| [diary.md](./diary.md) | Why decisions were made (architecture reasoning) |

---

## Feature Specs (`.kiro/specs/`)

| Spec | Status | Description |
|------|--------|-------------|
| `pocketbuddy-ai-enhancement` | ✅ Complete | Core feature implementation (auth, gamification, context engine, notifications, social, analytics, PWA) |
| `ai-engine-enhancement` | ✅ Complete | Multi-provider LLM engine with fallback, safety, caching |
| `ai-insights-enhancement` | 🔄 In Progress | AI-powered weekly review, daily insights, command center briefings |
| `intelligent-discover-module` | 🔄 In Progress | Smart food recommendations, travel route comparison, ObjectId fix |

---

## Collaboration

### Branching
- `main` — Production-ready, always stable
- `feature/<name>` — New features (e.g., `feature/voice-input`)
- `bugfix/<name>` — Bug fixes

### Before Pushing
1. Backend: `python -m pytest tests/ -v` (all tests must pass)
2. Frontend: `npm run build` (must compile without errors)
3. Write descriptive commit messages (e.g., `feat: add challenge completion with reflection`)

### Code Style
- **Backend**: Black + isort formatting, type hints where practical
- **Frontend**: ESLint (via craco), Tailwind class ordering, `bdy-*` for themed colors

---

## License

Private project — PocketBuddy team only.
