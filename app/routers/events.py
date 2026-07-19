from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, TicketTier, Booking, BookingAttendee, User
from app import auth, schemas, tasks

router = APIRouter(prefix="/events", tags=["events"])

# ── Events CRUD ──────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.EventOut, status_code=201)
def create_event(body: schemas.EventCreate, db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    ev = Event(**body.model_dump(), available_tickets=body.total_tickets, organizer_id=user.id)
    db.add(ev); db.commit(); db.refresh(ev)
    return ev

@router.get("", response_model=list[schemas.EventOut])
def list_events(skip: int = 0, limit: int = 100, category: str = None,
                age_rating: str = None, db: Session = Depends(get_db)):
    q = db.query(Event).filter(Event.status == "published")
    if category:   q = q.filter(Event.category == category)
    if age_rating: q = q.filter(Event.age_rating == age_rating)
    return q.order_by(Event.event_date).offset(skip).limit(limit).all()

@router.get("/mine", response_model=list[schemas.EventOut])
def my_events(db: Session = Depends(get_db),
              user: User = Depends(auth.require_role("organizer"))):
    return db.query(Event).filter_by(organizer_id=user.id).order_by(Event.event_date).all()

@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if not ev: raise HTTPException(404, "Event not found")
    return ev

@router.put("/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, body: schemas.EventUpdate, bg: BackgroundTasks,
                 db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    ev = db.get(Event, event_id)
    if not ev: raise HTTPException(404, "Event not found")
    if ev.organizer_id != user.id: raise HTTPException(403, "Not your event")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(ev, k, v)
    db.commit(); db.refresh(ev)
    for uid in {b.user_id for b in ev.bookings if b.status == "confirmed"}:
        bg.add_task(tasks.notify_event_update, uid, ev.id, ev.name)
    return ev

@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    ev = db.get(Event, event_id)
    if not ev: raise HTTPException(404, "Event not found")
    if ev.organizer_id != user.id: raise HTTPException(403, "Not your event")
    db.delete(ev); db.commit()

# ── Ticket Tiers ─────────────────────────────────────────────────────────────

@router.post("/{event_id}/tiers", response_model=schemas.TierOut, status_code=201)
def add_tier(event_id: int, body: schemas.TierCreate, db: Session = Depends(get_db),
             user: User = Depends(auth.require_role("organizer"))):
    ev = db.get(Event, event_id)
    if not ev: raise HTTPException(404, "Event not found")
    if ev.organizer_id != user.id: raise HTTPException(403, "Not your event")
    tier = TicketTier(**body.model_dump(), event_id=event_id, available_seats=body.total_seats)
    db.add(tier); db.commit(); db.refresh(tier)
    return tier

@router.get("/{event_id}/tiers", response_model=list[schemas.TierOut])
def get_tiers(event_id: int, db: Session = Depends(get_db)):
    if not db.get(Event, event_id): raise HTTPException(404, "Event not found")
    return db.query(TicketTier).filter_by(event_id=event_id).order_by(TicketTier.position).all()

@router.put("/{event_id}/tiers/{tier_id}", response_model=schemas.TierOut)
def update_tier(event_id: int, tier_id: int, body: schemas.TierUpdate,
                db: Session = Depends(get_db),
                user: User = Depends(auth.require_role("organizer"))):
    ev = db.get(Event, event_id)
    if not ev or ev.organizer_id != user.id: raise HTTPException(403, "Not your event")
    tier = db.get(TicketTier, tier_id)
    if not tier or tier.event_id != event_id: raise HTTPException(404, "Tier not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(tier, k, v)
    db.commit(); db.refresh(tier)
    return tier

@router.delete("/{event_id}/tiers/{tier_id}", status_code=204)
def delete_tier(event_id: int, tier_id: int, db: Session = Depends(get_db),
                user: User = Depends(auth.require_role("organizer"))):
    ev = db.get(Event, event_id)
    if not ev or ev.organizer_id != user.id: raise HTTPException(403, "Not your event")
    tier = db.get(TicketTier, tier_id)
    if not tier or tier.event_id != event_id: raise HTTPException(404, "Tier not found")
    db.delete(tier); db.commit()

# ── Seat availability ────────────────────────────────────────────────────────

@router.get("/{event_id}/seats")
def seat_availability(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if not ev: raise HTTPException(404, "Event not found")
    booked = (
        db.query(BookingAttendee.seat_label, BookingAttendee.booking_id)
        .join(Booking)
        .filter(Booking.event_id == event_id, Booking.status == "confirmed",
                BookingAttendee.seat_label.isnot(None))
        .all()
    )
    return {
        "event_id":           event_id,
        "has_seat_selection": ev.has_seat_selection,
        "booked_seats":       [r.seat_label for r in booked],
    }
