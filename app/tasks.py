"""
Background task entry points.

These are the callables the routers hand to FastAPI `BackgroundTasks`, so they run
*after* the HTTP response is returned and never block the caller. Each opens its
own DB session (the request-scoped session is already closed by the time these run)
and delegates delivery to the swappable `notifier` in `app.notifications`.

Why FastAPI `BackgroundTasks` and not Celery/Redis? The task is "print a line," and
the exercise explicitly allows any mechanism. `BackgroundTasks` keeps the project
zero-infra to run and review, while the `Notifier` seam means upgrading to a durable
queue is a one-class change here — the routers stay identical.
"""
from app.database import SessionLocal
from app import notifications


def send_booking_confirmation(email: str, event_name: str, booking_id: int,
                             user_id: int) -> None:
    """Background Task 1 — booking confirmation (simulated email + in-app record)."""
    db = SessionLocal()
    try:
        notifications.notifier.booking_confirmed(
            db, user_id=user_id, email=email,
            event_name=event_name, booking_id=booking_id,
        )
    finally:
        db.close()


def notify_event_update(user_id: int, event_id: int, event_name: str) -> None:
    """Background Task 2 — notify one customer who booked an updated event."""
    db = SessionLocal()
    try:
        notifications.notifier.event_updated(
            db, user_id=user_id, event_id=event_id, event_name=event_name,
        )
    finally:
        db.close()
