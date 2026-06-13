# Implementation Plan: PocketBuddy AI Enhancement

## Overview

This plan implements the PocketBuddy AI enhancement in incremental waves: starting with authentication and core backend services, then building out AI context, gamification, notifications, social, analytics, and offline/PWA capabilities, followed by frontend integration and UI coherence. Each task builds on prior steps, ensuring no orphaned code.

## Tasks

- [-] 1. Authentication and Security Foundation
  - [x] 1.1 Create backend auth module with registration, login, JWT, and refresh token endpoints
    - Create `backend/auth_service.py` with bcrypt password hashing (cost 12), JWT creation (24h expiry), refresh token (30d expiry)
    - Create `backend/auth_router.py` with `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`, `/api/auth/forgot-password`, `/api/auth/reset-password`, `/api/auth/delete-account`, `/api/auth/export-data` endpoints
    - Implement email validation (max 254 chars, standard format) and password validation (8–128 chars, 1 uppercase, 1 number)
    - Implement rate limiting: 5 failed attempts per email within 15 min locks login for 15 min
    - Return generic error messages for failed login (no field hints)
    - Reject duplicate email registration with appropriate message
    - _Requirements: 8.1, 8.2, 8.3, 8.5, 8.7, 8.9, 8.10_

  - [x] 1.2 Create JWT middleware to protect all API endpoints
    - Create `backend/jwt_middleware.py` that extracts user_id from JWT on every request
    - Return 401 for missing/invalid/expired tokens on authenticated endpoints
    - Replace `DEMO_USER` pattern with JWT-derived user_id across all existing routers
    - Implement axios interceptor on frontend to attach JWT and handle 401 → refresh flow
    - _Requirements: 8.4, 8.5, 8.6_

  - [x] 1.3 Create frontend auth pages (Login, Register, ForgotPassword)
    - Create `frontend/src/pages/LoginPage.jsx` with email/password form, validation display, error handling
    - Create `frontend/src/pages/RegisterPage.jsx` with password requirements display
    - Create `frontend/src/pages/ForgotPasswordPage.jsx` with email input
    - Create `frontend/src/context/AuthContext.jsx` for JWT storage, refresh logic, auth state management
    - Update `App.js` to add auth routes and protect authenticated routes
    - _Requirements: 8.1, 8.2, 8.3, 8.7_

  - [x] 1.4 Write property tests for authentication validation
    - **Property 23: Registration Validation** — Generate random emails/passwords, verify validation rules and bcrypt output
    - **Property 24: Authentication Enforcement** — Generate requests without valid JWT, verify 401 responses
    - **Property 25: Login Rate Limiting** — Generate failed login sequences, verify lockout after 5 attempts
    - **Validates: Requirements 8.1, 8.2, 8.4, 8.9**

- [-] 2. Gamification Engine
  - [-] 2.1 Create backend gamification service and router
    - Create `backend/gamification_service.py` with XP award logic, streak computation, level calculation, achievement tracking
    - Create `backend/gamification_router.py` with `/api/gamification/status`, `/api/gamification/achievements` endpoints
    - Implement daily caps: mood check-in 10 XP (first only), expense 5 XP (max 10/day), journal 10 XP (first only)
    - Implement streak bonus: min(streak_days × 2, 100) XP per day; reset streak if no mood check-in by 11:59 PM
    - Implement level formula: floor(total_xp / 100) + 1
    - Track achievements: "First Week", "Budget Master", "Sleep Champion", "Journal Keeper", "Social Butterfly"
    - Hook into existing mood, expense, and journal POST endpoints to trigger XP awards
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [ ]* 2.2 Write property tests for XP computation
    - **Property 10: XP Award Rules with Daily Caps** — Generate action sequences, verify daily cap enforcement
    - **Property 11: Streak Bonus Formula** — Generate streak day counts, verify bonus = min(N×2, 100)
    - **Property 12: Level Computation** — Generate XP totals, verify level = floor(XP/100) + 1
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

  - [~] 2.3 Create frontend gamification components
    - Create `frontend/src/components/XPProgressBar.jsx` with animated progress to next level
    - Create `frontend/src/components/StreakCounter.jsx` with flame animation
    - Create `frontend/src/components/AchievementBadge.jsx` for badge display
    - Create `frontend/src/components/LevelUpOverlay.jsx` with full-screen celebration (3s minimum)
    - Create `frontend/src/context/GamificationContext.jsx` for state management
    - Integrate gamification section into Profile page showing level, XP, streak, badges
    - _Requirements: 4.5, 4.7, 4.8_

