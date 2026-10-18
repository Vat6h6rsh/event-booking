from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update, func, or_
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from app.models import Event, TicketTier, Booking, BookingAttendee, User, Venue
from app import auth, schemas, outbox
from app.email import ist_date

router = APIRouter(prefix="/events", tags=["events"])


def _owned_event(db, event_id, user):
    # A no-op UPDATE serializes all capacity/tier editors on the parent, on
    # SQLite as well as PostgreSQL. Read aggregate tier totals only afterwards.
    ev = db.execute(update(Event).where(Event.id == event_id).values(
        available_tickets=Event.available_tickets
    ).returning(Event).execution_options(populate_existing=True)).scalar_one_or_none()
    if not ev: raise HTTPException(404, "Event not found")
    if ev.organizer_id != user.id: raise HTTPException(403, "Not your event")
    return ev


def _validate_venue(db, venue_id, user):
    if venue_id is None: return
    venue = db.get(Venue, venue_id)
    if not venue or venue.organizer_id != user.id: raise HTTPException(422, "Venue must belong to this organizer")


def _tier_total(db, event_id, excluding=None):
    query = select(func.coalesce(func.sum(TicketTier.total_seats), 0)).where(TicketTier.event_id == event_id)
    if excluding is not None: query = query.where(TicketTier.id != excluding)
    return db.scalar(query)

# ── Events CRUD ──────────────────────────────────────────────────────────────

@router.post("", response_model=schemas.EventOut, status_code=201)
def create_event(body: schemas.EventCreate, db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    _validate_venue(db, body.venue_id, user)
    ev = Event(**body.model_dump(), available_tickets=body.total_tickets, organizer_id=user.id)
    db.add(ev); db.commit(); db.refresh(ev)
    return ev

@router.get("", response_model=list[schemas.EventOut])
def list_events(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), category: str = None,
                age_rating: str = None, city: str = None, q: str = None, db: Session = Depends(get_db)):
    query = db.query(Event).options(selectinload(Event.tiers)).filter(Event.status == "published")
    if category:   query = query.filter(Event.category == category)
    if age_rating: query = query.filter(Event.age_rating == age_rating)
    if city: query = query.filter(or_(Event.venue.ilike(f"%{city}%"), Event.venue_obj.has(Venue.city.ilike(f"%{city}%"))))
    if q: query = query.filter(Event.name.ilike(f"%{q}%"))
    return query.order_by(Event.event_date, Event.id).offset(skip).limit(limit).all()

@router.get("/mine", response_model=list[schemas.EventOut])
def my_events(db: Session = Depends(get_db),
              user: User = Depends(auth.require_role("organizer"))):
    return db.query(Event).options(selectinload(Event.tiers)).filter_by(organizer_id=user.id).order_by(Event.event_date).all()

@router.get("/mine/stats", response_model=list[schemas.EventStats])
def my_event_stats(db: Session = Depends(get_db),
                   user: User = Depends(auth.require_role("organizer"))):
    """Authoritative sales aggregates for the organizer's events, in one grouped query."""
    confirmed = Booking.status == "confirmed"
    rows = db.execute(
        select(Event.id,
               func.count(Booking.id).filter(confirmed),
               func.coalesce(func.sum(Booking.quantity).filter(confirmed), 0),
               func.coalesce(func.sum(Booking.total_price).filter(confirmed), 0),
               func.count(Booking.id).filter(Booking.status == "cancelled"))
        .outerjoin(Booking, Booking.event_id == Event.id)
        .where(Event.organizer_id == user.id).group_by(Event.id)
    ).all()
    return [schemas.EventStats(event_id=r[0], confirmed_bookings=r[1], tickets_sold=r[2],
                               gross_paise=r[3], cancelled_bookings=r[4]) for r in rows]

@router.get("/{event_id}", response_model=schemas.EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(Event, event_id)
    if not ev: raise HTTPException(404, "Event not found")
    return ev

@router.put("/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, body: schemas.EventUpdate,
                 db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    ev = _owned_event(db, event_id, user)
    values = {k: v for k, v in body.model_dump(exclude_unset=True).items() if getattr(ev, k) != v}
    _validate_venue(db, values.get("venue_id"), user)
    start, end = values.get("event_date", ev.event_date), values.get("end_date", ev.end_date)
    if end is not None and end < start: raise HTTPException(422, "end_date must be on or after event_date")
    if "total_tickets" in values and _tier_total(db, event_id) > values["total_tickets"]:
        raise HTTPException(422, "Tier totals cannot exceed event capacity")
    if values:
        changed = sorted(values)
        statement = update(Event).where(Event.id == event_id)
        if "total_tickets" in values:
            available = Event.available_tickets + values["total_tickets"] - Event.total_tickets
            statement = statement.where(available >= 0)
            values["available_tickets"] = available
        ev = db.execute(statement.values(**values).returning(Event)
                        .execution_options(populate_existing=True)).scalar_one_or_none()
        if ev is None: raise HTTPException(422, "cannot reduce below tickets sold")
        summary = f"Changed: {', '.join(changed)}. Date: {ist_date(ev.event_date)}. Venue: {ev.venue}."
        outbox.enqueue_event_update(db, ev.id, summary)
    result = schemas.EventOut.model_validate(ev)
    db.commit()
    if values: outbox.kick()
    return result

@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    ev = _owned_event(db, event_id, user)
    if db.scalar(select(Booking.id).where(Booking.event_id == event_id).limit(1)):
        raise HTTPException(409, "Events with booking history cannot be deleted")
    db.delete(ev); db.commit()

# ── Ticket Tiers ─────────────────────────────────────────────────────────────

@router.post("/{event_id}/tiers", response_model=schemas.TierOut, status_code=201)
def add_tier(event_id: int, body: schemas.TierCreate, db: Session = Depends(get_db),
             user: User = Depends(auth.require_role("organizer"))):
    ev = _owned_event(db, event_id, user)
    if _tier_total(db, event_id) + body.total_seats > ev.total_tickets:
        raise HTTPException(422, "Tier totals cannot exceed event capacity")
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
    ev = _owned_event(db, event_id, user)
    tier = db.get(TicketTier, tier_id)
    if not tier or tier.event_id != event_id: raise HTTPException(404, "Tier not found")
    values = body.model_dump(exclude_unset=True)
    statement = update(TicketTier).where(TicketTier.id == tier_id)
    if "total_seats" in values:
        if _tier_total(db, event_id, tier_id) + values["total_seats"] > ev.total_tickets:
            raise HTTPException(422, "Tier totals cannot exceed event capacity")
        available = TicketTier.available_seats + values["total_seats"] - TicketTier.total_seats
        statement = statement.where(available >= 0)
        values["available_seats"] = available
    if values:
        tier = db.execute(statement.values(**values).returning(TicketTier)
                          .execution_options(populate_existing=True)).scalar_one_or_none()
        if tier is None: raise HTTPException(422, "cannot reduce below seats sold")
    result = schemas.TierOut.model_validate(tier)
    db.commit()
    return result

@router.delete("/{event_id}/tiers/{tier_id}", status_code=204)
def delete_tier(event_id: int, tier_id: int, db: Session = Depends(get_db),
                user: User = Depends(auth.require_role("organizer"))):
    ev = _owned_event(db, event_id, user)
    tier = db.get(TicketTier, tier_id)
    if not tier or tier.event_id != event_id: raise HTTPException(404, "Tier not found")
    if db.scalar(select(Booking.id).where(Booking.tier_id == tier_id).limit(1)):
        raise HTTPException(409, "Tiers with booking history cannot be deleted")
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
