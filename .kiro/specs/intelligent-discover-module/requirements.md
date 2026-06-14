# Requirements Document

## Introduction

This document defines the requirements for transforming PocketBuddy's static "Discover Buddy" module into an intelligent, AI-powered system. The module addresses four areas: fixing a MongoDB ObjectId serialization bug, implementing LLM-powered travel route comparison with real Indian pricing, replacing hardcoded food recommendations with fully AI-generated suggestions from real restaurants, making campus resources DB-driven, and updating the frontend to support free-text route input and graceful error handling.

## Glossary

- **System**: The PocketBuddy Discover Module backend (FastAPI + Motor)
- **Frontend**: The React DiscoverBuddy page component
- **LLM**: The Groq-hosted Llama 3.3 70B model accessed via `emergentintegrations.llm.chat`
- **Route_Cache**: MongoDB collection storing cached route comparison results
- **Food_Cache**: MongoDB collection storing cached food recommendations per user+meal-time
- **Travel_Service**: Backend service that generates intelligent route comparisons
- **Food_Service**: Backend service that generates AI-powered food recommendations
- **Campus_Service**: Backend service that manages DB-driven campus resources
- **Fare_Formula**: Deterministic distance-based pricing calculation used as LLM fallback
- **Saved_Place**: A user-defined location stored in MongoDB

## Requirements

### Requirement 1: ObjectId Bug Fix

**User Story:** As a user, I want saved places to be returned without MongoDB internal fields, so that the frontend can serialize and display them without errors.

#### Acceptance Criteria

1. WHEN `add_saved_place` inserts a document into MongoDB, THE System SHALL remove the `_id` field from the document before returning it as JSON
2. WHEN `add_campus_resource` inserts a document into MongoDB, THE System SHALL remove the `_id` field from the document before returning it as JSON
3. THE System SHALL provide a `sanitize_mongo_doc` utility function that removes `_id` from any dictionary while preserving all other key-value pairs

### Requirement 2: Intelligent Travel Route Comparison

**User Story:** As a college student, I want to compare travel options between any two Indian locations with realistic pricing, so that I can choose the most cost-effective transport mode.

#### Acceptance Criteria

1. WHEN a user submits source and destination via `POST /discover/routes`, THE Travel_Service SHALL return a list of transport mode options with cost (₹), duration, distance, eco-friendly flag, and safety flag
2. THE Travel_Service SHALL accept free-text source and destination strings representing any Indian location (cities, localities, landmarks, campus buildings)
3. WHEN a cached result exists for the same normalized source and destination within 24 hours, THE Travel_Service SHALL return the cached result without querying the LLM
4. WHEN no cache exists, THE Travel_Service SHALL query the LLM for realistic Indian transport pricing between the given locations
5. IF the LLM response is unavailable or returns invalid JSON, THEN THE Travel_Service SHALL fall back to the deterministic Fare_Formula
6. THE Fare_Formula SHALL compute costs using these rates: Auto (₹25 base + ₹15/km), Bus (₹7/km), Metro (₹10 base + ₹3/km capped at ₹60), Ola/Uber (₹50 base + ₹10/km), Cycle Rickshaw (₹20 base + ₹10/km for distance < 5km only), Walk (₹0 for distance < 3km only)
7. IF the source or destination is empty or whitespace-only, THEN THE System SHALL return HTTP 400 with error message "Source and destination required"
8. WHEN a valid route result is computed, THE Travel_Service SHALL cache it in Route_Cache with a 24-hour TTL
9. THE existing `GET /discover/travel` endpoint SHALL remain functional as a legacy fallback returning mock data

### Requirement 3: AI-Powered Food Recommendations

**User Story:** As a college student, I want personalized food recommendations from real restaurants near my campus, so that I can find affordable meals that match my dietary preferences and budget.

#### Acceptance Criteria

1. WHEN a user requests `GET /discover/food`, THE Food_Service SHALL query the LLM for real restaurant and eatery suggestions near the user's college location
2. THE Food_Service SHALL include user context in the LLM prompt: dietary preference, budget per meal, preferred cuisines, college/city location, and current time of day
3. THE Food_Service SHALL return only recommendations where price is within the user's budget_per_meal
4. THE Food_Service SHALL return only recommendations matching the user's dietary preference (veg users see only veg/vegan; vegan users see only vegan; non-veg and any users see all)
5. WHEN a cached result exists for the same user + time_of_day + dietary combination within 6 hours, THE Food_Service SHALL return the cached result without querying the LLM
6. IF the LLM is unavailable or returns invalid data, THEN THE Food_Service SHALL return an empty list with an error field containing a descriptive message
7. THE Food_Service SHALL NOT use any hardcoded food data as a fallback
8. WHEN the Food_Service returns an error response, THE response SHALL have the shape `{"items": [], "error": "<message>"}`
9. WHEN the Food_Service returns successful recommendations, THE response SHALL have the shape `{"items": [...], "error": null}`

### Requirement 4: Dynamic Campus Resources

**User Story:** As a college student, I want campus resources to be stored in the database and configurable, so that I can add my own college's specific resources and they persist across sessions.

#### Acceptance Criteria

1. THE Campus_Service SHALL store campus resources in MongoDB per user
2. WHEN a user first accesses campus resources and has none stored, THE Campus_Service SHALL seed default resources appropriate for Indian colleges (counseling center, library, health center, food pantry, financial aid, peer tutoring)
3. WHEN `add_campus_resource` inserts a document, THE Campus_Service SHALL remove the `_id` field before returning the response
4. THE Campus_Service SHALL support CRUD operations: list (GET), create (POST), delete (DELETE) on campus resources

### Requirement 5: Frontend Updates

**User Story:** As a user, I want to type any source and destination for travel comparison and see AI-generated food recommendations with proper loading and error states, so that I have a smooth and informative experience.

#### Acceptance Criteria

1. WHEN the Travel tab loads, THE Frontend SHALL display two free-text input fields for source and destination instead of dropdown selects
2. WHEN the user submits source and destination, THE Frontend SHALL send a `POST /discover/routes` request with `{from, to}` payload
3. WHILE the Travel route request is in progress, THE Frontend SHALL display a loading indicator
4. IF the Travel route request fails, THEN THE Frontend SHALL display an error message and allow retry
5. WHEN the Food tab loads, THE Frontend SHALL call `GET /discover/food` and handle the new response format `{"items": [...], "error": ...}`
6. IF the food response contains a non-null `error` field, THEN THE Frontend SHALL display the error message and a "Try Again" retry button
7. WHILE the Food request is in progress, THE Frontend SHALL display a loading indicator
8. WHEN food recommendations are successfully received, THE Frontend SHALL display food cards with name, price, rating, distance, tag, dietary info, and AI-generated reason
