import hashlib
import json
from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.database import get_db
from app.models import Event, Booking, BookingAttendee, TicketTier, User, IdempotencyKey, _ticket_code, utcnow
from app import auth, schemas, outbox

router = APIRouter(prefix="/bookings", tags=["bookings"])
_BOOKING_LOAD = (joinedload(Booking.event), joinedload(Booking.tier), selectinload(Booking.attendees))


def _reserve_key(db, user_id, key, body):
    fingerprint = hashlib.sha256(json.dumps(
        body.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()
    # Legacy sqlite3 transaction control does not BEGIN for SELECT/SAVEPOINT.
    # Explicitly begin the outer transaction so releasing the savepoint cannot
    # commit a key independently of its booking/outbox/inventory transaction.
    if db.bind.dialect.name == "sqlite":
        conn = db.connection()
        if not conn.connection.driver_connection.in_transaction:
            conn.exec_driver_sql("BEGIN")
    db.execute(delete(IdempotencyKey).where(
        IdempotencyKey.user_id == user_id, IdempotencyKey.key == key,
        IdempotencyKey.created_at < utcnow() - timedelta(hours=24),
    ))
    record = IdempotencyKey(user_id=user_id, key=key, request_hash=fingerprint)
    try:
        with db.begin_nested():
            db.add(record)
            db.flush()
    except IntegrityError:
        record = db.scalar(select(IdempotencyKey).where(
            IdempotencyKey.user_id == user_id, IdempotencyKey.key == key
        ))
        if record is None: raise HTTPException(409, "Request already in progress")
        if record.request_hash != fingerprint:
            raise HTTPException(422, "Idempotency-Key reused with a different request")
        if record.booking_id is None: raise HTTPException(409, "Request already in progress")
        booking = db.scalar(select(Booking).where(Booking.id == record.booking_id).options(*_BOOKING_LOAD))
        return record, schemas.BookingOut.model_validate(booking)
    return record, None


@router.post("", response_model=schemas.BookingOut, status_code=201)
def create_booking(body: schemas.BookingCreate, response: Response,
                   idempotency_key: str | None = Header(None, min_length=1, max_length=80),
                   db: Session = Depends(get_db),
                   user: User = Depends(auth.require_role("customer"))):
    user_id = user.id
    try:
        key = None
        if idempotency_key is not None:
            key, replay = _reserve_key(db, user_id, idempotency_key, body)
            if replay is not None:
                db.rollback()
                response.status_code = 200
                response.headers["Idempotent-Replayed"] = "true"
                return replay

        ev = db.get(Event, body.event_id)
        if not ev: raise HTTPException(404, "Event not found")
        if ev.status != "published": raise HTTPException(409, "Event is not open for booking")

        if ev.age_rating in ("A", "18+"):
            if not body.attendees or any(a.age is None or a.age < 18 for a in body.attendees):
                raise HTTPException(400, f"Every attendee must provide an age of 18+ for an event rated {ev.age_rating}")

        tier = None
        if body.tier_id is not None:
            tier = db.scalar(select(TicketTier).where(TicketTier.id == body.tier_id, TicketTier.event_id == ev.id))
            if not tier: raise HTTPException(404, "Ticket tier not found for this event")

        total = (tier.price if tier else ev.price) * body.quantity
        if total > 2_147_483_647: raise HTTPException(422, "Booking total exceeds the supported paise amount")
        booking = Booking(user_id=user_id, event_id=ev.id, tier_id=body.tier_id,
                          quantity=body.quantity, total_price=total, status="confirmed")
        db.add(booking); db.flush()
        attendees = []
        for i in range(body.quantity):
            src = body.attendees[i] if body.attendees else None
            attendees.append(dict(booking_id=booking.id, full_name=src.full_name if src else f"Guest {i+1}",
                                  age=src.age if src else None, phone=src.phone if src else None,
                                  seat_label=src.seat_label if src else None, ticket_code=_ticket_code()))
        saved = db.scalars(insert(BookingAttendee).returning(BookingAttendee), attendees).all()
        outbox.enqueue_booking_confirmation(db, booking.id)
        if key is not None: key.booking_id = booking.id
        db.flush()
        # Prepare all inserts before taking the hot event inventory lock. The
        # conditional decrements are the final writes before COMMIT in the
        # common path; failed claims roll the complete transaction back.
        ev = db.execute(update(Event).where(
            Event.id == body.event_id, Event.status == "published", Event.available_tickets >= body.quantity
        ).values(available_tickets=Event.available_tickets - body.quantity).returning(Event)
          .execution_options(populate_existing=True)).scalar_one_or_none()
        if ev is None:
            current = db.scalar(select(Event).where(Event.id == body.event_id).execution_options(populate_existing=True))
            if not current: raise HTTPException(404, "Event not found")
            if current.status != "published": raise HTTPException(409, "Event is not open for booking")
            raise HTTPException(409, f"Only {current.available_tickets} ticket(s) remaining")
        if ev.age_rating in ("A", "18+") and (not body.attendees or any(a.age is None or a.age < 18 for a in body.attendees)):
            raise HTTPException(400, f"Every attendee must provide an age of 18+ for an event rated {ev.age_rating}")
        if body.tier_id is not None:
            tier = db.execute(update(TicketTier).where(
                TicketTier.id == body.tier_id, TicketTier.event_id == ev.id,
                TicketTier.available_seats >= body.quantity
            ).values(available_seats=TicketTier.available_seats - body.quantity).returning(TicketTier)
              .execution_options(populate_existing=True)).scalar_one_or_none()
            if tier is None:
                current = db.scalar(select(TicketTier).where(TicketTier.id == body.tier_id, TicketTier.event_id == ev.id)
                                    .execution_options(populate_existing=True))
                if not current: raise HTTPException(404, "Ticket tier not found for this event")
                raise HTTPException(409, f"Only {current.available_seats} seat(s) left in '{current.name}'")
        # If an organizer changed the price between the initial read and claim,
        # use the locked row's price. Usually this requires no additional write.
        total = (tier.price if tier else ev.price) * body.quantity
        if total > 2_147_483_647: raise HTTPException(422, "Booking total exceeds the supported paise amount")
        if total != booking.total_price:
            booking.total_price = total
            db.flush()
        # Construct explicitly before commit. No relationship access, refresh or
        # lazy load occurs after commit, including during FastAPI serialization.
        result = schemas.BookingOut(
            id=booking.id, event_id=ev.id, event_name=ev.name, tier_id=body.tier_id,
            tier_name=tier.name if tier else None, quantity=booking.quantity,
            total_price=booking.total_price, status=booking.status, created_at=booking.created_at,
            attendees=[schemas.AttendeeOut.model_validate(a) for a in saved],
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    outbox.kick()
    return result


@router.get("", response_model=list[schemas.BookingOut])
def my_bookings(db: Session = Depends(get_db),
                user: User = Depends(auth.require_role("customer"))):
    return (db.query(Booking).options(*_BOOKING_LOAD).filter_by(user_id=user.id)
            .order_by(Booking.created_at.desc()).all())


@router.get("/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db),
                user: User = Depends(auth.require_role("customer"))):
    b = db.scalar(select(Booking).where(Booking.id == booking_id).options(*_BOOKING_LOAD))
    if not b: raise HTTPException(404, "Booking not found")
    if b.user_id != user.id: raise HTTPException(403, "Access denied")
    return b


@router.delete("/{booking_id}", status_code=204)
def cancel_booking(booking_id: int, db: Session = Depends(get_db),
                   user: User = Depends(auth.require_role("customer"))):
    try:
        b = db.get(Booking, booking_id)
        if not b: raise HTTPException(404, "Booking not found")
        if b.user_id != user.id: raise HTTPException(403, "Access denied")
        now = utcnow()
        cancelled = db.execute(update(Booking).where(
            Booking.id == booking_id, Booking.user_id == user.id, Booking.status == "confirmed"
        ).values(status="cancelled", cancelled_at=now).returning(
            Booking.event_id, Booking.tier_id, Booking.quantity
        )).first()
        if cancelled is None: raise HTTPException(409, "Already cancelled or not confirmed")
        # All inventory writers acquire the event row before the tier row.
        restored = db.execute(update(Event).where(
            Event.id == cancelled.event_id, Event.event_date > now,
            Event.available_tickets + cancelled.quantity <= Event.total_tickets
        ).values(available_tickets=Event.available_tickets + cancelled.quantity).returning(Event.id)).first()
        if restored is None: raise HTTPException(409, "Cannot cancel after event start or restore invalid inventory")
        if cancelled.tier_id is not None:
            restored = db.execute(update(TicketTier).where(
                TicketTier.id == cancelled.tier_id,
                TicketTier.available_seats + cancelled.quantity <= TicketTier.total_seats
            ).values(available_seats=TicketTier.available_seats + cancelled.quantity).returning(TicketTier.id)).first()
            if restored is None: raise HTTPException(409, "Cannot restore invalid tier inventory")
        db.commit()
    except Exception:
        db.rollback()
        raise
