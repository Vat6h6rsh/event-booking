# Jtickets — Technical Showcase

## What It Is

**Jtickets** is a full-stack event booking platform built as a take-home engineering assignment. It lets two types of users — **Event Organizers** and **Customers** — interact with a shared system: organizers create and manage events, customers browse and book tickets. The entire API is role-gated, and the UI is a responsive single-page app with scroll-triggered animations.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI (Python) | Async-ready, auto-generated OpenAPI docs, type-safe with Pydantic |
| Database | PostgreSQL (SQLite in dev) | Production-grade relational DB; SQLite for zero-infra local runs |
| ORM | SQLAlchemy 2.0 | Declarative models, session management, row-level locking |
| Auth | JWT (python-jose) + bcrypt | Stateless tokens — horizontally scalable, no shared session store |
| Background Tasks | FastAPI BackgroundTasks | Decoupled, non-blocking; drops in for Celery in production |
| Frontend | Vite + React 18 | Fast HMR, component model, minimal bundle |
| Animations | GSAP + ScrollTrigger | Production-grade animation library used by major studios |
| Styling | CSS Modules + custom properties | Zero-runtime, scoped, no build-time CSS-in-JS cost |

---

## Key Engineering Decisions

### 1. Concurrency-safe ticket inventory

The most technically interesting part of the system is the booking endpoint. A naive implementation reads `available_tickets`, checks it, then decrements it — leaving a race window where two concurrent requests both pass the check and oversell the last ticket.

The fix is one line:

```python
event = db.query(Event).filter_by(id=event_id).with_for_update().first()
```

`SELECT FOR UPDATE` acquires a row-level lock for the entire transaction. On PostgreSQL this is a true row lock; on SQLite it degrades to a full-table write lock (which still prevents overselling, just less granularly). The README is explicit about this distinction — showing awareness of *why* the code is correct, not just that it passes tests.

### 2. Role-based access control as a dependency

RBAC is a reusable FastAPI dependency, not scattered middleware:

```python
def require_role(role: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(403, f"Requires {role} role")
        return user
    return checker
```

Any route gets role enforcement by adding `Depends(require_role("organizer"))` to its signature. A customer hitting `POST /events` gets a `403` before a single line of business logic runs.

### 3. Background tasks that don't block the response

Booking confirmation emails and event-update notifications fire *after* the HTTP response is sent:

```python
bg.add_task(tasks.send_booking_confirmation, user.email, event.name, booking.id)
return booking  # response goes out here; task runs after
```

This keeps P99 booking latency independent of notification latency. In production this graduates to **Celery + Redis** for durability, retries, and dead-letter queues — noted explicitly in the README so reviewers see the production awareness.

### 4. JWT with role in payload

The token payload carries both `sub` (user ID) and `role`. The frontend decodes the payload client-side to conditionally render UI — no extra `/me` API call needed on page load.

---

## API Surface (10 endpoints)

```
POST  /signup            — register organizer or customer
POST  /login             — issue JWT token
POST  /events            — create event             [organizer]
GET   /events            — list all events           [public]
GET   /events/{id}       — event detail              [public]
PUT   /events/{id}       — update event              [organizer, owner-only]
DELETE /events/{id}      — delete event              [organizer, owner-only]
POST  /bookings          — book tickets              [customer]
GET   /bookings          — my bookings               [customer]
GET   /bookings/{id}     — single booking            [customer, owner-only]
```

---

## Frontend Highlights

- **GSAP ScrollTrigger** animations: hero words fly in on load, category cards spring in, event cards stagger up from the bottom on scroll
- **Optimistic UI**: after a booking, `available_tickets` decrements immediately in the React state tree without a refetch
- **Single-page, modal-driven flow**: auth (login/signup) and booking happen in layered modals — no page navigations
- **Mobile-first responsive layout**: hamburger nav, auto-fill event grid, full-width modals on small screens

---

## What I'd add for production

Celery + Redis for durable task queues, Alembic for schema migrations, idempotency keys on `POST /bookings`, rate limiting on the booking endpoint, structured JSON logging, read replicas for `GET /events`, and an API gateway for TLS termination + DDoS protection.
