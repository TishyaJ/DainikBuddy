# Discover Domain: Analysis & Improvement Tasks

## Current State Analysis

### Why is everything hardcoded?

The Discover Buddy was implemented during the initial spec sprint (Tasks 1–18) as a **static seed** — placeholder data to demonstrate the UI layout and flow. The comment in `server.py` literally says `# ============ DISCOVER (static seed) ============`. The endpoints return fixed JSON arrays regardless of user, location, or preferences.

**What's currently hardcoded (backend endpoints returning static arrays):**
- `GET /discover/food` → 4 fixed food places (Mess Express, Roll Zone, Student Thali, Coffee Cart)
- `GET /discover/travel` → 4 fixed routes (Metro, Cycle, Rideshare, Walk) with hardcoded Hostel → College
- `GET /discover/snacks` → 4 fixed brain-food items
- `GET /discover/activities` → 4 fixed stress-break activities
- `GET /discover/campus` → 4 fixed campus resources

**What's NOT fetched from anywhere intelligent:**
- No user location/college info used
- No source → destination route logic
- No food preference filtering
- No mess menu integration
- No real route/transport API calls
- No personalization based on budget or dietary needs
- Emergency contacts not stored/settable (only a stub endpoint exists)
- "Live route map" is a purple placeholder div — no map renders
- Student Deals section is fully hardcoded in frontend JSX

**Features that are misplaced:**
- "Activities" (stress breaks) → belongs in **Wellness** (already has similar exercise/breathing content)
- "Goals" → should be in **Social** domain (study groups + shared accountability)
- "Fitness" → should be in **Social** domain (exercise challenges, group fitness)
- "Snacks" → could merge with Wellness nutrition advice OR stay in Discover as food intelligence

---

## Task Plan

### Phase 1: Fix Structural Issues & Relocations

#### Task 1.1 — Move "Activities" (Stress Breaks) to Wellness
- Remove the `Activities` tab from DiscoverBuddy
- Merge into WellnessBuddy alongside existing sleep/exercise features
- Add timer functionality (countdown timer for each activity: 3min, 5min, 10min, 15min)
- Timer UI: start/pause/reset, circular progress, gentle chime on complete
- Keep the activities data in backend but serve from a `/api/wellness/activities` endpoint

#### Task 1.2 — Move "Goals" and "Fitness" to Social Domain
- Remove `Goals` and `Fitness` tabs from DiscoverBuddy
- Add them to StudyGroups page (Social domain) as additional tabs
- Goals → "My Goals" tab in Social (alongside My Groups / Challenges)
- Fitness → "Fitness" tab in Social (group exercise tracking, share progress)
- The "Join like-minded community" button already points to Social, so this makes logical sense

#### Task 1.3 — Fix Trends Graph (Life Balance)
- The Trends page shows "No trend data yet" even after logging data
- Investigate `analytics_service.py` data sufficiency check — likely requires 7+ days
- Add clearer messaging: "X more days of logging needed" with specific count
- Ensure the radar chart in Helper Buddy's Command Center shows correct domain scores

---

### Phase 2: Make Food Feature Intelligent

#### Task 2.1 — Mess Menu System
**Backend:**
- New endpoint `POST /api/discover/mess-menu` — upload/configure mess menu (per day/meal)
- Schema: `{day: "monday", meal: "lunch"|"dinner"|"breakfast", items: ["dal", "rice", "roti"], price: 50, subscription: bool}`
- New endpoint `GET /api/discover/mess-menu?day=today` — get today's menu
- `POST /api/discover/mess-subscription` — configure mess subscription (monthly ₹X, per-meal ₹Y)
- **Finance integration**: mess subscription auto-creates a budget category "Mess" with allocated amount
- Option for both per-meal tracking and subscription-based (monthly fixed cost)

**Frontend:**
- New "Mess" section in Food tab showing today's menu
- Upload mess menu option (manual entry or photo OCR placeholder)
- Mess subscription configuration card (monthly/per-meal toggle)
- Display: "Today's Mess: Dal + Rice + Sabzi — ₹50" with meal timing

#### Task 2.2 — Personalized Food Recommendations
**Backend:**
- New collection `user_food_preferences` storing: dietary type (veg/non-veg/vegan), allergies, cuisine likes/dislikes, budget per meal
- `POST /api/discover/food-preferences` — save preferences
- `GET /api/discover/food-preferences` — retrieve
- Update `GET /discover/food` to filter by user preferences (budget, dietary)
- Add mock data that respects filters (10-15 options, served filtered)

**Frontend:**
- One-time "Food Preferences" setup in Food tab (or onboarding)
- Dietary selector: Veg / Non-Veg / Vegan / Jain
- Budget per meal slider (₹20–₹200)
- Cuisine likes: North Indian, South Indian, Chinese, Street Food, Continental
- Allergies: Nuts, Dairy, Gluten (multi-select)

#### Task 2.3 — Snacks Intelligence
- Merge Snacks into Food tab as a sub-section
- Filter by user's dietary preferences
- Add: time-of-day awareness (morning → protein, late night → light, exam week → focus foods)
- Add budget filtering (only show snacks within remaining food budget)

---

### Phase 3: Make Travel Feature Intelligent

