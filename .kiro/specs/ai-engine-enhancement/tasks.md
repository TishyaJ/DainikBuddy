# Implementation Plan: AI Engine Enhancement

## Overview

Replace the non-functional shim at `backend/emergentintegrations/llm/chat.py` with a production-ready multi-provider AI engine. Implementation proceeds bottom-up: shared types first, then provider adapters, then cross-cutting concerns (fallback, safety, cache), and finally the orchestrator that wires everything together. All internal modules live alongside `chat.py` with `_` prefixes.

## Tasks

- [x] 1. Create internal models and shared types
  - [x] 1.1 Create `backend/emergentintegrations/llm/_models.py` with shared data models
    - Define `AdapterConfig` dataclass (provider, model, api_key, temperature, top_p, max_tokens)
    - Define `UsageInfo` dataclass (prompt_tokens, completion_tokens, total_tokens)
    - Define `StreamEvent` dataclass (content, is_done, usage)
    - Define `FALLBACK_MESSAGES` dict with domain-appropriate messages for each buddy type (finance, wellness, discover, helper)
    - Define `PROVIDER_ENV_KEYS` mapping and `SUPPORTED_PROVIDERS` frozenset
    - Implement `_resolve_api_key(provider, constructor_key)` with priority: constructor > env var > EMERGENT_LLM_KEY legacy
    - Define custom `ConfigurationError` exception class
    - _Requirements: 1.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.2, 8.3, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 2. Implement provider adapters
  - [x] 2.1 Create `backend/emergentintegrations/llm/_adapters.py` with the `ProviderAdapter` protocol
    - Define `ProviderAdapter` Protocol with `stream_completion` and `format_messages` method signatures
    - _Requirements: 1.1, 12.5_

  - [x] 2.2 Implement `OpenAIAdapter` in `_adapters.py`
    - Use `openai` SDK AsyncOpenAI client
    - Implement `format_messages`: system as first role=system message, history in order, current user message last
    - Implement `stream_completion`: stream=True, yield (text_chunk, usage) tuples
    - Extract token usage from stream final chunk if available
    - _Requirements: 1.2, 2.1, 2.2, 2.4, 5.1, 5.3, 5.4, 8.4, 9.1, 12.1_

  - [x] 2.3 Implement `AnthropicAdapter` in `_adapters.py`
    - Use `anthropic` SDK AsyncAnthropic client
    - Implement `format_messages`: system as top-level param, user/assistant messages in array
    - Implement `stream_completion`: stream via messages.stream(), yield text deltas
    - Handle Anthropic's `message_start` → `content_block_delta` → `message_stop` event sequence
    - Extract token usage from message_start and message_delta events
    - _Requirements: 1.3, 2.1, 2.2, 2.4, 5.1, 5.3, 5.4, 8.4, 9.1, 12.2_

  - [x] 2.4 Implement `GeminiAdapter` in `_adapters.py`
    - Use `google-generativeai` SDK with GenerativeModel
    - Implement `format_messages`: contents array with role/parts structure, system_instruction as separate config
    - Implement `stream_completion`: generate_content_async with stream=True, yield text chunks
    - Map "assistant" role to "model" role for Gemini format
    - Handle Gemini's usage_metadata for token tracking
    - _Requirements: 1.4, 2.1, 2.2, 2.4, 5.1, 5.3, 5.4, 8.4, 8.5, 9.1, 12.3_

  - [x] 2.5 Implement `GroqAdapter` in `_adapters.py`
    - Use `groq` SDK AsyncGroq client (OpenAI-compatible interface)
    - Implement `format_messages`: same as OpenAI format (role/content objects)
    - Implement `stream_completion`: stream=True at api.groq.com endpoint, yield tuples
    - Reuse OpenAI-style message formatting logic
    - _Requirements: 1.5, 2.1, 2.2, 2.4, 5.1, 5.3, 5.4, 8.4, 9.1, 12.4_

  - [ ]* 2.6 Write property tests for provider routing and message formatting
    - **Property 1: Provider Routing Correctness** — for any supported provider name, `with_model` configures the correct adapter
    - **Property 7: Message Formatting Correctness** — for any provider, system message, history, and user message, output conforms to schema
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 5.1, 5.3, 5.4, 12.1–12.5**
    - Create `backend/tests/test_ai_engine_properties.py` with these two properties

  - [ ]* 2.7 Write property test for unsupported provider rejection
    - **Property 2: Unsupported Provider Rejection** — for any string NOT in supported set, `with_model` raises ValueError containing that string
    - **Validates: Requirements 1.6**
    - Add to `backend/tests/test_ai_engine_properties.py`

