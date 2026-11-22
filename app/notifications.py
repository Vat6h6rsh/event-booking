"""Swappable delivery seam: one in-app record per job, plus transactional email."""
import logging

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app import email
from app.models import Notification

logger = logging.getLogger("jtickets.notifications")


class Notifier:
    def booking_confirmed(self, db, *, booking, job_id):
        raise NotImplementedError

    def event_updated(self, db, *, user, event, summary, job_id):
        raise NotImplementedError


def _persist(db, **values):
    insert = sqlite_insert if db.bind.dialect.name == "sqlite" else pg_insert
    db.execute(insert(Notification).values(**values).on_conflict_do_nothing(index_elements=["job_id"]))
    # Release the connection before network I/O. A retry sends email again but
    # job_id uniqueness protects the in-app record.
    db.commit()


class EmailNotifier(Notifier):
    def booking_confirmed(self, db, *, booking, job_id):
        event = booking.event
        recipient = booking.user.email
        subject = f"Booking confirmation - {event.name}"
        total = f"{booking.total_price // 100}.{booking.total_price % 100:02d}"
        html, text = email.ticket_template(
            event=event.name, when=email.ist_date(event.event_date), venue=event.venue,
            tier=booking.tier.name if booking.tier else "General", quantity=booking.quantity,
            total=total, booking_id=booking.id,
            attendees=[(a.full_name, a.seat_label, a.ticket_code) for a in booking.attendees],
        )
        _persist(db, user_id=booking.user_id, event_id=event.id, job_id=job_id,
                 type="booking_confirmed", message=f"Your booking for '{event.name}' is confirmed.")
        email.send_email(recipient, subject, html, text)
        logger.info("[EMAIL] Booking confirmation delivered | job_id=%s", job_id)

    def event_updated(self, db, *, user, event, summary, job_id):
        recipient = user.email
        subject = f"Event update - {event.name}"
        html, text = email.template("An event you booked has changed", [
            f"Event: {event.name}", summary,
        ])
        _persist(db, user_id=user.id, event_id=event.id, job_id=job_id,
                 type="event_updated", message=f"'{event.name}' was updated. {summary}")
        email.send_email(recipient, subject, html, text)
        logger.info("[NOTIFY] Event update delivered | job_id=%s", job_id)


notifier: Notifier = EmailNotifier()
