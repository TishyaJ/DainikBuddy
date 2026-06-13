# Requirements Document

## Introduction

This document defines the requirements for enhancing and completing the PocketBuddy AI Financial & Wellness Assistant for Students. PocketBuddy is an AI companion super-app for college students that manages monthly expenses, recommends affordable food and travel options, detects burnout patterns, encourages healthy routines, and provides personalized support for financial and emotional well-being.

The existing prototype provides core CRUD features (mood, expenses, journal, goals, budget, sleep, exercise, wellness scores) along with AI-powered chat, wellness cards, and discover features. This enhancement focuses on closing feature gaps (voice input, notifications), strengthening AI intelligence (cross-domain insights, proactive nudges), adding engagement mechanics (gamification, social features), ensuring all UI components are wired to real backend APIs, maintaining visual coherence across the app, and hardening the system for production use (authentication, offline support, analytics).

## Glossary

- **PocketBuddy_System**: The complete PocketBuddy application including frontend (React), backend (FastAPI), database (MongoDB), and AI services
- **AI_Companion**: The AI subsystem that provides context-aware, personalized responses across finance, wellness, discover, and helper domains
- **Cross_Domain_Engine**: The analytics engine that correlates data across financial, wellness, and behavioral domains to generate unified insights
- **Notification_Service**: The subsystem responsible for scheduling, delivering, and managing proactive push notifications and in-app nudges
- **Voice_Processor**: The module that converts speech to text for journal entries via the Web Speech API
- **Gamification_Engine**: The subsystem that manages XP points, streaks, achievements, levels, and engagement rewards
- **Social_Module**: The subsystem that manages study groups, peer accountability partnerships, community challenges, and shared goals
- **Offline_Manager**: The service worker and local storage subsystem that enables core app functionality without network connectivity
- **Auth_Service**: The authentication and authorization subsystem managing user identity, sessions, and access control
- **UI_Layer**: The React frontend presentation layer including all pages, components, navigation, and visual interactions rendered inside the PhoneFrame container
- **Domain_Theme_System**: The CSS variable system that dynamically applies domain-specific colors via the `data-domain` attribute, controlling `--bdy`, `--bdy-soft`, and `--bdy-2` custom properties
- **User**: A college student who interacts with PocketBuddy
- **Nudge**: A short, contextual, proactive notification triggered by detected patterns in user data
- **Streak**: A consecutive-day count of user engagement with a specific habit or check-in activity
- **XP**: Experience Points awarded for completing actions, maintaining streaks, and achieving milestones
- **PWA**: Progressive Web App — a web application that uses service workers and manifests to provide native-app-like behavior
- **PhoneFrame**: The mobile-device simulator container component (max-w-[420px]) that wraps all app content on desktop viewports
- **SubTabs**: The horizontal scrollable pill-style tab navigation pattern used within buddy pages
- **Card**: The standard content container component (rounded-2xl, p-4, shadow-sm, border border-slate-100)
- **InsightCard**: The AI-generated content card component with domain-colored accent background

## Requirements

### Requirement 1: Cross-Domain AI Context Engine

**User Story:** As a student, I want the AI buddies to connect insights across my financial, wellness, and behavioral data, so that I receive holistic recommendations that account for how my spending, sleep, stress, and habits affect each other.

#### Acceptance Criteria

