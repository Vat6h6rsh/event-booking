# Jtickets — Event Booking System

A backend for an event-booking platform with two roles — **organizers** manage events,
**customers** browse and book tickets — plus role-based API access and two background
tasks (booking confirmation, event-update notification). Built with **FastAPI +
SQLAlchemy**, shipped with a full **React** frontend on top.

- **Live demo:** _add your Vercel URL_ · **API docs (Swagger):** _add your Render URL_`/docs`
- **Deploy it yourself:** see [DEPLOYMENT.md](DEPLOYMENT.md) · **Demo walkthrough:** see [DEMO_SCRIPT.md](DEMO_SCRIPT.md)

> This started as a backend take-home. The core requirements are met exactly as asked;
> the tiers/venues/support/seat-map features and the React UI are extras built on the
> same role-gated API.

---

## Does it meet the brief? Requirement → code → test

Every graded requirement maps to a specific place in the code **and** a test that proves it.

| Requirement | Where it lives | Proven by |
|---|---|---|
| Two user types (`organizer`, `customer`) | `role` on `User` — [app/models.py](app/models.py#L17); constrained at signup — [app/schemas.py](app/schemas.py#L10) | `tests/test_rbac.py` |
| **Role-based API access control** | `require_role()` dependency factory — [app/auth.py](app/auth.py#L84) | `test_rbac.py::test_customer_cannot_create_event_403`, `::test_organizer_cannot_list_customer_bookings_403` |
| Ownership (beyond role) | `event.organizer_id == user.id` — [app/routers/events.py](app/routers/events.py#L43) | `test_rbac.py::test_organizer_cannot_edit_another_organizers_event_403` |
| Organizers manage events | organizer-gated CRUD — [app/routers/events.py](app/routers/events.py) | `test_booking.py`, `test_rbac.py` |
| Customers browse & book | public `GET /events`; customer `POST /bookings` — [app/routers/bookings.py](app/routers/bookings.py#L13) | `test_booking.py` |
| **Background Task 1 — booking confirmation** | scheduled after response — [app/routers/bookings.py](app/routers/bookings.py#L68) → [app/tasks.py](app/tasks.py) → [app/notifications.py](app/notifications.py) | `test_background_tasks.py::test_task1_booking_confirmation_fires` |
| **Background Task 2 — event-update notification to booked customers** | loop over confirmed bookings — [app/routers/events.py](app/routers/events.py#L47) → `notify_event_update` | `test_background_tasks.py::test_task2_event_update_notifies_booked_customer` (+ negative test) |
| _Bonus:_ concurrency-safe inventory | `SELECT FOR UPDATE` row lock — [app/routers/bookings.py](app/routers/bookings.py#L18) | `test_concurrency.py` (PostgreSQL) |

Run `pytest -q` → **11 passed, 1 skipped** (the concurrency test is PostgreSQL-only; see [Testing](#testing)).

---

## Quick start (local)

```bash
# ── Backend ──────────────────────────────────────────────
python -m venv venv && venv\Scripts\activate      # Windows  (source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python seed.py                                     # organizer + 12 sample events
uvicorn app.main:app --reload                      # http://127.0.0.1:8000/docs

# ── Tests (new terminal) ─────────────────────────────────
pytest -q

# ── Frontend (new terminal) ──────────────────────────────
cd frontend
npm install
npm run dev                                        # http://localhost:5173
```

Default organizer from `seed.py`: **admin@jtickets.com / jtickets2026**.
Register a `customer` from the UI (or `POST /signup`) to book.

No database to install — the app defaults to a local SQLite file. Set `DATABASE_URL` to
use PostgreSQL (see [.env.example](.env.example) and [DEPLOYMENT.md](DEPLOYMENT.md)).

---

## Architecture

```
                         ┌──────────────────────────────┐
  React SPA  ──HTTP──►    │  FastAPI                      │
  (Vite)      Bearer JWT  │   auth.require_role() gate    │──► SQLAlchemy ──► SQLite / PostgreSQL
                         │   routers/*                    │
                         │                                │
   POST /bookings  ──────┼─► BackgroundTasks ─► tasks ─► notifications.Notifier
   PUT  /events/{id} ────┘         (after response)         │   • console log  [EMAIL]/[NOTIFY]
                                                            │   • Notification row  ──► GET /notifications (bell)
```

- **One authorization gate.** Every protected route depends on `require_role("organizer")`
  or `require_role("customer")`, so a wrong-role request is rejected with `403` before any
  business logic runs. Ownership checks (`organizer_id == user.id`) add a second layer.
- **Background tasks never block the caller.** The HTTP response returns first; FastAPI then
  runs the task. Dispatch goes through a swappable `Notifier` — see below.
- **Both tasks are observable two ways:** the console log the brief asks for, *and* a
  persisted `Notification` the customer sees in the UI bell (so Task 2 isn't invisible).

---

## The two background tasks

**Task 1 — Booking confirmation.** On a successful `POST /bookings`, the router schedules
`send_booking_confirmation` on FastAPI `BackgroundTasks`. It logs:

```
[EMAIL] Booking confirmation -> fan@test.com | event='Neon Dreamz Live 2026' booking_id=7
```

**Task 2 — Event-update notification.** On `PUT /events/{id}`, the router collects the
distinct customers with a confirmed booking and schedules one `notify_event_update` per
customer. Each logs and records an in-app notification:

```
[NOTIFY] User 4 notified -> event 'Neon Dreamz Live 2026' (id=1) was updated
```

**Why FastAPI `BackgroundTasks` and not Celery/Redis?** The brief allows *any* mechanism and
says a print is sufficient, so the right call for a reviewable project is the zero-infra
option. The important part is that delivery is behind a seam — [`app/notifications.py`](app/notifications.py)
defines a `Notifier` interface with a default `LogNotifier`. Swapping to a durable queue is a
one-class change (`CeleryNotifier`) with **no router changes**. That upgrade path is the
design decision; the print is the placeholder.

---

## Design decisions

- **RBAC as a dependency factory.** `require_role(role)` returns a dependency, so
  authorization is declarative and testable, not copy-pasted `if` checks. — [app/auth.py](app/auth.py#L84)
- **Concurrency-safe inventory.** The booking transaction locks the event/tier row with
  `.with_for_update()` before checking availability, so two simultaneous requests for the
  last ticket can't both succeed. **Caveat:** this is a real row lock only on PostgreSQL;
  on SQLite it's a no-op, which is exactly why `test_concurrency.py` is PostgreSQL-gated and
  the deployment runs Postgres. — [app/routers/bookings.py](app/routers/bookings.py#L18)
- **Stateless JWT auth.** Tokens carry `id`, `role`, `email`; verified per request by
  `get_current_user`. No server session store → horizontally scalable. — [app/auth.py](app/auth.py)
- **Money in integer paise.** All prices are integers (paise), never floats — no rounding
  drift on totals. — [app/models.py](app/models.py#L61)
- **Two-level inventory.** An event has a base ticket pool *and* optional named tiers
  (General/VIP/…), each with its own locked seat count. — [app/routers/bookings.py](app/routers/bookings.py#L31)
- **Notifications are visible, not just logged.** Task output is persisted so the frontend
  bell can show it — the demo shows an alert appearing, not only a terminal line.
- **Operational hygiene.** Structured logging config, env-driven CORS (`CORS_ORIGINS`), a
  catch-all exception handler that logs the traceback and returns clean JSON, and a
  `postgres://`→`postgresql://` URL fix so a copy-pasted managed DB URL just works. —
  [app/main.py](app/main.py), [app/database.py](app/database.py)

---

## API reference

Auth: send `Authorization: Bearer <token>` from `POST /login`. In Swagger, click **Authorize**.

| Method | Endpoint | Access |
|---|---|---|
| POST | `/signup` | public |
| POST | `/login` | public |
| GET | `/users/me`, PUT `/users/me` | authenticated |
| GET | `/events` · `/events/{id}` · `/events/{id}/tiers` · `/events/{id}/seats` | public |
| GET | `/events/mine` | organizer |
| POST | `/events` | organizer |
| PUT · DELETE | `/events/{id}` | organizer (owner) — **PUT triggers Task 2** |
| POST · PUT · DELETE | `/events/{id}/tiers[/{tier_id}]` | organizer (owner) |
| POST | `/bookings` | customer — **triggers Task 1** |
| GET | `/bookings` · `/bookings/{id}` | customer (owner) |
| DELETE | `/bookings/{id}` | customer (owner) — restores inventory |
| GET | `/notifications` | authenticated (own) |
| POST | `/notifications/{id}/read` · `/notifications/read-all` | authenticated (own) |
| GET · POST · PUT · DELETE | `/venues[...]` | public read · organizer write (owner) |
| POST/GET/PUT | `/support/tickets[...]` | authenticated (own; organizers may view/reply) |
| POST | `/upload/image` | authenticated (Cloudflare R2) |
| GET | `/legal/terms` · `/legal/privacy` | public |

Full interactive reference at `/docs`.

---

## Testing

One command, no running server required (uses FastAPI's `TestClient`):

```bash
pytest -q
```

| File | What it proves |
|---|---|
| `tests/test_rbac.py` | 401 without a token; 403 on wrong role; 403 on cross-owner edits |
| `tests/test_booking.py` | inventory decrements; over-booking → 409; cancel restores inventory; age-gate |
| `tests/test_background_tasks.py` | **both** tasks fire — asserts the console log *and* the in-app notification row; plus a negative test that non-booking customers are not notified |
| `tests/test_concurrency.py` | last ticket is never oversold under concurrent requests — **PostgreSQL only** |

The concurrency test needs real row locks, so it **skips on SQLite**. To run it for real:

```bash
docker compose up -d db
DATABASE_URL=postgresql://jtickets:jtickets_dev@localhost:5432/eventbooking pytest tests/test_concurrency.py -v
```

The root-level `smoke_test.py` is a separate live-server script (14 assertions end-to-end)
you can run against a deployed URL by editing its `BASE`.

---

## Project structure

```
app/
  main.py           app wiring: routers, CORS, logging, error handler
  auth.py           JWT + require_role() RBAC gate
  models.py         SQLAlchemy models (User, Event, TicketTier, Booking, Notification, …)
  schemas.py        Pydantic request/response models
  database.py       engine/session; SQLite default, PostgreSQL via DATABASE_URL
  tasks.py          background-task entry points (scheduled by routers)
  notifications.py  swappable Notifier seam behind the two tasks
  routers/          auth, users, events, bookings, notifications, venues, support, upload, legal
tests/              pytest suite (rbac, booking, background_tasks, concurrency)
frontend/           Vite + React SPA (NotificationBell surfaces Task 2 in-app)
seed.py             organizer + 12 sample events
Dockerfile · docker-compose.yml   API image + local PostgreSQL
```

---

## What I'd add next (production)

1. **Durable queue** — swap `LogNotifier` for a Celery/Redis `Notifier` (retries, DLQ, real email).
2. **Idempotency keys** on `POST /bookings` — safe against client retries.
3. **Rate limiting** on booking — block ticket-hoarding bots (`slowapi`).
4. **Alembic migrations** — versioned schema instead of `create_all`.
5. **Read replica + connection pooling** for `GET`-heavy browse traffic.
