# Implementation Plan: Intelligent Discover Module

## Overview

Transform PocketBuddy's static Discover module into an AI-powered system using the existing Groq LLM integration. Implementation is in Python (FastAPI backend) and React (frontend). The approach is incremental: fix the ObjectId bug first, then add backend services (travel, food, campus), then update the frontend.

## Tasks

- [ ] 1. Fix ObjectId serialization bug
  - [ ] 1.1 Create `sanitize_mongo_doc` utility and fix `add_saved_place`
    - Add a `sanitize_mongo_doc(doc: dict) -> dict` helper function in `backend/server.py` (near the top utility section)
    - The function pops `_id` from the dict and returns it
    - Apply it in `add_saved_place` endpoint after `insert_one()` call
    - Apply it in `add_campus_resource` endpoint after `insert_one()` call
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 1.2 Write property tests for `sanitize_mongo_doc`
    - **Property 1: ObjectId Exclusion and Field Preservation**
    - Generate random dicts (with and without `_id` keys), verify `_id` is never in output and all other keys are preserved
    - File: `backend/tests/test_discover_sanitize.py`
    - Use `hypothesis` library
    - **Validates: Requirements 1.1, 1.2, 1.3, 4.3**

- [ ] 2. Implement Intelligent Travel Service (backend)
  - [ ] 2.1 Create `backend/discover_travel_service.py` with `TravelService` class
    - Implement `get_routes(source, destination, user_id)` → orchestrates cache check, LLM call, fallback
    - Implement `get_cached_route(source, destination)` → queries `route_cache` collection with TTL check
    - Implement `estimate_via_llm(source, destination)` → constructs travel prompt, calls LLM via `LlmChat`, parses JSON response
    - Implement `estimate_via_formula(distance_km)` → deterministic pricing using rates from design (Auto ₹25+₹15/km, Bus ₹7/km, Metro ₹10+₹3/km cap ₹60, Ola/Uber ₹50+₹10/km, Rickshaw ₹20+₹10/km <5km, Walk ₹0 <3km)
    - Implement `_cache_result(source, destination, routes)` → store in `route_cache` with 24h TTL
    - Normalize inputs: `source.strip().lower()` for cache key matching
    - Import `LlmChat, UserMessage, TextDelta, StreamDone` from `emergentintegrations.llm.chat`
    - Use `os.getenv("GROQ_API_KEY")` for API key, model `llama-3.3-70b-versatile`
    - LLM temperature: 0.3 for deterministic pricing
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8_

  - [ ] 2.2 Add `POST /discover/routes` endpoint in `backend/server.py`
    - Accept `{from: str, to: str}` payload
    - Validate: if source or destination is empty/whitespace → HTTP 400 "Source and destination required"
    - Instantiate `TravelService(db)` and call `get_routes()`
    - Return `{"routes": [...], "from": source, "to": destination, "saved_places": [...]}`
    - Keep existing `GET /discover/travel` endpoint untouched (legacy fallback)
    - _Requirements: 2.1, 2.7, 2.9_

  - [ ]* 2.3 Write property tests for fare formula
    - **Property 2: Fare Formula Non-Negativity and Determinism**
    - **Property 3: Fare Formula Mode Appropriateness**
    - Generate random positive floats for distance, verify all costs >= 0, deterministic output, and mode constraints (no Rickshaw >5km, no Walk >3km)
    - File: `backend/tests/test_travel_service.py`
    - Use `hypothesis` with `st.floats(min_value=0.1, max_value=500)`
    - **Validates: Requirements 2.6**

  - [ ]* 2.4 Write property test for input validation
    - **Property 7: Empty/Whitespace Input Rejection**
    - Generate whitespace-only strings, verify POST /discover/routes returns 400
    - File: `backend/tests/test_travel_service.py`
    - **Validates: Requirements 2.7**

- [ ] 3. Checkpoint - Verify travel service
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement AI Food Recommendation Service (backend)
  - [ ] 4.1 Create `backend/discover_food_service.py` with `FoodRecommendationService` class
    - Implement `get_recommendations(user_id)` → orchestrates context build, cache check, LLM call, filtering
    - Implement `build_context(user_id)` → fetch user_food_preferences, user profile (college/city), compute time_of_day
    - Construct food prompt with: dietary, budget, cuisines, location, time_of_day (from design FOOD_SYSTEM_PROMPT / FOOD_USER_PROMPT)
    - Call LLM with temperature 0.5 for variety
    - Parse JSON response, validate each item has required fields (name, price, rating, distance, tag, dietary, reason)
    - Filter by budget: `item["price"] <= budget_per_meal`
    - Filter by dietary: `matches_dietary(item_dietary, user_dietary)` helper
    - Cache results in `food_recommendation_cache` collection with key `{user_id}_{time_of_day}_{dietary}`, 6h TTL
    - On ANY exception: return empty list (NO hardcoded fallback)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [ ] 4.2 Update `GET /discover/food` endpoint in `backend/server.py`
    - Replace the hardcoded food array with call to `FoodRecommendationService(db).get_recommendations(user_id)`
    - On success: return `{"items": recommendations, "error": null}`
    - On empty result (LLM failed): return `{"items": [], "error": "Unable to fetch recommendations. Please try again."}`
    - Remove all hardcoded `all_food` array from the endpoint
    - _Requirements: 3.6, 3.7, 3.8, 3.9_

  - [ ]* 4.3 Write property tests for dietary and budget filtering
    - **Property 5: Dietary Filter Correctness**
    - **Property 6: Budget Filter Correctness**
    - Generate random food item lists with random prices/dietary values, apply filter functions, verify constraints hold
    - File: `backend/tests/test_food_service.py`
    - Use `hypothesis` with custom strategies for food items
    - **Validates: Requirements 3.3, 3.4**