1. WHEN the User initiates a chat with any AI buddy, THE AI_Companion SHALL include the User's last 7 days of mood entries, expense totals by category, sleep averages, active goals, and burnout score in the conversation context, assembling the context within 2 seconds before generating the first response token
2. WHEN the Cross_Domain_Engine detects that the User's stress score exceeds 70 and food spending increased by more than 30% compared to the prior 7-day period within the same 7-day window, THE AI_Companion SHALL generate a correlation insight linking emotional eating to financial impact and display it as an insight card in the Daily Hub AI Summary tab
3. WHEN the User's sleep average drops below 6 hours for 3 consecutive days and academic task completion rate falls below 50% in the same 3-day period, THE Cross_Domain_Engine SHALL flag a burnout-risk correlation and surface it as an insight card in the Daily Hub AI Summary section
4. THE Cross_Domain_Engine SHALL compute a unified context object containing financial health score (0–100), wellness composite score (0–100), habit consistency percentage (0–100), and a list of active stressors (maximum 10 items) for every AI interaction
5. WHEN the User asks the Finance Buddy a question and the User's stress score exceeds 60 or sleep average is below 6.5 hours in the last 7 days, THE AI_Companion SHALL reference the relevant wellness data point in its response and explain how it may relate to the financial topic
6. IF the Cross_Domain_Engine cannot retrieve data for one or more domains (mood, expenses, sleep, goals) when assembling the conversation context, THEN THE AI_Companion SHALL proceed with available data and indicate to the User which domain data is unavailable in its first response
7. IF fewer than 3 days of data exist across all domains for the User, THEN THE Cross_Domain_Engine SHALL omit cross-domain correlation insights and THE AI_Companion SHALL respond using only single-domain knowledge relevant to the active buddy

### Requirement 2: Voice Input for Journal Entries

**User Story:** As a student, I want to dictate journal entries by voice, so that I can quickly capture thoughts hands-free without typing.

#### Acceptance Criteria

1. WHEN the User taps the "Voice" button on the Journal screen, THE Voice_Processor SHALL activate the device microphone and begin speech-to-text transcription using the Web Speech API
2. WHILE the Voice_Processor is actively recording, THE PocketBuddy_System SHALL display the transcript in the journal text area within 500 milliseconds of spoken input and show a visual recording indicator (pulsing animation)
3. WHEN the User taps the stop button or pauses for more than 3 seconds, THE Voice_Processor SHALL finalize the transcription and append the complete transcript to any existing text in the journal text field, up to a maximum of 5000 characters total
4. IF the Web Speech API is not supported by the User's browser, THEN THE PocketBuddy_System SHALL hide the voice input button on the Journal screen and display no error
5. IF the Voice_Processor fails to recognize speech after 10 seconds of silence, THEN THE PocketBuddy_System SHALL stop recording and display a message suggesting the User try again in a quieter environment
6. IF the User's browser denies microphone permission, THEN THE PocketBuddy_System SHALL stop the recording attempt and display a message indicating that microphone access is required for voice input

### Requirement 3: Smart Notifications and Proactive Nudges

**User Story:** As a student, I want to receive timely, context-aware notifications that alert me to budget risks, wellness concerns, and positive reinforcement, so that I can take corrective action before problems escalate.

#### Acceptance Criteria

1. WHEN a budget category reaches 80% of its allocated amount, THE Notification_Service SHALL send the User a budget warning nudge within 1 minute of the expense that triggered the threshold, displaying the category name, current spent percentage, and remaining amount
2. WHEN the User's burnout score drops below 40 (on a 0–100 scale), THE Notification_Service SHALL deliver a wellness nudge suggesting a specific recovery action (break, sleep, breathing exercise) based on the User's self-care preference from their onboarding pattern
3. WHEN the User has not logged a mood check-in by 10:00 PM in the User's configured local timezone on any day, THE Notification_Service SHALL send a reminder nudge containing only the prompt text to complete the daily check-in without additional content
4. WHEN the User completes a streak milestone (7, 14, 30, 60, 90 days), THE Notification_Service SHALL deliver a celebration notification with the streak count and earned XP
5. WHILE the User's stress score exceeds 70 (on a 0–100 scale) for 2 consecutive days, THE Notification_Service SHALL limit total nudges to a maximum of 3 per day to avoid notification fatigue
6. THE PocketBuddy_System SHALL provide a notification preferences screen where the User can enable or disable each nudge category (budget alerts, wellness reminders, streak celebrations, social updates) independently, and SHALL respect these preferences by suppressing delivery of disabled categories
7. WHEN the User dismisses a nudge, THE Notification_Service SHALL record the dismissal and reduce frequency of that nudge type by 50% for the following 7 days; IF the User dismisses the same nudge type more than 3 times within 7 days, THEN THE Notification_Service SHALL suppress that nudge type entirely for 14 days
8. THE Notification_Service SHALL deliver nudges as in-app notifications; IF the User has granted browser push notification permission, THEN THE Notification_Service SHALL additionally deliver nudges via push notification when the app is not in the foreground
9. IF the User has not granted browser notification permission when a push-eligible nudge is triggered, THEN THE Notification_Service SHALL display the nudge only within the in-app notification center without prompting for permission more than once per session

