# Git Setup — Jtickets

## Mono-repo or two repos?

**Use one mono-repo.** Here's why:

- The frontend and backend share context (API contract, seed data, docs). Keeping them together means one `git clone`, one PR to review a full-stack feature, and one place to look at history.
- Both Vercel and Render can be pointed at a **subdirectory** of a single repo, so there's no technical reason to split.
- Two repos = twice the branch management, twice the README maintenance, and confusing "which repo has the bug?" moments during demos.

The only reason to split is if you're putting this into a team with separate frontend/backend squads. For a portfolio project, mono-repo wins.

---

## Initial setup

### 1. Create a `.gitignore`

Create `y:\cactro\event-booking\.gitignore`:

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
venv/
.env
*.db
*.sqlite3

# Node
node_modules/
dist/
.vercel/

# OS
.DS_Store
Thumbs.db

# Editor
.vscode/
.idea/
*.swp
```

> **Important**: `.env` is in the ignore list. Never commit real secrets. Only commit `.env.example`.

### 2. Initialise the repo

```bash
cd y:\cactro\event-booking

git init
git add .
git commit -m "feat: initial full-stack Jtickets project

- FastAPI backend with JWT auth, role-based access control
- Booking endpoint with SELECT FOR UPDATE concurrency safety
- Two background tasks (booking confirmation + event update notify)
- Vite + React frontend with GSAP ScrollTrigger animations
- PostgreSQL support via DATABASE_URL env var, SQLite for local dev
- 12 seeded sample events across Music, Movies, Social categories"
```

### 3. Create the GitHub repo and push

```bash
# Create on GitHub first (https://github.com/new), then:
git remote add origin https://github.com/YOUR_USERNAME/jtickets.git
git branch -M main
git push -u origin main
```

---

## Recommended branch strategy

For a solo portfolio project, keep it simple:

```
main          ← always deployable, protected
  └─ feature/xyz   ← new work
  └─ fix/xyz       ← bug fixes
```

- Work on a branch, open a PR to `main`, squash-merge
- Render and Vercel auto-deploy on every push to `main`
- Never commit directly to `main` (good habit for interviews)

---

## Keeping the commit history clean

Interviewers and hiring managers **do** look at your commit history. Some tips:

**Write descriptive commits** using conventional commits style:
```
feat: add booking confirmation background task
fix: prevent overselling with SELECT FOR UPDATE row lock
refactor: extract require_role into reusable dependency
docs: add deployment guide and technical showcase
```

**Don't do:**
```
wip
asdfasdf
fixed stuff
trying something
```

**Squash before merging** if you have messy WIP commits on a branch:
```bash
git rebase -i HEAD~4   # squash last 4 commits into one clean commit
```

---

## File structure at a glance

```
jtickets/
├── app/                   ← FastAPI application
│   ├── __init__.py
│   ├── auth.py            ← JWT + RBAC
│   ├── database.py        ← SQLAlchemy engine
│   ├── main.py            ← all routes
│   ├── models.py          ← ORM tables
│   ├── schemas.py         ← Pydantic schemas
│   └── tasks.py           ← background task functions
├── frontend/              ← Vite + React SPA
│   ├── src/
│   │   ├── components/    ← Navbar, Hero, Cards, Modals…
│   │   ├── context/       ← AppContext (global state)
│   │   └── lib/api.js     ← axios wrapper
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── .env.example           ← committed ✓
├── .gitignore             ← committed ✓
├── docker-compose.yml     ← local Postgres + API
├── Dockerfile             ← for Render deployment
├── requirements.txt
├── seed.py                ← populate sample data
├── smoke_test.py          ← 14-assertion e2e test
├── DEPLOY.md              ← deployment guide
├── GIT_SETUP.md           ← this file
├── SHOWCASE.md            ← technical pitch script
└── README.md              ← run instructions + design decisions
```

---

## Linking deployments in your portfolio

Once live, your two URLs will look like:

- **API**: `https://jtickets-api.onrender.com/docs` — shareable Swagger UI, no login needed
- **App**: `https://jtickets.vercel.app` — the full frontend

Put both in your portfolio/CV, your GitHub repo description, and the `README.md`. Recruiters click links; make them easy to find.

---

## Connecting deployments to auto-deploy

After connecting your GitHub repo to both Render and Vercel:

| Push to | What happens |
|---|---|
| `main` | Render rebuilds and redeploys the API; Vercel rebuilds and redeploys the frontend |
| feature branch | Nothing auto-deploys (Render) / Vercel creates a preview URL (optional) |

This means `git push origin main` is your entire deploy pipeline — no CI/CD configuration needed for a portfolio project.