- [x] 3. Implement fallback handler
  - [x] 3.1 Create `backend/emergentintegrations/llm/_fallback.py` with retry and fallback logic
    - Define `FallbackHandler` class with `TRANSIENT_CODES`, `NON_TRANSIENT_CODES`, `MAX_RETRIES`, `INITIAL_BACKOFF`, `RATE_LIMIT_BACKOFF` constants
    - Define `FALLBACK_CHAIN` dict mapping primary providers to fallback (provider, model) tuples
    - Implement `execute_with_retry`: retry up to 2 times with exponential backoff on transient errors
    - Handle HTTP 429 with Retry-After header: wait specified duration before retry
    - Handle HTTP 429 without Retry-After: exponential backoff starting at 2 seconds
    - On all retries exhausted: attempt fallback provider via `fallback_adapter_factory`
    - On non-transient errors (400/401/403): immediately yield user-friendly error, no retry
    - Log each retry attempt and fallback activation at WARNING level
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.1, 10.2, 10.3_

  - [ ]* 3.2 Write property tests for fallback behavior
    - **Property 5: Transient Error Retry Behavior** — for any transient code, retries ≤ 2 additional times before fallback
    - **Property 6: Non-Transient Error Immediate Failure** — for any non-transient code, no retries, immediate error response
    - **Validates: Requirements 4.1, 4.5, 10.1, 10.2**
    - Add to `backend/tests/test_ai_engine_properties.py`

- [x] 4. Implement safety filter
  - [x] 4.1 Create `backend/emergentintegrations/llm/_safety.py` with content moderation
    - Define `SafetyFilter` class with compiled regex patterns for medical diagnosis and self-harm content
    - Implement `check(text)` → (is_safe, replacement_text, filter_reason) tuple
    - Medical diagnosis patterns: "you have [condition]", "you are diagnosed with", "your symptoms indicate [disease]"
    - Self-harm patterns: encouragement of self-harm, suicide methods, dangerous activities
    - Safe replacement for diagnosis: message suggesting professional consultation
    - Safe replacement for self-harm: crisis resource information (iCall, Vandrevala Foundation)
    - Log each filtered response at WARNING level with the filter reason
    - Ensure check completes within 50ms for responses under 2000 characters
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 4.2 Write property test for safety filter
    - **Property 8: Safety Filter Correctness** — for any text, filter either passes unchanged or replaces with safe alternative; never modifies clean text, always replaces matched text
    - **Validates: Requirements 6.1, 6.2, 6.3**
    - Add to `backend/tests/test_ai_engine_properties.py`

- [x] 5. Implement response cache
  - [x] 5.1 Create `backend/emergentintegrations/llm/_cache.py` with LRU+TTL caching
    - Define `ResponseCache` class using `cachetools.TTLCache`
    - Implement `_make_key`: SHA-256 hash of (provider, model, sha256(system_message), user_message)
    - Implement `get(provider, model, system_message, user_message)` → cached response or None
    - Implement `put(provider, model, system_message, user_message, response)` → store in cache
    - Default TTL: 3600 seconds (1 hour)
    - Default max size: 1000 entries with LRU eviction
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [ ]* 5.2 Write property tests for cache behavior
    - **Property 9: Cache Round-Trip with Interface Consistency** — stored response equals retrieved response
    - **Property 10: Cache LRU Eviction at Capacity** — cache never exceeds 1000 entries after overflow
    - **Validates: Requirements 7.1, 7.3, 7.4**
    - Add to `backend/tests/test_ai_engine_properties.py`

