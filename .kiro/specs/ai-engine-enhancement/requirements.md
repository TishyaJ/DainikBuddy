# Requirements Document

## Introduction

PocketBuddy's AI engine is currently non-functional — a shim module (`emergentintegrations/llm/chat.py`) returns static fallback messages instead of real AI responses. This feature replaces the shim with a production-ready multi-provider AI engine that supports OpenAI, Anthropic, Google Gemini, and Groq. The new engine must maintain the existing interface (`LlmChat`, `UserMessage`, `TextDelta`, `StreamDone`) so that the server endpoints (`/api/chat/{buddy}`, `/api/wellness/phq2`, `/api/wellness/cards`, `/api/insights/daily`) work without rewriting their calling code. It adds provider routing, streaming, fallback/retry logic, safety moderation, response caching, and per-buddy temperature configuration.

**Critical constraint:** The AI engine must integrate seamlessly with the existing system architecture — context_engine.py, conversation_memory.py, notification_service.py, analytics_service.py, and all frontend consumers — without breaking any existing functionality. All AI-powered features (chat buddies, wellness cards, daily insights, PHQ-2 AI responses, cross-domain context injection, life-balance analysis, tomorrow's plan generation) must produce fully dynamic responses grounded in real user data. Zero hardcoded or mock data in production.

## Glossary

- **AI_Engine**: The replacement module at `emergentintegrations/llm/chat.py` that provides real multi-provider LLM functionality
- **LlmChat**: The primary class consumers use to create a chat session and stream messages from an LLM provider
- **UserMessage**: A dataclass wrapping the user's text input sent to the LLM
- **TextDelta**: A dataclass wrapping an incremental chunk of text streamed back from the LLM
- **StreamDone**: A dataclass signaling that the LLM has finished streaming its response
- **Provider**: An external LLM service (OpenAI, Anthropic, Google Gemini, or Groq) that the AI_Engine routes requests to
- **Provider_Router**: The internal component that maps a provider name and model to the correct API client and credentials
- **Fallback_Handler**: The component responsible for retry logic and graceful degradation when a Provider fails
- **Safety_Filter**: The component that screens AI output for harmful, diagnostic, or inappropriate content before delivery
- **Response_Cache**: An optional caching layer that stores and retrieves LLM responses for repeated similar queries
- **Buddy**: One of the four AI personalities (finance, wellness, discover, helper) configured in BUDDY_MODELS
- **SSE**: Server-Sent Events format used by the frontend to consume streamed AI responses
- **BUDDY_MODELS**: The configuration dict mapping each Buddy to a Provider, model name, and system prompt

## Requirements

### Requirement 1: Multi-Provider LLM Client

**User Story:** As a developer, I want the AI_Engine to support multiple LLM providers through a unified interface, so that each Buddy can use the optimal model without changing server code.

#### Acceptance Criteria

1. THE AI_Engine SHALL export the classes LlmChat, UserMessage, TextDelta, and StreamDone with the same signatures as the existing shim module
2. WHEN LlmChat.with_model is called with provider "openai" and a valid model name, THE AI_Engine SHALL route the request to the OpenAI Chat Completions API
3. WHEN LlmChat.with_model is called with provider "anthropic" and a valid model name, THE AI_Engine SHALL route the request to the Anthropic Messages API
4. WHEN LlmChat.with_model is called with provider "gemini" and a valid model name, THE AI_Engine SHALL route the request to the Google Gemini GenerateContent API
5. WHEN LlmChat.with_model is called with provider "groq" and a valid model name, THE AI_Engine SHALL route the request to the Groq Chat Completions API (OpenAI-compatible endpoint at api.groq.com)
6. WHEN LlmChat.with_model is called with an unsupported provider name, THE AI_Engine SHALL raise a ValueError with a descriptive message naming the unsupported provider

### Requirement 2: Streaming Response Delivery

**User Story:** As a user, I want AI responses to appear incrementally in real-time, so that I do not wait for the full response before seeing content.

#### Acceptance Criteria

1. WHEN LlmChat.stream_message is called, THE AI_Engine SHALL yield TextDelta objects containing incremental text chunks as the Provider streams them
2. WHEN the Provider finishes streaming its response, THE AI_Engine SHALL yield a StreamDone object as the final item
3. WHILE streaming is in progress, THE AI_Engine SHALL yield each TextDelta within 100ms of receiving the corresponding chunk from the Provider
4. THE AI_Engine SHALL support async iteration over the stream_message return value using `async for`

### Requirement 3: API Key Management

**User Story:** As a developer, I want API keys managed securely via environment variables, so that credentials are not hardcoded and can be rotated without code changes.

#### Acceptance Criteria

1. THE AI_Engine SHALL read the OpenAI API key from the environment variable OPENAI_API_KEY
2. THE AI_Engine SHALL read the Anthropic API key from the environment variable ANTHROPIC_API_KEY
3. THE AI_Engine SHALL read the Google Gemini API key from the environment variable GEMINI_API_KEY
4. THE AI_Engine SHALL read the Groq API key from the environment variable GROQ_API_KEY
5. IF an API key environment variable for the requested Provider is missing or empty, THEN THE AI_Engine SHALL raise a configuration error at request time with a message identifying the missing key
6. THE AI_Engine SHALL accept an api_key parameter in the LlmChat constructor as an override that takes precedence over environment variables

### Requirement 4: Fallback and Retry Logic

**User Story:** As a user, I want AI responses to recover gracefully from provider failures, so that transient errors do not break my experience.

#### Acceptance Criteria

1. IF a Provider returns a transient error (HTTP 429, 500, 502, 503, or network timeout), THEN THE Fallback_Handler SHALL retry the request up to 2 additional times with exponential backoff starting at 1 second
2. IF all retry attempts for a Provider fail, THEN THE Fallback_Handler SHALL attempt the request using a predefined fallback Provider and model
3. IF the fallback Provider also fails, THEN THE AI_Engine SHALL yield a single TextDelta containing a user-friendly error message followed by StreamDone
4. THE Fallback_Handler SHALL log each retry attempt and fallback activation with the error details at warning level
5. IF a Provider returns a non-transient error (HTTP 400, 401, 403), THEN THE AI_Engine SHALL yield a single TextDelta containing a user-friendly error message followed by StreamDone without retrying

### Requirement 5: Conversation History Support

**User Story:** As a user, I want the AI to remember the context of our conversation, so that responses are coherent and contextual across multiple messages.

#### Acceptance Criteria

1. WHEN a system_message is provided to the LlmChat constructor, THE AI_Engine SHALL include the system_message as the system-level prompt in the API request to the Provider
2. THE LlmChat class SHALL accept a conversation history as a list of message dicts with role and content fields
3. WHEN conversation history is provided, THE AI_Engine SHALL include all history messages in the API request in chronological order before the current UserMessage
4. THE AI_Engine SHALL format conversation history according to each Provider's specific message format requirements

### Requirement 6: Safety and Moderation Layer

**User Story:** As a product owner, I want AI outputs screened for harmful content before delivery to users, so that the assistant does not provide medical diagnoses, dangerous advice, or inappropriate content.

#### Acceptance Criteria

1. WHEN the AI_Engine receives a complete response from a Provider, THE Safety_Filter SHALL check the response text against a set of blocked content patterns
2. IF the Safety_Filter detects a medical diagnosis pattern (diagnostic language claiming a user has a specific condition), THEN THE Safety_Filter SHALL replace the response with a safe alternative suggesting professional consultation
3. IF the Safety_Filter detects self-harm encouragement or dangerous activity instructions, THEN THE Safety_Filter SHALL replace the response with a safe alternative including crisis resource information
4. THE Safety_Filter SHALL complete its check within 50ms for responses under 2000 characters
5. THE Safety_Filter SHALL log each filtered response with the filter reason at warning level

### Requirement 7: Response Caching

**User Story:** As a developer, I want repeated similar queries to return cached responses, so that API costs are reduced and latency is improved for common questions.

#### Acceptance Criteria

1. WHEN a non-streaming response is requested with a query that matches a cached entry (same provider, model, system message hash, and user message within similarity threshold), THE Response_Cache SHALL return the cached response
2. THE Response_Cache SHALL store responses with a time-to-live of 1 hour by default
3. THE Response_Cache SHALL use a maximum cache size of 1000 entries, evicting least-recently-used entries when full
4. WHEN a cached response is returned, THE AI_Engine SHALL still yield TextDelta and StreamDone objects to maintain interface consistency
5. WHERE caching is disabled via configuration, THE AI_Engine SHALL bypass the Response_Cache entirely

### Requirement 8: Per-Buddy Temperature and Parameter Configuration

**User Story:** As a developer, I want each Buddy to have independently tunable generation parameters, so that Finance Buddy gives precise responses while Wellness Buddy gives warmer, more creative ones.

#### Acceptance Criteria

1. THE LlmChat class SHALL accept optional parameters for temperature, top_p, and max_tokens
2. WHEN temperature is not explicitly provided, THE AI_Engine SHALL use a default temperature of 0.7
3. WHEN max_tokens is not explicitly provided, THE AI_Engine SHALL use a default max_tokens of 1024
4. THE AI_Engine SHALL pass the configured temperature, top_p, and max_tokens to the Provider API in the appropriate format for each Provider
5. IF a Provider does not support a given parameter, THEN THE AI_Engine SHALL silently omit that parameter from the API request

### Requirement 9: Token Usage Tracking

**User Story:** As a developer, I want to track token consumption per request, so that I can monitor costs and set usage alerts.

#### Acceptance Criteria

1. WHEN a streaming response completes, THE AI_Engine SHALL record the prompt token count and completion token count if the Provider includes usage data in its response
2. THE AI_Engine SHALL expose token usage data through a get_last_usage method on the LlmChat instance returning a dict with prompt_tokens, completion_tokens, and total_tokens fields
3. IF the Provider does not return token usage information, THEN THE AI_Engine SHALL return None from get_last_usage

### Requirement 10: Rate Limiting Awareness

**User Story:** As a developer, I want the AI_Engine to handle rate limiting gracefully, so that bursts of requests do not cause cascading failures.

#### Acceptance Criteria

1. IF a Provider returns HTTP 429 (Too Many Requests) with a Retry-After header, THEN THE AI_Engine SHALL wait the duration specified in the Retry-After header before retrying
2. IF a Provider returns HTTP 429 without a Retry-After header, THEN THE AI_Engine SHALL apply exponential backoff starting at 2 seconds
3. THE AI_Engine SHALL log rate limit encounters at warning level with the Provider name and wait duration

### Requirement 11: Graceful Degradation Fallback Response

**User Story:** As a user, I want to receive a helpful response even when all AI providers are unavailable, so that the app remains usable during outages.

#### Acceptance Criteria

1. IF all Provider attempts (including retries and fallback) fail, THEN THE AI_Engine SHALL yield a TextDelta containing a domain-appropriate fallback message based on the Buddy type
2. WHEN the Buddy is "finance", THE fallback message SHALL suggest the user check their expense log or budget manually
3. WHEN the Buddy is "wellness", THE fallback message SHALL include a brief calming statement and suggest the user try a breathing exercise
4. WHEN the Buddy is "discover", THE fallback message SHALL suggest the user check campus notice boards or student portals
5. WHEN the Buddy is "helper", THE fallback message SHALL acknowledge the outage and suggest the user try again shortly

### Requirement 12: Provider-Specific Message Formatting

**User Story:** As a developer, I want the AI_Engine to handle message format differences between providers internally, so that server code uses a single consistent interface.

#### Acceptance Criteria

1. WHEN routing to OpenAI, THE Provider_Router SHALL format messages using the OpenAI chat completions message schema (role/content objects)
2. WHEN routing to Anthropic, THE Provider_Router SHALL format messages using the Anthropic messages schema (system as top-level parameter, user/assistant content blocks)
3. WHEN routing to Gemini, THE Provider_Router SHALL format messages using the Gemini generateContent schema (contents array with role/parts)
4. WHEN routing to Groq, THE Provider_Router SHALL format messages using the OpenAI-compatible chat completions schema (role/content objects) directed at the Groq API base URL
5. THE Provider_Router SHALL map the system_message, conversation history, and current UserMessage into the correct format for each Provider without requiring caller changes

### Requirement 13: Full Context Engine Integration

**User Story:** As a user, I want the AI buddies to reference my actual financial, wellness, and behavioral data in their responses, so that advice is personalized and grounded in my real situation rather than generic platitudes.

#### Acceptance Criteria

1. WHEN the chat endpoint `/api/chat/{buddy}` is called, THE server SHALL invoke `context_engine.assemble_context()` to build the user's 7-day cross-domain data summary and inject it into the system prompt sent to the AI_Engine
2. WHEN the Finance Buddy receives a message and the user's stress score exceeds 60 or sleep average is below 6.5 hours, THE server SHALL include wellness context from `context_engine.get_wellness_context_for_finance()` in the AI prompt
3. WHEN the AI_Engine generates a response for any Buddy, THE response SHALL reference at least one specific data point from the assembled user context (a ₹ amount, a sleep figure, a mood trend, or a goal status)
4. THE AI_Engine integration SHALL NOT introduce any hardcoded example data, sample budgets, or placeholder figures into AI responses; every number or data reference must originate from the user's actual database entries
5. IF the context engine returns empty or partial data for a user, THE AI_Engine SHALL instruct the Buddy to acknowledge what data is missing and encourage the user to log it rather than fabricating values

### Requirement 14: Conversation Memory Integration

**User Story:** As a user, I want the AI to remember our past conversations and build on them, so that interactions feel continuous and personal across sessions.

#### Acceptance Criteria

1. WHEN a user sends a message to a Buddy, THE server SHALL invoke `conversation_memory.get_full_context_for_chat()` to load the last 5 messages and any existing conversation summary, and include them in the prompt sent to the AI_Engine
2. WHEN the AI_Engine generates a response, THE server SHALL persist both the user message and the AI response via `conversation_memory.store_message()` so they are available for future context
3. WHEN the user's message triggers a memory reference (e.g. "remember when"), THE server SHALL search conversation history via `_search_conversation_history()` and inject matching prior exchanges into the AI prompt
4. THE AI_Engine SHALL NOT reset or lose conversation context between requests — all context management is handled by the existing `conversation_memory.py` service, and the AI_Engine must faithfully include the provided history in API calls
5. WHEN conversation history exceeds 50 messages for a buddy, THE server SHALL auto-trigger `conversation_memory.trim_and_summarize()` to compress old messages into a summary, and the AI_Engine SHALL accept and use the summarized context without degradation

### Requirement 15: Dynamic AI-Powered Feature Integration

**User Story:** As a user, I want all AI-powered features in the app (insights, wellness cards, PHQ-2 analysis, tomorrow's plan, motivation nudges) to produce real, personalized content derived from my data, so that the app feels alive and genuinely helpful.

#### Acceptance Criteria

1. WHEN `/api/insights/daily` is called, THE server SHALL generate exactly 3 AI insight cards (financial tip, wellness suggestion, productivity recommendation) by sending the user's assembled context to the AI_Engine and parsing the structured response
2. WHEN `/api/wellness/cards` is called, THE server SHALL generate AI-powered wellness cards using the AI_Engine with the user's mood, sleep, and stress data as context, producing unique personalized advice each time
3. WHEN `/api/wellness/phq2` is called with questionnaire responses, THE server SHALL send the PHQ-2 scores to the AI_Engine with a clinical guidance system prompt and return a personalized AI-generated support message
4. WHEN `/api/insights/tomorrow-plan` is called after 8 PM, THE server SHALL use the AI_Engine with the user's life-balance scores to generate 3 specific, actionable plan items ordered by lowest-scoring domain
5. WHEN `/api/life-balance` is called, THE computed scores SHALL be derived from real user data (mood entries, expenses, sleep logs, task progress, social activity) and the AI_Engine SHALL NOT be used to fabricate scores — only to generate textual interpretations
6. ALL AI-generated content displayed in the frontend (InsightCards, wellness AI cards, chat responses, daily insights, correlation alerts) SHALL be produced by the AI_Engine using real user data; the frontend SHALL NOT contain any fallback hardcoded insight text for production use

### Requirement 16: System Architecture Preservation

**User Story:** As a developer, I want the AI engine replacement to be a drop-in upgrade that preserves the existing system architecture, so that no existing endpoints, frontend flows, or data pipelines break.

#### Acceptance Criteria

1. THE AI_Engine module SHALL remain at the path `backend/emergentintegrations/llm/chat.py` and export the same class names (LlmChat, UserMessage, TextDelta, StreamDone) with identical constructor signatures and method names
2. THE server.py import statement `from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone` SHALL continue to work without modification after the engine replacement
3. THE AI_Engine SHALL NOT modify the schemas or response formats of any existing API endpoints (`/api/chat/{buddy}`, `/api/wellness/phq2`, `/api/wellness/cards`, `/api/insights/daily`, `/api/insights/tomorrow-plan`, `/api/insights/weekly`, `/api/life-balance`)
4. THE frontend SSE streaming consumption logic SHALL continue to work without changes — the AI_Engine produces TextDelta chunks that the server formats as SSE events identically to the current (shim) flow
5. THE AI_Engine SHALL NOT require changes to `context_engine.py`, `conversation_memory.py`, `notification_service.py`, `gamification_service.py`, `analytics_service.py`, `categorization_service.py`, or any other existing backend service module
6. THE AI_Engine SHALL NOT add new API endpoints — it operates purely as an internal service consumed by existing endpoint handlers in server.py

### Requirement 17: End-to-End Validation

**User Story:** As a developer, I want to verify that the AI engine works correctly across all AI-powered features with real provider calls, so that I can confirm production readiness.

#### Acceptance Criteria

1. WHEN a registered user with at least 3 days of logged data (mood, expenses, sleep) sends a chat message to any Buddy, THE response SHALL be a real AI-generated message (not a fallback) that references the user's data
2. WHEN `/api/insights/daily` is called for a user with logged data, THE response SHALL contain 3 insight objects each with a `title` and `detail` field containing AI-generated text referencing user data points
3. WHEN `/api/wellness/cards` is called for a user with mood entries, THE response SHALL contain AI-generated wellness guidance that references the user's actual stress or sleep patterns
4. WHEN the AI_Engine is called and the configured provider returns a valid response, THE end-to-end latency from frontend request to first SSE chunk SHALL be under 3 seconds
5. WHEN a provider API key is missing, THE server SHALL still start successfully and return appropriate error messages only when AI features are actually invoked (lazy initialization)