- [~] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Cross-Domain AI Context Engine
  - [~] 4.1 Create backend context engine service
    - Create `backend/context_engine.py` that assembles 7-day user data (mood, expenses, sleep, goals, burnout score) into a unified context object
    - Compute financial_health_score (0–100), wellness_composite_score (0–100), habit_consistency_percentage (0–100), active_stressors (max 10 items)
    - Implement graceful degradation: proceed with available data if a domain fails, indicate unavailable domains
    - Implement data sufficiency guard: skip cross-domain correlations if <3 days of data exist
    - Context assembly must complete within 2 seconds
    - _Requirements: 1.1, 1.4, 1.6, 1.7_

  - [~] 4.2 Implement cross-domain correlation detection
    - Detect emotional-eating pattern: stress > 70 AND food spending +30% vs prior 7 days
    - Detect burnout-risk: sleep avg < 6h for 3 consecutive days AND task completion < 50%
    - Surface correlation insights as InsightCards in Daily Hub AI Summary tab
    - Include wellness context in Finance Buddy when stress > 60 or sleep avg < 6.5h
    - _Requirements: 1.2, 1.3, 1.5_

  - [ ]* 4.3 Write property tests for context engine
    - **Property 1: Cross-Domain Context Assembly Completeness** — Generate multi-domain user data, verify all available data included
    - **Property 2: Correlation Threshold Detection** — Generate threshold-crossing data, verify insight generation
    - **Property 3: Computed Scores Satisfy Domain Constraints** — Verify all scores are integers 0–100, stressors ≤ 10
    - **Property 4: Conditional Wellness Context Inclusion** — Verify Finance Buddy includes wellness data when thresholds crossed
    - **Property 5: Data Sufficiency Guard** — Generate <3 days data, verify no correlations produced
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.7**

- [ ] 5. AI Buddy Personality and Conversation Memory
  - [~] 5.1 Create backend conversation memory service
    - Create `backend/conversation_memory.py` with message persistence (last 50 per buddy)
    - Implement history loading: include last 5 messages as context when user sends message in new session
    - Implement summarization: when >50 messages, summarize older than most recent 20 into ≤500 char summary
    - Store summaries in `conversation_summaries` collection
    - Graceful fallback: proceed without history if DB retrieval fails
    - _Requirements: 9.1, 9.2, 9.5, 9.6, 9.7_

  - [~] 5.2 Implement distinct buddy personalities in chat router
    - Update `backend/chat_router.py` (or existing chat logic in server.py) with distinct system prompts per buddy
    - Finance Buddy: include numeric values/budget references in responses
    - Wellness Buddy: use validating language before suggestions
    - Discover Buddy: include concrete recommendation with price/location
    - Helper Buddy: reference at least two life domains
    - Integrate cross-domain context from context_engine into chat prompts
    - Implement topic search in conversation history for "remember when" references
    - _Requirements: 9.3, 9.4_

  - [ ]* 5.3 Write property tests for conversation memory
    - **Property 26: Conversation Memory Retention and Summarization** — Generate 50+ messages, verify only 20 retained + summary ≤500 chars
    - **Property 27: Context Loading from History** — Generate histories, verify exactly 5 messages loaded in new session
    - **Validates: Requirements 9.1, 9.2, 9.5**

