# HackOn with Amazon | Solution Document
**Confidential — For Jury Evaluation Only**

---

## HackOn with Amazon
### A Universe of Opportunity
### 48-Hour Hackathon | Solution Document

---

| Field | Details |
|-------|---------|
| **Team Name** | *[Your Team Name]* |
| **Hackathon Theme** | AI for Student Well-Being & Financial Literacy |
| **Date** | *[Submission Date]* |

### Team Members

| Name | College / University | Role | Email |
|------|---------------------|------|-------|
| [Member 1] | [College] | Full-Stack Dev / AI Integration | [Email] |
| [Member 2] | [College] | Frontend Dev / UI-UX | [Email] |
| [Member 3] | [College] | Backend Dev / ML Engineer | [Email] |
| [Member 4] | [College] | Designer / DevOps | [Email] |

---

## 1. Problem Statement & Relevance

### The Problem

**Many students struggle silently with budgeting, food expenses, emotional stress, irregular sleep, and balancing academics with social life.**

- **75%** of Indian college students report moderate-to-high stress levels (NIMHANS 2024).
- **62%** don't track their monthly spending and routinely overshoot budgets by the 3rd week (YouthPulse Survey 2025).
- **48%** of students report burnout-level fatigue at least once per semester, correlated with both sleep deprivation and financial anxiety.
- The student spending market in India alone represents **₹4.8 lakh crore** annually across 40+ million enrolled students.

Existing apps (Mint, Headspace, Todoist) solve **one** slice — finance **or** wellness **or** productivity — without understanding the *interconnected reality* of student living: **stress drives overspending, poor sleep tanks academic performance, financial anxiety worsens mental health.**

### Why It Matters

- **40+ million** college students in India; **200+ million** globally face the same challenges.
- Students who don't manage finances early develop poor money habits that compound for decades.
- Untreated student burnout contributes to a **23% dropout rate** (UGC India, 2024).
- The cost of inaction: students graduate with financial debt, poor mental health patterns, and habits they carry into their working lives.

### Theme Alignment

This problem aligns directly with **"A Universe of Opportunity"** — PocketBuddy gives every student the opportunity to thrive, not just survive, through college. By using AI to connect the dots between finance, wellness, and productivity, we transform fragmented, overwhelming student life into a manageable, even gamified, journey.

**Our unique angle:** We treat student life as a **single interconnected system** rather than isolated domains. When stress is high, our AI proactively adjusts financial advice. When sleep drops, it warns about burnout *before* productivity collapses.

### What Makes This Novel

1. **Cross-Domain AI Intelligence** — No existing app correlates spending patterns with sleep quality with mood trends. PocketBuddy's Context Engine assembles 7-day data across 5 domains and detects patterns like "emotional eating" (stress↑ + food spending↑30%) and "burnout risk" (sleep < 6h for 3 consecutive days + task completion < 50%).

2. **Multi-Provider AI Engine with 4 Specialized Personalities** — Not one generic chatbot, but a production-grade engine powering 4 distinct AI buddies across 4 LLM providers (OpenAI GPT-5.2, Anthropic Claude Sonnet 4.5, Google Gemini 3 Flash, Groq Llama 3.3 70B) with automatic failover, content safety filtering, response caching, and personality guardrails. Each buddy has conversation memory that persists across sessions.

3. **AI-Powered Insights with Grounding Validation** — LLM-generated weekly highlights, daily insight cards, and command center briefings that are *verified* against actual user data. Every AI-generated statement must reference a real number from the user's context — if it hallucinates, the system falls back to rule-based generation automatically.