### Requirement 4: Gamification and Engagement System

**User Story:** As a student, I want to earn points, unlock achievements, and maintain streaks for healthy financial and wellness behaviors, so that I stay motivated to build positive habits.

#### Acceptance Criteria

1. WHEN the User completes a daily mood check-in, THE Gamification_Engine SHALL award 10 XP to the User's total; THE Gamification_Engine SHALL award XP only for the first mood check-in per calendar day and ignore subsequent check-ins on the same day
2. WHEN the User logs an expense, THE Gamification_Engine SHALL award 5 XP to the User's total; THE Gamification_Engine SHALL award XP for a maximum of 10 expense logs per calendar day
3. WHEN the User completes a journal entry, THE Gamification_Engine SHALL award 10 XP to the User's total; THE Gamification_Engine SHALL award XP only for the first journal entry per calendar day
4. WHEN the User maintains a consecutive daily check-in streak, THE Gamification_Engine SHALL award a streak bonus of (streak_days × 2) XP on each day the streak continues, capped at a maximum bonus of 100 XP per day; IF the User does not complete a mood check-in before 11:59 PM in their local timezone, THEN THE Gamification_Engine SHALL reset the streak to 0
5. WHEN the User's total XP crosses a level threshold (Level = floor(XP / 100) + 1), THE Gamification_Engine SHALL display a level-up animation lasting at least 3 seconds and update the User's displayed level
6. THE Gamification_Engine SHALL track and display achievements including: "First Week" (7-day streak), "Budget Master" (end month under budget), "Sleep Champion" (7 consecutive nights of 7+ hours), "Journal Keeper" (30 journal entries), and "Social Butterfly" (join 3 study groups)
7. WHEN the User earns a new achievement, THE Gamification_Engine SHALL display a badge notification with the achievement name and description, visible for at least 5 seconds or until the User dismisses it
8. THE PocketBuddy_System SHALL display the User's current level, total XP, active streak count, and earned badges on the Profile screen

### Requirement 5: Social Features and Peer Accountability

**User Story:** As a student, I want to form study groups, set shared goals with friends, and participate in community challenges, so that I have social support and accountability for my financial and wellness habits.

#### Acceptance Criteria

1. WHEN the User creates a study group, THE Social_Module SHALL generate a unique 6-character alphanumeric invite code that other Users can enter to join the group; THE Social_Module SHALL enforce a maximum of 20 members per group
2. WHEN the User joins a study group using a valid invite code, THE Social_Module SHALL display the group members (display name and level only), shared goals progress, and a group activity feed showing the 20 most recent activity items
3. IF the User enters an invalid or expired invite code, THEN THE Social_Module SHALL display an error message indicating the code is not valid and suggest the User verify the code with the group creator
4. WHEN the User sets a goal as "shared" with a study group, THE Social_Module SHALL display each member's progress toward that goal on a leaderboard within the group, ranked by completion percentage
5. WHEN any group member completes a shared goal milestone (25%, 50%, 75%, 100%), THE Social_Module SHALL notify all group members with a celebration message containing the member's display name and milestone reached
6. THE Social_Module SHALL provide weekly community challenges (e.g., "No impulse spending for 5 days", "Sleep 7+ hours for 5 nights") that Users can opt into; challenges SHALL start every Monday at 00:00 UTC and end Sunday at 23:59 UTC
7. WHEN the User completes a community challenge, THE Gamification_Engine SHALL award 50 bonus XP and a challenge-specific badge
8. THE Social_Module SHALL enforce privacy: only the User's display name, level, and shared goal progress are visible to group members; financial amounts, mood details, and journal entries remain private
9. WHEN the User leaves a study group, THE Social_Module SHALL remove the User from the group member list and remove their progress from shared goal leaderboards; the User's previously earned XP and badges SHALL be retained