- [ ] 6. Smart Notifications and Proactive Nudges
  - [~] 6.1 Create backend notification service and router
    - Create `backend/notification_service.py` with nudge generation logic for budget warnings, wellness nudges, check-in reminders, streak celebrations
    - Create `backend/notification_router.py` with `/api/notifications`, `/api/notifications/{id}/dismiss`, `/api/notifications/preferences`, `/api/notifications/subscribe`
    - Budget warning: trigger when category reaches 80% of allocated amount
    - Wellness nudge: trigger when burnout score < 40, suggest recovery action
    - Check-in reminder: trigger if no mood entry by 10 PM local time
    - Streak celebration: trigger at milestones (7, 14, 30, 60, 90 days) with XP earned
    - Implement high-stress rate limit: max 3 nudges/day when stress > 70 for 2 consecutive days
    - Implement dismissal adaptation: 50% reduction for 7 days on single dismissal; suppress 14 days after 3 dismissals of same type
    - Implement notification preferences (enable/disable per category)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [ ]* 6.2 Write property tests for notification triggers
    - **Property 7: Notification Threshold Triggers** — Generate budget/wellness/streak states, verify correct nudges generated
    - **Property 8: High-Stress Notification Rate Limit** — Generate high-stress states, verify max 3 nudges/day
    - **Property 9: Dismissal-Based Frequency Adaptation** — Generate dismissal sequences, verify suppression rules
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.7**

  - [~] 6.3 Create frontend notification components
    - Create `frontend/src/components/NotificationBell.jsx` with unread badge count in Header
    - Create `frontend/src/pages/NotificationCenter.jsx` as sheet/drawer showing recent 10 notifications with timestamp, category icon, read/unread status
    - Create `frontend/src/pages/NotificationPreferences.jsx` with toggle switches per category
    - Create `frontend/src/context/NotificationContext.jsx` for state management and polling
    - Implement push notification subscription via Push API when permission granted
    - Display empty state "No notifications yet" when no nudges exist
    - _Requirements: 3.6, 3.8, 3.9, 12.8_

- [~] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Social Features and Peer Accountability
  - [~] 8.1 Create backend social module
    - Create `backend/social_service.py` with study group creation, invite code generation (6 alphanumeric chars), join/leave logic
    - Create `backend/social_router.py` with `/api/social/groups`, `/api/social/groups/{id}`, `/api/social/groups/{id}/join`, `/api/social/groups/{id}/leave`, `/api/social/groups/{id}/goals`, `/api/social/challenges`, `/api/social/challenges/{id}/join`
    - Enforce max 20 members per group
    - Shared goals with leaderboard sorted by completion percentage (descending)
    - Milestone notifications (25%, 50%, 75%, 100%) broadcast to all group members
    - Privacy enforcement: only display_name, level, shared goal progress visible to members
    - Weekly community challenges (Monday 00:00 UTC to Sunday 23:59 UTC)
    - Award 50 XP + badge on challenge completion via gamification service
    - On leave: remove from member list and leaderboards, retain personal XP/badges
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

  - [ ]* 8.2 Write property tests for social module
    - **Property 13: Invite Code Format and Group Capacity** — Verify 6 alphanumeric chars, reject joins at 20 members
    - **Property 14: Leaderboard Sort Order** — Generate progress data, verify descending sort by completion %
    - **Property 15: Milestone Broadcast** — Generate milestone crossings, verify notification to all other members
    - **Property 16: Group Privacy Enforcement** — Verify API responses contain only display_name, level, shared goal progress
    - **Property 17: Leave Group Data Integrity** — Verify removal from group + XP/badges unchanged
    - **Validates: Requirements 5.1, 5.4, 5.5, 5.8, 5.9**

  - [~] 8.3 Create frontend social components
    - Create `frontend/src/pages/StudyGroups.jsx` with group list, create group form, join by invite code
    - Create `frontend/src/components/StudyGroupCard.jsx` with member avatars preview
    - Create `frontend/src/components/GroupDetail.jsx` with members, shared goals, activity feed (20 recent items)
    - Create `frontend/src/components/InviteCodeInput.jsx` for 6-character entry with validation
    - Create `frontend/src/components/SharedGoalLeaderboard.jsx` showing progress per member
    - Create `frontend/src/components/CommunityChallenges.jsx` listing active weekly challenges
    - Add navigation to social features via BottomNav or SubTabs
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6_

