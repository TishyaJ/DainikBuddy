# PocketBuddy — Product Requirements Doc (PRD)

## Original Problem Statement
Build PocketBuddy, a Zepto-style super-app for students with 5 AI-powered domains:
1. Daily Check-In Hub (Mood, Expense, Journal, Goal Review, AI Summary)
2. Finance Buddy (Dashboard, Budget, Expenses, Cash Flow, Alerts, Subscriptions, Food/Travel, Emergency Fund, Savings, Split Bills + Chatbot)
3. Wellness Buddy (Dashboard, Sleep, Burnout, Stress, Routine, Check-Ins, Focus, Social, Support + Chatbot)
4. Discover Buddy (Dashboard, Food, Travel, Safe Night, Snacks, Activities, Campus, Goals, Fitness + Chatbot)
5. Helper Buddy (Command Center, Daily Insights, Weekly Review, Analytics, Life Balance + Orchestrator Chatbot)

## Architecture
- **Frontend**: React 19 + Tailwind + shadcn/ui + Recharts, mobile-styled phone-frame on desktop
- **Backend**: FastAPI + MongoDB (motor)
- **AI**: Multi-model via Emergent Universal LLM key (emergentintegrations):
  - Finance Buddy → OpenAI `gpt-5.2`
  - Wellness Buddy → Anthropic `claude-sonnet-4-5-20250929`
  - Discover Buddy → Google `gemini-3-flash-preview`
  - Helper Buddy → OpenAI `gpt-5.2` (orchestrator)
- **Auth**: None — single demo user `alex`
- **Voice & Receipt OCR**: UI MOCKED only (no real Whisper/Vision wired up yet)

## User Personas
- **Alex** — Indian college student tracking ₹ budget, wellness, daily habits, looking for cheap food/travel and cross-domain AI advice.

## What's Implemented (2026-02)
### Backend (`/api`)
- `/mood` POST/GET, `/mood/weekly`
- `/expenses` POST/GET, `/expenses/categorize`
- `/journal` POST/GET, `/journal/weekly` (with simple sentiment)
- `/goals` GET/POST/PATCH
- `/budget` GET/PATCH (envelope categories)
- `/subscriptions` GET
- `/savings` GET
- `/splits` GET
- `/sleep` POST, `/sleep/weekly`, `/wellness/scores`
- `/discover/food`, `/discover/travel`, `/discover/snacks`, `/discover/activities`, `/discover/campus`
- `/life-balance`, `/insights/daily`, `/insights/weekly`
- `/chat/{buddy}` SSE streaming POST (finance/wellness/discover/helper)
- `/chat/{buddy}/history` GET/DELETE
- Seed data on startup (budget, subs, savings, splits, goals, sleep, moods, expenses)

### Frontend
- Phone-frame wrapper (mobile-styled responsive)
- 5-tab bottom nav with active-domain theming via CSS vars
- Daily Hub (5 sub-tabs: Mood emoji picker + sliders, Expense form + scan, Journal + voice + weekly chart, Goals with progress bars, AI Summary cross-domain)
- Finance Buddy (9 sub-tabs: Dashboard ring, Expenses feed, Cash Flow line, Alerts, Subs, Food/Travel, Emergency radial, Savings goals, Splits)
- Wellness Buddy (9 sub-tabs: Dashboard score rings, Sleep bar chart, Burnout meter, Stress mood timeline, Routine habits, PHQ-2 check-ins, Pomodoro timer, Social, Support + crisis card)
- Discover Buddy (9 sub-tabs: Dashboard food grid + deals, Food, Travel modes, Safe Night SOS, Snacks, Activities, Campus resources, Goals, Fitness)
- Chat Center: 4 buddy cards + Helper Buddy Command Center (life-balance radar + insights + weekly review)
- BuddyChat: SSE streaming, suggested prompts, history, clear

## Prioritized Backlog
### P0 (Done)
- ✅ All 5 domains with key features
- ✅ All 4 buddy chatbots with streaming
- ✅ Mobile phone-frame layout
- ✅ Seed demo data

### P1
- [ ] Receipt OCR (real OpenAI Vision)
- [ ] Voice journal (Whisper)
- [ ] Editable budget allocations from UI
- [ ] Push notifications / scheduled alerts
- [ ] Real auth (Emergent Google) — currently demo user

### P2
- [ ] Dark mode
- [ ] PWA install banner
- [ ] Shared expense splitwise import
- [ ] Real campus/map integration

## Next Action Items
- Hook up receipt scanner to GPT-4o vision
- Hook up voice journaling to Whisper
- Add notifications/reminders engine
- Allow editing budget allocations + custom categories
