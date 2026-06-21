"""
Background task functions.

These are intentionally simple stubs that print to stdout.
In production these would dispatch to a durable task queue (e.g. Celery + Redis)
so that delivery is guaranteed even if the worker crashes.
"""


def send_booking_confirmation(email: str, event_name: str, booking_id: int) -> None:
    """Background Task 1 — simulates sending a booking confirmation email."""
    print(
        f"[EMAIL] Booking confirmation → {email} | "
        f"event='{event_name}' booking_id={booking_id}"
    )


def notify_event_update(user_id: int, event_id: int, event_name: str) -> None:
    """Background Task 2 — simulates notifying a customer about an event update."""
    print(
        f"[NOTIFY] User {user_id} notified → event '{event_name}' (id={event_id}) was updated"
    )
