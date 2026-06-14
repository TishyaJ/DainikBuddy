# PocketBuddy — Action Plan & Next Steps

A guide for the team on what to do next, how to use the spec system, and ready-made prompts for common workflows.

---

## Current Status (as of June 14, 2026)

### ✅ Completed — PocketBuddy AI Enhancement Spec
**Location:** `.kiro/specs/pocketbuddy-ai-enhancement/`

All 18 tasks from this spec are DONE:
- Authentication & security (JWT, bcrypt, rate limiting)
- Gamification engine (XP, levels, streaks, achievements)
- Cross-domain AI context engine
- Conversation memory & personality enforcement
- Smart notifications & nudges
- Social features (study groups, challenges, shared goals)
- Expense auto-categorization
- Analytics & trend detection
- Daily insights & life-balance radar
- Voice input (Web Speech API)
- Offline/PWA support
- UI/UX coherence pass
Find .kiro\specs\pocketbuddy-ai-enhancement folder containing specs files, Guides folder for project research reports [setup at the initial-most phase], change_log.md and diary.md for the best details about the project.
### 🔲 Next Up — AI Engine Enhancement Spec
**Location:** `.kiro/specs/ai-engine-enhancement/`

This spec replaces the current shim AI module with a production-ready multi-provider LLM engine. Currently the chat feature works through a basic wrapper — this upgrade adds:
- Multi-provider support (OpenAI, Anthropic, Gemini, Groq)
- Automatic fallback between providers
- Safety filtering (medical diagnosis, self-harm detection)
- Response caching (LRU + TTL)
- Proper streaming with token tracking

**All 10 task groups are pending.** Start from Task 1.

---

## Understanding the Spec System

### What are specs?

Specs live in `.kiro/specs/<spec-name>/` and contain three files:

| File | Purpose |
|------|---------|
| `requirements.md` | WHAT to build — user stories, acceptance criteria |
| `design.md` | HOW to build it — architecture, data models, correctness properties |
| `tasks.md` | Implementation steps — ordered, with dependencies and requirement traceability |

### How to use specs with Kiro

The tasks.md file is your implementation roadmap. Each task has:
- A checkbox `[ ]` (unchecked) or `[x]` (done)
- Bullet points describing exactly what to implement
- `_Requirements: X.X, Y.Y_` tracing back to the requirements document
- Tasks marked `*` are optional (property tests — skip for faster progress)

**The workflow:**
1. Open the tasks.md you're working on
2. Tell Kiro which task to implement (e.g., "Implement task 1.1 from the AI engine enhancement spec")
3. Kiro reads the task, reads the design.md for architecture guidance, and implements it
4. After implementation, Kiro marks the task `[x]` done
5. Move to the next task in dependency order (see the "Task Dependency Graph" at the bottom of tasks.md)

### Dependency Waves

Tasks are grouped into waves — all tasks in a wave can run in parallel, but a wave can only start after the previous wave completes:

```
Wave 0: Task 1.1 (shared models)
Wave 1: Task 2.1 (adapter protocol)
Wave 2: Tasks 2.2, 2.3, 2.4, 2.5 (all 4 provider adapters — can be parallel)
Wave 3: Tasks 3.1, 4.1, 5.1 (fallback, safety, cache — independent of each other)
Wave 4: Property tests (optional)
Wave 5: Task 7.1 (orchestrator — needs everything above)
Wave 6: Task 7.2, 7.3 (exports + tests)
Wave 7: Tasks 9.1–9.5 (unit + integration tests)
```

---

## Key Folders & Files Reference

| Path | What it is |
|------|-----------|
| `.kiro/specs/ai-engine-enhancement/tasks.md` | **Your next task list** — start implementing from here |
| `.kiro/specs/ai-engine-enhancement/design.md` | Architecture reference for AI engine (read before implementing) |
| `.kiro/specs/ai-engine-enhancement/requirements.md` | Acceptance criteria to validate against |
| `backend/emergentintegrations/llm/chat.py` | The file being replaced (current shim) |
| `backend/emergentintegrations/llm/` | Where all new AI engine modules go (`_models.py`, `_adapters.py`, etc.) |
| `backend/server.py` | Main app — imports from `emergentintegrations.llm.chat` (must keep working) |
| `backend/tests/` | Where new test files go |
| `backend/requirements.txt` | Python deps (all AI SDKs already listed) |
| `change_log.md` | Session log — update after every work session |
| `diary.md` | Architecture reasoning — update after every work session |
| `REPRODUCIBILITY.md` | Setup guide for new team members |

---

## Ready-Made Prompts for Common Workflows

Copy-paste these into the chat when you need them:
Note: Use #<files/folders> to give the context on the chat for reducing hallucination [for kiro, # is used, for antigravity @ is used]


### Starting a New Task

```
Implement task 1.1 from the ai-engine-enhancement spec. 
Read the design.md for architecture guidance and requirements.md for acceptance criteria.
Mark the task [x] when complete and run the tests.
```
^--- if automatic click on tasks don't work.

