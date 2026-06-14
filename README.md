# PocketBuddy

AI-powered wellness, finance, and productivity companion for students. Track moods, manage expenses, set goals, chat with AI buddies, join study groups, and build healthy habits — all in one gamified mobile-first app.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Tailwind CSS, Radix UI, Framer Motion, Recharts, Axios |
| **Backend** | Python 3.10+, FastAPI, Motor (async MongoDB), PyJWT, bcrypt |
| **Database** | MongoDB Atlas (cloud) or local MongoDB |
| **AI** | OpenAI / Anthropic / Gemini / Groq (multi-provider) |
| **PWA** | Workbox service worker, IndexedDB offline sync, Web Push |

---

## Project Structure

```
PocketBuddy/
├── backend/               ← FastAPI server (Python)
│   ├── server.py          ← Main app + core endpoints
│   ├── *_router.py        ← Feature routers (auth, social, analytics, etc.)
│   ├── *_service.py       ← Business logic modules
│   ├── tests/             ← 185+ pytest tests
│   └── README.md          ← Detailed backend documentation
│
├── frontend/              ← React app
│   ├── src/pages/         ← Page components
│   ├── src/components/    ← Reusable UI components
│   ├── src/context/       ← React context providers (auth, gamification, etc.)
│   ├── src/lib/           ← Utilities (API client, offline sync, voice input)
│   └── README.md          ← Detailed frontend documentation
│
├── REPRODUCIBILITY.md     ← ⭐ Complete setup guide for new team members
├── change_log.md          ← Session-by-session development log
├── diary.md               ← Implementation decisions and architecture reasoning
└── design_guidelines.json ← UI/UX design system reference
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

- **4 AI Buddies** — Finance, Wellness, Discover, Helper (each with distinct personality + conversation memory)
- **Cross-Domain Intelligence** — AI detects correlations between spending, sleep, stress, and habits
- **Gamification** — XP, levels, streaks, achievements, daily challenges
- **Study Groups** — Invite codes, shared goals with leaderboards, community challenges
- **Smart Notifications** — Budget warnings, wellness nudges, streak celebrations (rate-limited)
- **Analytics** — Trend charts, spending anomalies, monthly reports, recovery plans
- **Life-Balance Radar** — 5-domain scoring (finance, wellness, academics, social, self-care)
- **Voice Input** — Web Speech API for journal entries (3s pause auto-stop)
- **Offline Support** — PWA with IndexedDB queue, sync on reconnect, conflict resolution
- **Auto-Categorization** — Learns from user corrections to categorize future expenses

---

## Documentation

| Document | Purpose |
|----------|---------|
| [REPRODUCIBILITY.md](./REPRODUCIBILITY.md) | **Start here** — Full setup guide for new team members |
| [backend/README.md](./backend/README.md) | Backend architecture, all 55+ endpoints, service descriptions |
| [frontend/README.md](./frontend/README.md) | Frontend architecture, components, styling system |
| [change_log.md](./change_log.md) | What changed in each development session |
| [diary.md](./diary.md) | Why decisions were made (architecture reasoning) |

---

## Collaboration

### Branching
- `main` — Production-ready, always stable
- `feature/<name>` — New features (e.g., `feature/voice-input`)
- `bugfix/<name>` — Bug fixes

### Before Pushing
1. Backend: `python -m pytest tests/ -v` (all 185+ tests must pass)
2. Frontend: `npm run build` (must compile without errors)
3. Write descriptive commit messages (e.g., `feat: add challenge completion with reflection`)

### Code Style
- **Backend**: Black + isort formatting, type hints where practical
- **Frontend**: ESLint (via craco), Tailwind class ordering, `bdy-*` for themed colors

---

## License

Private project — PocketBuddy team only.
