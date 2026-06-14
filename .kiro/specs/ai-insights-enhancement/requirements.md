# Requirements Document

## Introduction

This feature transforms PocketBuddy's Weekly Review, Daily Insights, and Helper Buddy Command Center from hardcoded/template-driven outputs into fully AI-powered, data-driven features. The system will leverage the existing `context_engine.assemble_context()` infrastructure to compute real scores, calculate week-over-week trends, and use the LLM (Groq Llama 3.3 70B) to generate personalized, conversational insights grounded in actual user data.

## Glossary

- **Context_Engine**: The backend module (`context_engine.py`) that assembles 7 days of user data across all domains (mood, expenses, sleep, goals, tasks, budget) and computes composite scores.
- **Weekly_Review_Service**: The backend service responsible for computing real domain scores, week-over-week trends, and generating AI-powered weekly highlights and focus recommendations.
- **Daily_Insights_Service**: The backend service that generates personalized daily insight cards using LLM-enhanced text grounded in actual user metrics.
- **Command_Center_Service**: The backend service that produces proactive daily briefings and smart cross-domain action suggestions for the Helper Buddy.
- **LLM_Client**: The integration layer (`emergentintegrations.llm.chat.LlmChat`) used to call Groq Llama 3.3 70B for natural language generation.
- **Domain_Score**: A numeric value (0–100) representing user health in a specific life domain (Finance, Wellness, Productivity).
- **Trend**: The signed numeric difference between the current week's domain score and the previous week's domain score.
- **Insight_Card**: A structured object containing domain, title, detail text, icon, and data_reference fields displayed on the frontend.
- **Briefing**: A proactive summary of the user's current cross-domain state with actionable suggestions, delivered on login.
- **Assembled_Context**: The dictionary returned by `context_engine.assemble_context()` containing scores, raw data summaries, stressors, and correlations.

## Requirements

### Requirement 1: Compute Real Weekly Domain Scores

**User Story:** As a user, I want my Weekly Review scorecard to reflect my actual data from the past week, so that I can trust the scores represent my real progress.

#### Acceptance Criteria

1. WHEN the Weekly Review is requested, THE Weekly_Review_Service SHALL retrieve the Assembled_Context for the current 7-day period using Context_Engine.
2. WHEN the Assembled_Context is retrieved, THE Weekly_Review_Service SHALL map financial_health_score to the Finance domain, wellness_composite_score to the Wellness domain, and habit_consistency_percentage to the Productivity domain.
3. THE Weekly_Review_Service SHALL return each Domain_Score as an integer between 0 and 100 inclusive.
4. IF the Context_Engine returns unavailable_domains for a given domain, THEN THE Weekly_Review_Service SHALL return a score of null for that domain with a status indicating insufficient data.

### Requirement 2: Calculate Week-Over-Week Trends

**User Story:** As a user, I want to see how my scores changed compared to last week, so that I can understand whether I am improving or declining.

#### Acceptance Criteria

1. WHEN the Weekly Review is requested, THE Weekly_Review_Service SHALL retrieve or compute the Assembled_Context for the previous 7-day period (days 8–14 before the current date).
2. WHEN both current and previous week contexts are available, THE Weekly_Review_Service SHALL compute the Trend for each domain as (current_score minus previous_score).
3. THE Weekly_Review_Service SHALL represent each Trend as a signed integer (positive for improvement, negative for decline, zero for no change).
4. IF the previous week has insufficient data (fewer than 3 days), THEN THE Weekly_Review_Service SHALL return a Trend of null for affected domains.

### Requirement 3: Generate AI-Powered Weekly Highlights

**User Story:** As a user, I want personalized weekly highlights derived from my actual data, so that I receive meaningful recognition of my accomplishments.

#### Acceptance Criteria

1. WHEN current week scores and raw_data are available, THE Weekly_Review_Service SHALL send the Assembled_Context to the LLM_Client with a prompt requesting 3 concise highlight statements.
2. THE LLM_Client SHALL generate highlights that reference specific numbers from the user's raw_data (amounts in ₹, hours slept, tasks completed, percentages).
3. THE Weekly_Review_Service SHALL return exactly 3 highlight strings, each no longer than 80 characters.
4. IF the LLM_Client fails or times out within 5 seconds, THEN THE Weekly_Review_Service SHALL generate rule-based fallback highlights using the raw_data directly.

### Requirement 4: Generate AI-Powered Next-Week Focus

**User Story:** As a user, I want a personalized focus recommendation for next week, so that I know what to prioritize for improvement.

#### Acceptance Criteria

1. WHEN scores and Trends are computed, THE Weekly_Review_Service SHALL send the domain with the lowest score or most negative Trend to the LLM_Client for focus recommendation generation.
2. THE LLM_Client SHALL generate a single actionable focus statement that is specific, measurable, and references the user's actual data.
3. THE Weekly_Review_Service SHALL return exactly 1 focus string no longer than 120 characters.
4. IF the LLM_Client fails or times out within 5 seconds, THEN THE Weekly_Review_Service SHALL select a focus statement based on the lowest-scoring domain using a predefined template.

### Requirement 5: Enhance Daily Insights with LLM-Generated Text

**User Story:** As a user, I want richer, more conversational daily insight text that feels personalized, so that the insights are engaging and actionable.

#### Acceptance Criteria

