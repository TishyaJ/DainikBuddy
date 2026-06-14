# PocketBuddy Frontend

React 19 + Tailwind CSS + Radix UI progressive web app. Mobile-first design rendered inside a phone-frame container.

---

## Architecture Overview

```
src/
├── App.js                 ← Root component: providers, routing, PhoneFrame shell
├── index.js               ← Entry point, service worker registration
├── index.css              ← Tailwind directives, CSS variables, domain themes
├── App.css                ← Additional global styles
│
├── pages/                 ← Full-screen page components (routed)
│   ├── DailyHub.jsx       ← Home page: mood/expense/journal/goals/tasks tabs
│   ├── FinanceBuddy.jsx   ← Finance management: budget, transactions, splits, savings
│   ├── WellnessBuddy.jsx  ← Wellness: PHQ-2, sleep, exercises, bedtime goals
│   ├── DiscoverBuddy.jsx  ← Discovery: goals, recommendations, exercises
│   ├── ChatCenter.jsx     ← AI chat: 4 buddies (finance/wellness/discover/helper)
│   ├── BuddyChat.jsx      ← Individual chat conversation view
│   ├── Profile.jsx        ← User profile: gamification, history, patterns
│   ├── StudyGroups.jsx    ← Social: my groups + community challenges tabs
│   ├── TrendsView.jsx     ← Analytics: charts, anomalies, monthly report
│   ├── NotificationCenter.jsx    ← Notification list with dismiss
│   ├── NotificationPreferences.jsx ← Toggle notification categories
│   ├── Onboarding.jsx     ← First-time user setup flow
│   ├── LoginPage.jsx      ← Email/password login
│   ├── RegisterPage.jsx   ← Registration with password requirements
│   └── ForgotPasswordPage.jsx ← Password reset request
│
├── components/            ← Reusable UI components
│   ├── PhoneFrame.jsx     ← 430px max-width mobile frame container
│   ├── Header.jsx         ← Top bar: greeting, XP badge, notification bell
│   ├── BottomNav.jsx      ← 5-tab navigation (Home/Finance/Social/Discover/Chat)
│   ├── SubTabs.jsx        ← In-page tab switcher (role=tablist, accessible)
│   │
│   ├── AchievementBadge.jsx     ← Animated badge with spring slide-in
│   ├── StreakCounter.jsx        ← Streak display with milestone bounce
│   ├── XPProgressBar.jsx       ← Level progress bar
│   ├── LevelUpOverlay.jsx      ← Full-screen level-up celebration (particles)
│   │
│   ├── NotificationBell.jsx    ← Bell icon with unread badge count
│   ├── AnomalyFlag.jsx         ← Spending anomaly alert banner
│   ├── MonthlyReport.jsx       ← Financial health report card
│   │
│   ├── StudyGroupCard.jsx      ← Group card with member avatars
│   ├── GroupDetail.jsx         ← Full group view (members, goals, activity)
│   ├── InviteCodeInput.jsx     ← 6-char code input with auto-focus
│   ├── SharedGoalLeaderboard.jsx ← Sorted goal progress with trophy
│   ├── CommunityChallenges.jsx  ← Challenge list/create/join/complete
│   │
│   ├── VoiceInputButton.jsx    ← Mic button with pulsing animation
│   ├── OfflineIndicator.jsx    ← "You're offline" amber banner
│   ├── SyncStatus.jsx          ← Floating sync progress pill
│   ├── ConflictResolution.jsx  ← Conflict resolution modal (local vs server)
│   │
│   ├── Tasks.jsx               ← Task list + detail with archive
│   ├── Exercise.jsx            ← Exercise tracking components
│   │
│   ├── Skeleton.jsx            ← Loading skeleton components
│   ├── ErrorCard.jsx           ← Error display with retry button
│   ├── EmptyState.jsx          ← Empty state with icon + CTA
│   ├── PageTransition.jsx      ← Framer-motion page fade/slide wrapper
│   │
│   └── ui/                     ← shadcn/ui base components (Button, Card, Input, etc.)
│
├── context/               ← React context providers
│   ├── AuthContext.jsx    ← JWT auth state, login/register/logout/refresh functions
│   ├── DomainContext.jsx  ← Current domain (finance/wellness/social/etc), theme switching
│   ├── GamificationContext.jsx ← XP, level, streak, achievements polling
│   ├── NotificationContext.jsx ← Notifications list, 60s polling, push subscription
│   └── OfflineContext.jsx     ← Online/offline state, sync triggers, conflict tracking
│
├── lib/                   ← Utility modules
│   ├── api.js             ← Axios instance with auth interceptors (auto-refresh on 401)
│   ├── offlineSync.js     ← IndexedDB offline queue (500-entry cap, sync, conflicts)
│   ├── voiceInput.js      ← Web Speech API wrapper (3s pause, 10s silence timeout)
│   └── utils.js           ← cn() class merger utility
│
├── hooks/                 ← Custom React hooks
│   └── use-toast.js       ← Toast notification hook
│
└── constants/             ← Shared constants
    └── testIds/           ← data-testid constants for testing
```

---

## Routing

All routes are rendered inside `PhoneFrame` (mobile container) with `Header` + `BottomNav`:

