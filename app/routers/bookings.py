import secrets, string
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Booking, BookingAttendee, TicketTier, User
from app import auth, schemas, tasks

router = APIRouter(prefix="/bookings", tags=["bookings"])

def _code():
    return "JTK-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

@router.post("", response_model=schemas.BookingOut, status_code=201)
def create_booking(body: schemas.BookingCreate, bg: BackgroundTasks,
                   db: Session = Depends(get_db),
                   user: User = Depends(auth.require_role("customer"))):

    ev = db.query(Event).filter(Event.id == body.event_id).with_for_update().first()
    if not ev: raise HTTPException(404, "Event not found")
    if ev.status != "published": raise HTTPException(409, "Event is not open for booking")

    # ── Age gate ──────────────────────────────────────────────────────────────
    if ev.age_rating in ("A", "18+") and body.attendees:
        under = [a.full_name for a in body.attendees if a.age is not None and a.age < 18]
        if under:
            raise HTTPException(
                400,
                f"Attendee(s) {', '.join(under)} must be 18+ for an event rated {ev.age_rating}"
            )

    # ── Inventory: tier or base pool ─────────────────────────────────────────
    tier       = None
    unit_price = ev.price
    if body.tier_id:
        tier = (db.query(TicketTier)
                  .filter_by(id=body.tier_id, event_id=ev.id)
                  .with_for_update().first())
        if not tier: raise HTTPException(404, "Ticket tier not found for this event")
        if tier.available_seats < body.quantity:
            raise HTTPException(409, f"Only {tier.available_seats} seat(s) left in '{tier.name}'")
        tier.available_seats -= body.quantity
        unit_price = tier.price
    else:
        if ev.available_tickets < body.quantity:
            raise HTTPException(409, f"Only {ev.available_tickets} ticket(s) remaining")
        ev.available_tickets -= body.quantity

    booking = Booking(
        user_id=user.id, event_id=ev.id, tier_id=body.tier_id,
        quantity=body.quantity, total_price=unit_price * body.quantity,
        status="confirmed",
    )
    db.add(booking); db.flush()

    # ── Attendees ─────────────────────────────────────────────────────────────
    for i in range(body.quantity):
        src = (body.attendees or [])[i] if i < len(body.attendees or []) else None
        db.add(BookingAttendee(
            booking_id=booking.id,
            full_name=src.full_name if src else f"Guest {i+1}",
            age=src.age if src else None,
            phone=src.phone if src else None,
            seat_label=src.seat_label if src else None,
            ticket_code=_code(),
        ))

    db.commit(); db.refresh(booking)
    bg.add_task(tasks.send_booking_confirmation, user.email, ev.name, booking.id, user.id)
    return booking

@router.get("", response_model=list[schemas.BookingOut])
def my_bookings(db: Session = Depends(get_db),
                user: User = Depends(auth.require_role("customer"))):
    return (db.query(Booking)
              .filter_by(user_id=user.id)
              .order_by(Booking.created_at.desc())
              .all())

@router.get("/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db),
                user: User = Depends(auth.require_role("customer"))):
    b = db.get(Booking, booking_id)
    if not b: raise HTTPException(404, "Booking not found")
    if b.user_id != user.id: raise HTTPException(403, "Access denied")
    return b

@router.delete("/{booking_id}", status_code=204)
def cancel_booking(booking_id: int, db: Session = Depends(get_db),
                   user: User = Depends(auth.require_role("customer"))):
    b = db.get(Booking, booking_id)
    if not b: raise HTTPException(404, "Booking not found")
    if b.user_id != user.id: raise HTTPException(403, "Access denied")
    if b.status == "cancelled": raise HTTPException(409, "Already cancelled")
    # restore inventory
    ev = db.get(Event, b.event_id)
    if ev:
        if b.tier_id:
            t = db.get(TicketTier, b.tier_id)
            if t: t.available_seats += b.quantity
        else:
            ev.available_tickets += b.quantity
    b.status = "cancelled"
    db.commit()