- [ ] 5. Implement Dynamic Campus Resources Service (backend)
  - [ ] 5.1 Update campus endpoints to apply `sanitize_mongo_doc`
    - In `add_campus_resource`: call `sanitize_mongo_doc(resource)` after `insert_one()`
    - Verify `get_campus_resources` already uses `{"_id": 0}` projection (it does)
    - Ensure default seed resources include realistic Indian college data (counseling center with helpline, library 8AM-10PM, health center 24/7, etc.)
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 6. Checkpoint - Verify all backend services
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Update Frontend Travel Tab
  - [ ] 7.1 Replace dropdown selects with free-text inputs in Travel component
    - In `frontend/src/pages/DiscoverBuddy.jsx`, update the `Travel` component
    - Replace `<select>` elements for fromPlace/toPlace with `<input type="text">` fields
    - Add a "Compare Routes" submit button that triggers the POST request
    - Add `loading` state (boolean) and `error` state (string|null)
    - On submit: `POST /discover/routes` with `{from: fromPlace, to: toPlace}`
    - While loading: show a spinner/loading text in the route grid area
    - On error: show error message with "Try Again" button
    - On success: display route cards as before (from response.data.routes)
    - Keep saved places section for quick-fill (clicking a saved place fills the input)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 8. Update Frontend Food Tab
  - [ ] 8.1 Update Food component to handle new response format
    - In `frontend/src/pages/DiscoverBuddy.jsx`, update the `Food` component
    - Change `api.get("/discover/food")` handler to read `response.data.items` (array) and `response.data.error` (string|null)
    - Add `loading` state and `error` state
    - While loading: show skeleton/loading indicator in the food grid
    - If `error` is non-null: show error message card with "Try Again" button that re-calls the endpoint
    - Update food card rendering to show `reason` field (AI-generated recommendation reason)
    - Remove the hardcoded `InsightCard` about "Student Thali" (no longer relevant with AI data)
    - Handle the case where `items` is an empty array with no error (show "No recommendations available")
    - _Requirements: 5.5, 5.6, 5.7, 5.8_

- [ ] 9. Update Frontend Dashboard
  - [ ] 9.1 Update Dashboard component to handle new food response format
    - The Dashboard also calls `GET /discover/food` — update it to read `response.data.items`
    - Handle the case where items is empty or error is present gracefully
    - _Requirements: 5.5_

- [ ] 10. Final Checkpoint - Integration verification
  - Ensure all tests pass, ask the user if questions arise.
  - Verify `POST /discover/routes` returns correct data with mocked LLM
  - Verify `GET /discover/food` returns AI-generated data with mocked LLM
  - Verify ObjectId bug is fixed (no `_id` in responses)
  - Verify frontend handles loading, success, and error states

## Task Dependency Graph

```json
{
  "waves": [
    {
      "name": "Wave 1 - ObjectId Bug Fix",
      "tasks": ["1.1"],
      "description": "Fix the ObjectId serialization bug and create sanitize utility"
    },
    {
      "name": "Wave 2 - Backend Services",
      "tasks": ["2.1", "2.2", "4.1", "4.2", "5.1"],
      "description": "Implement travel service, food service, and campus resource fixes (can be parallel)"
    },
    {
      "name": "Wave 3 - Backend Verification",
      "tasks": ["2.3", "2.4", "4.3"],
      "description": "Property tests for backend services"
    },
    {
      "name": "Wave 4 - Frontend Updates",
      "tasks": ["7.1", "8.1", "9.1"],
      "description": "Update Travel tab, Food tab, and Dashboard to use new endpoints"
    }
  ]
}
```

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- The LLM integration uses the existing `emergentintegrations.llm.chat` module — no new dependencies needed
- All new backend files: `discover_travel_service.py`, `discover_food_service.py`
- All test files go in `backend/tests/`
- Frontend changes are contained to `frontend/src/pages/DiscoverBuddy.jsx`
- Cache collections: `route_cache` (24h TTL), `food_recommendation_cache` (6h TTL)