- [ ] 9. Expense Auto-Categorization Enhancement
  - [~] 9.1 Create backend categorization service
    - Create `backend/categorization_service.py` with user-specific merchant-to-category rule storage
    - Store corrections as case-insensitive exact match rules in `user_category_rules` collection
    - Support up to 500 rules per user
    - On expense creation: check user rules first (case-insensitive merchant match), then keyword rules, then default to "misc"
    - Overwrite existing rule on re-correction to different category
    - Prompt user to confirm/correct when "misc" is assigned
    - Update existing `/api/expenses` POST endpoint to use new categorization logic
    - Add `/api/expenses/{id}/recategorize` endpoint for category corrections
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 9.2 Write property tests for auto-categorization
    - **Property 32: Categorization Rule Round-Trip** — Generate merchant/category corrections, verify rule persistence and application
    - **Property 33: Category Rules Capacity Cap** — Generate 500+ rules, verify cap enforcement
    - **Property 34: Default Category Fallback** — Generate unmatched merchants, verify "misc" assignment
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5**

- [ ] 10. Enhanced Data Analytics and Trend Detection
  - [~] 10.1 Create backend analytics service and router
    - Create `backend/analytics_service.py` with trend computation (weekly/monthly), anomaly detection, monthly report generation, recovery plan generation
    - Create `backend/analytics_router.py` with `/api/analytics/trends`, `/api/analytics/anomalies`, `/api/analytics/monthly-report`, `/api/analytics/recovery-plan`
    - Weekly trends: require minimum 7 days of data; monthly: minimum 28 days
    - Spending anomaly: flag when daily spend > 2× 30-day daily average, include amount, average, and % deviation
    - Monthly report (1st of month): total income vs spending, category budget adherence, savings progress, predicted month-end balance
    - Recovery plan: trigger when habit consistency < 40% for 14 days, suggest ≤3 schedule adjustments
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 10.2 Write property tests for analytics
    - **Property 18: Trend Computation Data Sufficiency** — Generate varying data lengths, verify minimum day requirements
    - **Property 19: Spending Anomaly Threshold Detection** — Generate expense data, verify 2× average detection
    - **Property 20: Habit Decline Triggers Recovery Plan** — Generate declining habit data, verify plan generation with ≤3 suggestions
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.5**

  - [~] 10.3 Create frontend analytics components
    - Create `frontend/src/pages/TrendsView.jsx` with interactive line/bar charts, time range selector (7d/30d/90d)
    - Create `frontend/src/components/AnomalyFlag.jsx` for inline spending anomaly indicators
    - Create `frontend/src/components/MonthlyReport.jsx` for financial health report card display
    - Charts must render within 2 seconds using recharts library
    - Add Trends view accessible from Daily Hub
    - _Requirements: 6.2, 6.3, 6.6_

