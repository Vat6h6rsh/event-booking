from datetime import datetime, date, timezone
from typing import Optional, List, Literal, ClassVar
from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator


class PartialUpdate(BaseModel):
    required_columns: ClassVar[set[str]] = set()

    @model_validator(mode="before")
    @classmethod
    def reject_required_nulls(cls, values):
        if isinstance(values, dict) and any(k in values and values[k] is None for k in cls.required_columns):
            raise ValueError("Required fields cannot be null")
        return values


class EventDates(BaseModel):
    @field_validator("event_date", "end_date", check_fields=False)
    @classmethod
    def utc_dates(cls, value):
        if value is not None and value.tzinfo:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @model_validator(mode="after")
    def valid_dates(self):
        if self.event_date and self.end_date and self.end_date < self.event_date:
            raise ValueError("end_date must be on or after event_date")
        return self

# ── Auth / User ───────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email:     EmailStr
    password:  str = Field(min_length=8)
    role:      Literal["organizer", "customer"]
    full_name: Optional[str] = None
    phone:     Optional[str] = None

class UserUpdate(BaseModel):
    full_name:     Optional[str]  = None
    phone:         Optional[str]  = None
    date_of_birth: Optional[date] = None

class UserOut(BaseModel):
    id:            int
    email:         EmailStr
    role:          str
    full_name:     Optional[str]      = None
    phone:         Optional[str]      = None
    date_of_birth: Optional[date]     = None
    created_at:    Optional[datetime] = None
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type:   str
    user:         UserOut

# ── Venue ─────────────────────────────────────────────────────────────────────

class VenueCreate(BaseModel):
    name:        str = Field(min_length=1)
    address:     str = Field(min_length=1)
    city:        str = Field(min_length=1)
    state:       Optional[str] = None
    country:     str = "India"
    capacity:    int = Field(gt=0)
    description: Optional[str] = None
    image_url:   Optional[str] = None
    website:     Optional[str] = None

class VenueUpdate(PartialUpdate):
    required_columns = {"name", "address", "city", "capacity"}
    name:        Optional[str] = Field(None, min_length=1)
    address:     Optional[str] = Field(None, min_length=1)
    city:        Optional[str] = Field(None, min_length=1)
    state:       Optional[str] = None
    capacity:    Optional[int] = Field(None, gt=0)
    description: Optional[str] = None
    image_url:   Optional[str] = None
    website:     Optional[str] = None

class VenueOut(BaseModel):
    id:           int
    name:         str
    address:      str
    city:         str
    state:        Optional[str]
    country:      str
    capacity:     int
    description:  Optional[str]
    image_url:    Optional[str]
    website:      Optional[str]
    organizer_id: int
    created_at:   datetime
    model_config = {"from_attributes": True}

# ── Ticket Tier ───────────────────────────────────────────────────────────────

class TierCreate(BaseModel):
    name:        str = Field(min_length=1)
    price:       int = Field(ge=0)
    total_seats: int = Field(gt=0)
    color:       str = "#A78BFA"
    description: Optional[str] = None
    benefits:    Optional[str] = None
    position:    int = 0

class TierUpdate(PartialUpdate):
    required_columns = {"name", "price", "total_seats", "color", "position"}
    name:        Optional[str] = Field(None, min_length=1)
    price:       Optional[int] = Field(None, ge=0)
    total_seats: Optional[int] = Field(None, gt=0)
    position:    Optional[int] = None
    color:       Optional[str] = None
    description: Optional[str] = None
    benefits:    Optional[str] = None

class TierOut(BaseModel):
    id:              int
    event_id:        int
    name:            str
    price:           int
    total_seats:     int
    available_seats: int
    color:           str
    description:     Optional[str]
    benefits:        Optional[str]
    position:        int
    model_config = {"from_attributes": True}

# ── Event ─────────────────────────────────────────────────────────────────────

class EventCreate(EventDates):
    name:               str = Field(min_length=1)
    venue:              str = Field(min_length=1)
    venue_id:           Optional[int]      = Field(None, gt=0)
    event_date:         datetime
    end_date:           Optional[datetime] = None
    total_tickets:      int = Field(gt=0)
    category:           str = "Other"
    image_url:          Optional[str] = None
    banner_url:         Optional[str] = None
    price:              int = Field(default=0, ge=0)
    description:        Optional[str] = None
    age_rating:         Literal["U", "UA", "A", "18+"] = "U"
    event_type:         str = "Other"
    has_seat_selection: bool = False
    tags:               Optional[str] = None
    status:             Literal["draft", "published", "cancelled"] = "published"