- [x] 6. Checkpoint - Core components complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Replace chat.py with the orchestrator
  - [x] 7.1 Rewrite `backend/emergentintegrations/llm/chat.py` as the LlmChat orchestrator
    - REPLACE the entire shim file (do not append)
    - Export `LlmChat`, `UserMessage`, `TextDelta`, `StreamDone` with identical class names
    - `UserMessage(text: str)`, `TextDelta(content: str)`, `StreamDone()` — same dataclass signatures
    - `LlmChat.__init__`: preserve original params (api_key, session_id, system_message), add optional (history, temperature, top_p, max_tokens, cache_enabled, buddy_type)
    - `LlmChat.with_model(provider, model)`: validate provider in SUPPORTED_PROVIDERS, raise ValueError for unsupported; select adapter class
    - `LlmChat.stream_message(message)`: orchestrate full flow — check cache → call adapter via fallback handler → apply safety filter → yield TextDelta/StreamDone → store in cache
    - `LlmChat.get_last_usage()`: return UsageInfo dict or None
    - Lazy initialization: adapter clients created on first `stream_message` call, not at import/construction time
    - On cache hit: yield TextDelta chunks from cached text + StreamDone
    - On total failure: yield buddy-type-specific fallback message from FALLBACK_MESSAGES + StreamDone
    - Default temperature=0.7, default max_tokens=1024 when not provided
    - Silently omit unsupported parameters for providers that don't accept them
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 2.4, 3.5, 3.6, 4.3, 5.1, 5.2, 5.3, 7.4, 8.1, 8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 9.3, 11.1, 16.1, 16.2, 16.4, 16.6_

  - [x] 7.2 Update `backend/emergentintegrations/llm/__init__.py` to re-export from chat.py
    - Ensure `from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone` works
    - Ensure `from emergentintegrations.llm import LlmChat, UserMessage, TextDelta, StreamDone` also works
    - _Requirements: 16.1, 16.2_

  - [ ]* 7.3 Write property tests for stream termination and fallback messages
    - **Property 3: Stream Termination Invariant** — every `stream_message` call ends with StreamDone, all prior items are TextDelta
    - **Property 4: Missing API Key Detection** — for any provider with no key set, stream_message raises ConfigurationError naming the env var
    - **Property 11: Domain-Appropriate Fallback Messages** — for each buddy type, total failure yields buddy-specific message
    - **Validates: Requirements 2.1, 2.2, 3.5, 7.4, 11.1–11.5**
    - Add to `backend/tests/test_ai_engine_properties.py`

- [x] 8. Checkpoint - Integration verification
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Write unit and integration tests
  - [x] 9.1 Create `backend/tests/test_ai_adapters.py` with adapter unit tests
    - Test each adapter's `format_messages` produces correct structure for its provider
    - Test OpenAI adapter: system as first message, history in order, user last
    - Test Anthropic adapter: system separate, messages array without system role
    - Test Gemini adapter: contents array with role/parts, "model" instead of "assistant"
    - Test Groq adapter: same as OpenAI format
    - Test default parameter values (temperature=0.7, max_tokens=1024)
    - Mock SDK clients to verify correct API calls
    - _Requirements: 8.2, 8.3, 12.1, 12.2, 12.3, 12.4_

  - [x] 9.2 Create `backend/tests/test_ai_fallback.py` with retry/fallback unit tests
    - Test retry count limits (max 2 retries = 3 total attempts)
    - Test exponential backoff timing (1s, 2s)
    - Test Retry-After header parsing and wait
    - Test fallback provider activation after primary exhaustion
    - Test non-transient error skips retry
    - Test logging of retry/fallback events
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 10.1, 10.2, 10.3_

  - [x] 9.3 Create `backend/tests/test_ai_safety.py` with safety filter unit tests
    - Test medical diagnosis pattern detection ("you have depression", "you are diagnosed with ADHD")
    - Test self-harm pattern detection
    - Test clean text passes through unchanged
    - Test replacement messages contain professional consultation suggestion or crisis resources
    - Test performance: filter completes within 50ms for 2000-char text
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 9.4 Create `backend/tests/test_ai_cache.py` with cache unit tests
    - Test cache hit returns stored response
    - Test cache miss returns None
    - Test TTL expiration (mock time advancement)
    - Test LRU eviction at max capacity
    - Test cache disabled bypasses storage and retrieval
    - Test cache key uses SHA-256 of system_message (not raw text)
    - _Requirements: 7.1, 7.2, 7.3, 7.5_

  - [x] 9.5 Create `backend/tests/test_ai_integration.py` with integration tests
    - Test full streaming flow with mocked provider SDK (TextDelta sequence + StreamDone)
    - Test `server.py` import statement works: `from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone`
    - Test server starts with missing API keys (lazy init, no crash)
    - Test token usage tracking via `get_last_usage()`
    - Test api_key constructor param overrides env var
    - Test cache integration: second identical call returns cached response
    - _Requirements: 9.1, 9.2, 9.3, 16.1, 16.2, 16.5, 17.5_

- [x] 10. Final checkpoint - All tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The design uses Python — all implementations use Python with async/await
- Property tests use `hypothesis` library (already in requirements.txt)
- All internal modules use `_` prefix convention to indicate private implementation
- The key constraint is drop-in replacement: `server.py` must work with zero changes after the engine swap
- Checkpoints ensure incremental validation at logical boundaries
- Provider SDK packages are already listed in requirements.txt — no new dependencies needed

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5"] },
    { "id": 3, "tasks": ["2.6", "2.7", "3.1", "4.1", "5.1"] },
    { "id": 4, "tasks": ["3.2", "4.2", "5.2"] },
    { "id": 5, "tasks": ["7.1"] },
    { "id": 6, "tasks": ["7.2", "7.3"] },
    { "id": 7, "tasks": ["9.1", "9.2", "9.3", "9.4", "9.5"] }
  ]
}
```