- [~] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Daily Insights and Life-Balance Scoring
  - [~] 12.1 Create backend life-balance and daily insights endpoints
    - Create/update `/api/life-balance` endpoint with 5-domain radar scores (Finance, Wellness, Academics, Social, Self-Care), each integer 0–100
    - Compute from user-inputted data: Finance from expense-to-budget ratio + savings progress, Wellness from mood avg + sleep quality, Academics from task completion + study time, Social from group activity, Self-Care from exercise frequency + journal frequency
    - Create/update `/api/insights/daily` endpoint generating exactly 3 AI insight cards (financial tip, wellness suggestion, productivity recommendation) referencing specific user data points
    - Regenerate insights on first Daily Hub access after midnight (local timezone)
    - Implement "Tomorrow's Plan" logic: after 8 PM, return 3 actions ordered by lowest domain score first
    - Award 25 XP when user marks all 3 previous day's actions as complete
    - Handle partial data: compute with available days, display indicator noting days used
    - Low-score highlight: domains < 40 get red highlight + actionable step (≤140 chars)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ]* 12.2 Write property tests for life-balance scoring
    - **Property 3: Computed Scores Satisfy Domain Constraints** — Verify 5 scores, each integer 0–100
    - **Property 28: Daily Insight Card Count** — Verify exactly 3 cards generated
    - **Property 29: Low-Score Domain Actionable Step Length** — Verify step ≤140 characters for domains < 40
    - **Property 30: Tomorrow's Plan Ordering** — Verify 3 actions ordered by ascending domain score
    - **Property 31: Partial Data Score Computation** — Verify computation with <7 days includes day count indicator
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.6**

  - [~] 12.3 Update frontend Daily Hub with radar chart and insight cards
    - Add 5-domain life-balance radar chart to Daily Hub AI Summary tab (using recharts)
    - Render 3 AI-generated insight cards from `/api/insights/daily`
    - Highlight domains scoring <40 in red with actionable step
    - Add "Tomorrow's Plan" card (visible after 8 PM) with 3 ordered actions and completion checkboxes
    - Show celebration animation (3s) when all 3 actions marked complete with 25 XP
    - Display partial data indicator when <7 days available
    - Handle endpoint errors with retry button
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 12.10_

- [ ] 13. Voice Input for Journal Entries
  - [~] 13.1 Create frontend voice input module and component
    - Create `frontend/src/lib/voiceInput.js` wrapping Web Speech API with `isSupported()`, `start()`, `stop()` interface
    - Create `frontend/src/components/VoiceInputButton.jsx` with mic icon and pulsing recording indicator animation
    - Implement real-time transcript display in journal text area (within 500ms)
    - Stop on button tap or 3-second pause; finalize and append to existing text
    - Cap combined text at 5000 characters (truncate transcript to fit)
    - Hide voice button if Web Speech API is unsupported
    - Handle microphone permission denial with user-friendly message
    - Handle 10-second silence timeout with "try again in a quieter environment" message
    - Integrate into Journal entry screen
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 13.2 Write unit tests for voice input
    - Test Web Speech API support detection
    - Test transcript length capping at 5000 chars
    - Test silence timeout behavior
    - Test permission denial handling
    - **Property 6: Voice Transcript Length Cap** — Generate random existing text + transcript, verify combined ≤5000
    - **Validates: Requirements 2.3, 2.4, 2.5, 2.6**

- [ ] 14. Offline Support and PWA Capabilities
  - [~] 14.1 Create service worker and PWA manifest
    - Create service worker configuration (Workbox) to cache app shell (HTML, CSS, JS, icons)
    - Create `frontend/public/manifest.json` with icons (192×192, 512×512), theme color, display: "standalone"
    - Create `frontend/src/serviceWorkerRegistration.js` for SW registration
    - App must load offline within 3 seconds on subsequent visits
    - _Requirements: 7.1, 7.6_

  - [~] 14.2 Create frontend offline sync module
    - Create `frontend/src/lib/offlineSync.js` with IndexedDB storage (save, getAll, getCount, clear, sync)
    - Store mood, expenses, journal, sleep entries offline (max 500 entries)
    - Sync on reconnection within 30 seconds, retry up to 3 times (10s interval)
    - Implement conflict resolution: preserve both versions, prompt user to select (timestamp + source displayed)
    - Show warning at 500-entry capacity, block new entries until sync
    - _Requirements: 7.2, 7.3, 7.4, 7.8_

  - [~] 14.3 Create frontend offline UI components
    - Create `frontend/src/components/OfflineIndicator.jsx` for header offline status banner (show within 2s of connectivity change)
    - Create `frontend/src/components/SyncStatus.jsx` for sync progress indicator
    - Create `frontend/src/components/ConflictResolution.jsx` modal for resolving sync conflicts
    - Create `frontend/src/context/OfflineContext.jsx` for connectivity state management
    - Disable AI chat and discover features while offline with appropriate message
    - _Requirements: 7.5, 7.7_

  - [ ]* 14.4 Write property tests for offline storage
    - **Property 21: Offline Storage Capacity Cap** — Generate entry sequences, verify cap at 500 and rejection of entries beyond
    - **Property 22: Sync Conflict Dual Preservation** — Generate conflicting records, verify both versions preserved with timestamps
    - **Validates: Requirements 7.2, 7.4, 7.8**

