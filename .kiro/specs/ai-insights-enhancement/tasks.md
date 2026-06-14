# Implementation Plan: AI Insights Enhancement

## Overview

Transform PocketBuddy's Weekly Review, Daily Insights, and Helper Buddy Command Center from hardcoded/template-driven outputs into AI-powered, data-grounded features. Implementation creates `backend/insights_service.py` with three service classes (`WeeklyReviewService`, `DailyInsightsService`, `CommandCenterService`) plus shared utilities, then wires them into existing `server.py` endpoints.

## Tasks

- [ ] 1. Create shared utilities and WeeklyReviewService foundation
  - [ ] 1.1 Create `backend/insights_service.py` with shared utilities
    - Create the file with imports (asyncio, datetime, json, logging, LlmChat from emergentintegrations)
    - Implement `_call_llm_with_timeout(system_prompt, user_prompt, timeout_seconds, temperature, max_tokens)` using `asyncio.wait_for` wrapping LlmChat
    - Implement `_validate_grounding(text, context)` that checks generated text contains at least one numeric value present in context data
    - Implement `_get_iso_week(dt)` returning ISO week string like '2025-W03'
    - _Requirements: 9.4, 9.5, 11.1, 11.2, 11.3, 11.4_

  - [ ] 1.2 Implement `WeeklyReviewService` core: scores and trends
    - Create `WeeklyReviewService` class with `__init__(self, db)` constructor
    - Implement `_compute_scores(context)` mapping `financial_health_score` → Finance, `wellness_composite_score` → Wellness, `habit_consistency_percentage` → Productivity; return null for unavailable domains
    - Implement `_compute_trends(user_id, current_scores)` that looks up previous week's stored scores from `weekly_scores` collection and computes signed differences; return null if previous data_days < 3
    - Implement `_store_weekly_scores(user_id, iso_week, scores)` persisting scores for future trend computation
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

  - [ ] 1.3 Implement `WeeklyReviewService` LLM features: highlights, focus, and caching
    - Implement `_generate_highlights(context)` calling LLM with 5s timeout for 3 concise highlights referencing specific data; validate grounding
    - Implement `_fallback_highlights(context)` producing exactly 3 rule-based strings ≤80 chars each with numeric references from raw_data
    - Implement `_generate_focus(scores, trends, context)` calling LLM with 5s timeout for 1 actionable focus statement ≤120 chars
    - Implement `_fallback_focus(scores, trends)` using lowest-scoring domain template
    - Implement `_get_cached_review(user_id, iso_week)` and `_cache_review(user_id, iso_week, review)` using `weekly_insights` collection
    - Implement `invalidate_cache(user_id)` deleting cached weekly review for current ISO week
    - Implement `get_weekly_review(user_id)` as the main entry point orchestrating: cache check → context assembly → scores → trends → highlights → focus → cache store; handle insufficient data (data_days < 3)
    - Return `data_sufficiency` field: "full", "partial", or "insufficient"
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.4, 10.1, 10.4, 11.1_