### Requirement 6: Enhanced Data Analytics and Trend Detection

**User Story:** As a student, I want to see long-term trends in my spending, wellness, and habits with actionable predictions, so that I can make informed decisions about my lifestyle.

#### Acceptance Criteria

1. THE Cross_Domain_Engine SHALL compute weekly and monthly trend lines for spending by category, average mood score, sleep duration, and habit consistency; trend computation SHALL require a minimum of 7 days of data for weekly trends and 28 days for monthly trends
2. WHEN the User views the AI Summary tab, THE Cross_Domain_Engine SHALL display a 30-day trend comparison showing improvement or decline percentages for each tracked metric; IF fewer than 30 days of data exist, THEN the comparison SHALL use all available data and display the actual number of days used
3. WHEN the Cross_Domain_Engine detects a spending anomaly (daily spend exceeding 2x the User's 30-day daily average), THE PocketBuddy_System SHALL flag the anomaly in the expense feed with a contextual explanation including the anomalous amount, the 30-day daily average, and the percentage deviation
4. THE Cross_Domain_Engine SHALL generate a monthly financial health report on the 1st of each month containing: total income vs. spending, category-wise budget adherence percentages, savings goal progress, and a predicted month-end balance based on the current spending trajectory
5. WHEN the User's habit consistency for any tracked habit drops below 40% for 2 consecutive weeks (14 days), THE Cross_Domain_Engine SHALL generate a personalized recovery plan suggesting up to 3 specific schedule adjustments based on the User's energy peak and self-care preferences from their onboarding pattern
6. THE PocketBuddy_System SHALL provide a "Trends" view accessible from the Daily Hub that displays interactive charts (line charts for continuous metrics, bar charts for categorical metrics) for any metric over selectable time ranges (7 days, 30 days, 90 days); charts SHALL render within 2 seconds of selection

### Requirement 7: Offline Support and PWA Capabilities

**User Story:** As a student with unreliable internet connectivity, I want the app to work offline for core features and sync automatically when connectivity returns, so that I never lose data or access to basic functionality.

#### Acceptance Criteria

1. THE Offline_Manager SHALL cache the application shell (HTML, CSS, JavaScript, icons) using a service worker so the app loads without network connectivity within 3 seconds on subsequent visits
2. WHILE the device has no network connectivity, THE PocketBuddy_System SHALL allow the User to log mood entries, expenses, journal entries, and sleep data, storing them in IndexedDB up to a maximum of 500 entries
3. WHEN network connectivity is restored after an offline period, THE Offline_Manager SHALL synchronize all locally stored entries with the backend server within 30 seconds of reconnection, retrying up to 3 times with a 10-second interval if a sync attempt fails
4. IF a sync conflict occurs (same record modified both offline and on server), THEN THE Offline_Manager SHALL preserve both versions and prompt the User to select which version to keep, displaying the timestamp and source (local or server) of each version
5. WHEN the device loses network connectivity, THE PocketBuddy_System SHALL display an offline indicator in the header within 2 seconds of detecting the connectivity change, and remove it within 2 seconds of connectivity being restored
6. THE PocketBuddy_System SHALL provide a web app manifest with icons in at least 192x192 and 512x512 pixel sizes, a defined theme color, and display mode set to "standalone" enabling home-screen installation on mobile devices
7. WHILE offline, THE PocketBuddy_System SHALL disable AI chat and discover features, displaying a message that these features require internet connectivity
8. IF the IndexedDB offline storage reaches its 500-entry capacity, THEN THE PocketBuddy_System SHALL display a warning message indicating that offline storage is full and prevent new entries until connectivity is restored and sync completes

### Requirement 8: Authentication and Security

**User Story:** As a student, I want my financial and wellness data protected by secure authentication and encryption, so that my sensitive personal information remains private and accessible only to me.

#### Acceptance Criteria

1. WHEN the User opens PocketBuddy for the first time, THE Auth_Service SHALL display a registration screen requiring a valid email address (maximum 254 characters, standard email format validation) and password (minimum 8 characters, maximum 128 characters, at least one uppercase letter and one number)
2. WHEN the User submits valid registration credentials, THE Auth_Service SHALL create a user account, hash the password using bcrypt with a cost factor of 12, and issue a JWT access token with a 24-hour expiration
3. WHEN the User submits valid login credentials, THE Auth_Service SHALL verify the password hash and return a JWT access token and a refresh token with 30-day expiration
4. WHEN a request arrives at any authenticated API endpoint without a valid JWT token, THE Auth_Service SHALL return a 401 Unauthorized response
5. WHEN the JWT access token expires, THE Auth_Service SHALL accept the refresh token to issue a new access token without requiring the User to re-enter credentials
6. THE PocketBuddy_System SHALL transmit all data between frontend and backend over HTTPS exclusively
7. THE Auth_Service SHALL provide a "Forgot Password" flow that sends a password-reset link to the User's registered email, valid for 15 minutes; IF the submitted email is not associated with any account, THEN THE Auth_Service SHALL display the same success message as for registered emails to prevent account enumeration
8. WHEN the User navigates to Profile settings, THE PocketBuddy_System SHALL provide options to export personal data (JSON format) and to delete the account; WHEN the User selects account deletion, THE PocketBuddy_System SHALL require an explicit confirmation step before permanently removing the user account and all associated data (expenses, mood entries, journal entries, goals, chat history, and gamification data)
9. IF the User submits login credentials with an incorrect password or unregistered email, THEN THE Auth_Service SHALL return a generic error message indicating invalid credentials without specifying whether the email or password was incorrect, and SHALL allow a maximum of 5 failed login attempts per email within a 15-minute window before temporarily locking login for that email for 15 minutes
10. IF the User submits registration credentials with an email already associated with an existing account, THEN THE Auth_Service SHALL reject the registration and display an error message indicating the email is already in use

### Requirement 9: AI Buddy Personality and Conversation Memory

**User Story:** As a student, I want each AI buddy to remember past conversations and maintain a consistent personality, so that interactions feel personal and build on previous context rather than starting fresh each time.

#### Acceptance Criteria

1. THE AI_Companion SHALL maintain a conversation history of the last 20 messages per buddy (finance, wellness, discover, helper) persisted in the database, where each user message and each assistant response counts as one message individually
2. WHEN the User sends a message to a buddy after no messages have been exchanged in the current browser session, THE AI_Companion SHALL include the last 5 messages (ordered chronologically) from the stored conversation history as context in the prompt sent to the language model
3. THE AI_Companion SHALL include a distinct system prompt for each buddy that produces observable tone differences: Finance Buddy responses SHALL contain numeric values or budget references, Wellness Buddy responses SHALL use validating language before offering suggestions, Discover Buddy responses SHALL include at least one concrete recommendation with a price or location, and Helper Buddy responses SHALL reference at least two life domains (finance, wellness, productivity, or discovery)
4. WHEN the User references a previous conversation topic (e.g., "remember when I said I was stressed about rent"), THE AI_Companion SHALL search the stored conversation history for the buddy and, if a matching topic is found within the retained messages, include the relevant prior exchange in the model context so the response acknowledges the prior topic by restating or building on it
5. WHEN the conversation history for a buddy exceeds 50 messages, THE AI_Companion SHALL summarize messages older than the most recent 20 into a single context note of no more than 500 characters and retain only the 20 most recent full messages alongside the summary
6. IF the conversation history cannot be retrieved from the database when the User sends a message, THEN THE AI_Companion SHALL proceed with the current message only (without prior context) and return a response without displaying an error to the User
7. WHEN the User sends the first-ever message to a buddy with no prior conversation history, THE AI_Companion SHALL respond using only the buddy's system prompt personality and the current message without injecting any prior context

### Requirement 10: Daily Insights and Life-Balance Scoring Enhancement

**User Story:** As a student, I want a comprehensive daily AI-generated summary that connects my financial, wellness, and academic progress into an actionable plan, so that I have clear daily guidance.

#### Acceptance Criteria

1. WHEN the User opens the Daily Hub, THE PocketBuddy_System SHALL display a life-balance radar chart within 3 seconds with scores (each an integer from 0 to 100) for Finance, Wellness, Academics, Social, and Self-Care computed from the last 7 days of data
2. THE Cross_Domain_Engine SHALL generate exactly 3 daily insight cards once per calendar day (regenerated on first Daily Hub access after midnight in the User's local timezone): one financial tip, one wellness suggestion, and one productivity recommendation, each referencing at least one specific data point from the User's last 7 days of tracked metrics
3. WHEN the life-balance radar shows any domain scoring below 40, THE PocketBuddy_System SHALL highlight that domain in red and provide a single actionable step (maximum 140 characters) referencing the specific domain to improve it
4. WHEN the User views the Daily Hub after 8:00 PM in the User's local timezone, THE PocketBuddy_System SHALL display a "Tomorrow's Plan" card containing exactly 3 actions ordered by the domain with the lowest life-balance score first, derived from the User's goals, habits, and detected patterns
5. WHEN the User manually marks all 3 suggested actions from the previous day's plan as complete via a checkbox or completion button on each action, THE Gamification_Engine SHALL award 25 bonus XP and display a completion celebration animation for at least 3 seconds showing the XP earned
6. IF the User has fewer than 7 days of tracked data for any domain, THEN THE PocketBuddy_System SHALL compute the life-balance score using only the available days of data and display an indicator noting the number of days used in the calculation

### Requirement 11: Expense Auto-Categorization Enhancement

**User Story:** As a student, I want the expense categorization to be more accurate by learning from my correction patterns, so that manual re-categorization becomes unnecessary over time.

#### Acceptance Criteria

1. WHEN the User manually changes the category of an auto-categorized expense, THE PocketBuddy_System SHALL store the correction as a user-specific categorization rule mapping the merchant name (case-insensitive exact match) to the newly assigned category, replacing any previous rule for that merchant
2. WHEN the User logs a new expense with a merchant name that matches a stored user-specific rule via case-insensitive exact string comparison, THE PocketBuddy_System SHALL apply the user-specific category instead of the default keyword-based detection
3. THE PocketBuddy_System SHALL maintain a user-specific merchant-to-category mapping table supporting up to 500 stored rules per user, returning the correct category for any previously corrected merchant within 1 second of expense submission
4. WHEN a new expense matches no user-specific rule and no keyword-based rule, THE PocketBuddy_System SHALL assign the category "misc" and display a prompt asking the User to confirm or correct the category
5. IF the User corrects the same merchant to a different category than a previously stored rule, THEN THE PocketBuddy_System SHALL overwrite the existing rule with the most recent correction and apply the updated category to all future expenses from that merchant

### Requirement 12: UI Component Integration and Data Input Flows

**User Story:** As a student, I want every feature button and UI element in the app to be functional and connected to real backend data, so that I can actually use the features presented to me rather than encountering dead-end placeholders, and I want to be able to input all the data the app needs directly from the home and domain screens so that AI chatbots, graphs, analysis cards, and recommendations are always grounded in my real data.

#### Acceptance Criteria

1. THE UI_Layer SHALL ensure that every interactive button, card, and navigation element visible to the User either triggers a functional backend API call or navigates to a functional screen; THE UI_Layer SHALL NOT render non-functional placeholder buttons that perform no action on tap
2. THE PocketBuddy_System SHALL NOT hardcode or seed any display data (budget amounts, expense lists, mood history, sleep entries, goals, wellness scores, or insight text) for production use; every value displayed in charts, cards, progress indicators, and AI-generated content SHALL be computed from User-inputted data stored in the database
3. THE Daily Hub SHALL provide input components for every data type that feeds the AI context engine: mood check-in (mood + energy + stress + motivation sliders), expense logging (amount + merchant + category), journal entry (text), sleep logging (hours + quality), and task management (title + target minutes + progress); each input SHALL persist to the backend via API call immediately upon submission
4. WHEN any chart, score ring, progress bar, trend line, or numeric display across the app has no underlying User-inputted data, THE UI_Layer SHALL display an empty state prompting the User to input the relevant data rather than showing zero values or placeholder data
5. THE Finance Buddy domain SHALL provide input components for: expense logging, budget category allocation editing, subscription addition/removal, savings goal creation with target amount, and split bill entry (title, total, person, amounts); all financial graphs and AI insights SHALL derive exclusively from these User-inputted entries
6. THE Wellness Buddy domain SHALL provide input components for: daily mood check-in (mood + sliders), sleep entry (hours + quality + bedtime/waketime), PHQ-2 questionnaire responses (2 questions × 4 options each persisted via POST), bedtime goal selection, and reflection text entry; all wellness scores, burnout risk indicators, and AI wellness cards SHALL derive exclusively from these User-inputted entries
7. THE Discover Buddy domain SHALL provide input components for: exercise creation (name + body part + target minutes), exercise session start/stop with elapsed time, and discovery goal creation; all fitness summaries, sedentary warnings, and body-part balance analysis SHALL derive exclusively from these User-inputted exercise sessions
8. WHEN the User taps the notification bell icon in the Header component, THE UI_Layer SHALL open a notification center panel displaying the 10 most recent nudges with their timestamp, category icon, and read/unread status; WHEN no nudges exist, THE UI_Layer SHALL display an empty state with the text "No notifications yet"
9. WHEN the User navigates to the Profile page, THE UI_Layer SHALL display the User's gamification data including current level, total XP with a progress bar to next level, active streak count, and earned badges in a dedicated section above the account settings
10. WHEN the User opens the Daily Hub and selects the "AI Summary" tab, THE UI_Layer SHALL fetch data from the `/life-balance` and `/insights/daily` backend endpoints and render the life-balance radar chart and 3 insight cards; IF either endpoint returns an error, THEN THE UI_Layer SHALL display a user-friendly error message with a retry button
11. WHEN the User opens the ChatCenter page, THE UI_Layer SHALL fetch data from the `/life-balance`, `/insights/daily`, and `/insights/weekly` endpoints and render the Helper Buddy command center section including the radar chart, daily insights, and weekly review scorecard; IF any endpoint fails, THEN THE UI_Layer SHALL render the remaining successful sections and show an inline error for the failed section
12. THE UI_Layer SHALL remove the "Scan Receipt" button from the Daily Hub Expense tab and the Finance Buddy Expenses tab since receipt scanning is deprioritized; expense logging SHALL rely exclusively on the manual form fields (amount, merchant, category)
13. WHEN the User taps any Bedtime Planner time button (10:30pm, 11:00pm, 11:30pm) on the Wellness Buddy Sleep tab, THE UI_Layer SHALL send a POST request to `/sleep/bedtime-goal` with the selected time and display a confirmation message showing the set bedtime goal
14. WHEN the User taps the PHQ-2 response buttons on the Wellness Buddy Check-Ins tab, THE UI_Layer SHALL collect both answers and send a POST request to `/wellness/phq2` with the scores; THE UI_Layer SHALL display an AI-generated response card with supportive guidance based on the total score
15. WHEN the User taps "Notify Contact" or "SOS" buttons on the Discover Buddy Safe Night tab, THE UI_Layer SHALL trigger the corresponding action: "Notify Contact" SHALL send a location-sharing notification to the User's configured emergency contact, and "SOS" SHALL initiate a call to the campus emergency number or configured emergency service
16. WHEN new features are added (gamification XP display, notification center, social groups, trends view), THE UI_Layer SHALL integrate them as dedicated screens or sections within the existing page structure accessible via the BottomNav or SubTabs navigation patterns
17. WHEN the User taps any Wellness Dashboard action button (Quick Check-in, Breathing Exercise, Focus Session, Sleep Tips), THE UI_Layer SHALL navigate to the corresponding functional tab or display an interactive modal with the relevant feature content
18. THE AI_Companion chat context, wellness AI cards, daily insights, life-balance scores, and all recommendation cards SHALL derive their data exclusively from User-inputted entries (mood, expenses, journal, sleep, tasks, exercises, goals, onboarding pattern); THE PocketBuddy_System SHALL NOT generate AI responses based on fabricated or assumed data that the User has not entered
19. WHEN the User has not yet inputted data for a specific domain (e.g., zero expenses logged, zero sleep entries), THE AI_Companion SHALL acknowledge the missing data and encourage the User to input it rather than generating recommendations based on non-existent data
20. THE Daily Hub "AI Summary" tab life-balance radar chart SHALL compute each domain score from the following User-inputted sources: Finance score from expense-to-budget ratio and savings progress, Wellness score from mood average and sleep quality, Academics score from task completion rate and study session time, Social score from group membership activity and social event attendance, and Self-Care score from exercise frequency and journal entry frequency

### Requirement 13: Holistic UI/UX Coherence for Student Experience

**User Story:** As a student, I want the app to feel polished, consistent, and delightful across every screen, so that I trust the app with my personal data and enjoy using it daily.

#### Acceptance Criteria

1. THE UI_Layer SHALL apply the Domain_Theme_System consistently across all screens: every page wrapped in PhoneFrame SHALL inherit CSS variables (`--bdy`, `--bdy-soft`, `--bdy-2`) from the active `data-domain` attribute, and all accent-colored elements SHALL use `bdy-bg`, `bdy-text`, `bdy-soft`, or `bdy-gradient` utility classes instead of hardcoded color values
2. THE UI_Layer SHALL use the Outfit font family for all headings (h1–h6), card titles, numeric displays, and the `.font-display` class, and SHALL use Plus Jakarta Sans for all body text, input fields, labels, and small UI text; the UI_Layer SHALL NOT use Inter, Roboto, or Open Sans anywhere in the application
3. THE UI_Layer SHALL render all feature content containers using the Card component pattern (bg-white, rounded-2xl, p-4, shadow-sm, border border-slate-100); all AI-generated content blocks SHALL use the InsightCard component with domain-colored accent background (`bdy-soft`) and a domain-colored icon container
4. THE UI_Layer SHALL include `data-testid` attributes on all interactive elements (buttons, inputs, navigation items, cards) and key informational elements, using kebab-case role-based naming format as defined in the design guidelines
5. THE UI_Layer SHALL render all content within the PhoneFrame container (max-w-[420px]) and all layouts SHALL be designed mobile-first; horizontal overflow SHALL NOT occur on any screen at viewport widths between 320px and 420px
6. WHEN the User navigates between buddy pages via BottomNav (causing a domain change), THE UI_Layer SHALL apply a smooth color transition (duration 200ms, ease-out timing function) from the previous domain's color palette to the new domain's color palette on all `bdy-*` themed elements
7. WHEN a list view, feed, or data display section contains zero items, THE UI_Layer SHALL render an empty state containing a relevant illustration or icon, descriptive text explaining what the section shows, and a call-to-action button or prompt guiding the User on how to add the first item
8. WHILE the UI_Layer is fetching data from any backend API endpoint, THE UI_Layer SHALL display a skeleton loading state (pulsing placeholder shapes matching the expected content layout) in place of the content area until data arrives or an error occurs
9. IF any API call made by the UI_Layer returns an error (network failure, server error, timeout), THEN THE UI_Layer SHALL display a user-friendly error message describing the issue in plain language and a "Retry" button that re-attempts the failed request; THE UI_Layer SHALL NOT display raw error codes or stack traces to the User
10. THE UI_Layer SHALL use the SubTabs horizontal scrollable pill pattern (shrink-0, px-3.5, py-1.5, rounded-full, text-xs, font-semibold) for all tabbed navigation within buddy pages, with active state using `bdy-bg text-white` and inactive state using `bg-white text-slate-600 border border-slate-200`
11. THE UI_Layer SHALL use framer-motion for page transition animations (fade-in with slight upward slide, duration 200–300ms), level-up celebration overlays (scale-up with particle effects), achievement badge notifications (slide-in from top), and streak milestone animations (bounce effect on the streak counter)
12. THE UI_Layer SHALL ensure all interactive elements have appropriate `aria-label` attributes describing their function, all buttons SHALL have visible focus states (ring-2 ring-offset-2 using domain color), and all text against colored backgrounds SHALL meet WCAG AA contrast ratio minimum of 4.5:1 for normal text and 3:1 for large text