- [~] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. UI Component Integration and Data Input Flows
  - [~] 16.1 Wire all Daily Hub input components to backend APIs
    - Ensure mood check-in (mood + energy + stress + motivation sliders) persists via `/api/mood`
    - Ensure expense logging (amount + merchant + category) persists via `/api/expenses`
    - Ensure journal entry (text) persists via `/api/journal`
    - Ensure sleep logging (hours + quality) persists via `/api/sleep`
    - Ensure task management (title + target_minutes + progress) persists via `/api/tasks`
    - Remove all hardcoded/seeded display data from production frontend
    - Display empty states with data input prompts when no user data exists
    - _Requirements: 12.2, 12.3, 12.4_

  - [~] 16.2 Wire Finance Buddy domain input components
    - Ensure expense logging, budget category allocation editing, subscription add/remove, savings goal creation (target amount), split bill entry all functional with real API calls
    - Remove "Scan Receipt" button from Daily Hub Expense tab and Finance Buddy Expenses tab
    - All financial graphs and AI insights derive exclusively from user-inputted entries
    - _Requirements: 12.1, 12.5, 12.12_

  - [~] 16.3 Wire Wellness Buddy domain input components
    - Ensure daily mood check-in, sleep entry (hours + quality + bedtime/waketime), bedtime goal selection, reflection text entry all functional
    - Wire PHQ-2 questionnaire: collect both answers, POST to `/wellness/phq2`, display AI-generated response card
    - Wire bedtime planner time buttons (10:30pm, 11:00pm, 11:30pm) to POST `/sleep/bedtime-goal`
    - Wire Wellness Dashboard action buttons (Quick Check-in, Breathing Exercise, Focus Session, Sleep Tips) to functional tabs/modals
    - All wellness scores and AI cards derive exclusively from user-inputted entries
    - _Requirements: 12.6, 12.13, 12.14, 12.17_

  - [~] 16.4 Wire Discover Buddy domain input components
    - Ensure exercise creation (name + body part + target minutes), session start/stop with elapsed time, discovery goal creation all functional
    - Wire "Notify Contact" button to send location notification to emergency contact
    - Wire "SOS" button to initiate emergency call
    - All fitness summaries derive exclusively from user-inputted exercise sessions
    - _Requirements: 12.7, 12.15_

  - [~] 16.5 Wire ChatCenter and AI Summary integrations
    - ChatCenter: fetch `/life-balance`, `/insights/daily`, `/insights/weekly` and render Helper Buddy command center with radar chart, daily insights, weekly review
    - Daily Hub AI Summary: fetch and render life-balance radar + 3 insight cards
    - Handle partial endpoint failures: render successful sections, show inline error for failed
    - Ensure AI chat context, wellness AI cards, daily insights, life-balance scores derive exclusively from user-inputted entries
    - AI acknowledges missing domain data and encourages user to input it
    - _Requirements: 12.10, 12.11, 12.18, 12.19, 12.20_

  - [~] 16.6 Integrate new features into navigation structure
    - Add gamification XP display, notification center, social groups, trends view as screens/sections accessible via BottomNav or SubTabs
    - Ensure every interactive element triggers a functional API call or navigates to functional screen
    - No non-functional placeholder buttons
    - _Requirements: 12.1, 12.9, 12.16_

