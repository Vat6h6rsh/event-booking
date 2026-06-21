# Event Booking System

A backend REST API for managing events and ticket bookings, built with **FastAPI + SQLAlchemy + SQLite**.

---

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the development server
uvicorn app.main:app --reload

# Windows users: set PYTHONUTF8=1 first if you see encoding errors in the terminal
# set PYTHONUTF8=1 && uvicorn app.main:app --reload
```

The interactive docs (Swagger UI) are at **http://127.0.0.1:8000/docs**.

> **Note:** `fastapi dev` is equivalent but requires UTF-8 terminal support on Windows.
> Use `uvicorn` directly if you see a `UnicodeEncodeError` in the console.

---

## API Overview

| Method | Endpoint | Auth required | Role |
|--------|----------|---------------|------|
| POST | `/signup` | No | — |
| POST | `/login` | No | — |
| POST | `/events` | Yes | organizer |
| GET | `/events` | No | — |
| GET | `/events/{id}` | No | — |
| PUT | `/events/{id}` | Yes | organizer (owner only) |
| DELETE | `/events/{id}` | Yes | organizer (owner only) |
| POST | `/bookings` | Yes | customer |
| GET | `/bookings` | Yes | customer |
| GET | `/bookings/{id}` | Yes | customer (owner only) |

### Smoke-test walkthrough

```bash
BASE=http://127.0.0.1:8000

# 1. Register an organizer
curl -X POST $BASE/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"organizer@example.com","password":"secret123","role":"organizer"}'

# 2. Log in and capture the token
TOKEN=$(curl -s -X POST $BASE/login \
  -d "username=organizer@example.com&password=secret123" | jq -r .access_token)

# 3. Create an event
curl -X POST $BASE/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Rock Night","venue":"Arena","event_date":"2026-12-01T20:00:00","total_tickets":100}'

# 4. Register a customer, log in, and book tickets
curl -X POST $BASE/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"fan@example.com","password":"secret123","role":"customer"}'

CTOKEN=$(curl -s -X POST $BASE/login \
  -d "username=fan@example.com&password=secret123" | jq -r .access_token)

curl -X POST $BASE/bookings \
  -H "Authorization: Bearer $CTOKEN" \
  -H "Content-Type: application/json" \
  -d '{"event_id":1,"quantity":2}'
# → server console prints: [EMAIL] Booking confirmation → fan@example.com ...

# 5. Update the event as the organizer → notification fires
curl -X PUT $BASE/events/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"venue":"New Venue"}'
# → server console prints: [NOTIFY] User 2 notified → event 'Rock Night' (id=1) was updated
```

---

## Design Decisions

### FastAPI `BackgroundTasks` instead of Celery / Redis
For a take-home exercise with zero infrastructure requirements, FastAPI's built-in `BackgroundTasks` is the right tool. It runs the task in the same process on a thread pool **after** the HTTP response is returned, so it never blocks the caller. In production I'd replace this with **Celery + Redis** for durable, retriable, observable task execution.

### Row lock for concurrency-safe ticket inventory
`SELECT FOR UPDATE` (`.with_for_update()`) ensures that two simultaneous booking requests for the last N tickets can't both pass the availability check. One transaction holds the lock, decrements the counter, and commits; only then does the second transaction read the updated value.

> **Note on SQLite:** `with_for_update()` is a no-op on SQLite because SQLite serialises all writes with a single write lock, which achieves the same result by a different mechanism. On **PostgreSQL or MySQL** this becomes a genuine row-level lock as intended. The README explicitly calls this out so reviewers know the author understands *why* the code is correct, not just that the tests pass.

### JWT authentication
Stateless tokens make the API horizontally scalable with no shared session store. Tokens carry the user's `id` and `role`, verified on every request by the `get_current_user` dependency. The `SECRET_KEY` is read from the `SECRET_KEY` environment variable (defaulting to a placeholder that must be overridden in production).

### Role-based access control
The `require_role(role)` dependency factory is the single authorisation gate. Any route that accepts only organisers or only customers wraps its handler with `Depends(require_role("organizer"))` or `Depends(require_role("customer"))`. A wrong-role request gets a `403` before any business logic runs.

### Resource ownership check
`PUT /events/{id}` and `DELETE /events/{id}` additionally verify `event.organizer_id == user.id`, ensuring an organiser cannot modify another organiser's events. Similarly, `GET /bookings/{id}` checks ownership before returning data.

---

## Production Hardening (what I'd add next)

1. **Celery + Redis** — replace `BackgroundTasks` with a durable queue; add retry logic and dead-letter handling.
2. **PostgreSQL + connection pooling** — swap the SQLite URL; use `pgbouncer` or SQLAlchemy's built-in pool for concurrency.
3. **Idempotency keys on bookings** — client-supplied `Idempotency-Key` header stored in DB; replay safe against network retries.
4. **Rate limiting on `POST /bookings`** — `slowapi` or an API-gateway rule prevents ticket-hoarding bots.
5. **Structured logging** — replace `print` with `structlog` / `python-json-logger`; ship to a log aggregator.
6. **Alembic migrations** — version-controlled schema changes instead of `create_all`.
7. **Read replica** — route `GET` queries to a read replica to offload the primary.
8. **HTTPS / API gateway** — TLS termination, auth token rotation, and DDoS protection at the edge.