```
Continue with the next task in the ai-engine-enhancement spec.
Check the dependency graph — pick the next available task from the earliest incomplete wave.
```

### Reporting Issues Found During Testing

```
I was running the servers and checking the app from dev tools. I found these issues:
1. [describe what you saw]
2. [paste any console errors]
3. [describe expected vs actual behavior]

Please fix these issues and verify the fix works by curl test or invoke-web-requests test or powershell tests for prompting to both backend and frontend servers that are running on #terminal.
```

```
I was evaluating the FastAPI deployment via Swagger UI (/docs). I found these issues:
- Endpoint: [which endpoint]
- Request: [what you sent]
- Expected: [what should happen]
- Actual: [what actually happened / error code / response body]

Please investigate and fix.
```

```
Please find the attached terminal output. [paste or attach the output]
Diagnose what went wrong and fix it.
```

### After Completing Work (Logging)

```
Log all the latest changes to change_log.md and the story behind the developments, 
issues, resolvements, completion of those latest changes as diary of agent on diary.md.
```

### Running the Checkpoint

```
Run all backend tests (python -m pytest tests/ -v) and verify the frontend builds 
(npm run build in frontend/). Report results. If anything fails, fix it.
```

### Understanding Existing Code Before Changing It

```
Before making changes, read backend/emergentintegrations/llm/chat.py and 
backend/server.py's chat endpoint to understand how LlmChat is currently used.
I need the new engine to be a drop-in replacement.
```

### Debugging Connection Issues

```
The backend server is throwing connection errors when I try to start it.
Here's what I see in the terminal: [paste output]
Please diagnose and fix — check .env file, MongoDB connection, and dependencies.
```

### Verifying the AI Chat Works End-to-End

```
Test the AI chat flow end-to-end:
1. Start the backend server
2. Call POST /api/chat/finance with a test message
3. Verify it streams a real AI response (not a fallback message)
4. Check that conversation memory stores the message
5. Report results
```

### Adding a New Feature (Outside of Spec)

```
I want to add [describe feature]. Before implementing:
1. Check if it conflicts with any existing architecture
2. Identify which files need changes
3. Propose an approach
4. Implement after I approve

Then log the changes to change_log.md and diary.md.
```

---

## Next Steps — Prioritized Task List

### Priority 1: AI Engine Enhancement (the spec)

This is the main next development task. The current AI chat uses a shim that doesn't produce real responses. After this spec, all 4 AI buddies will respond with real LLM output.

**Start with:**
```
Implement task 1.1 from the ai-engine-enhancement spec.
```
Or go to tasks.md of ai-engine-enhancement folder and click on tasks to be executed by you.

**Then work through waves** (see dependency graph in tasks.md):
- Wave 0: Shared models → Wave 1: Protocol → Wave 2: Four adapters → Wave 3: Fallback + Safety + Cache → Wave 5: Orchestrator → Wave 7: Tests

**Expected time:** 3-5 sessions depending on depth of testing.

### Priority 2: Live Testing & Bug Fixes

After the AI engine is implemented, test the full flow:
- Register a new user
- Log moods, expenses, journal entries
- Chat with each AI buddy (verify real responses)
- Check daily insights (should now be AI-generated, not template)
- Test offline mode, notifications, social features

Use the reporting prompts above to file any issues found.

### Priority 3: Deployment Preparation

Once everything works locally:
- Set up production environment variables
- Choose hosting (Railway/Render for backend, Vercel/Netlify for frontend)
- Configure MongoDB Atlas for production (dedicated cluster or upgrade free tier)
- Test with production API keys

---

## Tips for Working with Kiro on This Project

1. **Always reference the spec** when asking for implementation work. Say "from the ai-engine-enhancement spec" so Kiro knows which tasks.md to follow.

2. **One task at a time** produces better results than "implement everything." Each task is designed to be a single coherent unit.

3. **Ask Kiro to read before writing.** If unsure about existing architecture: "Read context_engine.py and explain how it works before making changes."

4. **Run tests after every task.** Either ask Kiro to run them or do it yourself in the terminal:
   ```bash
   cd backend
   venv\Scripts\activate
   python -m pytest tests/ -v
   ```

5. **Keep the logs updated.** After every session, paste the logging prompt. The change_log and diary are invaluable for understanding what happened and why.

6. **Don't be afraid to paste errors.** Terminal output, browser console errors, network tab screenshots — the more context you give, the faster the fix.

7. **Skip optional tasks (marked `*`) for now.** Property tests are nice-to-have but not blocking. Get the core working first, add test coverage later.

---

## Environment Quick-Check

Before starting any work session, verify:

```bash
# Backend runs?
cd backend
venv\Scripts\activate
uvicorn server:app --reload --port 8000
# Should see "Application startup complete"

# Frontend runs?
cd frontend
npm start
# Should open http://localhost:3000

# Tests pass?
cd backend
python -m pytest tests/ -v
# Should see "185 passed"
```

If any of these fail, debug FIRST before starting new feature work. See `REPRODUCIBILITY.md` for troubleshooting.