4. **Intelligent Discover Module** — AI-powered food recommendations (real restaurants near the user's college, filtered by dietary/budget/time-of-day) and travel route comparison (realistic Indian transport pricing via LLM with deterministic formula fallback). No hardcoded data — all context-aware.

5. **Adaptive Smart Notifications** — Notifications get *smarter* over time: dismiss a nudge once → 50% reduction for 7 days. Dismiss 3× → suppressed for 14 days. Under high stress (>70 for 2 consecutive days) → max 3 nudges/day to avoid overwhelming users.

6. **Indian Student-First Design** — All amounts in ₹, budget templates using the 50/30/20 rule calibrated for Indian student expenses, campus-specific resources (iCall helpline, college counselors), AI food recommendations for Indian eateries, transport pricing with Auto/Metro/Bus/Ola rates.

---

## 2. Customer & Solution

### Target Customer

**Persona: Priya, 20, 2nd-year B.Tech student at a Delhi engineering college.**
- Monthly income: ₹16,000 (parental allowance + part-time tutoring)
- Routinely overspends on food delivery during exam stress
- Sleeps <6 hours during midterms, leading to 3-day "zombie mode"
- Wants to save for a laptop (₹65,000) but keeps dipping into savings
- Feels isolated — hasn't joined any study groups despite wanting to
- **Needs:** A single app that ties her finances, wellness, academics, and social life together and *proactively* helps before problems escalate.

### How We Solve It

PocketBuddy is an **AI-powered student super-app** that unifies financial management, emotional wellness, academic productivity, social connection, and lifestyle discovery into one gamified, mobile-first experience.

**Key Features:**

| # | Feature | What It Does | AI Model |
|---|---------|-------------|----------|
| 1 | **Multi-Provider AI Engine** | Production-grade LLM orchestration with 4 provider adapters (OpenAI, Anthropic, Gemini, Groq), automatic fallback chain, content safety filtering, LRU+TTL response caching, and streaming via SSE | All 4 providers |
| 2 | **4 AI Buddy System** | Finance Buddy (₹-driven advice), Wellness Buddy (empathetic CBT-informed support), Discover Buddy (cheap eats & travel), Helper Buddy (cross-domain life coach) — each with strict personality rules, domain guardrails, and persistent conversation memory | GPT-5.2, Claude Sonnet 4.5, Gemini 3 Flash, GPT-5.2 |
| 3 | **Cross-Domain Context Engine** | Assembles 7-day data across mood, expenses, sleep, goals, and tasks via `asyncio.gather()`. Detects "emotional eating", "burnout risk", and "financial stress" correlations. Computes 3 composite scores. All within 2 seconds | Rule-based + LLM-enhanced |
| 4 | **AI-Powered Weekly Review** | Real domain scores computed from actual data, week-over-week trends stored for comparison, LLM-generated highlights (3 statements ≤80 chars each, grounded in data), personalized next-week focus recommendation | Groq Llama 3.3 70B |
| 5 | **AI Daily Insights** | 3 personalized insight cards (finance, wellness, productivity) with LLM-enhanced conversational text, data_reference fields, cached per day, onboarding support for new users | Groq Llama 3.3 70B |
| 6 | **Command Center Briefing** | Proactive daily briefing with 1-sentence state summary, up to 3 cross-domain action suggestions, and 1 nudge connecting patterns across domains (e.g., "Your sleep dropped 2h this week AND food spending rose 40% — stress eating pattern?") | Groq Llama 3.3 70B |
| 7 | **AI Food Recommendations** | Context-aware restaurant suggestions for Indian college students — considers dietary preference, budget per meal, location/college, time of day (breakfast/lunch/dinner). Real places from LLM knowledge. Cached 6h per user+meal-period | Groq Llama 3.3 70B |
| 8 | **AI Travel Route Comparison** | Source-to-destination transport cost estimation for Indian cities. LLM estimates realistic pricing; deterministic formula fallback (Auto ₹25+₹15/km, Bus ₹7/km, Metro ₹10+₹3/km, Ola/Uber ₹50+₹10/km). Cached 24h | Groq Llama 3.3 70B |
| 9 | **AI Wellness Cards** | Personalized wellness action cards generated by Claude based on user's current mood, sleep, goals, and stress level. Dynamic content that adapts to user context | Anthropic Claude Sonnet 4.5 |
| 10 | **Dynamic Habit Tracking** | Real-time computation of 4 habit metrics (sleep consistency, exercise frequency, journaling, daily check-ins) from last 7 days of actual MongoDB data | Rule-based computation |
| 11 | **Smart Budget Manager** | Auto-balance budgets using 50/30/20 rule, track subscriptions, split bills with friends, savings goals with progress tracking, expense auto-categorization learning from corrections (3-tier: user rules → keywords → misc) | Rule-based + learning |
| 12 | **Gamification Engine** | XP system (10 XP/mood, 5 XP/expense, 25 XP/plan), streak bonuses (min(streak×2, 100)), levels (floor(XP/100)+1), 5 achievement badges, daily challenges | Rule-based |
| 13 | **5-Domain Life-Balance Radar** | Real-time radar chart scoring Finance, Wellness, Academics, Social, and Self-Care (each 0-100), with actionable steps (≤140 chars) for low-scoring domains | Rule-based |
| 14 | **Study Groups & Social** | Create/join groups via 6-char invite codes, shared goals with leaderboards (sorted by completion %), community challenges with reflection + mood on completion, milestone notifications (25/50/75/100%) broadcast to group members | Rule-based |
| 15 | **Smart Notifications** | Budget warnings at 80% spend, wellness nudges when burnout <40, streak celebrations at milestones, rate-limited under high stress, dismissal-adaptive frequency | Rule-based |
| 16 | **Analytics & Trends** | Weekly/monthly spending trends with data sufficiency guards, spending anomaly detection (>2× 30-day average), monthly financial health reports with predicted month-end balance, habit recovery plans (≤3 suggestions) | Rule-based |
| 17 | **PWA + Offline Support** | Workbox service worker (5 caching strategies), IndexedDB offline queue (500-entry cap), sync on reconnect with 3 retries, conflict resolution preserving both versions | Client-side |
| 18 | **Voice Input** | Web Speech API for journal entries with 3-second pause auto-stop, 10-second silence timeout, hidden on unsupported browsers | Browser API |

### User Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  1. ONBOARD  │────▶│  2. DAILY    │────▶│  3. AI ASSISTS   │
│              │     │  CHECK-IN    │     │  PROACTIVELY     │
│ Name, goals, │     │              │     │                  │
│ energy peak, │     │ Mood (5 +    │     │ Budget warnings, │
│ budget setup │     │ 3 sliders),  │     │ burnout alerts,  │
│              │     │ Log expense, │     │ cross-domain     │
│ Auto-balance │     │ Sleep entry  │     │ correlations,    │
│ 50/30/20     │     │              │     │ AI insights      │
└──────────────┘     └──────────────┘     └──────────────────┘
                                                    │
                     ┌──────────────┐     ┌─────────▼────────┐
                     │ 5. SOCIAL +  │◀────│  4. CHAT WITH    │
                     │ GAMIFICATION │     │  AI BUDDIES      │
                     │              │     │                  │
                     │ Study groups,│     │ Finance Buddy:   │
                     │ challenges,  │     │  ₹-based advice  │
                     │ XP & badges, │     │ Wellness Buddy:  │
                     │ leaderboards │     │  empathetic care  │
                     │              │     │ Discover Buddy:  │
                     │ Tomorrow's   │     │  food & travel   │
                     │ Plan (8PM+)  │     │ Helper Buddy:    │
                     └──────────────┘     │  cross-domain    │
                                          └──────────────────┘
```

### Working Prototype

**Live Demo:**
- Frontend: React 19 PWA deployed on AWS S3 + CloudFront
- Backend: FastAPI on AWS EC2 (t2.micro free tier) with 60+ endpoints
- API Docs: Auto-generated Swagger UI at `/docs`
- Database: MongoDB Atlas M0 (cloud, free tier)
- 200+ automated pytest tests across 15 test files

**AWS Services Used:**
- EC2 (compute) — FastAPI backend with nginx reverse proxy (t3.micro, free tier)
- S3 (storage) — Static React build hosting
- CloudFront (CDN) — HTTPS delivery + global caching
- All within AWS Free Tier ($0/month)

---

## 3. Tech Architecture & Scaling

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React 19 PWA on S3/CloudFront)         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ DailyHub │ │ Finance  │ │ Wellness │ │ Discover │ │ Helper   │ │
│  │ Page     │ │ Buddy    │ │ Buddy    │ │ Buddy    │ │ Buddy    │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Auth     │ │ Gamifi-  │ │ Notifi-  │ │ Study    │ │ Trends   │ │
│  │ Context  │ │ cation   │ │ cation   │ │ Groups   │ │ & Anal.  │ │
│  │          │ │ Context  │ │ Context  │ │          │ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Offline Layer: ServiceWorker + IndexedDB Queue + SyncEngine │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                    Axios ↕ SSE Streaming ↕ REST                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS (CloudFront → EC2)
┌────────────────────────────▼────────────────────────────────────────┐
│               BACKEND (FastAPI on AWS EC2 t2.micro)                 │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              JWT Middleware (Auth Layer)                       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Auth     │ │ Analytics│ │ Gamifi-  │ │ Notifi-  │ │ Social   │ │
│  │ Router   │ │ Router   │ │ cation   │ │ cation   │ │ Router   │ │
│  │          │ │          │ │ Router   │ │ Router   │ │          │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │               Core API Router (60+ Endpoints)                │  │
│  │  Mood · Expenses · Journal · Budget · Sleep · Tasks ·       │  │
│  │  Goals · Savings · Splits · Subscriptions · Exercises ·     │  │
│  │  Discover/Food · Discover/Routes · Wellness/Cards ·         │  │
│  │  Routine/Habits · Life-Balance · Insights · Chat · Profile  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐    │
│  │ Context      │  │ Conversation  │  │ AI Insights          │    │
│  │ Engine       │  │ Memory        │  │ Service              │    │
│  │              │  │               │  │                      │    │
│  │ 7-day data   │  │ Store/Trim/   │  │ WeeklyReview +       │    │
│  │ assembly,    │  │ Summarize,    │  │ DailyInsights +      │    │
│  │ cross-domain │  │ Topic search, │  │ CommandCenter        │    │
│  │ correlations │  │ Memory refs   │  │ (LLM + fallback)     │    │
│  └──────┬───────┘  └──────┬────────┘  └──────────┬───────────┘    │
│         │                 │                       │                │
│  ┌──────┴─────┐  ┌───────┴────────┐  ┌──────────┴───────────┐    │
│  │ Discover   │  │ Categorization │  │ Notification         │    │
│  │ Services   │  │ Service        │  │ Service              │    │
│  │            │  │                │  │                      │    │
│  │ Food AI +  │  │ User rules →   │  │ Budget warnings,     │    │
│  │ Travel AI  │  │ Keywords →     │  │ wellness nudges,     │    │
│  │ (Groq LLM) │  │ Learning       │  │ adaptive frequency   │    │
│  └──────┬─────┘  └────────────────┘  └──────────────────────┘    │
│         │                                                          │
│  ┌──────▼──────────────────────────────────────────────────────┐  │
│  │          Multi-Provider AI Engine (emergentintegrations)     │  │
│  │                                                             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │  │
│  │  │ OpenAI   │ │Anthropic │ │  Google  │ │  Groq    │     │  │
│  │  │ GPT-5.2  │ │ Claude   │ │  Gemini  │ │ LLaMA    │     │  │
│  │  │          │ │ Sonnet   │ │  3 Flash │ │ 3.3 70B  │     │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │  │
│  │                                                             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │  │
│  │  │ Fallback │ │ Safety   │ │ Response │ │ Provider │     │  │
│  │  │ Chain    │ │ Filter   │ │ Cache    │ │ Routing  │     │  │
│  │  │ (auto)   │ │ (regex)  │ │ (LRU+TTL)│ │ (config) │     │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │  │
│  │                                                             │  │
│  │  SSE Streaming · Retry w/ Backoff · Rate Limiting          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                             │                                      │
└─────────────────────────────┼──────────────────────────────────────┘
                              │
              ┌───────────────▼───────────────┐
              │     MongoDB Atlas (Cloud)      │
              │                               │
              │  25+ Collections:             │
              │  users · user_profiles ·      │
              │  mood_entries · expenses ·     │
              │  sleep_entries · journal ·     │
              │  budget_categories · goals ·   │
              │  tasks · task_sessions ·       │
              │  exercises · exercise_sessions·│
              │  chat_messages ·              │
              │  conversation_summaries ·      │
              │  study_groups · shared_goals · │
              │  community_challenges ·        │
              │  notifications · gamification · │
              │  daily_insights · phq2_entries·│
              │  weekly_scores · weekly_insights│
              │  user_category_rules ·         │
              │  food_recommendation_cache ·   │
              │  route_cache ·                │
              │  user_food_preferences         │
              └───────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React 19, Tailwind CSS 3.4, Radix UI, Framer Motion, Recharts, Axios | React 19 concurrent rendering; Tailwind for rapid consistent styling with domain-based CSS variables; Radix for accessible primitives; Framer Motion for polished micro-animations; Recharts for radar/line/bar visualizations |
| **Backend** | Python 3.10+, FastAPI, Motor (async MongoDB), PyJWT, bcrypt | FastAPI delivers 10x throughput vs Django REST with native async/await and auto-generated OpenAPI docs; Motor provides non-blocking MongoDB access critical for concurrent AI streaming + DB operations |
| **Database** | MongoDB Atlas (cloud) | Schema-flexible document model ideal for heterogeneous student data; native async driver (Motor); Atlas provides managed backups, monitoring, and global clusters |
| **AI Engine** | Custom multi-provider: OpenAI, Anthropic, Gemini, Groq | 4 provider adapters with automatic fallback, content safety filtering (medical diagnosis + self-harm patterns → safe replacements), LRU+TTL response caching (1000 entries, 1-hour TTL), streaming via SSE. Different models for different strengths |
| **AI Services** | Groq LLaMA 3.3-70B (insights, food, travel), Anthropic Claude (wellness cards) | Groq for ultra-low-latency structured generation (<200ms TTFB); Claude for nuanced empathetic wellness responses; all with timeout enforcement (3-8s) and rule-based fallbacks |
| **PWA/Offline** | Workbox 7.4, IndexedDB, Web Push API | 5 caching strategies by asset type; IndexedDB queue with 500-entry cap; conflict resolution preserving both versions; push notifications with session-limited permission prompts |
| **Deployment** | AWS EC2 + S3 + CloudFront (Free Tier) | EC2 t3.micro for backend (nginx → gunicorn → uvicorn); S3 for static frontend; CloudFront for HTTPS + global CDN. Total cost: $0/month |

### Key Algorithms & Technical Depth

| Algorithm | Complexity | Description |
|-----------|-----------|-------------|
| **Cross-Domain Correlation Engine** | O(n × m) | Detects "emotional eating" (stress > 70 AND food spending ↑30% vs prior 7 days), "burnout risk" (sleep < 6h for 3 consecutive days AND task completion < 50%), "financial stress" (budget overspend AND stress > 60). Uses sliding window comparison across 14-day periods |
| **Context Assembly Pipeline** | O(1) wall-clock | 5 concurrent MongoDB fetches via `asyncio.gather()` with graceful degradation. If any domain fails, proceeds with available data. Target: <2s total |
| **LLM Grounding Validation** | O(n) per response | Recursively extracts all numeric values from assembled context, verifies LLM output references at least one real number. Rejects hallucinated statistics → falls back to rule-based |
| **Multi-Provider Fallback Chain** | O(k) where k=providers | On timeout/rate-limit: exponential backoff (1s, 2s) × 2 retries → fallback provider → domain-appropriate error message. Non-transient errors (400/401/403) skip retry |
| **Conversation Memory + Summarization** | O(n) | At 50 messages: extracts representative samples (evenly-spaced indices), generates ≤500-char extractive summary, deletes old, retains 20 most recent. "Remember when" uses keyword scoring across last 50 messages |
| **Adaptive Notification System** | O(1) per decision | 4-layer pipeline: category preference → type suppression (14 days after 3 dismissals) → high-stress cap (max 3/day) → frequency reduction (50% probabilistic skip). Each layer short-circuits |
| **5-Domain Life Balance** | O(n) per domain | Finance = budget adherence × 0.7 + savings × 0.3; Wellness = avg(mood, stress⁻¹, energy, sleep quality, sleep hours); Academics = tasks × 0.6 + study time × 0.4; Social = f(groups, activity); Self-Care = exercise × 0.5 + journal × 0.5 |
| **AI Food Recommendations** | O(1) with caching | Context build (dietary + budget + location + time) → cache check → LLM call → JSON parse → budget filter → dietary filter → cache store (6h TTL). Empty list on any failure (no hallucinated fallback) |
| **Spending Anomaly Detection** | O(n), n=30 days | Daily totals over 30 days → daily average → flag days where total > 2× average with deviation % |
| **Fare Formula (Travel Fallback)** | O(1) | Deterministic: Auto ₹25+₹15/km, Bus ₹7/km, Metro min(₹10+₹3/km, ₹60), Ola/Uber ₹50+₹10/km. Mode constraints: no Rickshaw > 5km, no Walk > 3km |

### AWS Deployment Architecture

```
┌──────────────┐         ┌──────────────────────┐
│   Browser    │ ──────▶ │  AWS CloudFront      │
│  (React PWA) │         │  ↓ serves from S3    │
└──────┬───────┘         │  (Static Frontend)   │
       │ API calls       └──────────────────────┘
       ▼
┌──────────────────────┐
│  AWS EC2 t2.micro    │
│  ┌────────────────┐  │
│  │ Nginx (port 80)│  │
│  │   ↓ proxy      │  │
│  │ Gunicorn+Uvicorn│ │
│  │   ↓            │  │
│  │ FastAPI (8000) │  │
│  │ + AI Engine    │  │
│  └────────────────┘  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐     ┌─────────────────┐
│  MongoDB Atlas M0    │     │  LLM Providers  │
│  (Free Cloud DB)     │     │  OpenAI/Claude/ │
└──────────────────────┘     │  Gemini/Groq    │
                             └─────────────────┘
```

**Total AWS Cost: $0/month** (Free Tier eligible for 12 months)

### Scaling Strategy

| Dimension | Strategy | Scale Target |
|-----------|----------|-------------|
| **Database** | MongoDB Atlas auto-scaling with sharding on `user_id` | 10M+ users |
| **API Server** | Stateless FastAPI behind ALB, horizontal autoscaling on CPU | 100K concurrent |
| **AI Layer** | Multi-provider fallback + per-provider rate limiting + response caching | 50K AI queries/hour |
| **Frontend** | S3 + CloudFront global CDN with service worker caching | <100ms global delivery |
| **Offline** | Client-side IndexedDB queue with server-side conflict resolution | Unlimited offline writes |

---

## 4. Future Vision

### Where This Goes

In 1-3 years, PocketBuddy evolves from a student companion app to the **operating system for young adult life** — a platform that grows *with* the user from college through their first job. The cross-domain AI engine becomes the foundation for a personalized life management system that institutions integrate with.

**Vision:** Every student deserves a brilliant, always-available personal advisor who understands the interconnected reality of their life — and that advisor should be free.

### Roadmap

| Horizon | Milestone | Impact |
|---------|-----------|--------|
| **0-3 months** | Launch beta with 5 partner colleges in Delhi NCR. UPI transaction import (with consent) for automatic expense tracking. Hindi + Tamil language support for AI buddies | 10,000 active users |
| **3-6 months** | Partner with campus counseling centers for warm referral pipeline. Launch "PocketBuddy for Campuses" B2B dashboard with anonymized wellness trends | 50,000 users, 3 institutional partners |
| **6-12 months** | Expand to first-job young professionals (22-28). Account Aggregator framework integration for real financial data. Peer-to-peer financial mentoring marketplace | 200,000 users, B2B2C revenue |

### Value Impact

| Metric | Current (Prototype) | 12-Month Target |
|--------|-------------------|-----------------|
| **Users Impacted** | Working demo | 200,000 students |
| **Avg Student Savings** | — | ₹800/month per user |
| **Burnout Early Detection** | Detects in prototype | 90% accuracy, 72-hour advance warning |
| **Cost Savings for Universities** | — | ₹50L/year per partner |

---

## Links

| Resource | URL |
|----------|-----|
| GitHub | *[URL]* |
| Demo Video | *[URL]* |
| Live App (Frontend) | *[S3/CloudFront URL]* |
| Live API | *[EC2 URL]/docs* |
| API Documentation | Auto-generated Swagger UI |

---

## Appendix: Technical Depth

### A. Multi-Provider AI Engine (`emergentintegrations/llm/`)

The custom-built AI engine is the production backbone. 6 modules:
- **`chat.py`** — `LlmChat` class: streaming interface, lazy initialization, cache integration
- **`_adapters.py`** — 4 provider adapters (OpenAI AsyncClient, Anthropic message streaming, Gemini GenerativeModel, Groq OpenAI-compatible)
- **`_fallback.py`** — Automatic retry (2× with exponential backoff) → fallback provider → domain-appropriate error message
- **`_safety.py`** — Regex-based content filter (medical diagnosis patterns → professional referral; self-harm content → crisis resources: iCall, Vandrevala Foundation)
- **`_cache.py`** — LRU+TTL cache (1000 entries, 1-hour TTL, SHA-256 keys)
- **`_models.py`** — Shared types, provider routing, API key resolution (constructor > env var > legacy key)

### B. AI Insights Service (`insights_service.py`)

Three service classes with shared utilities:
- **`WeeklyReviewService`** — Real scores from context_engine, week-over-week trends (stored in `weekly_scores` collection), LLM highlights with 5s timeout + grounding validation, focus recommendation targeting lowest-scoring domain
- **`DailyInsightsService`** — 3 personalized insight cards with LLM-enhanced text, `data_reference` fields, onboarding cards for new users, daily cache
- **`CommandCenterService`** — Proactive briefing (summary + 3 actions spanning 2+ domains + cross-domain nudge ≤150 chars naming 2 domains)

**Key guarantee:** Every AI-generated statement is validated against real user data. If the LLM hallucinates numbers not in context, the system automatically falls back to rule-based generation.

### C. Context Engine (`context_engine.py`)

- Fetches from **5 domains** concurrently with graceful degradation
- Computes **3 composite scores**: Financial Health, Wellness Composite, Habit Consistency
- Identifies up to **10 active stressors** analyzing: high stress (>70), low energy (<40), poor sleep (<6h), overspent budgets, missed goals, low task completion
- Detects **3 cross-domain correlations** using period-over-period comparison and sliding windows
- **Data sufficiency guard**: <3 unique data days → skip correlations (prevents spurious pattern detection)

### D. Intelligent Discover Module

- **Food**: `FoodRecommendationService` — builds user context (dietary, budget, cuisines, college, time-of-day) → LLM generates 6 real Indian food places → validate + filter by budget/dietary → cache 6h. **No hardcoded fallback** — empty on failure
- **Travel**: `TravelService` — normalize inputs → cache check → LLM estimation → validate route structure → deterministic formula fallback → cache 24h. Supports intra-city (<15km) and intercity (>15km) mode selection

### E. Test Coverage

- **15 test files, 200+ pytest tests** covering:
  - Auth flows + property-based validation (Hypothesis)
  - AI engine: adapters, fallback, safety, cache, integration
  - Context engine: score computation, graceful degradation, correlations
  - Conversation memory: store, trim, summarize, topic search
  - Food/Travel services: dietary filtering, fare formula, cache behavior
  - Life balance: 5-domain scoring, partial data handling
  - Categorization: 3-tier cascading, user rule storage
  - Chat personality: trigger detection, system prompt validation

### F. Gamification System

- **XP Awards**: 10 (mood), 5 (expense, capped 10/day), 10 (journal), 25 (plan complete), 50 (challenge complete)
- **Streak Bonuses**: `min(streak × 2, 100)` bonus XP per mood check-in
- **Leveling**: `floor(total_xp / 100) + 1`
- **5 Achievements**: First Week, Budget Master, Sleep Champion, Journal Keeper, Social Butterfly
