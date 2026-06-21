from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import auth, models, schemas, tasks
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Event Booking System",
    description="Role-based event management and ticket booking API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED, tags=["auth"])
def signup(body: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user as either an organizer or customer."""
    if db.query(models.User).filter_by(email=body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=body.email,
        hashed_password=auth.hash_pw(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=schemas.Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate and receive a JWT bearer token. Use your email as the username."""
    user = db.query(models.User).filter_by(email=form.username).first()
    if not user or not auth.verify_pw(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": auth.create_token(user), "token_type": "bearer"}


# ── Events ────────────────────────────────────────────────────────────────────

@app.post(
    "/events",
    response_model=schemas.EventOut,
    status_code=status.HTTP_201_CREATED,
    tags=["events"],
)
def create_event(
    body: schemas.EventCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_role("organizer")),
):
    """Create a new event. Organizers only."""
    event = models.Event(
        **body.model_dump(),
        available_tickets=body.total_tickets,
        organizer_id=user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@app.get("/events", response_model=list[schemas.EventOut], tags=["events"])
def list_events(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List all events. Public endpoint — no auth required."""
    return db.query(models.Event).offset(skip).limit(limit).all()


@app.get("/events/{event_id}", response_model=schemas.EventOut, tags=["events"])
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Fetch a single event by ID. Public endpoint — no auth required."""
    event = db.get(models.Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.put("/events/{event_id}", response_model=schemas.EventOut, tags=["events"])
def update_event(
    event_id: int,
    body: schemas.EventUpdate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_role("organizer")),
):
    """Update an event's details. Organizers only; must own the event.
    Background Task 2 fires for every customer who has a booking on this event.
    """
    event = db.get(models.Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only update your own events")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)

    # Background Task 2: notify every customer who booked this event
    booker_ids = {booking.user_id for booking in event.bookings}
    for uid in booker_ids:
        bg.add_task(tasks.notify_event_update, uid, event.id, event.name)

    return event


@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["events"])
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_role("organizer")),
):
    """Delete an event. Organizers only; must own the event."""
    event = db.get(models.Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own events")
    db.delete(event)
    db.commit()


# ── Bookings ──────────────────────────────────────────────────────────────────

@app.post(
    "/bookings",
    response_model=schemas.BookingOut,
    status_code=status.HTTP_201_CREATED,
    tags=["bookings"],
)
def create_booking(
    body: schemas.BookingCreate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_role("customer")),
):
    """Book tickets for an event. Customers only.

    Uses SELECT FOR UPDATE to hold a row-level lock for the duration of the
    transaction, preventing overselling under concurrent requests.
    (On SQLite this degrades to a full-table write lock, which still serialises
    writes correctly. On PostgreSQL/MySQL it becomes a true row lock.)
    Background Task 1 fires a confirmation 'email' after a successful booking.
    """
    event = (
        db.query(models.Event)
        .filter(models.Event.id == body.event_id)
        .with_for_update()
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.available_tickets < body.quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Only {event.available_tickets} ticket(s) remaining",
        )

    event.available_tickets -= body.quantity
    booking = models.Booking(
        user_id=user.id,
        event_id=event.id,
        quantity=body.quantity,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Background Task 1: booking confirmation email
    bg.add_task(tasks.send_booking_confirmation, user.email, event.name, booking.id)

    return booking


@app.get("/bookings", response_model=list[schemas.BookingOut], tags=["bookings"])
def my_bookings(
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_role("customer")),
):
    """List all bookings for the authenticated customer."""
    return db.query(models.Booking).filter_by(user_id=user.id).all()


@app.get("/bookings/{booking_id}", response_model=schemas.BookingOut, tags=["bookings"])
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(auth.require_role("customer")),
):
    """Fetch a specific booking. Customers can only view their own bookings."""
    booking = db.get(models.Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return booking
