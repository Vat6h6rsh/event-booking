# Deployment Guide — Jtickets

## TL;DR recommendation

| Part | Service | Cost |
|---|---|---|
| Backend (FastAPI) | **Render** | Free (sleeps after 15 min idle) |
| Database (PostgreSQL) | **Render** | Free for 90 days, then ~$7/mo |
| Frontend (Vite/React) | **Vercel** | Free forever |

> **Why not AWS?** You'd pay for EC2, RDS, and a load balancer immediately. For a showcase project, Render + Vercel gives you a live HTTPS URL in under 10 minutes at zero cost.
>
> **Why not Vercel/Netlify for the backend?** Both are optimized for JS serverless functions. FastAPI is a long-running ASGI server — it needs a real container runtime like Render or Railway.

---

## Repo structure before deploying

```
jtickets/                ← your git root
├── app/                 ← FastAPI backend
├── frontend/            ← Vite + React
├── requirements.txt
├── Dockerfile
├── render.yaml
├── seed.py
└── ...
```

Everything lives in **one mono-repo**. Vercel deploys from the `frontend/` subdirectory; Render deploys the Python app from the repo root.

---

## Step 1 — Push to GitHub

See `GIT_SETUP.md` for the full git workflow. Once your repo is at `https://github.com/you/jtickets`, come back here.

---

## Step 2 — Deploy the backend on Render

### 2a. Create a PostgreSQL database

1. Go to [render.com](https://render.com) → **New → PostgreSQL**
2. Name: `jtickets-db`, Region: closest to you
3. Plan: **Free**
4. Click **Create Database**
5. Copy the **Internal Database URL** — you'll need it in 2b

### 2b. Create a Web Service for FastAPI

1. **New → Web Service** → connect your GitHub repo
2. Settings:
   - **Name**: `jtickets-api`
   - **Root Directory**: *(leave blank — Dockerfile is at repo root)*
   - **Environment**: Docker *(Render auto-detects the `Dockerfile`)*
   - **Plan**: Free
3. Under **Environment Variables**, add:

   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | the Internal Database URL from step 2a |
   | `SECRET_KEY` | any long random string (e.g. `openssl rand -hex 32`) |

4. Click **Create Web Service**
5. Render builds the Docker image and starts the server. First deploy takes ~3 minutes.
6. Your API is live at `https://jtickets-api.onrender.com`

### 2c. Seed the database

After the service is running, open the Render **Shell** tab and run:

```bash
python seed.py
```

This creates the organizer account and 12 sample events.

---

## Step 3 — Deploy the frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project** → import your GitHub repo
2. Configure:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Under **Environment Variables**, add:

   | Key | Value |
   |-----|-------|
   | `VITE_API_URL` | `https://jtickets-api.onrender.com` |

4. Update `frontend/src/lib/api.js` to use this env var in production:

   ```js
   const api = axios.create({
     baseURL: import.meta.env.VITE_API_URL || '/api',
   })
   ```

5. Click **Deploy** — done in ~30 seconds.
6. Your frontend is live at `https://jtickets.vercel.app` (or your custom Vercel URL).

### Update CORS in the backend

In `app/main.py`, add your Vercel URL to the CORS origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://jtickets.vercel.app",  # ← add this
    ],
    ...
)
```

Commit, push, Render redeploys automatically.

---

## Alternative: Railway (slightly better DX, tiny cost)

[Railway](https://railway.app) has a $5/month free credit and a much faster deploy experience than Render. Steps:

1. `railway login` (CLI or web)
2. Push repo → **New Project → Deploy from GitHub**
3. Add a **PostgreSQL** plugin — Railway injects `DATABASE_URL` automatically
4. Add `SECRET_KEY` env var
5. Railway detects the `Dockerfile` and deploys

Railway's advantage: services **never sleep** on the free credit tier. Render free tier sleeps after 15 minutes of inactivity and takes ~30 seconds to wake up on the first request — annoying for demos.

---

## Dockerfile (included in the repo)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Custom domain (optional, free on Vercel)

1. Buy a `.com` domain on Namecheap (~$10/year) or use a free `.is-a.dev` subdomain
2. In Vercel → **Settings → Domains** → add your domain
3. Follow the DNS instructions — takes 5 minutes to propagate

---

## Quick checklist before sharing your link

- [ ] Backend health check: `GET https://jtickets-api.onrender.com/docs` loads Swagger UI
- [ ] Frontend loads events from the real API (check Network tab)
- [ ] Signup → login → book a ticket works end-to-end
- [ ] CORS is configured for the Vercel domain
- [ ] `SECRET_KEY` is not the default placeholder