class EventUpdate(PartialUpdate, EventDates):
    required_columns = {"name", "venue", "event_date", "total_tickets", "category", "price", "age_rating", "event_type", "has_seat_selection", "status"}
    name:               Optional[str]      = Field(None, min_length=1)
    venue:              Optional[str]      = Field(None, min_length=1)
    venue_id:           Optional[int]      = Field(None, gt=0)
    event_date:         Optional[datetime] = None
    end_date:           Optional[datetime] = None
    total_tickets:      Optional[int]      = Field(None, gt=0)
    category:           Optional[str]      = None
    image_url:          Optional[str]      = None
    banner_url:         Optional[str]      = None
    price:              Optional[int]      = Field(None, ge=0)
    description:        Optional[str]      = None
    age_rating:         Optional[Literal["U", "UA", "A", "18+"]] = None
    event_type:         Optional[str]      = None
    has_seat_selection: Optional[bool]     = None
    tags:               Optional[str]      = None
    status:             Optional[Literal["draft", "published", "cancelled"]] = None

class EventStats(BaseModel):
    event_id:           int
    confirmed_bookings: int
    tickets_sold:       int
    gross_paise:        int   # sum of confirmed booking totals (no payments yet, so not "revenue")
    cancelled_bookings: int


class EventOut(BaseModel):
    id:                 int
    name:               str
    venue:              str
    venue_id:           Optional[int]
    event_date:         datetime
    end_date:           Optional[datetime]
    total_tickets:      int
    available_tickets:  int
    organizer_id:       int
    category:           str
    image_url:          Optional[str]
    banner_url:         Optional[str]
    price:              int
    description:        Optional[str]
    age_rating:         str
    event_type:         str
    has_seat_selection: bool
    tags:               Optional[str]
    status:             str
    tiers:              List[TierOut] = []
    model_config = {"from_attributes": True}

# ── Booking ───────────────────────────────────────────────────────────────────

class AttendeeCreate(BaseModel):
    full_name:  str = Field(min_length=1)
    age:        Optional[int] = Field(None, ge=0, le=120)
    phone:      Optional[str] = None
    seat_label: Optional[str] = None

class AttendeeOut(BaseModel):
    id:          int
    full_name:   str
    age:         Optional[int]
    phone:       Optional[str]
    seat_label:  Optional[str]
    ticket_code: str
    model_config = {"from_attributes": True}

class BookingCreate(BaseModel):
    event_id:  int = Field(gt=0)
    tier_id:   Optional[int]              = Field(None, gt=0)
    quantity:  int = Field(ge=1, le=10)
    attendees: Optional[List[AttendeeCreate]] = Field(None, max_length=10)

    @model_validator(mode="after")
    def attendee_count(self):
        if self.attendees and len(self.attendees) != self.quantity:
            raise ValueError("attendees must be empty or match quantity")
        return self

class BookingOut(BaseModel):
    id:          int
    event_id:    int
    event_name:  Optional[str]      = None
    tier_id:     Optional[int]
    tier_name:   Optional[str]      = None
    quantity:    int
    total_price: int
    status:      str
    attendees:   List[AttendeeOut]  = []
    created_at:  datetime
    model_config = {"from_attributes": True}

# ── Support ───────────────────────────────────────────────────────────────────

class SupportTicketCreate(BaseModel):
    subject:              str = Field(min_length=1)
    description:          str = Field(min_length=10)
    category:             Literal["general","booking","payment","event","venue"] = "general"
    priority:             Literal["low","medium","high","urgent"] = "medium"
    reference_booking_id: Optional[int] = None

class SupportTicketUpdate(BaseModel):
    status:   Optional[Literal["open","in_progress","resolved","closed"]] = None
    priority: Optional[Literal["low","medium","high","urgent"]]           = None

class SupportTicketOut(BaseModel):
    id:                   int
    user_id:              int
    subject:              str
    description:          str
    status:               str
    priority:             str
    category:             str
    reference_booking_id: Optional[int]
    created_at:           datetime
    updated_at:           datetime
    resolved_at:          Optional[datetime]
    model_config = {"from_attributes": True}

class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=1)

class ChatMessageOut(BaseModel):
    id:           int
    ticket_id:    int
    sender_id:    int
    sender_email: Optional[str] = None
    message:      str
    is_staff:     bool
    is_read:      bool
    created_at:   datetime
    model_config = {"from_attributes": True}

# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id:         int
    type:       str
    event_id:   Optional[int]
    message:    str
    is_read:    bool
    created_at: datetime
    model_config = {"from_attributes": True}

# ── Upload ────────────────────────────────────────────────────────────────────

class UploadOut(BaseModel):
    url:      str
    filename: str
    size:     int
