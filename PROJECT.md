# Jtickets

A full-stack event booking platform. Event organizers create and manage events; customers browse, filter by category, and book tickets in real time. Role-based API access is enforced on every endpoint.

**Live demo** — _[add your Vercel URL here]_  
**API docs** — _[add your Render URL]/docs_

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI · SQLAlchemy · SQLite (dev) / PostgreSQL (prod) |
| Auth | JWT (python-jose) · bcrypt |
| Background jobs | FastAPI BackgroundTasks |
| Frontend | Vite · React 18 · GSAP ScrollTrigger |
| Styling | CSS Modules · Google Fonts (Pacifico · Nunito) |
| Infra | Docker · docker-compose · Render · Vercel |

---

## Features

### Backend
- **Role-based access control** — two roles: `organizer` and `customer`; enforced via a reusable FastAPI dependency
- **Concurrency-safe booking** — `SELECT FOR UPDATE` row lock prevents overselling under simultaneous requests
- **Background tasks** — booking confirmation and event-update notifications fire after the HTTP response, never blocking the caller
- **10 REST endpoints** with full ownership checks (organizers can only edit their own events; customers can only view their own bookings)

### Frontend
- Scroll-triggered GSAP animations — hero word fly-in, category card spring, event card stagger
- Auth modal (login / register) with role picker
- Booking modal — quantity selector, live price total, optimistic UI update
- Mobile-responsive — hamburger nav, single-column grid on small screens

---

## Getting started

```bash
# Backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
python seed.py                                  # creates organizer + 12 sample events
uvicorn app.main:app --reload                   # http://127.0.0.1:8000/docs

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                                     # http://localhost:5173
```

Default organizer account created by `seed.py`:  
`admin@jtickets.com` / `jtickets2026`

---

## API overview

```
POST  /signup            public
POST  /login             public
GET   /events            public
GET   /events/{id}       public
POST  /events            organizer
PUT   /events/{id}       organizer (owner)
DELETE /events/{id}      organizer (owner)
POST  /bookings          customer
GET   /bookings          customer
GET   /bookings/{id}     customer (owner)
```

---

## PostgreSQL (production)

Set `DATABASE_URL` in a `.env` file (see `.env.example`). The app defaults to SQLite when the variable is absent.

```
DATABASE_URL=postgresql://user:pass@host:5432/eventbooking
```

Docker Compose spins up a local PostgreSQL instance:

```bash
docker compose up -d
```

---

## Repository structure

```
jtickets/
├── app/               FastAPI application (auth, models, routes, tasks)
├── frontend/          Vite + React SPA
├── seed.py            Populate sample data
├── smoke_test.py      14-assertion end-to-end test
├── Dockerfile         For Render deployment
├── docker-compose.yml Local PostgreSQL
└── requirements.txt
```