- [ ] 2. Wire WeeklyReviewService into server.py
  - [ ] 2.1 Update `GET /insights/weekly` endpoint in `server.py`
    - Import `WeeklyReviewService` from `insights_service`
    - Instantiate service with `db` and call `get_weekly_review(user_id)`
    - Replace current hardcoded response with service result
    - Add overall 8s timeout using `asyncio.wait_for` at endpoint level with fallback
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1, 11.1_

  - [ ] 2.2 Add cache invalidation hooks to data-write endpoints
    - In `create_expense`, `create_mood`, `create_task`, and `update_task` endpoints: after successful write, call `WeeklyReviewService.invalidate_cache(user_id)`
    - Keep invalidation fire-and-forget (don't await blocking the response)
    - _Requirements: 6.4_

- [ ] 3. Checkpoint - Verify weekly review works end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement DailyInsightsService
  - [ ] 4.1 Add `DailyInsightsService` class to `insights_service.py`
    - Create class with `__init__(self, db)` constructor
    - Implement `_generate_llm_insights(context)` calling LLM with 3s timeout for conversational title + detail per domain referencing specific data points (₹ amounts, percentages, hours); validate grounding on each card
    - Implement `_fallback_insights(context)` preserving the existing rule-based logic from `_generate_daily_insights` in server.py
    - Implement `_onboarding_insights()` returning 3 generic cards prompting user to log data when data_days < 1
    - Implement `get_daily_insights(user_id)` orchestrating: existing daily cache check → context assembly → LLM generation or fallback → cache store; include `data_sufficiency` field ("full", "partial", "onboarding")
    - Each InsightCard must contain: domain, title, detail, icon, data_reference
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.3, 9.2, 10.2, 10.4, 11.2_

  - [ ] 4.2 Update `GET /insights/daily` endpoint in `server.py`
    - Import `DailyInsightsService` from `insights_service`
    - Replace current `daily_insights` endpoint body to use `DailyInsightsService.get_daily_insights(user_id)`
    - Keep the existing `_generate_daily_insights` function as the fallback path (called by `_fallback_insights`)
    - Add overall 5s timeout at endpoint level with fallback
    - _Requirements: 5.1, 5.3, 11.2_

- [ ] 5. Checkpoint - Verify daily insights enhancement works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement CommandCenterService and briefing endpoint
  - [ ] 6.1 Add `CommandCenterService` class to `insights_service.py`
    - Create class with `__init__(self, db)` constructor
    - Implement `_generate_llm_briefing(context)` calling LLM with 5s timeout for structured briefing (summary, up to 3 actions spanning 2+ domains, cross-domain nudge); parse LLM JSON response
    - Implement `_fallback_briefing(context)` constructing briefing from lowest-scoring domain + active_stressors
    - Implement `_validate_nudge(nudge, context)` ensuring nudge names 2 domains and contains numeric value; ≤150 chars
    - Implement `get_briefing(user_id)` orchestrating: cache check (daily_briefings collection) → context assembly → LLM generation → nudge validation → cache store; omit nudge when sufficient_data is false
    - Return `data_sufficiency` field and structured response with summary, actions array, and nudge (or null)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3, 8.4, 9.3, 10.3, 10.4, 11.3_

  - [ ] 6.2 Add `GET /insights/briefing` endpoint to `server.py`
    - Import `CommandCenterService` from `insights_service`
    - Add new route `@api_router.get("/insights/briefing")` with user authentication
    - Instantiate service with `db` and call `get_briefing(user_id)`
    - Add overall 6s timeout at endpoint level with fallback
    - _Requirements: 7.1, 7.4, 11.3_

- [ ] 7. Final checkpoint - Full integration verification
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 8. Property-based tests
  - [ ]* 8.1 Write property test for score mapping (Property 1)
    - **Property 1: Score Mapping Produces Valid Domain Scores**
    - Use Hypothesis to generate random contexts with scores 0–100 and random unavailable_domains subsets
    - Assert: each available domain maps to correct source score as int in [0, 100]; unavailable domains map to null
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [ ]* 8.2 Write property test for trend computation (Property 2)
    - **Property 2: Trend Computation Correctness**
    - Use Hypothesis to generate random score pairs (0–100) and random data_days (0–7)
    - Assert: trend equals current_score - previous_score as signed int; null when previous data_days < 3
    - **Validates: Requirements 2.2, 2.3, 2.4**

  - [ ]* 8.3 Write property test for grounding validation (Property 3)
    - **Property 3: Grounding Validation Identifies Numeric References**
    - Use Hypothesis to generate random text with embedded numbers and random context dicts
    - Assert: returns true iff text contains at least one numeric value from context
    - **Validates: Requirements 3.2, 9.4**

  - [ ]* 8.4 Write property test for fallback highlights (Property 4)
    - **Property 4: Fallback Highlights Invariant**
    - Use Hypothesis to generate random assembled contexts with varying raw_data
    - Assert: produces exactly 3 strings, each ≤80 chars, each with at least one numeric reference from context
    - **Validates: Requirements 3.3**

  - [ ]* 8.5 Write property test for focus domain selection (Property 5)
    - **Property 5: Focus Domain Selection**
    - Use Hypothesis to generate random score/trend combinations
    - Assert: selects domain with lowest score (or most negative trend on tie); fallback produces 1 string ≤120 chars
    - **Validates: Requirements 4.1, 4.3**

  - [ ]* 8.6 Write property test for daily insights structure (Property 6)
    - **Property 6: Daily Insights Structure**
    - Use Hypothesis to generate random contexts with 0–3 domains populated
    - Assert: produces exactly 3 InsightCards covering distinct domains with non-empty data_reference
    - **Validates: Requirements 5.3, 5.4**

  - [ ]* 8.7 Write property test for briefing structure (Property 7)
    - **Property 7: Briefing Structure Invariant**
    - Use Hypothesis to generate random contexts with 1–3 domains
    - Assert: summary present, actions ≤3 items, actions span ≥2 domains when 2+ domains have data
    - **Validates: Requirements 7.3, 7.4**

  - [ ]* 8.8 Write property test for nudge constraints (Property 8)
    - **Property 8: Nudge Constraints**
    - Use Hypothesis to generate random nudge strings, domain lists, sufficient_data bool
    - Assert: nudge ≤150 chars naming 2+ domains when sufficient_data=true; null when sufficient_data=false
    - **Validates: Requirements 8.2, 8.3, 8.4, 10.3**

  - [ ]* 8.9 Write property test for data sufficiency field (Property 9)
    - **Property 9: Data Sufficiency Field Invariant**
    - Use Hypothesis to generate random data_days values 0–7
    - Assert: response contains data_sufficiency from {"full", "partial", "insufficient", "onboarding"}; when data_days < 3 for weekly, value is NOT "full"
    - **Validates: Requirements 10.1, 10.4**

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design using Hypothesis
- Unit tests validate specific examples and edge cases
- The existing `_generate_daily_insights` function in server.py is preserved as fallback logic
- All services follow the established pattern: constructor takes `db`, uses `context_engine.assemble_context()`, uses `LlmChat` with Groq

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["2.1", "2.2"] },
    { "id": 4, "tasks": ["4.1"] },
    { "id": 5, "tasks": ["4.2", "6.1"] },
    { "id": 6, "tasks": ["6.2"] },
    { "id": 7, "tasks": ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9"] }
  ]
}
```