1. WHEN generating daily insights, THE Daily_Insights_Service SHALL assemble the current context and pass domain-specific data summaries to the LLM_Client.
2. THE LLM_Client SHALL generate a conversational title and detail text for each Insight_Card that references specific data points (₹ amounts, percentages, hours).
3. THE Daily_Insights_Service SHALL return exactly 3 Insight_Cards covering finance, wellness, and productivity domains.
4. EACH Insight_Card SHALL contain a data_reference field with the raw metric value used to generate the insight text.
5. IF the LLM_Client fails or times out within 3 seconds, THEN THE Daily_Insights_Service SHALL fall back to the existing rule-based insight generation logic.

### Requirement 6: Cache Generated Insights

**User Story:** As a user, I want insights to load quickly on repeat visits, so that the app feels responsive without regenerating the same content.

#### Acceptance Criteria

1. WHEN weekly insights are generated, THE Weekly_Review_Service SHALL cache the result in MongoDB with the user_id and ISO week identifier as the key.
2. WHEN a cached weekly insight exists for the current ISO week, THE Weekly_Review_Service SHALL return the cached result without recomputing.
3. WHEN daily insights are generated, THE Daily_Insights_Service SHALL continue using the existing daily cache keyed by user_id and date string.
4. IF the user's underlying data changes (new expense, mood entry, or task completion), THE system SHALL invalidate the weekly cache for that user.

### Requirement 7: Helper Buddy Proactive Briefing Endpoint

**User Story:** As a user, I want a proactive daily briefing from Helper Buddy when I open the app, so that I immediately know what to focus on today.

#### Acceptance Criteria

1. WHEN the briefing endpoint is called, THE Command_Center_Service SHALL retrieve the Assembled_Context for the requesting user.
2. THE Command_Center_Service SHALL send the Assembled_Context (scores, stressors, correlations) to the LLM_Client with a prompt requesting a cross-domain briefing.
3. THE LLM_Client SHALL generate a briefing containing: a 1-sentence state summary, up to 3 smart action suggestions spanning at least 2 domains, and 1 cross-domain nudge connecting related patterns.
4. THE Command_Center_Service SHALL return the briefing as a structured object with fields: summary, actions (array of up to 3), and nudge.
5. IF the LLM_Client fails or times out within 5 seconds, THEN THE Command_Center_Service SHALL return a fallback briefing constructed from the lowest-scoring domain and active_stressors.

### Requirement 8: Cross-Domain Nudge Generation

**User Story:** As a user, I want Helper Buddy to connect patterns across different areas of my life, so that I gain insights I would not notice on my own.

#### Acceptance Criteria

1. WHEN the Assembled_Context contains correlations data, THE Command_Center_Service SHALL include the correlations in the LLM prompt for nudge generation.
2. THE LLM_Client SHALL generate a nudge that explicitly names two domains and describes a causal or correlational relationship using the user's data.
3. THE Command_Center_Service SHALL return the nudge as a single string no longer than 150 characters.
4. IF the Assembled_Context indicates sufficient_data is false, THEN THE Command_Center_Service SHALL omit the nudge field from the response.

### Requirement 9: Maintain Data Grounding in All AI Outputs

**User Story:** As a user, I want all AI-generated insights to be based on my actual numbers, so that I can trust the information is accurate and not fabricated.

#### Acceptance Criteria

1. THE Weekly_Review_Service SHALL include the raw_data summary in every LLM prompt so the LLM can reference actual metrics.
2. THE Daily_Insights_Service SHALL include domain-specific numeric data in every LLM prompt.
3. THE Command_Center_Service SHALL include scores, stressors, and correlations in the LLM prompt.
4. WHEN the LLM generates text, THE system SHALL validate that generated highlight and nudge strings contain at least one numeric reference that exists in the provided context data.
5. IF a generated string fails the numeric grounding validation, THEN THE system SHALL regenerate using the fallback rule-based approach.

### Requirement 10: Handle Empty or Insufficient User Data

**User Story:** As a user who is new or has limited data, I want the system to gracefully inform me rather than show misleading insights, so that I am encouraged to log more data.

#### Acceptance Criteria

1. IF the Context_Engine returns data_days fewer than 3, THEN THE Weekly_Review_Service SHALL return a response indicating insufficient data with a message encouraging the user to log more entries.
2. IF the Context_Engine returns data_days fewer than 1, THEN THE Daily_Insights_Service SHALL return generic onboarding insight cards prompting the user to start logging.
3. IF the Context_Engine returns sufficient_data as false, THEN THE Command_Center_Service SHALL omit cross-domain nudges and return only single-domain action suggestions.
4. THE system SHALL include a data_sufficiency field in all insight responses indicating whether full AI insights were generated or partial/fallback content was returned.

### Requirement 11: Response Time Constraints

**User Story:** As a user, I want insights to load within a reasonable time, so that the app feels fast and usable.

#### Acceptance Criteria

1. THE Weekly_Review_Service SHALL return a response within 8 seconds including context assembly and LLM generation.
2. THE Daily_Insights_Service SHALL return a response within 5 seconds including context assembly and LLM generation.
3. THE Command_Center_Service SHALL return a briefing response within 6 seconds including context assembly and LLM generation.
4. IF any service exceeds the time constraint, THEN THE service SHALL abort the LLM call and return the fallback response immediately.