| Path | Page | Domain Theme |
|------|------|--------------|
| `/` | DailyHub | hub |
| `/finance` | FinanceBuddy | finance |
| `/wellness` | WellnessBuddy | wellness |
| `/social` | StudyGroups | social |
| `/social/group/:groupId` | GroupDetail | social |
| `/discover` | DiscoverBuddy | discover |
| `/chat` | ChatCenter | chat |
| `/chat/:buddy` | BuddyChat | chat |
| `/profile` | Profile | hub |
| `/trends` | TrendsView | finance |
| `/notifications` | NotificationCenter | hub |
| `/notifications/preferences` | NotificationPreferences | hub |
| `/onboarding` | Onboarding | hub |

Guest routes (no auth required): `/login`, `/register`, `/forgot-password`

---

## Context Provider Stack

The app wraps in this order (outermost → innermost):

```jsx
<AuthProvider>           // JWT tokens, user state
  <GamificationProvider> // XP, level, streak
    <NotificationProvider> // Notifications, polling
      <OfflineProvider>    // Online state, sync
        <DomainProvider>   // Current theme domain
          <App />
        </DomainProvider>
      </OfflineProvider>
    </NotificationProvider>
  </GamificationProvider>
</AuthProvider>
```

---

## Styling System

### Tailwind CSS + CSS Variables

The project uses Tailwind CSS with custom CSS variables for domain-based theming:

```css
/* Each domain has its own color set */
[data-domain="finance"] {
  --bdy: #10b981;      /* emerald */
  --bdy-soft: #d1fae5;
  --bdy-2: #059669;
}
[data-domain="wellness"] {
  --bdy: #8b5cf6;      /* violet */
  --bdy-soft: #ede9fe;
  --bdy-2: #7c3aed;
}
/* ... etc for hub, social, discover, chat */
```

### Utility Classes
- `bdy-bg` → `background-color: var(--bdy)`
- `bdy-text` → `color: var(--bdy)`
- `bdy-soft` → `background-color: var(--bdy-soft)`

### Rules
- **NEVER** use hardcoded Tailwind colors like `bg-purple-500` for interactive/themed elements
- Always use `bdy-*` utilities so colors respond to domain changes
- Static/neutral elements (borders, backgrounds) can use Tailwind gray scale

---

## Setup Instructions

### Prerequisites
- Node.js 18+ (20 LTS recommended)
- npm 9+ (comes with Node.js)

### Step-by-Step

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install --legacy-peer-deps

# 3. Create .env (if not present)
echo REACT_APP_BACKEND_URL=http://localhost:8000 > .env

# 4. Start development server
npm start
```

The app will open at http://localhost:3000.

### ⚠️ CRITICAL: --legacy-peer-deps

You MUST use `--legacy-peer-deps` when installing. The project uses React 19 which has peer dependency conflicts with some packages (react-day-picker, some Radix UI packages). Without this flag, npm will refuse to install.

```bash
# ✅ Correct
npm install --legacy-peer-deps

# ❌ Will fail
npm install
```

### Build for Production

```bash
npm run build
# or equivalently:
npx craco build
```

Output goes to `frontend/build/`. This is a static bundle that can be served by any web server.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REACT_APP_BACKEND_URL` | Yes | — | Backend API URL (e.g., `http://localhost:8000`) |
| `ENABLE_HEALTH_CHECK` | No | `false` | Enable webpack health check plugin (dev only) |

---

## Development Guidelines

### Adding a New Page

1. Create `src/pages/MyPage.jsx`
2. Add route in `App.js` inside the Shell component:
   ```jsx
   <Route path="/mypage" element={<MyPage />} />
   ```
3. Add domain mapping in `ROUTE_DOMAIN` object in App.js:
   ```js
   '/mypage': 'hub', // or 'finance', 'wellness', etc.
   ```
4. Wrap content in `<PageTransition>` for consistent animations

### Adding a New Component

1. Create in `src/components/MyComponent.jsx`
2. Use `bdy-*` classes for themed elements
3. Add `aria-label` to all interactive elements
4. Use `EmptyState` for zero-item views
5. Use `Skeleton*` components for loading states
6. Use `ErrorCard` for error states with retry

### API Calls

All API calls go through the axios instance in `src/lib/api.js`:

```jsx
import api from '../lib/api';

// GET
const { data } = await api.get('/moods');

// POST
const { data } = await api.post('/moods', { mood: 'great', energy: 80 });

// The interceptor automatically:
// - Attaches JWT from localStorage
// - Refreshes token on 401
// - Retries the failed request
```

### Offline-Aware Components

For components that should work offline:

```jsx
import { useOffline } from '../context/OfflineContext';

function MyComponent() {
  const { isOnline, savePending } = useOffline();
  
  if (!isOnline) {
    return <EmptyState title="Requires Internet" />;
  }
  // ... normal render
}
```

---

## PWA Features

- **Service Worker**: Caches app shell, CSS/JS, images, fonts for offline access
- **Manifest**: Installable as standalone app on mobile/desktop
- **Offline Sync**: Data entered offline queues in IndexedDB, syncs when back online
- **Push Notifications**: Browser push notifications for nudges (permission requested once per session)

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `npm install` fails | React 19 peer deps | Use `npm install --legacy-peer-deps` |
| Blank page on load | Backend not running | Start backend first (`uvicorn server:app --reload`) |
| 401 errors everywhere | Token expired or backend restarted | Log out and back in |
| Styles not updating | Tailwind not rebuilding | Restart `npm start` |
| `craco build` warnings | Unused imports | Safe to ignore; fix with ESLint |
| Port 3000 already in use | Another process | Kill it or use `PORT=3001 npm start` |
