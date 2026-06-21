from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: Literal["organizer", "customer"]


class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


# ── Events ────────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    name: str = Field(min_length=1)
    venue: str = Field(min_length=1)
    event_date: datetime
    total_tickets: int = Field(gt=0)
    category: str = "Other"
    image_url: str | None = None
    price: int = Field(default=0, ge=0, description="Price in cents")


class EventUpdate(BaseModel):
    name: str | None = None
    venue: str | None = None
    event_date: datetime | None = None
    category: str | None = None
    image_url: str | None = None
    price: int | None = None


class EventOut(BaseModel):
    id: int
    name: str
    venue: str
    event_date: datetime
    total_tickets: int
    available_tickets: int
    organizer_id: int
    category: str
    image_url: str | None
    price: int

    model_config = {"from_attributes": True}


# ── Bookings ──────────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    event_id: int
    quantity: int = Field(gt=0)


class BookingOut(BaseModel):
    id: int
    event_id: int
    quantity: int
    created_at: datetime

    model_config = {"from_attributes": True}
