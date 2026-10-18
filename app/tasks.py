"""The two background task handlers, invoked by the durable outbox dispatcher."""
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.database import SessionLocal
from app.models import Booking, Event, User
from app import notifications


def send_booking_confirmation(booking_id: int, job_id: int):
    """Task 1: send a real confirmation email and persist the in-app record."""
    with SessionLocal() as db:
        booking = db.scalar(select(Booking).where(Booking.id == booking_id).options(
            joinedload(Booking.event), joinedload(Booking.tier), joinedload(Booking.user),
            selectinload(Booking.attendees),
        ))
        if not booking: raise RuntimeError("Booking for outbox job no longer exists")
        notifications.notifier.booking_confirmed(db, booking=booking, job_id=job_id)


def notify_event_update(user_id: int, event_id: int, summary: str, job_id: int):
    """Task 2: notify one distinct confirmed booker by email and in-app alert."""
    with SessionLocal() as db:
        user, event = db.get(User, user_id), db.get(Event, event_id)
        if not user or not event: raise RuntimeError("Recipient/event for outbox job no longer exists")
        notifications.notifier.event_updated(db, user=user, event=event, summary=summary, job_id=job_id)