- [ ] 17. Holistic UI/UX Coherence
  - [~] 17.1 Apply Domain Theme System and typography consistently
    - Ensure all pages in PhoneFrame inherit CSS variables (`--bdy`, `--bdy-soft`, `--bdy-2`) from `data-domain` attribute
    - Replace any hardcoded accent colors with `bdy-bg`, `bdy-text`, `bdy-soft`, `bdy-gradient` utilities
    - Apply Outfit font for all headings, card titles, numeric displays, `.font-display`
    - Apply Plus Jakarta Sans for body text, inputs, labels, small UI text
    - Remove any usage of Inter, Roboto, or Open Sans
    - Apply smooth color transition (200ms, ease-out) on domain changes via BottomNav
    - _Requirements: 13.1, 13.2, 13.6_

  - [~] 17.2 Apply Card, InsightCard, SubTabs, and empty state patterns
    - Ensure all content containers use Card component (bg-white, rounded-2xl, p-4, shadow-sm, border border-slate-100)
    - Ensure all AI-generated content uses InsightCard with domain-colored accent background
    - Ensure all buddy page tabbed navigation uses SubTabs pattern (shrink-0, px-3.5, py-1.5, rounded-full, text-xs, font-semibold)
    - Implement empty states with illustration/icon, descriptive text, and CTA for all zero-item views
    - _Requirements: 13.3, 13.7, 13.10_

  - [~] 17.3 Add loading states, error handling, and animations
    - Implement skeleton loading states (pulsing placeholder shapes) for all data-fetching sections
    - Implement user-friendly error messages with "Retry" button for all API failures (no raw codes/stack traces)
    - Add framer-motion animations: page transitions (fade-in + upward slide, 200–300ms), level-up celebration (scale-up + particles), achievement badge (slide-in from top), streak milestone (bounce effect)
    - _Requirements: 13.8, 13.9, 13.11_

  - [~] 17.4 Add data-testid attributes and accessibility compliance
    - Add `data-testid` (kebab-case, role-based) on all interactive and key informational elements
    - Ensure all content renders within PhoneFrame (max-w-[420px]), no horizontal overflow at 320–420px
    - Add `aria-label` on all interactive elements
    - Add visible focus states (ring-2 ring-offset-2 using domain color) on all buttons
    - Ensure WCAG AA contrast ratios: 4.5:1 for normal text, 3:1 for large text against colored backgrounds
    - _Requirements: 13.4, 13.5, 13.12_

- [~] 18. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Backend uses Python (FastAPI + Motor + emergentintegrations), frontend uses JavaScript (React 19 + Tailwind + shadcn/ui + framer-motion)
- Backend property tests use `hypothesis` library; frontend tests use Jest + React Testing Library
- The existing `DEMO_USER` pattern is replaced by JWT-derived user IDs after auth implementation
- All AI content must derive from user-inputted data — no hardcoded/seeded data in production

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4"] },
    { "id": 2, "tasks": ["2.1", "4.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "4.2", "5.1", "9.1"] },
    { "id": 4, "tasks": ["4.3", "5.2", "5.3", "9.2"] },
    { "id": 5, "tasks": ["6.1", "8.1", "10.1"] },
    { "id": 6, "tasks": ["6.2", "6.3", "8.2", "8.3", "10.2", "10.3"] },
    { "id": 7, "tasks": ["12.1"] },
    { "id": 8, "tasks": ["12.2", "12.3", "13.1"] },
    { "id": 9, "tasks": ["13.2", "14.1", "14.2"] },
    { "id": 10, "tasks": ["14.3", "14.4"] },
    { "id": 11, "tasks": ["16.1", "16.2", "16.3", "16.4"] },
    { "id": 12, "tasks": ["16.5", "16.6"] },
    { "id": 13, "tasks": ["17.1", "17.2"] },
    { "id": 14, "tasks": ["17.3", "17.4"] }
  ]
}
```
