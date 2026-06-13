# PocketBuddy

PocketBuddy is your all-in-one AI wellness, finance, and productivity assistant. Designed to help you keep track of your daily habits, manage your expenses, split bills, track goals, and maintain a healthy routine. It provides an intuitive, gamified experience with personalized wellness insights and a fully functional AI-powered backend.

## 🚀 Getting Started

To collaborate effectively or run this project locally, you need to set up both the **Frontend (React)** and **Backend (FastAPI)**.

### Prerequisites

- [Node.js](https://nodejs.org/) (for the frontend)
- [Python 3.10+](https://www.python.org/) (for the backend)
- MongoDB Database (Local or MongoDB Atlas)

---

### 1. Backend Setup

The backend is built with Python, FastAPI, and Motor (Async MongoDB). 

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up Environment Variables:**
   Create a `.env` file in the `backend` directory containing your local or remote MongoDB URL, DB Name, and your LLM Keys.
   ```env
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=pocketbuddy
   EMERGENT_LLM_KEY=your_key_here
   ```

6. **Run the server:**
   ```bash
   uvicorn server:app --reload
   ```
   *The backend should now be running at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.*

---

### 2. Frontend Setup

The frontend is a React application utilizing Tailwind CSS and Radix UI components.

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   Due to some peer dependency conflicts with newer React versions, we recommend installing with `--legacy-peer-deps`:
   ```bash
   npm install --legacy-peer-deps
   ```
   *(Alternatively, if you use Yarn, you can run `yarn install`)*

3. **Start the development server:**
   ```bash
   npm start
   ```
   *The frontend should now be running at `http://localhost:3000`.*

---

## 🤝 Collaboration Guidelines

To ensure smooth collaboration across the team, please adhere to the following workflow:

### Branching Strategy
- **`main`**: Production-ready code. Always stable.
- **Feature Branches**: Branch off `main` for new features using the format `feature/<your-feature-name>` or `bugfix/<issue-name>`. 
  - Example: `feature/auth-backend` or `feature/gamification`.

### Commits & Pull Requests
- Keep your commits small and descriptive. Use conventional commit messages if possible (e.g., `feat: added wellness AI cards`).
- Before pushing, make sure all your tests pass locally.
- Create a Pull Request (PR) against `main`. Describe the changes made and link any relevant issue or task ID.
- Request a review from at least one collaborator before merging.

### Code Style
- **Backend**: We use `black`, `isort`, `flake8`, and `mypy` for Python code formatting and linting. Run these tools prior to committing.
- **Frontend**: Follow standard ESLint rules provided in the CRA setup. Use Prettier for formatting. Component structures should follow our design guidelines.

### Spec and Task Workflow
Refer to `diary.md`, `design.md`, and `requirements.md` in the root (and any `test_result.md` or `.kiro` plans) before making architectural changes. The plan follows a dependency-driven wave approach:
1. **Auth First**
2. **Gamification & APIs**
3. **AI Context & Conversation Memory**
4. **Notifications & Analytics**
5. **UI Integration & Polish**

Happy Coding! 🚀
