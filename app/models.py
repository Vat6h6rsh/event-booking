import secrets, string
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Boolean, Text, Date
from sqlalchemy.orm import relationship
from app.database import Base


def _ticket_code():
    chars = string.ascii_uppercase + string.digits
    return "JTK-" + "".join(secrets.choice(chars) for _ in range(8))


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role            = Column(String, nullable=False)          # organizer | customer
    full_name       = Column(String, nullable=True)
    phone           = Column(String(20), nullable=True)
    date_of_birth   = Column(Date, nullable=True)
    created_at      = Column(DateTime, server_default=func.now())

    bookings        = relationship("Booking", back_populates="user")
    support_tickets = relationship("SupportTicket", back_populates="user")
    venues          = relationship("Venue", back_populates="organizer")


class Venue(Base):
    __tablename__ = "venues"
    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String, nullable=False)
    address      = Column(String, nullable=False)
    city         = Column(String, nullable=False)
    state        = Column(String, nullable=True)
    country      = Column(String, default="India", nullable=False)
    capacity     = Column(Integer, nullable=False)
    description  = Column(Text, nullable=True)
    image_url    = Column(String, nullable=True)
    website      = Column(String, nullable=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at   = Column(DateTime, server_default=func.now())

    organizer = relationship("User", back_populates="venues")
    events    = relationship("Event", back_populates="venue_obj")


class Event(Base):
    __tablename__ = "events"
    id                 = Column(Integer, primary_key=True, index=True)
    name               = Column(String, nullable=False)
    venue              = Column(String, nullable=False)          # free-text kept for compat
    venue_id           = Column(Integer, ForeignKey("venues.id"), nullable=True)
    event_date         = Column(DateTime, nullable=False)
    end_date           = Column(DateTime, nullable=True)
    total_tickets      = Column(Integer, nullable=False)
    available_tickets  = Column(Integer, nullable=False)
    organizer_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    category           = Column(String, default="Other", nullable=False)
    image_url          = Column(String, nullable=True)
    banner_url         = Column(String, nullable=True)
    price              = Column(Integer, default=0, nullable=False)   # base price (paise)
    description        = Column(Text, nullable=True)
    age_rating         = Column(String, default="U", nullable=False)  # U / UA / A / 18+
    event_type         = Column(String, default="Other", nullable=False)
    has_seat_selection = Column(Boolean, default=False)
    tags               = Column(String, nullable=True)                # comma-separated
    status             = Column(String, default="published")          # draft/published/cancelled/completed

    organizer = relationship("User", foreign_keys=[organizer_id])
    venue_obj = relationship("Venue", back_populates="events")
    bookings  = relationship("Booking", back_populates="event")
    tiers     = relationship("TicketTier", back_populates="event", cascade="all, delete-orphan", order_by="TicketTier.position")


class TicketTier(Base):
    __tablename__ = "ticket_tiers"
    id              = Column(Integer, primary_key=True, index=True)
    event_id        = Column(Integer, ForeignKey("events.id"), nullable=False)
    name            = Column(String, nullable=False)        # General / VIP / Backstage / IMAX …
    price           = Column(Integer, nullable=False)       # paise
    total_seats     = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
    color           = Column(String, default="#A78BFA")    # hex for UI colour-coding
    description     = Column(Text, nullable=True)
    benefits        = Column(String, nullable=True)         # comma-separated perks
    position        = Column(Integer, default=0)

    event    = relationship("Event", back_populates="tiers")
    bookings = relationship("Booking", back_populates="tier")


class Booking(Base):
    __tablename__ = "bookings"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_id    = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    tier_id     = Column(Integer, ForeignKey("ticket_tiers.id"), nullable=True)
    quantity    = Column(Integer, nullable=False)
    total_price = Column(Integer, default=0)               # paise
    status      = Column(String, default="confirmed")      # confirmed / cancelled / pending
    created_at  = Column(DateTime, server_default=func.now())

    user      = relationship("User", back_populates="bookings")
    event     = relationship("Event", back_populates="bookings")
    tier      = relationship("TicketTier", back_populates="bookings")
    attendees = relationship("BookingAttendee", back_populates="booking", cascade="all, delete-orphan")

    # Computed helpers for schema serialisation
    @property
    def event_name(self):
        return self.event.name if self.event else None

    @property
    def tier_name(self):
        return self.tier.name if self.tier else None


class BookingAttendee(Base):
    __tablename__ = "booking_attendees"
    id          = Column(Integer, primary_key=True, index=True)
    booking_id  = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    full_name   = Column(String, nullable=False)
    age         = Column(Integer, nullable=True)
    phone       = Column(String(20), nullable=True)
    seat_label  = Column(String, nullable=True)            # e.g. "A1"
    ticket_code = Column(String, unique=True, nullable=False, default=_ticket_code)

    booking = relationship("Booking", back_populates="attendees")


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject              = Column(String, nullable=False)
    description          = Column(Text, nullable=False)
    status               = Column(String, default="open")      # open/in_progress/resolved/closed
    priority             = Column(String, default="medium")    # low/medium/high/urgent
    category             = Column(String, default="general")   # general/booking/payment/event/venue
    reference_booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    created_at           = Column(DateTime, server_default=func.now())
    updated_at           = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at          = Column(DateTime, nullable=True)

    user     = relationship("User", back_populates="support_tickets")
    messages = relationship("ChatMessage", back_populates="ticket", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id         = Column(Integer, primary_key=True, index=True)
    ticket_id  = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    sender_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    message    = Column(Text, nullable=False)
    is_staff   = Column(Boolean, default=False)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User")


class Notification(Base):
    """In-app notification. Written by Background Task 2 (event update) so the
    customer can *see* the alert in the UI, not just in the server console."""
    __tablename__ = "notifications"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type       = Column(String, nullable=False)                 # booking_confirmed | event_updated
    event_id   = Column(Integer, ForeignKey("events.id"), nullable=True)
    message    = Column(String, nullable=False)
    is_read    = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