#### Task 3.1 — Source-Destination Route Logic
**Backend:**
- New endpoint `POST /api/discover/routes` with `{from: "hostel", to: "college"}`
- Store user's common locations: `POST /api/discover/saved-places` → `{name: "Hostel", address: "..."}`
- Returns route options with cost/time/mode (initially from configurable mock data per route pair)
- Support "hops" concept: if A→B has no direct, suggest A→X→B

**Frontend:**
- Replace hardcoded "Hostel → College" with selectable source/destination
- Saved Places: user adds their hostel, college, library, market, etc.
- Route cards show cost/time/mode comparison
- "Frequent Routes" section (auto-detected from usage)

#### Task 3.2 — Travel Goals Integration
- When user selects route for "Shopping" or "Outing" purpose:
  - Shopping: show budget-aware suggestions ("You have ₹500 left in shopping budget")
  - Outing: suggest affordable hangout spots en route
- Purpose selector: Commute / Shopping / Outing / Library / Medical

---

### Phase 4: Safe Night & Emergency Features

#### Task 4.1 — Emergency Contacts in Profile
**Backend:**
- Add `emergency_contacts` array to user profile: `[{name, phone, relationship}]`
- `PATCH /api/profile` already accepts arbitrary fields — ensure contacts are stored
- Existing `POST /api/safety/notify-contact` should read from this field

**Frontend:**
- Add "Emergency Contacts" section in Profile page
- Add/edit/remove contacts (max 3)
- Display which contact gets notified via "Notify Contact" button

#### Task 4.2 — Live Route Map Placeholder Enhancement
- Replace the purple placeholder with a useful display:
  - If location available: show lat/lng coordinates + timestamp
  - Add "Share Location" link (generates a Google Maps URL to share)
  - Add auto-refresh timer showing time since last location update
- No real map API integration yet (that's a deploy-time decision) — but make the UI functional

---

### Phase 5: Dynamic Data with Mock Backend

#### Task 5.1 — Replace Static Endpoints with DB-Driven Data
**Backend changes:**
- Create `discover_places` collection in MongoDB
- Seed with 10-15 food places, 5-6 travel routes, etc. during startup
- Endpoints query from DB instead of returning hardcoded arrays
- Add: user rating/review on food places (`POST /api/discover/food/{id}/rate`)
- Add: "hide" option (user hides a place they don't like)

#### Task 5.2 — Campus Resources as Configurable
- Move campus resources to DB collection
- Admin-configurable (or user-configurable for their college)
- Add: operating hours, booking URL, contact info
- The "Book" button should link out or trigger a booking flow

---

### Phase 6: Cross-Domain Intelligence

#### Task 6.1 — Finance Buddy Integration
- Mess subscription appears as a budget category automatically
- Food spending tracked against food budget (already works via categorization)
- Travel expenses auto-categorized as "Transport"
- Discover Buddy chat can reference budget: "You've spent ₹200 on food this week, ₹300 left"

#### Task 6.2 — Wellness Buddy Integration
- Activities (stress breaks) with timers live in Wellness
- If user's stress is high → Discover suggests low-effort food options ("Order in today")
- Sleep-deprived → Discover suggests nearby coffee options
- Exercise goals shared between Social (group) and personal tracking

---

## Revised Tab Structure After Changes

### Discover Buddy (slimmed down — focused on discovery)
| Tab | Content |
|-----|---------|
| Dashboard | Popular near you + Student Deals (dynamic from DB) |
| Food | Mess menu + Cheap eats (filtered by preferences) + Snacks |
| Travel | Source→Destination routes + Frequent routes + Travel tips |
| Safe Night | Emergency contacts + Location sharing + SOS |
| Campus | Campus resources (configurable) |

### Social Domain (expanded)
| Tab | Content |
|-----|---------|
| My Groups | Study groups (existing) |
| Challenges | Community challenges (existing) |
| Goals | Personal goals (moved from Discover) |
| Fitness | Exercise tracking (moved from Discover) |

### Wellness Domain (expanded)
| Tab | Content |
|-----|---------|
| Mood | Mood check-in (existing in DailyHub, link here) |
| Sleep | Sleep logging + bedtime planner (existing) |
| Activities | Quick stress breaks WITH timers (moved from Discover) |
| Exercises | Personal exercise log (keep reference to Social/Fitness) |

---

## Implementation Priority

1. **Phase 1** (structural fixes) — Do first, ~1 session. Moves features to correct domains.
2. **Phase 2** (food intelligence) — High value for student users. Mess menu is a killer feature.
3. **Phase 3** (travel intelligence) — Makes the Travel tab actually useful beyond hardcoded data.
4. **Phase 4** (safety) — Quick wins: emergency contacts in profile.
5. **Phase 5** (dynamic backend) — Makes everything DB-driven and extensible.
6. **Phase 6** (cross-domain) — The AI intelligence layer connecting everything.

---

## Notes for Implementation

- **Start with Phase 1** because it's pure restructuring (no new APIs needed, just moving components between files)
- **Phase 2.1 (Mess Menu)** is the single most impactful new feature for Indian college students — it's the #1 daily decision they make
- **Timers** (for activities): use a simple `useState` countdown with `useEffect` interval — no complex library needed
- **Mock data in DB** is better than hardcoded arrays because it makes the system extensible (admin can add new places later)
- The deep-research-report validates this direction: food insecurity affects 42% of students, travel costs are a major expense, and integrated financial + wellness support is the core differentiator
