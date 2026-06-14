# PocketBuddy — Reproducibility Guide

A complete guide to set up, run, and verify the PocketBuddy workspace from scratch. Written for someone new to full-stack development.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone the Repository](#clone-the-repository)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Running Both Servers](#running-both-servers)
6. [Verifying Everything Works](#verifying-everything-works)
7. [Environment Variable Reference](#environment-variable-reference)
8. [Common Errors & Fixes](#common-errors--fixes)
9. [Development Workflow](#development-workflow)
10. [Warnings & Guidelines](#warnings--guidelines)
11. [Architecture Quick Reference](#architecture-quick-reference)

---

## Prerequisites

You need these installed on your machine BEFORE starting:

### 1. Python 3.10 or higher

Download from https://www.python.org/downloads/

During installation:
- ✅ CHECK "Add Python to PATH" (this is critical!)
- ✅ CHECK "Install pip"

Verify after install:
```bash
python --version
# Should show: Python 3.10.x or higher

pip --version
# Should show: pip 23.x or higher
```

> ⚠️ On Windows, if `python` doesn't work, try `py` instead. Both should work if you checked "Add to PATH."

### 2. Node.js 18 or higher (20 LTS recommended)

Download from https://nodejs.org/ — pick the "LTS" version.

Verify after install:
```bash
node --version
# Should show: v18.x.x or higher (v20.x.x recommended)

npm --version
# Should show: 9.x.x or higher
```

### 3. Git

Download from https://git-scm.com/downloads

Verify:
```bash
git --version
# Should show: git version 2.x.x
```

### 4. MongoDB Atlas Account

You need a cloud MongoDB database. Options:
- **MongoDB Atlas** (free tier): https://www.mongodb.com/cloud/atlas/register
- Or a local MongoDB installation (advanced — not recommended for beginners)

If using Atlas:
1. Create a free cluster
2. Create a database user (remember the username and password!)
3. Whitelist your IP (or use `0.0.0.0/0` for "allow from anywhere")
4. Get your connection string (it looks like: `mongodb+srv://username:password@cluster-name.xxxxx.mongodb.net/`)

### 5. At Least ONE AI API Key

The app needs an LLM API for the chat feature. Get at least one:
- **OpenAI**: https://platform.openai.com/api-keys (most reliable)
- **Groq**: https://console.groq.com/keys (free tier, fast)
- **Anthropic**: https://console.anthropic.com/
- **Google Gemini**: https://makersuite.google.com/app/apikey

---

## Clone the Repository

```bash
git clone <your-repo-url> PocketBuddy
cd PocketBuddy
```

You should now see:
```
PocketBuddy/
├── backend/
├── frontend/
├── README.md
├── REPRODUCIBILITY.md   ← you are reading this
└── ...
```

---

## Backend Setup

### Step 1: Create Virtual Environment

```bash
cd backend
python -m venv venv
```

This creates a `venv/` folder. This is an isolated Python environment so our packages don't conflict with your system Python.

> ⚠️ **NEVER delete the `venv/` folder** while the server is running. If something goes wrong with venv, stop the server first, delete venv, and recreate it.

### Step 2: Activate the Virtual Environment

**This step is REQUIRED every time you open a new terminal to work on the backend.**

```bash
# Windows CMD:
venv\Scripts\activate

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Mac/Linux:
source venv/bin/activate
```

You'll know it worked when you see `(venv)` at the start of your terminal prompt:
```
(venv) D:\HACKON\PocketBuddy\backend>
```

> ⚠️ If you see `(venv)` → you're good. If you DON'T see it → activate again. Running commands without activation will use system Python and fail.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs ~40 packages. Should take 1-3 minutes. If you see red errors about "Microsoft Visual C++ required," install the Visual Studio Build Tools from https://visualstudio.microsoft.com/visual-cpp-build-tools/

Verify:
```bash
python -c "import fastapi; import motor; import bcrypt; print('All good!')"
# Should print: All good!
```

### Step 4: Create the .env File

Copy the example:
```bash
copy .env.example .env
```

Now open `backend/.env` in your editor and fill in REAL values:

```env
MONGO_URL=mongodb+srv://YOUR_USERNAME:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?appName=pocketbuddy&tls=true&tlsAllowInvalidCertificates=true
DB_NAME=pocketbuddy
JWT_SECRET=make-up-any-random-string-here-at-least-32-characters
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Put your API key here (at least one):
EMERGENT_LLM_KEY=sk-your-openai-key-here
OPENAI_API_KEY=sk-your-openai-key-here
```

#### ⚠️⚠️⚠️ CRITICAL: MongoDB Password Encoding ⚠️⚠️⚠️

This is the #1 cause of "it doesn't work" issues. If your MongoDB password has ANY of these characters, you MUST encode them:

| Character in password | Replace with |
|----------------------|--------------|
| `@` | `%40` |
| `#` | `%23` |
| `%` | `%25` |
| `/` | `%2F` |
| `:` | `%3A` |
| `+` | `%2B` |
| space | `%20` |

**Example:**
- Password is `Cool@Pass#1`
- In .env it becomes: `mongodb+srv://myuser:Cool%40Pass%231@cluster.mongodb.net/...`

**Also:** MongoDB Atlas shows `<password>` as a placeholder. Replace the ENTIRE thing including `<` and `>`. Do NOT keep the angle brackets.

```
# ❌ WRONG:
MONGO_URL=mongodb+srv://test:<MyPassword>@cluster.mongodb.net/

# ✅ CORRECT:
MONGO_URL=mongodb+srv://test:MyPassword@cluster.mongodb.net/
```

### Step 5: Start the Backend Server

```bash
uvicorn server:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to stop)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Verify by opening http://localhost:8000/docs in your browser — you should see the Swagger API documentation page.

> ⚠️ **Keep this terminal open!** The backend runs in this terminal. Open a NEW terminal for the frontend.

---

## Frontend Setup

Open a **NEW terminal window** (don't close the backend one!).

### Step 1: Navigate to Frontend

```bash
cd frontend
```

(Or if you're in the project root: `cd frontend`)

### Step 2: Install Dependencies

```bash
npm install --legacy-peer-deps
```

> ⚠️⚠️⚠️ **YOU MUST USE `--legacy-peer-deps`** ⚠️⚠️⚠️
>
> Without it, npm will show errors about peer dependency conflicts and refuse to install. This is because the project uses React 19 and some packages haven't updated their peer dependency declarations yet.
>
> ```bash
> # ✅ This works:
> npm install --legacy-peer-deps
>
> # ❌ This will FAIL:
> npm install
> ```

Installation takes 2-5 minutes. You'll see some deprecation warnings — these are fine, ignore them.

### Step 3: Create .env (if not present)

Check if `frontend/.env` exists. If not, create it:

```bash
echo REACT_APP_BACKEND_URL=http://localhost:8000 > .env
```

Or manually create the file with this content:
```env
REACT_APP_BACKEND_URL=http://localhost:8000
```

### Step 4: Start the Frontend Dev Server

```bash
npm start
```

This will:
1. Compile the app (takes 10-30 seconds first time)
2. Open http://localhost:3000 in your default browser
3. Show the PocketBuddy login page

> ⚠️ If port 3000 is already in use, it'll ask "Would you like to run on another port?" — say yes. It'll use 3001. Make sure your backend's `CORS_ORIGINS` includes that port.

---

## Running Both Servers

You need TWO terminal windows running simultaneously:

| Terminal | Directory | Command | URL |
|----------|-----------|---------|-----|
| Terminal 1 | `backend/` | `venv\Scripts\activate` then `uvicorn server:app --reload --port 8000` | http://localhost:8000 |
| Terminal 2 | `frontend/` | `npm start` | http://localhost:3000 |

**Both must be running for the app to work.** The frontend calls the backend API — if the backend is down, you'll see blank pages or error messages.

### Starting Up (Daily Workflow)

Every time you sit down to work:

```bash
# Terminal 1 — Backend
cd backend
venv\Scripts\activate
uvicorn server:app --reload --port 8000

# Terminal 2 — Frontend (new window!)
cd frontend
npm start
```

### Shutting Down

- Press `Ctrl+C` in each terminal to stop the servers
- Close the terminals

---

## Verifying Everything Works

After both servers are running, do these checks:

### Check 1: Backend is alive

Open http://localhost:8000/docs in your browser. You should see the Swagger UI with all the API endpoints listed.

### Check 2: Frontend is alive

Open http://localhost:3000. You should see the login page.

### Check 3: Backend-Frontend connection

1. On the login page, click "Register" to go to the registration page
2. Enter any email (e.g., `test@test.com`) and a password (must be 8+ chars, 1 uppercase, 1 number)
3. Click Register
4. If it succeeds → you'll be redirected to onboarding. **The full stack is working!**
5. If it fails with a network error → the backend isn't reachable from the frontend. Check that both are running and the `.env` URL is correct.

### Check 4: Database connection (from terminal)

In the backend terminal (with venv activated):
```bash
python fix_auth.py --list
```

If it prints `Found 0 users` or lists users → MongoDB connection is working.
If it shows a timeout error → your MONGO_URL is wrong (see the encoding section above).

### Check 5: API endpoint test (optional)

In a new terminal (or use your browser's dev tools):

```bash
# Windows PowerShell:
Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET | Select-Object StatusCode
# Should show: 200
```

Or just open http://localhost:8000/docs in your browser.

---

## Environment Variable Reference

### Backend (`backend/.env`)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `MONGO_URL` | ✅ YES | `mongodb+srv://user:pass@cluster.mongodb.net/?appName=pocketbuddy&tls=true&tlsAllowInvalidCertificates=true` | MongoDB connection string. MUST be URL-encoded if password has special chars |
| `DB_NAME` | ✅ YES | `pocketbuddy` | Database name in MongoDB |
| `JWT_SECRET` | ✅ YES | `my-super-secret-key-at-least-32-chars` | Secret for signing JWT tokens. Any random string 32+ chars |
| `CORS_ORIGINS` | ✅ YES | `http://localhost:3000,http://localhost:3001` | Comma-separated frontend URLs allowed to call the API |
| `EMERGENT_LLM_KEY` | ⚡ For chat | `sk-...` | OpenAI API key (legacy name, still works) |
| `OPENAI_API_KEY` | ⚡ For chat | `sk-...` | OpenAI API key |
| `ANTHROPIC_API_KEY` | ⚡ For chat | `sk-ant-...` | Anthropic Claude API key |
| `GEMINI_API_KEY` | ⚡ For chat | `AI...` | Google Gemini API key |
| `GROQ_API_KEY` | ⚡ For chat | `gsk_...` | Groq API key (free tier available) |

> ⚡ = At least ONE AI key is needed for the chat feature to work. Everything else works without AI keys.

### Frontend (`frontend/.env`)

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `REACT_APP_BACKEND_URL` | ✅ YES | `http://localhost:8000` | Backend API URL (no trailing slash!) |

---

## Common Errors & Fixes

### Backend Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'fastapi'` | Venv not activated | Run `venv\Scripts\activate` first |
| `ModuleNotFoundError: No module named 'bcrypt'` | Venv not activated OR packages not installed | Activate venv, then `pip install -r requirements.txt` |
| `KeyError: 'MONGO_URL'` | Missing .env file or missing variable | Create `backend/.env` with all required variables |
| `KeyError: 'DB_NAME'` | Missing DB_NAME in .env | Add `DB_NAME=pocketbuddy` to your .env |
| `ServerSelectionTimeoutError` | Can't connect to MongoDB | Check MONGO_URL encoding, check internet, check Atlas IP whitelist |
| `[Errno 11001] getaddrinfo failed` | DNS resolution failure (transient) | Check internet connection, restart server |
| `OperationFailure: Authentication failed` | Wrong MongoDB username/password | Double-check credentials in Atlas, re-encode password |
| `ImportError: cannot import name '_QUERY_OPTIONS'` | motor/pymongo version mismatch | `pip install motor==3.7.1` |
| `Address already in use (port 8000)` | Another process on port 8000 | Kill it: `taskkill /F /PID <pid>` or use `--port 8001` |
| `jwt.exceptions.DecodeError` | JWT_SECRET changed between sessions | Users must re-login (old tokens are invalid with new secret) |

### Frontend Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `npm ERR! ERESOLVE could not resolve` | Forgot `--legacy-peer-deps` | Run `npm install --legacy-peer-deps` |
| `npm ERR! peer dep missing` | Same as above | Same fix: `--legacy-peer-deps` |
| Blank page (no errors in console) | Backend not running | Start the backend server |
| Network Error on login/register | Backend URL wrong or backend down | Check `frontend/.env` has correct URL, check backend is running |
| `401 Unauthorized` on every request | Token expired or invalid | Log out and log back in |
| Port 3000 already in use | Another dev server running | Close it or accept port 3001 |
| `craco: command not found` | Using `npx craco` without install | Use `npm start` (which calls craco internally) |
| Build warnings about unused variables | Non-critical ESLint warnings | Safe to ignore for development |

### Database Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Registration says "Account exists" but login fails | Database has corrupted user entry | Run `python fix_auth.py --delete test@test.com` then register again |
| Everything was working, now timeouts | MongoDB Atlas paused free cluster (after 7 days idle) | Log into Atlas, resume the cluster |
| "IP not whitelisted" | Atlas Network Access restriction | Go to Atlas → Network Access → Add your current IP (or 0.0.0.0/0 for dev) |

---

## Development Workflow

### Making Changes

1. **Backend changes**: The `--reload` flag in uvicorn auto-restarts on file save. Just save your file and the server restarts automatically.
2. **Frontend changes**: React hot-reloads on file save. Just save and the browser updates.

### Running Tests

```bash
# Backend (make sure venv is activated!)
cd backend
venv\Scripts\activate
python -m pytest tests/ -v

# Frontend build check
cd frontend
npm run build
```

### Before Committing

1. Ensure backend tests pass: `python -m pytest tests/ -v`
2. Ensure frontend builds: `npm run build` (in frontend/)
3. Don't commit `.env` files (they're in .gitignore)
4. Don't commit `node_modules/` or `venv/` (also in .gitignore)

### Git Workflow

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make changes, then:
git add <specific-files>
git commit -m "feat: description of what you added"
git push -u origin feature/my-feature

# Then create a Pull Request on GitHub/GitLab
```

---

## Warnings & Guidelines

### 🔴 Critical (will break everything if ignored)

1. **Always activate venv before backend work.** Without it, Python can't find the installed packages.
2. **Always use `--legacy-peer-deps` for npm install.** Without it, installation fails.
3. **URL-encode MongoDB passwords.** Special characters in passwords MUST be encoded or the connection silently fails.
4. **Never edit `.env` while the server is running** and expect changes to take effect. Restart the server after .env changes.
5. **Both servers must run simultaneously.** Frontend without backend = blank page. Backend without frontend = API-only (works but no UI).

### 🟡 Important (will cause confusing issues)

6. **Don't delete `node_modules/` and reinstall without `--legacy-peer-deps`.** If you need to clean install: `rm -rf node_modules package-lock.json && npm install --legacy-peer-deps`
7. **The frontend port matters for CORS.** If your frontend runs on port 3001 instead of 3000, make sure `CORS_ORIGINS` in backend .env includes `http://localhost:3001`.
8. **JWT_SECRET must be the same across server restarts.** If you change it, all existing user sessions become invalid (they'll get 401 errors until they re-login).
9. **MongoDB Atlas free clusters pause after 7 days of inactivity.** If the backend suddenly can't connect, log into Atlas and check if the cluster is paused.
10. **`python` vs `py` on Windows.** Some Windows installs use `py` instead of `python`. If one doesn't work, try the other.

### 🟢 Good to Know

11. **Backend auto-reloads on file save** (thanks to `--reload` flag). No need to restart manually after code changes.
12. **Frontend hot-reloads on file save.** Changes appear in the browser within 1-2 seconds.
13. **Swagger docs at /docs.** Always available at http://localhost:8000/docs for testing endpoints manually.
14. **Tests use mocked databases.** Backend tests don't need a real MongoDB connection — they use unittest.mock.
15. **The `fix_auth.py` script** is useful for debugging: `python fix_auth.py --list` shows all users, `--delete email@test.com` removes a user.

---

## Architecture Quick Reference

### How a Request Flows

```
Browser (React) 
  → Axios (attaches JWT token) 
  → Backend API (FastAPI) 
  → jwt_middleware verifies token 
  → Route handler 
  → Service module (business logic) 
  → MongoDB (via Motor async driver)
  → Response back through the chain
```

### Database Collections

| Collection | Purpose |
|-----------|---------|
| `users` | User accounts (email, hashed password, profile) |
| `moods` | Mood check-in entries |
| `expenses` | Expense records |
| `journal` | Journal text entries |
| `tasks` | User tasks with progress |
| `goals` | Goals with target/current |
| `sleep` | Sleep log entries |
| `budget_categories` | Budget allocations per category |
| `subscriptions` | Tracked recurring subscriptions |
| `savings_goals` | Savings targets |
| `bill_splits` | Bill split records |
| `chat_messages` | AI chat history per buddy |
| `conversation_summaries` | Compressed old chat history |
| `notifications` | Generated notifications/nudges |
| `groups` | Study groups |
| `shared_goals` | Group shared goals with leaderboards |
| `challenges` | Community challenges |
| `group_activities` | Group activity feed |
| `gamification` | XP, level, streak per user |
| `achievements` | Earned achievement badges |
| `daily_insights` | Cached daily insight cards |
| `user_category_rules` | Learned expense categorization rules |
| `exercises` | Exercise log entries |

### Port Map

| Service | Default Port | URL |
|---------|-------------|-----|
| Backend API | 8000 | http://localhost:8000 |
| Frontend Dev | 3000 | http://localhost:3000 |
| Swagger Docs | 8000 | http://localhost:8000/docs |
| ReDoc | 8000 | http://localhost:8000/redoc |

---

## Deploying (Later)

When you're ready to deploy beyond localhost:

1. **Backend**: Deploy to any Python hosting (Railway, Render, AWS, etc.)
   - Set all environment variables in the hosting provider's dashboard
   - Run with `uvicorn server:app --host 0.0.0.0 --port $PORT` (no `--reload` in production)

2. **Frontend**: Build and deploy static files
   - `npm run build` creates a `build/` folder
   - Deploy to Vercel, Netlify, or any static hosting
   - Update `REACT_APP_BACKEND_URL` to point to your deployed backend URL

3. **Database**: MongoDB Atlas works for both dev and production (just ensure the deployment IP is whitelisted)

---

## Need Help?

- Check the [change_log.md](./change_log.md) to understand what was built in each session
- Check the [diary.md](./diary.md) to understand WHY certain decisions were made
- Check [backend/README.md](./backend/README.md) for the full API endpoint catalog
- Check [frontend/README.md](./frontend/README.md) for component architecture and styling
- The Swagger docs at http://localhost:8000/docs let you test any API endpoint directly in the browser
