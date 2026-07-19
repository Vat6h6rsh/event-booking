"""
Notification dispatch — the seam behind the two background tasks.

The routers schedule `app.tasks.*` on FastAPI `BackgroundTasks`; those thin
wrappers delegate here. Keeping dispatch behind a `Notifier` interface means the
delivery mechanism is a swap-one-line decision: today a `LogNotifier` (console log
+ an in-app record); in production a `CeleryNotifier` / `EmailNotifier` that pushes
onto a durable queue. The routers never change.
"""
import logging

from sqlalchemy.orm import Session

from app.models import Notification

logger = logging.getLogger("jtickets.notifications")


class Notifier:
    """Delivery interface. Implementations decide *how* a notification goes out."""

    def booking_confirmed(self, db: Session, *, user_id: int, email: str,
                          event_name: str, booking_id: int) -> None:
        raise NotImplementedError

    def event_updated(self, db: Session, *, user_id: int, event_id: int,
                      event_name: str) -> None:
        raise NotImplementedError


class LogNotifier(Notifier):
    """Default: emit a structured log line AND persist an in-app notification.

    The `[EMAIL]` / `[NOTIFY]` markers are kept explicit so they are easy to point
    at during the demo; the in-app row is what lets the customer *see* the alert.
    """

    def booking_confirmed(self, db: Session, *, user_id: int, email: str,
                          event_name: str, booking_id: int) -> None:
        logger.info(
            "[EMAIL] Booking confirmation -> %s | event=%r booking_id=%s",
            email, event_name, booking_id,
        )
        db.add(Notification(
            user_id=user_id,
            type="booking_confirmed",
            message=f"Your booking for '{event_name}' is confirmed. 🎟️",
        ))
        db.commit()

    def event_updated(self, db: Session, *, user_id: int, event_id: int,
                     event_name: str) -> None:
        logger.info(
            "[NOTIFY] User %s notified -> event %r (id=%s) was updated",
            user_id, event_name, event_id,
        )
        db.add(Notification(
            user_id=user_id,
            type="event_updated",
            event_id=event_id,
            message=f"'{event_name}' — an event you booked was just updated. Check the latest details.",
        ))
        db.commit()


# The single dispatch point the app imports. Reassign to swap delivery backends.
notifier: Notifier = LogNotifier()
